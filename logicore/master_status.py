"""Master enable/disable — the single registry for the whole feature.

Frappe v16 already hides a record from every Link dropdown, server-side, for every
form and child-table grid in the app, provided the record's doctype has a Check
field named exactly `disabled` (or `enabled`). See
apps/frappe/frappe/desk/search.py:213-217. Nothing here reimplements that.

Two things Frappe does NOT do, which this module supplies:

  sync_disabled_mirror()         keeps `disabled` in step with a master that already
                                 had its own lifecycle field (Employee.status etc.),
                                 so nobody has to tick two controls.

  validate_no_disabled_masters() closes the Data Import / REST path, which submits
                                 master names directly and never touches a dropdown.

Why the exact fieldname matters: a Custom Field created without an explicit
fieldname gets a `custom_` prefix (custom_field.py:145-156), and `custom_disabled`
is invisible to the search filter. Vehicle and Branch shipped that way for months —
users ticked "Disabled" and the vehicle kept appearing everywhere.

Design: docs/superpowers/specs/2026-08-06-master-enable-disable-design.md
"""

import frappe
from frappe import _
from frappe.utils import cint

# ── Registry ────────────────────────────────────────────────────────────────
#
# doctype -> (flag fieldname, flag value that means "disabled")
#
# Most masters are ("disabled", 1). UOM and Email Template carry `enabled`
# instead, so for them the disabled value is 0. Both spellings are honoured by
# Frappe's search filter; only the polarity differs.
#
# Deliberately absent: Company (disabling it would strip the company Link on
# every ERPNext transaction) and Import Log (a record of import runs, not a
# master, and a Link target nowhere).

MASTER_FLAGS = {
	# Group A — renamed from the inert `custom_disabled`
	"Branch": ("disabled", 1),
	"Vehicle": ("disabled", 1),
	# Group B — `disabled` is derived, see MIRROR_RULES
	"Driver": ("disabled", 1),
	"Employee": ("disabled", 1),
	"Import Template": ("disabled", 1),
	"TMS User Group": ("disabled", 1),
	# Group C — field added by this feature
	"Account Head": ("disabled", 1),
	"Compliance Document Type": ("disabled", 1),
	"Customer Group": ("disabled", 1),
	"GST HSN Code": ("disabled", 1),
	"Item Group": ("disabled", 1),
	"Repair Category": ("disabled", 1),
	"Repair Item": ("disabled", 1),
	"Repair Sub Category": ("disabled", 1),
	"Supplier Group": ("disabled", 1),
	# Already carried a working flag before this feature
	"Address": ("disabled", 1),
	"Business Format": ("disabled", 1),
	"Business Subformat": ("disabled", 1),
	"City": ("disabled", 1),
	"Customer": ("disabled", 1),
	"Email Template": ("enabled", 0),
	"Item": ("disabled", 1),
	"Supplier": ("disabled", 1),
	"Trip Type": ("disabled", 1),
	"UOM": ("enabled", 0),
	"Vehicle Type": ("disabled", 1),
	"Warehouse": ("disabled", 1),
}

# ── Group B mirror rules ────────────────────────────────────────────────────
#
# These masters already had a lifecycle field before this feature, and that field
# stays in charge. `disabled` is a hidden, read-only mirror of it.
#
# `active_values` is a whitelist, not a blacklist of known-bad values. If ERPNext
# adds an Employee status later, it lands on the disabled side by default instead
# of silently leaking into every dropdown.
#
# is_active is NOT renamed to `disabled`: it is load-bearing in
# tms_navigation_visibility.py:25, tms_list_settings.py:43,
# patches/sync_role_and_permissions_to_tms_user_group.py:88-95 and
# import_template.py:109. Inverting its polarity across all of those carries more
# defect surface than maintaining a mirror.

