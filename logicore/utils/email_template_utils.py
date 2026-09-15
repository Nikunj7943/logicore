import frappe

from logicore.utils.email_settings import get_sender_for_doctype


def ensure_email_template(name, subject, response_html, reference_doctype):
    """Idempotently create an Email Template record for `reference_doctype`
    if one doesn't already exist. `name` is only the docname given to the
    record on creation — the existence check is by `reference_doctype`, not
    `name`, so a user renaming the record via Setup > Email > Email Template
    is respected: a later bench migrate sees the renamed record already
    covers this reference_doctype and does not create a duplicate. Always
    use_html=1 — the design lives in response_html (a raw Jinja "Code"
    field), never the WYSIWYG "response" field, which sanitizes/reformats
    pasted markup and mangles hand-built HTML tables and inline styles.

    No-ops if a record for this reference_doctype already exists, so a
    user's later edits made through the UI (content or name) are never
    overwritten by a future bench migrate. Raises on failure — callers (an
    install.py `_ensure_*` step) keep their own try/except for
    doctype-specific logging, same as every other install.py seeding
    function.
    """
    if frappe.db.exists("Email Template", {"reference_doctype": reference_doctype}):
        return
    frappe.get_doc({
        "doctype": "Email Template",
        "name": name,
        "subject": subject,
        "use_html": 1,
        "response_html": response_html,
        "reference_doctype": reference_doctype,
        "enabled": 1,
    }).insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.logger().warning(f"Created Email Template '{name}'")


def render_and_send_email_template(
    template_doctype,
    context,
    recipients,
    *,
    cc=None,
    sender_doctype=None,
    reference_doctype=None,
    reference_name=None,
):
    """Look up the enabled Email Template whose "Doctype" field
    (reference_doctype) is `template_doctype`, render its subject/message
    against `context` via Frappe's own Email Template.get_formatted_email()
    (core method — the same one frappe.email.doctype.email_template's
    whitelisted get_email_template() uses), and send it.

    Looked up by reference_doctype, not a fixed record name — renaming the
    template in the UI never breaks the send. If more than one enabled
    template exists for `template_doctype`, the first one created (oldest)
    is used; there is no further disambiguation, so keep exactly one
    enabled template per reference_doctype for any doctype using this
    automatic-send path.

    Sends with now=True — synchronously, in-request — instead of Frappe's
    default of queueing into Email Queue for the next scheduler flush
    (which can lag several minutes on a live site). This is a submit-time
    confirmation email, not a bulk send, so the extra second or two on the
    submit request is worth not leaving the user wondering if it went out.

    Raises on any failure (render error, send error) — does NOT call
    frappe.msgprint() or swallow exceptions itself, except for the
    "no template found" / "disabled" cases below, which are user-facing
    setup issues, not send failures. The right user-facing message for a
    send failure ("vendor has no email", "customer email missing", etc.)
    is doctype-specific and belongs in the caller's own try/except, exactly
    like send_vendor_payment_email()'s wrapper does.
    """
    template_name = frappe.db.get_value(
        "Email Template",
        {"reference_doctype": template_doctype, "enabled": 1},
        "name",
        order_by="creation asc",
    )
    if not template_name:
        frappe.msgprint(
            f"Email was not sent because no enabled Email Template is set up for '{template_doctype}'.",
            title="Email Template Missing",
            indicator="orange",
            alert=True,
        )
        return False

    tpl = frappe.get_doc("Email Template", template_name)
    formatted = tpl.get_formatted_email(context)

    # Frappe's EmailAccount.find_outgoing() is wrapped in @cache_email_account
    # (frappe/email/doctype/email_account/email_account.py), which caches
    # resolved accounts on frappe.local per request — but its cache-lookup
    # always checks a "default" fallback key too. If ANYTHING earlier in this
    # same request already fell through to the default outgoing account (e.g.
    # a Notification/Energy Point email with no doctype-specific mapping),
    # that "default" entry poisons every later lookup in the same request —
    # our own match_by_email/match_by_doctype resolution never even runs,
    # silently returning the wrong (default) account instead. Clearing this
    # cache immediately before sending guarantees our call always does a
    # fresh, correct resolution regardless of what ran earlier in the request.
    if hasattr(frappe.local, "outgoing_email_account"):
        del frappe.local.outgoing_email_account

    frappe.sendmail(
        recipients=recipients,
        cc=cc,
        sender=get_sender_for_doctype(sender_doctype),
        subject=formatted["subject"],
        message=formatted["message"],
        now=True,
        reference_doctype=reference_doctype,
        reference_name=reference_name,
    )
    return True
