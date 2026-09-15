import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from logicore.utils.tds_utils import get_supplier_tds_pct
from logicore.utils.vendor_payment_email import send_vendor_payment_email


class VendorPayment(Document):

    def before_insert(self):
        if self.trips:
            # Import gave specific trips (e.g. Trip + Payment/Advance Amount
            # columns) — fill in the remaining display fields for those rows
            # instead of bulk-fetching unrelated unpaid trips on top.
            self._enrich_manual_trip_rows()
        else:
            self._auto_fetch_trips()

    def before_validate(self):
        if self.ignore_validations:
            self.flags.ignore_mandatory = True

    def validate(self):
        self._remove_zero_amount_trip_rows()
        if not self.ignore_validations:
            self._validate_trips()
        self._recalculate_totals()
        self._validate_reference_no_unique()

    def _remove_zero_amount_trip_rows(self):
        # User can clear payment_amount to drop a trip from the payment
        # instead of deleting the row manually — treat 0/blank as removal.
        self.set("trips", [row for row in self.trips if flt(row.payment_amount) > 0])
        for i, row in enumerate(self.trips, 1):
            row.idx = i

    def _auto_fetch_trips(self):
        """Populate `trips` from get_unpaid_trips() when a new record (manual
        entry without using Fetch Trips, Data Import, or a custom import
        template) arrives with the table empty — same filters/results as the
        Fetch Trips button, just run server-side so any creation path works.
        """
        if not self.vendor or not self.from_date or not self.to_date:
            frappe.throw(_(
                "Vendor, From Date and To Date are required to auto-fetch trips."
            ))

        trips = get_unpaid_trips(self.vendor, self.from_date, self.to_date, self.company)
        if not trips:
            frappe.throw(_(
                "No unpaid trips found for vendor {0} between {1} and {2}."
            ).format(self.vendor, self.from_date, self.to_date))

        for t in trips:
            balance = flt(t.vendor_balance_amount) or flt(t.amount_to_be_paid_to_vendor) or 0
            self.append("trips", {
                "trip": t.name,
                "trip_date": t.tcntrip_date,
                "tcntrip_no": t.tcntrip_no,
                "lr_no": t.lr_no,
                "vehicle_no": t.vehicle_no or t.vehicle_market,
                "hire_amount": flt(t.total_vendor_freight),
                "tds_amount": flt(t.vendor_tds_to_be_deducted),
                "employee_lr_money": flt(t.employee_lr_money),
                "employee_lr_locked": t.get("employee_lr_locked") or 0,
                "company_lr_money": flt(t.company_lr_money),
                "company_lr_locked": t.get("company_lr_locked") or 0,
                "balance": balance,
                "payment_amount": balance,
            })

    def _enrich_manual_trip_rows(self):
        """Fill in `balance` and `vehicle_no` for rows that only give `trip`
        (+ payment_amount) — trip_date/tcntrip_no/lr_no/hire_amount and the
        LR money fields are filled from Trip only when the row does not
        already carry a value. `vehicle_no` has no Fetch From (it must combine
        Trip's own-fleet `vehicle_no` Link with its market `vehicle_market`
        text field — a trip only ever fills one of the two) so it is set here
        explicitly, same as `balance`.

        Must not skip based on trip_date/etc already being set — Frappe's
        own Fetch From resolves those before before_insert() ever runs, so
        checking them here always looks "already enriched" and silently
        skips the fields that actually need this method.
        """
        for row in self.trips:
            if not row.trip or (row.balance and row.vehicle_no):
                continue
            trip = frappe.db.get_value(
                "Trip", row.trip,
                ["vendor_balance_amount", "amount_to_be_paid_to_vendor", "vehicle_no", "vehicle_market",
                 "employee_lr_money", "company_lr_money"],
                as_dict=True,
            )
            if not trip:
                frappe.throw(_("Row referencing Trip {0}: Trip not found.").format(row.trip))
            if not row.balance:
                row.balance = flt(trip.vendor_balance_amount) or flt(trip.amount_to_be_paid_to_vendor) or 0
            if not row.vehicle_no:
                row.vehicle_no = trip.vehicle_no or trip.vehicle_market
            if row.employee_lr_money in (None, ""):
                if _get_already_deducted_lr_money(row.trip, "employee_lr_money") > 0:
                    row.employee_lr_money = 0
                    row.employee_lr_locked = 1
                else:
                    row.employee_lr_money = flt(trip.employee_lr_money) if trip.employee_lr_money is not None else 0
            if row.company_lr_money in (None, ""):
                if _get_already_deducted_lr_money(row.trip, "company_lr_money") > 0:
                    row.company_lr_money = 0
                    row.company_lr_locked = 1
                else:
                    row.company_lr_money = flt(trip.company_lr_money) if trip.company_lr_money is not None else 0

    def _validate_reference_no_unique(self):
        if not self.reference_no:
            return
        duplicate = frappe.db.get_value(
            "Vendor Payment",
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
        # self._sync_trip_lr_money_from_rows()  # Disabled: Trip.employee_lr_money/
        # company_lr_money is the user's originally entered amount and must not be
        # overwritten by what got deducted here — "already deducted" is now derived
        # from SUM(Vendor Payment Trip) in _get_already_deducted_lr_money() instead.
        self._update_trip_payment_status()
        send_vendor_payment_email(self)

    def on_cancel(self):
        # self._cancel_payment_entry()  # Payment Entry integration disabled
        # self._restore_trip_lr_money_from_rows()  # Disabled alongside
        # _sync_trip_lr_money_from_rows() above — nothing on Trip needs restoring
        # since nothing is overwritten there anymore.
        self._reverse_trip_payment_status()

    def _validate_trips(self):
        if not self.trips:
            frappe.throw(_("Please add at least one trip before submitting."))
        for row in self.trips:
            if flt(row.payment_amount) <= 0:
                frappe.throw(
                    _("Row {0}: Payment Amount must be greater than zero for trip {1}.").format(
                        row.idx, row.trip
                    )
                )
            trip_vendor = frappe.db.get_value("Trip", row.trip, "vendor")
            if trip_vendor != self.vendor:
                frappe.throw(
                    _("Row {0}: Trip {1} belongs to vendor {2}, not {3}.").format(
                        row.idx, row.trip, trip_vendor, self.vendor
                    )
                )
            trip_status = frappe.db.get_value("Trip", row.trip, "vendor_payment_status")
            if trip_status == "Paid":
                frappe.throw(
                    _("Row {0}: Trip {1} is already fully paid.").format(row.idx, row.trip)
                )
            total_freight, already_paid = frappe.db.get_value(
                "Trip", row.trip, ["total_vendor_freight", "total_vendor_paid"]
            ) or (0, 0)
            balance = flt(total_freight) - flt(already_paid)
            if flt(row.payment_amount) > balance:
                frappe.throw(
                    _("Payment Amount {0} exceeds outstanding balance {1} for trip {2}.").format(
                        frappe.format_value(row.payment_amount, {"fieldtype": "Currency"}),
                        frappe.format_value(balance, {"fieldtype": "Currency"}),
                        row.trip,
                    )
                )

    def _recalculate_totals(self):
        tds_pct = _get_vendor_tds_pct(self.vendor) if self.vendor else 0
        total_payment = 0
        total_lr = 0
        total_tds = 0
        total_transfer = 0

        for row in self.trips:
            row_tds = flt(row.tds_amount)
            if tds_pct and row.trip:
                # TDS base must match Trip's own calc (trip.py _calc_vendor_payment_total):
                # base vendor_freight only, not total_vendor_freight (which adds vendor_freight_extra).
                trip_freight = flt(frappe.db.get_value("Trip", row.trip, "vendor_freight") or 0)
                calculated_tds = flt(trip_freight * tds_pct / 100, 2)
                already_deducted = flt(frappe.db.sql("""
                    SELECT COALESCE(SUM(vpt.tds_amount), 0)
                    FROM `tabVendor Payment Trip` vpt
                    JOIN `tabVendor Payment` vp ON vp.name = vpt.parent
                    WHERE vpt.trip = %s AND vp.docstatus = 1 AND vp.name != %s
                """, (row.trip, self.name or ""))[0][0])
                row_tds = max(flt(calculated_tds - already_deducted, 2), 0)
                row.tds_amount = row_tds

            if row.trip:
                already_emp_lr = _get_already_deducted_lr_money(
                    row.trip, "employee_lr_money", exclude_payment=self.name
                )
                row.employee_lr_locked = 1 if already_emp_lr > 0 else 0
                if already_emp_lr > 0:
                    row.employee_lr_money = 0

                already_co_lr = _get_already_deducted_lr_money(
                    row.trip, "company_lr_money", exclude_payment=self.name
                )
                row.company_lr_locked = 1 if already_co_lr > 0 else 0
                if already_co_lr > 0:
                    row.company_lr_money = 0

            total_row_lr = flt(row.employee_lr_money) + flt(row.company_lr_money)
            transfer = flt(row.payment_amount) - row_tds - total_row_lr
            row.transfer_amount = transfer
            total_payment += flt(row.payment_amount)
            total_lr += total_row_lr
            total_tds += row_tds
            total_transfer += transfer

        self.total_payment_amount = total_payment
        self.total_lr_money = total_lr
        self.total_tds_amount = total_tds
        self.total_transfer_amount = total_transfer

    # Disabled — see the comment above the call sites in on_submit()/on_cancel().
    # Trip.employee_lr_money/company_lr_money are the user's originally entered
    # amounts and must stay untouched; "already deducted" now comes from
    # _get_already_deducted_lr_money() (SUM over submitted Vendor Payment Trip).
    # def _sync_trip_lr_money_from_rows(self):
    #     for row in self.trips:
    #         if not row.trip:
    #             continue
    #         current_trip_lr = frappe.db.get_value(
    #             "Trip",
    #             row.trip,
    #             ["employee_lr_money", "company_lr_money"],
    #             as_dict=True,
    #         ) or {}
    #         if row.name:
    #             frappe.db.set_value("Vendor Payment Trip", row.name, {
    #                 "prev_employee_lr_money": flt(current_trip_lr.get("employee_lr_money") or 0),
    #                 "prev_company_lr_money": flt(current_trip_lr.get("company_lr_money") or 0),
    #             }, update_modified=False)
    #             row.prev_employee_lr_money = flt(current_trip_lr.get("employee_lr_money") or 0)
    #             row.prev_company_lr_money = flt(current_trip_lr.get("company_lr_money") or 0)
    #         frappe.db.set_value("Trip", row.trip, {
    #             "employee_lr_money": flt(row.employee_lr_money),
    #             "company_lr_money": flt(row.company_lr_money),
    #         }, update_modified=False)

    # def _restore_trip_lr_money_from_rows(self):
    #     for row in self.trips:
    #         if not row.trip:
    #             continue
    #         prev_employee_lr_money = row.get("prev_employee_lr_money")
    #         prev_company_lr_money = row.get("prev_company_lr_money")
    #         if prev_employee_lr_money in (None, "") and prev_company_lr_money in (None, ""):
    #             prev_lr = frappe.db.sql("""
    #                 SELECT
    #                     vpt.employee_lr_money,
    #                     vpt.company_lr_money
    #                 FROM `tabVendor Payment Trip` vpt
    #                 JOIN `tabVendor Payment` vp ON vp.name = vpt.parent
    #                 WHERE vpt.trip = %s
    #                   AND vp.docstatus = 1
    #                   AND vp.name != %s
    #                 ORDER BY vp.modified DESC, vp.creation DESC, vpt.idx DESC
    #                 LIMIT 1
    #             """, (row.trip, self.name or ""), as_dict=True)
    #             if prev_lr:
    #                 prev_employee_lr_money = prev_lr[0].get("employee_lr_money")
    #                 prev_company_lr_money = prev_lr[0].get("company_lr_money")
    #             else:
    #                 continue
    #         frappe.db.set_value("Trip", row.trip, {
    #             "employee_lr_money": flt(prev_employee_lr_money) if prev_employee_lr_money not in (None, "") else 0,
    #             "company_lr_money": flt(prev_company_lr_money) if prev_company_lr_money not in (None, "") else 0,
    #         }, update_modified=False)

    # Payment Entry integration disabled — managed via Account Head
    # def _create_payment_entry(self):
    #     from erpnext.accounts.party import get_party_account
    #     supplier_account = get_party_account("Supplier", self.vendor, self.company)
    #     ...
    #     pe.insert(ignore_permissions=False)
    #     pe.submit()
    #     self.db_set("payment_entry", pe.name)

    def _update_trip_payment_status(self):
        for row in self.trips:
            trip_doc = frappe.get_doc("Trip", row.trip)
            new_total_paid = flt(trip_doc.get("total_vendor_paid") or 0) + flt(row.payment_amount)
            balance = flt(trip_doc.amount_to_be_paid_to_vendor) - new_total_paid

            if balance <= 0:
                status = "Paid"
            elif new_total_paid > 0:
                status = "Partially Paid"
            else:
                status = "Unpaid"

            frappe.db.set_value("Trip", row.trip, {
                "total_vendor_paid": new_total_paid,
                "vendor_balance_amount": max(balance, 0),
                "vendor_payment_status": status,
            }, update_modified=False)

    # Payment Entry integration disabled
    # def _cancel_payment_entry(self):
    #     if self.payment_entry:
    #         pe = frappe.get_doc("Payment Entry", self.payment_entry)
    #         pe.cancel()
    #         self.db_set("payment_entry", None)

    def _reverse_trip_payment_status(self):
        for row in self.trips:
            trip_doc = frappe.get_doc("Trip", row.trip)
            new_total_paid = max(
                flt(trip_doc.get("total_vendor_paid") or 0) - flt(row.payment_amount), 0
            )
            balance = flt(trip_doc.amount_to_be_paid_to_vendor) - new_total_paid

            if balance <= 0:
                status = "Paid"
            elif new_total_paid > 0:
                status = "Partially Paid"
            else:
                status = "Unpaid"

            frappe.db.set_value("Trip", row.trip, {
                "total_vendor_paid": new_total_paid,
                "vendor_balance_amount": max(balance, 0),
                "vendor_payment_status": status,
            }, update_modified=False)


LR_MONEY_FIELDS = ("employee_lr_money", "company_lr_money")


def _get_already_deducted_lr_money(trip, field, exclude_payment=None):
    """Sum of `field` (employee_lr_money or company_lr_money) already deducted
    for this trip across submitted Vendor Payments — the same "deduct once"
    guard TDS already uses (see the inline SUM query in _recalculate_totals
    and get_unpaid_trips)."""
    if field not in LR_MONEY_FIELDS:
        frappe.throw(_("Invalid LR money field: {0}").format(field))
    condition = ""
    values = {"trip": trip}
    if exclude_payment:
        condition = "AND vp.name != %(exclude)s"
        values["exclude"] = exclude_payment
    result = frappe.db.sql(f"""
        SELECT COALESCE(SUM(vpt.{field}), 0)
        FROM `tabVendor Payment Trip` vpt
        JOIN `tabVendor Payment` vp ON vp.name = vpt.parent
        WHERE vpt.trip = %(trip)s AND vp.docstatus = 1 {condition}
    """, values)[0][0]
    return flt(result)


def _get_vendor_tds_pct(vendor):
    # Moved to utils/tds_utils.py so Supplier Payment can share the same parsing.
    # Kept as a delegating alias — existing callers here are unchanged.
    # import re
    # try:
    #     val = frappe.db.get_value("Supplier", vendor, "custom_tds_applicable") or ""
    #     m = re.search(r"(\d+(?:\.\d+)?)", val)
    #     return flt(m.group(1)) if m else 0
    # except Exception:
    #     return 0
    return get_supplier_tds_pct(vendor)


@frappe.whitelist()
def get_unpaid_trips(vendor, from_date, to_date, company=None):
    filters = {
        "vendor": vendor,
        "tcntrip_date": ["between", [from_date, to_date]],
        "docstatus": ["in", [0, 1]],
        "vendor_payment_status": ["in", ["Unpaid", "Partially Paid"]],
        "amount_to_be_paid_to_vendor": [">", 0],
    }

    trips = frappe.get_all(
        "Trip",
        filters=filters,
        fields=[
            "name", "tcntrip_date", "tcntrip_no", "lr_no", "vehicle_no", "vehicle_market",
            "origin_city", "destination_city_1",
            "customer", "customer_freight",
            "vendor_freight", "total_vendor_freight", "vendor_tds_to_be_deducted",
            "amount_to_be_paid_to_vendor", "total_vendor_paid",
            "vendor_balance_amount", "employee_lr_money", "company_lr_money", "vendor_payment_status",
            "trip_type", "branch",
        ],
        order_by="tcntrip_date asc",
    )

    tds_pct = _get_vendor_tds_pct(vendor)
    for t in trips:
        if tds_pct:
            # Same base as Trip._calc_vendor_payment_total(): vendor_freight only.
            total_tds = flt(flt(t.get("vendor_freight") or 0) * tds_pct / 100, 2)
            already_tds = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(vpt.tds_amount), 0)
                FROM `tabVendor Payment Trip` vpt
                JOIN `tabVendor Payment` vp ON vp.name = vpt.parent
                WHERE vpt.trip = %s AND vp.docstatus = 1
            """, t.name)[0][0])
            t["vendor_tds_to_be_deducted"] = max(flt(total_tds - already_tds, 2), 0)
        else:
            t["vendor_tds_to_be_deducted"] = 0

        # Employee/Company LR Money is a flat one-time amount per trip, not a
        # rate — once any submitted Vendor Payment has deducted it, it must
        # never be fetched (or deducted) again for this trip.
        already_emp_lr = _get_already_deducted_lr_money(t.name, "employee_lr_money")
        t["employee_lr_locked"] = 1 if already_emp_lr > 0 else 0
        if already_emp_lr > 0:
            t["employee_lr_money"] = 0

        already_co_lr = _get_already_deducted_lr_money(t.name, "company_lr_money")
        t["company_lr_locked"] = 1 if already_co_lr > 0 else 0
        if already_co_lr > 0:
            t["company_lr_money"] = 0

    return trips


# Neither Frappe's own Data Import tool (groups extra rows into one parent only
# when their parent-level columns are left blank) nor this app's generic
# Import Template engine (flat one-row-per-document, no child table grouping)
# supports "repeat the parent columns on every row, group by matching values"
# — the format the business actually wants to fill in by hand. This grouped
# importer exists specifically for that CSV shape.
BULK_IMPORT_PARENT_COLUMNS = [
    "payment_date", "from_date", "to_date", "company", "paid_from_account",
    "mode_of_payment", "vendor", "Reference No", "UPI ID",
]
BULK_IMPORT_ROW_COLUMNS = ["Trip (Trips)", "Payment Amount", "Ignore Validations (Import Only)"]


@frappe.whitelist()
def bulk_import_vendor_payments(file_url):
    """Group CSV rows sharing the same parent columns into one Vendor Payment
    each, with every row becoming a `trips` child row. Reuses the normal
    before_insert/validate pipeline (auto-fetch is skipped since trips is
    already populated; _recalculate_totals() computes TDS/LR-money/transfer
    amount from the given payment_amount as usual).
    """
    from logicore.logicore.utils.import_utils import (
        _normalize_header, _read_csv_rows, _strict_import_date, _validate_link_value,
        read_ignore_validations_flag,
    )

    paid_from_account_field = frappe.get_meta("Vendor Payment").get_field("paid_from_account")

    rows = _read_csv_rows(file_url)
    if not rows:
        frappe.throw(_("CSV file is empty."))

    # Normalized (collapsed whitespace + casefold) so "Payment Amount",
    # " payment  amount ", etc. all match the same column — hand-typed
    # spreadsheet headers are never byte-exact.
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
        label = parent.get("Reference No") or parent.get("vendor") or "(unlabeled group)"

        trip_rows = []
        for row in group["rows"]:
            trip_name = cell(row, "Trip (Trips)")
            if not trip_name:
                continue
            trip_rows.append({
                "trip": trip_name,
                "payment_amount": flt(cell(row, "Payment Amount")),
            })
        if not trip_rows:
            results.append({"label": label, "status": "Skipped", "message": _("No trip rows in this group.")})
            continue

        # ignore_validations = 1 if any(
        #     _parse_import_bool(cell(row, "Ignore Validations")) for row in group["rows"]
        # ) else 0
        # ^ the downloaded template's header is "Ignore Validations (Import
        # Only)" (the field's label), so this lookup never matched and the
        # flag was always 0. See read_ignore_validations_flag().
        ignore_validations = read_ignore_validations_flag(cell, group["rows"])

        # Undo only *this* group on failure. A bare frappe.db.rollback() here
        # threw away every earlier group's insert in the same run (they were
        # still uncommitted) and reverted the Import Log's own "Running" save,
        # whose stale timestamp then made the log's final save() throw
        # "Import Log has been modified after you have opened it" — one bad
        # group aborted the entire import.
        savepoint = f"tms_vp_import_{len(results)}"
        frappe.db.savepoint(savepoint)
        try:
            doc = frappe.get_doc({
                "doctype": "Vendor Payment",
                "payment_date": _strict_import_date(parent["payment_date"]) if parent["payment_date"] else None,
                "from_date": _strict_import_date(parent["from_date"]) if parent["from_date"] else None,
                "to_date": _strict_import_date(parent["to_date"]) if parent["to_date"] else None,
                "company": parent["company"] or None,
                "paid_from_account": _validate_link_value(paid_from_account_field, parent["paid_from_account"]) or None,
                "mode_of_payment": parent["mode_of_payment"] or None,
                "vendor": parent["vendor"] or None,
                "reference_no": parent["Reference No"] or None,
                "upi_id": parent["UPI ID"] or None,
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
