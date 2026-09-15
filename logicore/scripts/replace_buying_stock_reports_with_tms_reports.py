import frappe

SIDEBAR = "LogiCore"
AFTER_LABEL = "Supplier Payment"

REMOVE_LABELS = {
	"Stock Entry",
	"Stock Ledger",
	"Stock Balance",
	"Stock Projected Qty",
	"Stock Summary",
	"Stock Ageing",
	"Item Price Stock",
	"Warehouse Wise Stock Balance",
}

NEW_ROWS = [
	{"label": "TMS Stock Ledger", "link_to": "TMS Stock Ledger", "icon": "📒"},
	{"label": "TMS Stock Summary", "link_to": "TMS Stock Summary", "icon": "📃"},
]


def run():
	doc = frappe.get_doc("Workspace Sidebar", SIDEBAR)

	doc.items = [row for row in doc.items if row.label not in REMOVE_LABELS]

	anchor = next((i for i, row in enumerate(doc.items) if row.label == AFTER_LABEL), None)
	if anchor is None:
		frappe.throw(f'Could not find the "{AFTER_LABEL}" row to insert after.')

	for offset, spec in enumerate(NEW_ROWS, start=1):
		if any(row.link_to == spec["link_to"] for row in doc.items):
			continue
		new_row = frappe.new_doc("Workspace Sidebar Item")
		new_row.update({
			"label": spec["label"],
			"type": "Link",
			"link_type": "Report",
			"link_to": spec["link_to"],
			# Link rows MUST have child=1 to nest under the preceding Section Break —
			# see find_nested_items() in frappe/public/js/frappe/ui/sidebar/sidebar.js.
			"child": 1,
			"icon": spec["icon"],
			"parent": SIDEBAR,
			"parenttype": "Workspace Sidebar",
			"parentfield": "items",
		})
		doc.items.insert(anchor + offset, new_row)

	# Reassign idx across the whole list — Frappe does not renumber on insert/removal,
	# and leaving stale idx values silently reorders/duplicates rows in the sidebar.
	for i, row in enumerate(doc.items, start=1):
		row.idx = i

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	print(f"Buying section now has {len(doc.items)} total sidebar items (after removals/inserts).")
	for row in doc.items[anchor - 1 : anchor + len(NEW_ROWS) + 2]:
		print(f"  idx {row.idx}: {row.label} (type={row.type}, link_type={row.link_type}, child={row.child})")
