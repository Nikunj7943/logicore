import json

import frappe
from frappe.utils import flt

from logicore.tms_list_settings import save_tms_listview_settings
from logicore.utils import whitebooks_api


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

TRIP_FIELDS = [
    "name", "tcntrip_date", "tcntrip_no", "lr_no", "lr_date",
    "indent_no", "indent_date", "so", "company", "branch",
    "customer", "vendor", "trip_type", "business_format",
    "origin_city", "origin_city_2", "destination_city_1", "destination_city_2",
    "origin_state", "destination_state",
    "vehicle_no", "driver", "driver_mobile",
    "types_of_good", "packages", "eway_bill_no", "customer_invoice_no",
    "customer_freight", "vendor_freight", "total_vendor_freight",
    "total_trip_amount", "trip_total_amount_billed",
    "total_detention_amount", "total_additional_charges",
    "trip_status", "pod_status", "date_pod_uploaded_on_erp",
    "start_km", "end_km", "total_km", "standard_km",
    "journey_time", "journey_time_400_kmsday",
    "remarks",
]


# ══════════════════════════════════════════════════════════════════════════════
#  READ — list
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_trips(
    from_date=None,
    to_date=None,
    customer=None,
    branch=None,
    trip_status=None,
    page=1,
    page_size=20,
):
    """Return a paginated list of Trip records.

    Query parameters (all optional):
        from_date   – filter tcntrip_date >= from_date
        to_date     – filter tcntrip_date <= to_date
        customer    – exact match on customer field
        branch      – exact match on branch field
        trip_status – exact match on trip_status field
        page        – 1-based page number (default 1)
        page_size   – records per page, max 100 (default 20)
    """
    page      = int(page)
    page_size = int(page_size)

    if page < 1:
        frappe.throw("page must be >= 1")
    if page_size < 1:
        frappe.throw("page_size must be >= 1")
    if page_size > 100:
        frappe.throw("page_size cannot exceed 100")

    filters = []

    if from_date:
        filters.append(["Trip", "tcntrip_date", ">=", from_date])
    if to_date:
        filters.append(["Trip", "tcntrip_date", "<=", to_date])
    if customer:
        filters.append(["Trip", "customer", "=", customer])
    if branch:
        filters.append(["Trip", "branch", "=", branch])
    if trip_status:
        filters.append(["Trip", "trip_status", "=", trip_status])

    data = frappe.db.get_all(
        "Trip",
        filters=filters,
        fields=TRIP_FIELDS,
        limit_start=(page - 1) * page_size,
        limit_page_length=page_size,
        order_by="tcntrip_date desc",
    )

    total = frappe.db.count("Trip", filters=filters)

    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  READ — single
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_trip(trip_name):
    """Return a single Trip record by name.

    Raises frappe.DoesNotExistError automatically if trip_name is not found.
    Frappe's get_doc enforces read permission for the calling user.
    """
    if not trip_name:
        frappe.throw("trip_name is required")

    doc = frappe.get_doc("Trip", trip_name)
    doc_dict = doc.as_dict()

    return {field: doc_dict.get(field) for field in TRIP_FIELDS}


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def create_trip(data):
    """Create a new Trip record.

    Args:
        data: JSON string (or dict) containing field values for the new Trip.

    Returns:
        {"name": <new trip name>, "message": "Trip created successfully"}
    """
    if isinstance(data, str):
        data = json.loads(data)

    trip_data = {"doctype": "Trip"}
    trip_data.update(data)

    doc = frappe.get_doc(trip_data)
    doc.insert()

    return {"name": doc.name, "message": "Trip created successfully"}


# ══════════════════════════════════════════════════════════════════════════════
#  UPDATE
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def update_trip(trip_name, data):
    """Update an existing Trip record.

    Args:
        trip_name: Name (primary key) of the Trip to update.
        data:      JSON string (or dict) of field names and their new values.
                   Keys "doctype" and "name" are ignored.

    Returns:
        {"name": <trip name>, "message": "Trip updated successfully"}
    """
    if not trip_name:
        frappe.throw("trip_name is required")
    if not data:
        frappe.throw("data is required")

    if isinstance(data, str):
        data = json.loads(data)

    doc = frappe.get_doc("Trip", trip_name)

    for fieldname, value in data.items():
        if fieldname in ("doctype", "name"):
            continue
        setattr(doc, fieldname, value)

    doc.save()

    return {"name": doc.name, "message": "Trip updated successfully"}


# ══════════════════════════════════════════════════════════════════════════════
#  DELETE
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def delete_trip(trip_name):
    """Delete a Trip record.

    Uses force=True to allow deletion of submitted documents when the calling
    user has the appropriate permission (System Manager or Delete permission).

    Returns:
        {"message": "Trip <name> deleted successfully"}
    """
    if not trip_name:
        frappe.throw("trip_name is required")

    frappe.delete_doc("Trip", trip_name, force=True)

    return {"message": f"Trip {trip_name} deleted successfully"}


@frappe.whitelist()
def save_tms_listview_settings_api(doctype, listview_settings, removed_listview_fields):
    return save_tms_listview_settings(doctype, listview_settings, removed_listview_fields)


