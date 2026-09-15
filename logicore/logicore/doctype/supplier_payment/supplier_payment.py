import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from logicore.utils.supplier_payment_email import send_supplier_payment_email
from logicore.utils.supplier_payment_reconciliation import recalculate_for_supplier_payment


class SupplierPayment(Document):

    def before_insert(self):
        if self.invoices:
            # Import gave specific invoices (e.g. Supplier Invoice No + Payment
            # Amount columns) — fill in the remaining display fields for those
            # rows instead of bulk-fetching unrelated unpaid invoices on top.
            self._enrich_manual_invoice_rows()
        else:
            self._auto_fetch_invoices()

    def before_validate(self):
        if self.ignore_validations:
            self.flags.ignore_mandatory = True

    def validate(self):
        if not self.ignore_validations:
            self._validate_invoices()
        self._recalculate_totals()
        self._validate_reference_no_unique()

    def _auto_fetch_invoices(self):
        """Populate `invoices` from get_unpaid_invoices() when a new record
        (manual entry without using Fetch Invoices, Data Import, or a custom
        import template) arrives with the table empty — same filters/results
        as the Fetch Invoices button, just run server-side so any creation
        path works.
        """
        if not self.supplier or not self.from_date or not self.to_date:
            frappe.throw(_(
                "Supplier, From Date and To Date are required to auto-fetch invoices."
            ))

        invoices = get_unpaid_invoices(self.supplier, self.from_date, self.to_date, self.company)
        if not invoices:
            frappe.throw(_(
                "No unpaid invoices found for supplier {0} between {1} and {2}."
            ).format(self.supplier, self.from_date, self.to_date))

        for inv in invoices:
            self.append("invoices", {
                "purchase_invoice": inv.name,
                "supplier_invoice_no": inv.bill_no,
                "invoice_date": inv.bill_date or inv.posting_date,
                "grand_total": flt(inv.grand_total),
                "net_total": flt(inv.net_total),
                "paid_amount": flt(inv.custom_total_paid),
                "balance": flt(inv.balance),
                "payment_amount": flt(inv.balance),
            })

    def _enrich_manual_invoice_rows(self):
        """Fill in the display/amount fields for rows that only give
        `purchase_invoice` (+ payment_amount) — the path used by bulk import.
        `supplier_invoice_no` is not touched here — it is a Frappe "Fetch
        From" (purchase_invoice.bill_no, fetch_if_empty) and resolves on its
        own before before_insert() runs, same as Vendor Payment Trip's
        equivalent fields.

        Must not skip based on grand_total/etc already being set — Frappe's
        Fetch From only covers supplier_invoice_no, so checking other fields
        here would never actually run for the manual-entry path.
        """
        for row in self.invoices:
            if not row.purchase_invoice or row.balance:
                continue
            pi = frappe.db.get_value(
                "Purchase Invoice", row.purchase_invoice,
                ["grand_total", "net_total", "custom_total_paid", "custom_balance_amount",
                 "bill_date", "posting_date"],
                as_dict=True,
            )
            if not pi:
                frappe.throw(_("Row referencing Purchase Invoice {0}: Invoice not found.").format(row.purchase_invoice))
            row.grand_total = flt(pi.grand_total)
            row.net_total = flt(pi.net_total)
            row.paid_amount = flt(pi.custom_total_paid)
            row.balance = flt(pi.custom_balance_amount) or (flt(pi.grand_total) - flt(pi.custom_total_paid))
            if not row.invoice_date:
                row.invoice_date = pi.bill_date or pi.posting_date

    def _validate_reference_no_unique(self):
        if not self.reference_no:
            return
        duplicate = frappe.db.get_value(
            "Supplier Payment",
            {"reference_no": self.reference_no, "name": ("!=", self.name or "")},
            "name",
        )
        if duplicate:
            frappe.throw(_("Reference No. {0} already used in {1}.").format(self.reference_no, duplicate))

    def on_submit(self):
        if not self.ignore_validations:
            if self.mode_of_payment == "UPI" and not self.upi_id:
                frappe.throw(_("Please enter UPI ID before submitting."))
            if self.mode_of_payment in ("Bank Transfer", "Cheque") and not self.reference_no:
                frappe.throw(_("Please enter Reference No before submitting."))
        self._update_invoice_payment_status()
        # A freshly submitted payment is never reconciled yet, so this just
        # seeds the invoices' bank-reconciliation fields. On cancel it matters
        # for real: a payment that WAS reconciled has to stop counting.
        recalculate_for_supplier_payment(self.name)
        send_supplier_payment_email(self)

    def on_cancel(self):
        self._reverse_invoice_payment_status()
        recalculate_for_supplier_payment(self.name)

    def _validate_invoices(self):
        if not self.invoices:
            frappe.throw(_("Please add at least one invoice before submitting."))
        for row in self.invoices:
            label = row.supplier_invoice_no or row.purchase_invoice
            if flt(row.payment_amount) <= 0:
                frappe.throw(
                    _("Row {0}: Payment Amount must be greater than zero for invoice {1}.").format(row.idx, label)
                )
            pi_supplier = frappe.db.get_value("Purchase Invoice", row.purchase_invoice, "supplier")
            if pi_supplier != self.supplier:
                frappe.throw(
                    _("Row {0}: Invoice {1} belongs to supplier {2}, not {3}.").format(
                        row.idx, label, pi_supplier, self.supplier
                    )
                )
            pi_status = frappe.db.get_value("Purchase Invoice", row.purchase_invoice, "custom_payment_status")
            if pi_status == "Paid":
                frappe.throw(_("Row {0}: Invoice {1} is already fully paid.").format(row.idx, label))
            grand_total, already_paid = frappe.db.get_value(
                "Purchase Invoice", row.purchase_invoice, ["grand_total", "custom_total_paid"]
            ) or (0, 0)
            balance = flt(grand_total) - flt(already_paid)
            if flt(row.payment_amount) > balance:
                frappe.throw(
                    _("Payment Amount {0} exceeds outstanding balance {1} for invoice {2}.").format(
                        frappe.format_value(row.payment_amount, {"fieldtype": "Currency"}),
                        frappe.format_value(balance, {"fieldtype": "Currency"}),
                        label,
                    )
                )

    def _recalculate_totals(self):
        # TDS is a free-entry amount the user types per row (how much to
        # deduct for this payment) — never auto-computed or overwritten here.
        # Only transfer_amount and the parent totals are derived from it.
        total_payment = 0
        total_tds = 0
        total_transfer = 0

        for row in self.invoices:
            row_tds = flt(row.tds_amount)
            transfer = flt(row.payment_amount) - row_tds
            row.transfer_amount = transfer
            total_payment += flt(row.payment_amount)
            total_tds += row_tds
            total_transfer += transfer

        self.total_payment_amount = total_payment
        self.total_tds_amount = total_tds
        self.total_transfer_amount = total_transfer

    def _update_invoice_payment_status(self):
        for row in self.invoices:
            pi_doc = frappe.get_doc("Purchase Invoice", row.purchase_invoice)
            new_total_paid = flt(pi_doc.get("custom_total_paid") or 0) + flt(row.payment_amount)
            balance = flt(pi_doc.grand_total) - new_total_paid

            if balance <= 0:
                status = "Paid"
            elif new_total_paid > 0:
                status = "Partially Paid"
            else:
                status = "Unpaid"

            frappe.db.set_value("Purchase Invoice", row.purchase_invoice, {
                "custom_total_paid": new_total_paid,
                "custom_balance_amount": max(balance, 0),
                "custom_outstanding_balance": max(balance, 0),
                "custom_payment_status": status,
            }, update_modified=False)

    def _reverse_invoice_payment_status(self):
        for row in self.invoices:
            pi_doc = frappe.get_doc("Purchase Invoice", row.purchase_invoice)
            new_total_paid = max(
                flt(pi_doc.get("custom_total_paid") or 0) - flt(row.payment_amount), 0
            )
            balance = flt(pi_doc.grand_total) - new_total_paid

            if balance <= 0:
                status = "Paid"
            elif new_total_paid > 0:
                status = "Partially Paid"
            else:
                status = "Unpaid"

            frappe.db.set_value("Purchase Invoice", row.purchase_invoice, {
                "custom_total_paid": new_total_paid,
                "custom_balance_amount": max(balance, 0),
                "custom_outstanding_balance": max(balance, 0),
                "custom_payment_status": status,
            }, update_modified=False)


