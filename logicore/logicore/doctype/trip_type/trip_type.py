# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from logicore.utils.renaming import apply_pending_rename, capture_rename_target


class TripType(Document):
    def validate(self):
        if self.code:
            if len(self.code) > 5:
                frappe.throw("Code must be 1–5 characters (e.g. P, ST, SPC)")
            if not self.code.isalpha():
                frappe.throw("Code must contain only alphabet letters (e.g. P, ST, SC)")
            self.code = self.code.upper()

    def before_save(self):
        capture_rename_target(self, "trip_type")

    def on_update(self):
        apply_pending_rename(self)