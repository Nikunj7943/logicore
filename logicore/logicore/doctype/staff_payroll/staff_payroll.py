import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate, get_first_day, get_last_day, add_days
from datetime import datetime
import calendar
from frappe.model.document import Document

OLD_DATA_IMPORT_MARKER = "TMS_OLD_DATA_IMPORT"


def _has_old_data_import_marker(name):
    if not name:
        return False
    return bool(
        frappe.db.exists(
            "Comment",
            {
                "reference_doctype": "Staff Payroll",
                "reference_name": name,
                "comment_type": "Info",
                "content": ["like", f"%{OLD_DATA_IMPORT_MARKER}%"],
            },
        )
    )



@frappe.whitelist()
def get_driver_fuel_incentive(driver, from_date, to_date):
    if not (driver and from_date and to_date):
        return 0
    total = frappe.db.sql("""
        SELECT COALESCE(SUM(expense_amount), 0)
        FROM `tabFuel Urea Expenses`
        WHERE driver_id = %s
          AND date >= %s
          AND date <= %s
          AND name LIKE 'FUEL-%%'
          AND docstatus = 1
    """, (driver, from_date, to_date))[0][0]
    return flt(total)


@frappe.whitelist()
def get_driver_fuel_incentive_details(driver, from_date, to_date):
    """Return only FUEL- prefixed Fuel Urea Expenses records for the driver in the given period."""
    if not (driver and from_date and to_date):
        return []
    rows = frappe.db.sql("""
        SELECT
            name,
            date,
            vehicle,
            expense_amount,
            payment_reference
        FROM `tabFuel Urea Expenses`
        WHERE driver_id = %s
          AND date >= %s
          AND date <= %s
          AND name LIKE 'FUEL-%%'
          AND docstatus = 1
          AND expense_amount > 0
        ORDER BY date ASC
    """, (driver, from_date, to_date), as_dict=True)
    return rows


@frappe.whitelist()
def get_driver_trip_expense_details(driver, from_date, to_date):
    """Return Driver Trip Expense Payment records for the driver in the given period."""
    if not (driver and from_date and to_date):
        return []
    rows = frappe.db.sql("""
        SELECT
            name,
            date,
            amount,
            payment_reference
        FROM `tabPayment`
        WHERE driver = %s
          AND type = 'Driver Trip Expense'
          AND date >= %s
          AND date <= %s
          AND docstatus != 2
        ORDER BY date ASC
    """, (driver, from_date, to_date), as_dict=True)
    return rows


@frappe.whitelist()
def get_employee_incentive_details(employee, from_date, to_date):
    """Return Employee Incentive Payment records for the employee in the given period."""
    if not (employee and from_date and to_date):
        return []
    rows = frappe.db.sql("""
        SELECT
            name,
            date,
            amount,
            payment_reference
        FROM `tabPayment`
        WHERE employee = %s
          AND type = 'Employee Incentive'
          AND date >= %s
          AND date <= %s
          AND docstatus != 2
        ORDER BY date ASC
    """, (employee, from_date, to_date), as_dict=True)
    return rows


@frappe.whitelist()
def get_employee_lr_money_details(employee, from_date, to_date, company=None):
    """Return Trip rows that carry Employee LR Money for the employee in the period."""
    if not (employee and from_date and to_date):
        return []

    conditions = [
        "t.trip_coordinator = %s",
        "t.tcntrip_date >= %s",
        "t.tcntrip_date <= %s",
        "t.docstatus != 2",
        "COALESCE(t.employee_lr_money, 0) > 0",
    ]
    values = [employee, from_date, to_date]
    if company:
        conditions.append("t.company = %s")
        values.append(company)

    rows = frappe.db.sql(f"""
        SELECT
            t.name,
            t.tcntrip_date AS trip_date,
            t.tcntrip_no,
            t.lr_no,
            t.vehicle_no,
            t.vehicle_market,
            t.origin_city,
            t.destination_city_1,
            t.employee_lr_money AS amount,
            vp_latest.vendor_payment,
            vp_latest.vendor
        FROM `tabTrip` t
        LEFT JOIN (
            SELECT trip, vendor_payment, vendor
            FROM (
                SELECT
                    vpt.trip AS trip,
                    vp.name AS vendor_payment,
                    vp.vendor AS vendor,
                    ROW_NUMBER() OVER (
                        PARTITION BY vpt.trip
                        ORDER BY vp.payment_date DESC, vp.modified DESC
                    ) AS rn
                FROM `tabVendor Payment Trip` vpt
                INNER JOIN `tabVendor Payment` vp ON vp.name = vpt.parent
                WHERE vp.docstatus = 1
                  AND COALESCE(vpt.employee_lr_money, 0) > 0
            ) ranked
            WHERE ranked.rn = 1
        ) vp_latest ON vp_latest.trip = t.name
        WHERE {" AND ".join(conditions)}
        ORDER BY t.tcntrip_date ASC, t.name ASC
    """, tuple(values), as_dict=True)
    return rows


