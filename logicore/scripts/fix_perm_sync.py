import frappe
from logicore.logicore.doctype.tms_user_group.tms_user_group import PERM_MAP


def run():
	groups = {g.group_name: g.name for g in frappe.get_all("TMS User Group", fields=["name", "group_name"])}

	cdp_records = frappe.get_all(
		"Custom DocPerm",
		filters={"role": ["in", list(groups.keys())], "permlevel": 0},
		fields=["name", "parent", "role"] + list(PERM_MAP.keys()),
	)

	print(f"Custom DocPerm records to sync: {len(cdp_records)}")

	# Pre-pass: fix missing module field on all existing permission rows
	frappe.db.sql("""
		UPDATE `tabTMS User Group Permission` p
		JOIN `tabDocType` dt ON dt.name = p.document_type
		SET p.module = dt.module
		WHERE (p.module IS NULL OR p.module = '')
	""")
	frappe.db.commit()
	print("Pre-pass: fixed missing module fields")

	# Group by TMS User Group to minimise saves
	by_group = {}
	for cdp in cdp_records:
		gname = groups.get(cdp.role)
		if gname:
			by_group.setdefault(gname, []).append(cdp)

	fixed = 0
	for gname, cdp_list in by_group.items():
		group = frappe.get_doc("TMS User Group", gname)
		perm_by_dt = {r.document_type: r for r in group.permissions}
		changed = False

		for cdp in cdp_list:
			module = frappe.db.get_value("DocType", cdp.parent, "module") or ""
			if not module:
				continue  # skip doctypes with no module (e.g. uninstalled apps)
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
			print(f"  Fixed: {gname}")
			fixed += 1

	frappe.db.commit()
	print(f"\nDone. Fixed {fixed} TMS User Group records.")
