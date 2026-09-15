# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, today

from logicore.logicore.doctype.supplier_payment.supplier_payment import get_unpaid_invoices


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# Skip auto-generated Company/Fiscal Year test records — this site already
# has real Company/Fiscal Year data, and Frappe's standard test-record
# generator creates an overlapping "_Test Fiscal Year 2025" that conflicts
# with it. Tests use _get_company() to reuse an existing Company instead,
# same convention as test_staff_payroll.py.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Company", "Fiscal Year"]


class IntegrationTestSupplierPayment(IntegrationTestCase):
	"""
	Integration tests for SupplierPayment.
	Use this class for testing interactions between multiple components.
	"""

	def setUp(self):
		self.company = self._get_company()
		self.supplier = self._make_supplier()
		self.item = self._get_item()
		self._counter = 0

	def _get_company(self):
		company = frappe.db.get_value("Company", {}, "name")
		self.assertTrue(company, "No Company found in the test site — required for Supplier Payment tests")
		return company

	def _get_item(self):
		item = frappe.db.get_value("Item", {"disabled": 0}, "name")
		self.assertTrue(item, "No Item found in the test site — required for Supplier Payment tests")
		return item

	def _make_supplier(self):
		if not frappe.db.exists("Supplier Group", "Supplier"):
			frappe.get_doc({
				"doctype": "Supplier Group",
				"supplier_group_name": "Supplier",
			}).insert(ignore_permissions=True)
		supplier = frappe.get_doc({
			"doctype": "Supplier",
			"supplier_name": frappe.generate_hash(length=8),
			"supplier_group": "Supplier",
			"supplier_type": "Company",
		})
		supplier.insert(ignore_permissions=True)
		return supplier.name

	def _next_bill_no(self):
		self._counter += 1
		return f"TEST-BILL-{frappe.generate_hash(length=6)}-{self._counter}"

	def _make_purchase_invoice(self, bill_no=None, rate=1000, qty=1, supplier=None):
		pi = frappe.get_doc({
			"doctype": "Purchase Invoice",
			"supplier": supplier or self.supplier,
			"company": self.company,
			"payment_date": today(),
			"bill_no": bill_no if bill_no is not None else self._next_bill_no(),
			"bill_date": today(),
			"update_stock": 0,
			"items": [{
				"item_code": self.item,
				"qty": qty,
				"rate": rate,
			}],
		})
		pi.insert(ignore_permissions=True)
		pi.submit()
		return pi

	def test_fetch_excludes_blank_bill_no(self):
		self._make_purchase_invoice(bill_no="")
		result = get_unpaid_invoices(self.supplier, add_days(today(), -1), add_days(today(), 1), self.company)
		self.assertEqual(result, [])

	def test_fetch_excludes_draft_invoices(self):
		pi = frappe.get_doc({
			"doctype": "Purchase Invoice",
			"supplier": self.supplier,
			"company": self.company,
			"payment_date": today(),
			"bill_no": self._next_bill_no(),
			"bill_date": today(),
			"update_stock": 0,
			"items": [{"item_code": self.item, "qty": 1, "rate": 500}],
		})
		pi.insert(ignore_permissions=True)
		result = get_unpaid_invoices(self.supplier, add_days(today(), -1), add_days(today(), 1), self.company)
		self.assertNotIn(pi.name, [r.name for r in result])

	def test_fetch_includes_unpaid_and_excludes_fully_paid(self):
		pi = self._make_purchase_invoice(rate=1000)
		result = get_unpaid_invoices(self.supplier, add_days(today(), -1), add_days(today(), 1), self.company)
		self.assertIn(pi.name, [r.name for r in result])

		frappe.db.set_value("Purchase Invoice", pi.name, {
			"custom_payment_status": "Paid",
			"custom_total_paid": pi.grand_total,
			"custom_balance_amount": 0,
		}, update_modified=False)
		result = get_unpaid_invoices(self.supplier, add_days(today(), -1), add_days(today(), 1), self.company)
		self.assertNotIn(pi.name, [r.name for r in result])

	def test_partial_payment_sets_partially_paid(self):
		pi = self._make_purchase_invoice(rate=1000)
		sp = frappe.get_doc({
			"doctype": "Supplier Payment",
			"company": self.company,
			"payment_date": today(),
			"supplier": self.supplier,
			"mode_of_payment": "Cash",
			"from_date": today(),
			"to_date": today(),
			"invoices": [{
				"purchase_invoice": pi.name,
				"payment_amount": 400,
			}],
		})
		sp.insert(ignore_permissions=True)
		sp.submit()

		pi.reload()
		self.assertEqual(pi.custom_payment_status, "Partially Paid")
		self.assertEqual(flt(pi.custom_total_paid), 400)
		self.assertEqual(flt(pi.custom_balance_amount), flt(pi.grand_total) - 400)

	def test_full_payment_sets_paid_and_cancel_reverses(self):
		pi = self._make_purchase_invoice(rate=1000)
		sp = frappe.get_doc({
			"doctype": "Supplier Payment",
			"company": self.company,
			"payment_date": today(),
			"supplier": self.supplier,
			"mode_of_payment": "Cash",
			"from_date": today(),
			"to_date": today(),
			"invoices": [{
				"purchase_invoice": pi.name,
				"payment_amount": pi.grand_total,
			}],
		})
		sp.insert(ignore_permissions=True)
		sp.submit()

		pi.reload()
		self.assertEqual(pi.custom_payment_status, "Paid")
		self.assertEqual(flt(pi.custom_balance_amount), 0)

		sp.reload()
		sp.cancel()

		pi.reload()
		self.assertEqual(pi.custom_payment_status, "Unpaid")
		self.assertEqual(flt(pi.custom_total_paid), 0)
		self.assertEqual(flt(pi.custom_balance_amount), flt(pi.grand_total))

	def test_payment_amount_exceeding_balance_rejected(self):
		pi = self._make_purchase_invoice(rate=1000)
		sp = frappe.get_doc({
			"doctype": "Supplier Payment",
			"company": self.company,
			"payment_date": today(),
			"supplier": self.supplier,
			"mode_of_payment": "Cash",
			"from_date": today(),
			"to_date": today(),
			"invoices": [{
				"purchase_invoice": pi.name,
				"payment_amount": flt(pi.grand_total) + 100,
			}],
		})
		with self.assertRaises(frappe.ValidationError):
			sp.insert(ignore_permissions=True)

	def test_duplicate_reference_no_rejected(self):
		pi1 = self._make_purchase_invoice(rate=500)
		pi2 = self._make_purchase_invoice(rate=500)

		sp1 = frappe.get_doc({
			"doctype": "Supplier Payment",
			"company": self.company,
			"payment_date": today(),
			"supplier": self.supplier,
			"mode_of_payment": "Bank Transfer",
			"reference_no": "DUPREF-1",
			"from_date": today(),
			"to_date": today(),
			"invoices": [{"purchase_invoice": pi1.name, "payment_amount": 500}],
		})
		sp1.insert(ignore_permissions=True)

		sp2 = frappe.get_doc({
			"doctype": "Supplier Payment",
			"company": self.company,
			"payment_date": today(),
			"supplier": self.supplier,
			"mode_of_payment": "Bank Transfer",
			"reference_no": "DUPREF-1",
			"from_date": today(),
			"to_date": today(),
			"invoices": [{"purchase_invoice": pi2.name, "payment_amount": 500}],
		})
		with self.assertRaises(frappe.ValidationError):
			sp2.insert(ignore_permissions=True)

	def test_tds_amount_is_user_entered_and_not_overwritten(self):
		"""TDS is a free-entry field — whatever the user types per row is what
		gets deducted; the server only derives transfer_amount from it, it
		never recalculates or overwrites the typed value."""
		pi = self._make_purchase_invoice(rate=1000)

		sp = frappe.get_doc({
			"doctype": "Supplier Payment",
			"company": self.company,
			"payment_date": today(),
			"supplier": self.supplier,
			"mode_of_payment": "Cash",
			"from_date": today(),
			"to_date": today(),
			"invoices": [{"purchase_invoice": pi.name, "payment_amount": 500, "tds_amount": 20}],
		})
		sp.insert(ignore_permissions=True)
		self.assertEqual(flt(sp.invoices[0].tds_amount), 20)
		self.assertEqual(flt(sp.invoices[0].transfer_amount), 480)
		self.assertEqual(flt(sp.total_tds_amount), 20)
