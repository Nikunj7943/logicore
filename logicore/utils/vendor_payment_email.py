import frappe
from frappe import _
from frappe.utils import flt, format_date

from logicore.utils.email_template_utils import render_and_send_email_template
from logicore.utils.indian_format import format_inr

# The design used to live inline as _EMAIL_BODY below (now commented out).
# It now lives in an Email Template record (Setup > Email > Email Template)
# with reference_doctype="Vendor Payment", so it can be edited from the UI
# without a code deploy — install.py's after_migrate() creates it once if
# missing. render_and_send_email_template() looks the record up by
# reference_doctype, not by this name, so renaming it in the UI is safe;
# this constant only fixes the docname install.py uses when auto-creating it.
VENDOR_PAYMENT_EMAIL_TEMPLATE_NAME = "Vendor Payment Confirmation"


def _inr(value):
    # Whole-rupee display for the email — drop the ".00" that format_inr always appends.
    return format_inr(value).split(".")[0]


def send_vendor_payment_email(doc):
    """Email the vendor a payment confirmation when a Vendor Payment is submitted.
    Skips silently (with a form warning) if the Supplier has no Email ID set —
    call this after _update_trip_payment_status() so per-trip status is final.
    Errors are logged, not raised, so a mail failure never blocks submission.
    """
    try:
        _send(doc)
    except Exception:
        frappe.log_error(title=f"Vendor Payment email failed: {doc.name}")
        frappe.msgprint(
            _("Payment submitted, but the confirmation email could not be sent. See Error Log for details."),
            title=_("Email Not Sent"),
            indicator="orange",
        )


