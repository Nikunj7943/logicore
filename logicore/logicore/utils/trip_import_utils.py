# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

# Backward compat alias — kept for any old code still importing this
TARGET_DOCTYPE = "Import Template"

import csv
import io
import json
import os
import re
from datetime import datetime as _datetime
from typing import Any

from dateutil import parser
from dateutil.parser import ParserError

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, get_datetime, getdate, now_datetime
from frappe.utils.file_manager import save_file

TEMPLATE_DOCTYPE = "Import Template"
LOG_DOCTYPE = "Import Log"
CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
LAYOUT_FIELD_TYPES = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"Fold",
	"Heading",
	"HTML",
	"Button",
	"Image",
	"Attach Image",
	"Signature",
	"Geolocation",
	"Barcode",
	"Break",
	"Table",
	"Table MultiSelect",
}
INTERNAL_FIELDNAMES = {
	"doctype",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"parent",
	"parentfield",
	"parenttype",
	"idx",
	"_assign",
	"_comments",
	"_liked_by",
	"_seen",
	"_user_tags",
}
IMPORT_MODES = {
	"Update Existing Only",
	"Create New Only",
	"Update or Create",
}


def _normalize_header(value: str | None) -> str:
	return " ".join(cstr(value).strip().split()).casefold()


def get_importable_fields(doctype: str) -> list[frappe._dict]:
	"""Returns all fields eligible for import for the given doctype."""
	meta = frappe.get_meta(doctype)
	fields = [
		frappe._dict(
			fieldname="name",
			label=_("ID"),
			fieldtype="Data",
			reqd=0,
			read_only=1,
			options="",
		)
	]
	for df in meta.fields:
		if not df.fieldname or df.fieldname in INTERNAL_FIELDNAMES:
			continue
		if df.fieldtype in LAYOUT_FIELD_TYPES or df.read_only:
			continue
		fields.append(
			frappe._dict(
				fieldname=df.fieldname,
				label=df.label or df.fieldname,
				fieldtype=df.fieldtype,
				reqd=1 if df.reqd else 0,
				read_only=1 if df.read_only else 0,
				options=df.options or "",
			)
		)
	return fields


def get_trip_importable_fields() -> list[frappe._dict]:
	"""Backward-compat wrapper — returns importable fields for Trip."""
	return get_importable_fields("Trip")


def get_importable_field_map(doctype: str) -> dict[str, frappe._dict]:
	return {f.fieldname: f for f in get_importable_fields(doctype)}


def get_trip_importable_field_map() -> dict[str, frappe._dict]:
	"""Backward-compat wrapper."""
	return get_importable_field_map("Trip")


def parse_columns_json(columns_json: str | list[dict[str, Any]] | None) -> list[dict[str, Any]]:
	if not columns_json:
		return []
	if isinstance(columns_json, str):
		try:
			data = json.loads(columns_json)
		except Exception:
			frappe.throw(_("Columns JSON is not valid JSON."), title=_("Invalid Template"))
	else:
		data = columns_json
	if not isinstance(data, list):
		frappe.throw(_("Columns JSON must be a list of column definitions."), title=_("Invalid Template"))
	return [frappe._dict(row or {}) for row in data]


