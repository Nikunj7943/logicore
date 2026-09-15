import frappe


def run():
	doc = frappe.get_doc("Workspace Sidebar", "LogiCore")
	for row in doc.items:
		kind = "child" if row.child else "top "
		print(f"{row.idx:>3} | {row.type:<14} | {kind} | {row.label!r:<35} | {row.link_to}")
