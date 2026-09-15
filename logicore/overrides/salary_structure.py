import frappe
from frappe import _

# Staff Payroll generates a Salary Slip-like record per employee per month from a
# Salary Structure. By the time a new component needs adding, hundreds of Staff
# Payroll records can already be submitted against it -- cancelling/amending the
# structure would force-cancel all of them (Frappe's linked-doc cancel dialog). So
# both doctypes are allowed to be edited in place after submit (see the matching
# allow_on_submit Property Setters in install.py), restricted to Administrator /
# System Manager / whichever TMS User Group(s) are flagged "Is Admin" only.
#
# The admin TMS User Group's underlying Role name isn't a fixed string -- it's
# whatever that group is named/renamed to on a given site (e.g. "TMS ADMIN" on
# one site, "TMS-Admin" on another), so it must be looked up per site instead of
# hardcoded, or the check silently fails wherever the name differs.
ALLOWED_ROLES = {"System Manager"}


def _user_is_allowed():
	if frappe.session.user == "Administrator":
		return True
	user_roles = set(frappe.get_roles())
	if ALLOWED_ROLES & user_roles:
		return True
	admin_groups = frappe.get_all("TMS User Group", filters={"is_admin": 1, "is_active": 1}, pluck="name")
	return bool(set(admin_groups) & user_roles)


def restrict_component_edit_after_submit(doc, method=None):
	if doc.docstatus != 1:
		return
	if _user_is_allowed():
		return
	frappe.throw(
		_("Only Administrator, System Manager, or TMS Admin can modify a submitted Salary Structure."),
		frappe.PermissionError,
	)


def restrict_staff_payroll_component_edit_after_submit(doc, method=None):
	if doc.docstatus != 1:
		return
	# Set by backfill_staff_payroll_components() below -- that job re-saves old
	# Staff Payroll records on behalf of whichever admin edited the Salary
	# Structure, so it deliberately bypasses the interactive-edit role check.
	if doc.flags.get("ignore_component_restriction"):
		return
	if _user_is_allowed():
		return
	frappe.throw(
		_("Only Administrator, System Manager, or TMS Admin can modify a submitted Staff Payroll."),
		frappe.PermissionError,
	)


def enqueue_component_backfill(doc, method=None):
	"""Fires on every save of a submitted Salary Structure (allow_on_submit lets
	an allowed admin add/remove/edit component rows -- see restrict_component_edit_
	after_submit above). Re-saving each linked Staff Payroll, submitted or not,
	makes update_salary_components() (staff_payroll.py) pick up any component
	that's in the structure but missing from that record's table, appending it
	at amount=0 so historical net_salary/GL totals are untouched."""
	if doc.docstatus != 1:
		return
	frappe.enqueue(
		"logicore.overrides.salary_structure.backfill_staff_payroll_components",
		queue="long",
		job_name=f"backfill_staff_payroll_components_{doc.name}",
		salary_structure=doc.name,
	)


def backfill_staff_payroll_components(salary_structure):
	names = frappe.get_all(
		"Staff Payroll",
		filters={"salary_structure": salary_structure, "docstatus": ("!=", 2)},
		pluck="name",
	)
	for name in names:
		try:
			payroll = frappe.get_doc("Staff Payroll", name)
			payroll.flags.ignore_component_restriction = True
			payroll.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(), f"Failed to backfill salary components on Staff Payroll {name}"
			)
	frappe.db.commit()