def normalize_template_columns(
	columns_json: str | list[dict[str, Any]] | None,
	match_field: str,
	default_import_mode: str,
	target_doctype: str = "Trip",
) -> list[dict[str, Any]]:
	field_map = get_importable_field_map(target_doctype)
	if match_field and match_field not in field_map:
		frappe.throw(
			_("Match Field '{0}' is not a valid field on {1}.").format(match_field, target_doctype),
			title=_("Invalid Template"),
		)

	raw_columns = parse_columns_json(columns_json)
	normalized: list[dict[str, Any]] = []
	seen_headers: set[str] = set()
	seen_fields: set[str] = set()

	for idx, row in enumerate(raw_columns, start=1):
		csv_header = cstr(row.get("csv_header")).strip()
		fieldname = cstr(row.get("fieldname")).strip()
		if not csv_header and not fieldname:
			continue
		if not csv_header:
			frappe.throw(_("Column #{0}: CSV Header is required.").format(idx), title=_("Invalid Template"))
		if not fieldname:
			frappe.throw(_("Column #{0}: Field is required.").format(idx), title=_("Invalid Template"))
		if fieldname not in field_map:
			frappe.throw(
				_("Column #{0}: Field '{1}' is not importable on {2}.").format(
					idx, frappe.bold(fieldname), target_doctype
				),
				title=_("Invalid Template"),
			)
		header_key = _normalize_header(csv_header)
		if header_key in seen_headers:
			frappe.throw(
				_("CSV Header '{0}' is duplicated.").format(frappe.bold(csv_header)),
				title=_("Invalid Template"),
			)
		if fieldname in seen_fields:
			frappe.throw(
				_("Field '{0}' is duplicated.").format(frappe.bold(fieldname)),
				title=_("Invalid Template"),
			)
		field_info = field_map[fieldname]
		normalized.append(
			{
				"idx": len(normalized) + 1,
				"csv_header": csv_header,
				"fieldname": fieldname,
				"label": field_info.label,
				"fieldtype": field_info.fieldtype,
				"required": 1 if cint(row.get("required")) else 0,
				"default_value": row.get("default_value") if row.get("default_value") is not None else "",
				"is_match_key": 1 if row.get("is_match_key") else 0,
			}
		)
		seen_headers.add(header_key)
		seen_fields.add(fieldname)

	# Ensure primary match_field column exists (backward compat — old templates without is_match_key)
	if match_field:
		match_present = next((c for c in normalized if c["fieldname"] == match_field), None)
		if not match_present:
			field_info = field_map[match_field]
			normalized.insert(
				0,
				{
					"idx": 1,
					"csv_header": field_info.label or match_field,
					"fieldname": match_field,
					"label": field_info.label,
					"fieldtype": field_info.fieldtype,
					"required": 1,
					"default_value": "",
					"is_match_key": 1,
				},
			)
			for idx, row in enumerate(normalized, start=1):
				row["idx"] = idx
			match_present = normalized[0]

		if default_import_mode in {"Update Existing Only", "Update or Create"}:
			match_present["required"] = 1
			# Ensure the primary match_field column is marked as match key
			if not match_present.get("is_match_key"):
				match_present["is_match_key"] = 1

	if not normalized:
		frappe.throw(_("At least one column is required."), title=_("Invalid Template"))

	return normalized


def get_template_doc(template_name: str):
	if not template_name:
		frappe.throw(_("Template is required."))
	doc = frappe.get_doc(TEMPLATE_DOCTYPE, template_name)
	doc.check_permission("read")
	return doc


def get_log_doc(log_name: str, permtype: str = "read"):
	if not log_name:
		frappe.throw(_("Log is required."))
	doc = frappe.get_doc(LOG_DOCTYPE, log_name)
	doc.check_permission(permtype)
	return doc


def _read_csv_rows(file_url: str) -> list[list[str]]:
	if not file_url:
		frappe.throw(_("CSV file is required."))
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	full_path = file_doc.get_full_path()
	extension = os.path.splitext(file_doc.file_name or file_doc.file_url or "")[1].lower()
	if extension != ".csv":
		frappe.throw(_("Only CSV files are supported."), title=_("Unsupported File"))
	last_error = None
	for encoding in CSV_ENCODINGS:
		try:
			with open(full_path, "r", encoding=encoding, errors="strict", newline="") as handle:
				return list(csv.reader(handle))
		except UnicodeDecodeError as exc:
			last_error = exc
			continue
	if last_error:
		raise last_error
	return []


def _normalize_select_options(options: Any) -> list[str]:
	return [cstr(option).strip() for option in cstr(options or "").splitlines() if cstr(option).strip()]


def _strict_import_date(value: Any):
	if isinstance(value, _datetime):
		return value.date().isoformat()
	if hasattr(value, "isoformat") and not isinstance(value, str):
		return cstr(value.isoformat())

	text = cstr(value).strip()
	if not re.fullmatch(r"\d{2}-\d{2}-\d{4}", text):
		frappe.throw(
			_("Date '{0}' must be in dd-mm-yyyy format.").format(frappe.bold(text)),
			title=_("Invalid Date"),
		)
	try:
		return _datetime.strptime(text, "%d-%m-%Y").date().isoformat()
	except ValueError:
		frappe.throw(
			_("Date '{0}' is not valid.").format(frappe.bold(text)),
			title=_("Invalid Date"),
		)


