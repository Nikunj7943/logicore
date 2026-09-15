import re
import frappe
from frappe import _
from frappe.model import get_permitted_fields
from frappe.model.document import Document
from frappe.utils import today, getdate, now_datetime, time_diff_in_hours, flt, cint
from frappe.model.naming import make_autoname
from datetime import date, datetime

LOADING_FREE_HOURS   = 24
UNLOADING_FREE_HOURS = 24
KMS_PER_DAY          = 400


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Time calculations
# ══════════════════════════════════════════════════════════════════════════════

def hours_between(dt1, dt2):
    if not dt1 or not dt2:
        return 0.0
    try:
        return abs(time_diff_in_hours(str(dt2), str(dt1)))
    except Exception:
        return 0.0


def hours_to_readable(hours):
    if not hours:
        return "0h"
    h = int(hours)
    m = int((hours - h) * 60)
    d = h // 24
    h = h % 24
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    return " ".join(parts) if parts else "0h"


def _get_fy_key(trip_date):
    """Return 4-char financial-year key: e.g. '2526' for Apr 2025 – Mar 2026."""
    y, m = trip_date.year, trip_date.month
    start = y if m >= 4 else y - 1
    return f"{str(start)[2:]}{str(start + 1)[2:]}"


# def detention_days(total_hours, free_hours=24):
#     if total_hours <= free_hours:
#         return 0
#     excess = total_hours - free_hours
#     return int(excess // 24) + (1 if excess % 24 > 0 else 0)

