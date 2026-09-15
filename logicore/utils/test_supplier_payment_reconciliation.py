# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, today

from logicore.utils.bank_reconciliation_utils import get_eligible_records
from logicore.utils.supplier_payment_reconciliation import on_reconciliation_changed

EXTRA_TEST_RECORD_DEPENDENCIES = []
# Both empty on purpose. These tests reuse the site's real Company and Item
# (see setUp) and need no generated test records, so nothing is declared here —
# which also keeps Frappe from auto-creating a "_Test Fiscal Year 2025" that
# overlaps this site's real Fiscal Year. Same arrangement as
# test_bank_reconciliation_utils.py. Declaring IGNORE_TEST_RECORD_DEPENDENCIES
# instead would not help: Frappe only honours it for test modules that sit in a
# doctype folder, and even there it is skipped once cls.doctype resolves.
IGNORE_TEST_RECORD_DEPENDENCIES = []

SOURCE_CONFIG = {
	"doctype": "TMS Reconciliation Source",
	"label": "Supplier Payment",
	"target_doctype": "Supplier Payment",
	"direction": "Debit",
	"requires_submitted": 1,
	"date_fieldname": "payment_date",
	"amount_fieldname": "total_transfer_amount",
	"account_fieldname": "paid_from_account",
	"reconciled_fieldname": "is_reconciled",
	"reconciliation_link_fieldname": "bank_reconciliation",
}


