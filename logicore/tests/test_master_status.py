# Copyright (c) 2026, LogiCore and Contributors

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from logicore.master_status import (
	MASTER_FLAGS,
	MIRROR_RULES,
	compute_disabled,
	find_disabled_references,
	sync_disabled_mirror,
	validate_no_disabled_masters,
)


class TestMasterStatusRegistry(FrappeTestCase):
	def test_out_of_scope_masters_are_absent(self):
		# Company and Import Log were ruled out in the design; registering them
		# would start filtering them out of dropdowns app-wide.
		self.assertNotIn("Company", MASTER_FLAGS)
		self.assertNotIn("Import Log", MASTER_FLAGS)

	def test_inverted_polarity_masters_use_enabled(self):
		# UOM and Email Template carry `enabled`, not `disabled`; for them the
		# value that means "disabled" is 0, not 1.
		self.assertEqual(MASTER_FLAGS["UOM"], ("enabled", 0))
		self.assertEqual(MASTER_FLAGS["Email Template"], ("enabled", 0))

	def test_standard_masters_use_disabled_without_custom_prefix(self):
		# `custom_disabled` is invisible to frappe/desk/search.py:213-217 — the
		# whole feature depends on the bare name.
		for doctype in ("Vehicle", "Branch", "Account Head", "Repair Category"):
			self.assertEqual(MASTER_FLAGS[doctype], ("disabled", 1))

	def test_every_mirror_master_is_registered(self):
		for doctype in MIRROR_RULES:
			self.assertIn(doctype, MASTER_FLAGS)


class TestComputeDisabled(FrappeTestCase):
	def test_status_active_is_enabled(self):
		self.assertEqual(compute_disabled("Employee", "Active"), 0)
		self.assertEqual(compute_disabled("Driver", "Active"), 0)

	def test_every_non_active_status_is_disabled(self):
		for status in ("Inactive", "Suspended", "Left"):
			self.assertEqual(compute_disabled("Employee", status), 1)
		for status in ("Suspended", "Left"):
			self.assertEqual(compute_disabled("Driver", status), 1)

	def test_unknown_future_status_is_disabled(self):
		# Only "Active" is whitelisted, so a status ERPNext adds later is
		# excluded by default rather than silently leaking into dropdowns.
		self.assertEqual(compute_disabled("Employee", "Probation"), 1)

	def test_empty_status_is_disabled(self):
		self.assertEqual(compute_disabled("Employee", None), 1)
		self.assertEqual(compute_disabled("Employee", ""), 1)

	def test_check_kind_mirrors_falsy_source(self):
		self.assertEqual(compute_disabled("TMS User Group", 1), 0)
		self.assertEqual(compute_disabled("TMS User Group", 0), 1)
		self.assertEqual(compute_disabled("Import Template", 1), 0)
		self.assertEqual(compute_disabled("Import Template", 0), 1)

	def test_check_kind_handles_string_values(self):
		# Data Import and REST payloads deliver Check fields as strings.
		self.assertEqual(compute_disabled("Import Template", "1"), 0)
		self.assertEqual(compute_disabled("Import Template", "0"), 1)
		self.assertEqual(compute_disabled("Import Template", None), 1)

	def test_unregistered_doctype_raises(self):
		with self.assertRaises(KeyError):
			compute_disabled("Sales Invoice", "Active")


