# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TMSReconciliationSource(Document):
	def before_insert(self):
		if not self.sequence:
			max_sequence = frappe.db.sql(
				"select max(sequence) from `tabTMS Reconciliation Source`"
			)[0][0]
			self.sequence = (max_sequence or 0) + 1
