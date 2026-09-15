import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


def _get_loading_unloading_company_limit(trip_no):
    """Return only the loading/unloading amount payable by Company or Company Driver."""
    trip = frappe.db.get_value(
        "Trip",
        trip_no,
        ["loading_charge", "loading_charge_payment_by",
         "unloading_charge", "unloading_charge_payment_by"],
        as_dict=True,
    )
    if not trip:
        return 0
    company_paid = {"Company", "Company Driver"}
    loading = flt(trip.loading_charge or 0) if (trip.loading_charge_payment_by or "") in company_paid else 0
    unloading = flt(trip.unloading_charge or 0) if (trip.unloading_charge_payment_by or "") in company_paid else 0
    return loading + unloading


def _get_loading_company_limit(trip_no):
    """Return loading_charge only if payable by Company or Company Driver, else 0."""
    trip = frappe.db.get_value(
        "Trip", trip_no, ["loading_charge", "loading_charge_payment_by"], as_dict=True
    )
    if not trip:
        return 0
    company_paid = {"Company", "Company Driver"}
    return flt(trip.loading_charge or 0) if (trip.loading_charge_payment_by or "") in company_paid else 0


def _get_unloading_company_limit(trip_no):
    """Return unloading_charge only if payable by Company or Company Driver, else 0."""
    trip = frappe.db.get_value(
        "Trip", trip_no, ["unloading_charge", "unloading_charge_payment_by"], as_dict=True
    )
    if not trip:
        return 0
    company_paid = {"Company", "Company Driver"}
    return flt(trip.unloading_charge or 0) if (trip.unloading_charge_payment_by or "") in company_paid else 0


def _get_extra_expense_company_limit(trip_no):
    """Return extra_expenses only if paid by Company or Company Driver, else 0."""
    trip = frappe.db.get_value(
        "Trip",
        trip_no,
        ["extra_expenses", "extra_expense_paid_by"],
        as_dict=True,
    )
    if not trip:
        return 0
    company_paid = {"Company", "Company Driver"}
    return flt(trip.extra_expenses or 0) if (trip.extra_expense_paid_by or "") in company_paid else 0


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_trips(doctype, txt, searchfield, start, page_len, filters):
    search_txt = f"%{txt}%"
    return frappe.db.sql("""
        SELECT
            name,
            CONCAT_WS('  |  ',
                CASE WHEN tcntrip_no IS NOT NULL AND tcntrip_no != ''
                     THEN CONCAT('Tcn/Trip No: ', tcntrip_no) ELSE NULL END,
                CASE WHEN vehicle_no IS NOT NULL AND vehicle_no != ''
                     THEN CONCAT('Vehicle No: ', vehicle_no)
                     WHEN vehicle_market IS NOT NULL AND vehicle_market != ''
                     THEN CONCAT('Vehicle (Market): ', vehicle_market)
                     ELSE NULL END,
                CASE WHEN lr_no IS NOT NULL AND lr_no != ''
                     THEN CONCAT('LR No: ', lr_no) ELSE NULL END,
                CASE WHEN indent_no IS NOT NULL AND indent_no != ''
                     THEN CONCAT('Indent No: ', indent_no) ELSE NULL END,
                CASE WHEN so IS NOT NULL AND so != ''
                     THEN CONCAT('SO/PO No: ', so) ELSE NULL END
            ) AS description
        FROM `tabTrip`
        WHERE (name                    LIKE %(txt)s
            OR tcntrip_no              LIKE %(txt)s
            OR vehicle_no              LIKE %(txt)s
            OR vehicle_market          LIKE %(txt)s
            OR lr_no                   LIKE %(txt)s
            OR so                      LIKE %(txt)s
            OR indent_no               LIKE %(txt)s
            OR eway_bill_no            LIKE %(txt)s
            OR customer_invoice_no     LIKE %(txt)s
            OR seal_no                 LIKE %(txt)s
            OR driver_mobile           LIKE %(txt)s
            OR customer                LIKE %(txt)s
            OR vendor                  LIKE %(txt)s
            OR driver                  LIKE %(txt)s
            OR driver_market           LIKE %(txt)s
            OR driver_mobile_market    LIKE %(txt)s
            OR awb_no_for_dispatch     LIKE %(txt)s
            OR bookingid               LIKE %(txt)s
            OR bill_nodate             LIKE %(txt)s
            OR utr_no                  LIKE %(txt)s
            OR payment_advice_no       LIKE %(txt)s
            OR courier_name            LIKE %(txt)s
            OR origin_city             LIKE %(txt)s
            OR destination_city_1      LIKE %(txt)s
            OR branch                  LIKE %(txt)s)
        ORDER BY name DESC
        LIMIT %(start)s, %(page_len)s
    """, {"txt": search_txt, "start": start, "page_len": page_len})


