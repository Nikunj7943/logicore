# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, today

from logicore.logicore.doctype.vendor_payment.vendor_payment import get_unpaid_trips


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# Skip auto-generated Company/Fiscal Year test records — this site already
# has real Company/Fiscal Year data, and Frappe's standard test-record
# generator creates an overlapping "_Test Fiscal Year 2025" that conflicts
# with it. IntegrationTestVendorPaymentLrMoney reuses existing site data via
# _get_link_value("Company") instead, same convention as
# test_supplier_payment.py's _get_company().
IGNORE_TEST_RECORD_DEPENDENCIES = ["Company", "Fiscal Year"]


class IntegrationTestVendorPayment(IntegrationTestCase):
	"""
	Integration tests for VendorPayment.
	Use this class for testing interactions between multiple components.
	"""

	def test_is_reconciled_defaults_to_unchecked(self):
		meta = frappe.get_meta("Vendor Payment")
		self.assertIn("is_reconciled", [df.fieldname for df in meta.fields])
		self.assertIn("bank_reconciliation", [df.fieldname for df in meta.fields])
		is_reconciled_field = meta.get_field("is_reconciled")
		self.assertEqual(is_reconciled_field.fieldtype, "Check")
		bank_reconciliation_field = meta.get_field("bank_reconciliation")
		self.assertEqual(bank_reconciliation_field.fieldtype, "Link")
		self.assertEqual(bank_reconciliation_field.options, "TMS Bank Reconciliation")


class IntegrationTestVendorPaymentLrMoney(IntegrationTestCase):
	"""
	Employee/Company LR Money must be deducted at most once per trip across
	submitted Vendor Payments — once deducted, get_unpaid_trips() must return
	0 (and a locked flag) for that field so it can never be fetched/deducted
	again, independently per field. TDS's field must always be read-only.
	"""

	def setUp(self):
		self.company = self._get_link_value("Company")
		self.branch = self._get_link_value("Branch")
		self.trip_type = self._get_link_value("Trip Type")
		self.customer = self._get_link_value("Customer")
		self.supplier = self._make_supplier()
		self._counter = 0

	def _get_link_value(self, doctype):
		value = frappe.db.get_value(doctype, {}, "name")
		self.assertTrue(value, f"No {doctype} found in the test site — required for this test")
		return value

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

	def _make_trip(self, vendor_freight=5000, employee_lr_money=0, company_lr_money=0):
		self._counter += 1
		trip = frappe.get_doc({
			"doctype": "Trip",
			"tcntrip_date": today(),
			"tcntrip_no": f"TEST-LR-{frappe.generate_hash(length=6)}-{self._counter}",
			"trip_type": self.trip_type,
			"branch": self.branch,
			"customer": self.customer,
			"company": self.company,
			"vendor": self.supplier,
			"vendor_freight": vendor_freight,
			"employee_lr_money": employee_lr_money,
			"company_lr_money": company_lr_money,
		})
		trip.insert(ignore_permissions=True)
		return trip

	def _make_vendor_payment(self, trips):
		vp = frappe.get_doc({
			"doctype": "Vendor Payment",
			"company": self.company,
			"payment_date": today(),
			"vendor": self.supplier,
			"from_date": today(),
			"to_date": today(),
			"mode_of_payment": "Cash",
			"trips": trips,
		})
		vp.insert(ignore_permissions=True)
		return vp

	def test_fetch_returns_full_lr_money_when_never_deducted(self):
		trip = self._make_trip(vendor_freight=5000, employee_lr_money=100, company_lr_money=300)
		trips = get_unpaid_trips(self.supplier, today(), today(), self.company)
		row = next(t for t in trips if t.name == trip.name)
		self.assertEqual(flt(row.employee_lr_money), 100)
		self.assertEqual(row.employee_lr_locked, 0)
		self.assertEqual(flt(row.company_lr_money), 300)
		self.assertEqual(row.company_lr_locked, 0)

	def test_fetch_locks_and_zeroes_both_fields_after_full_deduction(self):
		trip = self._make_trip(vendor_freight=5000, employee_lr_money=100, company_lr_money=300)
		vp = self._make_vendor_payment([{"trip": trip.name, "payment_amount": 2000}])
		vp.submit()

		trips = get_unpaid_trips(self.supplier, today(), today(), self.company)
		row = next(t for t in trips if t.name == trip.name)
		self.assertEqual(flt(row.employee_lr_money), 0)
		self.assertEqual(row.employee_lr_locked, 1)
		self.assertEqual(flt(row.company_lr_money), 0)
		self.assertEqual(row.company_lr_locked, 1)

	def test_employee_and_company_lr_money_lock_independently(self):
		trip = self._make_trip(vendor_freight=5000, employee_lr_money=100, company_lr_money=300)
		# Only employee_lr_money actually gets deducted in this payment —
		# company_lr_money is explicitly left at 0 for this row.
		vp = self._make_vendor_payment([{
			"trip": trip.name,
			"payment_amount": 2000,
			"employee_lr_money": 100,
			"company_lr_money": 0,
		}])
		vp.submit()

		trips = get_unpaid_trips(self.supplier, today(), today(), self.company)
		row = next(t for t in trips if t.name == trip.name)
		self.assertEqual(flt(row.employee_lr_money), 0)
		self.assertEqual(row.employee_lr_locked, 1)
		self.assertEqual(flt(row.company_lr_money), 300)
		self.assertEqual(row.company_lr_locked, 0)

	def test_tds_field_is_always_read_only(self):
		meta = frappe.get_meta("Vendor Payment Trip")
		self.assertEqual(meta.get_field("tds_amount").read_only, 1)

	def test_lr_money_fields_are_conditionally_read_only(self):
		meta = frappe.get_meta("Vendor Payment Trip")
		employee_field = meta.get_field("employee_lr_money")
		company_field = meta.get_field("company_lr_money")
		self.assertEqual(employee_field.read_only_depends_on, "eval:doc.employee_lr_locked")
		self.assertEqual(company_field.read_only_depends_on, "eval:doc.company_lr_locked")
		self.assertFalse(employee_field.read_only)
		self.assertFalse(company_field.read_only)
