# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt
#Trip pod
from __future__ import annotations

import csv
import io
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import frappe
from frappe import _, cstr
from frappe.core.api.file import get_max_file_size
from frappe.model.document import Document
from frappe.utils import cint, get_site_path, now_datetime, nowdate
from frappe.utils.file_manager import save_file

PDF_EXTENSION = ".pdf"
READY_STATUS = "Ready"
IMPORTED_STATUS = "Imported"
FAILED_STATUS = "Failed"
NO_MATCH_STATUS = "No Match"
MULTIPLE_MATCHES_STATUS = "Multiple Matches"
INVALID_FILE_STATUS = "Invalid File"
INVALID_FILENAME_STATUS = "Invalid Filename"
DUPLICATE_TARGET_STATUS = "Duplicate Target"
TRIP_POD_STATUS_NOT_UPLOADED = "POD Not Uploaded"
TRIP_POD_STATUS_ORIGINAL = "Original POD Uploaded"
TRIP_POD_STATUS_DUPLICATE = "Duplicate POD Uploaded"
POD_TYPE_ORIGINAL = "Original"
POD_TYPE_DUPLICATE = "Duplicate"
POD_FIELD_ORIGINAL = "Original POD"
POD_FIELD_DUPLICATE = "Duplicate POD"
TRIP_TYPE_OTHER = "other"
SOURCE_MODE_BROWSER = "Browser Folder"
SOURCE_MODE_SERVER = "Server Folder"
JOB_STATUS_PENDING = "Pending"
JOB_STATUS_QUEUED = "Queued"
JOB_STATUS_RUNNING = "Running"
JOB_STATUS_COMPLETED = "Completed"
JOB_STATUS_FAILED = "Failed"
LARGE_BATCH_THRESHOLD = 500
ROW_DOCTYPE = "Trip POD Import File"
DEFAULT_BATCH_SIZE = 10
MAX_BATCH_SIZE = 50


class TripPODImport(Document):
	def before_insert(self):
		self._set_import_defaults()

	def validate(self):
		self._set_import_defaults()

	def _set_import_defaults(self):
		if self.name and self.import_no != self.name:
			self.import_no = self.name

		if not self.import_date:
			self.import_date = nowdate()

		if not self.import_by:
			self.import_by = (
				frappe.get_cached_value("User", frappe.session.user, "full_name")
				or frappe.session.user
			)

		_doc_set(self, "source_mode", cstr(_doc_get(self, "source_mode", "")).strip() or SOURCE_MODE_BROWSER)
		_doc_set(self, "scan_status", cstr(_doc_get(self, "scan_status", "")).strip() or JOB_STATUS_PENDING)
		_doc_set(
			self,
			"import_status",
			cstr(_doc_get(self, "import_status", "")).strip() or JOB_STATUS_PENDING,
		)
		_apply_summary_to_doc(self, _summary_from_rows(self.pod_files or []))


@frappe.whitelist()
def get_pod_preview(docname: str, trip_type: str | None = None):
	doc = _get_import_doc(docname, permtype="write")
	effective_trip_type = _get_effective_trip_type(doc, trip_type)
	return _save_and_build_preview(doc, effective_trip_type)


@frappe.whitelist()
def preview_local_folder_trip_pods(
	docname: str,
	trip_type: str | None = None,
	files: str | list[dict[str, Any]] | None = None,
):
	doc = _get_import_doc(docname, permtype="write")
	effective_trip_type = _get_effective_trip_type(doc, trip_type)
	file_entries = _coerce_local_preview_files(files)
	return _build_local_folder_preview(doc, effective_trip_type, file_entries)


