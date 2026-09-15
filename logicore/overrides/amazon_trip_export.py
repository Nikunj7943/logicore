import frappe

# Column order matches "Revised Amazon Format for New ERP - 22 Jun 2026.xlsx"
_AMAZON_TRIP_EXPORT_FIELDS = [
    ("company_name",               "Company Name"),
    ("customer",                   "Customer"),
    ("trip_type",                  "Trip Type"),
    ("branch",                     "Branch"),
    ("trip_coordinator",           "Trip Coordinator"),
    ("trip_date",                  "Trip Date"),
    ("tour_id_relay",              "Tour ID"),
    ("vr_id",                      "VR ID"),
    ("status",                     "Status"),
    ("facility_sequence",          "Facility Sequence"),
    ("cpt",                        "CPT"),
    ("is_cpt_truck",               "Is CPT Truck"),
    ("cr_id",                      "CR_ID"),
    ("shipper_accounts",           "Shipper Accounts"),
    ("equipment_type",             "Equipment Type"),
    ("estimated_cost",             "Estimated Cost"),
    ("tender_status",              "Tender Status"),
    ("driver_relay",               "Driver"),
    ("vehicle_id",                 "Vehicle ID"),
    ("vr_cancellation_date_time_utc", "VR Cancellation Date Time (UTC)"),
    ("transit_operator_type",      "Transit Operator Type"),
    ("spot_work",                  "Spot Work"),
    ("freight",                    "Customer Freight"),
    ("fuel_surcharge_manual",      "RLB Fuel Surcharge1"),
    ("cancellation_charge_manual", "RLB Cancellation Charge1"),
    ("detention_charge_manual",    "RLB Detention Charge1"),
    ("ot_cost_manual",             "RLB OT Cost1"),
    ("extra_distance_cost_manual", "RLB Extra Distance Cost1"),
    ("toll_parking_charges_manual","RLB Toll-Parking Charges1"),
    ("trip_cost",                  "Total Trip Amount"),
    ("vendor",                     "Vendor"),
    ("vendor_freight",             "Vendor Freight"),
    ("vendor_freight_extra",       "Vendor Freight (Extra)"),
    ("total_vendor_freight",       "Total Vendor Freight"),
    ("remarks_amazon",             "Remarks"),
    ("duplicate_trips",            "Duplicate Trips"),
    ("duplicate_record_no",        "Duplicate Record No"),
    ("manual_trip",                "Manual Trip"),
]

_AMAZON_DETAIL_EXPORT_FIELDS = [
    ("vr_id",                      "VR ID"),
    ("vr_status",                  "Status"),
    ("load_id",                    "Load ID"),
    ("vehicle_no",                 "Vehicle No."),
    ("start_date",                 "Start Date"),
    ("end_date",                   "End Date"),
    ("lane",                       "Lane"),
    ("city",                       "City"),
    ("operator_type_amazon",       "Operator Type"),
    ("total_distance",             "Total Distance"),
    ("contract_type",              "Contract Type"),
    ("rate_type",                  "Rate Type"),
    ("item_type",                  "Item Type"),
    ("work_type",                  "Work Type"),
    ("base_rate",                  "Base Rate"),
    ("fuel_surcharge_amazon",      "Fuel Surcharge"),
    ("cancellation_charge_amazon", "Cancellation Charge"),
    ("detention_charge_amazon",    "Detention Charge"),
    ("ot_cost_amazon",             "OT Cost"),
    ("extra_distance_cost_amazon", "Extra Distance Cost"),
    ("toll_parking_charges_amazon","Toll-Parking Charges"),
    ("tax_percent",                "Tax Percent"),
    ("gross_pay_amt_excl_tax",     "Gross Pay Amt (Excl. Tax)"),
    ("gross_tax_amt",              "Gross Tax Amt"),
    ("gross_pay_amt",              "Gross Pay Amt"),
    ("comments",                   "Comments"),
    ("extra_hours",                "Extra Hours"),
    ("extra_km",                   "Extra Km"),
    ("remarks3",                   "Remarks3"),
    ("original_sadashiv_bill_no",  "Bill No"),
    ("original_bill_date",         "Bill Date"),
    ("computed_total_freight",     "Computed Total Freight"),
    ("computed_billed_amount",     "Computed Billed Amount"),
    ("freight_difference",         "Freight Difference"),
    ("trip_status",                "Trip Status"),
]

