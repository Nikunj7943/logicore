# Staff Payroll Attendance/Advance Auto-Fetch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make bulk-imported Staff Payroll records (via Frappe's standard Data Import, and manual creation) auto-fetch attendance and outstanding advances on insert, identical to what the desk form's JS buttons produce today.

**Architecture:** Move the attendance-summary fetch and advance-recovery fetch — currently only triggered by client-side JS (`staff_payroll.js`) — into `staff_payroll.py`'s existing `before_save()` controller hook, guarded to run only on document creation (`self.is_new()`). Since every creation path (manual form save, Frappe's standard Data Import, and any future custom import) calls `doc.insert()`, all of them get this for free without per-tool code.

**Tech Stack:** Frappe Framework v15, Python, `IntegrationTestCase` (`bench run-tests`).

## Global Constraints

- Site name for all commands: `logicore.com`.
- Run tests with: `bench --site logicore.com run-tests --doctype "Staff Payroll"`.
- No `.json` schema changes in this plan, so no `bench migrate` needed.
- Do not run `bench migrate` / `bench --site logicore.com clear-cache` — the user runs these manually themselves.
- Never delete existing code — comment it out if it must be removed (this repo's convention; not applicable here since no removals are needed).
- Do not run `git commit`/`git add`/`git push` — the user commits manually.
- Minimal changes only — do not refactor unrelated code in `staff_payroll.py`.

---

### Task 1: Salary Type inference + attendance/advance auto-fetch for Driver Salary on create

**Files:**
- Modify: `apps/logicore/logicore/logicore/doctype/staff_payroll/staff_payroll.py:196-226` (the `before_save` method)
- Test: `apps/logicore/logicore/logicore/doctype/staff_payroll/test_staff_payroll.py`

**Interfaces:**
- Consumes: existing module-level functions `get_driver_advances(driver, exclude_payroll=None)` and `get_employee_advances(employee, exclude_payroll=None)` (staff_payroll.py:73, :107) — each returns a list of dicts with keys `payment_ref`, `advance_date`, `total_advance`, `already_recovered`, `outstanding`, `recovery_amount`. Existing method `StaffPayroll.set_attendance_from_staff_attendance()` (staff_payroll.py:323) — no args, reads `self.driver`/`self.employee`/`self.from_date`/`self.to_date`/`self.company`, sets `self.present_days`, `self.absent_days`, `self.leave_with_pay`, `self.leave_without_pay`, `self.worked_days`.
- Produces: new `StaffPayroll` methods `_infer_salary_type_from_person()`, `_auto_fetch_attendance_on_create()`, `_auto_fetch_advances_on_create()` — used only internally by `before_save()`, no other task depends on calling them directly.

- [ ] **Step 1: Write the failing test**

Replace the full contents of `test_staff_payroll.py` with:

```python
# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestStaffPayroll(IntegrationTestCase):
	"""
	Integration tests for StaffPayroll.
	Use this class for testing interactions between multiple components.
	"""

	def _get_company(self):
		company = frappe.db.get_value("Company", {}, "name")
		self.assertTrue(company, "No Company found in the test site — required for Staff Payroll tests")
		return company

	def _make_driver(self, company, ctc=300000):
		driver = frappe.get_doc({
			"doctype": "Driver",
			"full_name": "Test Import Driver",
			"custom_ctc": ctc,
			"custom_company": company,
		})
		driver.insert(ignore_permissions=True)
		return driver

	def _make_staff_attendance(self, company, link_doctype, person_name, date, status):
		att = frappe.get_doc({
			"doctype": "Staff Attendance",
			"date": date,
			"company": company,
			"attendance_details": [{
				"link_doctype": link_doctype,
				"employee_link": person_name,
				"status": status,
			}],
		})
		att.insert(ignore_permissions=True)
		return att

	def _make_driver_advance(self, company, driver_name, amount, date):
		payment = frappe.get_doc({
			"doctype": "Payment",
			"date": date,
			"type": "Driver Advance",
			"company": company,
			"mode_of_payment": "Cash",
			"driver": driver_name,
			"amount": amount,
		})
		payment.insert(ignore_permissions=True)
		payment.submit()
		return payment

	def test_driver_salary_auto_fetches_attendance_and_advance_on_import(self):
		company = self._get_company()
		driver = self._make_driver(company, ctc=300000)

		from_date = add_days(today(), -2)
		mid_date = add_days(today(), -1)
		to_date = today()
		self._make_staff_attendance(company, "Driver", driver.name, from_date, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, mid_date, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, to_date, "Absent")

		advance = self._make_driver_advance(company, driver.name, 5000, add_days(today(), -10))

		# Simulates what Frappe's standard Data Import produces: only the
		# person + period, no salary_type, no ctc/company, no attendance,
		# no advance rows — everything else must come from auto-fetch.
		payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": from_date,
			"to_date": to_date,
			"payroll_date": to_date,
			"payment_mode": "Bank Transfer",
		})
		payroll.insert(ignore_permissions=True)

		self.assertEqual(payroll.salary_type, "Driver Salary")
		self.assertEqual(payroll.company, company)
		self.assertEqual(payroll.ctc, 300000)
		self.assertEqual(payroll.present_days, 2)
		self.assertEqual(payroll.absent_days, 1)
		self.assertEqual(payroll.worked_days, 2)

		self.assertEqual(len(payroll.advance_recovery_table), 1)
		row = payroll.advance_recovery_table[0]
		self.assertEqual(row.payment_ref, advance.name)
		self.assertEqual(row.total_advance, 5000)
		self.assertEqual(row.outstanding, 5000)
		self.assertEqual(row.recovery_amount, 5000)

		basic_salary_row = next(r for r in payroll.earnings_table if r.earning_type == "Basic Salary")
		self.assertEqual(basic_salary_row.amount, 20000)  # (300000 / 30 fixed days) * 2 worked days

		advances_row = next(r for r in payroll.deductions_table if r.deduction_type == "Advances")
		self.assertEqual(advances_row.amount, 5000)

		self.assertEqual(payroll.net_salary, 15000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bench --site logicore.com run-tests --doctype "Staff Payroll"`
Expected: FAIL — the created `payroll` doc will have `salary_type` empty/wrong (no driver-detail fetch happens because `before_save`'s `if self.salary_type == "Driver Salary"` branch never matches when salary_type is blank), so `payroll.company`/`payroll.ctc` will be `None`/`0`, and likely a `MandatoryError` on `insert()` for blank `company`/`ctc`, or `AssertionError` on the `present_days`/`advance_recovery_table` assertions if it does insert.

- [ ] **Step 3: Write minimal implementation**

Replace `staff_payroll.py` lines 196-226 (the current `before_save`, `_sync_advance_recovery_to_deductions`, and the start of `_update_advance_already_recovered` — i.e. everything from `def before_save(self):` through the end of `_sync_advance_recovery_to_deductions`) with:

```python
    def before_save(self):
        """Auto-populate fields when employee or driver is selected"""
        self._infer_salary_type_from_person()

        if self.salary_type == "Driver Salary":
            if not self.driver:
                frappe.throw(_("Please select a Driver for Driver Salary type."))
            if self.driver:
                driver = frappe.db.get_value("Driver", self.driver, ["full_name", "name", "custom_ctc", "custom_company", "custom_branch"], as_dict=True)
                if driver:
                    if not self.employee_name:
                        self.employee_name = driver.full_name or driver.name
                    if not self.ctc and driver.custom_ctc:
                        self.ctc = driver.custom_ctc
                    if not self.company and driver.custom_company:
                        self.company = driver.custom_company
                    if not self.branch and driver.custom_branch:
                        self.branch = driver.custom_branch
        else:
            if self.employee and not self.employee_name:
                self.fetch_employee_details()

        if self.is_new():
            self._auto_fetch_attendance_on_create()
            self._auto_fetch_advances_on_create()

        self._sync_advance_recovery_to_deductions()
        self._update_advance_already_recovered()

    def _infer_salary_type_from_person(self):
        """Bulk imports (Frappe's standard Data Import in particular) leave
        Salary Type blank rather than defaulting it, since Frappe skips field
        defaults while frappe.flags.in_import is set. Infer it from whichever
        of employee/driver is populated so mandatory_depends_on resolves
        correctly and the right earning/deduction template is used."""
        if self.salary_type:
            return
        if self.driver and not self.employee:
            self.salary_type = "Driver Salary"
        elif self.employee and not self.driver:
            self.salary_type = "Employee Salary"

    def _auto_fetch_attendance_on_create(self):
        """Populate attendance fields on new records created without a
        browser open (bulk import) — the client-side auto-fetch in
        staff_payroll.js never runs there."""
        person = self.driver if self.salary_type == "Driver Salary" else self.employee
        if not (person and self.from_date and self.to_date):
            return
        self.set_attendance_from_staff_attendance()

    def _auto_fetch_advances_on_create(self):
        """Populate advance_recovery_table on new records created without a
        browser open (bulk import) — same rows/defaults the manual "fetch
        advance" flow produces."""
        if self.advance_recovery_table:
            return
        if self.salary_type == "Driver Salary":
            if not self.driver:
                return
            advances = get_driver_advances(self.driver)
        else:
            if not self.employee:
                return
            advances = get_employee_advances(self.employee)
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
            if row.deduction_type == "Advances":
                row.amount = total_recovery
                return
        if total_recovery > 0:
            self.append("deductions_table", {"deduction_type": "Advances", "amount": total_recovery})
```

Note this only replaces `before_save` and `_sync_advance_recovery_to_deductions` — leave `_update_advance_already_recovered` (staff_payroll.py:227 onward in the original file) exactly as it is; it already follows immediately after `_sync_advance_recovery_to_deductions` in the file.

- [ ] **Step 4: Run test to verify it passes**

Run: `bench --site logicore.com run-tests --doctype "Staff Payroll"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/logicore/logicore/logicore/doctype/staff_payroll/staff_payroll.py apps/logicore/logicore/logicore/doctype/staff_payroll/test_staff_payroll.py
git commit -m "feat(staff-payroll): auto-fetch attendance and advances on bulk-import create"
```

(Skip this step if the user has said they will commit manually themselves.)

---

### Task 2: Employee Salary path — same auto-fetch, different link field

**Files:**
- Modify: `apps/logicore/logicore/logicore/doctype/staff_payroll/test_staff_payroll.py` (add to the class from Task 1 — no production code changes expected, this task proves the `else` branch of the Task 1 implementation)

**Interfaces:**
- Consumes: same as Task 1 — `get_employee_advances`, `set_attendance_from_staff_attendance`, `_infer_salary_type_from_person`, `_auto_fetch_attendance_on_create`, `_auto_fetch_advances_on_create` (all already implemented in Task 1).
- Produces: nothing new for later tasks.

- [ ] **Step 1: Write the failing test**

Add these methods to `IntegrationTestStaffPayroll` (after `test_driver_salary_auto_fetches_attendance_and_advance_on_import`):

```python
	def _make_gender(self):
		gender = frappe.db.get_value("Gender", {}, "name")
		if gender:
			return gender
		doc = frappe.get_doc({"doctype": "Gender", "gender": "Test Gender"})
		doc.insert(ignore_permissions=True)
		return doc.name

	def _make_employee(self, company, ctc=300000):
		employee = frappe.get_doc({
			"doctype": "Employee",
			"first_name": "Test Import Employee",
			"company": company,
			"status": "Active",
			"gender": self._make_gender(),
			"date_of_birth": "1990-01-01",
			"date_of_joining": "2015-01-01",
			"ctc": ctc,
		})
		employee.insert(ignore_permissions=True)
		return employee

	def _make_employee_advance(self, company, employee_name, amount, date):
		payment = frappe.get_doc({
			"doctype": "Payment",
			"date": date,
			"type": "Employee Advance",
			"company": company,
			"mode_of_payment": "Cash",
			"employee": employee_name,
			"amount": amount,
		})
		payment.insert(ignore_permissions=True)
		payment.submit()
		return payment

	def test_employee_salary_auto_fetches_attendance_and_advance_on_import(self):
		company = self._get_company()
		employee = self._make_employee(company, ctc=300000)

		from_date = add_days(today(), -2)
		mid_date = add_days(today(), -1)
		to_date = today()
		self._make_staff_attendance(company, "Employee", employee.name, from_date, "Present")
		self._make_staff_attendance(company, "Employee", employee.name, mid_date, "Present")
		self._make_staff_attendance(company, "Employee", employee.name, to_date, "Absent")

		advance = self._make_employee_advance(company, employee.name, 4000, add_days(today(), -10))

		payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"employee": employee.name,
			"from_date": from_date,
			"to_date": to_date,
			"payroll_date": to_date,
			"payment_mode": "Bank Transfer",
		})
		payroll.insert(ignore_permissions=True)

		self.assertEqual(payroll.salary_type, "Employee Salary")
		self.assertEqual(payroll.company, company)
		self.assertEqual(payroll.ctc, 300000)
		self.assertEqual(payroll.present_days, 2)
		self.assertEqual(payroll.absent_days, 1)
		self.assertEqual(payroll.worked_days, 2)

		self.assertEqual(len(payroll.advance_recovery_table), 1)
		row = payroll.advance_recovery_table[0]
		self.assertEqual(row.payment_ref, advance.name)
		self.assertEqual(row.outstanding, 4000)
		self.assertEqual(row.recovery_amount, 4000)

		basic_salary_row = next(r for r in payroll.earnings_table if r.earning_type == "Basic Salary")
		self.assertEqual(basic_salary_row.amount, 200000)  # (300000 / 3 actual days) * 2 worked days

		advances_row = next(r for r in payroll.deductions_table if r.deduction_type == "Advances")
		self.assertEqual(advances_row.amount, 4000)
```

- [ ] **Step 2: Run test to verify it fails or passes**

Run: `bench --site logicore.com run-tests --doctype "Staff Payroll"`
Expected: If Task 1 is already implemented, this may PASS immediately since the `else` branch shares the same helper methods. If it FAILS (e.g. on the `salary_type` inference or an Employee-specific validation error from ERPNext's `Employee.validate()`), fix `_infer_salary_type_from_person`/`_auto_fetch_*` or the test's Employee field values accordingly — do not weaken the assertions.

- [ ] **Step 3: Confirm passing and no regressions**

Run: `bench --site logicore.com run-tests --doctype "Staff Payroll"`
Expected: PASS (both Task 1 and Task 2 tests green)

- [ ] **Step 4: Commit**

```bash
git add apps/logicore/logicore/logicore/doctype/staff_payroll/test_staff_payroll.py
git commit -m "test(staff-payroll): cover Employee Salary auto-fetch on import"
```

(Skip this step if the user has said they will commit manually themselves.)

---

### Task 3: Partial advance recovery carries forward correctly across periods

**Files:**
- Modify: `apps/logicore/logicore/logicore/doctype/staff_payroll/test_staff_payroll.py` (add one more test method)

**Interfaces:**
- Consumes: same helpers as Task 1 (`_get_company`, `_make_driver`, `_make_staff_attendance`, `_make_driver_advance`), plus `StaffPayroll.submit()` (standard Frappe `docstatus` transition, no new code).
- Produces: nothing new for later tasks — this is the scenario the user specifically described (reduce recovery_amount on one payroll, confirm the next import sees the reduced outstanding balance).

- [ ] **Step 1: Write the test**

Add to `IntegrationTestStaffPayroll`:

```python
	def test_advance_recovery_carries_forward_across_periods_when_submitted(self):
		company = self._get_company()
		driver = self._make_driver(company, ctc=300000)

		advance = self._make_driver_advance(company, driver.name, 5000, add_days(today(), -40))

		period1_from = add_days(today(), -32)
		period1_mid = add_days(today(), -31)
		period1_to = add_days(today(), -30)
		self._make_staff_attendance(company, "Driver", driver.name, period1_from, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, period1_mid, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, period1_to, "Present")

		payroll_1 = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": period1_from,
			"to_date": period1_to,
			"payroll_date": period1_to,
			"payment_mode": "Bank Transfer",
		})
		payroll_1.insert(ignore_permissions=True)
		self.assertEqual(payroll_1.advance_recovery_table[0].recovery_amount, 5000)

		# User reduces recovery to 3000 on the draft before submitting.
		payroll_1.advance_recovery_table[0].recovery_amount = 3000
		payroll_1.save(ignore_permissions=True)
		payroll_1.submit()

		period2_from = add_days(today(), -2)
		period2_mid = add_days(today(), -1)
		period2_to = today()
		self._make_staff_attendance(company, "Driver", driver.name, period2_from, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, period2_mid, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, period2_to, "Present")

		payroll_2 = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": period2_from,
			"to_date": period2_to,
			"payroll_date": period2_to,
			"payment_mode": "Bank Transfer",
		})
		payroll_2.insert(ignore_permissions=True)

		self.assertEqual(len(payroll_2.advance_recovery_table), 1)
		row = payroll_2.advance_recovery_table[0]
		self.assertEqual(row.payment_ref, advance.name)
		self.assertEqual(row.already_recovered, 3000)
		self.assertEqual(row.outstanding, 2000)
		self.assertEqual(row.recovery_amount, 2000)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `bench --site logicore.com run-tests --doctype "Staff Payroll"`
Expected: PASS. If it fails on `already_recovered`/`outstanding`, the issue is in `get_driver_advances`'s `docstatus = 1` join (staff_payroll.py:73-103) not matching — verify `payroll_1.submit()` actually succeeded (check `payroll_1.docstatus == 1`) before debugging further.

- [ ] **Step 3: Full test suite pass**

Run: `bench --site logicore.com run-tests --doctype "Staff Payroll"`
Expected: PASS — all three tests (Task 1, 2, 3) green together.

- [ ] **Step 4: Commit**

```bash
git add apps/logicore/logicore/logicore/doctype/staff_payroll/test_staff_payroll.py
git commit -m "test(staff-payroll): cover partial advance recovery carrying forward across periods"
```

(Skip this step if the user has said they will commit manually themselves.)

---

### Task 4: Manual verification via Frappe's standard Data Import in the browser

**Files:** none (manual QA, no code changes)

**Interfaces:** none — this task only exercises the UI built by Tasks 1-3.

- [ ] **Step 1: Prepare two small CSV files**

`driver_payroll_import.csv`:
```csv
Driver,From Date,To Date,Payroll Date
<existing driver name>,2026-06-01,2026-06-30,2026-07-01
```

`employee_payroll_import.csv`:
```csv
Employee,From Date,To Date,Payroll Date
<existing employee name>,2026-06-01,2026-06-30,2026-07-01
```

Use a real Driver/Employee that has at least one submitted "Driver Advance"/"Employee Advance" Payment and some Staff Attendance records in that date range, so the auto-fetch has real data to show.

- [ ] **Step 2: Run the Driver import**

In the browser: Staff Payroll list view → `...` menu → Import → map `Driver`/`From Date`/`To Date`/`Payroll Date` columns to the matching fields → leave Salary Type unmapped → import. Open the resulting Staff Payroll record.

Expected: `Salary Type` = "Driver Salary", `Company`/`CTC` populated, attendance fields populated, `Advance Recovery` table has a row matching the known advance, `Net Salary` computed — matching what manually clicking "Fetch Attendance" would have produced.

- [ ] **Step 3: Run the Employee import**

Same as Step 2 with `employee_payroll_import.csv`, mapping `Employee` instead of `Driver`.

Expected: `Salary Type` = "Employee Salary", same auto-fetch behavior.

- [ ] **Step 4: Confirm permission gating still works**

As a user whose TMS User Group does NOT have `perm_import` checked for Staff Payroll, confirm the `Import` menu item does not appear on the Staff Payroll list view (this is pre-existing Frappe/TMS User Group behavior — Task 1-3 changes do not touch it, this step just confirms no regression).
