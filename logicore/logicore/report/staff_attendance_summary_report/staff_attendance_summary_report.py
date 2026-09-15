import frappe
from frappe import _

STATUS_FIELD = {
	"Present": "present",
	"Absent": "absent",
	"On Leave With Pay": "on_leave_with_pay",
	"On Leave Without Pay": "on_leave_without_pay",
	"Sunday/Holiday": "sunday_holiday",
}


def execute(filters=None):
	filters = filters or {}
	columns = get_columns(filters)
	data = get_data(filters)
	summary = get_summary(data, filters)
	return columns, data, None, None, summary


def get_summary(data, filters):
	employee_type = filters.get("employee_type") or "Employee"
	return [
		{
			"label": _("Total Active {0}s").format(employee_type),
			"value": len(data),
			"datatype": "Int",
			"indicator": "Blue",
		}
	]


def get_columns(filters):
	employee_type = (filters or {}).get("employee_type") or "Employee"

	columns = [
		{
			"fieldname": "employee_link",
			"label": _("Employee/Driver ID"),
			"fieldtype": "Dynamic Link",
			"options": "link_doctype",
			"width": 140,
		},
		{"fieldname": "link_doctype", "label": _("Type"), "fieldtype": "Data", "width": 0, "hidden": 1},
		{"fieldname": "employee_name", "label": _("Name"), "fieldtype": "Data", "width": 160},
	]

	if employee_type == "Employee":
		columns.append(
			{
				"fieldname": "designation",
				"label": _("Designation"),
				"fieldtype": "Link",
				"options": "Designation",
				"width": 130,
			}
		)

	columns.append(
		{"fieldname": "branch", "label": _("Branch"), "fieldtype": "Link", "options": "Branch", "width": 120}
	)

	columns += [
		{"fieldname": "total_marked", "label": _("Total Attendance Marked"), "fieldtype": "Int", "width": 130},
		{"fieldname": "present", "label": _("Present"), "fieldtype": "Int", "width": 90},
		{"fieldname": "absent", "label": _("Absent"), "fieldtype": "Int", "width": 90},
		{"fieldname": "on_leave_with_pay", "label": _("On Leave With Pay"), "fieldtype": "Int", "width": 130},
		{
			"fieldname": "on_leave_without_pay",
			"label": _("On Leave Without Pay"),
			"fieldtype": "Int",
			"width": 140,
		},
		{"fieldname": "sunday_holiday", "label": _("Sunday/Holiday"), "fieldtype": "Int", "width": 110},
	]
	return columns


def get_active_records(employee_type):
	if employee_type == "Driver":
		return frappe.db.get_all(
			"Driver",
			filters={"status": "Active"},
			fields=["name", "full_name as employee_name", "custom_branch as branch"],
			order_by="full_name asc",
		)

	return frappe.db.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name", "designation", "branch"],
		order_by="employee_name asc",
	)


def get_data(filters):
	employee_type = filters.get("employee_type") or "Employee"
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	active_records = get_active_records(employee_type)

	data_map = {}
	for rec in active_records:
		row = {
			"employee_link": rec.name,
			"link_doctype": employee_type,
			"employee_name": rec.employee_name,
			"branch": rec.branch,
			"total_marked": 0,
			"present": 0,
			"absent": 0,
			"on_leave_with_pay": 0,
			"on_leave_without_pay": 0,
			"sunday_holiday": 0,
		}
		if employee_type == "Employee":
			row["designation"] = rec.designation
		data_map[rec.name] = row

	if not data_map:
		return []

	conditions = ["sa.docstatus = 1", "sad.link_doctype = %(link_doctype)s"]
	args = {"link_doctype": employee_type}

	if from_date and to_date:
		conditions.append("sa.date BETWEEN %(from_date)s AND %(to_date)s")
		args["from_date"] = from_date
		args["to_date"] = to_date
	elif from_date:
		conditions.append("sa.date >= %(from_date)s")
		args["from_date"] = from_date
	elif to_date:
		conditions.append("sa.date <= %(to_date)s")
		args["to_date"] = to_date

	counts = frappe.db.sql(
		f"""
		SELECT sad.employee_link, sad.status, COUNT(*) AS cnt
		FROM `tabStaff Attendance Detail` sad
		JOIN `tabStaff Attendance` sa ON sa.name = sad.parent
		WHERE {" AND ".join(conditions)}
		GROUP BY sad.employee_link, sad.status
		""",
		args,
		as_dict=True,
	)

	for c in counts:
		row = data_map.get(c.employee_link)
		if not row:
			continue
		field = STATUS_FIELD.get(c.status)
		if field:
			row[field] = c.cnt
			row["total_marked"] += c.cnt

	return list(data_map.values())
