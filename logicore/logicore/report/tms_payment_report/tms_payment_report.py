import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    ptype = (filters.get("type") or "").strip()
    if ptype == "Fuel Incentive":
        columns = get_fuel_incentive_columns()
        data    = get_fuel_incentive_data(filters)
        summary = get_fuel_incentive_summary(data)
        return columns, data, None, None, summary
    if ptype == "Vendor Payment":
        columns = get_vendor_payment_columns()
        data    = get_vendor_payment_data(filters)
        summary = get_summary(data)
        return columns, data, None, None, summary
    if ptype == "Supplier Payment":
        columns = get_supplier_payment_columns()
        data    = get_supplier_payment_data(filters)
        summary = get_summary(data)
        return columns, data, None, None, summary
    columns = get_columns(filters)
    data    = get_data(filters)
    summary = get_summary(data)
    return columns, data, None, None, summary


# ---------------------------------------------------------------------------
# Column helpers
# ---------------------------------------------------------------------------

def _col(fieldname, label, fieldtype, options=None, width=130, disable_total=False):
    c = {"fieldname": fieldname, "label": _(label), "fieldtype": fieldtype, "width": width}
    if options:
        c["options"] = options
    if disable_total:
        c["disable_total"] = 1
    return c


_NUMERIC_FIELDTYPES = {"Currency", "Float", "Int", "Percent"}


def _mark_total_label_anchor(columns):
    # Flags the column immediately before the first column that will actually
    # show a computed total, so the JS formatter can put the "Total" text label
    # right next to the real total instead of at a hardcoded fieldname.
    # Copies each column dict first — BASE/TYPE_EXTRA/ALL_EXTRA entries are shared,
    # cached module-level objects reused across every report call and every type;
    # mutating them in place would leak this flag onto unrelated column sets.
    columns = [dict(c) for c in columns]
    for i, col in enumerate(columns):
        if col["fieldtype"] in _NUMERIC_FIELDTYPES and not col.get("disable_total"):
            if i > 0:
                columns[i - 1]["show_total_label"] = 1
            break
    return columns


BASE = [
    # "Entry No"/"Entry Date"/Dynamic Link: this same column set is shared by the
    # all-types (blank Payment Type) view, which blends in Fuel Incentive entries
    # (sourced from Fuel Urea Expenses, not Payment) alongside Payment rows — so the
    # link target is resolved per-row from "doctype_ref" instead of being fixed to Payment.
    _col("payment_no",            "Entry No",          "Dynamic Link", "doctype_ref", 160),
    _col("date",                  "Entry Date",        "Date",     None,      110),
    _col("type",                  "Payment Type",      "Data",     None,      150),
    _col("status",                "Status",            "Data",     None,       90),
    _col("mode_of_payment",       "Mode of Payment",   "Data",     None,      130),
    _col("paid_from_account_name","Paid From Account", "Data",     None,      170),
    _col("reference_no",          "Reference No",      "Data",     None,      130),
]

_AMOUNT_COL = _col("amount", "Amount (₹)", "Currency", None, 130)

_TRIP_COLS = [
    _col("trip_no",           "Trip No",       "Link", "Trip", 140),
    _col("trip_tcn_no",       "TCN / Trip No", "Data", None,   140),
    _col("trip_date",         "Trip Date",     "Date", None,   110),
    _col("trip_origin",       "Origin",        "Data", None,   120),
    _col("trip_destination",  "Destination",   "Data", None,   120),
    _col("trip_vehicle_type", "Vehicle Type",  "Data", None,   120),
]

_VENDOR_COL = _col("vendor_supplier",        "Vendor / Supplier", "Link", "Supplier", 150)
_DRIVER_COL = _col("driver_name",            "Driver",            "Data", None,       160)
_EMP_COL    = _col("employee_name",          "Employee",          "Data", None,       160)

# Reference No now lives in BASE, right next to Paid From Account, for every type.
TYPE_EXTRA = {
    "Loading":             [_VENDOR_COL] + _TRIP_COLS,
    "Unloading":           [_VENDOR_COL] + _TRIP_COLS,
    "Extra Expense":       [_VENDOR_COL] + _TRIP_COLS,
    "Border Crossing/Vehicle Expense/Toll Tax": [_VENDOR_COL] + _TRIP_COLS,
    "Police Entry":        [_VENDOR_COL] + _TRIP_COLS,
    "Employee LR Money":   [_EMP_COL]    + _TRIP_COLS,
    "Driver Trip Expense": [_DRIVER_COL] + _TRIP_COLS,
    "Driver Advance": [
        _DRIVER_COL,
    ],
    "Employee Advance": [
        _EMP_COL,
    ],
    "Employee Incentive": [
        _EMP_COL,
    ],
    "Office": [
        _col("select_account_name", "Expense Account", "Data", None, 170),
        _VENDOR_COL,
    ],
    "Other Expense": [
        _col("select_account_name", "Expense Account", "Data", None, 170),
        _VENDOR_COL,
    ],
    "Vehicle Finance EMI": [
        _col("vehicle_finance", "Vehicle Finance", "Link", "Vehicle Finance", 150),
        _col("vf_vehicle",      "Vehicle No",      "Data", None,              130),
        _col("vf_financer",     "Financer / Bank", "Data", None,              150),
        _col("vf_loan_account", "Loan Account",    "Data", None,              150),
    ],
    "Bank Transfer": [
        _col("transfer_to_account_name", "Transfer To Account", "Data", None, 170),
    ],
    "Cash Withdrawal": [
        _col("select_account_name", "Expense Account", "Data", None, 170),
    ],
}

