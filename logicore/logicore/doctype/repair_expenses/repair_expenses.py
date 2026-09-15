# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class RepairExpenses(Document):
	def before_save(self):
		for row in self.repair_items or []:
			row.amount = flt(row.qty) * flt(row.rate)
		self.total_qty = sum(flt(row.qty) for row in (self.repair_items or []))
		self.amount = sum(flt(row.amount) for row in (self.repair_items or []))

	def validate(self):
		self._validate_reference_no_unique()

	def _validate_reference_no_unique(self):
		if not self.reference_no:
			return
		duplicate = frappe.db.get_value(
			"Repair Expenses",
			{"reference_no": self.reference_no, "name": ("!=", self.name or "")},
			"name",
		)
		if duplicate:
			frappe.throw(_("Reference No. {0} already used in {1}.").format(self.reference_no, duplicate))