@frappe.whitelist(methods=["POST"])
def stage_local_folder_trip_pods(
	docname: str,
	trip_type: str | None = None,
	batch_rows: str | list[dict[str, Any]] | None = None,
):
	doc = _get_import_doc(docname, permtype="write")
	effective_trip_type = _get_effective_trip_type(doc, trip_type)
	if _doc_has_field(doc, "trip_type"):
		doc.trip_type = effective_trip_type

	requested_rows = _coerce_batch_rows(batch_rows)
	if not requested_rows:
		frappe.throw(_("No mapped files were provided for staging."))

	batch_limit = min(max(cint(_doc_get(doc, "batch", DEFAULT_BATCH_SIZE)), 1), MAX_BATCH_SIZE)
	requested_rows = requested_rows[:batch_limit]
	file_map = _get_uploaded_batch_files()
	rows_by_key = {
		cstr(getattr(row, "client_row_key", "")).strip(): row
		for row in doc.pod_files
		if cstr(getattr(row, "client_row_key", "")).strip()
	}

	staged_count = 0
	failed_count = 0
	failures: list[frappe._dict] = []

	for item in requested_rows:
		client_row_key = cstr(item.get("client_row_key")).strip()
		row = rows_by_key.get(client_row_key)
		if not row or not cint(row.can_import) or not cstr(row.matched_trip).strip():
			continue

		uploaded_file = file_map.get(client_row_key)
		if not uploaded_file:
			row.preview_status = FAILED_STATUS
			row.status_message = _("Missing uploaded PDF for {0}.").format(row.file_name)
			row.can_import = 0
			row.error_trace = _("The browser did not send the selected file.")
			failed_count += 1
			failures.append(
				frappe._dict(
					file_name=row.file_name,
					matched_trip=row.matched_trip,
					message=row.status_message,
				)
			)
			continue

		save_point = f"trip_pod_stage_{row.idx}"
		frappe.db.savepoint(save_point)
		try:
			_delete_import_attachment(doc, cstr(getattr(row, "pod_file", "")).strip())
			file_doc = save_file(
				row.file_name or uploaded_file.filename,
				uploaded_file.stream.read(),
				doc.doctype,
				doc.name,
				folder="Home/Attachments",
				is_private=0,
			)
			row.pod_file = file_doc.file_url
			row.source_path = ""
			row.preview_status = READY_STATUS
			row.status_message = _("Ready to import into Trip {0}.").format(row.matched_trip)
			row.error_trace = ""
			staged_count += 1
			frappe.db.release_savepoint(save_point)
		except Exception as exc:
			frappe.db.rollback(save_point=save_point)
			row.preview_status = FAILED_STATUS
			row.status_message = cstr(exc)
			row.can_import = 0
			row.error_trace = frappe.get_traceback()
			failed_count += 1
			failures.append(
				frappe._dict(
					file_name=row.file_name,
					matched_trip=row.matched_trip,
					message=cstr(exc),
				)
			)

	_delete_unused_import_pdf_attachments(
		doc,
		{
			cstr(getattr(row, "pod_file", "")).strip()
			for row in doc.pod_files
			if cstr(getattr(row, "pod_file", "")).strip()
		},
	)
	_apply_summary_to_doc(doc, _summary_from_rows(doc.pod_files))
	_doc_set(doc, "scan_status", JOB_STATUS_COMPLETED)
	_doc_set(doc, "import_status", JOB_STATUS_PENDING)
	_clear_result_report(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	payload = _build_client_payload(doc, include_doc=True)
	payload.update(
		frappe._dict(
			staged_count=staged_count,
			failed_count=failed_count,
			failures=failures,
		)
	)
	return payload


@frappe.whitelist()
def import_staged_trip_pods(docname: str, trip_type: str | None = None):
	doc = _get_import_doc(docname, permtype="write")
	effective_trip_type = _get_effective_trip_type(doc, trip_type)
	if _doc_has_field(doc, "trip_type"):
		doc.trip_type = effective_trip_type

	missing_staged_files = [
		row.file_name
		for row in doc.pod_files
		if cint(row.can_import) and cstr(row.matched_trip).strip() and not cstr(row.pod_file).strip()
	]
	if missing_staged_files:
		frappe.throw(_("Please finish staging the selected PDFs before importing."))

	if not any(cint(row.can_import) and cstr(row.matched_trip).strip() for row in doc.pod_files):
		frappe.throw(_("No files are ready to import."))

	_doc_set(doc, "import_status", JOB_STATUS_RUNNING)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	result = _run_import(doc.name, background=False)
	doc = _get_import_doc(docname, permtype="read")
	payload = _build_client_payload(doc, include_doc=True)
	result.update(payload)
	return result


@frappe.whitelist(methods=["POST"])
def import_selected_trip_pods(
	docname: str,
	trip_type: str | None = None,
	batch_rows: str | list[dict[str, Any]] | None = None,
):
	doc = _get_import_doc(docname, permtype="write")
	effective_trip_type = _get_effective_trip_type(doc, trip_type)
	if _doc_has_field(doc, "trip_type"):
		doc.trip_type = effective_trip_type

	requested_rows = _coerce_batch_rows(batch_rows)
	if not requested_rows:
		frappe.throw(_("No mapped files were provided for import."))

	batch_limit = min(max(cint(_doc_get(doc, "batch", DEFAULT_BATCH_SIZE)), 1), MAX_BATCH_SIZE)
	requested_rows = requested_rows[:batch_limit]
	file_map = _get_uploaded_batch_files()
	rows_by_key = {
		cstr(getattr(row, "client_row_key", "")).strip(): row
		for row in doc.pod_files
		if cstr(getattr(row, "client_row_key", "")).strip()
	}
	require_arrival, require_release = _get_pod_date_requirements(effective_trip_type)
	check_dates = require_arrival or require_release
	pod_type = cstr(_doc_get(doc, "pod_type", POD_FIELD_ORIGINAL)).strip() or POD_FIELD_ORIGINAL

	imported_count = 0
	failed_count = 0
	imported_trips: list[str] = []
	failures: list[frappe._dict] = []

	for item in requested_rows:
		client_row_key = cstr(item.get("client_row_key")).strip()
		row = rows_by_key.get(client_row_key)
		if not row or not cint(row.can_import) or not cstr(row.matched_trip).strip():
			continue

		uploaded_file = file_map.get(client_row_key)
		if not uploaded_file:
			row.preview_status = FAILED_STATUS
			row.status_message = _("Missing uploaded PDF for {0}.").format(row.file_name)
			row.can_import = 0
			row.error_trace = _("The browser did not send the selected file.")
			failed_count += 1
			failures.append(
				frappe._dict(
					file_name=row.file_name,
					matched_trip=row.matched_trip,
					message=row.status_message,
				)
			)
			continue

		trip_vals = frappe.db.get_value(
			"Trip", row.matched_trip,
			["date_pod_uploaded_on_erp", "arrival_date_time", "release_date_time"], as_dict=True,
		) or {}
		pre_msg = None
		if trip_vals.get("date_pod_uploaded_on_erp"):
			pre_msg = _("Trip {0} already has a POD uploaded. Delete the existing POD before importing a new one.").format(
				row.matched_trip
			)
		elif check_dates:
			missing = []
			if require_arrival and not trip_vals.get("arrival_date_time"):
				missing.append(_("Arrival Date/Time"))
			if require_release and not trip_vals.get("release_date_time"):
				missing.append(_("Release Date/Time"))
			if missing:
				pre_msg = _("Trip {0}: {1} must be filled before POD can be imported.").format(
					row.matched_trip, _(" and ").join(missing)
				)
		if pre_msg:
			row.preview_status = FAILED_STATUS
			row.status_message = pre_msg
			row.can_import = 0
			row.error_trace = ""
			failed_count += 1
			failures.append(frappe._dict(
				file_name=row.file_name, matched_trip=row.matched_trip, message=pre_msg
			))
			continue

		save_point = f"trip_pod_import_batch_{row.idx}"
		frappe.db.savepoint(save_point)
		try:
			file_content = uploaded_file.stream.read()
			_check_pod_file_size(row.file_name, len(file_content))
			_delete_trip_pod_attachments(row.matched_trip)
			_clean_stale_file_hashes(file_content)
			original_display_name = row.file_name or uploaded_file.filename
			_clean_orphan_disk_files(original_display_name)
			saved_file = save_file(
				original_display_name,
				file_content,
				"Trip",
				row.matched_trip,
				folder="Home/Attachments",
				is_private=0,
			)
			# Frappe may store a hash-suffixed filename on disk; always restore the
			# original display name so the user sees e.g. "21085267.pdf" in the Trip.
			frappe.db.set_value("File", saved_file.name, "file_name", original_display_name)
			try:
				from logicore.logicore.api import compress_pod_pdf
				compress_pod_pdf(saved_file.name)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "POD Compress failed in bulk import")
			frappe.db.set_value(
				"Trip",
				row.matched_trip,
				{
					"date_pod_uploaded_on_erp": nowdate(),
					**_get_import_pod_updates(pod_type),
				},
				update_modified=True,
			)
			row.preview_status = IMPORTED_STATUS
			row.status_message = _("Imported to Trip {0}.").format(row.matched_trip)
			row.can_import = 0
			row.imported_on = now_datetime()
			row.error_trace = ""
			imported_count += 1
			imported_trips.append(row.matched_trip)
			frappe.db.release_savepoint(save_point)
		except Exception as exc:
			frappe.db.rollback(save_point=save_point)
			row.preview_status = FAILED_STATUS
			row.status_message = cstr(exc)
			row.can_import = 0
			row.imported_on = None
			row.error_trace = frappe.get_traceback()
			failed_count += 1
			failures.append(
				frappe._dict(
					file_name=row.file_name,
					matched_trip=row.matched_trip,
					message=cstr(exc),
				)
			)

	_apply_summary_to_doc(doc, _summary_from_rows(doc.pod_files))
	_doc_set(doc, "import_status", JOB_STATUS_COMPLETED)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	payload = _build_client_payload(doc, include_doc=True)
	payload.update(
		frappe._dict(
			imported_count=imported_count,
			failed_count=failed_count,
			imported_trips=imported_trips,
			failures=failures,
		)
	)
	return payload


