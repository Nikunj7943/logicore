import frappe

SIDEBAR = "LogiCore"
LINK_TO = "Account Ledger"
AFTER_LABEL = "TDS Report"


def run():
	doc = frappe.get_doc("Workspace Sidebar", SIDEBAR)

	row_idx = next((i for i, row in enumerate(doc.items) if row.link_to == LINK_TO), None)
	if row_idx is None:
		frappe.throw(f'Could not find a sidebar row linking to "{LINK_TO}".')

	row = doc.items.pop(row_idx)

	anchor = next((i for i, r in enumerate(doc.items) if r.label == AFTER_LABEL), None)
	if anchor is None:
		frappe.throw(f'Could not find the "{AFTER_LABEL}" row to insert after.')

	doc.items.insert(anchor + 1, row)

	for i, r in enumerate(doc.items, start=1):
		r.idx = i

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	print(f'Moved "{LINK_TO}" to idx {anchor + 2} (right after "{AFTER_LABEL}").')
	for r in doc.items[max(anchor - 1, 0):anchor + 4]:
		print(f"  idx {r.idx}: {r.label} (type={r.type}, child={r.child}, link_to={r.link_to})")