def _fieldtype_cast(value: Any, field_info: frappe._dict | str):
	if value in (None, ""):
		return ""
	if isinstance(field_info, str):
		field_info = frappe._dict(fieldtype=field_info, options="", label=field_info)
	fieldtype = cstr(field_info.get("fieldtype"))
	options = field_info.get("options")
	label = cstr(field_info.get("label") or field_info.get("fieldname") or fieldtype)
	if fieldtype in {"Data", "Small Text", "Text", "Long Text", "Text Editor", "Link", "Dynamic Link"}:
		return cstr(value).strip()
	if fieldtype == "Select":
		selected = cstr(value).strip()
		allowed = _normalize_select_options(options)
		if allowed and selected not in allowed:
			frappe.throw(
				_("'{0}' is not a valid option for {1}. Allowed values: {2}").format(
					frappe.bold(selected),
					frappe.bold(label),
					", ".join(allowed),
				),
				title=_("Invalid Option"),
			)
		return selected
	if fieldtype in {"Int", "Check"}:
		return cint(value)
	if fieldtype in {"Float", "Currency", "Percent"}:
		return flt(value)
	if fieldtype == "Date":
		return _strict_import_date(value)
	if fieldtype == "Datetime":
		if isinstance(value, _datetime):
			return value.strftime("%Y-%m-%d %H:%M:%S")
		try:
			return _datetime.fromisoformat(cstr(value)).strftime("%Y-%m-%d %H:%M:%S")
		except ValueError:
			try:
				return parser.parse(cstr(value), dayfirst=True).strftime("%Y-%m-%d %H:%M:%S")
			except ParserError:
				frappe.throw(
					_("{} is not a valid datetime string.").format(frappe.bold(cstr(value))),
					title=_("Invalid Date"),
				)
	return value


def _validate_link_value(field_info: frappe._dict, value: Any):
	if field_info.fieldtype != "Link" or value in (None, ""):
		return value
	if not frappe.db.exists(field_info.options, value):
		frappe.throw(
			_("{0} '{1}' was not found.").format(field_info.options or _("Linked record"), frappe.bold(cstr(value))),
			title=_("Invalid Link"),
		)
	return value


def _is_blank_row(row: list[Any]) -> bool:
	return all(cstr(cell).strip() == "" for cell in row)


def _get_csv_value(row: list[Any], index_map: dict[str, int], csv_header: str):
	idx = index_map.get(_normalize_header(csv_header))
	if idx is None or idx >= len(row):
		return ""
	return row[idx]


def _get_match_columns(columns: list[dict[str, Any]], match_field: str) -> list[dict[str, Any]]:
	"""Returns columns marked as match keys; falls back to match_field for old templates."""
	match_cols = [c for c in columns if cint(c.get("is_match_key"))]
	if not match_cols and match_field:
		match_cols = [c for c in columns if c["fieldname"] == match_field]
	return match_cols