@frappe.whitelist()
def remember_uploaded_file_names(docname: str, uploaded_files: str | list[dict[str, Any]]):
	doc = _get_import_doc(docname, permtype="write")
	_, duplicate_map = _deduplicate_attached_import_files(doc)
	entries = _coerce_uploaded_files(uploaded_files)
	if not entries:
		return _build_modified_response(doc)

	existing_rows = {
		cstr(row.pod_file).strip(): row
		for row in doc.pod_files
		if cstr(row.pod_file).strip()
	}

	for entry in entries:
		file_url = cstr(entry.get("file_url")).strip()
		file_url = duplicate_map.get(file_url, file_url)
		original_file_name = cstr(entry.get("original_file_name")).strip()
		if not file_url or not original_file_name:
			continue

		row = existing_rows.get(file_url)
		if not row:
			row = doc.append("pod_files", {})
			existing_rows[file_url] = row

		row.pod_file = file_url
		row.file_name = original_file_name
		row.source_path = ""
		row.reference_no = ""
		row.matched_trip = ""
		row.preview_status = ""
		row.status_message = ""
		row.can_import = 0
		row.match_count = 0
		row.imported_on = None
		row.error_trace = ""

	_doc_set(doc, "scan_status", JOB_STATUS_PENDING)
	if _doc_get(doc, "import_status", JOB_STATUS_PENDING) != JOB_STATUS_RUNNING:
		_doc_set(doc, "import_status", JOB_STATUS_PENDING)
	_apply_summary_to_doc(doc, _summary_from_rows(doc.pod_files))
	doc.save(ignore_permissions=True)
	return _build_modified_response(doc)


@frappe.whitelist()
def scan_pod_source(docname: str, trip_type: str | None = None):
	doc = _get_import_doc(docname, permtype="write")
	effective_trip_type = _get_effective_trip_type(doc, trip_type)

	if _is_server_source(doc):
		_validate_server_source_directory(_doc_get(doc, "source_folder_path", ""))
		_doc_db_set(
			doc.doctype,
			doc.name,
			{
				"scan_status": JOB_STATUS_QUEUED,
				"import_status": JOB_STATUS_PENDING,
			},
			update_modified=True,
		)
		frappe.enqueue(
			f"{__name__}._scan_server_source_job",
			queue="long",
			timeout=5400,
			job_name=f"trip_pod_scan::{doc.name}",
			enqueue_after_commit=True,
			docname=doc.name,
			trip_type=effective_trip_type,
		)
		return frappe._dict(
			queued=True,
			scan_status=JOB_STATUS_QUEUED,
			import_status=JOB_STATUS_PENDING,
		)

	return _save_and_build_preview(doc, effective_trip_type)


@frappe.whitelist()
def queue_import_trip_pods(docname: str, trip_type: str | None = None):
	doc = _get_import_doc(docname, permtype="write")
	effective_trip_type = _get_effective_trip_type(doc, trip_type)

	if _doc_get(doc, "scan_status", JOB_STATUS_PENDING) in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}:
		frappe.throw(_("Please wait for the scan to finish before importing."))

	if _is_browser_source(doc):
		if _doc_has_field(doc, "trip_type"):
			doc.trip_type = effective_trip_type
		missing_staged_files = [
			row.file_name
			for row in doc.pod_files
			if cint(row.can_import) and cstr(row.matched_trip).strip() and not cstr(row.pod_file).strip()
		]
		if missing_staged_files:
			frappe.throw(
				_("Please finish staging the selected PDFs before starting background import.")
			)

	if not any(cint(row.can_import) for row in doc.pod_files):
		frappe.throw(_("No files are ready to import."))

	_doc_db_set(
		doc.doctype,
		doc.name,
		{"import_status": JOB_STATUS_QUEUED},
		update_modified=True,
	)
	frappe.enqueue(
		f"{__name__}._import_trip_pods_job",
		queue="long",
		timeout=5400,
		job_name=f"trip_pod_import::{doc.name}",
		enqueue_after_commit=True,
		docname=doc.name,
	)
	return frappe._dict(queued=True, import_status=JOB_STATUS_QUEUED)


@frappe.whitelist()
def get_import_job_status(docname: str):
	doc = _get_import_doc(docname, permtype="read")
	include_doc = not _has_running_job(doc)
	return _build_client_payload(doc, include_doc=include_doc)


@frappe.whitelist()
def import_trip_pods(docname: str, trip_type: str | None = None):
	doc = _get_import_doc(docname, permtype="write")
	effective_trip_type = _get_effective_trip_type(doc, trip_type)
	if not _is_server_source(doc):
		_save_and_build_preview(doc, effective_trip_type)
	result = _run_import(doc.name, background=False)
	doc = _get_import_doc(docname, permtype="read")
	payload = _build_client_payload(doc, include_doc=True)
	result.update(payload)
	return result


def _scan_server_source_job(docname: str, trip_type: str) -> None:
	try:
		_doc_db_set(
			"Trip POD Import",
			docname,
			{
				"scan_status": JOB_STATUS_RUNNING,
				"import_status": JOB_STATUS_PENDING,
			},
			update_modified=True,
		)
		frappe.db.commit()

		doc = frappe.get_doc("Trip POD Import", docname)
		source_dir = _validate_server_source_directory(_doc_get(doc, "source_folder_path", ""))
		existing_rows = {
			cstr(row.source_path).strip(): _entry_from_row(row)
			for row in doc.pod_files
			if cstr(row.source_path).strip()
		}
		entries = []
		for path in _list_server_pdf_files(source_dir):
			existing = existing_rows.get(str(path), {})
			entries.append(
				frappe._dict(
					pod_file="",
					file_name=existing.get("file_name") or path.name,
					source_path=str(path),
					reference_no="",
					matched_trip=existing.get("matched_trip") or "",
					preview_status=existing.get("preview_status") or "",
					status_message=existing.get("status_message") or "",
					can_import=existing.get("can_import") or 0,
					match_count=existing.get("match_count") or 0,
					imported_on=existing.get("imported_on") or "",
					error_trace=existing.get("error_trace") or "",
				)
			)

		preview = _evaluate_file_entries(entries, trip_type)
		doc.set("pod_files", [])
		_append_rows(doc, preview.rows)
		_apply_summary_to_doc(doc, preview.summary)
		_doc_set(doc, "scan_status", JOB_STATUS_COMPLETED)
		_doc_set(doc, "import_status", JOB_STATUS_PENDING)
		doc.save(ignore_permissions=True)
		_refresh_result_report(doc)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), _("Trip POD Import server folder scan failed"))
		_doc_db_set(
			"Trip POD Import",
			docname,
			{"scan_status": JOB_STATUS_FAILED},
			update_modified=True,
		)
		frappe.db.commit()


def _import_trip_pods_job(docname: str) -> None:
	try:
		_doc_db_set(
			"Trip POD Import",
			docname,
			{"import_status": JOB_STATUS_RUNNING},
			update_modified=True,
		)
		frappe.db.commit()
		_run_import(docname, background=True)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), _("Trip POD Import import job failed"))
		_doc_db_set(
			"Trip POD Import",
			docname,
			{"import_status": JOB_STATUS_FAILED},
			update_modified=True,
		)
		frappe.db.commit()