# Check fields on Amazon Trip parent — stored as 0/1, export as No/Yes
_AMAZON_PARENT_CHECK_FIELDS = {"is_cpt_truck", "manual_trip", "spot_work"}

# Own-fleet parent field -> its free-text "Market" (non-fleet) counterpart. Both are
# selectable in the column picker, but the Market side never gets its own output
# column: whichever is selected (either, or both), the data always lands in the
# single fleet-named column, falling back to the Market value when the fleet
# value is empty.
_AMAZON_MARKET_FALLBACK = {
    "vehicle_id":   "vehicle_id_market",
    "driver_relay": "driver_market",
}
_AMAZON_MARKET_TO_FLEET = {v: k for k, v in _AMAZON_MARKET_FALLBACK.items()}

# Driver Mobile has no stored fleet-side field on Amazon Trip — the fleet number
# comes from Driver.cell_number via driver_relay. driver_mobile_market is both the
# selectable checkbox and the canonical merged column (no separate "(Market)" column).
_DRIVER_MOBILE_FIELD = "driver_mobile_market"
_DRIVER_MOBILE_LABEL = "Driver Mobile"


def _collapse_amazon_market_columns(db_fields, headers):
    """Rewrite any Market-side parent field to its fleet counterpart (or the
    canonical Driver Mobile label) and drop duplicates, so a pair is never
    exported as two columns."""
    meta = frappe.get_meta("Amazon Trip")
    out_fields, out_headers, seen = [], [], set()
    for fn, hd in zip(db_fields, headers):
        canon = _AMAZON_MARKET_TO_FLEET.get(fn, fn)
        if canon in seen:
            continue
        seen.add(canon)
        if canon == _DRIVER_MOBILE_FIELD:
            hd = _DRIVER_MOBILE_LABEL
        elif canon != fn:
            df = meta.get_field(canon)
            hd = df.label if df else hd
        out_fields.append(canon)
        out_headers.append(hd)
    return out_fields, out_headers


# Parent-section fields whose value must come from the current child row, not the parent.
# Key = fieldname as declared in parent section of the export dialog.
# Value = actual child fieldname to read from.
# "vr_id"  → child.vr_id   (parent.vr_id is usually empty; child has the real VR ID per row)
# "status" → child.vr_status (column header stays "Status"; data is child vr_status per row)
_AMAZON_PARENT_FROM_CHILD = {
    "vr_id":  "vr_id",
    "status": "vr_status",
}


def _fmt_val(v, fn=""):
    from datetime import date, datetime
    if fn in _AMAZON_PARENT_CHECK_FIELDS:
        return "Yes" if v else "No"
    if isinstance(v, datetime):
        return v.strftime("%d-%m-%Y %H:%M:%S")
    if isinstance(v, date):
        return v.strftime("%d-%m-%Y")
    return v


def _build_filters(filters):
    result = []

    if filters.get("names"):
        names = filters["names"]
        if isinstance(names, list) and names:
            result.append(["Amazon Trip", "name", "in", names])

    def _add(field, op, val):
        if val:
            result.append(["Amazon Trip", field, op, val])

    _add("company_name",           "=",  filters.get("company"))
    _add("branch",                 "=",  filters.get("branch"))
    _add("customer",               "=",  filters.get("customer"))
    _add("vendor",                 "=",  filters.get("vendor"))
    _add("amazon_business_format", "=",  filters.get("business_format"))
    _add("trip_type",              "=",  filters.get("trip_type"))
    _add("status",                 "=",  filters.get("status"))
    _add("trip_status",            "=",  filters.get("trip_status"))
    _add("trip_date",              ">=", filters.get("date_from"))
    _add("trip_date",              "<=", filters.get("date_to"))

    if filters.get("tour_id"):
        result.append(["Amazon Trip", "tour_id_relay", "like", f"%{filters['tour_id']}%"])

    return result