@frappe.whitelist()
def get_driver_advances(driver, exclude_payroll=None, until_date=None):
    if not driver:
        return []
    filters = {"driver": driver, "type": "Driver Advance", "docstatus": 1}
    if until_date:
        filters["date"] = ["<=", until_date]
    advances = frappe.db.get_all(
        "Payment",
        filters=filters,
        fields=["name", "date", "amount"],
        order_by="date asc",
    )
    result = []
    for adv in advances:
        already_recovered = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(par.recovery_amount), 0)
            FROM `tabPayroll Advance Recovery` par
            INNER JOIN `tabStaff Payroll` sp ON sp.name = par.parent
            WHERE par.payment_ref = %s
              AND sp.docstatus = 1
              AND (%s IS NULL OR sp.name != %s)
        """, (adv.name, exclude_payroll, exclude_payroll))[0][0])
        total_advance = flt(adv.amount)
        effective_recovered = min(total_advance, already_recovered)
        outstanding = max(0, total_advance - effective_recovered)
        # Fully recovered advances have nothing left to deduct — only rows with
        # a pending balance are shown.
        if outstanding <= 0:
            continue
        result.append({
            "payment_ref": adv.name,
            "advance_date": adv.date,
            "total_advance": total_advance,
            "already_recovered": effective_recovered,
            "outstanding": outstanding,
            "recovery_amount": outstanding,
        })
    return result


@frappe.whitelist()
def get_employee_advances(employee, exclude_payroll=None, until_date=None):
    if not employee:
        return []
    filters = {"employee": employee, "type": "Employee Advance", "docstatus": 1}
    if until_date:
        filters["date"] = ["<=", until_date]
    advances = frappe.db.get_all(
        "Payment",
        filters=filters,
        fields=["name", "date", "amount"],
        order_by="date asc",
    )
    result = []
    for adv in advances:
        already_recovered = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(par.recovery_amount), 0)
            FROM `tabPayroll Advance Recovery` par
            INNER JOIN `tabStaff Payroll` sp ON sp.name = par.parent
            WHERE par.payment_ref = %s
              AND sp.docstatus = 1
              AND (%s IS NULL OR sp.name != %s)
        """, (adv.name, exclude_payroll, exclude_payroll))[0][0])
        total_advance = flt(adv.amount)
        effective_recovered = min(total_advance, already_recovered)
        outstanding = max(0, total_advance - effective_recovered)
        # Fully recovered advances have nothing left to deduct — only rows with
        # a pending balance are shown.
        if outstanding <= 0:
            continue
        result.append({
            "payment_ref": adv.name,
            "advance_date": adv.date,
            "total_advance": total_advance,
            "already_recovered": effective_recovered,
            "outstanding": outstanding,
            "recovery_amount": outstanding,
        })
    return result


# Earning/deduction component lists used to be hardcoded here (see git history
# for the old EMPLOYEE_EARNING_TYPES / EMPLOYEE_DEDUCTION_TYPES /
# DRIVER_EARNING_TYPES / DRIVER_DEDUCTION_TYPES lists). They now come live
# from the linked Salary Structure's own earnings/deductions rows, so adding
# or renaming a component in the Salary Structure master is reflected here
# automatically — no code change needed.

