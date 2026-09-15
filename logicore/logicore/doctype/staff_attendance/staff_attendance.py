# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

_STATUS_MAP = {
	"Present": "Present",
	"Absent": "Absent",
	"On Leave With Pay": "On Leave",
	"On Leave Without Pay": "On Leave",
	# Sunday/Holiday has no HR Attendance equivalent — skipped
}


class StaffAttendance(Document):
	def after_insert(self):
		self.db_set("attendance_no", self.name)

	def validate(self):
		self._check_duplicate_date()

	def on_submit(self):
		_sync_hr_attendance(self, cancel=False)

	def on_cancel(self):
		_sync_hr_attendance(self, cancel=True)

	def _check_duplicate_date(self):
		filters = {
			"date": self.date,
			"employee_type": self.employee_type,
			"company": self.company,
			"docstatus": ["<", 2],
			"name": ["!=", self.name],
		}
		existing = frappe.db.get_value("Staff Attendance", filters, "name")
		if existing:
			frappe.throw(
				frappe._("Attendance for <b>{0}</b> ({1}) already exists: {2}").format(
					self.date, self.employee_type, existing
				),
				title=frappe._("Duplicate Attendance"),
			)


def _sync_hr_attendance(doc, cancel=False):
	"""Create / cancel ERPNext Attendance records for Employee rows on submit/cancel."""
	if doc.employee_type != "Employee":
		return

	for row in doc.attendance_details:
		if row.link_doctype != "Employee":
			continue

		hr_status = _STATUS_MAP.get(row.status)
		if not hr_status:
			continue  # Sunday/Holiday — no HR Attendance record needed

		existing = frappe.db.get_value(
			"Attendance",
			{
				"employee": row.employee_link,
				"attendance_date": doc.date,
				"docstatus": ["<", 2],
			},
			"name",
		)

		if cancel:
			if existing:
				att = frappe.get_doc("Attendance", existing)
				if att.docstatus == 1:
					att.cancel()
		else:
			if existing:
				att = frappe.get_doc("Attendance", existing)
				if att.docstatus == 0:
					att.status = hr_status
					att.save()
					att.submit()
			else:
				att = frappe.get_doc({
					"doctype": "Attendance",
					"employee": row.employee_link,
					"attendance_date": doc.date,
					"company": doc.company,
					"status": hr_status,
				})
				att.insert(ignore_permissions=True)
				att.submit()


def _get_previous_statuses(employee_type, current_date, company):
	"""Return {employee_link: status} from the most recent prior attendance record."""
	filters = [
		["docstatus", "!=", 2],
		["employee_type", "=", employee_type],
	]
	if company:
		filters.append(["company", "=", company])
	if current_date:
		filters.append(["date", "<", current_date])

	prev_docs = frappe.get_all(
		"Staff Attendance",
		filters=filters,
		fields=["name"],
		order_by="date desc",
		limit=1,
	)
	if not prev_docs:
		return {}

	rows = frappe.get_all(
		"Staff Attendance Detail",
		filters={"parent": prev_docs[0].name},
		fields=["employee_link", "status"],
	)
	return {r.employee_link: r.status for r in rows}


@frappe.whitelist()
def get_attendance_employees(employee_type, company=None, date=None):
	"""Return list of employees/drivers with status pre-filled from the previous attendance record."""
	prev_statuses = _get_previous_statuses(employee_type, date, company)
	rows = []

	if employee_type == "Employee":
		filters = {"status": "Active"}
		if company:
			filters["company"] = company

		employees = frappe.get_all(
			"Employee",
			filters=filters,
			fields=["name", "employee_name", "designation", "branch"],
			order_by="employee_name asc",
		)
		for emp in employees:
			status = prev_statuses.get(emp.name, "Present")
			rows.append({
				"link_doctype": "Employee",
				"employee_link": emp.name,
				"employee_name": emp.employee_name,
				"designation": emp.designation or "",
				"branch": emp.branch or "",
				"status": status,
				"work_at": "On Duty" if status == "Present" else "",
			})

	elif employee_type == "Driver":
		drivers = frappe.get_all(
			"Driver",
			filters={"status": "Active"},
			fields=["name", "full_name", "custom_branch"],
			order_by="full_name asc",
		)
		for drv in drivers:
			status = prev_statuses.get(drv.name, "Present")
			rows.append({
				"link_doctype": "Driver",
				"employee_link": drv.name,
				"employee_name": drv.full_name or drv.name,
				"designation": "Driver",
				"branch": drv.custom_branch or "",
				"status": status,
				"work_at": "On Duty" if status == "Present" else "",
			})

	return rows