def _run_import(docname: str, background: bool) -> frappe._dict:
	doc = frappe.get_doc("Trip POD Import", docname)
	source_files = _get_attached_file_docs_by_url(doc) if _is_browser_source(doc) else {}
	imported_count = 0
	skipped_count = 0
	failed_count = 0
	imported_trips: list[str] = []
	failures: list[frappe._dict] = []
	skipped_files: list[frappe._dict] = []
	row_updates_since_commit = 0
	trip_type = cstr(_doc_get(doc, "trip_type", "")).strip()
	pod_type = cstr(_doc_get(doc, "pod_type", POD_FIELD_ORIGINAL)).strip() or POD_FIELD_ORIGINAL
	require_arrival, require_release = _get_pod_date_requirements(trip_type)
	check_dates = require_arrival or require_release

	for row in doc.pod_files:
		if not cint(row.can_import) or not cstr(row.matched_trip).strip():
			skipped_count += 1
			skipped_files.append(
				frappe._dict(
					file_name=row.file_name,
					message=row.status_message or _("File is not ready for import."),
				)
			)
			continue

		save_point = f"trip_pod_import_{row.idx}"
		staged_file_url = cstr(getattr(row, "pod_file", "")).strip()
		saved_file_name = None
		frappe.db.savepoint(save_point)
		try:
			trip_vals = frappe.db.get_value(
				"Trip", row.matched_trip,
				["date_pod_uploaded_on_erp", "arrival_date_time", "release_date_time"], as_dict=True,
			) or {}
			if trip_vals.get("date_pod_uploaded_on_erp"):
				raise frappe.ValidationError(
					_("Trip {0} already has a POD uploaded. Delete the existing POD before importing a new one.").format(
						row.matched_trip
					)
				)
			if check_dates:
				missing = []
				if require_arrival and not trip_vals.get("arrival_date_time"):
					missing.append(_("Arrival Date/Time"))
				if require_release and not trip_vals.get("release_date_time"):
					missing.append(_("Release Date/Time"))
				if missing:
					raise frappe.ValidationError(
						_("Trip {0}: {1} must be filled before POD can be imported.").format(
							row.matched_trip, _(" and ").join(missing)
						)
					)
			file_name, content, is_private = _get_source_file_payload(doc, row, source_files)
			_check_pod_file_size(file_name, len(content))
			_delete_trip_pod_attachments(row.matched_trip)
			_clean_stale_file_hashes(content)
			_clean_orphan_disk_files(file_name)
			saved_file = save_file(
				file_name,
				content,
				"Trip",
				row.matched_trip,
				folder="Home/Attachments",
				is_private=is_private,
			)
			frappe.db.set_value("File", saved_file.name, "file_name", file_name)
			frappe.db.set_value(
				"Trip",
				row.matched_trip,
				{
					"date_pod_uploaded_on_erp": nowdate(),
					**_get_import_pod_updates(pod_type),
				},
				update_modified=True,
			)

			updates = {
				"preview_status": IMPORTED_STATUS,
				"status_message": _("Imported to Trip {0}.").format(row.matched_trip),
				"can_import": 0,
				"pod_file": "",
				"imported_on": now_datetime(),
				"error_trace": "",
			}
			imported_count += 1
			imported_trips.append(row.matched_trip)
			frappe.db.release_savepoint(save_point)
			saved_file_name = saved_file.name
		except Exception as exc:
			frappe.db.rollback(save_point=save_point)
			updates = {
				"preview_status": FAILED_STATUS,
				"status_message": cstr(exc),
				"can_import": 0,
				"pod_file": "",
				"imported_on": None,
				"error_trace": frappe.get_traceback(),
			}
			failed_count += 1
			failures.append(
				frappe._dict(
					file_name=row.file_name,
					matched_trip=row.matched_trip,
					message=cstr(exc),
				)
			)
		_delete_import_attachment(doc, staged_file_url)

		if background:
			frappe.db.set_value(ROW_DOCTYPE, row.name, updates, update_modified=False)
			row_updates_since_commit += 1
		else:
			for fieldname, value in updates.items():
				setattr(row, fieldname, value)

		# Compress outside savepoint — compress_pod_pdf calls db.commit which destroys savepoints
		if saved_file_name:
			try:
				from logicore.logicore.api import compress_pod_pdf
				compress_pod_pdf(saved_file_name)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "POD Compress failed in bulk import")

		if background and row_updates_since_commit >= 25:
			frappe.db.commit()
			row_updates_since_commit = 0

	if background:
		frappe.db.commit()
		doc = frappe.get_doc("Trip POD Import", docname)
		_apply_summary_to_doc(doc, _summary_from_rows(doc.pod_files))
		_doc_set(doc, "import_status", JOB_STATUS_COMPLETED)
		doc.save(ignore_permissions=True)
		_refresh_result_report(doc)
		frappe.db.commit()
	else:
		_apply_summary_to_doc(doc, _summary_from_rows(doc.pod_files))
		_doc_set(doc, "import_status", JOB_STATUS_COMPLETED)
		doc.save(ignore_permissions=True)
		_refresh_result_report(doc)
		frappe.db.commit()

	return frappe._dict(
		imported_count=imported_count,
		skipped_count=skipped_count,
		failed_count=failed_count,
		total_files=len(doc.pod_files),
		imported_trips=imported_trips,
		skipped_files=skipped_files,
		failures=failures,
	)


def _get_import_doc(docname: str, permtype: str = "read") -> TripPODImport:
	if not docname:
		frappe.throw(_("Please save the import document before continuing."))

	doc = frappe.get_doc("Trip POD Import", docname)
	doc.check_permission(permtype)
	return doc


def _doc_has_field(doc: Document, fieldname: str) -> bool:
	meta = getattr(doc, "meta", None)
	if not meta:
		return False
	return bool(meta.has_field(fieldname))


def _doc_get(doc: Document, fieldname: str, default=None):
	if not _doc_has_field(doc, fieldname):
		return default
	return getattr(doc, fieldname, default)


def _doc_set(doc: Document, fieldname: str, value) -> None:
	if _doc_has_field(doc, fieldname):
		setattr(doc, fieldname, value)


def _doc_db_set(doctype: str, docname: str, values: dict[str, Any], update_modified: bool) -> None:
	meta = frappe.get_meta(doctype)
	valid_values = {key: value for key, value in values.items() if meta.has_field(key)}
	if not valid_values:
		return
	frappe.db.set_value(doctype, docname, valid_values, update_modified=update_modified)


def _save_and_build_preview(doc: TripPODImport, trip_type: str) -> frappe._dict:
	if _doc_has_field(doc, "trip_type"):
		doc.trip_type = trip_type

	if _is_browser_source(doc):
		_rebuild_import_rows_from_attachments(doc)

	preview = _build_preview(doc, trip_type)
	doc.set("pod_files", [])
	_append_rows(doc, preview.rows)
	_apply_summary_to_doc(doc, preview.summary)
	_doc_set(doc, "scan_status", JOB_STATUS_COMPLETED)
	if _doc_get(doc, "import_status", JOB_STATUS_PENDING) != JOB_STATUS_RUNNING:
		_doc_set(
			doc,
			"import_status",
			JOB_STATUS_COMPLETED if preview.summary.imported_files else JOB_STATUS_PENDING
		)
	_clear_result_report(doc)
	doc.save(ignore_permissions=True)
	preview.result_report_file = _refresh_result_report(doc)
	preview.show_rows = preview.summary.total_files <= LARGE_BATCH_THRESHOLD
	preview.large_batch = preview.summary.total_files > LARGE_BATCH_THRESHOLD
	if not preview.show_rows:
		preview.rows = []
	preview.doc_modified = doc.modified
	preview.doc_modified_by = doc.modified_by
	preview.scan_status = _doc_get(doc, "scan_status", JOB_STATUS_COMPLETED)
	preview.import_status = _doc_get(doc, "import_status", JOB_STATUS_PENDING)
	_add_doc_snapshot(preview, doc, include_rows=preview.show_rows)
	return preview


