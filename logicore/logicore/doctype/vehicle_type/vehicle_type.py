# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from logicore.utils.renaming import apply_pending_rename, capture_rename_target


class VehicleType(Document):
	def validate(self):
		if self.upto_day and self.upto_day > 99:
			frappe.throw("Up To Days must be a 2-digit number (0-99)")

	def before_save(self):
		capture_rename_target(self, "name1")

	def on_update(self):
		apply_pending_rename(self)
