# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ServiceLogs(Document):
	def validate(self):
		self._validate_reference_no_unique()
		self._sync_next_service_date()

	def _sync_next_service_date(self):
		dates = [row.next_date for row in self.service_replacement_item if row.next_date]
		self.next_service_date = min(dates) if dates else None

	def _validate_reference_no_unique(self):
		if not self.reference_no:
			return
		duplicate = frappe.db.get_value(
			"Service Logs",
			{"reference_no": self.reference_no, "name": ("!=", self.name or "")},
			"name",
		)
		if duplicate:
			frappe.throw(_("Reference No. {0} already used in {1}.").format(self.reference_no, duplicate))


@frappe.whitelist()
def get_last_service_info(vehicle_no, current_name=None, current_voucher_date=None):
	filters = {"vehicle_no": vehicle_no}
	if current_name:
		filters["name"] = ("!=", current_name)
	if current_voucher_date:
		filters["voucher_date"] = ("<=", current_voucher_date)
	result = frappe.db.get_all(
		"Service Logs",
		filters=filters,
		fields=["voucher_date", "km"],
		order_by="voucher_date desc, creation desc",
		limit=1,
	)
	return result[0] if result else {}


@frappe.whitelist()
def get_last_service_item_info(vehicle_no, service_replacement, current_name=None, current_voucher_date=None):
	conditions = "sl.vehicle_no = %(vehicle_no)s AND sri.service_replacement = %(service_replacement)s"
	values = {"vehicle_no": vehicle_no, "service_replacement": service_replacement}
	if current_name:
		conditions += " AND sl.name != %(current_name)s"
		values["current_name"] = current_name
	if current_voucher_date:
		conditions += " AND sl.voucher_date <= %(current_voucher_date)s"
		values["current_voucher_date"] = current_voucher_date
	result = frappe.db.sql(
		f"""
		SELECT sl.voucher_date, sl.km
		FROM `tabService Logs` sl
		JOIN `tabService  Replacement Item` sri ON sri.parent = sl.name
		WHERE {conditions}
		ORDER BY sl.voucher_date DESC, sl.creation DESC
		LIMIT 1
		""",
		values,
		as_dict=True,
	)
	return result[0] if result else {}
