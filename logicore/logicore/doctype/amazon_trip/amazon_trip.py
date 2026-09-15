# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, today, now_datetime, time_diff_in_hours, get_datetime
from datetime import datetime

# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════

def _hours_between(dt1, dt2):
    """Return absolute hours between two datetime values. Returns 0 if either is None."""
    if not dt1 or not dt2:
        return 0.0
    try:
        return abs(time_diff_in_hours(str(dt2), str(dt1)))
    except Exception:
        return 0.0


def _detention_days(total_hours, free_hours=24):
    """
    First 24 hrs free, then every 24 hrs = 1 detention day.
    Fractional day after free period still counts as 1 day.
    """
    if total_hours <= free_hours:
        return 0
    excess = total_hours - free_hours
    return int(excess // 24) + (1 if excess % 24 > 0 else 0)


# ══════════════════════════════════════════════════════════════════
#  DOCUMENT CLASS
# ══════════════════════════════════════════════════════════════════

class AmazonTrip(Document):

    def autoname(self):
        from frappe.model.naming import make_autoname
        from frappe.utils import getdate, today
        d = getdate(today())
        fy_start = d.year if d.month >= 4 else d.year - 1
        fy_short = f"{str(fy_start)[-2:]}-{str(fy_start + 1)[-2:]}"  # e.g. "25-26"
        self.name = make_autoname(f"AT-{fy_short}-.#####")

    def validate(self):
        self._validate_unique_tour_id()
        self._validate_unique_vr_ids()
        self._validate_km()

    def before_save(self):
        self._calc_trip_cost()
        self._calc_total_vendor_freight()
        self._calc_computed_amounts()
        self._calc_freight_difference()
        self._calc_total_km()
        # self._calc_trip_status()  # Disabled — user sets trip_status manually

    # ── Tour ID Uniqueness (global, across all Amazon Trips) ──────

    def _validate_unique_tour_id(self):
        """tour_id_relay must be unique — one Tour ID can map to only one Amazon Trip."""
        tour_id = (self.tour_id_relay or "").strip()
        if not tour_id:
            return
        existing = frappe.db.get_value(
            "Amazon Trip",
            {"tour_id_relay": tour_id, "name": ["!=", self.name or "__new__"]},
            "name",
        )
        if existing:
            frappe.throw(
                f"Tour ID <b>{frappe.utils.escape_html(tour_id)}</b> is already used by "
                f"Amazon Trip <b>{frappe.utils.escape_html(existing)}</b>. "
                "Each Tour ID must be unique across all Amazon Trips.",
                title="Duplicate Tour ID",
            )

    # ── VR ID Uniqueness (global, across all Amazon Trips) ─────────

    def _validate_unique_vr_ids(self):
        """A VR ID must be globally unique — it can appear only once across
        every Amazon Trip's payment-data grid. Checks both duplicates within
        this document and clashes with any OTHER Amazon Trip.
        """
        rows = self.get("amazon_trip_details") or []

        # 1) Duplicates within this same document
        seen = {}
        for row in rows:
            vr = (row.vr_id or "").strip()
            if not vr:
                continue
            if vr in seen:
                frappe.throw(
                    f"VR ID <b>{frappe.utils.escape_html(vr)}</b> is entered more than once "
                    f"in this trip (rows {seen[vr]} and {row.idx}). Each VR ID must be unique.",
                    title="Duplicate VR ID",
                )
            seen[vr] = row.idx

        if not seen:
            return

        # 2) Clash with any OTHER Amazon Trip (different parent)
        clashes = frappe.db.sql(
            """
            SELECT d.vr_id, d.parent
            FROM `tabAmazon Trip Detail` d
            WHERE d.vr_id IN %(vr_ids)s
              AND d.parenttype = 'Amazon Trip'
              AND d.parent != %(self_name)s
            """,
            {"vr_ids": tuple(seen.keys()), "self_name": self.name or "__new__"},
            as_dict=True,
        )
        if clashes:
            msgs = [
                f"VR ID <b>{frappe.utils.escape_html(c.vr_id)}</b> already exists in Amazon Trip "
                f"<b>{frappe.utils.escape_html(c.parent)}</b>."
                for c in clashes
            ]
            frappe.throw(
                "<br>".join(msgs) + "<br><br>A VR ID can belong to only one Amazon Trip.",
                title="VR ID Already Used",
            )

    # ── Scheduled Trip KM ────────────────────────────────────────────

    def _validate_km(self):
        start = flt(self.start_km)
        end = flt(self.end_km)
        if start and end and end < start:
            frappe.throw(
                f"End KM (<b>{end}</b>) cannot be less than Start KM (<b>{start}</b>).",
                title="KM Validation Error",
            )

    def _calc_total_km(self):
        self.total_km = flt(self.end_km or 0) - flt(self.start_km or 0)

    def before_submit(self):
        self._calc_trip_cost()
        self._calc_total_vendor_freight()
        self._calc_computed_amounts()
        self._calc_freight_difference()
        self._calc_total_km()
        # self._calc_trip_status()  # Disabled — user sets trip_status manually

    # ── Total Trip Amount ──────────────────────────────────────────

    def _calc_trip_cost(self):
        self.trip_cost = (
            flt(self.freight or 0)
            + flt(self.fuel_surcharge_manual or 0)
            + flt(self.cancellation_charge_manual or 0)
            + flt(self.detention_charge_manual or 0)
            + flt(self.ot_cost_manual or 0)
            + flt(self.extra_distance_cost_manual or 0)
            + flt(self.toll_parking_charges_manual or 0)
        )

    # ── Computed Amounts ───────────────────────────────────────────

    def _calc_computed_amounts(self):
        """computed_total_freight = Total Trip Amount (trip_cost).
        computed_billed_amount = first non-zero child row value (Amazon repeats
        the tour-level billed amount on every VR row — do not sum).
        Push computed_total_freight to every child row.
        """
        self.computed_total_freight = flt(self.trip_cost or 0)
        rows = self.get("amazon_trip_details") or []
        self.computed_billed_amount = next(
            (flt(r.computed_billed_amount) for r in rows if flt(r.computed_billed_amount or 0)),
            0.0,
        )
        for row in rows:
            row.computed_total_freight = self.computed_total_freight

    # ── Freight Difference (Computed Billed - Computed Total) ──────

    def _calc_freight_difference(self):
        self.freight_difference = (
            flt(self.computed_billed_amount or 0)
            - flt(self.computed_total_freight or 0)
        )
        # Push same freight_difference to every child row
        for row in (self.get("amazon_trip_details") or []):
            row.freight_difference = self.freight_difference

    # ── Vendor Freight ─────────────────────────────────────────────

    def _calc_total_vendor_freight(self):
        self.total_vendor_freight = (
            flt(self.vendor_freight or 0)
            + flt(self.vendor_freight_extra or 0)
        )

    # ── Trip Status ────────────────────────────────────────────────

    def _calc_trip_status(self):
        """Auto-compute trip_status using only Amazon Trip fields."""
        if self.trip_status == "Cancelled":
            return

        if self.vr_cancellation_date_time_utc:
            self.trip_status = "Cancelled"
        elif self.original_sadashiv_bill_no:
            self.trip_status = "Billed"
        elif self.end_date:
            self.trip_status = "Delivered"
        elif self.start_date:
            self.trip_status = "In Transit"
        else:
            self.trip_status = "Open"


# ══════════════════════════════════════════════════════════════════
#  WHITELISTED APIs (called from amazon_trip.js)
# ══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_default_trip_coordinator():
    """
    Return the Employee linked to the logged-in user, for use as the default
    Trip Coordinator on a new Amazon Trip. Only an Active employee is
    returned (Administrator or an Inactive/Left employee -> blank).
    """
    user = frappe.session.user
    if user == "Administrator":
        return None

    return frappe.db.get_value(
        "Employee",
        {"user_id": user, "status": "Active"},
        "name",
    )


@frappe.whitelist()
def get_trip_status_preview(
    vr_cancellation_date_time_utc=None,
    original_sadashiv_bill_no=None,
    start_date=None,
    end_date=None,
    current_status=None,
):
    """Return what trip_status should be — used for live client preview."""
    if current_status == "Cancelled":
        return "Cancelled"
    if vr_cancellation_date_time_utc:
        return "Cancelled"
    if original_sadashiv_bill_no:
        return "Billed"
    if end_date:
        return "Delivered"
    if start_date:
        return "In Transit"
    return "Open"


@frappe.whitelist()
def check_tour_id_unique(tour_id_relay, current_name=None):
    """Return {exists, trip} — used by client-side live validation."""
    tour_id = (tour_id_relay or "").strip()
    if not tour_id:
        return {"exists": False}
    filters = {"tour_id_relay": tour_id}
    if current_name:
        filters["name"] = ["!=", current_name]
    existing = frappe.db.get_value("Amazon Trip", filters, "name")
    if existing:
        return {"exists": True, "trip": existing}
    return {"exists": False}


@frappe.whitelist()
def bulk_update_status():
    """
    Re-compute trip_status for all non-submitted Amazon Trip records.
    Safe to run from a scheduled job or a List View button.
    """
    records = frappe.get_all("Amazon Trip", filters={"docstatus": 0}, pluck="name")
    updated = 0
    for name in records:
        try:
            doc = frappe.get_doc("Amazon Trip", name)
            old = doc.trip_status
            doc._calc_trip_status()
            if doc.trip_status != old:
                doc.save(ignore_permissions=True)
                updated += 1
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Amazon Trip bulk_update_status error: {name}")
    frappe.db.commit()
    return {"updated": updated, "total": len(records)}


@frappe.whitelist()
def get_vehicle_last_trip_end_km(vehicle_id=None, vehicle_id_market=None, trip_name=None):
    """Start KM auto-fill: return the End KM of the most recent Amazon Trip for
    this vehicle. vehicle_id (Link) and vehicle_id_market (free-text) are mutually
    exclusive on this doctype — whichever is passed is used for the lookup.
    Market values are matched after trimming/upper-casing so manual entry
    variations (spacing, case, copy-paste) still match.
    """
    if vehicle_id:
        filters = {"vehicle_id": vehicle_id, "end_km": [">", 0], "docstatus": ["!=", 2]}
        if trip_name:
            filters["name"] = ["!=", trip_name]
        result = frappe.db.get_all(
            "Amazon Trip", filters=filters, fields=["end_km"], order_by="creation desc", limit=1
        )
        return result[0].end_km if result else 0

    if vehicle_id_market:
        normalized = vehicle_id_market.strip().upper().replace(" ", "")
        if not normalized:
            return 0
        conditions = ["UPPER(REPLACE(vehicle_id_market, ' ', '')) = %(normalized)s", "end_km > 0", "docstatus != 2"]
        values = {"normalized": normalized}
        if trip_name:
            conditions.append("name != %(trip_name)s")
            values["trip_name"] = trip_name
        result = frappe.db.sql(
            f"""
            SELECT end_km FROM `tabAmazon Trip`
            WHERE {' AND '.join(conditions)}
            ORDER BY creation DESC
            LIMIT 1
            """,
            values,
            as_dict=True,
        )
        return result[0].end_km if result else 0

    return 0


@frappe.whitelist()
def get_default_vendor_for_vehicle(vehicle_id=None):
    """Return the given Vehicle's Company's default_supplier, or None if
    the vehicle has no company, or its company has no default_supplier."""
    if not vehicle_id:
        return None
    company = frappe.db.get_value("Vehicle", vehicle_id, "company")
    if not company:
        return None
    return frappe.db.get_value("Company", company, "default_supplier")