# All-types view: every possible column visible
ALL_EXTRA = [
    # Party columns
    _EMP_COL,
    _DRIVER_COL,
    _VENDOR_COL,
    # Trip columns
    _col("trip_no",           "Trip No",         "Link", "Trip", 140),
    _col("trip_tcn_no",       "TCN / Trip No",   "Data", None,   140),
    _col("trip_date",         "Trip Date",       "Date", None,   110),
    _col("trip_origin",       "Origin",          "Data", None,   120),
    _col("trip_destination",  "Destination",     "Data", None,   120),
    _col("trip_vehicle_type", "Vehicle Type",    "Data", None,   120),
    # Vehicle Finance columns
    _col("vehicle_finance",   "Vehicle Finance", "Link", "Vehicle Finance", 150),
    _col("vf_vehicle",        "Vehicle No",      "Data", None,              130),
    _col("vf_financer",       "Financer / Bank", "Data", None,              150),
    _col("vf_loan_account",   "Loan Account",    "Data", None,              150),
    # Expense account (Office/Other Expense/Cash Withdrawal)
    _col("select_account_name","Expense Account","Data", None,              170),
    # Transfer To Account (Bank Transfer)
    _col("transfer_to_account_name","Transfer To Account","Data", None,     170),
    # Fuel Incentive columns
    _col("fixed_kpl",             "Fixed KPL",                  "Float",    None, 100, disable_total=True),
    _col("kpl",                   "Actual KPL",                 "Float",    None, 100, disable_total=True),
    _col("excessshort_fuel",      "Excess/Short Fuel",          "Float",    None, 130, disable_total=True),
    _col("excessshort_fuel_rate", "Excess/Short Rate (₹)",      "Currency", None, 130, disable_total=True),
    _col("fuel_incentive",        "Fuel Incentive (₹)",         "Currency", None, 140),
    # Vendor Payment (trip-line) columns
    _col("hire_amount",           "Hire Amount (₹)",            "Currency", None, 130, disable_total=True),
    _col("balance",               "Balance (₹)",                "Currency", None, 120, disable_total=True),
    _col("payment_amount",        "Payment Amount (₹)",         "Currency", None, 140, disable_total=True),
    _col("employee_lr_money",     "Employee LR Money (₹)",      "Currency", None, 150, disable_total=True),
    _col("company_lr_money",      "Company LR Money (₹)",       "Currency", None, 150, disable_total=True),
    _col("lr_money",              "LR Money (₹)",               "Currency", None, 120, disable_total=True),
    _col("tds_amount",            "TDS (₹)",                    "Currency", None, 110, disable_total=True),
    _col("advance_or_balance",    "Advance/Balance",            "Data",     None, 120),
    _col("row_payment_type",      "Payment Sub-Type",           "Data",     None, 120),
    _col("row_remarks",           "Remarks",                    "Data",     None, 150),
]


_EMPLOYEE_FIRST_TYPES = {"Employee LR Money", "Employee Advance", "Employee Incentive"}


def get_columns(filters):
    ptype = (filters.get("type") or "").strip()
    extra = TYPE_EXTRA.get(ptype, ALL_EXTRA)

    if ptype in _EMPLOYEE_FIRST_TYPES:
        # Employee column goes right after Payment No for these two types.
        extra = [c for c in extra if c["fieldname"] != "employee_name"]
        columns = [BASE[0], _EMP_COL] + BASE[1:] + extra + [_AMOUNT_COL]
    else:
        columns = BASE + extra + [_AMOUNT_COL]

    return _mark_total_label_anchor(columns)