def _get_vendor_email(supplier):
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
    vendor_email = _get_vendor_email(doc.vendor)
    if not vendor_email:
        frappe.msgprint(
            _("Vendor {0}'s Email ID is not set, so the payment confirmation email was not sent.").format(doc.vendor),
            indicator="blue",
            alert=True,
        )
        return

    vendor_name = frappe.db.get_value("Supplier", doc.vendor, "supplier_name") or doc.vendor

    context = {
        "vendor_name": frappe.utils.escape_html(vendor_name),
        "payment_no": doc.name,
        "payment_date": format_date(doc.payment_date, "dd-mm-yyyy"),
        "mode_of_payment": doc.mode_of_payment or "",
        "reference_no": doc.reference_no or "-",
        "trips": [_trip_row_context(row) for row in doc.trips],
        "total_payment_amount": _inr(doc.total_payment_amount),
        "total_tds_amount": _inr(doc.total_tds_amount),
        "total_lr_money": _inr(doc.total_lr_money),
        "total_transfer_amount": _inr(doc.total_transfer_amount),
    }

    cc = []
    user = frappe.session.user
    if user and user not in ("Administrator", "Guest") and "@" in user:
        cc.append(user)

    sent = render_and_send_email_template(
        doc.doctype,
        context,
        recipients=[vendor_email],
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
    #     _("Payment confirmation email has been sent to {0}.").format(vendor_email),
    #     title=_("Email Sent"),
    #     indicator="green",
    # )


def _trip_row_context(row):
    lr_money = flt(row.employee_lr_money) + flt(row.company_lr_money)
    return {
        "trip_no": row.tcntrip_no or "-",
        "lr_no": row.lr_no or "-",
        "trip_date": format_date(row.trip_date, "dd-mm-yyyy") if row.trip_date else "-",
        "vehicle_no": row.vehicle_no or "-",
        "hire_amount": _inr(row.hire_amount),
        "tds_amount": _inr(row.tds_amount),
        "lr_money": _inr(lr_money),
        "paid_amount": _inr(row.payment_amount),
    }


# Superseded by the "Vendor Payment Confirmation" Email Template record (see
# VENDOR_PAYMENT_EMAIL_TEMPLATE_NAME above) — kept per the "comment out, never
# delete" rule. The Jinja version of this same design lives in
# install.py::_VENDOR_PAYMENT_EMAIL_TEMPLATE_HTML, seeded onto that record.
#
# def _trip_row_html(row, index):
#     lr_money = flt(row.employee_lr_money) + flt(row.company_lr_money)
#     bg = "#ffffff" if index % 2 == 0 else "#f8fafc"
#     return """
#         <tr style="background-color:{bg};">
#             <td style="padding:10px 12px;font-weight:600;color:#1e293b;">{trip_no}</td>
#             <td style="padding:10px 12px;color:#475569;">{lr_no}</td>
#             <td style="padding:10px 12px;color:#475569;">{trip_date}</td>
#             <td style="padding:10px 12px;color:#475569;">{vehicle_no}</td>
#             <td style="padding:10px 12px;text-align:right;color:#475569;">{hire_amount}</td>
#             <td style="padding:10px 12px;text-align:right;color:#475569;">{tds_amount}</td>
#             <td style="padding:10px 12px;text-align:right;color:#475569;">{lr_money}</td>
#             <td style="padding:10px 12px;text-align:right;font-weight:700;color:#0f172a;">{paid_amount}</td>
#         </tr>
#     """.format(
#         bg=bg,
#         trip_no=row.tcntrip_no or "-",
#         lr_no=row.lr_no or "-",
#         trip_date=format_date(row.trip_date, "dd-mm-yyyy") if row.trip_date else "-",
#         vehicle_no=row.vehicle_no or "-",
#         hire_amount=_inr(row.hire_amount),
#         tds_amount=_inr(row.tds_amount),
#         lr_money=_inr(lr_money),
#         paid_amount=_inr(row.payment_amount),
#     )
#
#
# _EMAIL_BODY = """
# <div style="background-color:#eef1f6;padding:32px 16px;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;margin:0 auto;background-color:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);">
#     <tr>
#         <td style="background:linear-gradient(135deg,#0f2942 0%,#1c3f5f 60%,#0d3b66 100%);background-color:#0f2942;padding:32px 36px;">
#             <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
#                 <tr>
#                     <td>
#                         <span style="display:inline-block;background-color:rgba(255,255,255,0.12);color:#7ee787;font-size:11px;font-weight:700;letter-spacing:1px;padding:5px 12px;border-radius:20px;text-transform:uppercase;">&#10003; Payment Confirmed</span>
#                         <div style="color:#ffffff;font-size:15px;margin-top:16px;opacity:0.85;">Amount Transferred</div>
#                         <div style="color:#ffffff;font-size:34px;font-weight:700;margin-top:4px;letter-spacing:0.3px;">{total_transfer_amount}</div>
#                     </td>
#                     <td style="text-align:right;vertical-align:top;">
#                         <div style="color:#ffffff;font-size:13px;opacity:0.75;">Payment No</div>
#                         <div style="color:#ffffff;font-size:16px;font-weight:600;margin-top:2px;">{payment_no}</div>
#                     </td>
#                 </tr>
#             </table>
#         </td>
#     </tr>
#
#     <tr>
#         <td style="padding:32px 36px 8px 36px;">
#             <p style="color:#0f172a;font-size:16px;margin:0 0 6px 0;">To <strong>{vendor_name}</strong>,</p>
#             <p style="color:#64748b;font-size:14px;line-height:1.6;margin:0;">We have processed a payment against the trip(s) listed below. Please find the complete breakdown for your records.</p>
#         </td>
#     </tr>
#
#     <tr>
#         <td style="padding:20px 36px 0 36px;">
#             <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:10px;">
#                 <tr>
#                     <td style="padding:16px 20px;width:25%;border-right:1px solid #eef1f6;">
#                         <div style="color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Payment Date</div>
#                         <div style="color:#0f172a;font-size:14px;font-weight:600;margin-top:4px;">{payment_date}</div>
#                     </td>
#                     <td style="padding:16px 20px;width:25%;border-right:1px solid #eef1f6;">
#                         <div style="color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Mode of Payment</div>
#                         <div style="color:#0f172a;font-size:14px;font-weight:600;margin-top:4px;">{mode_of_payment}</div>
#                     </td>
#                     <td style="padding:16px 20px;width:50%;">
#                         <div style="color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Reference No</div>
#                         <div style="color:#0f172a;font-size:14px;font-weight:600;margin-top:4px;">{reference_no}</div>
#                     </td>
#                 </tr>
#             </table>
#         </td>
#     </tr>
#
#     <tr>
#         <td style="padding:24px 36px 0 36px;">
#             <div style="color:#0f172a;font-size:14px;font-weight:700;margin-bottom:10px;">Trip Breakdown</div>
#             <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:12.5px;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
#                 <thead>
#                     <tr style="background-color:#0f2942;">
#                         <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Trip No</th>
#                         <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">LR No</th>
#                         <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Trip Date</th>
#                         <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Vehicle No</th>
#                         <th style="padding:10px 12px;text-align:right;color:#ffffff;font-weight:600;">Hire Amount</th>
#                         <th style="padding:10px 12px;text-align:right;color:#ffffff;font-weight:600;">TDS</th>
#                         <th style="padding:10px 12px;text-align:right;color:#ffffff;font-weight:600;">LR Money</th>
#                         <th style="padding:10px 12px;text-align:right;color:#ffffff;font-weight:600;">Paid Amount</th>
#                     </tr>
#                 </thead>
#                 <tbody>
#                     {trip_rows}
#                 </tbody>
#             </table>
#         </td>
#     </tr>
#
#     <tr>
#         <td style="padding:24px 36px 0 36px;">
#             <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;border-radius:10px;">
#                 <tr>
#                     <td style="padding:18px 22px;">
#                         <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
#                             <tr>
#                                 <td style="color:#64748b;font-size:13px;padding:3px 0;">Total Payment Amount</td>
#                                 <td style="color:#334155;font-size:13px;padding:3px 0;text-align:right;">{total_payment_amount}</td>
#                             </tr>
#                             <tr>
#                                 <td style="color:#64748b;font-size:13px;padding:3px 0;">Total TDS Deducted</td>
#                                 <td style="color:#334155;font-size:13px;padding:3px 0;text-align:right;">{total_tds_amount}</td>
#                             </tr>
#                             <tr>
#                                 <td style="color:#64748b;font-size:13px;padding:3px 0;">Total LR Money</td>
#                                 <td style="color:#334155;font-size:13px;padding:3px 0;text-align:right;">{total_lr_money}</td>
#                             </tr>
#                             <tr>
#                                 <td colspan="2" style="border-top:1px solid #e2e8f0;padding-top:10px;margin-top:8px;"></td>
#                             </tr>
#                             <tr>
#                                 <td style="color:#0f172a;font-size:15px;font-weight:700;padding-top:6px;">Total Transfer Amount</td>
#                                 <td style="color:#0d3b66;font-size:19px;font-weight:800;padding-top:6px;text-align:right;">{total_transfer_amount}</td>
#                             </tr>
#                         </table>
#                     </td>
#                 </tr>
#             </table>
#         </td>
#     </tr>
#
#     <tr>
#         <td style="padding:24px 36px 32px 36px;">
#             <p style="color:#94a3b8;font-size:12px;line-height:1.6;margin:0;border-top:1px solid #eef1f6;padding-top:16px;">
#                 This is a system-generated payment confirmation. Please contact us if you notice any discrepancy in the above details.
#             </p>
#         </td>
#     </tr>
#
#     <tr>
#         <td style="background-color:#0f2942;padding:26px 36px;text-align:center;">
#             <p style="margin:0 0 12px 0;font-size:11px;color:#93a5bd;letter-spacing:0.5px;text-transform:uppercase;">Sent automatically by</p>
#             <a href="https://www.logicore.com/products" target="_blank" style="display:inline-block;background-color:#ffffff;color:#0d3b66;font-weight:800;font-size:14px;letter-spacing:0.2px;text-decoration:none;padding:10px 22px;border-radius:999px;">LogiCore &rarr;</a>
#             <p style="margin:14px 0 0 0;font-size:11px;color:#5a7591;">Transforming Logistics with ERP &amp; Automation</p>
#         </td>
#     </tr>
# </table>
# </div>
# """
