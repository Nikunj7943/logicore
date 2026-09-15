# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.utils import flt

UNRECONCILED = "Unreconciled"
PARTIALLY_RECONCILED = "Partially Reconciled"
RECONCILED = "Reconciled"

# Amounts are compared at 2 decimals so a rounding tail never leaves a fully
# settled invoice stuck on "Partially Reconciled".
PRECISION = 2


def on_reconciliation_changed(doctype: str, docname: str) -> None:
	"""Called by TMS Bank Reconciliation whenever it sets or clears a target
	record's reconciled flag. Only Supplier Payment cascades onto another
	doctype today — every other leg is a no-op here.
	"""
	if doctype != "Supplier Payment":
		return
	recalculate_for_supplier_payment(docname)


def recalculate_for_supplier_payment(supplier_payment: str) -> None:
	"""Refresh the bank-reconciliation status of every Purchase Invoice this
	Supplier Payment touches.
	"""
	invoices = frappe.db.get_all(
		"Payment Invoices",
		filters={"parent": supplier_payment, "parenttype": "Supplier Payment"},
		pluck="purchase_invoice",
	)
	for purchase_invoice in {inv for inv in invoices if inv}:
		recalculate_invoice_reconciliation(purchase_invoice)


def recalculate_invoice_reconciliation(purchase_invoice: str) -> None:
	"""Recompute `custom_reconciled_amount` / `custom_bank_reconciliation_status`
	on one Purchase Invoice from scratch.

	Deliberately a full recompute rather than an incremental +/-: the same
	invoice can be reconciled and un-reconciled through several different TMS
	Bank Reconciliations, and Supplier Payments against it can be cancelled or
	amended in between. Summing the current truth every time keeps the two
	fields correct no matter what order those events arrive in, and makes the
	function safe to call twice.

	Note the amount summed is `payment_amount`, not `transfer_amount`: the bank
	statement matches the post-TDS transfer, but what settles the invoice is the
	pre-TDS payment — the same basis `custom_total_paid` uses.
	"""
	invoice = frappe.db.get_value(
		"Purchase Invoice", purchase_invoice, ["grand_total"], as_dict=True
	)
	if not invoice:
		return

	reconciled_amount = flt(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(spi.payment_amount), 0)
			FROM `tabPayment Invoices` spi
			JOIN `tabSupplier Payment` sp ON sp.name = spi.parent
			WHERE spi.purchase_invoice = %s
			  AND spi.parenttype = 'Supplier Payment'
			  AND sp.docstatus = 1
			  AND sp.is_reconciled = 1
			""",
			purchase_invoice,
		)[0][0]
	)

	grand_total = flt(invoice.grand_total, PRECISION)
	reconciled_amount = flt(reconciled_amount, PRECISION)

	if reconciled_amount <= 0:
		status = UNRECONCILED
	elif grand_total and reconciled_amount >= grand_total:
		status = RECONCILED
	else:
		status = PARTIALLY_RECONCILED

	frappe.db.set_value(
		"Purchase Invoice",
		purchase_invoice,
		{
			"custom_reconciled_amount": reconciled_amount,
			"custom_bank_reconciliation_status": status,
		},
		update_modified=False,
	)