def get_fuel_incentive_columns():
    columns = [
        _col("payment_no",              "Entry No",                   "Link",     "Fuel Urea Expenses", 150),
        _col("date",                    "Entry Date",                 "Date",     None,                  110),
        _col("status",                  "Status",                     "Data",     None,                   90),
        _col("mode_of_payment",         "Mode of Payment",            "Data",     None,                  130),
        _col("bank_account_name",       "Bank Account",               "Data",     None,                  170),
        _col("reference_no",            "Reference",                  "Data",     None,                  130),
        _col("driver_name",             "Driver",                     "Data",     None,                  160),
        _col("vehicle_no",              "Vehicle No",                 "Data",     None,                  130),
        _col("fixed_kpl",               "Fixed KPL",                  "Float",    None,                  100, disable_total=True),
        _col("kpl",                     "Actual KPL",                 "Float",    None,                  100, disable_total=True),
        _col("excessshort_fuel",        "Excess/Short Fuel",          "Float",    None,                  130, disable_total=True),
        _col("excessshort_fuel_rate",   "Excess/Short Rate (₹)",      "Currency", None,                  130, disable_total=True),
        _col("fuel_incentive",          "Fuel Incentive (₹)",         "Currency", None,                  140),
        _col("amount",                  "Amount Paid to Driver (₹)",  "Currency", None,                  170),
    ]
    return _mark_total_label_anchor(columns)


def get_vendor_payment_columns():
    # One row per Vendor Payment Trip line (a single Vendor Payment can cover many
    # trips), so every child-table field is surfaced alongside the payment header.
    columns = [
        _col("payment_no",              "Entry No",              "Link",     "Vendor Payment", 150),
        _col("date",                    "Entry Date",            "Date",     None,             110),
        _col("status",                  "Status",                "Data",     None,              90),
        _col("mode_of_payment",         "Mode of Payment",       "Data",     None,             130),
        _col("paid_from_account_name",  "Paid From Account",     "Data",     None,             170),
        _col("reference_no",            "Reference No",          "Data",     None,             130),
        _col("vendor_supplier",         "Vendor",                "Link",     "Supplier",       160),
        _col("trip_no",                 "Trip No",               "Link",     "Trip",           140),
        _col("trip_date",               "Trip Date",             "Date",     None,             110),
        _col("tcn_no",                  "TCN/Trip No",           "Data",     None,             130),
        _col("lr_no",                   "LR No",                 "Data",     None,             110),
        _col("vehicle_no",              "Vehicle No",            "Link",     "Vehicle",        130),
        _col("hire_amount",             "Hire Amount (₹)",       "Currency", None,             130, disable_total=True),
        _col("balance",                 "Balance (₹)",           "Currency", None,             120, disable_total=True),
        _col("payment_amount",          "Payment Amount (₹)",    "Currency", None,             140, disable_total=True),
        _col("employee_lr_money",       "Employee LR Money (₹)", "Currency", None,             150, disable_total=True),
        _col("company_lr_money",        "Company LR Money (₹)",  "Currency", None,             150, disable_total=True),
        _col("lr_money",                "LR Money (₹)",          "Currency", None,             120, disable_total=True),
        _col("tds_amount",              "TDS (₹)",               "Currency", None,             110, disable_total=True),
        _col("advance_or_balance",      "Advance/Balance",       "Data",     None,             120),
        _col("row_payment_type",        "Type",                  "Data",     None,             100),
        _col("row_remarks",             "Remarks",               "Data",     None,             150),
        _col("amount",                  "Transfer Amount (₹)",   "Currency", None,             150),
    ]
    return _mark_total_label_anchor(columns)


def get_supplier_payment_columns():
    # One row per Payment Invoices line (a single Supplier Payment can cover many
    # Purchase Invoices), so every child-table field is surfaced alongside the
    # payment header — same shape as get_vendor_payment_columns() but for the
    # non-trip Supplier Payment source.
    columns = [
        _col("payment_no",              "Entry No",              "Link",     "Supplier Payment", 150),
        _col("date",                    "Entry Date",            "Date",     None,             110),
        _col("status",                  "Status",                "Data",     None,              90),
        _col("mode_of_payment",         "Mode of Payment",       "Data",     None,             130),
        _col("paid_from_account_name",  "Paid From Account",     "Data",     None,             170),
        _col("reference_no",            "Reference No",          "Data",     None,             130),
        _col("vendor_supplier",         "Supplier",              "Link",     "Supplier",       160),
        _col("purchase_invoice",        "Purchase Invoice",      "Link",     "Purchase Invoice", 150),
        _col("invoice_date",            "Invoice Date",          "Date",     None,             110),
        _col("supplier_invoice_no",     "Supplier Invoice No",   "Data",     None,             150),
        _col("grand_total",             "Grand Total (₹)",       "Currency", None,             130, disable_total=True),
        _col("balance",                 "Balance (₹)",           "Currency", None,             120, disable_total=True),
        _col("payment_amount",          "Payment Amount (₹)",    "Currency", None,             140, disable_total=True),
        _col("tds_amount",              "TDS (₹)",               "Currency", None,             110, disable_total=True),
        _col("advance_or_balance",      "Advance/Balance",       "Data",     None,             120),
        _col("row_remarks",             "Remarks",               "Data",     None,             150),
        _col("amount",                  "Transfer Amount (₹)",   "Currency", None,             150),
    ]
    return _mark_total_label_anchor(columns)