def _rebuild_import_rows_from_attachments(doc: TripPODImport) -> None:
	existing_rows = {
		cstr(row.pod_file): _entry_from_row(row)
		for row in doc.pod_files
		if cstr(row.pod_file).strip()
	}
	files, duplicate_map = _deduplicate_attached_import_files(doc)
	for duplicate_url, kept_url in duplicate_map.items():
		if duplicate_url in existing_rows and kept_url not in existing_rows:
			existing_rows[kept_url] = existing_rows[duplicate_url]
	doc.set("pod_files", [])

	for file_doc in files:
		existing = existing_rows.get(file_doc.file_url, {})
		doc.append(
			"pod_files",
			{
				"pod_file": file_doc.file_url,
				"file_name": existing.get("file_name")
				or file_doc.file_name
				or os.path.basename(file_doc.file_url),
				"source_path": "",
				"reference_no": existing.get("reference_no") or "",
				"matched_trip": existing.get("matched_trip") or "",
				"preview_status": existing.get("preview_status") or "",
				"status_message": existing.get("status_message") or "",
				"can_import": existing.get("can_import") or 0,
				"match_count": existing.get("match_count") or 0,
				"imported_on": existing.get("imported_on") or "",
				"error_trace": existing.get("error_trace") or "",
			},
		)


def _get_attached_import_files(doc: TripPODImport) -> list[frappe._dict]:
	return frappe.get_all(
		"File",
		filters={"attached_to_doctype": doc.doctype, "attached_to_name": doc.name},
		fields=["name", "file_name", "file_url", "is_private", "creation", "content_hash"],
		order_by="creation desc",
	)


def _deduplicate_attached_import_files(
	doc: TripPODImport,
) -> tuple[list[frappe._dict], dict[str, str]]:
	files = _get_attached_import_files(doc)
	if not files:
		return [], {}

	grouped_files: dict[str, list[frappe._dict]] = defaultdict(list)
	for file_doc in files:
		group_key = cstr(file_doc.content_hash).strip() or cstr(file_doc.file_url).strip()
		grouped_files[group_key].append(file_doc)

	kept_files: list[frappe._dict] = []
	duplicate_map: dict[str, str] = {}
	for grouped in grouped_files.values():
		canonical_file = grouped[0]
		kept_files.append(canonical_file)
		for duplicate_file in grouped[1:]:
			duplicate_map[cstr(duplicate_file.file_url).strip()] = cstr(canonical_file.file_url).strip()
			frappe.delete_doc("File", duplicate_file.name, force=True, ignore_permissions=True)

	return kept_files, duplicate_map


def _get_attached_file_doc(doc: TripPODImport, file_url: str):
	file_name = frappe.db.get_value(
		"File",
		{"attached_to_doctype": doc.doctype, "attached_to_name": doc.name, "file_url": file_url},
		"name",
	)
	return frappe.get_doc("File", file_name) if file_name else None


def _get_attached_file_docs_by_url(doc: TripPODImport) -> dict[str, Document]:
	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": doc.doctype, "attached_to_name": doc.name},
		fields=["name", "file_url"],
	)
	return {
		cstr(file_doc.file_url).strip(): frappe.get_doc("File", file_doc.name)
		for file_doc in files
		if cstr(file_doc.file_url).strip()
	}


def _build_preview(doc: TripPODImport, trip_type: str) -> frappe._dict:
	return _evaluate_file_entries([_entry_from_row(row) for row in doc.pod_files], trip_type)


