import frappe
from logicore.role_profile_sync import FRAPPE_SYSTEM_ROLES
from logicore.logicore.doctype.tms_user_group.tms_user_group import (
	PERM_MAP,
	_NO_EXPLICIT_DENY,
	_bulk_sync_custom_docperms,
	_get_managed_doctypes,
)


def execute():
	_cleanup_system_role_data()
	frappe.db.commit()
	_cleanup_no_explicit_deny_cdps()
	frappe.db.commit()
	_sync_role_disabled()
	frappe.db.commit()
	_fix_module_fields()
	frappe.db.commit()
	_sync_cdp_to_tug()
	frappe.db.commit()
	_sync_tug_to_cdp()
	frappe.db.commit()
	frappe.clear_cache()


def _cleanup_no_explicit_deny_cdps():
	"""Delete any Custom DocPerm rows for _NO_EXPLICIT_DENY doctypes.

	When ANY Custom DocPerm exists for a doctype, Frappe ignores ALL file-based DocPerms
	for that doctype — including other roles.  A stale deny CDP on e.g. TMS User Group
	therefore silently blocks System Manager from reading it, breaking navigation.
	"""
	for doctype in _NO_EXPLICIT_DENY:
		names = frappe.get_all("Custom DocPerm", filters={"parent": doctype}, pluck="name")
		if names:
			frappe.db.sql(
				f"DELETE FROM `tabCustom DocPerm` WHERE name IN ({','.join(['%s']*len(names))})",
				names,
			)
			frappe.clear_cache(doctype="Custom DocPerm")


def _cleanup_system_role_data():
	"""Remove system roles from TMS User Group and their Custom DocPerm records."""
	system_roles = list(FRAPPE_SYSTEM_ROLES)

	# Delete Custom DocPerm for system roles (we never manage these)
	frappe.db.sql(
		f"DELETE FROM `tabCustom DocPerm` WHERE role IN ({','.join(['%s']*len(system_roles))})",
		system_roles
	)

	# Delete TMS User Group permission rows for system roles
	system_tugs = frappe.get_all(
		"TMS User Group",
		filters={"group_name": ["in", system_roles]},
		pluck="name"
	)
	for tug_name in system_tugs:
		frappe.db.sql("DELETE FROM `tabTMS User Group Permission` WHERE parent=%s", tug_name)
		frappe.delete_doc("TMS User Group", tug_name, ignore_permissions=True, force=True)


def _create_missing_user_groups():
	"""Create TMS User Group for every enabled non-system Role that doesn't have one."""
	existing = set(frappe.get_all("TMS User Group", pluck="group_name"))
	for role_name in frappe.get_all("Role", filters={"disabled": 0}, pluck="name"):
		if role_name in FRAPPE_SYSTEM_ROLES or role_name in existing:
			continue
		frappe.get_doc({
			"doctype": "TMS User Group",
			"group_name": role_name,
			"is_active": 1,
		}).insert(ignore_permissions=True)

	# Remove any system roles that were accidentally added before
	system_tugs = frappe.get_all(
		"TMS User Group",
		filters={"group_name": ["in", list(FRAPPE_SYSTEM_ROLES)]},
		pluck="name"
	)
	for tug_name in system_tugs:
		frappe.delete_doc("TMS User Group", tug_name, ignore_permissions=True, force=True)


def _sync_role_disabled():
	"""Mirror Role.disabled → TMS User Group.is_active."""
	for g in frappe.get_all("TMS User Group", fields=["name", "group_name", "is_active"]):
		role_disabled = frappe.db.get_value("Role", g["group_name"], "disabled")
		if role_disabled is None:
			continue
		expected = 0 if role_disabled else 1
		if g["is_active"] != expected:
			frappe.db.set_value("TMS User Group", g["name"], "is_active", expected, update_modified=False)


def _fix_module_fields():
	"""Fill missing module on TMS User Group Permission rows."""
	rows = frappe.get_all(
		"TMS User Group Permission",
		filters=[["module", "in", ["", None]]],
		fields=["name", "document_type"],
	)
	for row in rows:
		module = frappe.db.get_value("DocType", row.document_type, "module") or ""
		if module:
			frappe.db.set_value("TMS User Group Permission", row.name, "module", module, update_modified=False)


def _sync_cdp_to_tug():
	"""Mirror existing Custom DocPerm → TMS User Group permission rows."""
	groups = {g.group_name: g.name for g in frappe.get_all("TMS User Group", fields=["name", "group_name"])}
	cdp_records = frappe.get_all(
		"Custom DocPerm",
		filters={"role": ["in", list(groups.keys())], "permlevel": 0},
		fields=["name", "parent", "role"] + list(PERM_MAP.keys()),
	)

	by_group = {}
	for cdp in cdp_records:
		gname = groups.get(cdp.role)
		if gname:
			by_group.setdefault(gname, []).append(cdp)

	for gname, cdp_list in by_group.items():
		group = frappe.get_doc("TMS User Group", gname)
		perm_by_dt = {r.document_type: r for r in group.permissions}
		changed = False

		for cdp in cdp_list:
			module = frappe.db.get_value("DocType", cdp.parent, "module") or ""
			if not module:
				continue
			perm_vals = {cf: int(bool(cdp.get(ff))) for ff, cf in PERM_MAP.items()}
			row = perm_by_dt.get(cdp.parent)
			if row:
				if not row.get("module"):
					row.set("module", module)
					changed = True
				for cf, val in perm_vals.items():
					if row.get(cf) != val:
						row.set(cf, val)
						changed = True
			else:
				group.append("permissions", {"document_type": cdp.parent, "module": module, **perm_vals})
				changed = True

		if changed:
			group.flags.ignore_permissions = True
			group.flags.skip_custom_docperm_sync = True
			group.save(ignore_permissions=True)
			frappe.db.commit()


def _sync_tug_to_cdp():
	"""Mirror TMS User Group permissions → Custom DocPerm (bulk, fast).
	All managed doctypes not granted get explicit all-zero Custom DocPerm (deny).
	"""
	for g in frappe.get_all("TMS User Group", fields=["name", "group_name"]):
		role = g["group_name"]
		if role in FRAPPE_SYSTEM_ROLES:
			continue
		if frappe.db.get_value("Role", role, "disabled"):
			continue
		try:
			group = frappe.get_doc("TMS User Group", g["name"])
			_bulk_sync_custom_docperms(role, group.permissions)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"TMS User Group perm sync failed for {role}")