# ---------------------------------------------------------------------------
# Filters definition
# ---------------------------------------------------------------------------

def get_report_filters():
    return [
        # ── Core ──────────────────────────────────────────────────────────
        {
            "fieldname": "company",
            "label": _("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "reqd": 1,
            "default": frappe.defaults.get_user_default("Company"),
        },
        {
            "fieldname": "from_date",
            "label": _("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.utils.add_months(frappe.utils.today(), -1),
        },
        {
            "fieldname": "to_date",
            "label": _("To Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.utils.today(),
        },
        {
            "fieldname": "type",
            "label": _("Payment Type"),
            "fieldtype": "Select",
            "options": (
                "\nLoading\nUnloading\nExtra Expense\nEmployee LR Money"
                "\nOffice\nOther Expense\nPolice Entry\nEmployee Advance\nEmployee Incentive\nDriver Advance"
                "\nDriver Trip Expense\nVehicle Finance EMI\nFuel Incentive"
                "\nVendor Payment\nBank Transfer\nCash Withdrawal\nSupplier Payment"
            ),
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Select",
            "options": "\nDraft\nPaid\nCancelled",
        },
        {
            "fieldname": "mode_of_payment",
            "label": _("Mode of Payment"),
            "fieldtype": "Select",
            "options": "\nCash\nBank Transfer\nCheque\nUPI",
        },
        # ── Party filters (use whichever is relevant to the selected type) ─
        {
            "fieldname": "trip_no",
            "label": _("Trip No"),
            "fieldtype": "Link",
            "options": "Trip",
        },
        {
            "fieldname": "driver",
            "label": _("Driver"),
            "fieldtype": "Link",
            "options": "Driver",
        },
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
        },
        {
            "fieldname": "vendor_supplier",
            "label": _("Vendor / Supplier"),
            "fieldtype": "Link",
            "options": "Supplier",
        },
        # ── Vehicle Finance filters ────────────────────────────────────────
        {
            "fieldname": "vehicle_finance",
            "label": _("Vehicle Finance"),
            "fieldtype": "Link",
            "options": "Vehicle Finance",
        },
        {
            "fieldname": "vf_vehicle",
            "label": _("Vehicle No"),
            "fieldtype": "Link",
            "options": "Vehicle",
        },
        {
            "fieldname": "financer",
            "label": _("Financer / Bank"),
            "fieldtype": "Data",
        },
    ]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

_VENDOR_TYPES   = {"Loading", "Unloading", "Extra Expense", "Vendor Payment", "Supplier Payment"}
_EMPLOYEE_TYPES = {"Employee LR Money", "Employee Advance", "Employee Incentive"}
_DRIVER_TYPES   = {"Driver Advance", "Driver Trip Expense", "Fuel Incentive"}
_VF_TYPES       = {"Vehicle Finance EMI"}
_OFFICE_TYPES   = {"Office", "Other Expense"}


def _map_fuel_incentive_row_for_blend(row):
    # Fuel Urea Expenses rows use their own fieldnames (bank_account_name, vehicle_no);
    # remap them onto the Payment-shaped fields the all-types (blank Payment Type)
    # view's columns expect, so both sources render through the same column set.
    return {
        "payment_no":             row["payment_no"],
        "doctype_ref":            row["doctype_ref"],
        "date":                   row["date"],
        "type":                   row["type"],
        "status":                 row["status"],
        "mode_of_payment":        row["mode_of_payment"],
        "paid_from_account_name": row["bank_account_name"],
        "driver_name":            row["driver_name"],
        "vf_vehicle":             row["vehicle_no"],
        "reference_no":           row["reference_no"],
        "fixed_kpl":              row["fixed_kpl"],
        "kpl":                    row["kpl"],
        "excessshort_fuel":       row["excessshort_fuel"],
        "excessshort_fuel_rate":  row["excessshort_fuel_rate"],
        "fuel_incentive":         row["fuel_incentive"],
        "amount":                 row["amount"],
    }


def _map_vendor_payment_row_for_blend(row):
    # Vendor Payment Trip (child) rows use their own fieldnames (trip_no, tcn_no,
    # vehicle_no); remap them onto the same Payment-shaped fields as every other
    # blended source so they render through the all-types view's shared columns.
    return {
        "payment_no":             row["payment_no"],
        "doctype_ref":            row["doctype_ref"],
        "date":                   row["date"],
        "type":                   row["type"],
        "status":                 row["status"],
        "mode_of_payment":        row["mode_of_payment"],
        "paid_from_account_name": row["paid_from_account_name"],
        "vendor_supplier":        row["vendor_supplier"],
        "trip_no":                row["trip_no"],
        "trip_tcn_no":            row["tcn_no"],
        "trip_date":              row["trip_date"],
        "vf_vehicle":             row["vehicle_no"],
        "reference_no":           row["reference_no"],
        "hire_amount":            row["hire_amount"],
        "balance":                row["balance"],
        "payment_amount":         row["payment_amount"],
        "employee_lr_money":      row["employee_lr_money"],
        "company_lr_money":       row["company_lr_money"],
        "lr_money":               row["lr_money"],
        "tds_amount":             row["tds_amount"],
        "advance_or_balance":     row["advance_or_balance"],
        "row_payment_type":       row["row_payment_type"],
        "row_remarks":            row["row_remarks"],
        "amount":                 row["amount"],
    }


def _map_supplier_payment_row_for_blend(row):
    # Payment Invoices (child) rows use their own fieldnames (purchase_invoice,
    # invoice_date); remap them onto the same Payment-shaped fields as every
    # other blended source so they render through the all-types view's shared
    # columns.
    return {
        "payment_no":             row["payment_no"],
        "doctype_ref":            row["doctype_ref"],
        "date":                   row["date"],
        "type":                   row["type"],
        "status":                 row["status"],
        "mode_of_payment":        row["mode_of_payment"],
        "paid_from_account_name": row["paid_from_account_name"],
        "vendor_supplier":        row["vendor_supplier"],
        "reference_no":           row["reference_no"],
        "balance":                row["balance"],
        "payment_amount":         row["payment_amount"],
        "tds_amount":             row["tds_amount"],
        "advance_or_balance":     row["advance_or_balance"],
        "row_remarks":            row["row_remarks"],
        "amount":                 row["amount"],
    }


def _compute_party(row):
    ptype = row.get("type", "")
    if ptype in _VENDOR_TYPES:
        return row.get("vendor_supplier") or ""
    if ptype in _EMPLOYEE_TYPES:
        return row.get("employee_name") or row.get("employee") or ""
    if ptype in _DRIVER_TYPES:
        return row.get("driver_name") or row.get("driver") or ""
    if ptype in _VF_TYPES:
        return row.get("vf_vehicle") or ""
    if ptype in _OFFICE_TYPES:
        return row.get("select_account_name") or row.get("vendor_supplier") or ""
    return row.get("driver_name") or row.get("employee_name") or row.get("vendor_supplier") or ""


def get_data(filters):
    params = {
        "company":   filters.get("company"),
        "from_date": filters.get("from_date"),
        "to_date":   filters.get("to_date"),
    }

    # Build optional WHERE clauses (all prefixed with p.)
    extra = []

    # Exact-match Link filters
    simple = [
        ("type",              "p.type"),
        ("status",            "p.status"),
        ("mode_of_payment",   "p.mode_of_payment"),
        ("paid_from_account", "p.paid_from_account"),
        ("trip_no",           "p.trip_no"),
        ("driver",            "p.driver"),
        ("employee",          "p.employee"),
        ("vendor_supplier",   "p.vendor_supplier"),
        ("vehicle_finance",   "p.vehicle_finance"),
        ("vf_vehicle",        "p.vf_vehicle"),
        ("select_account",    "p.select_account"),
        ("vehicle_type",      "p.trip_vehicle_type"),
    ]
    for key, col in simple:
        if filters.get(key):
            extra.append(f"{col} = %({key})s")
            params[key] = filters[key]

    # Data fields — partial LIKE match
    like_filters = [
        ("tcn_no",       "p.trip_tcn_no"),
        ("origin",       "p.trip_origin"),
        ("destination",  "p.trip_destination"),
        ("financer",     "p.vf_financer"),
        ("loan_account", "p.vf_loan_account"),
    ]
    for key, col in like_filters:
        if filters.get(key):
            extra.append(f"{col} LIKE %({key})s")
            params[key] = f"%{filters[key]}%"

    extra_where = (" AND " + " AND ".join(extra)) if extra else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            p.name              AS payment_no,
            'Payment'           AS doctype_ref,
            p.date,
            p.type,
            p.status,
            p.mode_of_payment,
            p.amount,
            p.vendor_supplier,
            p.driver,
            COALESCE(dr.full_name, p.driver)       AS driver_name,
            p.employee,
            COALESCE(emp.employee_name, p.employee) AS employee_name,
            p.vehicle_finance,
            p.trip_no,
            p.trip_tcn_no,
            p.trip_date,
            p.trip_origin,
            p.trip_destination,
            p.trip_vehicle_type,
            p.vf_vehicle,
            p.vf_financer,
            p.vf_loan_account,
            p.paid_from_account,
            p.select_account,
            p.transfer_to_account,
            p.reference_no,
            COALESCE(ah_paid.name1,  p.paid_from_account)     AS paid_from_account_name,
            COALESCE(ah_sel.name1,   p.select_account)        AS select_account_name,
            COALESCE(ah_xfer.name1,  p.transfer_to_account)   AS transfer_to_account_name
        FROM `tabPayment` p
        LEFT JOIN `tabAccount Head` ah_paid ON ah_paid.name = p.paid_from_account
        LEFT JOIN `tabAccount Head` ah_sel  ON ah_sel.name  = p.select_account
        LEFT JOIN `tabAccount Head` ah_xfer ON ah_xfer.name = p.transfer_to_account
        LEFT JOIN `tabDriver`   dr  ON dr.name  = p.driver
        LEFT JOIN `tabEmployee` emp ON emp.name = p.employee
        WHERE p.company   = %(company)s
          AND p.date BETWEEN %(from_date)s AND %(to_date)s
          AND p.docstatus != 2
          {extra_where}
        ORDER BY p.date DESC, p.name DESC
        """,
        params,
        as_dict=True,
    )

    # All-types view (no Payment Type filter): blend in Fuel Incentive and Vendor
    # Payment entries too — they live in Fuel Urea Expenses / Vendor Payment, not
    # Payment, so they're fetched separately and remapped onto the same column shape
    # before merging.
    if not filters.get("type"):
        fi_rows = [_map_fuel_incentive_row_for_blend(r) for r in get_fuel_incentive_data(filters)]
        vp_rows = [_map_vendor_payment_row_for_blend(r) for r in get_vendor_payment_data(filters)]
        sp_rows = [_map_supplier_payment_row_for_blend(r) for r in get_supplier_payment_data(filters)]
        rows = rows + fi_rows + vp_rows + sp_rows
        rows.sort(key=lambda r: (r.get("date"), r.get("payment_no")), reverse=True)
        for row in rows:
            row["party"] = _compute_party(row)

    return rows


# Party/detail filter fields whose applicability varies by source doctype (every
# fieldname the report's filter panel defines, apart from the 5 universal ones —
# company/from_date/to_date/status/mode_of_payment — which every source already
# handles on its own terms). If a blended source's schema has no matching field for
# one of these, and the user has set it, that source must contribute zero rows —
# not silently ignore the filter — otherwise unrelated entries (e.g. every Fuel
# Incentive row) leak into a result that's supposed to be narrowed by, say, Vendor.
# Every new blended source added in future must declare its own applicable subset
# the same way, so no filter field is ever silently dropped for any type.
_VARIABLE_FILTER_FIELDS = {
    "trip_no", "driver", "employee", "vendor_supplier",
    "vehicle_finance", "vf_vehicle", "financer", "loan_account",
    "paid_from_account", "tcn_no", "origin", "destination",
    "vehicle_type", "select_account",
}


def _source_excluded_by_filters(filters, applicable_fields):
    for field in _VARIABLE_FILTER_FIELDS - applicable_fields:
        if filters.get(field):
            return True
    return False


_FUEL_INCENTIVE_APPLICABLE_FILTERS = {"driver", "vf_vehicle", "paid_from_account"}
_FUEL_INCENTIVE_STATUS_TO_DOCSTATUS = {"Draft": 0, "Paid": 1, "Cancelled": 2}


def get_fuel_incentive_data(filters):
    if _source_excluded_by_filters(filters, _FUEL_INCENTIVE_APPLICABLE_FILTERS):
        return []

    params = {
        "company":   filters.get("company"),
        "from_date": filters.get("from_date"),
        "to_date":   filters.get("to_date"),
    }

    extra = []

    if filters.get("driver"):
        extra.append("fue.driver_id = %(driver)s")
        params["driver"] = filters["driver"]

    if filters.get("vf_vehicle"):
        extra.append("fue.vehicle = %(vf_vehicle)s")
        params["vf_vehicle"] = filters["vf_vehicle"]

    if filters.get("mode_of_payment"):
        extra.append("fue.driver_payment_mode = %(mode_of_payment)s")
        params["mode_of_payment"] = filters["mode_of_payment"]

    if filters.get("paid_from_account"):
        extra.append("fue.driver_bank_name = %(paid_from_account)s")
        params["paid_from_account"] = filters["paid_from_account"]

    status = filters.get("status")
    if status in _FUEL_INCENTIVE_STATUS_TO_DOCSTATUS:
        extra.append("fue.docstatus = %(docstatus)s")
        params["docstatus"] = _FUEL_INCENTIVE_STATUS_TO_DOCSTATUS[status]
    # else: no Status filter set — show every status (Draft, Paid, Cancelled);
    # only "Paid" rows count toward the Amount total (see get_fuel_incentive_summary)

    extra_where = (" AND " + " AND ".join(extra)) if extra else ""

    return frappe.db.sql(
        f"""
        SELECT
            fue.name                                 AS payment_no,
            'Fuel Urea Expenses'                     AS doctype_ref,
            'Fuel Incentive'                         AS type,
            fue.date                                  AS date,
            CASE fue.docstatus
                WHEN 0 THEN 'Draft'
                WHEN 1 THEN 'Paid'
                ELSE 'Cancelled'
            END                                        AS status,
            fue.driver_payment_mode                   AS mode_of_payment,
            COALESCE(ah.name1, fue.driver_bank_name)   AS bank_account_name,
            COALESCE(dr.full_name, fue.driver_id)      AS driver_name,
            fue.vehicle                                AS vehicle_no,
            fue.fixed_kpl                              AS fixed_kpl,
            fue.kpl                                    AS kpl,
            fue.excessshort_fuel                       AS excessshort_fuel,
            fue.excessshort_fuel_rate                  AS excessshort_fuel_rate,
            fue.fuel_incentive                         AS fuel_incentive,
            fue.driver_payment_reference                AS reference_no,
            fue.expense_amount                         AS amount
        FROM `tabFuel Urea Expenses` fue
        LEFT JOIN `tabDriver` dr       ON dr.name = fue.driver_id
        LEFT JOIN `tabVehicle` veh     ON veh.name = fue.vehicle
        LEFT JOIN `tabAccount Head` ah ON ah.name = fue.driver_bank_name
        WHERE veh.company = %(company)s
          AND fue.date BETWEEN %(from_date)s AND %(to_date)s
          AND fue.fuel_incentive != 0
          {extra_where}
        ORDER BY fue.date DESC, fue.name DESC
        """,
        params,
        as_dict=True,
    )


_VENDOR_PAYMENT_APPLICABLE_FILTERS = {
    "vendor_supplier", "trip_no", "vf_vehicle", "paid_from_account", "tcn_no",
}
_VENDOR_PAYMENT_STATUS_TO_DOCSTATUS = {"Draft": 0, "Paid": 1, "Cancelled": 2}


def get_vendor_payment_data(filters):
    if _source_excluded_by_filters(filters, _VENDOR_PAYMENT_APPLICABLE_FILTERS):
        return []

    params = {
        "company":   filters.get("company"),
        "from_date": filters.get("from_date"),
        "to_date":   filters.get("to_date"),
    }

    extra = []

    if filters.get("vendor_supplier"):
        extra.append("vp.vendor = %(vendor_supplier)s")
        params["vendor_supplier"] = filters["vendor_supplier"]

    if filters.get("mode_of_payment"):
        extra.append("vp.mode_of_payment = %(mode_of_payment)s")
        params["mode_of_payment"] = filters["mode_of_payment"]

    if filters.get("trip_no"):
        extra.append("vpt.trip = %(trip_no)s")
        params["trip_no"] = filters["trip_no"]

    if filters.get("paid_from_account"):
        extra.append("vp.paid_from_account = %(paid_from_account)s")
        params["paid_from_account"] = filters["paid_from_account"]

    if filters.get("tcn_no"):
        extra.append("vpt.tcntrip_no LIKE %(tcn_no)s")
        params["tcn_no"] = f"%{filters['tcn_no']}%"

    if filters.get("vf_vehicle"):
        extra.append("vpt.vehicle_no = %(vf_vehicle)s")
        params["vf_vehicle"] = filters["vf_vehicle"]

    status = filters.get("status")
    if status in _VENDOR_PAYMENT_STATUS_TO_DOCSTATUS:
        extra.append("vp.docstatus = %(docstatus)s")
        params["docstatus"] = _VENDOR_PAYMENT_STATUS_TO_DOCSTATUS[status]
    else:
        extra.append("vp.docstatus != 2")

    extra_where = (" AND " + " AND ".join(extra)) if extra else ""

    return frappe.db.sql(
        f"""
        SELECT
            vp.name                                      AS payment_no,
            'Vendor Payment'                              AS doctype_ref,
            'Vendor Payment'                              AS type,
            vp.payment_date                               AS date,
            CASE vp.docstatus
                WHEN 0 THEN 'Draft'
                WHEN 1 THEN 'Paid'
                ELSE 'Cancelled'
            END                                            AS status,
            vp.mode_of_payment                            AS mode_of_payment,
            COALESCE(ah.name1, vp.paid_from_account)      AS paid_from_account_name,
            vp.reference_no                               AS reference_no,
            vp.vendor                                     AS vendor_supplier,
            vpt.trip                                      AS trip_no,
            vpt.trip_date                                 AS trip_date,
            vpt.tcntrip_no                                AS tcn_no,
            vpt.lr_no                                     AS lr_no,
            vpt.vehicle_no                                AS vehicle_no,
            vpt.hire_amount                                AS hire_amount,
            vpt.balance                                    AS balance,
            vpt.payment_amount                             AS payment_amount,
            vpt.employee_lr_money                          AS employee_lr_money,
            vpt.company_lr_money                           AS company_lr_money,
            vpt.lr_money                                   AS lr_money,
            vpt.tds_amount                                 AS tds_amount,
            vpt.advance_or_balance                         AS advance_or_balance,
            vpt.payment_type                               AS row_payment_type,
            vpt.row_remarks                                AS row_remarks,
            vpt.transfer_amount                            AS amount
        FROM `tabVendor Payment` vp
        INNER JOIN `tabVendor Payment Trip` vpt ON vpt.parent = vp.name
        LEFT JOIN `tabAccount Head` ah ON ah.name = vp.paid_from_account
        WHERE vp.company = %(company)s
          AND vp.payment_date BETWEEN %(from_date)s AND %(to_date)s
          {extra_where}
        ORDER BY vp.payment_date DESC, vp.name DESC, vpt.idx ASC
        """,
        params,
        as_dict=True,
    )


_SUPPLIER_PAYMENT_APPLICABLE_FILTERS = {"vendor_supplier", "paid_from_account"}
_SUPPLIER_PAYMENT_STATUS_TO_DOCSTATUS = {"Draft": 0, "Paid": 1, "Cancelled": 2}


def get_supplier_payment_data(filters):
    if _source_excluded_by_filters(filters, _SUPPLIER_PAYMENT_APPLICABLE_FILTERS):
        return []

    params = {
        "company":   filters.get("company"),
        "from_date": filters.get("from_date"),
        "to_date":   filters.get("to_date"),
    }

    extra = []

    if filters.get("vendor_supplier"):
        extra.append("sp.supplier = %(vendor_supplier)s")
        params["vendor_supplier"] = filters["vendor_supplier"]

    if filters.get("mode_of_payment"):
        extra.append("sp.mode_of_payment = %(mode_of_payment)s")
        params["mode_of_payment"] = filters["mode_of_payment"]

    if filters.get("paid_from_account"):
        extra.append("sp.paid_from_account = %(paid_from_account)s")
        params["paid_from_account"] = filters["paid_from_account"]

    status = filters.get("status")
    if status in _SUPPLIER_PAYMENT_STATUS_TO_DOCSTATUS:
        extra.append("sp.docstatus = %(docstatus)s")
        params["docstatus"] = _SUPPLIER_PAYMENT_STATUS_TO_DOCSTATUS[status]
    else:
        extra.append("sp.docstatus != 2")

    extra_where = (" AND " + " AND ".join(extra)) if extra else ""

    return frappe.db.sql(
        f"""
        SELECT
            sp.name                                       AS payment_no,
            'Supplier Payment'                            AS doctype_ref,
            'Supplier Payment'                             AS type,
            sp.payment_date                               AS date,
            CASE sp.docstatus
                WHEN 0 THEN 'Draft'
                WHEN 1 THEN 'Paid'
                ELSE 'Cancelled'
            END                                            AS status,
            sp.mode_of_payment                            AS mode_of_payment,
            COALESCE(ah.name1, sp.paid_from_account)      AS paid_from_account_name,
            sp.reference_no                               AS reference_no,
            sp.supplier                                   AS vendor_supplier,
            pi.purchase_invoice                           AS purchase_invoice,
            pi.invoice_date                               AS invoice_date,
            pi.supplier_invoice_no                        AS supplier_invoice_no,
            pi.grand_total                                AS grand_total,
            pi.balance                                    AS balance,
            pi.payment_amount                             AS payment_amount,
            pi.tds_amount                                 AS tds_amount,
            pi.advance_or_balance                         AS advance_or_balance,
            pi.row_remarks                                AS row_remarks,
            pi.transfer_amount                            AS amount
        FROM `tabSupplier Payment` sp
        INNER JOIN `tabPayment Invoices` pi ON pi.parent = sp.name
        LEFT JOIN `tabAccount Head` ah ON ah.name = sp.paid_from_account
        WHERE sp.company = %(company)s
          AND sp.payment_date BETWEEN %(from_date)s AND %(to_date)s
          {extra_where}
        ORDER BY sp.payment_date DESC, sp.name DESC, pi.idx ASC
        """,
        params,
        as_dict=True,
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _total_amount(data):
    # Fuel Incentive rows only count toward the total when Paid — every status is
    # listed for visibility, but Draft/Cancelled don't represent money actually given
    # to the driver. Every other payment type counts regardless of status, unchanged.
    return sum(
        flt(r.get("amount"))
        for r in data
        if r.get("type") != "Fuel Incentive" or r.get("status") == "Paid"
    )


def get_summary(data):
    return [
        {"label": _("Total Transactions"), "value": len(data),         "datatype": "Int",      "indicator": "blue"},
        {"label": _("Total Amount"),       "value": _total_amount(data), "datatype": "Currency", "indicator": "green"},
    ]


def get_fuel_incentive_summary(data):
    return [
        {"label": _("Total Entries"),        "value": len(data),           "datatype": "Int",      "indicator": "blue"},
        {"label": _("Total Amount (Paid)"),  "value": _total_amount(data), "datatype": "Currency", "indicator": "green"},
    ]