# ══════════════════════════════════════════════════════════════════════════════
#  FLEET DASHBOARD — vehicle aggregation helpers
# ══════════════════════════════════════════════════════════════════════════════

# Trip Type tab key (as sent by the Trip Operations widget) -> Trip Type master name
TRIP_OPERATIONS_TYPE_MAP = {
    "primary": "PRIMARY",
    "secondary_market": "SECONDARY MARKET",
    "secondary_dedicated": "SECONDARY DEDICATED",
    "other": "OTHER",
}


def _trip_operations_card_conditions(trip_type_value):
    """Return {card_key: [extra SQL conditions]} for the given Trip Type master name.

    Shared by get_trip_operations_summary (COUNT) and get_trip_operations_records
    (exact matching Trip names) so the click-through list always matches the badge.
    """
    not_cancelled = "(trip_status IS NULL OR trip_status != 'Cancel')"

    if trip_type_value == "PRIMARY":
        return {
            # Pending POD — arrival recorded but POD not uploaded (or blank), trip not Cancelled
            "pending_pod": [
                "arrival_date_time IS NOT NULL",
                "arrival_date_time != ''",
                "(pod_status = 'POD Not Uploaded' OR pod_status IS NULL OR pod_status = '')",
                not_cancelled,
            ],
            # Pending LR No — lr_no blank, trip not Cancelled
            "pending_lr_no": [
                "(lr_no IS NULL OR lr_no = '')",
                not_cancelled,
            ],
            # Pending Dispatch — lr_no set, reach recorded, dispatch not recorded, trip not Cancelled
            "pending_dispatch": [
                "lr_no IS NOT NULL",
                "lr_no != ''",
                "reach_date_time IS NOT NULL",
                "reach_date_time != ''",
                "(dispatch_date_time IS NULL OR dispatch_date_time = '')",
                not_cancelled,
            ],
            # Pending Arrival — lr_no set, dispatch recorded, arrival not recorded, trip not Cancelled
            "pending_arrival": [
                "lr_no IS NOT NULL",
                "lr_no != ''",
                "dispatch_date_time IS NOT NULL",
                "dispatch_date_time != ''",
                "(arrival_date_time IS NULL OR arrival_date_time = '')",
                not_cancelled,
            ],
            # Pending Customer Freight — LR No filled but customer_freight still 0/blank
            # and Bill No still blank, trip not Cancelled
            "pending_customer_freight": [
                "lr_no IS NOT NULL",
                "lr_no != ''",
                "(customer_freight IS NULL OR customer_freight = 0)",
                "(bill_nodate IS NULL OR bill_nodate = '')",
                not_cancelled,
            ],
            # Pending Vendor Freight — total_vendor_freight is 0/blank, trip not Cancelled
            "pending_vendor_freight": [
                "lr_no IS NOT NULL",
                "lr_no != ''",
                "(total_vendor_freight IS NULL OR total_vendor_freight = 0)",
                "(vendor IS NULL OR vendor != 'SADASHIV LOGISTICS PVT LTD')",
                not_cancelled,
            ],
            # Trip No To Be Provided — trip_no_not_yet_provided = 1, trip not Cancelled
            "trip_no_pending": [
                "trip_no_not_yet_provided = 1",
                "lr_no IS NOT NULL",
                "lr_no != ''",
                "(tcntrip_no IS NULL OR tcntrip_no = '' OR UPPER(tcntrip_no) = 'NA')",
                not_cancelled,
            ],
            # Trip To Be Billed — release recorded, Bill No & Bill Date both blank, trip not Cancelled
            "trip_to_be_billed": [
                "release_date_time IS NOT NULL",
                "release_date_time != ''",
                "lr_no IS NOT NULL",
                "lr_no != ''",
                "(bill_nodate IS NULL OR bill_nodate = '')",
                "(bill_date IS NULL OR bill_date = '')",
                not_cancelled,
            ],
            # Trip Payment Awaited — release recorded, Bill No & Bill Date set, Date Bill Credited blank, trip not Cancelled
            "trip_payment_awaited": [
                "release_date_time IS NOT NULL",
                "release_date_time != ''",
                "lr_no IS NOT NULL",
                "lr_no != ''",
                "bill_nodate IS NOT NULL",
                "bill_nodate != ''",
                "bill_date IS NOT NULL",
                "bill_date != ''",
                "(date_bill_credited IS NULL OR date_bill_credited = '')",
                not_cancelled,
            ],
            # Original POD Awaited — Uploaded Original/Duplicate Pod = "Duplicate" and Pod Status = "Duplicate POD Uploaded", trip not Cancelled
            "original_pod_awaited": [
                "uploaded_pod_originalduplicate = 'Duplicate'",
                "pod_status = 'Duplicate POD Uploaded'",
                not_cancelled,
            ],
        }

    if trip_type_value == "OTHER":
        # Net Receivable = Trip Total Freight minus Brokerage Amount and Broker LR Money
        # (matches the "Net Receivable" figure shown on the Trip's Customer Receipts summary).
        net_receivable = "(COALESCE(total_trip_amount, 0) - COALESCE(brokerage_amount, 0) - COALESCE(lr_money, 0))"
        no_receipt_rows = "NOT EXISTS (SELECT 1 FROM `tabCustomer Receipt Trip` crt WHERE crt.trip = tabTrip.name)"
        has_receipt_rows = "EXISTS (SELECT 1 FROM `tabCustomer Receipt Trip` crt WHERE crt.trip = tabTrip.name)"
        received_short_of_net_receivable = (
            "(SELECT COALESCE(SUM(crt2.received_amount), 0) FROM `tabCustomer Receipt Trip` crt2 "
            f"WHERE crt2.trip = tabTrip.name) < {net_receivable}"
        )
        return {
            # Arrival/Dispatch Columns Blank — any of the four milestone datetimes is blank, trip not Cancelled
            "arrival_dispatch_blank": [
                "("
                "(reach_date_time IS NULL OR reach_date_time = '') OR "
                "(dispatch_date_time IS NULL OR dispatch_date_time = '') OR "
                "(arrival_date_time IS NULL OR arrival_date_time = '') OR "
                "(release_date_time IS NULL OR release_date_time = '')"
                ")",
                not_cancelled,
            ],
            # Original POD Awaited — same definition as Primary's
            "original_pod_awaited": [
                "uploaded_pod_originalduplicate = 'Duplicate'",
                "pod_status = 'Duplicate POD Uploaded'",
                not_cancelled,
            ],
            # Pending POD — same definition as Primary's
            "pending_pod": [
                "arrival_date_time IS NOT NULL",
                "arrival_date_time != ''",
                "(pod_status = 'POD Not Uploaded' OR pod_status IS NULL OR pod_status = '')",
                not_cancelled,
            ],
            # Advance Amount Awaited — trip has a net receivable amount but no receipt recorded yet at all
            "advance_amount_awaited": [
                f"{net_receivable} != 0",
                no_receipt_rows,
                not_cancelled,
            ],
            # Balance Amount Awaited — some receipt recorded, but total received so far is short of net receivable
            "balance_amount_awaited": [
                f"{net_receivable} != 0",
                has_receipt_rows,
                received_short_of_net_receivable,
                not_cancelled,
            ],
            # Original POD Not Despatched — Original/Duplicate POD set & uploaded, but not yet sent to customer
            "original_pod_not_despatched": [
                "uploaded_pod_originalduplicate IS NOT NULL",
                "uploaded_pod_originalduplicate != ''",
                "pod_status IN ('Original POD Uploaded', 'Duplicate POD Uploaded')",
                "(date_pod_sent_to_customer IS NULL OR date_pod_sent_to_customer = '')",
                not_cancelled,
            ],
        }

    if trip_type_value == "SECONDARY DEDICATED":
        return {
            # Pending POD — same definition as Primary's (arrival recorded but POD not uploaded)
            "pending_pod": [
                "arrival_date_time IS NOT NULL",
                "arrival_date_time != ''",
                "(pod_status = 'POD Not Uploaded' OR pod_status IS NULL OR pod_status = '')",
                not_cancelled,
            ],
            # Start KM and End KM Not Filled — both Start Km and End Km blank, trip not Cancelled
            "start_end_km_not_filled": [
                "(start_km IS NULL OR start_km = 0)",
                "(end_km IS NULL OR end_km = 0)",
                not_cancelled,
            ],
            # Standard KM Not Filled — Standard Km blank, trip not Cancelled
            "standard_km_not_filled": [
                "(standard_km IS NULL OR standard_km = '')",
                not_cancelled,
            ],
        }

    if trip_type_value == "SECONDARY MARKET":
        return {
            # Pending POD — same definition as Primary's
            "pending_pod": [
                "arrival_date_time IS NOT NULL",
                "arrival_date_time != ''",
                "(pod_status = 'POD Not Uploaded' OR pod_status IS NULL OR pod_status = '')",
                not_cancelled,
            ],
        }

    return {}


