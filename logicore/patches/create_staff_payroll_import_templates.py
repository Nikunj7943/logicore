import json

import frappe

OLD_EARNINGS = [
	("old_basic_salary", "Basic Salary"),
	("old_incentive", "Incentive"),
	("old_bonus", "Bonus"),
	("old_reimbursement", "Reimbursement"),
	("old_accident_insurance", "Accident Insurance"),
	("old_medical_insurance", "Medical Insurance"),
]

OLD_DEDUCTIONS = [
	("old_other_deductions", "Other Deductions"),
	("old_leave_deductions", "Leave Deductions"),
	("old_paid_incentive", "Paid Incentive"),
]


def execute():
	_create_template(
		name="Staff Payroll Import - Driver",
		person_field="driver",
		person_label="Driver",
		salary_type="Driver Salary",
	)
	_create_template(
		name="Staff Payroll Import - Employee",
		person_field="employee",
		person_label="Employee",
		salary_type="Employee Salary",
	)
	_create_old_template(
		name="Payroll Import Old - Driver",
		person_field="driver",
		person_label="Driver",
		salary_type="Driver Salary",
	)
	_create_old_template(
		name="Payroll Import Old - Employee",
		person_field="employee",
		person_label="Employee",
		salary_type="Employee Salary",
	)


def _create_template(name, person_field, person_label, salary_type):
	if frappe.db.exists("Import Template", name):
		return
	columns = [
		{"csv_header": person_label, "fieldname": person_field, "required": 1, "is_match_key": 1},
		{"csv_header": "From Date", "fieldname": "from_date", "required": 1, "is_match_key": 1},
		{"csv_header": "To Date", "fieldname": "to_date", "required": 1, "is_match_key": 1},
		{"csv_header": "Payroll Date", "fieldname": "payroll_date", "required": 1},
		{"csv_header": "Payment Mode", "fieldname": "payment_mode", "required": 0, "default_value": "Bank Transfer"},
		{"csv_header": "Bank Account", "fieldname": "bank_account", "required": 1},
		{"csv_header": "Salary Type", "fieldname": "salary_type", "required": 0, "default_value": salary_type},
	]
	doc = frappe.get_doc({
		"doctype": "Import Template",
		"template_name": name,
		"target_doctype": "Staff Payroll",
		"is_active": 1,
		"default_import_mode": "Create New Only",
		"import_action": "None",
		"columns_json": json.dumps(columns),
	})
	doc.insert(ignore_permissions=True)


def _create_old_template(name, person_field, person_label, salary_type):
	if frappe.db.exists("Import Template", name):
		return
	columns = [
		{"csv_header": person_label, "fieldname": person_field, "required": 1, "is_match_key": 1},
		{"csv_header": "From Date", "fieldname": "from_date", "required": 1, "is_match_key": 1},
		{"csv_header": "To Date", "fieldname": "to_date", "required": 1, "is_match_key": 1},
		{"csv_header": "Payroll Date", "fieldname": "payroll_date", "required": 1},
		{"csv_header": "Payment Mode", "fieldname": "payment_mode", "required": 0, "default_value": "Bank Transfer"},
		{"csv_header": "Bank Account", "fieldname": "bank_account", "required": 1},
		{"csv_header": "Salary Type", "fieldname": "salary_type", "required": 0, "default_value": salary_type},
	]
	for fieldname, header in OLD_EARNINGS:
		columns.append(
			{
				"csv_header": header,
				"fieldname": fieldname,
				"required": 0,
			}
		)
	for fieldname, header in OLD_DEDUCTIONS:
		columns.append(
			{
				"csv_header": header,
				"fieldname": fieldname,
				"required": 0,
			}
		)
	doc = frappe.get_doc({
		"doctype": "Import Template",
		"template_name": name,
		"target_doctype": "Staff Payroll",
		"is_active": 1,
		"default_import_mode": "Create New Only",
		"import_action": "None",
		"columns_json": json.dumps(columns),
	})
	doc.insert(ignore_permissions=True)
