# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from logicore.utils.account_balance_utils import refresh_current_balance


class AccountLedger(Document):
	# Rows only ever come from a linked transaction being submitted/saved (see
	# account_balance_utils.py) — never typed in by hand, not even by an admin
	# role that technically has create permission via the "+ Add" button. That
	# button existing at all is a UI artifact of having create=1 for
	# Administrator/System Manager/TMS ADMIN to satisfy other framework
	# affordances (e.g. Data Import); the actual path is always automated.
	# account_balance_utils.py flags itself via
	# frappe.flags.tms_internal_ledger_write to get through this guard.
	def before_insert(self):
		if frappe.flags.tms_internal_ledger_write:
			return
		frappe.throw(
			_(
				"Account Ledger rows can't be created directly. They're written "
				"automatically when a linked transaction (Vendor Payment, Payment, "
				"Receipt, Fuel Urea Expenses, Staff Payroll, Tyre/Battery Expenses, "
				"Repair Expenses, Compliances, Service Logs, Supplier Payment) is "
				"submitted or saved."
			)
		)

	def validate(self):
		if self.amount is not None and self.amount < 0:
			frappe.throw(_("Amount must be positive — use Direction to indicate money in vs money out."))

	# Normally these rows are only written by a source document's on_submit
	# (which refreshes the affected accounts itself). A TMS Admin can still edit
	# one by hand, though, so recompute here too — otherwise Account Head's
	# cached current_balance would silently drift away from the ledger it is
	# supposed to summarise.
	def on_update(self):
		previous = self.get_doc_before_save()
		if previous and previous.account and previous.account != self.account:
			refresh_current_balance(previous.account)
		refresh_current_balance(self.account)

	def after_delete(self):
		refresh_current_balance(self.account)

	# A ledger row is never the source of truth for whether money moved — the
	# transaction it's linked to (reference_doctype/reference_name) is. Deleting
	# the row directly would leave that transaction still Submitted/Paid while
	# its ledger footprint silently vanishes, so the only sanctioned way to
	# remove one is to cancel/delete the transaction, which routes back through
	# account_balance_utils.py's own housekeeping (opening-balance cleared, a
	# save-based document's leg going away) — that code flags itself via
	# frappe.flags.tms_internal_ledger_write to get through this guard.
	def on_trash(self):
		if frappe.flags.tms_internal_ledger_write:
			return
		frappe.throw(
			_(
				"Account Ledger rows can't be deleted directly. "
				"Cancel or delete {0} {1} instead — its ledger entry will be removed automatically."
			).format(_(self.reference_doctype), self.reference_name)
		)