class IntegrationTestSupplierPaymentReconciliation(IntegrationTestCase):

	def setUp(self):
		self.company = frappe.db.get_value("Company", {}, "name")
		self.assertTrue(self.company, "No Company on this site — required for these tests")
		self.item = frappe.db.get_value("Item", {"disabled": 0}, "name")
		self.assertTrue(self.item, "No Item on this site — required for these tests")
		self.supplier = self._make_supplier()
		self.bank_account = frappe.get_doc({
			"doctype": "Account Head",
			"name1": f"Test SP Recon Bank {frappe.generate_hash(length=6)}",
			"group": "BANK",
		}).insert(ignore_permissions=True).name
		if not frappe.db.exists("TMS Reconciliation Source", "Supplier Payment"):
			frappe.get_doc(dict(SOURCE_CONFIG)).insert(ignore_permissions=True)

	def _make_supplier(self):
		if not frappe.db.exists("Supplier Group", "Supplier"):
			frappe.get_doc({
				"doctype": "Supplier Group",
				"supplier_group_name": "Supplier",
			}).insert(ignore_permissions=True)
		return frappe.get_doc({
			"doctype": "Supplier",
			"supplier_name": frappe.generate_hash(length=8),
			"supplier_group": "Supplier",
			"supplier_type": "Company",
		}).insert(ignore_permissions=True).name

	def _make_purchase_invoice(self, rate=1000):
		pi = frappe.get_doc({
			"doctype": "Purchase Invoice",
			"supplier": self.supplier,
			"company": self.company,
			"posting_date": today(),
			"bill_no": f"RECON-BILL-{frappe.generate_hash(length=6)}",
			"bill_date": today(),
			"update_stock": 0,
			"items": [{"item_code": self.item, "qty": 1, "rate": rate}],
		})
		pi.insert(ignore_permissions=True)
		pi.submit()
		return pi

	def _make_supplier_payment(self, invoice_rows, submit=True):
		sp = frappe.get_doc({
			"doctype": "Supplier Payment",
			"company": self.company,
			"payment_date": today(),
			"supplier": self.supplier,
			"mode_of_payment": "Cash",
			"paid_from_account": self.bank_account,
			"from_date": today(),
			"to_date": today(),
			"invoices": invoice_rows,
		})
		sp.insert(ignore_permissions=True)
		if submit:
			sp.submit()
		return sp

	def _reconcile(self, supplier_payment, reconciled=True):
		"""Do exactly what TMSBankReconciliation._set_reconciled_flag() does —
		flip the flag with db.set_value, then fire the cascade."""
		frappe.db.set_value(
			"Supplier Payment", supplier_payment, "is_reconciled", 1 if reconciled else 0
		)
		on_reconciliation_changed("Supplier Payment", supplier_payment)

	def _status_of(self, purchase_invoice):
		return frappe.db.get_value(
			"Purchase Invoice", purchase_invoice,
			["custom_bank_reconciliation_status", "custom_reconciled_amount"],
			as_dict=True,
		)

	def test_full_payment_reconciled_marks_invoice_reconciled(self):
		pi = self._make_purchase_invoice(rate=1000)
		sp = self._make_supplier_payment([
			{"purchase_invoice": pi.name, "payment_amount": pi.grand_total},
		])

		# Submitted but not yet bank-matched.
		self.assertEqual(self._status_of(pi.name).custom_bank_reconciliation_status, "Unreconciled")

		self._reconcile(sp.name)
		result = self._status_of(pi.name)
		self.assertEqual(result.custom_bank_reconciliation_status, "Reconciled")
		self.assertEqual(flt(result.custom_reconciled_amount), flt(pi.grand_total))

	def test_partial_payment_reconciled_marks_invoice_partially_reconciled(self):
		pi = self._make_purchase_invoice(rate=1000)
		sp = self._make_supplier_payment([
			{"purchase_invoice": pi.name, "payment_amount": 400},
		])

		self._reconcile(sp.name)
		result = self._status_of(pi.name)
		self.assertEqual(result.custom_bank_reconciliation_status, "Partially Reconciled")
		self.assertEqual(flt(result.custom_reconciled_amount), 400)

	def test_one_of_two_payments_reconciled_is_partial(self):
		pi = self._make_purchase_invoice(rate=1000)
		half = flt(pi.grand_total) / 2
		sp1 = self._make_supplier_payment([{"purchase_invoice": pi.name, "payment_amount": half}])
		sp2 = self._make_supplier_payment([{"purchase_invoice": pi.name, "payment_amount": half}])

		self._reconcile(sp1.name)
		self.assertEqual(self._status_of(pi.name).custom_bank_reconciliation_status, "Partially Reconciled")

		self._reconcile(sp2.name)
		result = self._status_of(pi.name)
		self.assertEqual(result.custom_bank_reconciliation_status, "Reconciled")
		self.assertEqual(flt(result.custom_reconciled_amount), flt(pi.grand_total))

	def test_un_reconciling_reverts_invoice_status(self):
		pi = self._make_purchase_invoice(rate=1000)
		sp = self._make_supplier_payment([
			{"purchase_invoice": pi.name, "payment_amount": pi.grand_total},
		])
		self._reconcile(sp.name)
		self.assertEqual(self._status_of(pi.name).custom_bank_reconciliation_status, "Reconciled")

		# Cancelling the TMS Bank Reconciliation clears the flag the same way.
		self._reconcile(sp.name, reconciled=False)
		result = self._status_of(pi.name)
		self.assertEqual(result.custom_bank_reconciliation_status, "Unreconciled")
		self.assertEqual(flt(result.custom_reconciled_amount), 0)

	def test_cancelling_a_reconciled_payment_reverts_invoice_status(self):
		pi = self._make_purchase_invoice(rate=1000)
		sp = self._make_supplier_payment([
			{"purchase_invoice": pi.name, "payment_amount": pi.grand_total},
		])
		self._reconcile(sp.name)
		self.assertEqual(self._status_of(pi.name).custom_bank_reconciliation_status, "Reconciled")

		sp.reload()
		sp.cancel()

		result = self._status_of(pi.name)
		self.assertEqual(result.custom_bank_reconciliation_status, "Unreconciled")
		self.assertEqual(flt(result.custom_reconciled_amount), 0)

	def test_one_payment_updates_every_invoice_it_covers(self):
		invoices = [self._make_purchase_invoice(rate=500) for _ in range(3)]
		sp = self._make_supplier_payment([
			{"purchase_invoice": pi.name, "payment_amount": pi.grand_total} for pi in invoices
		])

		self._reconcile(sp.name)
		for pi in invoices:
			result = self._status_of(pi.name)
			self.assertEqual(result.custom_bank_reconciliation_status, "Reconciled")
			self.assertEqual(flt(result.custom_reconciled_amount), flt(pi.grand_total))

	def test_reconciled_amount_uses_payment_amount_not_transfer_amount(self):
		"""The bank moved grand_total minus TDS, but the invoice is settled by
		the full payment_amount — so a fully-paid invoice with TDS deducted must
		still come out Reconciled, not Partially Reconciled."""
		pi = self._make_purchase_invoice(rate=1000)
		sp = self._make_supplier_payment([
			{"purchase_invoice": pi.name, "payment_amount": pi.grand_total, "tds_amount": 100},
		])
		self.assertEqual(flt(sp.total_transfer_amount), flt(pi.grand_total) - 100)

		self._reconcile(sp.name)
		result = self._status_of(pi.name)
		self.assertEqual(result.custom_bank_reconciliation_status, "Reconciled")
		self.assertEqual(flt(result.custom_reconciled_amount), flt(pi.grand_total))

	def test_submitted_supplier_payment_is_an_eligible_debit_candidate(self):
		"""Guards the TMS Reconciliation Source field names against typos: if any
		of them stopped matching a real Supplier Payment field, the leg would
		silently never match anything."""
		pi = self._make_purchase_invoice(rate=1000)
		sp = self._make_supplier_payment([
			{"purchase_invoice": pi.name, "payment_amount": pi.grand_total},
		])

		debit_map, credit_map = get_eligible_records(self.bank_account, today(), today())
		key = (frappe.utils.getdate(today()), flt(sp.total_transfer_amount))
		self.assertIn(("Supplier Payment", "Supplier Payment", sp.name), debit_map.get(key, []))
		self.assertNotIn(("Supplier Payment", "Supplier Payment", sp.name), credit_map.get(key, []))
