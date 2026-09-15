import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    data, summary = get_data(filters)
    columns = get_columns(filters)
    return columns, data, None, None, summary


def get_columns(filters):
    direction = filters.get("direction") or "Both"
    base = [
        {"fieldname": "sr_no",        "label": _("#"),            "fieldtype": "Int",          "width": 50},
        {"fieldname": "date",         "label": _("Date"),         "fieldtype": "Date",         "width": 110},
        {"fieldname": "category",     "label": _("Category"),     "fieldtype": "Data",         "width": 150},
        {"fieldname": "description",  "label": _("Description"),  "fieldtype": "Data",         "width": 220},
        {"fieldname": "reference",    "label": _("Reference"),    "fieldtype": "Dynamic Link",
         "options": "ref_doctype",    "width": 170},
        {"fieldname": "ref_doctype",  "label": _("Ref DocType"),  "fieldtype": "Data",         "width": 0, "hidden": 1},
        {"fieldname": "payment_mode", "label": _("Payment Mode"), "fieldtype": "Data",         "width": 130},
        {"fieldname": "bank_account", "label": _("Bank / Account"), "fieldtype": "Data",       "width": 200},
    ]
    if direction == "Given":
        base.append({"fieldname": "given", "label": _("Given (₹)"), "fieldtype": "Currency", "width": 140})
    elif direction == "Taken":
        base.append({"fieldname": "taken", "label": _("Recovered (₹)"), "fieldtype": "Currency", "width": 140})
    else:  # Both
        base += [
            {"fieldname": "given",   "label": _("Given (₹)"),     "fieldtype": "Currency", "width": 130},
            {"fieldname": "taken",   "label": _("Recovered (₹)"), "fieldtype": "Currency", "width": 130},
            {"fieldname": "balance", "label": _("Balance (₹)"),   "fieldtype": "Currency", "width": 130},
        ]
    return base


# Cache Account Head name1 lookups within a single report run
def _resolve_bank_name(account_head_map, code):
    if not code:
        return ""
    if code not in account_head_map:
        val = frappe.db.get_value("Account Head", code, "name1") or code
        account_head_map[code] = val
    return account_head_map[code]


def _resolve_bank_account_name(bank_account_map, name):
    if not name:
        return ""
    if name not in bank_account_map:
        val = frappe.db.get_value("Bank Account", name, "account_name") or name
        bank_account_map[name] = val
    return bank_account_map[name]


