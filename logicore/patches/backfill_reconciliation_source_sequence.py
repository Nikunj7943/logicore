import frappe


def execute():
	"""Assign a sequence number to any existing TMS Reconciliation Source row
	that doesn't have one yet, in creation order — the field is auto-set on
	insert going forward, but rows created before it existed are left at the
	column default (0)."""
	frappe.reload_doc("logicore", "doctype", "tms_reconciliation_source")

	rows = frappe.get_all(
		"TMS Reconciliation Source",
		filters={"sequence": ["in", (0, None)]},
		fields=["name"],
		order_by="creation asc",
	)
	if not rows:
		return

	next_sequence = (
		frappe.db.sql("select max(sequence) from `tabTMS Reconciliation Source`")[0][0] or 0
	) + 1
	for row in rows:
		frappe.db.set_value("TMS Reconciliation Source", row.name, "sequence", next_sequence)
		next_sequence += 1
	frappe.db.commit()