class TestSyncDisabledMirror(FrappeTestCase):
	def test_employee_left_is_mirrored(self):
		doc = frappe._dict(doctype="Employee", status="Left", disabled=0)
		sync_disabled_mirror(doc)
		self.assertEqual(doc.disabled, 1)

	def test_employee_active_is_mirrored(self):
		doc = frappe._dict(doctype="Employee", status="Active", disabled=1)
		sync_disabled_mirror(doc)
		self.assertEqual(doc.disabled, 0)

	def test_mirror_overwrites_a_hand_edited_value(self):
		# `disabled` is read_only in the UI, but Data Import and the REST API can
		# still send it. The source of truth must win.
		doc = frappe._dict(doctype="Employee", status="Active", disabled=1)
		sync_disabled_mirror(doc)
		self.assertEqual(doc.disabled, 0)

	def test_tms_user_group_inactive_is_mirrored(self):
		doc = frappe._dict(doctype="TMS User Group", is_active=0, disabled=0)
		sync_disabled_mirror(doc)
		self.assertEqual(doc.disabled, 1)

	def test_non_mirror_doctype_is_untouched(self):
		# The hook is wired per-doctype, but it must also be inert if it is ever
		# reached by a doctype with no rule.
		doc = frappe._dict(doctype="Trip Type", disabled=0)
		sync_disabled_mirror(doc)
		self.assertEqual(doc.disabled, 0)


class TestFindDisabledReferences(FrappeTestCase):
	def test_existing_document_is_never_checked(self):
		# Requirement 3: a document saved before the master was disabled must keep
		# saving forever. An existing doc has no __islocal flag, so is_new() is
		# False and the guard returns before touching the database.
		doc = frappe.new_doc("Compliances")
		doc.document_type = "RC BOOK"
		doc.set("__islocal", None)
		self.assertFalse(doc.is_new())
		with patch("logicore.master_status._disabled_names") as lookup:
			validate_no_disabled_masters(doc)
		lookup.assert_not_called()

	def test_new_document_is_checked(self):
		# The mirror of the test above: frappe.new_doc sets __islocal
		# (create_new.py:35), which is what insert() relies on at document.py:465.
		doc = frappe.new_doc("Compliances")
		doc.document_type = "RC BOOK"
		self.assertTrue(doc.is_new())

	def test_no_query_when_document_has_no_registered_masters(self):
		# Most doctypes in the app link to nothing in the registry; they must not
		# cost a query on every insert. Trip Type has no Link fields at all.
		doc = frappe.new_doc("Trip Type")
		with patch("logicore.master_status._disabled_names") as lookup:
			find_disabled_references(doc)
		lookup.assert_not_called()

	def test_disabled_reference_is_reported(self):
		doc = frappe.new_doc("Compliances")
		doc.document_type = "RC BOOK"
		with patch(
			"logicore.master_status._disabled_names",
			return_value={"RC BOOK"},
		):
			found = find_disabled_references(doc)
		self.assertEqual(found, [("document_type", "Compliance Document Type", "RC BOOK")])

	def test_enabled_reference_is_not_reported(self):
		doc = frappe.new_doc("Compliances")
		doc.document_type = "RC BOOK"
		with patch("logicore.master_status._disabled_names", return_value=set()):
			self.assertEqual(find_disabled_references(doc), [])

	def test_validate_throws_on_disabled_reference(self):
		doc = frappe.new_doc("Compliances")
		doc.document_type = "RC BOOK"
		# The guard short-circuits under frappe.flags.in_test so it never fights
		# Frappe's own fixtures; clear it to exercise the real path. frappe.flags is
		# a _dict proxy, so patch.object cannot reach it — set and restore by hand.
		was_in_test = frappe.flags.in_test
		frappe.flags.in_test = False
		try:
			with patch(
				"logicore.master_status._disabled_names",
				return_value={"RC BOOK"},
			):
				with self.assertRaises(frappe.ValidationError):
					validate_no_disabled_masters(doc)
		finally:
			frappe.flags.in_test = was_in_test

	def test_guard_is_inert_during_migration(self):
		doc = frappe.new_doc("Compliances")
		doc.document_type = "RC BOOK"
		frappe.flags.in_migrate = True
		try:
			with patch("logicore.master_status._disabled_names") as lookup:
				validate_no_disabled_masters(doc)
			lookup.assert_not_called()
		finally:
			frappe.flags.in_migrate = False
