import frappe

SIDEBAR = "LogiCore"
AFTER_LABEL = "Supplier Payment"
LABEL = "Stock Entry"
LINK_TO = "Stock Entry"


def run():
	doc = frappe.get_doc("Workspace Sidebar", SIDEBAR)

	if any(row.link_to == LINK_TO and row.link_type == "DocType" for row in doc.items):
		print(f'"{LABEL}" is already in the {SIDEBAR} sidebar — nothing to do.')
		return

	anchor = next((i for i, row in enumerate(doc.items) if row.label == AFTER_LABEL), None)
	if anchor is None:
		frappe.throw(f'Could not find the "{AFTER_LABEL}" row to insert after.')

	new_row = frappe.new_doc("Workspace Sidebar Item")
	new_row.update({
		"label": LABEL,
		"type": "Link",
		"link_type": "DocType",
		"link_to": LINK_TO,
		"child": 1,
		"icon": "🔄",
		"parent": SIDEBAR,
		"parenttype": "Workspace Sidebar",
		"parentfield": "items",
	})
	doc.items.insert(anchor + 1, new_row)

	for i, row in enumerate(doc.items, start=1):
		row.idx = i

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	print(f'Inserted "{LABEL}" at idx {anchor + 2}. Sidebar now has {len(doc.items)} items.')
	for row in doc.items[anchor - 1 : anchor + 4]:
		print(f"  idx {row.idx}: {row.label} (type={row.type}, link_type={row.link_type}, child={row.child})")
