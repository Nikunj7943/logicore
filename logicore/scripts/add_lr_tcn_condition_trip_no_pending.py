import frappe

OLD = "trip_no_pending:        [['trip_no_not_yet_provided','=',1],['trip_status','!=','Cancel']],"
NEW = "trip_no_pending:        [['trip_no_not_yet_provided','=',1],['lr_no','is','set'],['tcntrip_no','is','not set'],['trip_status','!=','Cancel']],"


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
	print("Updated TMS Trip Operations block: added lr_no + tcntrip_no condition to trip_no_pending")
