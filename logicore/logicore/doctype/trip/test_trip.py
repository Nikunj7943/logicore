# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestTrip(IntegrationTestCase):
	"""
	Integration tests for Trip.
	Use this class for testing interactions between multiple components.
	"""

	pass


class UnitTestTripChronology(IntegrationTestCase):
	"""
	Unit tests for Trip._validate_chronology(), called directly on an
	unsaved frappe.new_doc("Trip") so mandatory-field setup is not needed.
	"""

	def test_dispatch_blocked_without_reach(self):
		trip = frappe.new_doc("Trip")
		trip.dispatch_date_time = "2026-07-08 15:27:00"
		self.assertRaises(frappe.ValidationError, trip._validate_chronology)

	def test_dispatch_equal_to_reach_allowed(self):
		trip = frappe.new_doc("Trip")
		trip.reach_date_time = "2026-07-08 15:27:00"
		trip.dispatch_date_time = "2026-07-08 15:27:00"
		trip._validate_chronology()  # should not raise

	def test_dispatch_before_reach_blocked(self):
		trip = frappe.new_doc("Trip")
		trip.reach_date_time = "2026-07-08 15:27:00"
		trip.dispatch_date_time = "2026-07-08 10:00:00"
		self.assertRaises(frappe.ValidationError, trip._validate_chronology)

	def test_arrival_blocked_without_dispatch(self):
		trip = frappe.new_doc("Trip")
		trip.reach_date_time = "2026-07-08 15:27:00"
		trip.arrival_date_time = "2026-07-09 09:00:00"
		self.assertRaises(frappe.ValidationError, trip._validate_chronology)

	def test_release_blocked_without_arrival(self):
		trip = frappe.new_doc("Trip")
		trip.reach_date_time = "2026-07-08 15:27:00"
		trip.dispatch_date_time = "2026-07-08 16:00:00"
		trip.release_date_time = "2026-07-09 09:00:00"
		self.assertRaises(frappe.ValidationError, trip._validate_chronology)

	def test_full_valid_chain_allowed(self):
		trip = frappe.new_doc("Trip")
		trip.reach_date_time = "2026-07-08 15:27:00"
		trip.dispatch_date_time = "2026-07-08 16:00:00"
		trip.arrival_date_time = "2026-07-09 09:00:00"
		trip.release_date_time = "2026-07-09 11:00:00"
		trip._validate_chronology()  # should not raise