def _trip_operations_common_args(company, branch, from_date, to_date, trip_type):
    """Validate shared Trip Operations args and build the base (trip_type/company/branch/date) SQL conditions."""
    from frappe.utils import cstr

    def _safe(val):
        if val is None:
            return None
        val = cstr(val).strip()
        return val if val else None

    company   = _safe(company)
    branch    = _safe(branch)
    from_date = _safe(from_date)
    to_date   = _safe(to_date)
    trip_type = _safe(trip_type)

    if from_date:
        try:
            frappe.utils.getdate(from_date)
        except Exception:
            frappe.throw("from_date must be a valid date (YYYY-MM-DD)")
    if to_date:
        try:
            frappe.utils.getdate(to_date)
        except Exception:
            frappe.throw("to_date must be a valid date (YYYY-MM-DD)")

    if company and not frappe.db.exists("Company", company):
        frappe.throw(f"Company '{frappe.utils.escape_html(company)}' does not exist")
    if branch and not frappe.db.exists("Branch", branch):
        frappe.throw(f"Branch '{frappe.utils.escape_html(branch)}' does not exist")

    trip_type_value = TRIP_OPERATIONS_TYPE_MAP.get(trip_type)
    if not trip_type_value:
        return None, []

    base_conditions = [f"trip_type = {frappe.db.escape(trip_type_value)}"]
    if company:
        base_conditions.append(f"company = {frappe.db.escape(company)}")
    if branch:
        base_conditions.append(f"branch = {frappe.db.escape(branch)}")
    if from_date:
        base_conditions.append(f"tcntrip_date >= {frappe.db.escape(from_date)}")
    if to_date:
        base_conditions.append(f"tcntrip_date <= {frappe.db.escape(to_date)}")

    return trip_type_value, base_conditions