@frappe.whitelist()
def get_payment_history(purchase_invoice):
    """Submitted Supplier Payment rows made against this invoice — shown as a
    read-only table on the Purchase Invoice form (mirrors Trip's vendor
    payment history table)."""
    return frappe.db.sql(
        """
        SELECT
            sp.name, sp.payment_date, sp.mode_of_payment, sp.reference_no,
            spi.payment_amount, spi.tds_amount, spi.transfer_amount
        FROM `tabPayment Invoices` spi
        JOIN `tabSupplier Payment` sp ON sp.name = spi.parent
        WHERE spi.purchase_invoice = %s AND sp.docstatus = 1
        ORDER BY sp.payment_date ASC, sp.creation ASC
        """,
        purchase_invoice,
        as_dict=True,
    )


@frappe.whitelist()
def get_unpaid_invoices(supplier, from_date, to_date, company=None):
    filters = {
        "supplier": supplier,
        "posting_date": ["between", [from_date, to_date]],
        "docstatus": 1,
        "bill_no": ["is", "set"],
        "custom_payment_status": ["in", ["Unpaid", "Partially Paid"]],
    }
    if company:
        filters["company"] = company

    invoices = frappe.get_all(
        "Purchase Invoice",
        filters=filters,
        fields=[
            "name", "bill_no", "bill_date", "posting_date",
            "grand_total", "net_total",
            "custom_total_paid", "custom_balance_amount", "custom_payment_status",
        ],
        order_by="posting_date asc",
    )

    for inv in invoices:
        balance = flt(inv.get("custom_balance_amount"))
        if not balance:
            balance = flt(inv.get("grand_total")) - flt(inv.get("custom_total_paid"))
        inv["balance"] = balance

    return invoices


