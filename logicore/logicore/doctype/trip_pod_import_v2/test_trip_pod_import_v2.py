# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

from __future__ import annotations

import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import frappe
from pypdf import PdfWriter

from logicore.logicore.doctype.trip_pod_import_v2 import trip_pod_import_v2


class TestTripPODImportV2(TestCase):
	def setUp(self):
		self.translation_patcher = patch.object(trip_pod_import_v2, "_", side_effect=lambda message: message)
		self.throw_patcher = patch.object(
			trip_pod_import_v2.frappe,
			"throw",
			side_effect=lambda message, exc=frappe.ValidationError, **kwargs: (_ for _ in ()).throw(exc(message)),
		)
		self.translation_patcher.start()
		self.throw_patcher.start()

	def tearDown(self):
		self.throw_patcher.stop()
		self.translation_patcher.stop()

	def _make_pdf_bytes(self, page_count: int = 1) -> bytes:
		writer = PdfWriter()
		for _index in range(page_count):
			writer.add_blank_page(width=72, height=72)

		buffer = io.BytesIO()
		writer.write(buffer)
		return buffer.getvalue()

	def test_coerce_local_preview_files_sorts_by_file_name(self):
		files = [
			{"client_row_key": "row_2", "file_name": "b-file.pdf"},
			{"client_row_key": "row_1", "file_name": "a-file.pdf"},
		]

		rows = trip_pod_import_v2._coerce_local_preview_files(files)

		self.assertEqual([row.client_row_key for row in rows], ["row_1", "row_2"])

	def test_extract_reference_no_uses_last_hyphenated_part(self):
		self.assertEqual(
			trip_pod_import_v2._extract_reference_no("16-03-2026-12-42-31-602781.pdf"),
			"602781",
		)
		self.assertIsNone(trip_pod_import_v2._extract_reference_no("invalid.pdf"))

	def test_ensure_path_within_allowed_base_accepts_relative_subpath(self):
		with TemporaryDirectory() as temp_dir:
			base_path = Path(temp_dir).resolve()
			target_dir = base_path / "nested" / "folder"
			target_dir.mkdir(parents=True)

			with patch.object(
				trip_pod_import_v2,
				"_get_allowed_server_base_path",
				return_value=base_path,
			):
				resolved = trip_pod_import_v2._ensure_path_within_allowed_base("nested/folder")

			self.assertEqual(resolved, target_dir)

	def test_ensure_path_within_allowed_base_rejects_outside_paths(self):
		with TemporaryDirectory() as temp_dir:
			base_path = Path(temp_dir).resolve()

			with patch.object(
				trip_pod_import_v2,
				"_get_allowed_server_base_path",
				return_value=base_path,
			):
				with self.assertRaises(frappe.ValidationError):
					trip_pod_import_v2._ensure_path_within_allowed_base("/tmp/outside-folder")

	def test_evaluate_file_entries_bulk_matches_and_duplicate_targets(self):
		entries = [
			frappe._dict(client_row_key="row_1", file_name="16-03-2026-12-42-31-111.pdf", pod_file="/files/111.pdf"),
			frappe._dict(client_row_key="row_2", file_name="16-03-2026-12-42-31-444.pdf", pod_file="/files/444.pdf"),
			frappe._dict(client_row_key="row_3", file_name="16-03-2026-12-42-31-222.pdf", pod_file="/files/222.pdf"),
			frappe._dict(client_row_key="row_4", file_name="16-03-2026-12-42-31-333.pdf", pod_file="/files/333.pdf"),
			frappe._dict(
				client_row_key="row_5",
				file_name="16-03-2026-12-42-31-555.pdf",
				pod_file="/files/555.pdf",
				preview_status=trip_pod_import_v2.IMPORTED_STATUS,
				matched_trip="TRIP-5",
			),
			frappe._dict(client_row_key="row_6", file_name="notes.txt", pod_file="/files/notes.txt"),
		]
		trip_rows = [
			frappe._dict(name="TRIP-1", tcntrip_no="111"),
			frappe._dict(name="TRIP-1", tcntrip_no="444"),
			frappe._dict(name="TRIP-3A", tcntrip_no="333"),
			frappe._dict(name="TRIP-3B", tcntrip_no="333"),
			frappe._dict(name="TRIP-5", tcntrip_no="555"),
		]

		with patch.object(trip_pod_import_v2.frappe, "get_all", return_value=trip_rows) as mocked_get_all:
			preview = trip_pod_import_v2._evaluate_file_entries(entries, "Market")

		self.assertEqual(mocked_get_all.call_count, 1)
		statuses = {row.file_name: row.preview_status for row in preview.rows}
		self.assertEqual(statuses["16-03-2026-12-42-31-111.pdf"], trip_pod_import_v2.DUPLICATE_TARGET_STATUS)
		self.assertEqual(statuses["16-03-2026-12-42-31-444.pdf"], trip_pod_import_v2.DUPLICATE_TARGET_STATUS)
		self.assertEqual(statuses["16-03-2026-12-42-31-222.pdf"], trip_pod_import_v2.NO_MATCH_STATUS)
		self.assertEqual(statuses["16-03-2026-12-42-31-333.pdf"], trip_pod_import_v2.MULTIPLE_MATCHES_STATUS)
		self.assertEqual(statuses["16-03-2026-12-42-31-555.pdf"], trip_pod_import_v2.IMPORTED_STATUS)
		self.assertEqual(statuses["notes.txt"], trip_pod_import_v2.INVALID_FILE_STATUS)
		self.assertEqual(preview.summary.total_files, 6)
		self.assertEqual(preview.summary.imported_files, 1)
		self.assertEqual(preview.summary.unmatched_files, 1)
		self.assertEqual(preview.summary.duplicate_match_files, 1)
		self.assertEqual(preview.summary.duplicate_target_files, 2)
		self.assertEqual(preview.summary.invalid_files, 1)
		self.assertEqual(
			{row.file_name: row.client_row_key for row in preview.rows},
			{
				"16-03-2026-12-42-31-111.pdf": "row_1",
				"16-03-2026-12-42-31-444.pdf": "row_2",
				"16-03-2026-12-42-31-222.pdf": "row_3",
				"16-03-2026-12-42-31-333.pdf": "row_4",
				"16-03-2026-12-42-31-555.pdf": "row_5",
				"notes.txt": "row_6",
			},
		)

	def test_compress_pdf_bytes_uses_smaller_valid_output(self):
		original_bytes = self._make_pdf_bytes(page_count=3)
		compressed_bytes = self._make_pdf_bytes(page_count=1)

		with patch.object(
			trip_pod_import_v2,
			"_run_ghostscript_compression",
			return_value=compressed_bytes,
		):
			result = trip_pod_import_v2._compress_pdf_bytes(original_bytes)

		self.assertEqual(result, compressed_bytes)

	def test_compress_pdf_bytes_tries_stronger_profile_for_50_percent_target(self):
		original_bytes = self._make_pdf_bytes(page_count=4)
		first_pass_bytes = self._make_pdf_bytes(page_count=3)
		second_pass_bytes = self._make_pdf_bytes(page_count=1)

		def fake_compress(_pdf_bytes, profile):
			if profile == "/ebook":
				return first_pass_bytes
			if profile == "/screen":
				return second_pass_bytes
			raise AssertionError(f"Unexpected profile: {profile}")

		with patch.object(
			trip_pod_import_v2,
			"_run_ghostscript_compression",
			side_effect=fake_compress,
		):
			result = trip_pod_import_v2._compress_pdf_bytes(original_bytes)

		self.assertEqual(result, second_pass_bytes)

	def test_compress_pdf_bytes_keeps_original_when_output_is_not_smaller(self):
		original_bytes = self._make_pdf_bytes(page_count=1)
		larger_bytes = self._make_pdf_bytes(page_count=3)

		with patch.object(
			trip_pod_import_v2,
			"_run_ghostscript_compression",
			return_value=larger_bytes,
		):
			result = trip_pod_import_v2._compress_pdf_bytes(original_bytes)

		self.assertEqual(result, original_bytes)

	def test_compress_pdf_bytes_keeps_original_when_ghostscript_fails(self):
		original_bytes = self._make_pdf_bytes(page_count=2)

		with patch.object(
			trip_pod_import_v2,
			"_run_ghostscript_compression",
			side_effect=RuntimeError("ghostscript failed"),
		):
			result = trip_pod_import_v2._compress_pdf_bytes(original_bytes)

		self.assertEqual(result, original_bytes)

	def test_compress_pdf_bytes_keeps_original_when_output_is_unreadable(self):
		original_bytes = self._make_pdf_bytes(page_count=3)
		unreadable_bytes = b"not-a-real-pdf"

		with patch.object(
			trip_pod_import_v2,
			"_run_ghostscript_compression",
			return_value=unreadable_bytes,
		):
			result = trip_pod_import_v2._compress_pdf_bytes(original_bytes)

		self.assertEqual(result, original_bytes)

	def test_stage_local_folder_trip_pods_saves_original_when_compression_falls_back(self):
		original_bytes = self._make_pdf_bytes(page_count=2)
		row = frappe._dict(
			idx=1,
			client_row_key="row_1",
			file_name="16-03-2026-12-42-31-111.pdf",
			matched_trip="TRIP-1",
			can_import=1,
			pod_file="",
			source_path="",
			preview_status="",
			status_message="",
			error_trace="",
		)

		class FakeDoc:
			doctype = "Trip POD Import V2"
			name = "POD-IMP-2026-00001"
			trip_type = "Market"

			def __init__(self, pod_files):
				self.pod_files = pod_files
				self.scan_status = ""
				self.import_status = ""

			def save(self, ignore_permissions=False):
				self.saved_with_ignore_permissions = ignore_permissions

		doc = FakeDoc([row])
		uploaded_file = SimpleNamespace(
			filename=row.file_name,
			stream=io.BytesIO(original_bytes),
		)
		fake_db = SimpleNamespace(
			savepoint=lambda *args, **kwargs: None,
			release_savepoint=lambda *args, **kwargs: None,
			commit=lambda *args, **kwargs: None,
			rollback=lambda *args, **kwargs: None,
		)
		fake_frappe = SimpleNamespace(
			_dict=frappe._dict,
			db=fake_db,
			get_traceback=lambda: "",
		)

		with (
			patch.object(trip_pod_import_v2, "frappe", fake_frappe),
			patch.object(trip_pod_import_v2, "_get_import_doc", return_value=doc),
			patch.object(trip_pod_import_v2, "_get_effective_trip_type", return_value="Market"),
			patch.object(trip_pod_import_v2, "_get_uploaded_batch_files", return_value={"row_1": uploaded_file}),
			patch.object(trip_pod_import_v2, "_delete_import_attachment"),
			patch.object(
				trip_pod_import_v2,
				"_delete_unused_import_pdf_attachments",
			),
			patch.object(trip_pod_import_v2, "_clear_result_report"),
			patch.object(trip_pod_import_v2, "_run_ghostscript_compression", side_effect=RuntimeError("boom")),
			patch.object(
				trip_pod_import_v2,
				"save_file",
				return_value=frappe._dict(file_url="/private/files/111.pdf"),
			) as mocked_save_file,
			patch.object(
				trip_pod_import_v2,
				"_build_client_payload",
				return_value=frappe._dict(summary=frappe._dict(importable_files=1)),
			),
		):
			payload = trip_pod_import_v2.stage_local_folder_trip_pods(
				docname=doc.name,
				trip_type="Market",
				batch_rows=[{"client_row_key": "row_1"}],
			)

		self.assertEqual(mocked_save_file.call_args.args[1], original_bytes)
		self.assertEqual(row.pod_file, "/private/files/111.pdf")
		self.assertEqual(row.preview_status, trip_pod_import_v2.READY_STATUS)
		self.assertEqual(payload.staged_count, 1)
