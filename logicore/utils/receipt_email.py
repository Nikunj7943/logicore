import frappe
from frappe import _
from frappe.utils import format_date

from logicore.utils.email_template_utils import render_and_send_email_template
from logicore.utils.indian_format import format_inr


def _inr(value):
    # Whole-rupee display for the email — drop the ".00" that format_inr always appends.
    return format_inr(value).split(".")[0]


def send_receipt_email(doc):
    """Email the customer a payment-received confirmation when a Receipt is
    submitted. Skips silently (with a form warning) if the Customer has no
    Email ID set. Errors are logged, not raised, so a mail failure never
    blocks submission.
    """
    try:
        _send(doc)
    except Exception:
        frappe.log_error(title=f"Receipt email failed: {doc.name}")
        frappe.msgprint(
            _("Receipt submitted, but the confirmation email could not be sent. See Error Log for details."),
            title=_("Email Not Sent"),
            indicator="orange",
        )


def _get_customer_email(customer):
    # Customer.email_id is a Read-Only fetch_from field (customer_primary_contact.email_id)
    # that only refreshes when the Customer form itself is saved with that link field
    # changed — it silently goes stale if the Contact's email is edited any other way.
    # Read the Contact directly so this always reflects the current address.
    primary_contact = frappe.db.get_value("Customer", customer, "customer_primary_contact")
    if primary_contact:
        contact_email = frappe.db.get_value("Contact", primary_contact, "email_id")
        if contact_email:
            return contact_email
    return frappe.db.get_value("Customer", customer, "email_id")


def _send(doc):
    customer_email = _get_customer_email(doc.customer)
    if not customer_email:
        frappe.msgprint(
            _("Customer {0}'s Email ID is not set, so the payment confirmation email was not sent.").format(doc.customer),
            indicator="blue",
            alert=True,
        )
        return

    customer_name = frappe.db.get_value("Customer", doc.customer, "customer_name") or doc.customer

    context = {
        "customer_name": frappe.utils.escape_html(customer_name),
        "payment_no": doc.name,
        "payment_date": format_date(doc.payment_date, "dd-mm-yyyy"),
        "mode_of_payment": doc.mode_of_payment or "",
        "reference_no": doc.reference_no or "-",
        "trips": [_trip_row_context(row) for row in doc.trips],
        "total_invoice_amount": _inr(doc.total_invoice_amount),
        "total_brokerage_amount": _inr(doc.total_brokerage_amount),
        "total_lr_money": _inr(doc.total_lr_money),
        "total_tds_amount": _inr(doc.total_tds_amount),
        "total_received_amount": _inr(doc.total_received_amount),
        "total_outstanding_amount": _inr(doc.total_outstanding_amount),
    }

    cc = []
    user = frappe.session.user
    if user and user not in ("Administrator", "Guest") and "@" in user:
        cc.append(user)

    sent = render_and_send_email_template(
        doc.doctype,
        context,
        recipients=[customer_email],
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
    #     _("Payment confirmation email has been sent to {0}.").format(customer_email),
    #     title=_("Email Sent"),
    #     indicator="green",
    # )


def _trip_row_context(row):
    return {
        "trip_no": row.tcntrip_no or "-",
        "lr_no": row.lr_no or "-",
        "trip_date": format_date(row.trip_date, "dd-mm-yyyy") if row.trip_date else "-",
        "vehicle_no": row.vehicle_no or "-",
        "invoice_amount": _inr(row.invoice_amount),
        "tds_amount": _inr(row.tds_amount),
        "lr_money": _inr(row.lr_money),
        "received_amount": _inr(row.received_amount),
    }
