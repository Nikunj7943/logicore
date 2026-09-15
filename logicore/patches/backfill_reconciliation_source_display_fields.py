import frappe

DISPLAY_FIELDNAMES_BY_LABEL = {
	"Vendor Payment": "vendor,reference_no",
	"Supplier Payment": "supplier,reference_no",
	"Receipt": "customer,reference_no",
	"Payment": "type,reference_no",
	"Fuel Urea Expenses - Supplier": "vehicle,supplier",
	"Fuel Urea Expenses - Driver Incentive": "vehicle,driver_id",
	"Repair Expenses": "vehicle_id,vendor",
	"Tyre Expenses": "vehicle_id,vendor",
	"Battery Expenses": "vehicle_id,vendor",
	"Compliances": "vehicle,document_type",
	"Service Logs": "vehicle_no,service_type",
	"Staff Payroll": "salary_type,employee_name",
}


def execute():
	"""Backfill display_fieldnames on existing TMS Reconciliation Source rows
	(the field is set on fresh inserts going forward via install.py, but rows
	created before it existed are left blank)."""
	frappe.reload_doc("logicore", "doctype", "tms_reconciliation_source")

	for label, display_fieldnames in DISPLAY_FIELDNAMES_BY_LABEL.items():
		if not frappe.db.exists("TMS Reconciliation Source", label):
			continue
		current = frappe.db.get_value("TMS Reconciliation Source", label, "display_fieldnames")
		if not current:
			frappe.db.set_value(
				"TMS Reconciliation Source", label, "display_fieldnames", display_fieldnames
			)
	frappe.db.commit()