def _build_local_folder_preview(
	doc: TripPODImport,
	trip_type: str,
	file_entries: list[frappe._dict],
) -> frappe._dict:
	if _doc_has_field(doc, "trip_type"):
		doc.trip_type = trip_type

	preview = _evaluate_file_entries(file_entries, trip_type)
	mapped_rows = [
		row
		for row in preview.rows
		if cint(row.can_import) and cstr(row.matched_trip).strip()
	]
	doc.set("pod_files", [])
	_append_rows(doc, mapped_rows)
	_delete_unused_import_pdf_attachments(doc, set())
	_apply_summary_to_doc(doc, _summary_from_rows(doc.pod_files))
	_doc_set(doc, "scan_status", JOB_STATUS_COMPLETED)
	_doc_set(doc, "import_status", JOB_STATUS_PENDING)
	_clear_result_report(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	payload = _build_client_payload(doc, include_doc=True)
	payload.selection_summary = preview.summary
	payload.selected_file_count = len(file_entries)

	# Attach sample unmatched reference numbers to help diagnose no-match issues
	unmatched_refs = [
		cstr(row.reference_no).strip()
		for row in preview.rows
		if cstr(row.preview_status).strip() == NO_MATCH_STATUS and cstr(row.reference_no).strip()
	]
	payload.sample_unmatched_refs = unmatched_refs[:10]

	# Include failed rows so the JS can show per-file validation error messages
	payload.selection_failed_rows = [
		_serialize_row(row)
		for row in preview.rows
		if cstr(row.get("preview_status")).strip() == FAILED_STATUS
	]
	return payload


def _evaluate_file_entries(entries: list[frappe._dict], trip_type: str) -> frappe._dict:
	summary = _blank_summary()
	rows: list[frappe._dict] = []
	ready_rows_by_trip: dict[str, list[frappe._dict]] = defaultdict(list)
	match_field, match_label = _get_trip_match_config(trip_type)
	reference_numbers: list[str] = []
	entries_by_reference: dict[str, list[int]] = defaultdict(list)

	for entry in entries:
		previous_status = cstr(entry.get("preview_status")).strip()
		previous_matched_trip = cstr(entry.get("matched_trip")).strip()
		file_name = cstr(entry.get("file_name") or _guess_file_name(entry.get("pod_file"))).strip()
		row = frappe._dict(
			client_row_key=cstr(entry.get("client_row_key")).strip(),
			pod_file=cstr(entry.get("pod_file")).strip(),
			file_name=file_name,
			source_path=cstr(entry.get("source_path")).strip(),
			reference_no="",
			matched_trip="",
			preview_status="",
			status_message="",
			can_import=0,
			match_count=0,
			imported_on=entry.get("imported_on") or "",
			error_trace=entry.get("error_trace") or "",
		)

		if not file_name:
			row.preview_status = INVALID_FILE_STATUS
			row.status_message = _("Missing file name for this entry.")
			summary.invalid_files += 1
			rows.append(row)
			continue

		if not _is_pdf(file_name):
			row.preview_status = INVALID_FILE_STATUS
			row.status_message = _("Only PDF files are allowed.")
			summary.invalid_files += 1
			rows.append(row)
			continue

		reference_no = _extract_reference_no(file_name)
		if not reference_no:
			row.preview_status = INVALID_FILENAME_STATUS
			row.status_message = _(
				"Could not parse the reference value from the file name. Name the file with just the TCN/Trip No (or LR No), e.g. RC90210521.pdf."
			)
			summary.invalid_files += 1
			rows.append(row)
			continue

		row.reference_no = reference_no
		entries_by_reference[reference_no].append(len(rows))
		reference_numbers.append(reference_no)
		rows.append(row)

	if reference_numbers:
		trip_rows = frappe.get_all(
			"Trip",
			filters={"trip_type": trip_type, match_field: ["in", sorted(set(reference_numbers))]},
			fields=["name", match_field],
			limit_page_length=max(len(set(reference_numbers)) * 10, 1),
		)
	else:
		trip_rows = []

	matches_by_reference: dict[str, list[str]] = defaultdict(list)
	for trip_row in trip_rows:
		reference_no = cstr(trip_row.get(match_field)).strip()
		if reference_no:
			matches_by_reference[reference_no].append(trip_row.name)

	for reference_no, row_indexes in entries_by_reference.items():
		matches = matches_by_reference.get(reference_no, [])
		for row_index in row_indexes:
			row = rows[row_index]
			previous_status = cstr(entries[row_index].get("preview_status")).strip()
			previous_matched_trip = cstr(entries[row_index].get("matched_trip")).strip()
			row.match_count = len(matches)

			if len(matches) == 1:
				row.matched_trip = matches[0]
				if previous_status == IMPORTED_STATUS and previous_matched_trip == matches[0]:
					row.preview_status = IMPORTED_STATUS
					row.status_message = _("Already imported to Trip {0}.").format(matches[0])
					summary.imported_files += 1
				else:
					row.preview_status = READY_STATUS
					row.status_message = _("Ready to import into Trip {0}.").format(matches[0])
					row.can_import = 1
					ready_rows_by_trip[matches[0]].append(row)
			elif not matches:
				row.preview_status = NO_MATCH_STATUS
				row.status_message = _("No Trip found for {0} {1} with Trip Type {2}.").format(
					match_label, reference_no, trip_type
				)
				summary.unmatched_files += 1
			else:
				row.preview_status = MULTIPLE_MATCHES_STATUS
				row.status_message = _(
					"Multiple Trips found for {0} {1} with Trip Type {2}."
				).format(match_label, reference_no, trip_type)
				summary.duplicate_match_files += 1

	for trip_name, trip_rows in ready_rows_by_trip.items():
		if len(trip_rows) < 2:
			continue

		for row in trip_rows:
			row.preview_status = DUPLICATE_TARGET_STATUS
			row.status_message = _(
				"Multiple uploaded PDFs map to Trip {0}. Keep only one file per Trip."
			).format(trip_name)
			row.can_import = 0
			summary.duplicate_target_files += 1

	summary = _summary_from_rows(rows)
	return frappe._dict(summary=summary, rows=rows, can_import=bool(summary.importable_files))


def _delete_trip_pod_attachments(trip_name: str) -> None:
	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Trip", "attached_to_name": trip_name},
		fields=["name", "file_name", "content_hash"],
	)
	for file_doc in files:
		if os.path.splitext(cstr(file_doc.file_name or "").strip())[1].lower() in {
			".jpg",
			".jpeg",
			".png",
			".pdf",
		}:
			# Clear content_hash before deletion so that Frappe's save_file deduplication
			# cannot reuse a stale URL after the physical file is removed.
			if cstr(file_doc.content_hash).strip():
				frappe.db.set_value("File", file_doc.name, "content_hash", "")
			try:
				frappe.delete_doc("File", file_doc.name, force=True, ignore_permissions=True)
			except OSError:
				frappe.db.delete("File", {"name": file_doc.name})


def _clean_orphan_disk_files(file_name: str) -> None:
	"""Remove physical files matching file_name (including hash variants) that no File record references.

	When Frappe saves a file and a same-named file already exists on disk it appends a
	content-hash suffix (e.g. 21085267436b42.pdf).  That hash ends up in both file_url
	AND file_name of the File record, so the audit trail shows the ugly hash name.
	Deleting unreferenced old copies lets save_file write the file with the clean original
	name, giving a correct audit trail entry.
	"""
	import glob
	site_files_path = frappe.get_site_path("public", "files")
	base = os.path.splitext(file_name)[0]
	ext = os.path.splitext(file_name)[1].lower()
	for physical_path in glob.glob(os.path.join(site_files_path, f"{base}*{ext}")):
		physical_url = "/files/" + os.path.basename(physical_path)
		if not frappe.db.exists("File", {"file_url": physical_url}):
			try:
				os.remove(physical_path)
			except Exception:
				pass


def _clean_stale_file_hashes(content: bytes) -> None:
	"""Before save_file, clear content_hash on any File record whose physical file is missing.

	Frappe deduplicates uploads by content_hash: if a match exists it reuses the stored
	file_url.  When the physical file was deleted (e.g. user deleted a Trip POD) but the
	File record remains in the DB, save_file tries to use the old URL → [Errno 2].
	Clearing the hash forces save_file to write a fresh physical file instead.
	"""
	import hashlib
	content_hash = hashlib.md5(content).hexdigest()
	matching = frappe.db.get_all(
		"File",
		filters={"content_hash": content_hash},
		fields=["name", "file_url", "is_private"],
	)
	for f in matching:
		file_url = cstr(f.file_url).strip()
		if not file_url:
			continue
		try:
			file_doc = frappe.get_doc("File", f.name)
			full_path = file_doc.get_full_path()
			if not os.path.exists(full_path):
				frappe.db.set_value("File", f.name, "content_hash", "")
		except Exception:
			frappe.db.set_value("File", f.name, "content_hash", "")


def _get_import_pod_updates(pod_type: str) -> dict[str, str]:
	if cstr(pod_type).strip() == POD_FIELD_DUPLICATE:
		return {
			"uploaded_pod_originalduplicate": POD_TYPE_DUPLICATE,
			"pod_status": TRIP_POD_STATUS_DUPLICATE,
		}
	return {
		"uploaded_pod_originalduplicate": POD_TYPE_ORIGINAL,
		"pod_status": TRIP_POD_STATUS_ORIGINAL,
	}


def _get_effective_trip_type(doc: TripPODImport, trip_type: str | None) -> str:
	effective_trip_type = cstr(trip_type).strip() or cstr(doc.trip_type).strip()
	if not effective_trip_type:
		frappe.throw(_("Please select Trip Type before previewing or importing POD files."))
	return effective_trip_type


def _get_trip_match_config(trip_type: str) -> tuple[str, str]:
	if _normalize_trip_type(trip_type) == TRIP_TYPE_OTHER:
		return "lr_no", _("LR No")
	return "tcntrip_no", _("TCN/Trip No")


def _normalize_trip_type(trip_type: str | None) -> str:
	return cstr(trip_type).strip().casefold()