def detention_days(total_hours, free_hours=24):
    return int(total_hours // 24)
# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Distance from master
# ══════════════════════════════════════════════════════════════════════════════

def get_distance_between(origin_city, destination_city):
    if not origin_city or not destination_city:
        return 0
    for dt in ["City Distance", "Route Master"]:
        if frappe.db.exists("DocType", dt):
            dist = frappe.db.get_value(
                dt,
                {"origin_city": origin_city, "destination_city": destination_city},
                "distance"
            ) or frappe.db.get_value(
                dt,
                {"origin_city": destination_city, "destination_city": origin_city},
                "distance"
            )
            if dist:
                return flt(dist)
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Billing cycle dates from Business Format record
# ══════════════════════════════════════════════════════════════════════════════

# def get_billing_dates_for_current_month(billing_start_date, billing_end_date, reference_date=None):
#     """
#     Given template dates from Business Format, shift their day numbers onto
#     the month of reference_date (defaults to today).

#     Same-month cycle (end_day >= start_day), e.g. 1 to 31:
#         1st of ref month to last day of ref month (capped)

#     Cross-month cycle (end_day < start_day), e.g. 26 to 25:
#         26th of PREVIOUS month to 25th of ref month
#     """
#     import calendar

#     ref_d     = getdate(reference_date or today())
#     start_day = getdate(billing_start_date).day
#     end_day   = getdate(billing_end_date).day

#     yr  = ref_d.year
#     mon = ref_d.month

#     if end_day >= start_day:
#         last_day = calendar.monthrange(yr, mon)[1]
#         b_start  = date(yr, mon, start_day)
#         b_end    = date(yr, mon, min(end_day, last_day))
#     else:
#         if mon == 1:
#             prev_yr, prev_mon = yr - 1, 12
#         else:
#             prev_yr, prev_mon = yr, mon - 1
#         b_start = date(prev_yr, prev_mon, start_day)
#         b_end   = date(yr, mon, end_day)

#     return b_start, b_end
def get_billing_dates_for_current_month(billing_start_date, billing_end_date, reference_date=None):
    import calendar

    ref_d     = getdate(reference_date or today())
    yr        = ref_d.year
    mon       = ref_d.month

    # Day numbers from the template
    start_day = getdate(billing_start_date).day

    billing_end_dt  = getdate(billing_end_date)
    end_day         = billing_end_dt.day
    # Check if template end = last day of its own month (e.g. Feb 28, Mar 31)
    tpl_month_last  = calendar.monthrange(billing_end_dt.year, billing_end_dt.month)[1]
    end_is_eom      = (end_day == tpl_month_last)

    # Last day of the TRIP's month
    trip_month_last = calendar.monthrange(yr, mon)[1]

    # Resolve actual end day for trip's month
    resolved_end = trip_month_last if end_is_eom else min(end_day, trip_month_last)

    if end_day >= start_day:
        # Same-month cycle: e.g. 1→28, 1→15, 1→31
        b_start = date(yr, mon, start_day)
        b_end   = date(yr, mon, resolved_end)
    else:
        # Cross-month cycle: e.g. 26→25
        if mon == 1:
            prev_yr, prev_mon = yr - 1, 12
        else:
            prev_yr, prev_mon = yr, mon - 1
        b_start = date(prev_yr, prev_mon, start_day)
        b_end   = date(yr, mon, resolved_end)

    return b_start, b_end

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DOCUMENT CLASS
# ══════════════════════════════════════════════════════════════════════════════

class Trip(Document):

    def onload(self):
        # Fetch Vendor Payments
        self.set_onload("vendor_payments", frappe.db.sql("""
            SELECT
                vpt.parent AS reference,
                vp.payment_date,
                vpt.payment_amount,
                vpt.transfer_amount,
                vpt.tds_amount,
                vpt.employee_lr_money,
                vpt.company_lr_money,
                vp.vendor
            FROM `tabVendor Payment Trip` vpt
            INNER JOIN `tabVendor Payment` vp ON vp.name = vpt.parent
            WHERE vpt.trip = %s
              AND vp.docstatus = 1
            ORDER BY vp.payment_date ASC
        """, (self.name,), as_dict=True))

        # Fetch Regular Payments
        self.set_onload("payments", frappe.db.sql("""
            SELECT
                p.name,
                p.date AS payment_date,
                p.amount,
                p.type AS payment_type,
                COALESCE(NULLIF(p.vendor_supplier, ''), NULLIF(e.employee_name, ''), '') AS party
            FROM `tabPayment` p
            LEFT JOIN `tabEmployee` e ON e.name = p.employee
            WHERE p.trip_no = %s
              AND p.docstatus = 1
            ORDER BY p.date ASC
        """, (self.name,), as_dict=True))

        # Fetch Customer Receipts — invoice_amount and outstanding computed in JS from trip fields
        self.set_onload("receipts", frappe.db.sql("""
            SELECT
                crt.parent AS name,
                r.payment_date,
                SUM(COALESCE(crt.received_amount, 0)) AS received_amount,
                SUM(COALESCE(crt.brokerage_amount, 0)) AS brokerage_amount,
                SUM(COALESCE(crt.lr_money, 0)) AS lr_money,
                SUM(COALESCE(crt.tds_amount, 0)) AS tds_amount
            FROM `tabCustomer Receipt Trip` crt
            INNER JOIN `tabReceipt` r ON r.name = crt.parent
            WHERE crt.trip = %s
              AND r.docstatus = 1
            GROUP BY crt.parent, r.payment_date
            ORDER BY r.payment_date ASC
        """, (self.name,), as_dict=True))

    def autoname(self):
        trip_date = getdate(self.tcntrip_date) if self.tcntrip_date else now_datetime().date()

        # ── 1. Company abbreviation ────────────────────────────────────
        company_abbr = "TMS"
        if self.company:
            abbr = frappe.db.get_value("Company", self.company, "abbr")
            if abbr:
                company_abbr = abbr.upper()

        # ── 2. Trip Type code ──────────────────────────────────────────
        type_code = None
        if self.trip_type:
            code = frappe.db.get_value("Trip Type", self.trip_type, "code")
            if code:
                type_code = code.strip().upper()
        if not type_code:
            frappe.throw(
                f"Trip Type <b>{self.trip_type or '(not set)'}</b> has no Code configured. "
                "Set a single-character Code in the Trip Type master.",
                title="Trip Type Code Missing"
            )

        # ── 3. Build keys ──────────────────────────────────────────────
        # series_key = company + FY only → ONE shared counter for all trip types in the FY
        # name_prefix keeps type_code so the name still shows the type
        mmyy        = trip_date.strftime("%m%y")                    # e.g. "0426"
        fy_key      = _get_fy_key(trip_date)                        # e.g. "2627"
        name_prefix = f"{company_abbr}-{type_code}-{mmyy}"         # e.g. "UG-P-0426"
        series_key  = f"{company_abbr}-{fy_key}"                   # e.g. "UG-2627"

        # ── 4. Self-heal: max counter across ALL types for this company in this FY ──
        fy_start_year = trip_date.year if trip_date.month >= 4 else trip_date.year - 1
        fy_start = date(fy_start_year, 4, 1)
        fy_end   = date(fy_start_year + 1, 3, 31)

        result = frappe.db.sql("""
            SELECT MAX(CAST(SUBSTRING(name, -5) AS UNSIGNED))
            FROM `tabTrip`
            WHERE tcntrip_date BETWEEN %(s)s AND %(e)s
              AND name REGEXP %(pat)s
        """, {
            "s": fy_start, "e": fy_end,
            "pat": f"^{re.escape(company_abbr)}-[A-Z]-[0-9]{{4}}[0-9]{{5}}$",
        }, as_list=True)

        db_max = int(result[0][0] or 0) if result else 0
        if db_max > 0:
            frappe.db.sql("""
                INSERT INTO tabSeries (name, current) VALUES (%(key)s, %(val)s)
                ON DUPLICATE KEY UPDATE current = GREATEST(current, %(val)s)
            """, {"key": series_key, "val": db_max})

        series_name = make_autoname(f"{series_key}.#####")
        counter     = series_name.replace(series_key, "")          # e.g. "00005"
        self.name   = f"{name_prefix}{counter}"                    # e.g. "UG-D-042600005"
    # ── Before Save ───────────────────────────────────────────────────────────

    def validate(self):

        if not self.is_new():
            old_trip_type = frappe.db.get_value("Trip", self.name, "trip_type")
            if old_trip_type and self.trip_type != old_trip_type:
                frappe.throw(
                    f"Trip Type cannot be changed after the trip has been saved. "
                    f"Current value: <b>{old_trip_type}</b>",
                    title="Trip Type Locked"
                )
        self._validate_unique_fields()
        self._validate_chronology()
        self._validate_pod_upload()
        self._validate_km()
        self._validate_payment_field_reduction()

    def _validate_unique_fields(self):
        fields = [
            ("indent_no",  "Indent No"),
            ("tcntrip_no", "TCN/Trip No"),
            ("lr_no",      "LR No"),
            # ("so",         "SO/PO No"),  # unique validation removed — SO/PO No can repeat across trips
        ]
        errors = []
        for fieldname, label in fields:
            value = (getattr(self, fieldname, None) or "").strip()
            if not value:
                continue
            filters = {fieldname: value}
            if not self.is_new():
                filters["name"] = ["!=", self.name]
            duplicate = frappe.db.get_value("Trip", filters, "name")
            if duplicate:
                errors.append(
                    f"<b>{label}</b> <i>{value}</i> is already used in "
                    f'Trip <a href="/app/trip/{duplicate}" target="_blank">{duplicate}</a>.'
                )
        if errors:
            frappe.throw("<br><br>".join(errors), title="Duplicate Value Error")
    
    def _validate_chronology(self):
        from frappe.utils import get_datetime

        def _dt(val):
            if not val:
                return None
            try:
                return get_datetime(val)
            except Exception:
                return None

        sequence = [
            ("reach_date_time", "Reach Loading Point Date/Time"),
            ("dispatch_date_time", "Dispatch Loading Point Date/Time"),
            ("arrival_date_time", "Arrival Unloading Point Date/Time"),
            ("release_date_time", "Release Unloading Point Date/Time"),
        ]

        errors = []
        for i in range(1, len(sequence)):
            prev_field, prev_label = sequence[i - 1]
            cur_field, cur_label = sequence[i]
            prev_val = _dt(getattr(self, prev_field, None))
            cur_val = _dt(getattr(self, cur_field, None))
            if cur_val and not prev_val:
                errors.append(f"<b>{prev_label}</b> must be entered before <b>{cur_label}</b>.")
            elif prev_val and cur_val and cur_val < prev_val:
                errors.append(f"<b>{cur_label}</b> cannot be before <b>{prev_label}</b>.")

        if errors:
            frappe.throw("<br>".join(errors), title="Chronology Validation Error")

    def _validate_pod_upload(self):
        if self.date_pod_uploaded_on_erp:
            # Only validate when the field is being set for the first time
            if not self.is_new():
                old_val = frappe.db.get_value("Trip", self.name, "date_pod_uploaded_on_erp")
                if old_val:
                    return
            if not self.arrival_date_time or not self.release_date_time:
                frappe.throw(
                    "POD cannot be uploaded until <b>Arrival Date/Time</b> and <b>Release Date/Time</b> "
                    "at the Unloading Site have been filled.",
                    title="POD Upload Not Allowed"
                )

    def _validate_km(self):
        from frappe.utils import flt as _flt
        start = _flt(self.start_km)
        end   = _flt(self.end_km)
        if start and end and end < start:
            frappe.throw(
                f"End KM (<b>{end}</b>) cannot be less than Start KM (<b>{start}</b>).",
                title="KM Validation Error"
            )

    def _validate_payment_field_reduction(self):
        if self.is_new():
            return
        from frappe.utils import flt as _flt

        # --- Payment doctype checks (Loading, Unloading, Extra Expense, Employee LR Money) ---
        field_map = {
            # "Loading/Unloading": "total_loading_unloading_charge",  # split into separate Loading / Unloading types
            "Loading": "loading_charge",
            "Unloading": "unloading_charge",
            "Extra Expense": "extra_expenses",
            "Employee LR Money": "employee_lr_money",
        }
        for payment_type, trip_field in field_map.items():
            new_value = _flt(getattr(self, trip_field, 0))
            payments = frappe.db.sql("""
                SELECT name, amount FROM `tabPayment`
                WHERE trip_no = %s AND type = %s AND docstatus = 1
                ORDER BY creation
            """, (self.name, payment_type), as_dict=True)
            already_paid = sum(_flt(p.amount) for p in payments)
            if already_paid > 0 and new_value < already_paid:
                links = "".join(
                    f'<li><a href="/app/payment/{p.name}" target="_blank">{p.name}</a>'
                    f' — {frappe.format_value(p.amount, {"fieldtype": "Currency"})}</li>'
                    for p in payments
                )
                frappe.throw(
                    _("{0} amount cannot be set to {1} because {2} has already been paid against this trip.<br><br>"
                      "Please cancel or delete the following payment entries first, then reduce the amount:<br>"
                      "<ul>{3}</ul>").format(
                        payment_type,
                        frappe.format_value(new_value, {"fieldtype": "Currency"}),
                        frappe.format_value(already_paid, {"fieldtype": "Currency"}),
                        links,
                    ),
                    title=_("Payment Already Made")
                )

        # --- Vendor Payment check (total_vendor_freight) ---
        new_freight = _flt(getattr(self, "total_vendor_freight", 0))
        vp_entries = frappe.db.sql("""
            SELECT vp.name, vp.payment_date, vpt.payment_amount
            FROM `tabVendor Payment` vp
            JOIN `tabVendor Payment Trip` vpt ON vpt.parent = vp.name
            WHERE vpt.trip = %s AND vp.docstatus = 1
            ORDER BY vp.payment_date
        """, (self.name,), as_dict=True)
        total_vp_paid = sum(_flt(r.payment_amount) for r in vp_entries)
        if total_vp_paid > 0 and new_freight < total_vp_paid:
            links = "".join(
                f'<li><a href="/app/vendor-payment/{r.name}" target="_blank">{r.name}</a>'
                f' — {frappe.format_value(r.payment_amount, {"fieldtype": "Currency"})}'
                f' ({frappe.utils.formatdate(r.payment_date)})</li>'
                for r in vp_entries
            )
            frappe.throw(
                _("Vendor Freight cannot be set to {0} because {1} has already been paid to the vendor against this trip.<br><br>"
                  "Please cancel or delete the following Vendor Payment entries first, then reduce the amount:<br>"
                  "<ul>{2}</ul>").format(
                    frappe.format_value(new_freight, {"fieldtype": "Currency"}),
                    frappe.format_value(total_vp_paid, {"fieldtype": "Currency"}),
                    links,
                ),
                title=_("Vendor Payment Already Made")
            )

    def after_save(self):
        if self.vehicle_no and self.end_km:
            frappe.db.set_value("Vehicle", self.vehicle_no, "last_odometer", cint(self.end_km))

    def _recalc_vendor_payment_status(self):
        """Recompute vendor payment status based on current freight vs total paid.
        Called in before_save so db_update writes the correct values."""
        if self.is_new():
            return
        total_paid = flt(frappe.db.get_value("Trip", self.name, "total_vendor_paid") or 0)
        new_freight = flt(self.total_vendor_freight or 0)
        balance = new_freight - total_paid
        if total_paid <= 0:
            status = "Unpaid"
        elif balance <= 0:
            status = "Paid"
        else:
            status = "Partially Paid"
        self.vendor_balance_amount = max(balance, 0)
        self.vendor_payment_status = status

    def before_save(self):

        if self.name:
            self.so_no = self.name

        # Auto-fill billing dates from Business Format
        self._calc_billing_dates()

        if self.driver:
        # Fetch the name once on the server side
            self.driver_name = frappe.db.get_value("Driver", self.driver, "full_name")
        else:
            self.driver_name = ""

        # Run all calculations
        self._calc_distance_and_journey_time()
        self._calc_loading_detention()
        self._calc_unloading_detention()
        self._calc_total_detention()
        self._calc_loading_unloading_total()
        self._calc_total_additional_charges()
        self._calc_vendor_freight()
        self._calc_dedicated_km()
        self._calc_approved_charges()
        self._calc_trip_totals()
        self._calc_vendor_payment_total()
        self._recalc_vendor_payment_status()
        self._update_pod_status()
        self._derive_states()
        self._fill_address_display_fields()

    # ── 0. Billing Dates from Business Format ─────────────────────────────────

    def _calc_billing_dates(self):
        if not self.business_format:
            return

        bf = frappe.db.get_value(
            "Business Format",
            self.business_format,
            ["billing_start_date", "billing_end_date"],
            as_dict=True,
        )
        if not bf or not bf.get("billing_start_date") or not bf.get("billing_end_date"):
            return

        b_start, b_end = get_billing_dates_for_current_month(
            bf["billing_start_date"], bf["billing_end_date"],
            reference_date=self.tcntrip_date,
        )
        self.billing_start_date = str(b_start)
        self.billing_end_date   = str(b_end)

    # ── 1. Distance & Journey Time ─────────────────────────────────────────────

    def _calc_distance_and_journey_time(self):
        dist = get_distance_between(self.origin_city, self.destination_city_1)
        if dist:
            self.distance_loadingunloading_site = dist

        dist = flt(self.distance_loadingunloading_site) or 0
        if dist:
            self.journey_time_400_kmsday = hours_to_readable((dist / KMS_PER_DAY) * 24)

        actual_hours = hours_between(self.dispatch_date_time, self.arrival_date_time)
        if actual_hours:
            self.journey_time = hours_to_readable(actual_hours)

    # ── 2. Loading Site Detention ──────────────────────────────────────────────

    def _calc_loading_detention(self):
        if self.reach_date_time and self.dispatch_date_time:
            total_hrs = hours_between(self.reach_date_time, self.dispatch_date_time)
            self.loading_detention_days = detention_days(total_hrs, LOADING_FREE_HOURS)
        else:
            self.loading_detention_days = self.loading_detention_days or 0

        self.loading_site_detention_amount = (
            cint(self.loading_detention_days) * flt(self.loading_detention_rate_per_day)
        )

    # ── 3. Unloading Site Detention ────────────────────────────────────────────

    def _calc_unloading_detention(self):
        if self.arrival_date_time and self.release_date_time:
            total_hrs = hours_between(self.arrival_date_time, self.release_date_time)
            self.unloading_detention_days = detention_days(total_hrs, UNLOADING_FREE_HOURS)
        else:
            self.unloading_detention_days = self.unloading_detention_days or 0

        self.unloading_site_detention_amount = (
            cint(self.unloading_detention_days) * flt(self.unloading_detention_rate_per_day)
        )

    # ── 4. Total Detention ─────────────────────────────────────────────────────

    def _calc_total_detention(self):
        self.total_detention_days = (
            cint(self.loading_detention_days or 0)
            + cint(self.unloading_detention_days or 0)
        )
        self.total_detention_amount = (
            flt(self.loading_site_detention_amount or 0)
            + flt(self.unloading_site_detention_amount or 0)
        )

    # ── 5. Loading + Unloading total ──────────────────────────────────────────

    def _calc_loading_unloading_total(self):
        self.total_loading_unloading_charge = (
            flt(self.loading_charge or 0) + flt(self.unloading_charge or 0)
        )

    # ── 6. Total Additional Charges ────────────────────────────────────────────

    def _calc_total_additional_charges(self):
        self.total_additional_charges = (
            flt(self.total_detention_amount or 0)
            + flt(self.total_loading_unloading_charge or 0)
            + flt(self.weighment_charges or 0)
            + flt(self.extra_expenses or 0)
        )

    # ── 7. Vendor Freight ─────────────────────────────────────────────────────

    def _calc_vendor_freight(self):
        self.total_vendor_freight = (
            flt(self.vendor_freight or 0) + flt(self.vendor_freight_extra or 0)
        )

    
    def _calc_dedicated_km(self):
        start = flt(self.start_km or 0)
        end   = flt(self.end_km or 0)
        self.total_km = end - start         

        std = flt(self.standard_km or 0)
        if std:
            self.variation = flt(self.total_km) - std

    # ── 9. Approved Charges ────────────────────────────────────────────────────

    def _calc_approved_charges(self):
        self.approved_detention_charge = (
            flt(self.approved_origin_detention or 0)
            + flt(self.approved_destination_detention or 0)
        )
        self.approved_loadingunloading_charge = (
            flt(self.approved_loading_charge or 0)
            + flt(self.approved_unloading_charge or 0)
        )
        total_approved = (
            flt(self.approved_detention_charge or 0)
            + flt(self.approved_loadingunloading_charge or 0)
            + flt(self.approved_weighment_charge or 0)
            + flt(self.approved_extra_expenses or 0)
        )
        self.total_approved_addl_amount = total_approved
        self.difference_claimedapproved = (
            flt(self.total_additional_charges or 0) - flt(self.total_approved_addl_amount or 0)
        )

    # ── 10. Trip Totals ────────────────────────────────────────────────────────

    def _calc_trip_totals(self):
        # Deductions (brokerage, lr_money, tds) are applied at Receipt level, not here
        # if (self.trip_type or "").strip().lower() == "other":
        #     self.total_trip_amount = (
        #         flt(self.customer_freight or 0)
        #         + flt(self.total_approved_addl_amount or 0)
        #         - flt(self.brokerage_amount or 0)
        #         - flt(self.lr_money or 0)
        #         - flt(self.tds_deducted_by_customer or 0)
        #     )
        # else:
        self.total_trip_amount = (
            flt(self.customer_freight or 0) + flt(self.total_approved_addl_amount or 0)
        )

    # ── 11. Vendor Payment Total ───────────────────────────────────────────────

    def _calc_vendor_payment_total(self):
        if self.vendor:
            # Recalculate TDS only when the Vendor Freight value itself has
            # actually changed — saving the Trip after editing an unrelated
            # field must not silently recompute/overwrite this figure.
            if self.is_new():
                freight_changed = True
            else:
                prev_vendor_freight = flt(frappe.db.get_value("Trip", self.name, "vendor_freight") or 0)
                freight_changed = prev_vendor_freight != flt(self.vendor_freight or 0)

            if freight_changed:
                try:
                    import re as _re
                    val = frappe.db.get_value("Supplier", self.vendor, "custom_tds_applicable") or ""
                    m = _re.search(r"(\d+(?:\.\d+)?)", val)
                    tds_pct = flt(m.group(1)) if m else 0
                except Exception:
                    tds_pct = 0
                if tds_pct:
                    # TDS is calculated on the base Vendor Freight only, not on
                    # total_vendor_freight (which also includes vendor_freight_extra).
                    self.vendor_tds_to_be_deducted = flt(
                        flt(self.vendor_freight or 0) * tds_pct / 100, 2
                    )
        self.amount_to_be_paid_to_vendor = flt(self.total_vendor_freight or 0)

    # ── 12. POD Status ─────────────────────────────────────────────────────────

    def _update_pod_status(self):
        if self.date_pod_uploaded_on_erp:
            pod_type = (self.uploaded_pod_originalduplicate or "Original").strip()
            self.pod_status = "Duplicate POD Uploaded" if pod_type == "Duplicate" else "Original POD Uploaded"
        elif not self.pod_status or self.pod_status == "Left":
            self.pod_status = "POD Not Uploaded"

    # ── 13. Derive Origin/Destination States ──────────────────────────────────

    def _derive_states(self):
        if self.origin_city:
            state = frappe.db.get_value("City", self.origin_city, "state")
            if state:
                self.origin_state = state

        if self.destination_city_1:
            state = frappe.db.get_value("City", self.destination_city_1, "state")
            if state:
                self.destination_state = state

    # ── 14. Address Display Fields ────────────────────────────────────────────

    def _fill_address_display_fields(self):
        for addr_field, display_field in [
            ("origin_address_1",      "origin_address_1_full"),
            ("origin_address_2",      "origin_address_2_full"),
            ("destination_address_1", "destination_address_1_full"),
            ("destination_address_2", "destination_address_2_full"),
        ]:
            addr_name = getattr(self, addr_field, None)
            setattr(self, display_field, custom(addr_name) if addr_name else "")




# ══════════════════════════════════════════════════════════════════════════════
#  WHITELISTED APIs
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_vehicle_last_odometer(vehicle_no):
    return frappe.db.get_value("Vehicle", vehicle_no, "last_odometer") or 0


@frappe.whitelist()
def get_vehicle_last_trip_end_km(vehicle_no, trip_name=None):
    # For Secondary/Dedicated trips: start_km = end_km of the last trip for this vehicle
    filters = {"vehicle_no": vehicle_no, "end_km": [">", 0], "docstatus": ["!=", 2]}
    if trip_name:
        filters["name"] = ["!=", trip_name]
    result = frappe.db.get_all(
        "Trip",
        filters=filters,
        fields=["end_km"],
        order_by="creation desc",
        limit=1,
    )
    return result[0].end_km if result else 0


@frappe.whitelist()
def get_vendor_tds(vendor):
    if not vendor:
        return 0
    try:
        import re
        val = frappe.db.get_value("Supplier", vendor, "custom_tds_applicable") or ""
        match = re.search(r"(\d+(?:\.\d+)?)", val)
        return flt(match.group(1)) if match else 0
    except Exception:
        return 0


@frappe.whitelist()
def reset_pod_status(docname):
    """Reset POD fields — works on submitted docs (bypasses docstatus check)."""
    frappe.db.set_value("Trip", docname, {
        "date_pod_uploaded_on_erp":       None,
        "uploaded_pod_originalduplicate": None,
        "pod_status":                     "POD Not Uploaded",
    })
    frappe.db.commit()


@frappe.whitelist()
def validate_pod_file_name(docname, file_name):
    """Enforce the same filename convention bulk POD import uses (must equal the
    Trip's TCN/Trip No or LR No, no hyphens) before the manual POD Manager upload
    on the Trip form accepts a file."""
    from logicore.utils.pod_filename import validate_pod_filename_matches_trip
    validate_pod_filename_matches_trip(docname, file_name)


@frappe.whitelist()
def set_pod_status(docname, pod_date, pod_type):
    """Set POD fields after upload — works on submitted docs."""
    status = "Duplicate POD Uploaded" if pod_type == "Duplicate" else "Original POD Uploaded"
    frappe.db.set_value("Trip", docname, {
        "date_pod_uploaded_on_erp":       pod_date,
        "uploaded_pod_originalduplicate": pod_type,
        "pod_status":                     status,
    })
    frappe.db.commit()


@frappe.whitelist()
def delete_pod_files(docname):
    """Delete all JPG/PNG/PDF file attachments on a Trip before re-uploading POD."""
    import os

    files = frappe.get_all(
        "File",
        filters={"attached_to_doctype": "Trip", "attached_to_name": docname},
        fields=["name", "file_name"],
    )
    deleted = 0
    for f in files:
        if not re.search(r'\.(jpg|jpeg|png|pdf)$', f.file_name or '', re.I):
            continue
        try:
            file_doc = frappe.get_doc("File", f.name)
            physical_path = file_doc.get_full_path()
        except Exception:
            physical_path = None

        frappe.delete_doc("File", f.name, force=True, ignore_permissions=True)

        # Explicitly remove physical file — frappe.delete_doc may skip this
        if physical_path and os.path.exists(physical_path):
            try:
                os.remove(physical_path)
            except Exception:
                pass

        deleted += 1

    frappe.db.commit()
    return {"deleted": deleted}


@frappe.whitelist()
def get_latest_pod_file(docname):
    """Return the most recently uploaded POD (PDF) attached to a Trip, if any."""
    if not docname:
        frappe.throw(_("Trip name is required."))
    if not frappe.has_permission("Trip", "read", doc=docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    files = frappe.get_all(
        "File",
        filters={"attached_to_doctype": "Trip", "attached_to_name": docname},
        fields=["file_name", "file_url"],
        order_by="creation desc",
        limit=10,
    )
    pdf = next((f for f in files if re.search(r'\.pdf$', f.file_name or '', re.I)), None)
    if not pdf:
        return {}
    return {"file_name": pdf.file_name, "file_url": pdf.file_url}


@frappe.whitelist()
def get_city_state(city):
    """Return state for a given city."""
    if not city:
        return ""
    return frappe.db.get_value("City", city, "state") or ""


@frappe.whitelist()
def get_route_distance(origin_city, destination_city):
    """Return distance between two cities from master."""
    return get_distance_between(origin_city, destination_city)


@frappe.whitelist()
def get_user_branch():
    """
    Return branch for the logged-in user.
    Resolution order:
      1. Employee record  (user_id = current user, branch field)
      2. User Permission  (allow = Branch, user = current user)
      3. Any single Branch that exists (if only one branch in system)
    Returns dict: { branch, source, debug }
    """
    user = frappe.session.user

    # 1. Employee linked to this user
    emp = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["name", "branch", "employee_name"],
        as_dict=True,
    )
    if emp:
        if emp.get("branch"):
            return {"branch": emp["branch"], "source": "employee", "debug": None}
        return {
            "branch": None, "source": None,
            "debug": (
                "Employee '{}' has no Branch set. "
                "Open HR > Employees > {} and fill the Branch field.".format(
                    emp.get("employee_name") or emp["name"], emp["name"]
                )
            ),
        }

    # 2. User Permission for Branch
    branch_perm = frappe.db.get_value(
        "User Permission",
        {"user": user, "allow": "Branch"},
        "for_value",
    )
    if branch_perm:
        return {"branch": branch_perm, "source": "user_permission", "debug": None}

    # 3. If only one Branch exists in the system, use it as default
    all_branches = frappe.db.get_all("Branch", pluck="name", limit=2)
    if len(all_branches) == 1:
        return {"branch": all_branches[0], "source": "single_branch", "debug": None}

    # 4. Nothing found — return actionable debug message
    branch_list = ", ".join(all_branches) if all_branches else "none created yet"
    return {
        "branch": None, "source": None,
        "debug": (
            "Auto-branch failed for '{}'. "
            "Quick fix (choose one):\n"
            "A) Settings > User Permissions > New > "
            "User='{}', Allow='Branch', For Value=<your branch>\n"
            "B) HR > Employees > open your employee record > "
            "set User ID='{}' and Branch field.\n"
            "Available branches: {}.".format(user, user, user, branch_list)
        ),
    }


@frappe.whitelist()
def get_billing_cycle_dates(trip_type, business_format, reference_date=None):
    """
    DEPRECATED (kept for backwards compatibility).
    Now billing dates are fetched directly from the Business Format record.
    """
    if not business_format:
        import calendar
        ref  = getdate(reference_date or today())
        last = calendar.monthrange(ref.year, ref.month)[1]
        return {
            "start": str(date(ref.year, ref.month, 1)),
            "end":   str(date(ref.year, ref.month, last)),
        }

    bf = frappe.db.get_value(
        "Business Format",
        business_format,
        ["billing_start_date", "billing_end_date"],
        as_dict=True,
    )
    if not bf or not bf.get("billing_start_date"):
        import calendar
        ref  = getdate(reference_date or today())
        last = calendar.monthrange(ref.year, ref.month)[1]
        return {
            "start": str(date(ref.year, ref.month, 1)),
            "end":   str(date(ref.year, ref.month, last)),
        }

    b_start, b_end = get_billing_dates_for_current_month(
        bf["billing_start_date"], bf["billing_end_date"]
    )
    return {"start": str(b_start), "end": str(b_end)}


@frappe.whitelist()
def render_email_template_for_trip(template_name, trip_name):
    """Renders Email Template with Trip doc context."""
    if not template_name or not trip_name:
        return {"subject": "", "message": ""}

    tpl  = frappe.get_doc("Email Template", template_name)
    trip = frappe.get_doc("Trip", trip_name)

    # Render trip_coordinator (Link to Employee) as the employee's name, not their ID
    if trip.trip_coordinator:
        coordinator_name = frappe.db.get_value("Employee", trip.trip_coordinator, "employee_name")
        if coordinator_name:
            trip.trip_coordinator = coordinator_name

    # Build a dot-accessible dict with dates formatted as DD-MM-YYYY / DD-MM-YYYY HH:MM
    doc_dict = frappe._dict(trip.as_dict())

    for fld in trip.meta.fields:
        val = doc_dict.get(fld.fieldname)
        if not val:
            continue
        if fld.fieldtype == "Date":
            try:
                if isinstance(val, date):
                    doc_dict[fld.fieldname] = val.strftime("%d-%m-%Y")
                else:
                    doc_dict[fld.fieldname] = datetime.strptime(str(val)[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
            except Exception:
                pass
        elif fld.fieldtype == "Datetime":
            try:
                if isinstance(val, datetime):
                    doc_dict[fld.fieldname] = val.strftime("%d-%m-%Y %H:%M")
                else:
                    doc_dict[fld.fieldname] = datetime.strptime(str(val)[:16], "%Y-%m-%d %H:%M").strftime("%d-%m-%Y %H:%M")
            except Exception:
                pass

    context = {"doc": doc_dict}

    try:
        subject = frappe.render_template(tpl.subject or "", context)
        message = frappe.render_template(tpl.response or "", context)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Email Template Render Error")
        subject = tpl.subject or ""
        message = tpl.response or ""

    return {"subject": subject, "message": message}

@frappe.whitelist()
def get_address_display_label(address_name):
    return custom(address_name)


@frappe.whitelist()
def custom(address_name):
    if not address_name:
        return ""

    city_fieldname = None
    try:
        for f in frappe.get_meta("Address").fields:
            if f.fieldtype == "Link" and f.options == "City":
                city_fieldname = f.fieldname
                break
    except Exception:
        pass

    fields = ["address_line1", "address_line2", "county", "state", "custom_postal_code", "pincode"]
    if city_fieldname:
        fields.append(city_fieldname)

    addr = frappe.db.get_value("Address", address_name, fields, as_dict=True)
    if not addr:
        return address_name

    city_name = ""
    state = ""

    if city_fieldname and addr.get(city_fieldname):
        city_name = addr.get(city_fieldname)
        city_state = frappe.db.get_value("City", city_name, "state")
        if city_state:
            state = city_state

    if not state:
        state = (addr.get("state") or "").strip()

    parts = [
        addr.get("address_line1"),
        addr.get("address_line2"),
        addr.get("county"),
        city_name,
        state,
    ]
    label = ", ".join(p for p in parts if p)

    # ── Use custom_postal_code first, fall back to standard pincode ──
    postal = (addr.get("pincode") or "").strip() or (addr.get("custom_postal_code") or "").strip()

    if postal:
        label += f" - {postal}"

    return label or address_name


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_address(doctype, txt, searchfield, start, page_len, filters):
	search_txt = f"%{txt}%"

	# Detect custom City Link fieldname
	city_field = "city"
	try:
		for f in frappe.get_meta("Address").fields:
			if f.fieldtype == "Link" and f.options == "City":
				city_field = f.fieldname
				break
	except Exception:
		pass

	return frappe.db.sql(
		f"""
		SELECT
			a.name,
			NULLIF(TRIM(a.address_line1), '')        AS address_line1,
			NULLIF(TRIM(a.address_line2), '')        AS address_line2,
			NULLIF(TRIM(a.`{city_field}`), '')       AS city,
			NULLIF(TRIM(a.county), '')               AS county,
			COALESCE(
				NULLIF(TRIM(c.state), ''),
				NULLIF(TRIM(a.state), '')
			)                                        AS state,
			NULLIF(TRIM(a.pincode), '')   AS pincode
		FROM `tabAddress` a
		LEFT JOIN `tabCity` c ON c.name = a.`{city_field}`
		WHERE
			a.disabled = 0
			AND (
				a.name                      LIKE %(txt)s
				OR a.address_title          LIKE %(txt)s
				OR a.address_line1          LIKE %(txt)s
				OR a.address_line2          LIKE %(txt)s
				OR a.`{city_field}`         LIKE %(txt)s
				OR a.county                 LIKE %(txt)s
				OR a.state                  LIKE %(txt)s
				OR a.pincode     LIKE %(txt)s
			)
		ORDER BY
			CASE
				WHEN a.`{city_field}`       LIKE %(txt)s THEN 1
				WHEN a.address_line2        LIKE %(txt)s THEN 2
				WHEN a.county               LIKE %(txt)s THEN 3
				WHEN a.pincode   LIKE %(txt)s THEN 4
				ELSE 5
			END,
			LOWER(REGEXP_REPLACE(a.name, '[[:digit:]]+', '')),
			CAST(IFNULL(NULLIF(REGEXP_SUBSTR(a.name, '[[:digit:]]+'), ''), 0) AS UNSIGNED),
			a.`{city_field}`, a.address_line2
		LIMIT %(start)s, %(page_len)s
		""",
		{"txt": search_txt, "start": start, "page_len": page_len},
	)

@frappe.whitelist()
def get_trip_summary(trip_name):
    """Returns key financial and operational fields for the Trip Summary dialog."""
    if not trip_name:
        return {}
    if not frappe.has_permission("Trip", "read", doc=trip_name):
        frappe.throw(_("Not permitted to view this Trip"), frappe.PermissionError)

    trip = frappe.get_doc("Trip", trip_name)
    fields = {
        "so_no":                      trip.so_no,
        "customer_freight":           trip.customer_freight,
        "total_additional_charges":   trip.total_additional_charges,
        "total_approved_addl_amount": trip.total_approved_addl_amount,
        "total_trip_amount":          trip.total_trip_amount,
        "total_vendor_freight":       trip.total_vendor_freight,
        "amount_to_be_paid_to_vendor": trip.amount_to_be_paid_to_vendor,
        "total_detention_days":       trip.total_detention_days,
        "total_detention_amount":     trip.total_detention_amount,
        "journey_time":               trip.journey_time,
        "journey_time_400_kmsday":    trip.journey_time_400_kmsday,
        "pod_status":                 trip.pod_status,
    }
    permitted = set(get_permitted_fields("Trip", user=frappe.session.user))
    return {k: v for k, v in fields.items() if k in permitted}

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_employee(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name, employee_name
        FROM `tabEmployee`
        WHERE status = 'Active'
        AND (name LIKE %(txt)s OR employee_name LIKE %(txt)s)
        ORDER BY LOWER(employee_name), LOWER(name)
        LIMIT %(start)s, %(page_len)s
    """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_driver(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name, full_name, cell_number
        FROM `tabDriver`
        WHERE status = 'Active'
        AND (full_name LIKE %(txt)s OR name LIKE %(txt)s OR cell_number LIKE %(txt)s)
        ORDER BY full_name
        LIMIT %(start)s, %(page_len)s
    """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_vehicle_by_vendor(doctype, txt, searchfield, start, page_len, filters):
    filters = frappe.parse_json(filters) if isinstance(filters, str) else filters
    vendor = filters.get("vendor") if filters else ""

    # A custom `query` makes search_widget return before it appends its own
    # `disabled != 1` filter (frappe/desk/search.py:126 vs :213-217), so this
    # dropdown has to exclude disabled Vehicles itself. search_employee and
    # search_driver above do the same thing via `status = 'Active'`.
    conditions = ["docstatus < 2", "disabled = 0"]

    if vendor:
        conditions.append("custom_vendor = %(vendor)s")   # ✅ correct now

    if txt:
        conditions.append("name LIKE %(txt)s")

    return frappe.db.sql(f"""
        SELECT name
        FROM `tabVehicle`
        WHERE {' AND '.join(conditions)}
        ORDER BY name
        LIMIT %(start)s, %(page_len)s
    """, {
        "vendor": vendor,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_address(doctype, txt, searchfield, start, page_len, filters):
    search_txt = f"%{txt}%"
    filters = frappe.parse_json(filters) if isinstance(filters, str) else filters
    filters = filters or {}

    # Detect custom City Link fieldname
    city_field = "city"
    try:
        for f in frappe.get_meta("Address").fields:
            if f.fieldtype == "Link" and f.options == "City":
                city_field = f.fieldname
                break
    except Exception:
        pass

    # is_primary_address = Origin checkbox
    # is_shipping_address = Destination checkbox
    if filters.get("is_origin"):
        type_condition = "AND a.is_primary_address = 1"
    elif filters.get("is_destination"):
        type_condition = "AND a.is_shipping_address = 1"
    else:
        type_condition = ""

    return frappe.db.sql(
        f"""
        SELECT
            a.name,
            NULLIF(TRIM(a.address_line1), '')        AS address_line1,
            NULLIF(TRIM(a.address_line2), '')        AS address_line2,
            NULLIF(TRIM(a.`{city_field}`), '')       AS city,
            NULLIF(TRIM(a.county), '')               AS county,
            COALESCE(
                NULLIF(TRIM(c.state), ''),
                NULLIF(TRIM(a.state), '')
            )                                        AS state,
            NULLIF(TRIM(a.custom_postal_code), '')   AS pincode
        FROM `tabAddress` a
        LEFT JOIN `tabCity` c ON c.name = a.`{city_field}`
        WHERE
            a.disabled = 0
            {type_condition}
            AND (
                a.name                      LIKE %(txt)s
                OR a.address_title          LIKE %(txt)s
                OR a.address_line1          LIKE %(txt)s
                OR a.address_line2          LIKE %(txt)s
                OR a.`{city_field}`         LIKE %(txt)s
                OR a.county                 LIKE %(txt)s
                OR a.state                  LIKE %(txt)s
                OR a.custom_postal_code     LIKE %(txt)s
            )
        ORDER BY
            CASE
                WHEN a.`{city_field}`       LIKE %(txt)s THEN 1
                WHEN a.address_line2        LIKE %(txt)s THEN 2
                WHEN a.county               LIKE %(txt)s THEN 3
                WHEN a.custom_postal_code   LIKE %(txt)s THEN 4
                ELSE 5
            END,
            LOWER(REGEXP_REPLACE(a.name, '[[:digit:]]+', '')),
            CAST(IFNULL(NULLIF(REGEXP_SUBSTR(a.name, '[[:digit:]]+'), ''), 0) AS UNSIGNED),
            a.`{city_field}`, a.address_line2
        LIMIT %(start)s, %(page_len)s
        """,
        {"txt": search_txt, "start": start, "page_len": page_len},
    )
