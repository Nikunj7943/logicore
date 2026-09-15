import frappe

SIDEBAR = "LogiCore"
RENAMES = {
	"TMS Stock Ledger": "Stock Ledger",
	"TMS Stock Summary": "Stock Summary",
}


def run():
	doc = frappe.get_doc("Workspace Sidebar", SIDEBAR)

	changed = False
	for row in doc.items:
		if row.link_to in RENAMES and row.label != RENAMES[row.link_to]:
			row.label = RENAMES[row.link_to]
			changed = True

	if not changed:
		print("Nothing to rename — labels already match.")
		return

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	for row in doc.items:
		if row.link_to in RENAMES:
			print(f"  {row.link_to} -> label: {row.label}")
