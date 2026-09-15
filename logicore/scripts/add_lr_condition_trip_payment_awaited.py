import frappe

OLD = "trip_payment_awaited:   [['release_date_time','is','set'],['bill_nodate','is','set'],['bill_date','is','set'],['date_bill_credited','is','not set'],['trip_status','!=','Cancel']],"
NEW = "trip_payment_awaited:   [['release_date_time','is','set'],['lr_no','is','set'],['bill_nodate','is','set'],['bill_date','is','set'],['date_bill_credited','is','not set'],['trip_status','!=','Cancel']],"


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
	print("Updated TMS Trip Operations block: added lr_no condition to trip_payment_awaited")