@frappe.whitelist()
def get_trip_operations_summary(company=None, branch=None, from_date=None, to_date=None, trip_type=None):
    """Return Trip Operations card counts for the given trip_type tab.

    Optional filters (applied as AND conditions when provided and non-empty):
        company   – Trip.company exact match
        branch    – Trip.branch exact match
        from_date – Trip.tcntrip_date >= from_date
        to_date   – Trip.tcntrip_date <= to_date
        trip_type – one of "primary", "secondary_market", "secondary_dedicated", "other"

    Only "primary" and "other" have confirmed card logic today; other trip types
    return an empty dict (frontend shows 0 placeholders) until their logic is defined.
    """
    trip_type_value, base_conditions = _trip_operations_common_args(company, branch, from_date, to_date, trip_type)
    if not trip_type_value:
        return {}

    conditions_map = _trip_operations_card_conditions(trip_type_value)

    result = {}
    for card_key, extra_conditions in conditions_map.items():
        where_clause = " AND ".join(base_conditions + extra_conditions)
        row = frappe.db.sql(f"SELECT COUNT(*) AS cnt FROM `tabTrip` WHERE {where_clause}", as_dict=True)
        result[card_key] = row[0].cnt if row else 0
    return result


@frappe.whitelist()
def get_trip_operations_records(card_key, company=None, branch=None, from_date=None, to_date=None, trip_type=None):
    """Return the exact list of Trip names matching one Trip Operations card.

    Used by the click-through on each card so the opened Trip list always shows
    exactly the same records the badge counted — including cards whose logic
    (OR-conditions, Customer Receipt Trip aggregation) can't be expressed as
    simple AND-ed list-view filters.
    """
    trip_type_value, base_conditions = _trip_operations_common_args(company, branch, from_date, to_date, trip_type)
    if not trip_type_value:
        return []

    conditions_map = _trip_operations_card_conditions(trip_type_value)
    extra_conditions = conditions_map.get(card_key)
    if extra_conditions is None:
        frappe.throw(f"Unknown Trip Operations card '{frappe.utils.escape_html(card_key)}'")

    where_clause = " AND ".join(base_conditions + extra_conditions)
    rows = frappe.db.sql(
        f"SELECT name FROM `tabTrip` WHERE {where_clause} ORDER BY tcntrip_date DESC",
        as_dict=True,
    )
    return [r.name for r in rows]


@frappe.whitelist()
def get_financial_summary(company=None, branch=None, from_date=None, to_date=None):
    """Return total vendor pending, customer received, and customer outstanding,
    filtered by company/branch/trip date range (tcntrip_date)."""
    # Previous behaviour (date filters intentionally ignored — all-time totals):
    # """Return all-time total vendor pending, customer received, and customer outstanding.
    # Date/company/branch filters are intentionally ignored — these are global totals."""
    from frappe.utils import cstr

    base = ["t.docstatus != 2"]
    if company:
        company = cstr(company).strip()
        if company:
            base.append(f"t.company = {frappe.db.escape(company)}")
    if branch:
        branch = cstr(branch).strip()
        if branch:
            base.append(f"t.branch = {frappe.db.escape(branch)}")
    if from_date:
        from_date = cstr(from_date).strip()
        if from_date:
            base.append(f"t.tcntrip_date >= {frappe.db.escape(from_date)}")
    if to_date:
        to_date = cstr(to_date).strip()
        if to_date:
            base.append(f"t.tcntrip_date <= {frappe.db.escape(to_date)}")
    where = " AND ".join(base)

    # Vendor Freight total
    total_vendor_freight = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(t.total_vendor_freight), 0)
        FROM `tabTrip` t
        WHERE {where} AND t.total_vendor_freight > 0
    """)[0][0])

    # Vendor Paid = sum of all submitted VP payments
    total_vendor_paid = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(vpt.payment_amount), 0)
        FROM `tabVendor Payment Trip` vpt
        JOIN `tabVendor Payment` vp ON vp.name = vpt.parent
        JOIN `tabTrip` t ON t.name = vpt.trip
        WHERE vp.docstatus = 1 AND {where}
    """)[0][0])

    # Vendor Pending = freight - paid (same logic as Vendor Pending block)
    total_vendor_pending = flt(total_vendor_freight - total_vendor_paid)

    # Restrict invoice/received/outstanding to "Other" trip type, matching the Trip Other block
    where_other = where + " AND LOWER(COALESCE(t.trip_type, '')) LIKE '%other%'"

    # Customer Received = sum of all submitted receipts (Other trips only)
    total_customer_received = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(crt.received_amount), 0)
        FROM `tabCustomer Receipt Trip` crt
        JOIN `tabReceipt` r ON r.name = crt.parent
        JOIN `tabTrip` t ON t.name = crt.trip
        WHERE r.docstatus = 1 AND {where_other}
    """)[0][0])

    # Total Invoice = net receive amount (gross invoice less brokerage/LR/TDS) for Other trips
    total_invoice = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(
            COALESCE(t.customer_freight, 0) + COALESCE(t.total_approved_addl_amount, 0)
            - COALESCE(t.tds_deducted_by_customer, 0)
            - CASE WHEN UPPER(COALESCE(t.trip_type, '')) = 'OTHER'
                THEN COALESCE(t.brokerage_amount, 0) + COALESCE(t.lr_money, 0)
                ELSE 0
              END
        ), 0)
        FROM `tabTrip` t
        WHERE {where_other}
            AND (COALESCE(t.customer_freight, 0) + COALESCE(t.total_approved_addl_amount, 0)) > 0
    """)[0][0])

    # Customer Outstanding = total invoice - already received
    total_customer_outstanding = flt(total_invoice - total_customer_received)

    return {
        "total_vendor_freight":       total_vendor_freight,
        "total_vendor_paid":          total_vendor_paid,
        "total_vendor_pending":       total_vendor_pending,
        "total_invoice":              total_invoice,
        "total_customer_received":    total_customer_received,
        "total_customer_outstanding": total_customer_outstanding,
    }