def _build_preview_row(
	template_doc,
	columns: list[dict[str, Any]],
	header_index_map: dict[str, int],
	row: list[Any],
	row_number: int,
	import_mode: str,
) -> frappe._dict:
	target_doctype = cstr(template_doc.target_doctype).strip() or "Trip"
	field_map = get_importable_field_map(target_doctype)
	match_field = cstr(template_doc.match_field).strip()
	match_columns = _get_match_columns(columns, match_field)
	errors: list[str] = []

	# Build compound match filter — cast values to DB-compatible format
	match_filters: dict[str, Any] = {}
	for mc in match_columns:
		val = cstr(_get_csv_value(row, header_index_map, mc["csv_header"])).strip()
		if not val:
			errors.append(_("Match key '{0}' value is missing.").format(mc["csv_header"]))
		else:
			try:
				match_filters[mc["fieldname"]] = _fieldtype_cast(val, field_map[mc["fieldname"]])
			except Exception:
				match_filters[mc["fieldname"]] = val

	existing_name = ""
	if match_filters and not errors:
		if len(match_filters) == 1 and "name" in match_filters:
			existing_name = (
				match_filters["name"] if frappe.db.exists(target_doctype, match_filters["name"]) else ""
			)
		else:
			existing_name = frappe.db.get_value(target_doctype, match_filters, "name") or ""

	status = "Ready"
	action = "Create"
	if import_mode == "Update Existing Only":
		action = "Update"
		if not existing_name and match_filters:
			errors.append(
				_("Record not found for {0}.").format(
					", ".join(f"{k}={v}" for k, v in match_filters.items())
				)
			)
	elif import_mode == "Create New Only":
		action = "Create"
		if existing_name:
			errors.append(
				_("Record already exists for {0}.").format(
					", ".join(f"{k}={v}" for k, v in match_filters.items())
				)
			)
	elif import_mode == "Update or Create":
		action = "Update" if existing_name else "Create"

	for column in columns:
		raw_value = _get_csv_value(row, header_index_map, column["csv_header"])
		if raw_value in (None, "") and column.get("default_value") not in (None, ""):
			raw_value = column.get("default_value")
		if cint(column.get("required")) and raw_value in (None, ""):
			errors.append(_("'{0}' is required.").format(column["csv_header"]))
			continue
		if raw_value in (None, ""):
			continue
		try:
			casted = _fieldtype_cast(raw_value, field_map[column["fieldname"]])
			_validate_link_value(field_map[column["fieldname"]], casted)
		except Exception as exc:
			errors.append(cstr(exc))

	if errors:
		status = "Issue"
		action = "Blocked"

	return frappe._dict(
		row_number=row_number,
		match_filters=match_filters,
		existing_name=existing_name,
		action=action,
		status=status,
		message="; ".join(dict.fromkeys(errors)) if errors else _("Ready to import."),
	)


def build_preview_payload(template_doc, file_url: str, import_mode: str) -> frappe._dict:
	if import_mode not in IMPORT_MODES:
		frappe.throw(_("Invalid import mode."))
	columns = parse_columns_json(template_doc.columns_json)
	rows = _read_csv_rows(file_url)
	if not rows:
		frappe.throw(_("The uploaded CSV file is empty."))

	headers = [cstr(v).strip() for v in rows[0]]
	header_keys = [_normalize_header(v) for v in headers]
	duplicate_headers = sorted({headers[i] for i, key in enumerate(header_keys) if key and header_keys.count(key) > 1})
	missing_headers = [
		column["csv_header"]
		for column in columns
		if cint(column.get("required")) and _normalize_header(column["csv_header"]) not in header_keys
	]

	blocking_errors = []
	if duplicate_headers:
		blocking_errors.append(_("Duplicate CSV headers found: {0}").format(", ".join(duplicate_headers)))
	if missing_headers:
		blocking_errors.append(_("Missing mandatory headers: {0}").format(", ".join(missing_headers)))

	header_index_map = {_normalize_header(label): idx for idx, label in enumerate(headers)}
	data_rows = rows[1:]
	preview_rows = []
	rows_ready = 0
	rows_with_issues = 0
	create_rows = 0
	update_rows = 0

	for row_number, row in enumerate(data_rows, start=2):
		if _is_blank_row(row):
			if len(preview_rows) < 25:
				preview_rows.append(
					frappe._dict(
						row_number=row_number,
						match_filters={},
						existing_name="",
						action="",
						status="Ignored",
						message=_("Blank row, skipped."),
					)
				)
			continue
		preview = _build_preview_row(template_doc, columns, header_index_map, row, row_number, import_mode)
		if len(preview_rows) < 25:
			preview_rows.append(preview)
		if preview.status == "Issue":
			rows_with_issues += 1
		else:
			rows_ready += 1
		if preview.action == "Create":
			create_rows += 1
		elif preview.action == "Update":
			update_rows += 1

	matched_headers = sum(1 for column in columns if _normalize_header(column["csv_header"]) in header_keys)

	payload = frappe._dict(
		headers=headers,
		columns=columns,
		preview_rows=preview_rows,
		total_rows=len(data_rows),
		matched_headers=matched_headers,
		missing_headers=missing_headers,
		duplicate_headers=duplicate_headers,
		rows_ready=rows_ready,
		rows_with_issues=rows_with_issues,
		create_rows=create_rows,
		update_rows=update_rows,
		blocking_errors=blocking_errors,
		can_import=not blocking_errors,
	)
	return payload