MIRROR_RULES = {
	"Driver": {"source": "status", "active_values": ("Active",)},
	"Employee": {"source": "status", "active_values": ("Active",)},
	"Import Template": {"source": "is_active", "kind": "check"},
	"TMS User Group": {"source": "is_active", "kind": "check"},
}


def compute_disabled(doctype: str, source_value) -> int:
	"""Return the `disabled` value a Group B master should carry.

	Raises KeyError for a doctype with no mirror rule — that is a registry bug,
	not a runtime condition, so it should be loud.
	"""
	rule = MIRROR_RULES[doctype]

	if rule.get("kind") == "check":
		return 0 if cint(source_value) else 1

	return 0 if source_value in rule["active_values"] else 1


def sync_disabled_mirror(doc, method=None):
	"""before_validate hook for Group B masters. Keeps `disabled` derived."""
	rule = MIRROR_RULES.get(doc.doctype)
	if not rule:
		return

	doc.disabled = compute_disabled(doc.doctype, doc.get(rule["source"]))


# ── New-document guard ──────────────────────────────────────────────────────
#
# Frappe's dropdown filter is client-facing. Data Import and REST callers submit
# master names directly and never touch a dropdown, and this app has an active
# import pipeline (Trip POD Import, Import Template), so that path matters.
#
# Scoped to doc.is_new() on purpose. That single condition is what keeps the
# promise that a document saved before its master was disabled goes on saving
# forever -- editing an existing record never enters this code at all.


def _disabled_names(doctype: str, names: list) -> set:
	"""Return which of `names` are currently disabled. One query per doctype."""
	flag_field, disabled_value = MASTER_FLAGS[doctype]

	return set(
		frappe.get_all(
			doctype,
			filters={"name": ["in", names], flag_field: disabled_value},
			pluck="name",
			ignore_permissions=True,
		)
	)


def _registered_link_values(doc) -> dict:
	"""Collect {master doctype: {value: fieldname}} for this doc and its children.

	Returns early-empty for the great majority of doctypes, which link to nothing
	in the registry -- that is what keeps this cheap on every insert.
	"""
	collected = {}

	def scan(row):
		for field in row.meta.get_link_fields():
			if field.options not in MASTER_FLAGS:
				continue
			value = row.get(field.fieldname)
			if value:
				collected.setdefault(field.options, {}).setdefault(value, field.fieldname)

	scan(doc)
	for child in doc.get_all_children():
		scan(child)

	return collected


def find_disabled_references(doc) -> list:
	"""Return [(fieldname, master doctype, value)] for disabled masters on `doc`."""
	found = []

	for doctype, values in _registered_link_values(doc).items():
		for name in sorted(_disabled_names(doctype, list(values))):
			found.append((values[name], doctype, name))

	return found


def validate_no_disabled_masters(doc, method=None):
	"""validate hook (wired on "*"). Blocks disabled masters on NEW documents.

	is_new() is bool(self.get("__islocal")) (base_document.py:631). insert() sets
	that flag at document.py:465, before run_before_save_methods() runs validate,
	and clears it at document.py:510 once the insert lands -- so this is True
	during an insert's validate and False during an update's. That single line is
	the entire reason an existing document keeps saving after its master was
	disabled.
	"""
	if not doc.is_new():
		return

	if frappe.flags.in_migrate or frappe.flags.in_install or frappe.flags.in_patch:
		return

	if frappe.flags.in_test:
		# Frappe's own test fixtures create records against whatever masters
		# exist; the guard is exercised directly in tests/test_master_status.py.
		return

	found = find_disabled_references(doc)
	if not found:
		return

	lines = "<br>".join(
		f"<b>{frappe.unscrub(fieldname)}</b>: {value} ({_(doctype)})"
		for fieldname, doctype, value in found
	)
	frappe.throw(
		_("These records are disabled in their master and cannot be used on a new {0}:<br>{1}").format(
			_(doc.doctype), lines
		),
		title=_("Disabled Master Record"),
	)