def _serialize_row(row) -> frappe._dict:
	return frappe._dict(
		client_row_key=cstr(getattr(row, "client_row_key", row.get("client_row_key", ""))).strip(),
		pod_file=cstr(getattr(row, "pod_file", "")).strip(),
		file_name=cstr(getattr(row, "file_name", "")).strip(),
		source_path=cstr(getattr(row, "source_path", "")).strip(),
		reference_no=cstr(getattr(row, "reference_no", "")).strip(),
		matched_trip=cstr(getattr(row, "matched_trip", "")).strip(),
		preview_status=cstr(getattr(row, "preview_status", "")).strip(),
		status_message=cstr(getattr(row, "status_message", "")).strip(),
		can_import=cint(getattr(row, "can_import", 0)),
		match_count=cint(getattr(row, "match_count", 0)),
		imported_on=getattr(row, "imported_on", None),
		error_trace=cstr(getattr(row, "error_trace", "")).strip(),
	)


def _entry_from_row(row) -> frappe._dict:
	return _serialize_row(row)


def _append_rows(doc: TripPODImport, rows: list[frappe._dict]) -> None:
	for row in rows:
		doc.append("pod_files", dict(_serialize_row(row)))


def _guess_file_name(file_url: str | None) -> str:
	return os.path.basename(cstr(file_url or "").strip())


def _is_pdf(file_name: str) -> bool:
	return os.path.splitext(cstr(file_name).strip())[1].lower() == PDF_EXTENSION


def _check_pod_file_size(file_name: str, size_bytes: int) -> None:
	"""Raise if `size_bytes` exceeds System Settings' Max File Size — the same limit
	Frappe's own File doctype enforces on insert (frappe.core.api.file.get_max_file_size),
	so this only ever fails earlier with a friendlier, file-specific message."""
	max_size = get_max_file_size()
	if size_bytes > max_size:
		frappe.throw(_("File '{0}' is {1:.1f} MB — maximum allowed is {2:.0f} MB.").format(
			file_name, size_bytes / (1024 * 1024), max_size / (1024 * 1024)
		))


def _extract_reference_no(file_name: str) -> str | None:
	# File name must be exactly the Reference No (TCN/Trip No or LR No), e.g. RC90210521.pdf.
	# Older date-time-prefixed names (with hyphens) are no longer accepted.
	base_name = os.path.splitext(os.path.basename(cstr(file_name).strip()))[0].strip()
	if not base_name or "-" in base_name:
		return None
	return base_name