@frappe.whitelist()
def export_amazon_trips_filtered(filters=None, selected_fields=None):
    """
    Called via form POST from the Amazon Trip list Export dialog.
    Exports parent Amazon Trip fields + flattened Amazon Trip Detail child rows.
    Each child detail row produces one CSV row; parent fields are repeated.
    If no child rows exist, a single row is exported with empty child columns.
    """
    import csv
    import io as _io
    import json

    if isinstance(filters, str):
        filters = json.loads(filters)
    filters = filters or {}

    if isinstance(selected_fields, str):
        selected_fields = json.loads(selected_fields)
    selected_fields = selected_fields or {}

    frappe_filters = _build_filters(filters)

    # ── Determine parent columns ─────────────────────────────────────────────
    parent_fields_selected = selected_fields.get("Amazon Trip", [])
    if parent_fields_selected:
        parent_db_fields = list(parent_fields_selected)
        meta = frappe.get_meta("Amazon Trip")
        def _parent_label(fn):
            if fn == "name":
                return "Amazon Trip No"
            df = meta.get_field(fn)
            return df.label if df else fn
        parent_headers = [_parent_label(fn) for fn in parent_db_fields]
    else:
        parent_db_fields = [f[0] for f in _AMAZON_TRIP_EXPORT_FIELDS]
        parent_headers   = [f[1] for f in _AMAZON_TRIP_EXPORT_FIELDS]

    # Vehicle ID/Driver always export as one column, never split into a
    # separate "(Market)" column even if that checkbox was selected.
    parent_db_fields, parent_headers = _collapse_amazon_market_columns(parent_db_fields, parent_headers)

    # ── Determine child columns ──────────────────────────────────────────────
    detail_fields_selected = selected_fields.get("Amazon Trip Detail", [])
    if detail_fields_selected:
        detail_db_fields = list(detail_fields_selected)
        meta_detail = frappe.get_meta("Amazon Trip Detail")
        def _detail_label(fn):
            df = meta_detail.get_field(fn)
            return df.label if df else fn
        detail_headers = [_detail_label(fn) for fn in detail_db_fields]
    else:
        detail_db_fields = [f[0] for f in _AMAZON_DETAIL_EXPORT_FIELDS]
        detail_headers   = [f[1] for f in _AMAZON_DETAIL_EXPORT_FIELDS]

    # ── Query parent records ─────────────────────────────────────────────────
    # Always include `name` for child lookup.
    # Exclude virtual "parent-from-child" fields from the parent query — their
    # values come from each child row, not the parent record.
    parent_query_fields = [f for f in parent_db_fields if f not in _AMAZON_PARENT_FROM_CHILD]
    if "name" not in parent_query_fields:
        parent_query_fields.append("name")

    # Also fetch each Market fallback field alongside its own-fleet counterpart, and
    # driver_relay whenever Driver Mobile is wanted (needed to look up Driver.cell_number).
    for fn in parent_db_fields:
        market_fn = _AMAZON_MARKET_FALLBACK.get(fn)
        if market_fn and market_fn not in parent_query_fields:
            parent_query_fields.append(market_fn)
    if _DRIVER_MOBILE_FIELD in parent_db_fields and "driver_relay" not in parent_query_fields:
        parent_query_fields.append("driver_relay")

    trips = frappe.db.get_all(
        "Amazon Trip",
        filters=frappe_filters or {},
        fields=parent_query_fields,
        order_by="trip_date desc, name desc",
        limit_page_length=0,
    )

    # ── Resolve Link fields that store IDs instead of display names ──────────
    # trip_coordinator → Employee.employee_name
    if "trip_coordinator" in parent_db_fields:
        emp_ids = list({t.get("trip_coordinator") for t in trips if t.get("trip_coordinator")})
        if emp_ids:
            _emp_map = {
                r.name: r.employee_name
                for r in frappe.db.get_all(
                    "Employee",
                    filters=[["name", "in", emp_ids]],
                    fields=["name", "employee_name"],
                )
            }
            for trip in trips:
                tc = trip.get("trip_coordinator")
                if tc:
                    trip["trip_coordinator"] = _emp_map.get(tc, tc)

    # driver_relay → Driver.full_name / Driver.cell_number. Resolved into separate
    # keys (not overwriting driver_relay) so the Market-fallback check below can
    # still tell an empty fleet driver apart from a resolved name/number.
    if "driver_relay" in parent_query_fields:
        driver_ids = list({t.get("driver_relay") for t in trips if t.get("driver_relay")})
        if driver_ids:
            _driver_map = {
                r.name: r
                for r in frappe.db.get_all(
                    "Driver",
                    filters=[["name", "in", driver_ids]],
                    fields=["name", "full_name", "cell_number"],
                )
            }
            for trip in trips:
                dr = trip.get("driver_relay")
                info = _driver_map.get(dr) if dr else None
                trip["_driver_full_name"]   = info.full_name if info else None
                trip["_driver_cell_number"] = info.cell_number if info else None

    # ── Build CSV (flatten parent + child) ───────────────────────────────────
    headers = parent_headers + detail_headers
    rows = [headers]

    # Child query needs the "parent-from-child" source fields even if not in detail_db_fields
    child_query_fields = list(detail_db_fields)
    for child_fn in _AMAZON_PARENT_FROM_CHILD.values():
        if child_fn not in child_query_fields:
            child_query_fields.append(child_fn)

    def _amazon_market_value(trip, fn):
        if fn == "driver_relay":
            return trip.get("_driver_full_name") or trip.get("driver_relay") or trip.get("driver_market")
        if fn == _DRIVER_MOBILE_FIELD:
            return trip.get("_driver_cell_number") or trip.get(_DRIVER_MOBILE_FIELD)
        market_fn = _AMAZON_MARKET_FALLBACK.get(fn)
        if market_fn:
            return trip.get(fn) or trip.get(market_fn)
        return trip.get(fn)

    for trip in trips:
        # Build the static part of parent_row (fields that don't come from child)
        static_parent = {}
        for fn in parent_db_fields:
            if fn in _AMAZON_PARENT_FROM_CHILD:
                continue  # filled per child row below
            v = _amazon_market_value(trip, fn)
            if fn in _AMAZON_PARENT_CHECK_FIELDS:
                static_parent[fn] = "Yes" if v else "No"
            elif v is not None:
                static_parent[fn] = str(_fmt_val(v, fn))
            else:
                static_parent[fn] = ""

        details = frappe.db.get_all(
            "Amazon Trip Detail",
            filters={"parent": trip.get("name"), "parenttype": "Amazon Trip"},
            fields=child_query_fields,
            order_by="idx asc",
            limit_page_length=0,
        )

        def _build_parent_row(detail):
            row = []
            for fn in parent_db_fields:
                if fn in _AMAZON_PARENT_FROM_CHILD:
                    # Take value from current child row
                    child_fn = _AMAZON_PARENT_FROM_CHILD[fn]
                    v = detail.get(child_fn) if detail else None
                    row.append(str(_fmt_val(v, child_fn)) if v is not None else "")
                else:
                    row.append(static_parent[fn])
            return row

        def _build_detail_row(detail):
            return [
                str(_fmt_val(detail.get(fn), fn)) if detail.get(fn) is not None else ""
                for fn in detail_db_fields
            ]

        if details:
            for detail in details:
                rows.append(_build_parent_row(detail) + _build_detail_row(detail))
        else:
            rows.append(_build_parent_row(None) + [""] * len(detail_db_fields))

    buf = _io.StringIO()
    csv.writer(buf).writerows(rows)

    ts = frappe.utils.now_datetime().strftime("%d-%m-%Y %H%M")
    frappe.response["filename"]    = f"Amazon Trip Export - {ts}.csv"
    frappe.response["filecontent"] = buf.getvalue().encode("utf-8-sig")
    frappe.response["type"]        = "binary"
