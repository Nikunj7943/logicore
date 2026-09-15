# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from logicore.logicore.doctype.fuel_urea_expenses.fuel_urea_expenses import (
	get_vehicle_fuel_history,
)


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestFuelUreaExpenses(IntegrationTestCase):
	"""
	Integration tests for FuelUreaExpenses.
	Use this class for testing interactions between multiple components.
	"""

	def setUp(self):
		self.vehicle = self._make_vehicle()
		self.driver = self._make_driver()
		self.supplier = self._make_supplier()
		self.bank_account = self._make_account_head()

	def _make_vehicle(self):
		doc = frappe.get_doc({
			"doctype": "Vehicle",
			"license_plate": frappe.generate_hash(length=10),
			"make": "Test Make",
			"model": "Test Model",
			"last_odometer": 0,
			"fuel_type": "Diesel",
			"uom": frappe.db.get_value("UOM", {}, "name"),
		}).insert()
		return doc.name

	def _make_driver(self):
		doc = frappe.get_doc({
			"doctype": "Driver",
			"full_name": f"Test Driver {frappe.generate_hash(length=6)}",
			"status": "Active",
		}).insert()
		return doc.name

	def _make_supplier(self):
		doc = frappe.get_doc({
			"doctype": "Supplier",
			"supplier_name": f"Test Supplier {frappe.generate_hash(length=6)}",
			"supplier_type": "Company",
		}).insert()
		return doc.name

	def _make_account_head(self):
		doc = frappe.get_doc({
			"doctype": "Account Head",
			"name1": f"Test Bank {frappe.generate_hash(length=6)}",
			"group": "BANK",
		}).insert()
		return doc.name

	def _make_entry(self, date, current_odometer, fuelurea="Diesel", submit=True,
			fill_type="Top Up (Full Tank)", liters=50, fixed_kpl=0, excessshort_fuel_rate=0):
		doc = frappe.get_doc({
			"doctype": "Fuel Urea Expenses",
			"date": date,
			"driver_id": self.driver,
			"vehicle": self.vehicle,
			"fill_type": fill_type,
			"current_odometer": current_odometer,
			"last_odoometer": 0,
			"fuelurea": fuelurea,
			"liters": liters,
			"fixed_kpl": fixed_kpl,
			"excessshort_fuel_rate": excessshort_fuel_rate,
			"fuelurea_amount": 5000,
			"supplier": self.supplier,
			"payment_mode": "Cash",
			"bank_name": self.bank_account,
		}).insert()
		if submit:
			doc.submit()
		return doc

	def test_default_30_day_window_excludes_older_entries(self):
		recent = self._make_entry(add_days(today(), -10), 1100)
		older = self._make_entry(add_days(today(), -45), 1200)

		result = get_vehicle_fuel_history(self.vehicle)
		names = [row["name"] for row in result]

		self.assertIn(recent.name, names)
		self.assertNotIn(older.name, names)

	def test_custom_range_includes_older_entries(self):
		older = self._make_entry(add_days(today(), -45), 1200)

		result = get_vehicle_fuel_history(
			self.vehicle, from_date=add_days(today(), -60), to_date=today()
		)
		names = [row["name"] for row in result]

		self.assertIn(older.name, names)

	def test_excludes_given_document_name(self):
		entry = self._make_entry(add_days(today(), -5), 1100)

		result = get_vehicle_fuel_history(self.vehicle, exclude_name=entry.name)
		names = [row["name"] for row in result]

		self.assertNotIn(entry.name, names)

	def test_excludes_draft_and_cancelled_entries(self):
		draft = self._make_entry(add_days(today(), -5), 1100, submit=False)
		cancelled = self._make_entry(add_days(today(), -6), 1200)
		cancelled.cancel()

		result = get_vehicle_fuel_history(self.vehicle)
		names = [row["name"] for row in result]

		self.assertNotIn(draft.name, names)
		self.assertNotIn(cancelled.name, names)

	def test_includes_both_fuel_and_urea_entries(self):
		fuel_entry = self._make_entry(add_days(today(), -5), 1100, fuelurea="Diesel")
		urea_entry = self._make_entry(add_days(today(), -4), 1200, fuelurea="Urea")

		result = get_vehicle_fuel_history(self.vehicle)
		names = [row["name"] for row in result]

		self.assertIn(fuel_entry.name, names)
		self.assertIn(urea_entry.name, names)

	def test_partial_refill_calculates_kpl_from_own_distance_and_liters(self):
		self._make_entry(add_days(today(), -10), 1000, fill_type="Top Up (Full Tank)", liters=40)
		partial = self._make_entry(add_days(today(), -9), 1200, fill_type="Partial Refill", liters=30)

		self.assertEqual(partial.last_odoometer, 1000)
		self.assertEqual(partial.distance, 200)
		self.assertEqual(partial.kpl, round(200 / 30, 2))

	def test_partial_refill_incentive_and_excess_short_stay_zero(self):
		self._make_entry(add_days(today(), -10), 1000, fill_type="Top Up (Full Tank)", liters=40)
		partial = self._make_entry(
			add_days(today(), -9), 1200, fill_type="Partial Refill", liters=30,
			fixed_kpl=4, excessshort_fuel_rate=70,
		)

		self.assertNotEqual(partial.kpl, 0)
		self.assertEqual(partial.excessshort_fuel, 0)
		self.assertEqual(partial.fuel_incentive, 0)

	def test_consecutive_partial_refills_use_immediately_previous_entry(self):
		self._make_entry(add_days(today(), -10), 1000, fill_type="Top Up (Full Tank)", liters=40)
		self._make_entry(add_days(today(), -9), 1200, fill_type="Partial Refill", liters=10)
		partial_2 = self._make_entry(add_days(today(), -8), 1400, fill_type="Partial Refill", liters=8)

		# Must chain off the immediately previous entry (odo 1200), not the last Top Up (odo 1000)
		self.assertEqual(partial_2.last_odoometer, 1200)
		self.assertEqual(partial_2.distance, 200)

	def test_topup_still_carries_forward_partial_liters_for_its_own_kpl(self):
		self._make_entry(add_days(today(), -10), 1000, fill_type="Top Up (Full Tank)", liters=40)
		self._make_entry(add_days(today(), -9), 1200, fill_type="Partial Refill", liters=10)
		self._make_entry(add_days(today(), -8), 1400, fill_type="Partial Refill", liters=8)
		topup = self._make_entry(
			add_days(today(), -7), 1600, fill_type="Top Up (Full Tank)", liters=35,
			fixed_kpl=4, excessshort_fuel_rate=70,
		)

		# Top Up's own last_odometer must still be the last Top Up (1000), not the last Partial (1400)
		self.assertEqual(topup.last_odoometer, 1000)
		self.assertEqual(topup.distance, 600)
		self.assertEqual(topup.partial_liters_carried, 18)
		self.assertEqual(topup.effective_liters, 53)
		self.assertEqual(topup.kpl, round(600 / 53, 2))

	def test_cancelling_topup_reverts_vehicle_last_odometer(self):
		self._make_entry(add_days(today(), -10), 1000, fill_type="Top Up (Full Tank)", liters=40)
		second = self._make_entry(add_days(today(), -5), 1600, fill_type="Top Up (Full Tank)", liters=35)

		self.assertEqual(frappe.db.get_value("Vehicle", self.vehicle, "last_odometer"), 1600)

		second.cancel()

		self.assertEqual(frappe.db.get_value("Vehicle", self.vehicle, "last_odometer"), 1000)