def create_validated_log(template_doc, file_url: str, import_mode: str, company: str | None, preview_payload) -> Any:
	log = frappe.get_doc(
		{
			"doctype": LOG_DOCTYPE,
			"template": template_doc.name,
			"template_name": template_doc.template_name,
			"company": company or template_doc.get("company"),
			"import_mode": import_mode,
			"status": "Validated",
			"uploaded_file": file_url,
			"preview_json": json.dumps(preview_payload, indent=2, default=str),
			"summary_json": json.dumps(
				{
					"total_rows": preview_payload.total_rows,
					"rows_ready": preview_payload.rows_ready,
					"rows_with_issues": preview_payload.rows_with_issues,
					"create_rows": preview_payload.create_rows,
					"update_rows": preview_payload.update_rows,
				},
				indent=2,
			),
			"row_result_json": "[]",
			"total_rows": preview_payload.total_rows,
			"imported_by": frappe.session.user,
		}
	)
	log.insert(ignore_permissions=True)
	return log


def _apply_template_defaults(template_doc, values: dict[str, Any], *, for_create: bool):
	if for_create:
		company = template_doc.get("company")
		if company and not values.get("company"):
			values["company"] = company


def _apply_import_action(doc, import_action: str, action: str) -> str:
	"""Execute post-save action and return a human-readable action label for the log."""
	if import_action == "Submit After Update":
		if doc.docstatus != 0:
			frappe.throw(_("Only Draft documents can be submitted. '{0}' is not in Draft state.").format(doc.name))
		doc.submit()
		return action + " + Submit"
	elif import_action == "Cancel Document":
		if doc.docstatus != 1:
			frappe.throw(_("Only Submitted documents can be cancelled. '{0}' is not Submitted.").format(doc.name))
		doc.cancel()
		return "Cancel"
	return action


