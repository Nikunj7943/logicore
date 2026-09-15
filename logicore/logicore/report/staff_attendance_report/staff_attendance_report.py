import frappe
from frappe import _


STATUS_INDICATOR = {
	"Present": "Green",
	"Absent": "Red",
	"On Leave With Pay": "Orange",
	"On Leave Without Pay": "Orange",
	"Sunday/Holiday": "Grey",
}


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	summary = get_summary(data)
	return columns, data, None, None, summary


def get_summary(data):
	counts = {status: 0 for status in STATUS_INDICATOR}
	for row in data:
		if row.status in counts:
			counts[row.status] += 1

	summary = [
		{"label": _("Total Attendance Marked"), "value": len(data), "datatype": "Int", "indicator": "Blue"}
	]
	summary += [
		{"label": _(status), "value": counts[status], "datatype": "Int", "indicator": indicator}
		for status, indicator in STATUS_INDICATOR.items()
	]
	return summary


def get_columns():
	return [
		{"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
		{
			"fieldname": "attendance_no",
			"label": _("Attendance Record"),
			"fieldtype": "Link",
			"options": "Staff Attendance",
			"width": 130,
		},
		{
			"fieldname": "employee_link",
			"label": _("Employee/Driver ID"),
			"fieldtype": "Dynamic Link",
			"options": "link_doctype",
			"width": 140,
		},
		{"fieldname": "link_doctype", "label": _("Type"), "fieldtype": "Data", "width": 0, "hidden": 1},
		{"fieldname": "employee_name", "label": _("Name"), "fieldtype": "Data", "width": 160},
		{"fieldname": "designation", "label": _("Designation"), "fieldtype": "Data", "width": 130},
		{"fieldname": "branch", "label": _("Branch"), "fieldtype": "Data", "width": 120},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 150},
		{"fieldname": "work_at", "label": _("Work At"), "fieldtype": "Data", "width": 110},
	]


def get_data(filters):
	employee_type = filters.get("employee_type") or "Employee"
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	selected_ids = filters.get("employee") if employee_type == "Employee" else filters.get("driver")
	selected_statuses = filters.get("status")

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

	if selected_ids:
		conditions.append("sad.employee_link IN %(selected_ids)s")
		args["selected_ids"] = tuple(selected_ids)

	if selected_statuses:
		conditions.append("sad.status IN %(selected_statuses)s")
		args["selected_statuses"] = tuple(selected_statuses)

	rows = frappe.db.sql(
		f"""
		SELECT
			sa.date, sa.name AS attendance_no, sad.link_doctype, sad.employee_link, sad.employee_name,
			sad.designation, sad.branch, sad.status, sad.work_at
		FROM `tabStaff Attendance Detail` sad
		JOIN `tabStaff Attendance` sa ON sa.name = sad.parent
		WHERE {" AND ".join(conditions)}
		ORDER BY sa.date ASC, sad.employee_name ASC
		""",
		args,
		as_dict=True,
	)

	return rows
