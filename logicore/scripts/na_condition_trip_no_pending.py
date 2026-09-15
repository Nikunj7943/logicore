import frappe

OLD = "trip_no_pending:        [['trip_no_not_yet_provided','=',1],['lr_no','is','set'],['tcntrip_no','is','not set'],['trip_status','!=','Cancel']],\n"
NEW = ""


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
	print(
		"Updated TMS Trip Operations block: removed trip_no_pending from ROUTE_FILTERS "
		"(now falls back to exact-match get_trip_operations_records since tcntrip_no "
		"blank-OR-NA can't be expressed as a simple AND field filter)"
	)
