import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "posting_date", "label": _("Date"), "fieldtype": "Date", "width": 100},
        {"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "stock_uom", "label": _("Stock UOM"), "fieldtype": "Link", "options": "UOM", "width": 90},
        {"fieldname": "in_qty", "label": _("In Qty"), "fieldtype": "Float", "width": 90},
        {"fieldname": "out_qty", "label": _("Out Qty"), "fieldtype": "Float", "width": 90},
        {"fieldname": "balance_qty", "label": _("Balance Qty"), "fieldtype": "Float", "width": 100},
        {"fieldname": "warehouse", "label": _("Warehouse"), "fieldtype": "Link", "options": "Warehouse", "width": 130},
        {"fieldname": "item_group", "label": _("Item Group"), "fieldtype": "Link", "options": "Item Group", "width": 110},
        {"fieldname": "valuation_rate", "label": _("Valuation Rate"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "stock_value", "label": _("Balance Value"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "stock_value_difference", "label": _("Value Change"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 130},
        {"fieldname": "voucher_no", "label": _("Voucher No"), "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 150},
        {"fieldname": "vehicle", "label": _("Vehicle No"), "fieldtype": "Link", "options": "Vehicle", "width": 130},
    ]


# Expense doctypes whose "In Stock Use" flow auto-creates a Stock Entry and
# records it back on `stock_entry` — used to trace a Stock Entry voucher back
# to the vehicle it was issued for. Each entry is (doctype, vehicle_fieldname).
_VEHICLE_SOURCE_DOCTYPES = [
    ("Battery Expenses", "vehicle_id"),
    ("Tyre Expenses", "vehicle_id"),
    ("Fuel Urea Expenses", "vehicle"),
]


def _get_stock_entry_vehicle_map():
    mapping = {}
    for doctype, vehicle_field in _VEHICLE_SOURCE_DOCTYPES:
        rows = frappe.db.get_all(
            doctype,
            filters={"stock_entry": ["is", "set"]},
            fields=["stock_entry", f"{vehicle_field} as vehicle"],
        )
        for row in rows:
            if row.vehicle:
                mapping[row.stock_entry] = row.vehicle
    return mapping


def get_data(filters):
    conditions = ["sle.is_cancelled = 0"]
    values = {}

    if filters.get("company"):
        conditions.append("sle.company = %(company)s")
        values["company"] = filters["company"]
    if filters.get("item_code"):
        conditions.append("sle.item_code = %(item_code)s")
        values["item_code"] = filters["item_code"]
    if filters.get("item_group"):
        conditions.append("item.item_group = %(item_group)s")
        values["item_group"] = filters["item_group"]
    if filters.get("warehouse"):
        conditions.append("sle.warehouse = %(warehouse)s")
        values["warehouse"] = filters["warehouse"]
    if filters.get("voucher_no"):
        conditions.append("sle.voucher_no = %(voucher_no)s")
        values["voucher_no"] = filters["voucher_no"]
    if filters.get("from_date"):
        conditions.append("sle.posting_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("sle.posting_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    where_clause = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            sle.posting_date,
            sle.posting_time,
            sle.item_code,
            item.item_name,
            item.item_group,
            item.brand,
            item.description,
            sle.warehouse,
            sle.voucher_type,
            sle.voucher_no,
            sle.actual_qty,
            sle.qty_after_transaction AS balance_qty,
            sle.stock_uom,
            sle.valuation_rate,
            sle.stock_value,
            sle.stock_value_difference
        FROM `tabStock Ledger Entry` sle
        LEFT JOIN `tabItem` item ON item.name = sle.item_code
        WHERE {where_clause}
        ORDER BY sle.posting_date ASC, sle.posting_time ASC, sle.creation ASC
        """,
        values,
        as_dict=1,
    )

    vehicle_map = _get_stock_entry_vehicle_map()
    vehicle_filter = filters.get("vehicle")

    result = []
    for row in rows:
        qty = row.pop("actual_qty") or 0
        row["in_qty"] = qty if qty > 0 else 0
        row["out_qty"] = abs(qty) if qty < 0 else 0
        row["posting_time"] = _format_time(row["posting_time"])
        if row["voucher_type"] == "Stock Entry":
            row["vehicle"] = vehicle_map.get(row["voucher_no"])

        # vehicle isn't a real Stock Ledger Entry column (it's derived from the
        # Battery/Tyre/Fuel Urea Expenses record behind the Stock Entry), so
        # this filter has to be applied here rather than in the SQL WHERE clause.
        if vehicle_filter and row.get("vehicle") != vehicle_filter:
            continue
        result.append(row)

    return result


def _format_time(value):
    # posting_time comes back as a datetime.timedelta (MariaDB TIME column)
    # with microsecond precision — trim to a plain zero-padded HH:MM:SS.
    if value is None:
        return ""
    total_seconds = int(value.total_seconds()) if hasattr(value, "total_seconds") else int(value)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