# Old name-based mapping (structure had to be literally named "Employee
# Salary Structure" / "Driver Salary Structure", or the fallback silently
# broke on rename). Replaced by the `custom_tms_salary_type` Select field on
# Salary Structure itself — any structure can carry any name now.
# DEFAULT_SALARY_STRUCTURE = {
#     "Employee Salary": "Employee Salary Structure",
#     "Driver Salary": "Driver Salary Structure",
# }


def get_default_salary_structure(salary_type):
    """Active, submitted Salary Structure tagged with this salary_type via
    the custom_tms_salary_type field. None if none is set up yet."""
    return frappe.db.get_value(
        "Salary Structure",
        {"custom_tms_salary_type": salary_type, "is_active": "Yes", "docstatus": 1},
        "name",
    )


def get_salary_structure_components(salary_type, salary_structure=None):
    """Component names (in Salary Structure row order) for the given salary
    type, read from `salary_structure` if set, else the default structure for
    that salary type. Returns {} for both lists if the structure doesn't exist
    yet (e.g. master data not set up)."""
    structure_name = salary_structure or get_default_salary_structure(salary_type)
    if not structure_name or not frappe.db.exists("Salary Structure", structure_name):
        return {"earnings": [], "deductions": []}
    return {
        "earnings": frappe.get_all(
            "Salary Detail",
            filters={"parent": structure_name, "parenttype": "Salary Structure", "parentfield": "earnings"},
            pluck="salary_component",
            order_by="idx",
        ),
        "deductions": frappe.get_all(
            "Salary Detail",
            filters={"parent": structure_name, "parenttype": "Salary Structure", "parentfield": "deductions"},
            pluck="salary_component",
            order_by="idx",
        ),
    }


@frappe.whitelist()
def get_salary_structure_component_types(salary_type, salary_structure=None):
    return get_salary_structure_components(salary_type, salary_structure)


@frappe.whitelist()
def is_old_data_import_doc(name):
    return _has_old_data_import_marker(name)


