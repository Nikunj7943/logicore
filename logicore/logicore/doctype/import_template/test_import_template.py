# Copyright (c) 2026, LogiCore and Contributors

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from logicore.logicore.utils.import_utils import (
	_fieldtype_cast,
	_strict_import_date,
	_validate_link_value,
)


class TestImportTemplate(FrappeTestCase):
	def test_date_import_requires_dd_mm_yyyy(self):
		self.assertEqual(_fieldtype_cast("05-01-2026", "Date"), "2026-01-05")
		self.assertEqual(_strict_import_date("31-05-2026"), "2026-05-31")
		with self.assertRaises(frappe.ValidationError):
			_strict_import_date("2026-07-08")

	def test_select_import_rejects_invalid_option(self):
		field_info = frappe._dict(fieldtype="Select", options="Cash\nBank Transfer", label="Payment Mode")
		self.assertEqual(_fieldtype_cast("Bank Transfer", field_info), "Bank Transfer")
		with self.assertRaises(frappe.ValidationError):
			_fieldtype_cast("Cheque", field_info)

	def test_link_import_requires_master_record(self):
		field_info = frappe._dict(fieldtype="Link", options="Bank Account", label="Bank Account")
		with patch("frappe.db.exists", return_value=True):
			self.assertEqual(_fieldtype_cast("HDFC BANK GURGAON", field_info), "HDFC BANK GURGAON")
		with patch("frappe.db.exists", return_value=False):
			with self.assertRaises(frappe.ValidationError):
				_validate_link_value(field_info, "HDFC BANK GURGAON")