def process_import_log(log_doc) -> frappe._dict:
	template_doc = frappe.get_doc(TEMPLATE_DOCTYPE, log_doc.template)
	template_doc.check_permission("read")
	target_doctype = cstr(template_doc.target_doctype).strip() or "Trip"
	import_action = cstr(template_doc.get("import_action") or "None").strip()
	columns = parse_columns_json(template_doc.columns_json)
	rows = _read_csv_rows(log_doc.uploaded_file)
	headers = [cstr(v).strip() for v in rows[0]]
	header_index_map = {_normalize_header(label): idx for idx, label in enumerate(headers)}
	field_map = get_importable_field_map(target_doctype)
	import_mode = log_doc.import_mode

	log_doc.status = "Running"
	log_doc.started_at = now_datetime()
	log_doc.save(ignore_permissions=True)

	results = []
	failure_rows = []
	created_count = 0
	updated_count = 0
	failed_count = 0
	skipped_count = 0

	try:
		for row_number, row in enumerate(rows[1:], start=2):
			if _is_blank_row(row):
				skipped_count += 1
				results.append(
					{
						"row_number": row_number,
						"status": "Ignored",
						"action": "",
						"message": _("Blank row, skipped."),
						"record_name": "",
					}
				)
				continue
			preview = _build_preview_row(template_doc, columns, header_index_map, row, row_number, import_mode)
			if preview.status == "Issue":
				failed_count += 1
				result = {
					"row_number": row_number,
					"status": "Failed",
					"action": preview.action,
					"message": preview.message,
					"record_name": "",
				}
				results.append(result)
				failure_rows.append(result | {"row_data": row})
				continue

			values: dict[str, Any] = {}
			for column in columns:
				raw_value = _get_csv_value(row, header_index_map, column["csv_header"])
				if raw_value in (None, "") and column.get("default_value") not in (None, ""):
					raw_value = column.get("default_value")
				if raw_value in (None, ""):
					continue
				try:
					casted = _fieldtype_cast(raw_value, field_map[column["fieldname"]])
					casted = _validate_link_value(field_map[column["fieldname"]], casted)
				except Exception as exc:
					failed_count += 1
					result = {
						"row_number": row_number,
						"status": "Failed",
						"action": preview.action,
						"message": cstr(exc),
						"record_name": "",
					}
					results.append(result)
					failure_rows.append(result | {"row_data": row})
					values = {}
					break
				if column["fieldname"] == "name" and preview.action == "Create":
					continue
				values[column["fieldname"]] = casted
			if any(r["row_number"] == row_number and r["status"] == "Failed" for r in results):
				continue

			try:
				if import_action == "Cancel Document":
					# Cancel: only find existing doc, do not update fields
					if not preview.existing_name:
						raise Exception(_("Record not found to cancel."))
					doc = frappe.get_doc(target_doctype, preview.existing_name)
					final_action = _apply_import_action(doc, import_action, "Cancel")
					updated_count += 1
					results.append(
						{
							"row_number": row_number,
							"status": "Success",
							"action": final_action,
							"message": _("Record cancelled successfully."),
							"record_name": doc.name,
						}
					)
				elif preview.action == "Update":
					doc = frappe.get_doc(target_doctype, preview.existing_name)
					for fieldname, value in values.items():
						if value in ("", None) and not cint(template_doc.get("allow_blank_update")):
							continue
						doc.set(fieldname, value)
					doc.save(ignore_permissions=False)
					final_action = _apply_import_action(doc, import_action, "Update")
					updated_count += 1
					results.append(
						{
							"row_number": row_number,
							"status": "Success",
							"action": final_action,
							"message": _("Record updated successfully."),
							"record_name": doc.name,
						}
					)
				else:
					doc = frappe.get_doc({"doctype": target_doctype})
					_apply_template_defaults(template_doc, values, for_create=True)
					for fieldname, value in values.items():
						doc.set(fieldname, value)
					doc.insert(ignore_permissions=False)
					final_action = _apply_import_action(doc, import_action, "Create")
					created_count += 1
					results.append(
						{
							"row_number": row_number,
							"status": "Success",
							"action": final_action,
							"message": _("Record created successfully."),
							"record_name": doc.name,
						}
					)
			except Exception as exc:
				failed_count += 1
				results.append(
					{
						"row_number": row_number,
						"status": "Failed",
						"action": preview.action,
						"message": cstr(exc),
						"record_name": "",
					}
				)
				failure_rows.append({"row_number": row_number, "message": cstr(exc), "row_data": row})

		success_rows = created_count + updated_count
		summary = {
			"total_rows": len(rows) - 1,
			"success_rows": success_rows,
			"failed_rows": failed_count,
			"created_count": created_count,
			"updated_count": updated_count,
			"skipped_count": skipped_count,
		}

		error_file = ""
		if failure_rows:
			buffer = io.StringIO()
			writer = csv.writer(buffer)
			writer.writerow(["row_number", "message", *headers])
			for failure in failure_rows:
				writer.writerow([failure["row_number"], failure["message"], *(failure.get("row_data") or [])])
			file_doc = save_file(
				f"import_errors_{log_doc.name}.csv",
				buffer.getvalue().encode(),
				LOG_DOCTYPE,
				log_doc.name,
				is_private=0,
			)
			error_file = file_doc.file_url

		log_doc.status = "Completed With Errors" if failed_count else "Completed"
		log_doc.error_file = error_file
		log_doc.row_result_json = json.dumps(results, indent=2, default=str)
		log_doc.summary_json = json.dumps(summary, indent=2)
		log_doc.success_rows = success_rows
		log_doc.failed_rows = failed_count
		log_doc.created_count = created_count
		log_doc.updated_count = updated_count
		log_doc.skipped_count = skipped_count
		log_doc.finished_at = now_datetime()
		log_doc.save(ignore_permissions=True)

		template_doc.last_used_on = now_datetime()
		template_doc.last_used_by = frappe.session.user
		template_doc.save(ignore_permissions=True)

		return frappe._dict(summary | {"log_name": log_doc.name, "error_file": error_file, "results": results[:25]})
	except Exception:
		log_doc.status = "Failed"
		log_doc.finished_at = now_datetime()
		log_doc.row_result_json = json.dumps(results, indent=2, default=str)
		log_doc.summary_json = json.dumps(
			{
				"total_rows": len(rows) - 1,
				"success_rows": created_count + updated_count,
				"failed_rows": failed_count,
				"created_count": created_count,
				"updated_count": updated_count,
				"skipped_count": skipped_count,
			},
			indent=2,
		)
		log_doc.save(ignore_permissions=True)
		raise


def build_template_csv_content(template_doc) -> bytes:
	columns = parse_columns_json(template_doc.columns_json)
	buffer = io.StringIO()
	writer = csv.writer(buffer)
	writer.writerow([column["csv_header"] for column in columns])
	return buffer.getvalue().encode("utf-8")