class StaffPayroll(Document):
    """Staff Payroll DocType with auto-fetch attendance and employee details"""

    @property
    def earning_types(self):
        return get_salary_structure_components(self.salary_type, self.salary_structure)["earnings"]

    @property
    def deduction_types(self):
        return get_salary_structure_components(self.salary_type, self.salary_structure)["deductions"]

    def validate(self):
        """Validate payroll data"""
        self._infer_salary_type_from_person()
        self._fetch_person_details()
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                frappe.throw(_("From Date must be less than To Date"))
            self.calculate_period()

        self.update_salary_components()
        self.calculate_earnings_deductions()
        if self._is_old_data_import():
            self._reorder_component_rows_for_old_import()
        self._validate_transaction_id_unique()

        # Check status before submission
        #if self.docstatus == 1 and self.approval_status != "Approved":
         #   frappe.throw(_("Payroll must be approved before submission"))

    def _validate_transaction_id_unique(self):
        if not self.transaction_id:
            return
        duplicate = frappe.db.get_value(
            "Staff Payroll",
            {"transaction_id": self.transaction_id, "name": ("!=", self.name or "")},
            "name",
        )
        if duplicate:
            frappe.throw(_("Transaction ID {0} already used in {1}.").format(self.transaction_id, duplicate))

    def on_submit(self):
        """Update status on submission"""
        self.status = "Processed"
        self.db_set("status", "Processed")

    def on_cancel(self):
        """Update status on cancellation"""
        self.status = "Cancelled"
        self.db_set("status", "Cancelled")

    def before_validate(self):
        """Import-only. validate() (which computes attendance-driven salary
        components) runs BEFORE before_save() in Frappe's save lifecycle, so
        the import-only auto-fetch must happen here — doing it in
        before_save() would populate attendance/advances too late for
        validate()'s calculations to see them. Manual desk-form saves and
        API calls never set frappe.flags.in_import, so this is a no-op for
        every path except Frappe's standard Data Import — manual entry
        behaviour is completely unchanged."""
        if not (self.is_new() and frappe.flags.in_import):
            return
        self._infer_salary_type_from_person()
        self._apply_field_defaults_for_import()
        if not self.payment_date:
            self.payment_date = self.payroll_date
        self._fetch_person_details()
        self._auto_fetch_attendance_on_create()
        self._auto_fetch_advances_on_create()
        # validate()'s calculate_earnings_deductions() runs right after this
        # and sums deductions_table as it stands now — the "Advances" row
        # must already reflect the fetched advances before that happens.
        self._sync_advance_recovery_to_deductions()

    def before_insert(self):
        """Populate master-driven fields early so mandatory validation can
        see them during create/import."""
        self._infer_salary_type_from_person()
        self._fetch_person_details()
        if not self.payment_date:
            self.payment_date = self.payroll_date

    def before_save(self):
        """Auto-populate fields when employee or driver is selected"""
        self._fetch_person_details()
        self._sync_advance_recovery_to_deductions()
        self._update_advance_already_recovered()

    def _is_old_data_import(self):
        return bool(
            getattr(self, "_tms_old_data_import", False)
            or getattr(self.flags, "tms_old_data_import", False)
            or _has_old_data_import_marker(self.name)
        )

    def _fetch_person_details(self):
        if self.salary_type == "Driver Salary":
            if not self.driver:
                frappe.throw(_("Please select a Driver for Driver Salary type."))
            if self.driver:
                driver = frappe.db.get_value("Driver", self.driver, ["full_name", "name", "custom_ctc", "custom_company", "custom_branch"], as_dict=True)
                if driver:
                    if not self.employee_name:
                        self.employee_name = driver.full_name or driver.name
                    if flt(driver.custom_ctc) > 0:
                        if not self.ctc:
                            self.ctc = driver.custom_ctc
                    else:
                        frappe.throw(
                            _("Salary/CTC is missing in the Driver master for {0}. Please set it before importing Staff Payroll.").format(
                                frappe.bold(self.driver)
                            )
                        )
                    if not self.company and driver.custom_company:
                        self.company = driver.custom_company
                    if not self.branch and driver.custom_branch:
                        self.branch = driver.custom_branch
                    if not self.salary_structure:
                        self.salary_structure = get_default_salary_structure(self.salary_type)
        else:
            if self.employee:
                self.fetch_employee_details()

    def _apply_field_defaults_for_import(self):
        """Import-only (see before_validate). Frappe skips
        Document._set_defaults() entirely while frappe.flags.in_import is
        set (e.g. Series/naming_series, Payment Mode both have static
        defaults that would otherwise stay blank and fail mandatory
        validation). Reuse Frappe's own defaulting logic — which already
        knows how to resolve every default type, not just static strings —
        by toggling the flag off just for this call."""
        frappe.flags.in_import = False
        try:
            self._set_defaults()
        finally:
            frappe.flags.in_import = True

    def _infer_salary_type_from_person(self):
        """Import-only (see before_save). Frappe's standard Data Import
        leaves Salary Type blank rather than defaulting it, since Frappe
        skips field defaults while frappe.flags.in_import is set. Infer it
        from whichever of employee/driver is populated so
        mandatory_depends_on resolves correctly and the right
        earning/deduction template is used."""
        if self.salary_type:
            return
        if self.driver and not self.employee:
            self.salary_type = "Driver Salary"
        elif self.employee and not self.driver:
            self.salary_type = "Employee Salary"

    def _auto_fetch_attendance_on_create(self):
        """Import-only (see before_save). Populates attendance fields for
        records created via Frappe's standard Data Import, where the
        client-side auto-fetch in staff_payroll.js never runs."""
        person = self.driver if self.salary_type == "Driver Salary" else self.employee
        if not (person and self.from_date and self.to_date):
            return
        self.set_attendance_from_staff_attendance()

    def _auto_fetch_advances_on_create(self):
        """Import-only (see before_save). Populates advance_recovery_table
        for records created via Frappe's standard Data Import — same
        rows/defaults the manual "fetch advance" flow produces."""
        if self.advance_recovery_table:
            return
        if self.salary_type == "Driver Salary":
            if not self.driver:
                return
            advances = get_driver_advances(self.driver, until_date=self.payroll_date if frappe.flags.in_import else None)
        else:
            if not self.employee:
                return
            advances = get_employee_advances(self.employee, until_date=self.payroll_date if frappe.flags.in_import else None)
        for adv in advances:
            self.append("advance_recovery_table", {
                "payment_ref": adv["payment_ref"],
                "advance_date": adv["advance_date"],
                "total_advance": adv["total_advance"],
                "already_recovered": adv["already_recovered"],
                "outstanding": adv["outstanding"],
                "recovery_amount": adv["recovery_amount"],
            })

    def _sync_advance_recovery_to_deductions(self):
        total_recovery = sum(flt(row.recovery_amount) for row in (self.advance_recovery_table or []))
        for row in (self.deductions_table or []):
            if row.salary_component == "Advances":
                if self._is_old_data_import():
                    return
                row.amount = total_recovery
                return
        if total_recovery > 0:
            self.append("deductions_table", {"salary_component": "Advances", "amount": total_recovery})

    def _reorder_component_rows_for_old_import(self):
        """Keep imported rows aligned to the linked Salary Structure order."""
        earning_order = {component: idx for idx, component in enumerate(self.earning_types or [], start=1)}
        deduction_order = {component: idx for idx, component in enumerate(self.deduction_types or [], start=1)}

        def _sort_key(row, order_map):
            return (order_map.get(cstr(row.salary_component), 999), cstr(row.salary_component), getattr(row, "idx", 0))

        if self.earnings_table:
            self.earnings_table = sorted(self.earnings_table, key=lambda row: _sort_key(row, earning_order))
            for idx, row in enumerate(self.earnings_table, start=1):
                row.idx = idx
        if self.deductions_table:
            self.deductions_table = sorted(self.deductions_table, key=lambda row: _sort_key(row, deduction_order))
            for idx, row in enumerate(self.deductions_table, start=1):
                row.idx = idx

    def _resolve_employee(self):
        if not self.employee:
            return None
        if frappe.db.exists("Employee", self.employee):
            return frappe.get_doc("Employee", self.employee)

        meta = frappe.get_meta("Employee")
        title_field = meta.title_field
        if title_field and title_field != "name":
            matches = frappe.db.get_all("Employee", filters={title_field: self.employee}, pluck="name")
            if len(matches) == 1:
                return frappe.get_doc("Employee", matches[0])
            if len(matches) > 1:
                frappe.throw(
                    _("Multiple Employee records match '{0}'. Please use the exact ID.").format(
                        frappe.bold(self.employee)
                    )
                )
        return None

    def _update_advance_already_recovered(self):
        """Update already_recovered to cumulative (base + recovery_amount) so the grid shows total recovered."""
        if not self.advance_recovery_table:
            return
        for row in self.advance_recovery_table:
            if not row.payment_ref:
                continue
            base_recovered = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(par.recovery_amount), 0)
                FROM `tabPayroll Advance Recovery` par
                INNER JOIN `tabStaff Payroll` sp ON sp.name = par.parent
                WHERE par.payment_ref = %s
                  AND sp.docstatus = 1
                  AND sp.name != %s
            """, (row.payment_ref, self.name or ""))[0][0])
            total = flt(row.total_advance)
            cumulative = min(total, base_recovered + flt(row.recovery_amount))
            row.already_recovered = cumulative
            row.outstanding = max(0, total - cumulative)
    
    def fetch_employee_details(self):
        """Fetch employee details from Employee doctype"""
        employee = self._resolve_employee()
        if not employee:
            frappe.throw(_("Employee {0} was not found.").format(frappe.bold(self.employee)))
        self.employee_name = employee.employee_name
        if flt(employee.ctc) > 0:
            self.ctc = employee.ctc
        else:
            frappe.throw(
                _("Salary/CTC is missing in the Employee master for {0}. Please set it before importing Staff Payroll.").format(
                    frappe.bold(self.employee)
                )
            )
        self.department = employee.department
        self.designation = employee.designation
        self.branch = employee.branch
        self.company = employee.company

        # Fetch salary structure if available
        salary_structure_assignment = frappe.db.get_value(
            "Salary Structure Assignment",
            filters={
                "employee": employee.name,
                "docstatus": 1,
                "from_date": ["<=", self.payroll_date or frappe.utils.today()],
            },
            fieldname="salary_structure",
            order_by="from_date desc",
        )
        if salary_structure_assignment:
            self.salary_structure = salary_structure_assignment[0]
        elif not self.salary_structure:
            self.salary_structure = get_default_salary_structure(self.salary_type)

    def calculate_period(self):
        """Calculate period and salary basis."""
        if not (self.from_date and self.to_date):
            return

        try:
            from_date = getdate(self.from_date)
            to_date = getdate(self.to_date)

            actual_days = (to_date - from_date).days + 1
            # Driver salary always uses 30 days regardless of actual month length
            self.total_days = 30 if self.salary_type == "Driver Salary" else actual_days
            self.working_days = self.total_days
            self.worked_days = flt(self.present_days) + flt(self.leave_with_pay)
            self.salary_per_day = flt(self.ctc) / self.total_days if self.total_days else 0
            
        except Exception as e:
            frappe.msgprint(_("Error calculating period: {0}").format(str(e)))
    
    def fetch_attendance_data(self):
        """Fetch attendance data from Staff Attendance for the employee"""
        try:
            summary = get_attendance_summary(
                self.employee,
                self.from_date,
                self.to_date,
                self.company,
            )
            if summary["message"] == "No attendance records found":
                frappe.msgprint(_("No attendance records found for this period"))
                return
            
            self.present_days = summary["present_days"]
            self.absent_days = summary["absent_days"]
            self.leave_with_pay = summary["leave_with_pay"]
            self.leave_without_pay = summary["leave_without_pay"]
            self.worked_days = summary["worked_days"]
            self.update_salary_components()
            
            frappe.msgprint(
                _("Attendance fetched:<br>Present: {0}<br>Leave with Pay: {1}<br>Leave without Pay: {2}<br>Absent: {3}").format(
                    self.present_days, self.leave_with_pay, self.leave_without_pay, self.absent_days
                ),
                title=_("Attendance Summary")
            )
            
        except Exception as e:
            frappe.msgprint(_("Error fetching attendance data: {0}").format(str(e)))
    
    def set_attendance_from_staff_attendance(self):
        """Update attendance summary from Staff Attendance before calculation."""
        person = self.driver if self.salary_type == "Driver Salary" else self.employee
        if not (person and self.from_date and self.to_date):
            return

        summary = get_attendance_summary(
            person,
            self.from_date,
            self.to_date,
            self.company,
        )
        self.present_days = summary["present_days"]
        self.absent_days = summary["absent_days"]
        self.leave_with_pay = summary["leave_with_pay"]
        self.leave_without_pay = summary["leave_without_pay"]
        self.worked_days = summary["worked_days"]
    
    def update_salary_components(self):
        """Ensure salary rows exist and update formula-driven amounts."""
        old_data_import = self._is_old_data_import()
        # Driver salary always uses 30 days regardless of actual month length
        total_days = 30 if self.salary_type == "Driver Salary" else flt(self.total_days)
        ctc = flt(self.ctc)
        self.salary_per_day = ctc / total_days if total_days else 0
        present = flt(self.present_days)
        lwp = flt(self.leave_with_pay)
        lwop = flt(self.leave_without_pay)
        absent = flt(self.absent_days)
        total_attendance = present + lwp + lwop + absent
        self.total_attendance_days = total_attendance
        self.worked_days = present + lwp
        # Driver Salary always prices a day at ctc/30, so a 31-day calendar
        # month has one more marked attendance day than the pay basis covers —
        # that extra day must not be charged as a leave deduction.
        extra_days = max(0, total_attendance - total_days) if self.salary_type == "Driver Salary" else 0
        lop_days = max(0, lwop - extra_days)
        lop_amount = flt(self.salary_per_day) * lop_days

        # Remove stale earning types that no longer belong to this salary type
        _MOVED_TO_SECTIONS = {"Fuel Incentive", "Trip Expenses"}
        self.earnings_table = [
            row for row in (self.earnings_table or [])
            if row.salary_component not in _MOVED_TO_SECTIONS
        ]

        earning_rows = {row.salary_component: row for row in self.earnings_table or [] if row.salary_component}
        for earning_type in self.earning_types:
            row = earning_rows.get(earning_type)
            is_new_row = row is None
            if not row:
                row = self.append("earnings_table", {
                    "salary_component": earning_type,
                    "amount": 0,
                })
            if old_data_import:
                if row.amount is None:
                    row.amount = 0
                continue
            # The formula only seeds a freshly created row. Once the row exists,
            # its amount is whatever was last saved — a manual edit must survive
            # every re-save. Switching employee/driver/salary_type rebuilds the
            # tables from scratch, which is what brings the formula back.
            if earning_type == "Basic Salary" and is_new_row:
                # row.amount = flt(self.salary_per_day) * flt(self.worked_days)  # prorated: salary_per_day × (present + lwp)
                row.amount = flt(self.ctc)  # master salary flows directly into Basic Salary
            if row.amount is None:
                row.amount = 0

        deduction_rows = {row.salary_component: row for row in self.deductions_table or [] if row.salary_component}
        for deduction_type in self.deduction_types:
            row = deduction_rows.get(deduction_type)
            is_new_row = row is None
            if not row:
                row = self.append("deductions_table", {
                    "salary_component": deduction_type,
                    "amount": 0,
                })
            if old_data_import:
                if row.amount is None:
                    row.amount = 0
                continue
            # Seed-only, same as Basic Salary above — manual edits win.
            if deduction_type == "Leave Deductions" and is_new_row:
                row.amount = lop_amount
            if row.amount is None:
                row.amount = 0
    
    def calculate_earnings_deductions(self):
        """Calculate total earnings and deductions"""
        try:
            total_earnings = 0
            for row in self.earnings_table or []:
                total_earnings += flt(row.amount)
            
            total_deductions = 0
            for row in self.deductions_table or []:
                total_deductions += flt(row.amount)
            
            self.total_earnings = total_earnings
            self.total_deductions = total_deductions
            self.net_salary = total_earnings - total_deductions
            
        except Exception as e:
            frappe.msgprint(_("Error calculating totals: {0}").format(str(e)))


# ============== RPC METHODS (Can be called from JavaScript) ==============

@frappe.whitelist()
def fetch_employee_details(employee):
    """RPC method to fetch employee details
    
    Called from JavaScript when employee is selected
    
    Args:
        employee: Employee ID/name
    
    Returns:
        dict with employee details
    """
    try:
        emp = frappe.get_doc("Employee", employee)
        
        # Get salary structure
        salary_structure = frappe.db.get_value(
            "Salary Structure Assignment",
            filters={
                "employee": employee,
                "docstatus": 1,
                "from_date": ["<=", frappe.utils.today()]
            },
            fieldname="salary_structure",
            order_by="from_date desc"
        )
        
        return {
            "employee_name": emp.employee_name,
            "ctc": emp.ctc or 0,
            "department": emp.department,
            "designation": emp.designation,
            "branch": emp.branch,
            "company": emp.company,
            "salary_structure": salary_structure[0] if salary_structure else None
        }
    except Exception as e:
        frappe.throw(_("Error: {0}").format(str(e)))


@frappe.whitelist()
def fetch_attendance_for_period(employee, from_date, to_date, company):
    """RPC method to fetch attendance for date range
    
    Called from JavaScript "Fetch Attendance" button
    
    Args:
        employee: Employee ID
        from_date: Start date
        to_date: End date  
        company: Company ID
    
    Returns:
        dict with attendance summary
    """
    try:
        return get_attendance_summary(employee, from_date, to_date, company)
    except Exception as e:
        frappe.throw(_("Error fetching attendance: {0}").format(str(e)))


def get_attendance_summary(employee, from_date, to_date, company=None):
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    
    conditions = [
        "sa.date >= %(from_date)s",
        "sa.date <= %(to_date)s",
        "sad.employee_link = %(employee)s",
    ]
    values = {
        "from_date": from_date,
        "to_date": to_date,
        "employee": employee,
    }
    if company:
        conditions.append("sa.company = %(company)s")
        values["company"] = company
    
    attendance_records = frappe.db.sql(
        """
        select sad.status
        from `tabStaff Attendance Detail` sad
        inner join `tabStaff Attendance` sa on sa.name = sad.parent
        where {conditions}
        """.format(conditions=" and ".join(conditions)),
        values,
        as_dict=True,
    )
    
    if not attendance_records:
        return {
            "present_days": 0,
            "absent_days": 0,
            "leave_with_pay": 0,
            "leave_without_pay": 0,
            "worked_days": 0,
            "message": "No attendance records found"
        }
    
    # "Sunday/Holiday" days are paid like Present — count them as present so
    # they're included in worked_days (prorated Basic Salary), not dropped.
    present = sum(1 for r in attendance_records if r.status in ("Present", "Sunday/Holiday"))
    # "Absent" is now treated the same as "On Leave Without Pay" for payroll —
    # both trigger the Leave Deductions amount. absent_days stays 0 so the
    # total_attendance_days = present + lwp + lwop + absent formula below
    # doesn't double-count these days.
    absent = 0
    leave_with_pay = sum(1 for r in attendance_records if r.status == "On Leave With Pay")
    leave_without_pay = sum(1 for r in attendance_records if r.status in ("On Leave Without Pay", "Absent"))

    return {
        "present_days": present,
        "absent_days": absent,
        "leave_with_pay": leave_with_pay,
        "leave_without_pay": leave_without_pay,
        "worked_days": present + leave_with_pay,
        "message": "Attendance fetched successfully"
    }


def get_attendance_date_summary(payroll_name):
    """Return attendance dates grouped by status for salary slip print formats."""
    payroll = frappe.get_doc("Staff Payroll", payroll_name)
    if not (payroll.employee and payroll.from_date and payroll.to_date):
        return {
            "Present": [],
            "On Leave With Pay": [],
            "On Leave Without Pay": [],
            "Absent": [],
        }
    
    conditions = [
        "sa.date >= %(from_date)s",
        "sa.date <= %(to_date)s",
        "sad.employee_link = %(employee)s",
    ]
    values = {
        "from_date": getdate(payroll.from_date),
        "to_date": getdate(payroll.to_date),
        "employee": payroll.employee,
    }
    if payroll.company:
        conditions.append("sa.company = %(company)s")
        values["company"] = payroll.company
    
    rows = frappe.db.sql(
        """
        select sa.date, sad.status
        from `tabStaff Attendance Detail` sad
        inner join `tabStaff Attendance` sa on sa.name = sad.parent
        where {conditions}
        order by sa.date
        """.format(conditions=" and ".join(conditions)),
        values,
        as_dict=True,
    )
    
    summary = {
        "Present": [],
        "On Leave With Pay": [],
        "On Leave Without Pay": [],
        "Absent": [],
    }
    for row in rows:
        # Sunday/Holiday is paid like Present (see get_attendance_summary) —
        # list it under Present for print consistency with that count.
        status = "Present" if row.status == "Sunday/Holiday" else row.status
        if status in summary:
            summary[status].append(frappe.utils.formatdate(row.date, "dd-MMM-yy"))

    return summary


@frappe.whitelist()
def approve_payroll(payroll_name, approved_by=None):
    """RPC method to approve payroll
    
    Called from JavaScript "Approve" button
    
    Args:
        payroll_name: Staff Payroll document name
        approved_by: User approving (defaults to current user)
    
    Returns:
        Success message
    """
    try:
        if not approved_by:
            approved_by = frappe.session.user
        
        payroll = frappe.get_doc("Staff Payroll", payroll_name)
        payroll.approval_status = "Approved"
        payroll.approved_by = approved_by
        payroll.approved_date = frappe.utils.now()
        payroll.status = "Approved"
        payroll.save()
        
        return {
            "message": "Payroll approved successfully",
            "status": "success"
        }
    except Exception as e:
        frappe.throw(_("Error approving payroll: {0}").format(str(e)))
