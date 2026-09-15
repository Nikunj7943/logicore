import frappe

from logicore.tms_navigation_visibility import _get_user_tms_group_candidates


def add_tms_report_menu_bootinfo(bootinfo):
	bootinfo.tms_can_use_admin_report_menu = is_tms_report_menu_admin(frappe.session.user)


def is_tms_report_menu_admin(user=None):
	user = user or frappe.session.user

	if user == "Administrator":
		return True

	if "System Manager" in frappe.get_roles(user):
		return True

	for group_name in _get_user_tms_group_candidates(user):
		if frappe.db.get_value("TMS User Group", group_name, "is_admin"):
			return True

	return False
