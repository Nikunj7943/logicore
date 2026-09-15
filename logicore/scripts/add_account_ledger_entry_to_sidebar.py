import frappe

SIDEBAR = "LogiCore"
NEW_LINK_TO = "Account Ledger Entry"
AFTER_LABEL = "Account Head"


def run():
	doc = frappe.get_doc("Workspace Sidebar", SIDEBAR)

	if any(row.link_to == NEW_LINK_TO for row in doc.items):
		print(f'"{NEW_LINK_TO}" is already in the {SIDEBAR} sidebar — nothing to do.')
		return

	anchor = next((i for i, row in enumerate(doc.items) if row.label == AFTER_LABEL), None)
	if anchor is None:
		frappe.throw(f'Could not find the "{AFTER_LABEL}" row to insert after.')

	new_row = frappe.new_doc("Workspace Sidebar Item")
	new_row.update({
		"label": "Account Ledger Entry",
		"type": "Link",
		"link_type": "DocType",
		"link_to": NEW_LINK_TO,
		# Link rows MUST have child=1 to nest under the preceding Section Break —
		# see find_nested_items() in frappe/public/js/frappe/ui/sidebar/sidebar.js.
		"child": 1,
		"icon": "📒",
		"parent": SIDEBAR,
		"parenttype": "Workspace Sidebar",
		"parentfield": "items",
	})

	doc.items.insert(anchor + 1, new_row)

	# Reassign idx across the whole list — Frappe does not renumber on insert, and
	# leaving stale idx values silently reorders/duplicates rows in the sidebar.
	for i, row in enumerate(doc.items, start=1):
		row.idx = i

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	print(f'Inserted "{NEW_LINK_TO}" at idx {anchor + 2}. Sidebar now has {len(doc.items)} items.')
	for row in doc.items[anchor - 1 : anchor + 3]:
		print(f"  idx {row.idx}: {row.label} (type={row.type}, child={row.child})")
