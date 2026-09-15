import frappe
from frappe.utils import flt

DOCSTATUS_LABEL = {0: "Draft", 1: "Submitted", 2: "Cancelled"}

# Core `status` values that are not payment-derived (Paid/Partly Paid/Unpaid) and
# not docstatus-derived (Draft/Submitted/Cancelled) — these still belong on the
# payment/business-state column so nothing is lost from consolidating "Status"
# away, without reimplementing ERPNext's own set_status() date/return logic.
_STATUS_PASSTHROUGH = {"Return", "Debit Note Issued", "Overdue", "Internal Transfer"}


def set_default_warehouse(doc, method=None):
	if not doc.is_new() or doc.set_warehouse:
		return

	doc.set_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")


def set_title_to_name(doc, method=None):
	"""Show the invoice's own number (PINV-26-00001) in the breadcrumb/title
	instead of ERPNext's default (Supplier Name) — the `title` field is real
	and safe to point `title_field` at, unlike the virtual "name" fieldname
	which crashes Frappe's meta lookups when used directly as title_field.
	"""
	doc.title = doc.name


def sync_payment_fields(doc, method=None):
	"""Keep the TMS payment fields showing what is actually owed at every
	save — draft or submitted — not just after the first Supplier Payment
	touches this invoice. `custom_total_paid` is only ever changed by
	Supplier Payment (via frappe.db.set_value, since Purchase Invoice is
	submitted by then), so re-deriving balance/status from it here on every
	validate is safe: it never contradicts what Supplier Payment last wrote.

	validate() runs before the document row is written, so plain attribute
	assignment (unlike frappe.db.set_value, needed in on_submit-style hooks)
	persists normally.

	Core ERPNext's own set_status() already ran earlier in this same validate()
	call and may have set `status` to "Return"/"Debit Note Issued"/"Overdue"/
	"Internal Transfer" — those are business states, not docstatus, so they
	belong on this column too rather than being lost when the native "Status"
	field is hidden from the UI. Everything else keeps the plain balance-based
	Paid/Partially Paid/Unpaid calculation.
	"""
	total_paid = flt(doc.custom_total_paid)
	balance = flt(doc.grand_total) - total_paid

	if doc.status in _STATUS_PASSTHROUGH:
		status = doc.status
	elif balance <= 0 and doc.grand_total:
		status = "Paid"
	elif total_paid > 0:
		status = "Partially Paid"
	else:
		status = "Unpaid"

	doc.custom_payment_status = status
	doc.custom_balance_amount = max(balance, 0)
	doc.custom_outstanding_balance = max(balance, 0)


def sync_document_status(doc, method=None):
	"""Keep `custom_document_status` (Draft/Submitted/Cancelled) showing the
	document's actual docstatus as its own plain-text column — separate from
	`custom_payment_status`, which tracks money owed, not submission state.

	validate() runs before the row is written and sees docstatus already
	updated to 1 during submit, so plain assignment is enough here; cancel
	does not go through validate() so it is handled separately below.
	"""
	doc.custom_document_status = DOCSTATUS_LABEL.get(doc.docstatus, "Draft")


def set_document_status_on_cancel(doc, method=None):
	"""on_cancel runs after docstatus is already 2 with no further save() call,
	so the field must be written directly rather than via attribute assignment.
	"""
	frappe.db.set_value("Purchase Invoice", doc.name, "custom_document_status", "Cancelled")