def _coerce_uploaded_files(uploaded_files: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
	if not uploaded_files:
		return []
	if isinstance(uploaded_files, str):
		return json.loads(uploaded_files)
	return list(uploaded_files)


def _coerce_local_preview_files(files: str | list[dict[str, Any]] | None) -> list[frappe._dict]:
	if not files:
		return []
	if isinstance(files, str):
		files = json.loads(files)

	normalized_files = []
	for item in list(files):
		file_name = cstr(item.get("file_name")).strip()
		client_row_key = cstr(item.get("client_row_key")).strip()
		if not file_name or not client_row_key:
			continue
		normalized_files.append(
			frappe._dict(
				client_row_key=client_row_key,
				file_name=file_name,
				pod_file="",
				source_path="",
			)
		)

	normalized_files.sort(key=lambda item: (item.file_name.casefold(), item.client_row_key))
	return normalized_files


def _coerce_batch_rows(
	batch_rows: str | list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
	if not batch_rows:
		return []
	if isinstance(batch_rows, str):
		return json.loads(batch_rows)
	return list(batch_rows)


def _get_uploaded_batch_files() -> dict[str, Any]:
	file_map: dict[str, Any] = {}
	for fieldname in frappe.request.files:
		if not fieldname.startswith("file__"):
			continue
		client_row_key = fieldname.removeprefix("file__").strip()
		if client_row_key:
			file_map[client_row_key] = frappe.request.files[fieldname]
	return file_map


def _is_server_source(doc: TripPODImport) -> bool:
	return cstr(_doc_get(doc, "source_mode", SOURCE_MODE_BROWSER)).strip() == SOURCE_MODE_SERVER


def _is_browser_source(doc: TripPODImport) -> bool:
	return not _is_server_source(doc)


def _blank_summary() -> frappe._dict:
	return frappe._dict(
		total_files=0,
		importable_files=0,
		skipped_files=0,
		unmatched_files=0,
		duplicate_match_files=0,
		invalid_files=0,
		duplicate_target_files=0,
		imported_files=0,
		failed_files=0,
	)


def _summary_from_rows(rows) -> frappe._dict:
	summary = _blank_summary()
	row_list = list(rows or [])
	summary.total_files = len(row_list)

	for row in row_list:
		status = cstr(getattr(row, "preview_status", row.get("preview_status", ""))).strip()
		can_import = cint(getattr(row, "can_import", row.get("can_import", 0)))
		if can_import:
			summary.importable_files += 1
		if status == IMPORTED_STATUS:
			summary.imported_files += 1
		elif status == FAILED_STATUS:
			summary.failed_files += 1
		elif status == NO_MATCH_STATUS:
			summary.unmatched_files += 1
		elif status == MULTIPLE_MATCHES_STATUS:
			summary.duplicate_match_files += 1
		elif status == DUPLICATE_TARGET_STATUS:
			summary.duplicate_target_files += 1
		elif status in {INVALID_FILE_STATUS, INVALID_FILENAME_STATUS}:
			summary.invalid_files += 1

	summary.skipped_files = max(summary.total_files - summary.importable_files, 0)
	return summary


def _apply_summary_to_doc(doc: TripPODImport, summary: frappe._dict) -> None:
	_doc_set(doc, "total_files_count", cint(summary.total_files))
	_doc_set(doc, "ready_files_count", cint(summary.importable_files))
	_doc_set(doc, "imported_files_count", cint(summary.imported_files))
	_doc_set(doc, "failed_files_count", cint(summary.failed_files))
	_doc_set(doc, "unmatched_files_count", cint(summary.unmatched_files))
	_doc_set(doc, "duplicate_match_files_count", cint(summary.duplicate_match_files))
	_doc_set(doc, "duplicate_target_files_count", cint(summary.duplicate_target_files))
	_doc_set(doc, "invalid_files_count", cint(summary.invalid_files))


def _build_client_payload(doc: TripPODImport, include_doc: bool = False) -> frappe._dict:
	summary = _summary_from_rows(doc.pod_files)
	show_rows = summary.total_files <= LARGE_BATCH_THRESHOLD
	rows = [_serialize_row(row) for row in doc.pod_files] if show_rows else []
	payload = frappe._dict(
		summary=summary,
		rows=rows,
		can_import=bool(summary.importable_files),
		show_rows=show_rows,
		large_batch=summary.total_files > LARGE_BATCH_THRESHOLD,
		source_mode=_doc_get(doc, "source_mode", SOURCE_MODE_BROWSER),
		scan_status=_doc_get(doc, "scan_status", JOB_STATUS_PENDING),
		import_status=_doc_get(doc, "import_status", JOB_STATUS_PENDING),
		result_report_file=_doc_get(doc, "result_report_file", ""),
		doc_modified=doc.modified,
		doc_modified_by=doc.modified_by,
	)
	if include_doc and show_rows:
		_add_doc_snapshot(payload, doc, include_rows=True)
	return payload


def _build_modified_response(doc: TripPODImport) -> frappe._dict:
	response = frappe._dict(modified=doc.modified, modified_by=doc.modified_by)
	summary = _summary_from_rows(doc.pod_files)
	if summary.total_files <= LARGE_BATCH_THRESHOLD:
		_add_doc_snapshot(response, doc, include_rows=True)
	return response


def _add_doc_snapshot(payload: frappe._dict, doc: TripPODImport, include_rows: bool) -> None:
	doc_snapshot = doc.as_dict()
	if not include_rows:
		doc_snapshot["pod_files"] = []
	payload.doc = doc_snapshot


def _has_running_job(doc: TripPODImport) -> bool:
	return _doc_get(doc, "scan_status", JOB_STATUS_PENDING) in {
		JOB_STATUS_QUEUED,
		JOB_STATUS_RUNNING,
	} or _doc_get(doc, "import_status", JOB_STATUS_PENDING) in {
		JOB_STATUS_QUEUED,
		JOB_STATUS_RUNNING,
	}


def _get_source_file_payload(
	doc: TripPODImport, row, source_files: dict[str, Document]
) -> tuple[str, bytes, int]:
	source_path = cstr(getattr(row, "source_path", "")).strip()
	if source_path:
		file_path = _validate_server_source_file(source_path)
		return (
			cstr(getattr(row, "file_name", "")).strip() or file_path.name,
			file_path.read_bytes(),
			1,
		)

	source_file = source_files.get(cstr(row.pod_file).strip()) or _get_attached_file_doc(
		doc, row.pod_file
	)
	if not source_file:
		raise frappe.ValidationError(
			_("Could not find the uploaded PDF for {0}.").format(row.file_name or row.pod_file)
		)

	return (
		row.file_name or source_file.file_name,
		source_file.get_content(),
		cint(source_file.is_private),
	)


def _get_allowed_server_base_path() -> Path:
	configured_path = cstr(getattr(frappe.conf, "trip_pod_import_allowed_base_path", "")).strip()
	base_path = Path(configured_path) if configured_path else Path(
		get_site_path("private", "files", "trip_pod_imports")
	)
	return base_path.expanduser().resolve()


def _validate_server_source_directory(source_path: str | None) -> Path:
	if not cstr(source_path).strip():
		frappe.throw(_("Please enter a server folder path before scanning."))

	resolved_path = _ensure_path_within_allowed_base(source_path)
	if not resolved_path.exists():
		frappe.throw(_("Server folder not found: {0}").format(resolved_path))
	if not resolved_path.is_dir():
		frappe.throw(_("Server source path must be a folder: {0}").format(resolved_path))
	return resolved_path


def _validate_server_source_file(source_path: str) -> Path:
	resolved_path = _ensure_path_within_allowed_base(source_path)
	if not resolved_path.exists():
		raise frappe.ValidationError(_("Source file not found: {0}").format(resolved_path))
	if not resolved_path.is_file():
		raise frappe.ValidationError(_("Source path is not a file: {0}").format(resolved_path))
	return resolved_path


def _ensure_path_within_allowed_base(source_path: str | os.PathLike[str]) -> Path:
	base_path = _get_allowed_server_base_path()
	input_path = Path(source_path).expanduser()
	if not input_path.is_absolute():
		input_path = base_path / input_path
	resolved_path = input_path.resolve()

	try:
		resolved_path.relative_to(base_path)
	except ValueError as exc:
		frappe.throw(
			_("Path {0} is outside the allowed import base path {1}.").format(
				resolved_path, base_path
			)
		)
		raise exc

	return resolved_path


def _list_server_pdf_files(source_dir: Path) -> list[Path]:
	return sorted(path for path in source_dir.rglob("*") if path.is_file() and path.suffix.lower() == PDF_EXTENSION)


def _refresh_result_report(doc: TripPODImport) -> str:
	# V2 no longer keeps per-import CSV reports to avoid extra storage usage.
	_clear_result_report(doc)
	return ""


def _clear_result_report(doc: TripPODImport) -> None:
	if not _doc_has_field(doc, "result_report_file"):
		return

	existing_file_url = cstr(_doc_get(doc, "result_report_file", "")).strip()
	if existing_file_url:
		_delete_report_file(doc, existing_file_url)
	_doc_set(doc, "result_report_file", "")
	_doc_db_set(doc.doctype, doc.name, {"result_report_file": ""}, update_modified=False)


def _build_result_report_csv(rows: list[frappe._dict]) -> str:
	buffer = io.StringIO()
	writer = csv.writer(buffer)
	writer.writerow(
		[
			"File Name",
			"Source Path",
			"Reference No",
			"Matched Trip",
			"Status",
			"Message",
			"Imported On",
		]
	)
	for row in rows:
		writer.writerow(
			[
				row.file_name,
				row.source_path,
				row.reference_no,
				row.matched_trip,
				row.preview_status,
				row.status_message,
				row.imported_on,
			]
		)
	return buffer.getvalue()


def _delete_report_file(doc: TripPODImport, file_url: str) -> None:
	file_name = frappe.db.get_value(
		"File",
		{
			"attached_to_doctype": doc.doctype,
			"attached_to_name": doc.name,
			"file_url": file_url,
		},
		"name",
	)
	if not file_name:
		return
	try:
		frappe.delete_doc("File", file_name, force=True, ignore_permissions=True)
	except OSError:
		# Physical file already missing; clean up the dangling DB record
		frappe.db.delete("File", {"name": file_name})


def _delete_import_attachment(doc: TripPODImport, file_url: str) -> None:
	if not file_url:
		return
	_delete_report_file(doc, file_url)


def _delete_unused_import_pdf_attachments(
	doc: TripPODImport,
	keep_file_urls: set[str] | None = None,
) -> None:
	keep_file_urls = {
		cstr(file_url).strip()
		for file_url in (keep_file_urls or set())
		if cstr(file_url).strip()
	}
	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": doc.doctype, "attached_to_name": doc.name},
		fields=["name", "file_name", "file_url"],
	)
	for file_doc in files:
		file_url = cstr(file_doc.file_url).strip()
		if file_url in keep_file_urls:
			continue
		if os.path.splitext(cstr(file_doc.file_name or "").strip())[1].lower() != PDF_EXTENSION:
			continue
		try:
			frappe.delete_doc("File", file_doc.name, force=True, ignore_permissions=True)
		except OSError:
			frappe.db.delete("File", {"name": file_doc.name})


def _get_pod_date_requirements(trip_type: str) -> tuple[bool, bool]:
	"""Return (require_arrival, require_release) based on Trip Settings field visibility.

	Mirrors the client-side isVisible() check in _pod_do_upload() in trip.js:
	- Field listed with is_visible=0 → not required
	- Field not listed or is_visible=1 → required (default visible)
	- No Trip Settings doc for this trip_type → both required
	"""
	def _field_required(doc, fieldname: str) -> bool:
		for row in doc.trip_field_settings:
			if row.fieldname == fieldname:
				return bool(row.is_visible)
		return True

	if not trip_type or not frappe.db.exists("Trip Settings", trip_type):
		return True, True
	doc = frappe.get_cached_doc("Trip Settings", trip_type)
	return _field_required(doc, "arrival_date_time"), _field_required(doc, "release_date_time")
