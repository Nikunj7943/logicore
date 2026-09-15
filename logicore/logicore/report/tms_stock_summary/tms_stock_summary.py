import frappe
from frappe import _
from frappe.utils import add_months, today


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "item_code", "label": _("Item"), "fieldtype": "Link", "options": "Item", "width": 150},
        {"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "item_group", "label": _("Item Group"), "fieldtype": "Link", "options": "Item Group", "width": 110},
        {"fieldname": "warehouse", "label": _("Warehouse"), "fieldtype": "Link", "options": "Warehouse", "width": 130},
        {"fieldname": "received_qty", "label": _("Received (Period)"), "fieldtype": "Float", "width": 120},
        {"fieldname": "used_qty", "label": _("Used (Period)"), "fieldtype": "Float", "width": 110},
        {"fieldname": "actual_qty", "label": _("Current Balance"), "fieldtype": "Float", "width": 110},
        {"fieldname": "reserved_qty", "label": _("Reserved Qty"), "fieldtype": "Float", "width": 100},
        {"fieldname": "stock_uom", "label": _("UOM"), "fieldtype": "Link", "options": "UOM", "width": 80},
        {"fieldname": "valuation_rate", "label": _("Valuation Rate"), "fieldtype": "Currency", "width": 120},
        {"fieldname": "stock_value", "label": _("Stock Value"), "fieldtype": "Currency", "width": 120},
    ]


def get_data(filters):
    conditions = []
    values = {}

    if not filters.get("show_zero_qty"):
        conditions.append("bin.actual_qty != 0")
    if filters.get("company"):
        conditions.append("warehouse.company = %(company)s")
        values["company"] = filters["company"]
    if filters.get("item_code"):
        conditions.append("bin.item_code = %(item_code)s")
        values["item_code"] = filters["item_code"]
    if filters.get("item_group"):
        conditions.append("item.item_group = %(item_group)s")
        values["item_group"] = filters["item_group"]
    if filters.get("warehouse"):
        conditions.append("bin.warehouse = %(warehouse)s")
        values["warehouse"] = filters["warehouse"]

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            bin.item_code,
            item.item_name,
            item.item_group,
            bin.warehouse,
            bin.actual_qty,
            bin.reserved_qty,
            item.stock_uom,
            bin.valuation_rate,
            bin.stock_value
        FROM `tabBin` bin
        LEFT JOIN `tabItem` item ON item.name = bin.item_code
        LEFT JOIN `tabWarehouse` warehouse ON warehouse.name = bin.warehouse
        {where_clause}
        ORDER BY item.item_group, bin.item_code, bin.warehouse
        """,
        values,
        as_dict=1,
    )

    movement = _get_period_movement(filters)
    for row in rows:
        key = (row["item_code"], row["warehouse"])
        received, used = movement.get(key, (0, 0))
        row["received_qty"] = received
        row["used_qty"] = used

    return rows


def _get_period_movement(filters):
    # Received/Used are period-scoped (from_date/to_date), unlike the current
    # Bin balance columns which are always as-of-now — so this is aggregated
    # separately from Stock Ledger Entry rather than read off Bin.
    from_date = filters.get("from_date") or add_months(today(), -1)
    to_date = filters.get("to_date") or today()

    conditions = ["sle.is_cancelled = 0", "sle.posting_date >= %(from_date)s", "sle.posting_date <= %(to_date)s"]
    values = {"from_date": from_date, "to_date": to_date}

    if filters.get("company"):
        conditions.append("sle.company = %(company)s")
        values["company"] = filters["company"]
    if filters.get("item_code"):
        conditions.append("sle.item_code = %(item_code)s")
        values["item_code"] = filters["item_code"]
    if filters.get("warehouse"):
        conditions.append("sle.warehouse = %(warehouse)s")
        values["warehouse"] = filters["warehouse"]

    where_clause = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            sle.item_code,
            sle.warehouse,
            SUM(CASE WHEN sle.actual_qty > 0 THEN sle.actual_qty ELSE 0 END) AS received_qty,
            SUM(CASE WHEN sle.actual_qty < 0 THEN -sle.actual_qty ELSE 0 END) AS used_qty
        FROM `tabStock Ledger Entry` sle
        WHERE {where_clause}
        GROUP BY sle.item_code, sle.warehouse
        """,
        values,
        as_dict=1,
    )

    return {(r.item_code, r.warehouse): (r.received_qty or 0, r.used_qty or 0) for r in rows}