@frappe.whitelist()
def get_vendor_pending_summary(from_date=None, to_date=None, company=None, branch=None):
    """Return vendor-wise pending freight balances grouped by vendor."""
    conditions = ["t.docstatus != 2", "t.total_vendor_freight > 0"]
    if from_date:
        conditions.append("t.tcntrip_date >= %(from_date)s")
    if to_date:
        conditions.append("t.tcntrip_date <= %(to_date)s")
    if company:
        conditions.append("t.company = %(company)s")
    if branch:
        conditions.append("t.branch = %(branch)s")
    where = " AND ".join(conditions)
    rows = frappe.db.sql(
        f"""
        SELECT
            t.vendor AS vendor,
            COALESCE(s.supplier_type, 'Vendor') AS vendor_type,
            SUM(t.total_vendor_freight) AS total_freight,
            SUM(COALESCE(paid.paid_amount, 0)) AS paid_amount,
            SUM(t.total_vendor_freight) - SUM(COALESCE(paid.paid_amount, 0)) AS balance,
            MIN(t.tcntrip_date) AS oldest_trip_date
        FROM `tabTrip` t
        LEFT JOIN (
            SELECT vpt.trip, SUM(vpt.payment_amount) AS paid_amount
            FROM `tabVendor Payment Trip` vpt
            INNER JOIN `tabVendor Payment` vp ON vp.name = vpt.parent AND vp.docstatus = 1
            GROUP BY vpt.trip
        ) paid ON paid.trip = t.name
        LEFT JOIN `tabSupplier` s ON s.name = t.vendor
        WHERE {where}
        GROUP BY t.vendor
        HAVING balance > 0
        ORDER BY oldest_trip_date ASC
        """,
        {"from_date": from_date, "to_date": to_date, "company": company, "branch": branch},
        as_dict=True,
    )
    return rows


