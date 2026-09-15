# Staff Payroll Bulk Import — Design

Date: 2026-07-08

## Goal

Allow bulk-importing Staff Payroll records (Driver and Employee) where the CSV
only needs to identify the person and the payroll period. Attendance, advances
outstanding, CTC/company details, and salary computation must come out
identical to what a user gets by manually creating a Staff Payroll record
through the desk form — no separate "import calculation" logic.

Must work through **both**:
1. The app's own bulk-import engine (`Import Template` + `Import Log`
   doctypes, `utils/import_utils.py`) — already lists "Staff Payroll" as an
   importable doctype.
2. Frappe's built-in Data Import tool (List View → `...` → Import).

## Current state (why a plain import doesn't work today)

- Attendance (`present_days`, `absent_days`, `leave_with_pay`,
  `leave_without_pay`, `worked_days`) and advance recovery
  (`advance_recovery_table`) are populated **only by client-side JavaScript**
  (`staff_payroll.js`: `schedule_attendance_fetch`, "Fetch Attendance"
  button, `get_driver_advances`/`get_employee_advances` calls). None of this
  runs during `doc.insert()` on the server — it requires a browser form to be
  open and firing onchange handlers.
- `validate()` in `staff_payroll.py` computes Basic Salary from
  `worked_days` and rolls `advance_recovery_table` into the "Advances"
  deduction — but only correctly if those fields/table are already
  populated before save.
- Fuel Incentive and Trip Expense sections are **display-only HTML**,
  computed live client-side from `driver` + date range whenever the form is
  opened. They are never stored on the document, so import needs no special
  handling for them — they render correctly automatically once the payroll
  record has `driver`/`from_date`/`to_date` set.
- Both import mechanisms (custom + Frappe standard) ultimately call
  `doc.insert()`/`doc.save()`, which already runs `before_save()` today (e.g.
  it fetches Employee/Driver company/CTC "if blank"). This is the hook point
  to extend.

## Design

### 1. Server-side auto-fetch in `staff_payroll.py` (`before_save`)

Extend `before_save()` so that, for **new** records where the relevant
fields/tables are still empty, it runs the same logic the JS currently
triggers manually:

- Attendance: call `get_attendance_summary(person, from_date, to_date,
  company)` (same function backing the `fetch_attendance_for_period`
  whitelisted RPC) and set `present_days`, `absent_days`, `leave_with_pay`,
  `leave_without_pay`, `worked_days`. Runs after company is resolved (driver
  or employee detail fetch, which already exists earlier in `before_save`).
- Advances: if `advance_recovery_table` is empty, call
  `get_driver_advances(driver)` / `get_employee_advances(employee)`
  (existing functions — unchanged) and append rows. `recovery_amount`
  defaults to full outstanding, same as manual fetch.
- `salary_type` inference: if blank, infer from whichever of
  `employee`/`driver` is set (`Employee Salary` / `Driver Salary`). This is a
  safety net for Frappe's standard Import, which cannot set a fixed default
  value per template the way our custom engine can.
- No changes needed to `validate()`, `update_salary_components()`,
  `_sync_advance_recovery_to_deductions()`, `_update_advance_already_recovered()`
  — they already do the right thing once the above fields are populated.

Because this lives in the doctype controller (not in an import-tool-specific
script), it fires identically for: manual form save, the custom Import
Template engine, and Frappe's standard Data Import.

### 2. Two `Import Template` records (no new doctypes)

- **"Staff Payroll Import — Driver"**: columns = `Driver` (mandatory),
  `From Date` (mandatory), `To Date` (mandatory), `Payroll Date`
  (mandatory). No `Salary Type` column — always "Driver Salary" for this
  template (via a fixed non-CSV column with `default_value`).
- **"Staff Payroll Import — Employee"**: columns = `Employee` (mandatory),
  `From Date` (mandatory), `To Date` (mandatory), `Payroll Date`
  (mandatory). Always "Employee Salary".
- Blank From/To Date is an error (not defaulted to current month), per
  explicit requirement.
- Match keys: the person link field + `From Date` + `To Date` together, with
  `default_import_mode = "Create New Only"` — re-importing the same
  person+period is blocked with an error instead of silently duplicating.
- `import_action` stays "None" (Draft) by default; user can switch a
  template to "Submit After Update" to get auto-submit on import (works for
  both create and update rows, per existing `_apply_import_action` code).

### 3. Frappe standard Data Import compatibility

Two plain CSVs (Driver-only, Employee-only) map 1:1 to real fields
(`driver`/`employee`, `from_date`, `to_date`, `payroll_date`) — no custom
column-to-field resolution needed. `salary_type` is inferred server-side (see
§1) since Frappe's tool has no per-template default-value concept. Frappe's
own "Submit after import" checkbox covers the Draft/Submit choice on that
path.

### 4. Partial advance recovery across periods (no new logic needed)

`get_driver_advances`/`get_employee_advances` already compute "already
recovered" by summing `recovery_amount` from `Payroll Advance Recovery` rows
belonging to **submitted** (`docstatus = 1`) Staff Payroll records. So:
editing `recovery_amount` down on an imported Draft record and submitting it
correctly reduces the outstanding amount seen by the next import. If the
record is left in Draft, the advance is not counted as recovered — existing
behavior, unchanged.

## Note: custom Import Template tool has no UI yet

Investigated separately: `Import Template`/`Import Log` has a complete
backend (`upload_and_preview_import`, `run_import` whitelisted functions in
`import_log.py`) but **no frontend wired up anywhere** — no button, page, or
dialog calls these methods today, for Staff Payroll or any of the other
doctypes already listed in `TMS_IMPORTABLE_DOCTYPES`. Building that UI is
out of scope for this round; the immediate work (this spec) targets
Frappe's standard Data Import, which already has a working UI.

When that custom-tool UI is eventually built, it must gate visibility/access
per target_doctype using `frappe.has_permission(target_doctype, "import")`
— `TMS User Group Permission.perm_import` already syncs into Frappe's
native `Custom DocPerm.import` bit (`tms_user_group.py` `PERM_MAP["import"]
= "perm_import"`), which is the same bit that already correctly gates
Frappe's own standard Import button today. No new permission system is
needed — reuse this existing bit for every current and future Import
Template, not just Staff Payroll.

## Out of scope

- Fuel Incentive / Trip Expense are not imported or stored — confirmed
  display-only, computed live per form load.
- Auto-detecting Employee vs Driver from a single mixed "Name" column —
  rejected in favor of two separate templates (matches how Frappe's standard
  Import maps one column to one field anyway).
- Auto-defaulting From/To Date to "current month" when blank — rejected;
  blank dates are a hard import error.

## Testing plan

- Manual: create a Driver with a submitted advance and existing attendance
  records for a date range; import via custom Import Template with just
  Driver + dates; verify attendance, advance recovery row, and computed
  earnings/deductions match what manual "Fetch Attendance" + advance fetch
  would produce.
- Same via Frappe's standard Data Import (two files, Driver-only and
  Employee-only).
- Partial recovery: submit an imported payroll with a reduced
  `recovery_amount`, re-import next period for the same person, confirm
  outstanding reflects the reduction.
- Duplicate protection: re-import the same person+period, confirm it's
  blocked as an error, not a duplicate record.
