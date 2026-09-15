# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import formatdate, getdate

from logicore.utils.bank_reconciliation_utils import (
	compute_opening_closing_balance,
	extract_statement_footer_balances,
	match_transactions,
	parse_statement_file,
)
from logicore.utils.date_utils import get_fy_key
from logicore.utils.supplier_payment_reconciliation import on_reconciliation_changed


class TMSBankReconciliation(Document):

	def autoname(self):
		self.name = make_autoname(f"BRC-{get_fy_key()}-.#####")

	def validate(self):
		self._validate_no_other_draft_for_account()
		self._validate_not_earlier_than_first_period()

	def _validate_no_other_draft_for_account(self):
		"""Only one Draft TMS Bank Reconciliation may exist per Bank Account at
		a time — submit (or delete) the existing one before starting another,
		so two drafts can never both try to match the same underlying
		transactions against overlapping statement periods."""
		if not self.bank_account:
			return
		existing = frappe.db.get_value(
			"TMS Bank Reconciliation",
			{"bank_account": self.bank_account, "docstatus": 0, "name": ["!=", self.name or ""]},
			"name",
		)
		if existing:
			frappe.throw(
				_(
					"A Draft Bank Reconciliation ({0}) already exists for this Bank Account. "
					"Submit or delete it before creating another."
				).format(existing)
			)

	def _validate_not_earlier_than_first_period(self):
		"""Once this Bank Account's very first reconciliation period has been
		recorded, nothing earlier can be added after the fact — e.g. if
		01-07-2026 to 31-07-2026 was reconciled first, a June period can't be
		created later. Reconciliations must build forward in time from
		whichever period was entered first; going back to insert an earlier
		gap would let the same real transaction be eligible for two
		overlapping-in-time reconciliations of the same account."""
		if not self.bank_account or not self.from_date:
			return
		earliest_row = frappe.db.get_all(
			"TMS Bank Reconciliation",
			filters={"bank_account": self.bank_account, "docstatus": ["!=", 2], "name": ["!=", self.name or ""]},
			fields=["from_date"],
			order_by="from_date asc",
			limit_page_length=1,
		)
		earliest = earliest_row[0].from_date if earliest_row else None
		if earliest and getdate(self.from_date) < getdate(earliest):
			frappe.throw(
				_(
					"This Bank Account's first reconciliation period starts {0} — an earlier "
					"period (From Date {1}) cannot be added after the fact."
				).format(formatdate(earliest, "dd-mm-yyyy"), formatdate(self.from_date, "dd-mm-yyyy"))
			)

	def before_submit(self):
		if not self.transactions:
			frappe.throw(_("Run Parse & Match before submitting — there are no transactions to reconcile."))
		unresolved = [row for row in self.transactions if not row.matched_docname]
		if unresolved:
			rows = ", ".join(str(row.row_number) for row in unresolved)
			frappe.throw(
				_("Row(s) {0}: every transaction must be matched before submitting.").format(rows)
			)

	def on_submit(self):
		for row in self.transactions:
			self._set_reconciled_flag(row, reconciled=True)

	def on_cancel(self):
		for row in self.transactions:
			self._set_reconciled_flag(row, reconciled=False)

	def _set_reconciled_flag(self, row, reconciled: bool):
		if not row.matched_docname or not row.matched_source:
			return
		source = frappe.db.get_value(
			"TMS Reconciliation Source", row.matched_source,
			["direction", "reconciled_fieldname", "reconciliation_link_fieldname",
			 "credit_reconciled_fieldname", "credit_reconciliation_link_fieldname"],
			as_dict=True,
		)
		# direction="Both" sources (e.g. Payment's "Bank Transfer" type) track
		# the Debit and Credit legs with separate flags on the same record —
		# route to whichever leg this transaction row's own direction is.
		if source.direction == "Both" and row.direction == "Credit":
			reconciled_fieldname = source.credit_reconciled_fieldname
			reconciliation_link_fieldname = source.credit_reconciliation_link_fieldname
		else:
			reconciled_fieldname = source.reconciled_fieldname
			reconciliation_link_fieldname = source.reconciliation_link_fieldname
		frappe.db.set_value(
			row.matched_doctype, row.matched_docname,
			{
				reconciled_fieldname: 1 if reconciled else 0,
				reconciliation_link_fieldname: self.name if reconciled else None,
			},
		)
		# Legs whose reconciled state has to roll up onto another document —
		# Supplier Payment onto its Purchase Invoices — get their cascade here.
		# Every other leg is a no-op.
		on_reconciliation_changed(row.matched_doctype, row.matched_docname)

	@frappe.whitelist()
	def parse_and_match(self):
		if self.docstatus != 0:
			frappe.throw(_("Can only Parse & Match a Draft document."))
		if not self.statement_file:
			frappe.throw(_("Attach a statement file first."))

		parsed_rows = parse_statement_file(
			self.bank_account, self.reconciliation_setting, self.statement_file,
			self.from_date, self.to_date,
		)
		matched_rows = match_transactions(parsed_rows, self.bank_account, self.from_date, self.to_date)

		self.opening_balance, self.closing_balance = extract_statement_footer_balances(self.statement_file)
		if self.opening_balance is None or self.closing_balance is None:
			# Row-below-header footers (e.g. HDFC's Opening Balance/Closing Bal
			# summary) can carry the value the file genuinely doesn't have for
			# one side (or a layout the footer scan doesn't recognise at all)
			# — fall back to deriving whichever figure is still missing from
			# the parsed rows' own Balance Column, without discarding the
			# other figure the footer scan already found.
			fallback_opening, fallback_closing = compute_opening_closing_balance(parsed_rows)
			if self.opening_balance is None:
				self.opening_balance = fallback_opening
			if self.closing_balance is None:
				self.closing_balance = fallback_closing

		self.set("transactions", [])
		matched_count = unmatched_count = 0
		total_amount = total_matched_amount = 0.0
		for row in matched_rows:
			self.append("transactions", {
				"row_number": row.row_number,
				"transaction_date": row.transaction_date,
				"amount": row.amount,
				"direction": row.direction,
				"narration": row.narration,
				"reference_no": row.reference_no,
				"status": row.status,
				"matched_source": row.matched_source,
				"matched_doctype": row.matched_doctype,
				"matched_docname": row.matched_docname,
			})
			total_amount += row.amount
			if row.status == "Matched":
				matched_count += 1
				total_matched_amount += row.amount
			else:
				unmatched_count += 1

		self.total_transactions = len(matched_rows)
		self.matched_count = matched_count
		self.unmatched_count = unmatched_count
		self.total_amount = total_amount
		self.total_matched_amount = total_matched_amount
		self.save()
		return self.as_dict()