@frappe.whitelist()
def get_trip_other_summary(from_date=None, to_date=None, company=None, branch=None):
    """Return Trip rows whose trip type contains "other" in any casing."""
    from frappe.utils import cstr

    def _safe(val):
        if val is None:
            return None
        val = cstr(val).strip()
        return val if val else None

    company = _safe(company)
    branch = _safe(branch)
    from_date = _safe(from_date)
    to_date = _safe(to_date)

    if from_date:
        try:
            frappe.utils.getdate(from_date)
        except Exception:
            frappe.throw("from_date must be a valid date (YYYY-MM-DD)")
    if to_date:
        try:
            frappe.utils.getdate(to_date)
        except Exception:
            frappe.throw("to_date must be a valid date (YYYY-MM-DD)")

    if company and not frappe.db.exists("Company", company):
        frappe.throw(f"Company '{frappe.utils.escape_html(company)}' does not exist")
    if branch and not frappe.db.exists("Branch", branch):
        frappe.throw(f"Branch '{frappe.utils.escape_html(branch)}' does not exist")

    conditions = [
        "t.docstatus != 2",
        "LOWER(COALESCE(t.trip_type, '')) LIKE %(trip_type_like)s",
        "(COALESCE(t.total_trip_amount, 0) > 0 OR COALESCE(t.customer_freight, 0) > 0)",
    ]
    if from_date:
        conditions.append("t.tcntrip_date >= %(from_date)s")
    if to_date:
        conditions.append("t.tcntrip_date <= %(to_date)s")
    if company:
        conditions.append("t.company = %(company)s")
    if branch:
        conditions.append("t.branch = %(branch)s")

    where = " AND ".join(conditions)
    rows = frappe.db.sql(
        f"""
        SELECT
            t.name AS name,
            t.tcntrip_date AS trip_date,
            t.name AS trip_no,
            t.origin_city AS origin_city,
            t.destination_city_1 AS destination_city,
            t.lr_no AS lr_no,
            t.vehicle_no AS vehicle_no,
            COALESCE(t.customer_freight, 0) AS freight,
            COALESCE(t.total_approved_addl_amount, 0) AS approved_addl_amount,
            (COALESCE(t.customer_freight, 0) + COALESCE(t.total_approved_addl_amount, 0)) AS total_trip_amount,
            COALESCE(t.brokerage_amount, 0) AS brokerage_amount,
            COALESCE(t.lr_money, 0) AS broker_lr,
            COALESCE(t.tds_deducted_by_customer, 0) AS tds_amount,
            COALESCE((
                SELECT SUM(crt.received_amount)
                FROM `tabCustomer Receipt Trip` crt
                INNER JOIN `tabReceipt` r ON r.name = crt.parent
                WHERE crt.trip = t.name AND r.docstatus = 1
            ), 0) AS amount_received,
            (COALESCE(t.customer_freight, 0) + COALESCE(t.total_approved_addl_amount, 0)
                - COALESCE(t.brokerage_amount, 0)
                - COALESCE(t.lr_money, 0)
                - COALESCE(t.tds_deducted_by_customer, 0)
            ) AS net_receive_amount,
            (COALESCE(t.customer_freight, 0) + COALESCE(t.total_approved_addl_amount, 0)
                - COALESCE(t.brokerage_amount, 0)
                - COALESCE(t.lr_money, 0)
                - COALESCE(t.tds_deducted_by_customer, 0)
                - COALESCE((
                    SELECT SUM(crt.received_amount)
                    FROM `tabCustomer Receipt Trip` crt
                    INNER JOIN `tabReceipt` r ON r.name = crt.parent
                    WHERE crt.trip = t.name AND r.docstatus = 1
                ), 0)
            ) AS balance_amt
        FROM `tabTrip` t
        WHERE {where}
        ORDER BY t.tcntrip_date DESC, t.tcntrip_no DESC, t.name DESC
        """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "company": company,
            "branch": branch,
            "trip_type_like": "%other%",
        },
        as_dict=True,
    )
    return rows


@frappe.whitelist()
def get_trip_filter_options():
    """Return lists of active companies and branches for the filter bar."""
    companies = frappe.get_all(
        "Company",
        filters={"is_group": 0},
        fields=["name", "company_name"],
        order_by="company_name asc",
    )
    branches = frappe.get_all(
        "Branch",
        fields=["name", "branch"],
        order_by="branch asc",
    )
    return {
        "companies": [{"value": c.name, "label": c.company_name or c.name} for c in companies],
        "branches":  [{"value": b.name, "label": b.branch or b.name} for b in branches],
    }


@frappe.whitelist()
def get_fleet_vehicle_fuel():
    """Top 15 vehicles ranked by total fuel cost."""
    return frappe.db.sql(
        """
        SELECT
            vehicle,
            COUNT(*)                         AS fills,
            ROUND(SUM(liters), 1)            AS total_liters,
            ROUND(SUM(expense_amount), 0)    AS total_cost,
            ROUND(AVG(kpl), 2)               AS avg_kpl
        FROM `tabFuel Urea Expenses`
        WHERE vehicle IS NOT NULL AND vehicle != ''
        GROUP BY vehicle
        ORDER BY total_cost DESC
        LIMIT 15
        """,
        as_dict=True,
    )


@frappe.whitelist()
def get_fleet_vehicle_expenses():
    """Combined expense breakdown (fuel, repair, service, tyre) per vehicle."""
    from frappe.utils import flt

    fuel_rows = frappe.db.sql(
        """
        SELECT vehicle AS v, ROUND(SUM(expense_amount), 0) AS amt
        FROM `tabFuel Urea Expenses`
        WHERE vehicle IS NOT NULL AND vehicle != ''
        GROUP BY vehicle_no
        """,
        as_dict=True,
    )
    repair_rows = frappe.db.sql(
        """
        SELECT vehicle_id AS v, ROUND(SUM(amount), 0) AS amt
        FROM `tabRepair Expenses`
        WHERE vehicle_id IS NOT NULL AND vehicle_id != ''
        GROUP BY vehicle_id
        """,
        as_dict=True,
    )
    service_rows = frappe.db.sql(
        """
        SELECT vehicle_no AS v, ROUND(SUM(total_amount), 0) AS amt
        FROM `tabService Logs`
        WHERE vehicle_no IS NOT NULL AND vehicle_no != ''
        GROUP BY vehicle_no
        """,
        as_dict=True,
    )
    tyre_rows = frappe.db.sql(
        """
        SELECT vehicle_id AS v, ROUND(SUM(cost), 0) AS amt
        FROM `tabTyre Expenses`
        WHERE vehicle_id IS NOT NULL AND vehicle_id != ''
        GROUP BY vehicle_id
        """,
        as_dict=True,
    )

    summary = {}

    def add(rows, key):
        for row in rows:
            if not row.v:
                continue
            if row.v not in summary:
                summary[row.v] = {"vehicle": row.v, "fuel": 0.0, "repair": 0.0, "service": 0.0, "tyre": 0.0}
            summary[row.v][key] = flt(row.amt)

    add(fuel_rows, "fuel")
    add(repair_rows, "repair")
    add(service_rows, "service")
    add(tyre_rows, "tyre")

    result = list(summary.values())
    for r in result:
        r["total"] = r["fuel"] + r["repair"] + r["service"] + r["tyre"]

    result.sort(key=lambda x: x["total"], reverse=True)
    return result[:15]


