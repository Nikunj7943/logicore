# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from logicore.utils.account_balance_utils import get_account_balance, sync_opening_balance_entry


class AccountHead(Document):
	def before_save(self):
		# A brand-new record isn't in the DB yet, so Account Ledger's
		# Link field to it would fail to validate — that leg is handled by
		# after_insert() instead, once this row actually exists.
		if self.group in ("BANK", "CASH") and not self.is_new():
			sync_opening_balance_entry(self.name, self.opening_balance, self.opening_balance_date)
			self.current_balance = get_account_balance(self.name)

	def after_insert(self):
		if self.group in ("BANK", "CASH"):
			sync_opening_balance_entry(self.name, self.opening_balance, self.opening_balance_date)
			frappe.db.set_value(
				self.doctype, self.name, "current_balance", get_account_balance(self.name), update_modified=False
			)
