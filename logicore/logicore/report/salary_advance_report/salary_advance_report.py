import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data, summary = get_data(filters)
    return columns, data, None, None, summary


def get_columns():
    return [
        {
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "fieldname": "description",
            "label": _("Description"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "reference",
            "label": _("Reference"),
            "fieldtype": "Dynamic Link",
            "options": "ref_doctype",
            "width": 160,
        },
        {
            "fieldname": "ref_doctype",
            "label": _("Ref DocType"),
            "fieldtype": "Data",
            "width": 0,
            "hidden": 1,
        },
        {
            "fieldname": "given",
            "label": _("Given (₹)"),
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "fieldname": "taken",
            "label": _("Recovered (₹)"),
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "fieldname": "balance",
            "label": _("Balance (₹)"),
            "fieldtype": "Currency",
            "width": 130,
        },
    ]


def get_data(filters):
    employee_type = filters.get("employee_type", "Employee")
    employee_link = filters.get("employee_link")

    rows = []

    if employee_type == "Employee":
        if not employee_link:
            return [], []
        advance_type = "Employee Advance"
        party_filter = {"employee": employee_link}
        payroll_party_field = "employee"
    else:
        if not employee_link:
            return [], []
        advance_type = "Driver Advance"
        party_filter = {"driver": employee_link}
        payroll_party_field = "driver"

    # --- Advances Given (from Payment) ---
    advances = frappe.db.get_all(
        "Payment",
        filters={**party_filter, "type": advance_type, "docstatus": 1},
        fields=["name", "date", "amount"],
        order_by="date asc",
    )

    for adv in advances:
        rows.append({
            "date": adv.date,
            "description": "Salary Advance Given",
            "reference": adv.name,
            "ref_doctype": "Payment",
            "given": flt(adv.amount),
            "taken": 0,
            "balance": 0,
            "_type": "given",
        })

    # --- Advance Recoveries (from Staff Payroll) ---
    recoveries = frappe.db.sql(f"""
        SELECT
            sp.payroll_date AS date,
            sp.name AS payroll_name,
            par.payment_ref,
            par.recovery_amount
        FROM `tabPayroll Advance Recovery` par
        INNER JOIN `tabStaff Payroll` sp ON sp.name = par.parent
        WHERE sp.{payroll_party_field} = %s
          AND sp.docstatus = 1
          AND par.recovery_amount > 0
        ORDER BY sp.payroll_date ASC, sp.creation ASC, par.idx ASC
    """, (employee_link,), as_dict=True)

    for rec in recoveries:
        rows.append({
            "date": rec.date,
            "description": f"Advance Recovery — {rec.payroll_name}",
            "reference": rec.payroll_name,
            "ref_doctype": "Staff Payroll",
            "given": 0,
            "taken": flt(rec.recovery_amount),
            "balance": 0,
            "_type": "taken",
        })

    # Sort all rows by date
    rows.sort(key=lambda r: str(r["date"]))

    # Running balance
    running_balance = 0
    for row in rows:
        running_balance += flt(row["given"]) - flt(row["taken"])
        row["balance"] = running_balance

    # Summary row
    total_given = sum(flt(r["given"]) for r in rows)
    total_taken = sum(flt(r["taken"]) for r in rows)
    final_balance = total_given - total_taken

    summary = [
        {"label": _("Total Advance Given"), "value": total_given, "datatype": "Currency", "indicator": "blue"},
        {"label": _("Total Recovered"), "value": total_taken, "datatype": "Currency", "indicator": "green"},
        {"label": _("Outstanding Balance"), "value": final_balance, "datatype": "Currency",
         "indicator": "red" if final_balance > 0 else "green"},
    ]

    # Add bold total row at bottom
    if rows:
        rows.append({
            "date": None,
            "description": "TOTAL",
            "reference": "",
            "ref_doctype": "",
            "given": total_given,
            "taken": total_taken,
            "balance": final_balance,
            "_type": "total",
            "bold": 1,
        })

    return rows, summary
