import frappe
from frappe.utils import now_datetime


def execute():
	method = "logicore.logicore.doctype.vehicle_finance.vehicle_finance.create_emi_payments_for_today"
	existing = frappe.db.get_value("Scheduled Job Type", {"method": method}, "name")
	today_midnight = now_datetime().strftime("%Y-%m-%d 00:00:00")
	if existing:
		frappe.db.sql(
			"UPDATE `tabScheduled Job Type` SET cron_format='0 23 * * *', last_execution=%s WHERE name=%s",
			(today_midnight, existing),
		)
	else:
		frappe.get_doc({
			"doctype": "Scheduled Job Type",
			"method": method,
			"frequency": "Cron",
			"cron_format": "0 23 * * *",
		}).insert(ignore_permissions=True)
		frappe.db.sql(
			"UPDATE `tabScheduled Job Type` SET last_execution=%s WHERE method=%s",
			(today_midnight, method),
		)
	frappe.db.commit()
