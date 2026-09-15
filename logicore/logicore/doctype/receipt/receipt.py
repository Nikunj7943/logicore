import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from logicore.utils.receipt_email import send_receipt_email


class Receipt(Document):

    def before_insert(self):
        if self.receipt_type == "Other Receipt":
            return
        if self.trips:
            # Import gave specific trips (e.g. Trip + Net Receivable Amount
            # columns) — fill in the remaining display fields for those rows
            # instead of bulk-fetching unrelated pending trips on top.
            self._enrich_manual_trip_rows()
        else:
            self._auto_fetch_trips()

    def before_validate(self):
        if self.ignore_validations:
            self.flags.ignore_mandatory = True

    def validate(self):
        if self.receipt_type == "Other Receipt":
            self.trips = []
            self.total_brokerage_amount = 0
            self.total_lr_money = 0
            self.total_tds_amount = 0
            self.total_received_amount = flt(self.total_invoice_amount)
            self.total_outstanding_amount = 0
        else:
            if not self.ignore_validations:
                self._validate_trips()
            self._recalculate_totals()
        self._validate_reference_no_unique()

    def _auto_fetch_trips(self):
        """Populate `trips` from get_unreceived_trips() when a new record
        (manual entry without using Fetch Trips, Data Import, or a custom
        import template) arrives with the table empty — same filters/results
        as the Fetch Trips button, just run server-side so any creation path
        works.
        """
        if not self.customer or not self.from_date or not self.to_date or not self.trip_type:
            frappe.throw(_(
                "Customer, From Date, To Date and Trip Type are required to auto-fetch trips."
            ))

        trips = get_unreceived_trips(
            self.customer, self.from_date, self.to_date, self.company, self.trip_type
        )
        if not trips:
            frappe.throw(_(
                "No pending trips found for customer {0} between {1} and {2}."
            ).format(self.customer, self.from_date, self.to_date))

        for t in trips:
            is_other_trip = (t.trip_type or "").strip().upper() == "OTHER"
            net_balance = flt(t.customer_balance_amount)
            self.append("trips", {
                "trip": t.name,
                "trip_date": t.tcntrip_date,
                "tcntrip_no": t.tcntrip_no,
                "lr_no": t.lr_no,
                "vehicle_no": t.vehicle_no or t.vehicle_market,
                "origin_city": t.origin_city,
                "destination_city": t.destination_city_1,
                "customer_freight": flt(t.customer_freight),
                "approved_addl_amount": flt(t.total_approved_addl_amount),
                "invoice_amount": flt(t.net_invoice_amount),
                "brokerage_amount": flt(t.brokerage_amount) if is_other_trip else 0,
                "lr_money": flt(t.lr_money) if is_other_trip else 0,
                "tds_amount": flt(t.tds_deducted_by_customer),
                "balance": net_balance,
                "received_amount": net_balance,
                "payment_advice_no": t.payment_advice_no or "",
                "utr_no": t.utr_no or "",
            })

    def _enrich_manual_trip_rows(self):
        """Fill in payment advice/UTR refs and `vehicle_no` for rows that only
        give `trip` (+ received_amount) — trip_date/tcntrip_no/lr_no/
        origin_city/destination_city all auto-populate from the `trip` link's
        Fetch From on their own; invoice_amount/balance/tds_amount/
        brokerage_amount/lr_money are recomputed for every row anyway in
        _recalculate_totals(). `vehicle_no` has no Fetch From (it must
        combine Trip's own-fleet `vehicle_no` Link with its market
        `vehicle_market` text field — a trip only ever fills one of the two)
        so it is set here explicitly. Net Receivable Amount from the row is
        never touched.

        Must not skip based on trip_date/etc already being set — Frappe's
        own Fetch From resolves those before before_insert() ever runs, so
        checking them here always looks "already enriched" and silently
        skips the fields that actually need this method.
        """
        for row in self.trips:
            if not row.trip or (row.payment_advice_no and row.utr_no and row.vehicle_no):
                continue
            trip = frappe.db.get_value(
                "Trip", row.trip,
                ["payment_advice_no", "utr_no", "vehicle_no", "vehicle_market"], as_dict=True,
            )
            if not trip:
                frappe.throw(_("Row referencing Trip {0}: Trip not found.").format(row.trip))
            row.payment_advice_no = row.payment_advice_no or trip.payment_advice_no or ""
            row.utr_no = row.utr_no or trip.utr_no or ""
            row.vehicle_no = row.vehicle_no or trip.vehicle_no or trip.vehicle_market

    def _validate_reference_no_unique(self):
        if not self.reference_no:
            return
        duplicate = frappe.db.get_value(
            "Receipt",
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
        # self._create_payment_entry()  # Payment Entry integration disabled
        self._update_trip_receipt_status()
        send_receipt_email(self)

    def on_cancel(self):
        # self._cancel_payment_entry()  # Payment Entry integration disabled
        self._reverse_trip_receipt_status()

    def _validate_trips(self):
        if not self.trips:
            frappe.throw(_("Please add at least one trip before submitting."))
        for row in self.trips:
            if flt(row.received_amount) <= 0:
                frappe.throw(
                    _("Received Amount must be greater than zero for trip {0}.").format(row.trip)
                )
            trip_customer = frappe.db.get_value("Trip", row.trip, "customer")
            if trip_customer != self.customer:
                frappe.throw(
                    _("Trip {0} belongs to customer {1}, not {2}.").format(
                        row.trip, trip_customer, self.customer
                    )
                )
            invoice_amount = flt(frappe.db.get_value("Trip", row.trip, "total_trip_amount") or 0)
            already_received = frappe.db.sql("""
                SELECT COALESCE(SUM(crt.received_amount), 0)
                FROM `tabCustomer Receipt Trip` crt
                JOIN `tabReceipt` r ON r.name = crt.parent
                WHERE crt.trip = %s AND r.docstatus = 1 AND r.name != %s
            """, (row.trip, self.name))[0][0] or 0
            balance = invoice_amount - flt(already_received)
            # if flt(row.received_amount) > balance + 0.01:
            #     frappe.throw(
            #         _("Received Amount {0} exceeds outstanding balance {1} for trip {2}.").format(
            #             frappe.format_value(row.received_amount, {"fieldtype": "Currency"}),
            #             frappe.format_value(balance, {"fieldtype": "Currency"}),
            #             row.trip,
            #         )
            #     )

    def _recalculate_totals(self):
        total_invoice = 0
        total_brokerage = 0
        total_lr_money = 0
        total_tds = 0
        total_received = 0

        for row in self.trips:
            if row.trip:
                trip_fields = frappe.db.get_value(
                    "Trip",
                    row.trip,
                    ["trip_type", "customer_freight", "total_approved_addl_amount", "total_trip_amount", "brokerage_amount", "lr_money", "tds_deducted_by_customer"],
                    as_dict=True,
                ) or {}

                cf = flt(trip_fields.get("customer_freight") or 0)
                addl = flt(trip_fields.get("total_approved_addl_amount") or 0)
                net_payable = flt(trip_fields.get("total_trip_amount") or 0)
                row.customer_freight = cf
                row.approved_addl_amount = addl

                already_received = frappe.db.sql("""
                    SELECT COALESCE(SUM(crt.received_amount), 0)
                    FROM `tabCustomer Receipt Trip` crt
                    JOIN `tabReceipt` r ON r.name = crt.parent
                    WHERE crt.trip = %s AND r.docstatus = 1 AND r.name != %s
                """, (row.trip, self.name or ""))[0][0] or 0

                is_other = (trip_fields.get("trip_type") or "").strip().upper() == "OTHER"
                # Net payable = gross - one-time trip deductions; balance = remaining after all receipts including this one
                _trip_brokerage = flt(trip_fields.get("brokerage_amount") or 0) if is_other else 0
                _trip_lr        = flt(trip_fields.get("lr_money") or 0) if is_other else 0
                _trip_tds       = flt(trip_fields.get("tds_deducted_by_customer") or 0)
                _net_payable    = net_payable - _trip_brokerage - _trip_lr - _trip_tds
                row.invoice_amount = _net_payable
                row.balance     = max(_net_payable - flt(already_received), 0)
                # TDS — deduct only once (first receipt)
                already_tds = flt(frappe.db.sql("""
                    SELECT COALESCE(SUM(crt.tds_amount), 0)
                    FROM `tabCustomer Receipt Trip` crt
                    JOIN `tabReceipt` r ON r.name = crt.parent
                    WHERE crt.trip = %s AND r.docstatus = 1 AND r.name != %s
                """, (row.trip, self.name or ""))[0][0])
                trip_tds = flt(trip_fields.get("tds_deducted_by_customer") or 0)
                row.tds_amount = max(flt(trip_tds - already_tds, 2), 0)

                if is_other:
                    # Brokerage — deduct only once (first receipt)
                    already_brokerage = flt(frappe.db.sql("""
                        SELECT COALESCE(SUM(crt.brokerage_amount), 0)
                        FROM `tabCustomer Receipt Trip` crt
                        JOIN `tabReceipt` r ON r.name = crt.parent
                        WHERE crt.trip = %s AND r.docstatus = 1 AND r.name != %s
                    """, (row.trip, self.name or ""))[0][0])
                    trip_brokerage = flt(trip_fields.get("brokerage_amount") or 0)
                    row.brokerage_amount = max(flt(trip_brokerage - already_brokerage, 2), 0)

                    # LR Money — deduct only once (first receipt)
                    already_lr = flt(frappe.db.sql("""
                        SELECT COALESCE(SUM(crt.lr_money), 0)
                        FROM `tabCustomer Receipt Trip` crt
                        JOIN `tabReceipt` r ON r.name = crt.parent
                        WHERE crt.trip = %s AND r.docstatus = 1 AND r.name != %s
                    """, (row.trip, self.name or ""))[0][0])
                    trip_lr = flt(trip_fields.get("lr_money") or 0)
                    row.lr_money = max(flt(trip_lr - already_lr, 2), 0)
                else:
                    row.brokerage_amount = 0
                    row.lr_money = 0

            row.net_received = flt(row.received_amount)
            total_invoice += flt(row.invoice_amount)
            total_brokerage += flt(row.brokerage_amount)
            total_lr_money += flt(row.lr_money)
            total_tds += flt(row.tds_amount)
            total_received += flt(row.received_amount)

        self.total_invoice_amount = total_invoice
        self.total_brokerage_amount = total_brokerage
        self.total_lr_money = total_lr_money
        self.total_tds_amount = total_tds
        self.total_received_amount = total_received
        self.total_outstanding_amount = max(total_invoice - total_received, 0)

    # Payment Entry integration disabled — managed via Account Head
    # def _create_payment_entry(self): ...
    # def _cancel_payment_entry(self): ...

    def _update_trip_receipt_status(self):
        pass  # trip status tracked via Receipt child table queries

    def _reverse_trip_receipt_status(self):
        pass  # trip status tracked via Receipt child table queries


@frappe.whitelist()
def get_unreceived_trips(customer, from_date, to_date, company=None, trip_type=None):
    filters = {
        "customer": customer,
        "tcntrip_date": ["between", [from_date, to_date]],
        "docstatus": ["in", [0, 1]],
    }
    if trip_type:
        filters["trip_type"] = trip_type

    trips = frappe.get_all(
        "Trip",
        filters=filters,
        fields=[
            "name", "tcntrip_date", "tcntrip_no", "lr_no", "vehicle_no", "vehicle_market",
            "origin_city", "destination_city_1",
            "customer", "customer_freight", "total_approved_addl_amount", "total_trip_amount",
            "trip_type", "brokerage_amount", "lr_money", "tds_deducted_by_customer",
            "payment_advice_no", "utr_no",
        ],
        order_by="tcntrip_date asc",
    )

    result = []
    for t in trips:
        already_received = frappe.db.sql("""
            SELECT COALESCE(SUM(crt.received_amount), 0)
            FROM `tabCustomer Receipt Trip` crt
            JOIN `tabReceipt` r ON r.name = crt.parent
            WHERE crt.trip = %s AND r.docstatus = 1
        """, t.name)[0][0] or 0

        net_payable = flt(t.total_trip_amount)
        t["total_customer_received"] = flt(already_received)

        is_other = (t.get("trip_type") or "").strip().upper() == "OTHER"
        # Net payable = gross - one-time trip deductions; balance = remaining after already received
        _trip_brokerage = flt(t.get("brokerage_amount") or 0) if is_other else 0
        _trip_lr        = flt(t.get("lr_money") or 0) if is_other else 0
        _trip_tds       = flt(t.get("tds_deducted_by_customer") or 0)
        _net_invoice_amount = net_payable - _trip_brokerage - _trip_lr - _trip_tds
        t["net_invoice_amount"] = _net_invoice_amount
        net_balance     = _net_invoice_amount - flt(already_received)
        t["customer_balance_amount"] = max(net_balance, 0)

        # TDS — deduct only once (first receipt)
        already_tds = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(crt.tds_amount), 0)
            FROM `tabCustomer Receipt Trip` crt
            JOIN `tabReceipt` r ON r.name = crt.parent
            WHERE crt.trip = %s AND r.docstatus = 1
        """, t.name)[0][0])
        trip_tds = flt(t.get("tds_deducted_by_customer") or 0)
        t["tds_deducted_by_customer"] = max(flt(trip_tds - already_tds, 2), 0)

        if is_other:
            # Brokerage — deduct only once (first receipt)
            already_brokerage = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(crt.brokerage_amount), 0)
                FROM `tabCustomer Receipt Trip` crt
                JOIN `tabReceipt` r ON r.name = crt.parent
                WHERE crt.trip = %s AND r.docstatus = 1
            """, t.name)[0][0])
            t["brokerage_amount"] = max(flt(flt(t.get("brokerage_amount") or 0) - already_brokerage, 2), 0)

            # LR Money — deduct only once (first receipt)
            already_lr = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(crt.lr_money), 0)
                FROM `tabCustomer Receipt Trip` crt
                JOIN `tabReceipt` r ON r.name = crt.parent
                WHERE crt.trip = %s AND r.docstatus = 1
            """, t.name)[0][0])
            t["lr_money"] = max(flt(flt(t.get("lr_money") or 0) - already_lr, 2), 0)
        else:
            t["brokerage_amount"] = 0
            t["lr_money"] = 0

        if net_balance > 0.01:
            result.append(t)

    return result


# See the matching comment in vendor_payment.py — neither Frappe's own Data
# Import tool nor this app's generic Import Template engine supports "repeat
# the parent columns on every row, group by matching values", so this grouped
# importer exists specifically for that CSV shape.
BULK_IMPORT_PARENT_COLUMNS = [
    "payment_date", "from_date", "to_date", "company", "paid_from_account",
    "mode_of_payment", "customer", "Reference No", "UPI ID", "Trip Type",
]


@frappe.whitelist()
def bulk_import_receipts(file_url):
    """Group CSV rows sharing the same parent columns into one Receipt each,
    with every row becoming a `trips` child row. Reuses the normal
    before_insert/validate pipeline (auto-fetch is skipped since trips is
    already populated; _recalculate_totals() computes invoice_amount/balance/
    TDS/brokerage/LR-money from the given received_amount as usual).
    """
    from logicore.logicore.utils.import_utils import (
        _normalize_header, _read_csv_rows, _strict_import_date, _validate_link_value,
        read_ignore_validations_flag,
    )

    paid_from_account_field = frappe.get_meta("Receipt").get_field("paid_from_account")

    rows = _read_csv_rows(file_url)
    if not rows:
        frappe.throw(_("CSV file is empty."))

    # Normalized (collapsed whitespace + casefold) so "Net Receivable Amount",
    # " net  receivable amount ", etc. all match the same column — hand-typed
    # spreadsheet headers are never byte-exact.
    header = [(h or "").strip() for h in rows[0]]
    required = BULK_IMPORT_PARENT_COLUMNS + ["Trip (Trips)", "Net Receivable Amount"]
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
        label = parent.get("Reference No") or parent.get("customer") or "(unlabeled group)"

        trip_rows = []
        for row in group["rows"]:
            trip_name = cell(row, "Trip (Trips)")
            if not trip_name:
                continue
            trip_rows.append({
                "trip": trip_name,
                "received_amount": flt(cell(row, "Net Receivable Amount")),
            })
        if not trip_rows:
            results.append({"label": label, "status": "Skipped", "message": _("No trip rows in this group.")})
            continue

        # ignore_validations = 1 if any(
        #     cell(row, "Ignore Validations") in ("1", "true", "True", "yes", "Yes") for row in group["rows"]
        # ) else 0
        # ^ two bugs: the template's header is "Ignore Validations (Import
        # Only)" (the field's label) so the lookup never matched, and the
        # exact-match tuple missed Excel's all-caps "TRUE" anyway.
        ignore_validations = read_ignore_validations_flag(cell, group["rows"])

        # See the matching comment in vendor_payment.py — a bare rollback here
        # discarded earlier groups and broke the Import Log's save.
        savepoint = f"tms_rc_import_{len(results)}"
        frappe.db.savepoint(savepoint)
        try:
            doc = frappe.get_doc({
                "doctype": "Receipt",
                "payment_date": _strict_import_date(parent["payment_date"]) if parent["payment_date"] else None,
                "from_date": _strict_import_date(parent["from_date"]) if parent["from_date"] else None,
                "to_date": _strict_import_date(parent["to_date"]) if parent["to_date"] else None,
                "company": parent["company"] or None,
                "paid_from_account": _validate_link_value(paid_from_account_field, parent["paid_from_account"]) or None,
                "mode_of_payment": parent["mode_of_payment"] or None,
                "customer": parent["customer"] or None,
                "reference_no": parent["Reference No"] or None,
                "upi_id": parent["UPI ID"] or None,
                "trip_type": parent["Trip Type"] or None,
                "ignore_validations": ignore_validations,
                "trips": trip_rows,
            })
            doc.insert(ignore_permissions=True)
            frappe.db.release_savepoint(savepoint)
            results.append({
                "label": doc.name,
                "status": "Success",
                "message": _("{0} trip(s) imported.").format(len(trip_rows)),
            })
        except Exception as e:
            # frappe.db.rollback()
            frappe.db.rollback(save_point=savepoint)
            results.append({"label": label, "status": "Failed", "message": str(e)})

    frappe.db.commit()
    return results
