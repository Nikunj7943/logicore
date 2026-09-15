import frappe


def execute():
	"""Cleanup for the default-supplier feature.

	- Drop the obsolete Supplier-default_for_company custom field.
	- Delete helper Server Scripts and Client Script that used to sync
	  Supplier.represents_company (no longer needed — Company keeps the link).
	- Clear any represents_company values previously auto-set so the
	  (now hidden) field doesn't carry stale data.
	"""
	cf_name = "Supplier-default_for_company"
	if frappe.db.exists("Custom Field", cf_name):
		frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True, force=True)

	for ss in ("Company Default Supplier Sync", "Supplier Default Company Lock"):
		if frappe.db.exists("Server Script", ss):
			frappe.delete_doc("Server Script", ss, ignore_permissions=True, force=True)

	cs = "Supplier Lock Company If Default"
	if frappe.db.exists("Client Script", cs):
		frappe.delete_doc("Client Script", cs, ignore_permissions=True, force=True)

	if frappe.db.has_column("Company", "default_supplier"):
		companies = frappe.get_all(
			"Company",
			filters={"default_supplier": ["is", "set"]},
			fields=["name", "default_supplier"],
		)
		for c in companies:
			if c.default_supplier and frappe.db.exists("Supplier", c.default_supplier):
				current = frappe.db.get_value("Supplier", c.default_supplier, "represents_company")
				if current == c.name:
					frappe.db.set_value(
						"Supplier", c.default_supplier, "represents_company", None,
						update_modified=False,
					)

	frappe.db.commit()