# ══════════════════════════════════════════════════════════════════════════════
#  POD PDF COMPRESSION (Ghostscript)
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def enqueue_compress_pod_pdf(file_doc_name):
    """Enqueue PDF compression as background job — returns immediately."""
    frappe.enqueue(
        "logicore.logicore.api.compress_pod_pdf",
        file_doc_name=file_doc_name,
        queue="short",
        timeout=120,
    )
    return {"queued": True}


@frappe.whitelist()
def compress_pod_pdf(file_doc_name, original_name=None):
    import os
    import shutil
    import subprocess
    import tempfile

    # Target: reduce file BY 50-70% while keeping text/signatures clearly readable
    TARGET_MAX   = 0.50   # accept if compressed <= 50% of original
    MIN_DPI      = 80     # never go below this — readability floor for scanned PODs

    file_doc  = frappe.get_doc("File", file_doc_name)
    file_path = file_doc.get_full_path()

    if not os.path.exists(file_path):
        frappe.throw("File not found on disk.")

    original_size = os.path.getsize(file_path)

    def _save_meta(size):
        updates = {"file_size": size}
        if original_name:
            updates["file_name"] = original_name
        frappe.db.set_value("File", file_doc.name, updates)
        frappe.db.commit()

    gs_bin = shutil.which("gs") or "/usr/bin/gs"
    if not os.path.exists(gs_bin):
        frappe.log_error(f"Ghostscript not found at '{gs_bin}'", "POD Compress")
        _save_meta(original_size)
        return {"compressed": False, "original_size": original_size, "final_size": original_size, "error": "gs_missing"}

    def _gs(in_path, out_path, dpi):
        """Run Ghostscript with explicit DPI — never uses low-quality presets."""
        cmd = [
            gs_bin, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            # Image downsampling
            "-dDownsampleColorImages=true", f"-dColorImageResolution={dpi}",
            "-dDownsampleGrayImages=true",  f"-dGrayImageResolution={dpi}",
            "-dDownsampleMonoImages=true",  f"-dMonoImageResolution={dpi}",
            # JPEG compression at controlled quality (keeps text sharp)
            "-dAutoFilterColorImages=false", "-dColorImageFilter=/DCTEncode",
            "-dAutoFilterGrayImages=false",  "-dGrayImageFilter=/DCTEncode",
            f"-sOutputFile={out_path}", in_path,
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=90)
        return r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0

    tmp = tempfile.mkdtemp()
    try:
        # Pass 1: 100 DPI — good readability for scanned PODs, ~50-65% reduction
        p1 = os.path.join(tmp, "p1.pdf")
        p1_ok = _gs(file_path, p1, dpi=100)
        sz1 = os.path.getsize(p1) if p1_ok else original_size

        if p1_ok and sz1 <= original_size * TARGET_MAX:
            shutil.copy(p1, file_path)
            _save_meta(sz1)
            return {"compressed": True, "original_size": original_size, "final_size": sz1}

        # Pass 2: 80 DPI — readability floor, only when pass 1 not sufficient
        p2 = os.path.join(tmp, "p2.pdf")
        p2_ok = _gs(file_path, p2, dpi=MIN_DPI)
        sz2 = os.path.getsize(p2) if p2_ok else original_size

        candidates = [(sz, path) for ok, sz, path in [(p1_ok, sz1, p1), (p2_ok, sz2, p2)] if ok]
        if candidates:
            best_size, best_path = min(candidates)
            if best_size < original_size:
                shutil.copy(best_path, file_path)
                _save_meta(best_size)
                return {"compressed": True, "original_size": original_size, "final_size": best_size}

        _save_meta(original_size)
        return {"compressed": False, "original_size": original_size, "final_size": original_size}

    except subprocess.TimeoutExpired:
        frappe.log_error("Ghostscript timed out", "POD Compress")
        return {"compressed": False, "original_size": original_size, "final_size": original_size, "error": "timeout"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@frappe.whitelist()
def get_session_expiry():
    if frappe.session.user == "Guest":
        frappe.throw("Not logged in")
    expiry_str = frappe.db.get_single_value("System Settings", "session_expiry") or "170:00"
    parts = expiry_str.split(":")
    hours   = int(parts[0]) if len(parts) > 0 else 170
    minutes = int(parts[1]) if len(parts) > 1 else 0
    seconds = int(parts[2]) if len(parts) > 2 else 0
    return {"expiry_seconds": (hours * 3600) + (minutes * 60) + seconds}


# ══════════════════════════════════════════════════════════════════════════════
#  VEHICLE FINANCE ACTIVITY — home screen widget
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_vehicle_finance_activity_summary(from_date=None, to_date=None):
    """Return counts for Vehicle Finance Activity widgets.

    active_finance_vehicles — loans currently running (start_date <= today <= end_date).
    emi_in_period          — submitted Vehicle Finance EMI payments with date in from_date..to_date.
    emi_draft_payments     — auto-created EMI payments still in Draft with no reference_no.
    """
    from frappe.utils import cstr

    today = frappe.utils.today()

    def _safe_date(val):
        if not val:
            return None
        val = cstr(val).strip()
        if not val:
            return None
        try:
            frappe.utils.getdate(val)
            return val
        except Exception:
            return None

    from_date = _safe_date(from_date)
    to_date   = _safe_date(to_date)

    active_finance_vehicles = flt(frappe.db.sql("""
        SELECT COUNT(*) FROM `tabVehicle Finance`
        WHERE docstatus != 2
          AND start_date IS NOT NULL
          AND end_date IS NOT NULL
          AND start_date <= %(today)s
          AND end_date >= %(today)s
    """, {"today": today})[0][0])

    # Old logic — counted Vehicle Finance masters whose date_of_emi fell in the range.
    # date_of_emi is the EMI day-of-month on the loan master, not a transaction date,
    # so the card read 0 for every period except the one the master was set up in.
    # emi_conds = ["docstatus != 2", "date_of_emi IS NOT NULL"]
    # emi_vals  = {}
    # if from_date:
    #     emi_conds.append("date_of_emi >= %(from_date)s")
    #     emi_vals["from_date"] = from_date
    # if to_date:
    #     emi_conds.append("date_of_emi <= %(to_date)s")
    #     emi_vals["to_date"] = to_date
    #
    # emi_in_period = flt(frappe.db.sql(
    #     "SELECT COUNT(*) FROM `tabVehicle Finance` WHERE " + " AND ".join(emi_conds),
    #     emi_vals
    # )[0][0])

    # EMI Transferred — submitted EMI payments (Payment.on_submit sets docstatus=1, status=Paid)
    emi_conds = ["docstatus = 1", "type = 'Vehicle Finance EMI'", "status = 'Paid'"]
    emi_vals  = {}
    if from_date:
        emi_conds.append("date >= %(from_date)s")
        emi_vals["from_date"] = from_date
    if to_date:
        emi_conds.append("date <= %(to_date)s")
        emi_vals["to_date"] = to_date

    emi_in_period = flt(frappe.db.sql(
        "SELECT COUNT(*) FROM `tabPayment` WHERE " + " AND ".join(emi_conds),
        emi_vals
    )[0][0])

    # EMI Payment in Draft Mode — type=Vehicle Finance EMI, status=Draft, reference_no blank
    pay_conds = [
        "docstatus = 0",
        "type = 'Vehicle Finance EMI'",
        "status = 'Draft'",
        "(reference_no IS NULL OR reference_no = '')",
    ]
    pay_vals  = {}
    if from_date:
        pay_conds.append("date >= %(pay_from)s")
        pay_vals["pay_from"] = from_date
    if to_date:
        pay_conds.append("date <= %(pay_to)s")
        pay_vals["pay_to"] = to_date

    emi_draft_payments = flt(frappe.db.sql(
        "SELECT COUNT(*) FROM `tabPayment` WHERE " + " AND ".join(pay_conds),
        pay_vals
    )[0][0])

    return {
        "active_finance_vehicles": int(active_finance_vehicles),
        "emi_in_period":           int(emi_in_period),
        "emi_draft_payments":      int(emi_draft_payments),
    }


@frappe.whitelist()
def is_eway_bill_lookup_enabled(company=None):
    """Whether the Trip form should attempt an E-Way Bill lookup at all.

    With no Company picked yet the Trip form still needs an answer, so report
    whether any Company has the lookup switched on -- that decides whether nudging
    the user to pick a Company is helpful or just noise.
    """
    if company:
        return whitebooks_api.is_enabled(company)
    return bool(frappe.db.exists("Eway Bill Settings", {"enabled": 1}))


@frappe.whitelist()
def get_eway_bill_details(ewb_no, company):
    """Look up an e-way bill on Whitebooks and resolve its vehicle to a Vehicle record."""
    if not ewb_no:
        frappe.throw("E-Way Bill No is required.")
    if not company:
        frappe.throw("Please select a Company on this Trip before looking up the E-Way Bill.")

    # Lookup switched off (or not configured) for this Company — stay silent so the
    # user just fills Eway Bill Date, Expiry Date and Vehicle No by hand.
    if not whitebooks_api.is_enabled(company):
        return None

    result = whitebooks_api.get_e_waybill_details(ewb_no, company)
    vehicle_no_raw = result.pop("vehicle_no_raw")

    vehicle_name = None
    vehicle_not_found = None
    if vehicle_no_raw:
        vehicle_name = frappe.db.get_value("Vehicle", {"license_plate": vehicle_no_raw}, "name")
        if not vehicle_name:
            vehicle_not_found = vehicle_no_raw

    result["vehicle_no"] = vehicle_name
    result["vehicle_not_found"] = vehicle_not_found
    return result
