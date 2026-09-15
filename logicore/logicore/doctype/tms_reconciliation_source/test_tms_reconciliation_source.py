# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []


class IntegrationTestTMSReconciliationSource(IntegrationTestCase):
	"""
	Integration tests for TMS Reconciliation Source.
	"""

	def test_names_by_label(self):
		doc = frappe.get_doc({
			"doctype": "TMS Reconciliation Source",
			"label": "Test Source Label",
			"target_doctype": "Vendor Payment",
			"direction": "Debit",
			"date_fieldname": "payment_date",
			"amount_fieldname": "total_transfer_amount",
			"account_fieldname": "paid_from_account",
			"reconciled_fieldname": "is_reconciled",
			"reconciliation_link_fieldname": "bank_reconciliation",
		}).insert(ignore_permissions=True)
		self.assertEqual(doc.name, "Test Source Label")
		doc.delete()

	def test_sequence_auto_assigned_when_not_set(self):
		max_sequence = frappe.db.sql(
			"select max(sequence) from `tabTMS Reconciliation Source`"
		)[0][0] or 0
		doc = frappe.get_doc({
			"doctype": "TMS Reconciliation Source",
			"label": "Test Source Auto Sequence",
			"target_doctype": "Vendor Payment",
			"direction": "Debit",
			"date_fieldname": "payment_date",
			"amount_fieldname": "total_transfer_amount",
			"account_fieldname": "paid_from_account",
			"reconciled_fieldname": "is_reconciled",
			"reconciliation_link_fieldname": "bank_reconciliation",
		}).insert(ignore_permissions=True)
		self.assertEqual(doc.sequence, max_sequence + 1)
		doc.delete()
