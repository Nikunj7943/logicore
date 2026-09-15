# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


class IntegrationTestTMSBankReconciliationSetting(IntegrationTestCase):
	"""
	Integration tests for TMS Bank Reconciliation Setting.
	"""

	def setUp(self):
		self.bank_account = frappe.get_doc({
			"doctype": "Account Head",
			"name1": "Test ICICI Recon Account",
			"group": "BANK",
		}).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.delete("TMS Bank Reconciliation Setting", {"bank_account": self.bank_account.name})
		self.bank_account.delete()

	def test_names_by_bank_account(self):
		setting = frappe.get_doc({
			"doctype": "TMS Bank Reconciliation Setting",
			"bank_account": self.bank_account.name,
			"header_row": 17,
			"data_start_row": 18,
			"transaction_date_column": "Transaction Date",
			"debit_column": "Withdrawal Amt (INR)",
			"credit_column": "Deposit Amt (INR)",
			"narration_column": "Transaction Remarks",
			"reference_column": "Cheque. No./Ref. No.",
		}).insert(ignore_permissions=True)
		self.assertEqual(setting.name, self.bank_account.name)

	def test_second_setting_for_same_bank_account_fails(self):
		frappe.get_doc({
			"doctype": "TMS Bank Reconciliation Setting",
			"bank_account": self.bank_account.name,
			"header_row": 17,
			"data_start_row": 18,
			"transaction_date_column": "Transaction Date",
			"debit_column": "Withdrawal Amt (INR)",
			"credit_column": "Deposit Amt (INR)",
		}).insert(ignore_permissions=True)
		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc({
				"doctype": "TMS Bank Reconciliation Setting",
				"bank_account": self.bank_account.name,
				"header_row": 17,
				"data_start_row": 18,
				"transaction_date_column": "Transaction Date",
				"debit_column": "Withdrawal Amt (INR)",
				"credit_column": "Deposit Amt (INR)",
			}).insert(ignore_permissions=True)
