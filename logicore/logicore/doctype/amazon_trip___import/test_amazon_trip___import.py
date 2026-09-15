# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

from datetime import datetime

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime
from frappe.utils.file_manager import save_file
from frappe.utils.xlsxutils import make_xlsx

from logicore.logicore.doctype.amazon_trip___import.amazon_trip___import import (
	_prepare_import_data,
	_run_import_job,
)


EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


def _make_import_doc(file_url: str) -> "frappe.model.document.Document":
	return frappe.get_doc(
		{"doctype": "Amazon trip - Import", "file_selection": file_url}
	).insert(ignore_permissions=True)


class IntegrationTestAmazontripImport(IntegrationTestCase):
	"""End-to-end tests for the async import pipeline.

	Imports are driven by directly invoking the worker function synchronously —
	this bypasses the RQ enqueue step but exercises the same parse + bulk upsert
	logic that runs in production.
	"""

	def test_csv_preview_detects_unknown_and_missing_required_columns(self):
		content = b"company_name,unknown_column\nLogiCore,ABC\n"
		file_doc = save_file("amazon_trip_preview.csv", content, None, None, is_private=1)

		preview = _prepare_import_data(file_doc.file_url)

		self.assertEqual(preview.summary.total_rows, 1)
		self.assertEqual(preview.summary.detected_columns, 2)
		self.assertEqual(preview.summary.unknown_columns, 1)
		self.assertEqual(len(preview.data), 1)
		self.assertTrue(any("Unknown column" in warning.message for warning in preview.warnings))
		self.assertTrue(any("Missing required column" in warning.message for warning in preview.warnings))

	def test_xlsx_preview_reads_rows(self):
		workbook = make_xlsx(
			[
				["vr_id", "company_name", "customer", "trip_date"],
				["VR-TEST-001", "LogiCore", "Test Customer", "2026-03-20"],
			],
			"AmazonTripPreview",
		)
		file_doc = save_file(
			"amazon_trip_preview.xlsx",
			workbook.getvalue(),
			None,
			None,
			is_private=1,
		)

		preview = _prepare_import_data(file_doc.file_url)

		self.assertEqual(preview.summary.total_rows, 1)
		self.assertEqual(preview.summary.detected_columns, 4)
		self.assertEqual(preview.summary.unknown_columns, 0)
		# preview.data row shape: [import_action, <mapped columns in header order>]
		self.assertIn(preview.data[0][0], ("Create New", "Update Existing"))
		self.assertEqual(preview.data[0][1], "VR-TEST-001")
		self.assertEqual(preview.data[0][2], "LogiCore")

	def test_prepare_import_data_marks_rows_with_missing_required_values(self):
		content = b"vr_id,company_name,customer,trip_date\nVR-TEST-002,LogiCore,,2026-03-20\n"
		file_doc = save_file("amazon_trip_row_errors.csv", content, None, None, is_private=1)

		parsed = _prepare_import_data(file_doc.file_url)

		self.assertEqual(parsed.summary.total_rows, 1)
		self.assertEqual(parsed.summary.importable_rows, 0)
		self.assertEqual(parsed.summary.failed_rows, 1)
		self.assertFalse(parsed.can_import)
		self.assertTrue(parsed.import_rows[0].errors)

	def test_import_uses_prepared_field_values(self):
		content = (
			b"vr_id,company_name,customer,trip_date\n"
			b"VR-TEST-003,LogiCore,Test Customer,2026-03-20\n"
		)
		file_doc = save_file("amazon_trip_import_ok.csv", content, None, None, is_private=1)

		parsed = _prepare_import_data(file_doc.file_url, create_missing_select_options=True)
		self.assertEqual(parsed.summary.importable_rows, 1)
		self.assertEqual(parsed.import_rows[0].field_values["company_name"], "LogiCore")
		self.assertEqual(parsed.import_rows[0].field_values["customer"], "Test Customer")

		import_doc = _make_import_doc(file_doc.file_url)
		_run_import_job(import_doc.name, file_doc.file_url, frappe.session.user)

		import_doc.reload()
		self.assertEqual(import_doc.job_status, "Completed")
		self.assertEqual(import_doc.inserted_count + import_doc.updated_count, 1)
		self.assertEqual(import_doc.failed_count, 0)

		# Verify the Amazon Trip actually exists with the imported VR ID.
		existing = frappe.get_all(
			"Amazon Trip", filters={"vr_id": "VR-TEST-003"}, pluck="name"
		)
		self.assertEqual(len(existing), 1)

	def test_import_preserves_excel_start_and_end_timestamps(self):
		content = (
			b"vr_id,company_name,customer,trip_date,start_date,end_date\n"
			b"VR-TEST-004,LogiCore,Test Customer,2026-03-20,"
			b"12/27/2025 20:00:00 IST,12/27/2025 23:30:00 IST\n"
		)
		file_doc = save_file("amazon_trip_import_datetime.csv", content, None, None, is_private=1)

		parsed = _prepare_import_data(file_doc.file_url, create_missing_select_options=True)
		row_values = parsed.import_rows[0].field_values

		self.assertEqual(parsed.summary.importable_rows, 1)
		self.assertIsInstance(row_values["start_date"], datetime)
		self.assertIsInstance(row_values["end_date"], datetime)
		self.assertEqual(row_values["start_date"].hour, 20)
		self.assertEqual(row_values["end_date"].hour, 23)

		import_doc = _make_import_doc(file_doc.file_url)
		_run_import_job(import_doc.name, file_doc.file_url, frappe.session.user)

		import_doc.reload()
		self.assertEqual(import_doc.job_status, "Completed")
		self.assertEqual(import_doc.inserted_count + import_doc.updated_count, 1)
		self.assertEqual(import_doc.failed_count, 0)

		imported = frappe.get_all(
			"Amazon Trip",
			filters={"vr_id": "VR-TEST-004"},
			fields=["name", "start_date", "end_date"],
		)
		self.assertEqual(len(imported), 1)
		self.assertEqual(get_datetime(imported[0].start_date).strftime("%Y-%m-%d %H:%M:%S"), "2025-12-27 20:00:00")
		self.assertEqual(get_datetime(imported[0].end_date).strftime("%Y-%m-%d %H:%M:%S"), "2025-12-27 23:30:00")
