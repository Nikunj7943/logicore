import frappe
from frappe import _
from frappe.utils import format_date

from logicore.utils.email_template_utils import render_and_send_email_template
from logicore.utils.indian_format import format_inr


def _inr(value):
    # Whole-rupee display for the email — drop the ".00" that format_inr always appends.
    return format_inr(value).split(".")[0]


def send_supplier_payment_email(doc):
    """Email the supplier a payment confirmation when a Supplier Payment is submitted.
    Skips silently (with a form warning) if the Supplier has no Email ID set —
    call this after _update_invoice_payment_status() so per-invoice status is final.
    Errors are logged, not raised, so a mail failure never blocks submission.
    """
    try:
        _send(doc)
    except Exception:
        frappe.log_error(title=f"Supplier Payment email failed: {doc.name}")
        frappe.msgprint(
            _("Payment submitted, but the confirmation email could not be sent. See Error Log for details."),
            title=_("Email Not Sent"),
            indicator="orange",
        )


def _get_supplier_email(supplier):
    # Supplier.email_id is a Read-Only fetch_from field (supplier_primary_contact.email_id)
    # that only refreshes when the Supplier form itself is saved with that link field
    # changed — it silently goes stale if the Contact's email is edited any other way.
    # Read the Contact directly so this always reflects the current address.
    primary_contact = frappe.db.get_value("Supplier", supplier, "supplier_primary_contact")
    if primary_contact:
        contact_email = frappe.db.get_value("Contact", primary_contact, "email_id")
        if contact_email:
            return contact_email
    return frappe.db.get_value("Supplier", supplier, "email_id")


def _send(doc):
    supplier_email = _get_supplier_email(doc.supplier)
    if not supplier_email:
        frappe.msgprint(
            _("Supplier {0}'s Email ID is not set, so the payment confirmation email was not sent.").format(doc.supplier),
            indicator="blue",
            alert=True,
        )
        return

    supplier_name = frappe.db.get_value("Supplier", doc.supplier, "supplier_name") or doc.supplier

    context = {
        "supplier_name": frappe.utils.escape_html(supplier_name),
        "payment_no": doc.name,
        "payment_date": format_date(doc.payment_date, "dd-mm-yyyy"),
        "mode_of_payment": doc.mode_of_payment or "",
        "reference_no": doc.reference_no or "-",
        "invoices": [_invoice_row_context(row) for row in doc.invoices],
        "total_payment_amount": _inr(doc.total_payment_amount),
        "total_tds_amount": _inr(doc.total_tds_amount),
        "total_transfer_amount": _inr(doc.total_transfer_amount),
    }

    cc = []
    user = frappe.session.user
    if user and user not in ("Administrator", "Guest") and "@" in user:
        cc.append(user)

    sent = render_and_send_email_template(
        doc.doctype,
        context,
        recipients=[supplier_email],
        cc=cc or None,
        sender_doctype=doc.doctype,
        reference_doctype=doc.doctype,
        reference_name=doc.name,
    )

    if not sent:
        return

    # User requested this confirmation popup be removed from the UI — sending
    # still happens silently, just no msgprint shown.
    # frappe.msgprint(
    #     _("Payment confirmation email has been sent to {0}.").format(supplier_email),
    #     title=_("Email Sent"),
    #     indicator="green",
    # )


def _invoice_row_context(row):
    return {
        "invoice_no": row.supplier_invoice_no or row.purchase_invoice or "-",
        "invoice_date": format_date(row.invoice_date, "dd-mm-yyyy") if row.invoice_date else "-",
        "invoice_amount": _inr(row.grand_total),
        "tds_amount": _inr(row.tds_amount),
        "paid_amount": _inr(row.payment_amount),
    }