# Neither Frappe's own Data Import tool nor this app's generic Import Template
# engine supports "repeat the parent columns on every row, group by matching
# values" — the format the business actually wants to fill in by hand. This
# grouped importer exists specifically for that CSV shape, same as
# bulk_import_vendor_payments()/bulk_import_receipts(). Row identity is the
# Supplier Invoice No the user typed at invoice creation, not the Purchase
# Invoice's auto-generated name — that name is never exposed to the importer.
BULK_IMPORT_PARENT_COLUMNS = [
    "payment_date", "from_date", "to_date", "company", "paid_from_account",
    "mode_of_payment", "supplier", "Reference No", "UPI ID",
]
BULK_IMPORT_ROW_COLUMNS = [
    "Supplier Invoice No (Invoices)", "Payment Amount", "Ignore Validations (Import Only)",
]


@frappe.whitelist()
def bulk_import_supplier_payments(file_url):
    """Group CSV rows sharing the same parent columns into one Supplier
    Payment each, with every row becoming an `invoices` child row. Reuses the
    normal before_insert/validate pipeline (auto-fetch is skipped since
    invoices is already populated; _recalculate_totals() computes TDS/
    transfer amount from the given payment_amount as usual).
    """
    from logicore.logicore.utils.import_utils import (
        _normalize_header, _read_csv_rows, _strict_import_date, _validate_link_value,
        read_ignore_validations_flag,
    )

    paid_from_account_field = frappe.get_meta("Supplier Payment").get_field("paid_from_account")

    rows = _read_csv_rows(file_url)
    if not rows:
        frappe.throw(_("CSV file is empty."))

    header = [(h or "").strip() for h in rows[0]]
    required = BULK_IMPORT_PARENT_COLUMNS + BULK_IMPORT_ROW_COLUMNS[:2]
    normalized_header = {_normalize_header(h) for h in header}
    missing = [c for c in required if _normalize_header(c) not in normalized_header]
    if missing:
        frappe.throw(_("Missing required columns: {0}").format(", ".join(missing)))

    col_index = {_normalize_header(h): i for i, h in enumerate(header)}

    def cell(row, column):
        i = col_index.get(_normalize_header(column))
        if i is None or i >= len(row) or row[i] is None:
            return ""
        return str(row[i]).strip()

    groups = []
    group_by_key = {}
    for row in rows[1:]:
        if not row or all(not cell(row, c) for c in header):
            continue
        key = tuple(cell(row, c) for c in BULK_IMPORT_PARENT_COLUMNS)
        group = group_by_key.get(key)
        if group is None:
            group = {"key": key, "rows": []}
            group_by_key[key] = group
            groups.append(group)
        group["rows"].append(row)

    results = []
    for group in groups:
        parent = dict(zip(BULK_IMPORT_PARENT_COLUMNS, group["key"]))
        label = parent.get("Reference No") or parent.get("supplier") or "(unlabeled group)"

        invoice_rows = []
        unresolved = []
        for row in group["rows"]:
            bill_no = cell(row, "Supplier Invoice No (Invoices)")
            if not bill_no:
                continue
            pi_filters = {"supplier": parent["supplier"], "bill_no": bill_no, "docstatus": 1}
            if parent.get("company"):
                pi_filters["company"] = parent["company"]
            pi_name = frappe.db.get_value("Purchase Invoice", pi_filters, "name")
            if not pi_name:
                unresolved.append(bill_no)
                continue
            invoice_rows.append({
                "purchase_invoice": pi_name,
                "payment_amount": flt(cell(row, "Payment Amount")),
            })

        if not invoice_rows:
            message = _("No invoice rows in this group.")
            if unresolved:
                message = _(
                    "No matching submitted Purchase Invoice found for Supplier Invoice No: {0}."
                ).format(", ".join(unresolved))
            results.append({"label": label, "status": "Skipped", "message": message})
            continue

        # ignore_validations = 1 if any(
        #     _parse_import_bool(cell(row, "Ignore Validations")) for row in group["rows"]
        # ) else 0
        # ^ the downloaded template's header is "Ignore Validations (Import
        # Only)" (the field's label), so this lookup never matched.
        ignore_validations = read_ignore_validations_flag(cell, group["rows"])

        # See the matching comment in vendor_payment.py — a bare rollback here
        # discarded earlier groups and broke the Import Log's save.
        savepoint = f"tms_sp_import_{len(results)}"
        frappe.db.savepoint(savepoint)
        try:
            doc = frappe.get_doc({
                "doctype": "Supplier Payment",
                "payment_date": _strict_import_date(parent["payment_date"]) if parent["payment_date"] else None,
                "from_date": _strict_import_date(parent["from_date"]) if parent["from_date"] else None,
                "to_date": _strict_import_date(parent["to_date"]) if parent["to_date"] else None,
                "company": parent["company"] or None,
                "paid_from_account": _validate_link_value(paid_from_account_field, parent["paid_from_account"]) or None,
                "mode_of_payment": parent["mode_of_payment"] or None,
                "supplier": parent["supplier"] or None,
                "reference_no": parent["Reference No"] or None,
                "upi_id": parent["UPI ID"] or None,
                "ignore_validations": ignore_validations,
                "invoices": invoice_rows,
            })
            doc.insert(ignore_permissions=True)
            frappe.db.release_savepoint(savepoint)
            message = _("{0} invoice(s) imported.").format(len(invoice_rows))
            if unresolved:
                message += " " + _("{0} row(s) skipped — no matching invoice for: {1}.").format(
                    len(unresolved), ", ".join(unresolved)
                )
            results.append({"label": doc.name, "status": "Success", "message": message})
        except Exception as e:
            # frappe.db.rollback()
            frappe.db.rollback(save_point=savepoint)
            results.append({"label": label, "status": "Failed", "message": str(e)})

    frappe.db.commit()
    return results
