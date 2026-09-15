# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from logicore.utils.renaming import apply_pending_rename, capture_rename_target


class BusinessFormat(Document):
	def before_save(self):
		capture_rename_target(self, "business_format")

	def on_update(self):
		apply_pending_rename(self)