def get_data(filters):
    employee_type      = filters.get("employee_type", "Employee")
    employee_link      = filters.get("driver_link") if employee_type == "Driver" else filters.get("employee_link")
    from_date          = filters.get("from_date")
    to_date            = filters.get("to_date")
    data_type          = filters.get("data_type") or "All"
    direction          = filters.get("direction") or "Both"
    payment_mode_f     = filters.get("payment_mode_filter") or "All"
    bank_filter        = filters.get("bank_filter") or ""

    if not employee_link:
        return [], []

    is_driver = employee_type == "Driver"
    rows = []

    show_all           = data_type == "All"
    show_advance       = show_all or data_type in ("Salary Advance", "Driver Advance")
    show_trip_expense  = show_all or data_type == "Trip Expense"
    show_fuel_incentive = show_all or data_type == "Fuel Incentive"
    show_payroll       = show_all or data_type == "Staff Payroll"

    ah_map  = {}   # Account Head code → name1
    bac_map = {}   # Bank Account name → account_name

    def date_filter_dict(existing):
        f = dict(existing)
        if from_date and to_date:
            f["date"] = ["between", [from_date, to_date]]
        elif from_date:
            f["date"] = [">=", from_date]
        elif to_date:
            f["date"] = ["<=", to_date]
        return f

    def date_sql_cond(col="date"):
        cond, args = "", []
        if from_date and to_date:
            cond = f"AND {col} BETWEEN %s AND %s"
            args = [from_date, to_date]
        elif from_date:
            cond = f"AND {col} >= %s"
            args = [from_date]
        elif to_date:
            cond = f"AND {col} <= %s"
            args = [to_date]
        return cond, args

    # --- Salary / Driver Advance (Given) ---
    if show_advance and direction in ("Both", "Given"):
        advance_type = "Driver Advance" if is_driver else "Employee Advance"
        party_filt   = {"driver": employee_link} if is_driver else {"employee": employee_link}
        adv_f = date_filter_dict({**party_filt, "type": advance_type, "docstatus": 1})
        if payment_mode_f != "All":
            adv_f["mode_of_payment"] = payment_mode_f
        if bank_filter:
            adv_f["paid_from_account"] = bank_filter

        advances = frappe.db.get_all(
            "Payment",
            filters=adv_f,
            fields=["name", "date", "amount", "mode_of_payment", "paid_from_account"],
            order_by="date asc",
        )
        label = "Driver Advance Given" if is_driver else "Salary Advance Given"
        cat   = "Driver Advance" if is_driver else "Salary Advance"
        for adv in advances:
            rows.append({
                "date": adv.date,
                "category": cat,
                "description": label,
                "reference": adv.name,
                "ref_doctype": "Payment",
                "payment_mode": adv.mode_of_payment or "",
                "bank_account": _resolve_bank_name(ah_map, adv.paid_from_account),
                "given": flt(adv.amount),
                "taken": 0,
                "balance": 0,
                "_type": "advance_given",
                "_bank_code": adv.paid_from_account or "",
            })

    # --- Advance Recoveries (Taken) ---
    if show_advance and direction in ("Both", "Taken"):
        party_field = "driver" if is_driver else "employee"
        dc, da = date_sql_cond("sp.payroll_date")
        rows_sql = frappe.db.sql(f"""
            SELECT
                sp.payroll_date AS date,
                sp.name AS payroll_name,
                sp.payment_mode,
                sp.bank_account,
                par.payment_ref,
                par.recovery_amount
            FROM `tabPayroll Advance Recovery` par
            INNER JOIN `tabStaff Payroll` sp ON sp.name = par.parent
            WHERE sp.{party_field} = %s
              AND sp.docstatus = 1
              AND par.recovery_amount > 0
              {dc}
            ORDER BY sp.payroll_date ASC, sp.creation ASC, par.idx ASC
        """, [employee_link] + da, as_dict=True)

        cat = "Driver Advance" if is_driver else "Salary Advance"
        for rec in rows_sql:
            bank_display = _resolve_bank_name(ah_map, rec.bank_account)
            if payment_mode_f != "All" and rec.payment_mode != payment_mode_f:
                continue
            if bank_filter and rec.bank_account != bank_filter:
                continue
            rows.append({
                "date": rec.date,
                "category": cat,
                "description": f"Advance Recovery — {rec.payroll_name}",
                "reference": rec.payroll_name,
                "ref_doctype": "Staff Payroll",
                "payment_mode": rec.payment_mode or "",
                "bank_account": bank_display,
                "given": 0,
                "taken": flt(rec.recovery_amount),
                "balance": 0,
                "_type": "advance_taken",
                "_bank_code": rec.bank_account or "",
            })

    # --- Driver Trip Expense (Driver only, Given) ---
    if is_driver and show_trip_expense and direction in ("Both", "Given"):
        te_f = date_filter_dict({"driver": employee_link, "type": "Driver Trip Expense", "docstatus": 1})
        if payment_mode_f != "All":
            te_f["mode_of_payment"] = payment_mode_f
        if bank_filter:
            te_f["paid_from_account"] = bank_filter

        trip_exps = frappe.db.get_all(
            "Payment",
            filters=te_f,
            fields=["name", "date", "amount", "mode_of_payment", "paid_from_account", "remarks"],
            order_by="date asc",
        )
        for exp in trip_exps:
            rows.append({
                "date": exp.date,
                "category": "Trip Expense",
                "description": exp.remarks or "Driver Trip Expense",
                "reference": exp.name,
                "ref_doctype": "Payment",
                "payment_mode": exp.mode_of_payment or "",
                "bank_account": _resolve_bank_name(ah_map, exp.paid_from_account),
                "given": flt(exp.amount),
                "taken": 0,
                "balance": 0,
                "_type": "trip_expense",
                "_bank_code": exp.paid_from_account or "",
            })

    # --- Fuel Incentive (Driver only, Given) ---
    if is_driver and show_fuel_incentive and direction in ("Both", "Given"):
        dc, da = date_sql_cond("date")
        mode_cond = ""
        if payment_mode_f != "All":
            mode_cond = "AND driver_payment_mode = %s"
            da.append(payment_mode_f)
        bank_cond = ""
        if bank_filter:
            bank_cond = "AND driver_bank_name = %s"
            da.append(bank_filter)

        fuel_rows = frappe.db.sql(f"""
            SELECT
                name, date, vehicle, expense_amount,
                driver_payment_mode, driver_bank_name
            FROM `tabFuel Urea Expenses`
            WHERE driver_id = %s
              AND name LIKE 'FUEL-%%'
              AND docstatus != 2
              {dc} {mode_cond} {bank_cond}
            ORDER BY date ASC
        """, [employee_link] + da, as_dict=True)

        for fuel in fuel_rows:
            rows.append({
                "date": fuel.date,
                "category": "Fuel Incentive",
                "description": f"Fuel Incentive — {fuel.vehicle or fuel.name}",
                "reference": fuel.name,
                "ref_doctype": "Fuel Urea Expenses",
                "payment_mode": fuel.driver_payment_mode or "",
                "bank_account": _resolve_bank_name(ah_map, fuel.driver_bank_name),
                "given": flt(fuel.expense_amount),
                "taken": 0,
                "balance": 0,
                "_type": "fuel_incentive",
                "_bank_code": fuel.driver_bank_name or "",
            })

    # --- Staff Payroll net salary (Given) ---
    if show_payroll and direction in ("Both", "Given"):
        party_field = "driver" if is_driver else "employee"
        dc, da = date_sql_cond("payroll_date")
        mode_cond = ""
        if payment_mode_f != "All":
            mode_cond = "AND payment_mode = %s"
            da.append(payment_mode_f)
        # Staff Payroll bank_account links to Bank Account, not Account Head — skip bank_filter here

        payrolls = frappe.db.sql(f"""
            SELECT
                name, payroll_date, net_salary, payment_mode, bank_account,
                from_date, to_date
            FROM `tabStaff Payroll`
            WHERE {party_field} = %s
              AND docstatus = 1
              {dc} {mode_cond}
            ORDER BY payroll_date ASC
        """, [employee_link] + da, as_dict=True)

        for pr in payrolls:
            bank_display = _resolve_bank_name(ah_map, pr.bank_account)
            if bank_filter and pr.bank_account != bank_filter:
                continue
            period = ""
            if pr.from_date and pr.to_date:
                period = f" ({pr.from_date} to {pr.to_date})"
            rows.append({
                "date": pr.payroll_date,
                "category": "Staff Payroll",
                "description": f"Net Salary{period}",
                "reference": pr.name,
                "ref_doctype": "Staff Payroll",
                "payment_mode": pr.payment_mode or "",
                "bank_account": bank_display,
                "given": flt(pr.net_salary),
                "taken": 0,
                "balance": 0,
                "_type": "payroll",
                "_bank_code": pr.bank_account or "",
            })

    # Sort by date
    rows.sort(key=lambda r: str(r["date"] or ""))

    # Assign serial numbers (TOTAL row gets none)
    for i, row in enumerate(rows, start=1):
        row["sr_no"] = i

    # --- Opening advance balance (all advances given/recovered BEFORE from_date) ---
    # This ensures the running balance in rows is always correct even with a date range filter
    party_field  = "driver" if is_driver else "employee"
    advance_type = "Driver Advance" if is_driver else "Employee Advance"

    opening_adv_given  = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(amount), 0) FROM `tabPayment`
        WHERE {party_field} = %s AND type = %s AND docstatus = 1
          {("AND date < %s" if from_date else "")}
    """, [employee_link, advance_type] + ([from_date] if from_date else []))[0][0])

    opening_adv_taken  = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(par.recovery_amount), 0)
        FROM `tabPayroll Advance Recovery` par
        INNER JOIN `tabStaff Payroll` sp ON sp.name = par.parent
        WHERE sp.{party_field} = %s AND sp.docstatus = 1 AND par.recovery_amount > 0
          {("AND sp.payroll_date < %s" if from_date else "")}
    """, [employee_link] + ([from_date] if from_date else []))[0][0])

    opening_balance = opening_adv_given - opening_adv_taken

    # --- All-time advance balance (for summary card, ignores date filter) ---
    all_adv_given = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(amount), 0) FROM `tabPayment`
        WHERE {party_field} = %s AND type = %s AND docstatus = 1
    """, (employee_link, advance_type))[0][0])

    all_adv_taken = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(par.recovery_amount), 0)
        FROM `tabPayroll Advance Recovery` par
        INNER JOIN `tabStaff Payroll` sp ON sp.name = par.parent
        WHERE sp.{party_field} = %s AND sp.docstatus = 1 AND par.recovery_amount > 0
    """, (employee_link,))[0][0])

    total_adv_balance = all_adv_given - all_adv_taken  # true outstanding advance

    # Running balance — ONLY on advance rows; starts from opening balance
    advance_types    = {"advance_given", "advance_taken"}
    running_adv_balance = opening_balance
    for row in rows:
        if row["_type"] in advance_types:
            running_adv_balance += flt(row["given"]) - flt(row["taken"])
            row["balance"] = running_adv_balance
        else:
            row["balance"] = None  # earnings — no balance

    total_given = sum(flt(r["given"]) for r in rows)
    total_taken = sum(flt(r["taken"]) for r in rows)

    summary = []
    if direction in ("Both", "Given"):
        summary.append({"label": _("Total Given"),     "value": total_given,      "datatype": "Currency", "indicator": "blue"})
    if direction in ("Both", "Taken"):
        summary.append({"label": _("Total Recovered"), "value": total_taken,      "datatype": "Currency", "indicator": "green"})
    if direction == "Both" and (all_adv_given or all_adv_taken):
        summary.append({
            "label": _("Advance Balance (Outstanding)"),
            "value": total_adv_balance,
            "datatype": "Currency",
            "indicator": "red" if total_adv_balance > 0 else "green",
        })

    if rows:
        rows.append({
            "sr_no": None,
            "date": None,
            "category": "",
            "description": "",
            "reference": "", "ref_doctype": "",
            "payment_mode": "", "bank_account": "TOTAL",
            "given": total_given,
            "taken": total_taken,
            "balance": total_adv_balance if direction == "Both" else None,
            "_type": "total", "bold": 1,
        })

    return rows, summary