@frappe.whitelist()
def get_trip_payment_balance(trip_no, payment_type, exclude_payment=None):
    field_map = {
        "Employee LR Money": "employee_lr_money",
    }
    if payment_type == "Loading":
        limit = _get_loading_company_limit(trip_no)
    elif payment_type == "Unloading":
        limit = _get_unloading_company_limit(trip_no)
    elif payment_type == "Loading/Unloading":  # legacy combined type (kept for old records)
        limit = _get_loading_unloading_company_limit(trip_no)
    elif payment_type == "Extra Expense":
        limit = _get_extra_expense_company_limit(trip_no)
    else:
        trip_field = field_map.get(payment_type)
        if not trip_field:
            return {"limit": 0, "already_paid": 0, "balance": 0}
        limit = flt(frappe.db.get_value("Trip", trip_no, trip_field) or 0)
    already_paid = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0) FROM `tabPayment`
        WHERE trip_no = %s AND type = %s AND docstatus = 1 AND name != %s
    """, (trip_no, payment_type, exclude_payment or ""))[0][0])
    return {"limit": limit, "already_paid": already_paid, "balance": limit - already_paid}


@frappe.whitelist()
def get_trip_payments(trip_no):
    return frappe.db.sql("""
        SELECT
            p.name, p.date, p.type, p.amount,
            COALESCE(NULLIF(p.vendor_supplier, ''), NULLIF(e.employee_name, ''), NULLIF(p.driver, ''), '') AS party
        FROM `tabPayment` p
        LEFT JOIN `tabEmployee` e ON e.name = p.employee
        WHERE p.trip_no = %s AND p.docstatus = 1
        ORDER BY p.date ASC
    """, (trip_no,), as_dict=True)


class Payment(Document):
    def before_insert(self):
        self.status = self.status or "Draft"

    def validate(self):
        self._validate_reference_no_format()
        self._validate_reference_no_unique()
        self._mirror_cash_withdrawal_destination_account()
        self._validate_transfer_accounts_differ()

    def _mirror_cash_withdrawal_destination_account(self):
        """A Cash Withdrawal moves money out of a bank account and into a
        CASH-group account (physical cash held by an employee) — same shape
        as a Bank Transfer, just with the destination captured in
        `select_account` instead of `transfer_to_account` (the field the UI
        actually shows for this type). Mirror it into `transfer_to_account`
        so the same generic Both-direction ledger/reconciliation leg
        derivation that already handles Bank Transfer (see
        TMS Reconciliation Source "Payment" row, credit_account_fieldname=
        transfer_to_account) also writes the Credit-side ledger entry into
        the cash account — without this, only the Debit leg out of the bank
        got recorded and the cash account's own balance never moved.
        """
        if self.type == "Cash Withdrawal":
            self.transfer_to_account = self.select_account

    def _validate_transfer_accounts_differ(self):
        if self.type not in ("Bank Transfer", "Cash Withdrawal"):
            return
        if self.paid_from_account and self.paid_from_account == self.transfer_to_account:
            frappe.throw(_("Paid From Account and Transfer To/Cash Account cannot be the same."))

    def _validate_reference_no_format(self):
        if not self.reference_no:
            return
        value = self.reference_no.strip()
        if len(value) < 8:
            frappe.throw(_(
                "Reference No. must be at least 8 characters — enter the actual bank/UPI "
                "transaction reference. Values like '1', '0', or 'NA' are not valid."
            ))

    def _validate_reference_no_unique(self):
        if not self.reference_no:
            return
        duplicate = frappe.db.get_value(
            "Payment",
            {"reference_no": self.reference_no, "name": ("!=", self.name or "")},
            "name",
        )
        if duplicate:
            frappe.throw(_("Reference No. {0} already used in {1}.").format(self.reference_no, duplicate))

    def before_save(self):
        if self.trip_no and (not self.trip_tcn_no or not self.vf_vehicle):
            trip = frappe.db.get_value(
                "Trip",
                self.trip_no,
                ["tcntrip_no", "tcntrip_date", "trip_type", "origin_city", "destination_city_1",
                 "vehicle_type", "vehicle_no", "vehicle_market"],
                as_dict=True,
            )
            if trip:
                self.trip_tcn_no = trip.tcntrip_no
                self.trip_date = trip.tcntrip_date
                self.trip_type = trip.trip_type
                self.trip_origin = trip.origin_city
                self.trip_destination = trip.destination_city_1
                self.trip_vehicle_type = trip.vehicle_type
                if self.type != "Vehicle Finance EMI":
                    vehicle_no = trip.vehicle_no or trip.vehicle_market
                    if vehicle_no:
                        self.vf_vehicle = vehicle_no

        if self.type == "Vehicle Finance EMI" and self.vehicle_finance:
            vf = frappe.get_doc("Vehicle Finance", self.vehicle_finance)
            self.vf_vehicle = vf.vehicle
            self.trip_vehicle_type = frappe.db.get_value("Vehicle", vf.vehicle, "custom_vehicle_type") if vf.vehicle else ""
            self.vf_financer = vf.finance
            self.vf_loan_account = vf.loan_account or ""
            self.amount = vf.emi_amount
            self.paid_from_account = vf.bank_name
            self.mode_of_payment = vf.payment_mode or "Bank Transfer"

    def autoname(self):
        from frappe.model.naming import make_autoname
        self.name = make_autoname("PMT-.YYYY.-.MM.-.#####")
        self.payment_no = self.name

    # Types that do not require a trip and have no trip-based payment limit
    NO_TRIP_TYPES = (
        "Office/Other Expense", "Employee Advance", "Employee Incentive", "Driver Advance", "Vehicle Finance EMI",
        "Border Crossing/Vehicle Expense/Toll Tax", "Police Entry", "Bank Transfer", "Cash Withdrawal",
    )

    def on_submit(self):
        if self.mode_of_payment == "UPI" and not self.upi_id:
            frappe.throw(_("Please enter UPI ID before submitting."))
        if self.mode_of_payment in ("Bank Transfer", "Cheque") and not self.reference_no:
            frappe.throw(_("Please enter Reference No before submitting."))
        if self.type not in self.NO_TRIP_TYPES:
            self._validate_payment_limit()
        # self._create_journal_entry_for_office_expense()  # Payment Entry disabled
        # self._create_payment_entry()                     # Payment Entry disabled
        self.db_set("status", "Paid")
        if self.type == "Vehicle Finance EMI" and self.vehicle_finance:
            vf = frappe.get_doc("Vehicle Finance", self.vehicle_finance)
            vf.update_emi_summary()
        # Account Ledger Entries for both legs are written generically by
        # logicore.utils.account_balance_utils.on_submit_write_ledger,
        # wired via hooks.py doc_events — not here, to keep every TMS
        # Reconciliation Source target_doctype on one shared code path.

    def _validate_payment_limit(self):
        if not self.trip_no or not self.type:
            return
        field_map = {
            "Employee LR Money": "employee_lr_money",
        }
        if self.type == "Loading":
            limit = _get_loading_company_limit(self.trip_no)
        elif self.type == "Unloading":
            limit = _get_unloading_company_limit(self.trip_no)
        elif self.type == "Loading/Unloading":  # legacy combined type (kept for old records)
            limit = _get_loading_unloading_company_limit(self.trip_no)
        elif self.type == "Extra Expense":
            limit = _get_extra_expense_company_limit(self.trip_no)
        else:
            trip_field = field_map.get(self.type)
            if not trip_field:
                return
            limit = flt(frappe.db.get_value("Trip", self.trip_no, trip_field) or 0)
        already_paid = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0) FROM `tabPayment`
            WHERE trip_no = %s AND type = %s AND docstatus = 1 AND name != %s
        """, (self.trip_no, self.type, self.name or ""))[0][0])
        balance = limit - already_paid
        if flt(self.amount) > balance:
            frappe.throw(_(
                "{0}: Payment of {1} exceeds available balance of {2} "
                "(Trip {3} allows {4}, already paid {5})."
            ).format(
                self.type,
                frappe.format_value(self.amount, {"fieldtype": "Currency"}),
                frappe.format_value(balance, {"fieldtype": "Currency"}),
                self.trip_no,
                frappe.format_value(limit, {"fieldtype": "Currency"}),
                frappe.format_value(already_paid, {"fieldtype": "Currency"}),
            ))

    # Payment Entry / Journal Entry integration disabled — managed via Account Head
    # def _create_journal_entry_for_office_expense(self): ...
    # def _create_payment_entry(self): ...

    def on_cancel(self):
        # self._cancel_payment_entry()  # Payment Entry integration disabled
        self.db_set("status", "Cancelled")
        if self.type == "Vehicle Finance EMI" and self.vehicle_finance:
            vf = frappe.get_doc("Vehicle Finance", self.vehicle_finance)
            vf.update_emi_summary()
        # current_balance reversal is handled generically — see on_submit's note.

    # Payment Entry integration disabled
    # def _cancel_payment_entry(self):
    #     if self.payment_entry:
    #         pe = frappe.get_doc("Payment Entry", self.payment_entry)
    #         pe.cancel()
    #         self.db_set("payment_entry", None)
