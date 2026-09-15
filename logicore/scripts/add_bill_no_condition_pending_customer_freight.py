import frappe

OLD = "pending_customer_freight: [['lr_no','is','set'],['customer_freight','<=',0],['trip_status','!=','Cancel']],"
NEW = "pending_customer_freight: [['lr_no','is','set'],['customer_freight','<=',0],['bill_nodate','is','not set'],['trip_status','!=','Cancel']],"


def run():
	doc = frappe.get_doc("Custom HTML Block", "TMS Trip Operations")
	script = doc.script
	count = script.count(OLD)
	if count != 1:
		print(f"Expected exactly 1 match, found {count}. Aborting without changes.")
		return
	doc.script = script.replace(OLD, NEW)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	print("Updated TMS Trip Operations block: added bill_nodate condition to pending_customer_freight")
