import frappe

# NOTE: The canonical list now lives in `install.py` as RECONCILIATION_SOURCES and
# is applied automatically by `_sync_reconciliation_sources()` on every migrate
# (local, other developers' clones, and Frappe Cloud alike). The SOURCES list
# below is kept for reference only — `run()` delegates to install.py so both
# paths can never drift apart. Edit install.py, not this file.
SOURCES = [
	{
		"label": "Vendor Payment",
		"target_doctype": "Vendor Payment",
		"direction": "Debit",
		"date_fieldname": "payment_date",
		"amount_fieldname": "total_transfer_amount",
		"account_fieldname": "paid_from_account",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		# Matched on the post-TDS transfer, since that is the figure the bank
		# statement carries. What rolls up onto the Purchase Invoice is the
		# pre-TDS payment_amount — see utils/supplier_payment_reconciliation.py.
		"label": "Supplier Payment",
		"target_doctype": "Supplier Payment",
		"direction": "Debit",
		"date_fieldname": "payment_date",
		"amount_fieldname": "total_transfer_amount",
		"account_fieldname": "paid_from_account",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Receipt",
		"target_doctype": "Receipt",
		"direction": "Credit",
		"date_fieldname": "payment_date",
		"amount_fieldname": "total_received_amount",
		"account_fieldname": "paid_from_account",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Payment",
		"target_doctype": "Payment",
		"direction": "Debit",
		"date_fieldname": "date",
		"amount_fieldname": "amount",
		"account_fieldname": "paid_from_account",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Fuel Urea Expenses - Supplier",
		"target_doctype": "Fuel Urea Expenses",
		"direction": "Debit",
		"date_fieldname": "payment_date",
		"amount_fieldname": "fuelurea_amount",
		"account_fieldname": "bank_name",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Fuel Urea Expenses - Driver Incentive",
		"target_doctype": "Fuel Urea Expenses",
		"direction": "Debit",
		"date_fieldname": "payment_date",
		"amount_fieldname": "expense_amount",
		"account_fieldname": "driver_bank_name",
		"reconciled_fieldname": "is_reconciled_driver",
		"reconciliation_link_fieldname": "bank_reconciliation_driver",
	},
	{
		"label": "Repair Expenses",
		"target_doctype": "Repair Expenses",
		"direction": "Debit",
		"requires_submitted": 0,
		"date_fieldname": "payment_date",
		"amount_fieldname": "amount",
		"account_fieldname": "bank_name",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Tyre Expenses",
		"target_doctype": "Tyre Expenses",
		"direction": "Debit",
		"requires_submitted": 0,
		"date_fieldname": "purchase_date",
		"amount_fieldname": "total_cost",
		"account_fieldname": "bank_name",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Battery Expenses",
		"target_doctype": "Battery Expenses",
		"direction": "Debit",
		"requires_submitted": 0,
		"date_fieldname": "purchase_date",
		"amount_fieldname": "cost",
		"account_fieldname": "bank_name",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Compliances",
		"target_doctype": "Compliances",
		"direction": "Debit",
		"requires_submitted": 0,
		"date_fieldname": "issue_date",
		"amount_fieldname": "amount",
		"account_fieldname": "bank_name",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Service Logs",
		"target_doctype": "Service Logs",
		"direction": "Debit",
		"requires_submitted": 0,
		"date_fieldname": "voucher_date",
		"amount_fieldname": "total_amount",
		"account_fieldname": "bank_name",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
	{
		"label": "Staff Payroll",
		"target_doctype": "Staff Payroll",
		"direction": "Debit",
		"date_fieldname": "payment_date",
		"amount_fieldname": "net_salary",
		"account_fieldname": "bank_account",
		"reconciled_fieldname": "is_reconciled",
		"reconciliation_link_fieldname": "bank_reconciliation",
	},
]


def run():
	from logicore.install import RECONCILIATION_SOURCES, _sync_reconciliation_sources

	_sync_reconciliation_sources()
	print(f"Synced {len(RECONCILIATION_SOURCES)} TMS Reconciliation Source rows from install.py.")

# Superseded by the delegation above — kept per the "comment out, never delete" rule.
# def run():
# 	created = 0
# 	for source in SOURCES:
# 		if frappe.db.exists("TMS Reconciliation Source", source["label"]):
# 			continue
# 		frappe.get_doc({"doctype": "TMS Reconciliation Source", **source}).insert(ignore_permissions=True)
# 		created += 1
# 	frappe.db.commit()
# 	print(f"Created {created} new TMS Reconciliation Source rows ({len(SOURCES) - created} already existed).")
