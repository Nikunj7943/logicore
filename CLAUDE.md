# LogiCore — CLAUDE.md

> **For AI agents:** Read this file fully before touching any code. It replaces guessing with ground truth.

---

## 1. Project Identity

| Key | Value |
|-----|-------|
| App name | `logicore` |
| Publisher | LogiCore (`support@logicore.app`) |
| License | MIT |
| Domain | Indian road logistics & fleet management |
| Bench root | `/home/nikunj/logistics-bench/` |
| App root | `/home/nikunj/logistics-bench/apps/logicore/` |
| Module root | `apps/logicore/logicore/logicore/` |
| Site | logms.com |

---

## 2. Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14+, Frappe Framework v15 |
| Frontend | Frappe Form JS, vanilla JS (no React/Vue) |
| CSS | `public/css/` — never inject via JS |
| Linting | `ruff` (Python), `eslint` + `prettier` (JS) |
| Tests | `bench run-tests` (Frappe test runner) |
| PDF | Ghostscript (auto-installed via `install.py`) |
| Background jobs | `frappe.enqueue()` (Redis-backed) |
| DB | MariaDB via Frappe ORM |

---

## 3. Essential Commands

```bash
# After any .py or .js change
bench --site [site] clear-cache

# After any .json DocType schema change
bench --site [site] migrate

# After .js/.css change (assets rebuild)
bench build --app logicore

# Run all app tests
bench run-tests --app logicore

# Run specific doctype tests
bench run-tests --doctype Trip

# Python lint + format
ruff check . && ruff format .

# All pre-commit hooks
pre-commit run --all-files

# Export fixtures (after changing dashboards/workspaces/custom fields)
bench --site [site] export-fixtures --app logicore

# Sync TMS permissions after role changes
bench --site [site] execute logicore.logicore.doctype.tms_user_group.tms_user_group.sync_all_user_groups
```

---

## 4. Directory Structure (Canonical)

```
apps/logicore/
├── CLAUDE.md                          ← you are here
├── pyproject.toml
├── .pre-commit-config.yaml
│
└── logicore/                   # Python package root
    ├── hooks.py                       # ALL app wiring: fixtures, JS/CSS includes, doc_events
    ├── install.py                     # after_install + after_migrate handlers
    ├── address_migration.py           # one-off address migration utilities
    ├── role_profile_sync.py           # declarative role/profile management
    │
    ├── utils/                         # ← SHARED BUSINESS LOGIC GOES HERE
    │   ├── trip_utils.py              # detention_days(), journey_time_days()
    │   ├── date_utils.py              # get_financial_year_start(), get_fy_suffix()
    │   └── indian_format.py           # format_inr(), format_inr_short()
    │
    ├── overrides/                     # Frappe framework overrides
    │   ├── address.py                 # auto-set primary address on first insert
    │   ├── login_redirect.py          # force redirect → /desk/logicore-tms on login
    │   └── twofactor.py              # custom 2FA email template
    │
    ├── patches/                       # bench migrate patches (run-once)
    │   ├── sync_role_and_permissions_to_tms_user_group.py
    │   ├── migrate_address_custom_to_default_fields.py
    │   ├── drop_customer_primary_address_reqd.py
    │   └── remove_supplier_default_for_company.py
    │
    ├── scripts/                       # one-off utility scripts (NOT production)
    │   └── fix_perm_sync.py
    │
    └── logicore/               # module root (DocTypes, API, reports)
        ├── api.py                     # 13 whitelisted REST endpoints
        │
        ├── doctype/                   # 42 custom DocTypes
        │   ├── trip/                  # CORE — trip.py (1,056L) + trip.js (4,762L)
        │   ├── amazon_trip___import/  # Amazon bulk import engine (1,533L)
        │   ├── trip_pod_import_v2/    # POD import v2 — CURRENT (1,598L)
        │   ├── trip_pod_import/       # POD import v1 — LEGACY (1,535L)
        │   ├── trip_settings/         # per-trip-type field config + color (175L)
        │   ├── tms_user_group/        # custom RBAC system (700L)
        │   ├── vendor_payment/        # vendor freight payment + GL (232L)
        │   ├── staff_payroll/         # monthly payroll processing (395L)
        │   ├── staff_attendance/      # daily shift tracking (165L)
        │   ├── business_format/       # billing rules + freight rates
        │   ├── business_subformat/
        │   ├── city/
        │   ├── vehicle_type/
        │   ├── trip_type/
        │   ├── trip_classification/
        │   ├── trip_field_setting/
        │   ├── standard_km/           # distance master (city-pair → KM)
        │   ├── compliances/           # vehicle regulatory compliance tracking
        │   ├── vehicle_expense/       # aggregated vehicle maintenance costs
        │   ├── vehicle_expense_item/
        │   ├── fuel_urea_expenses/    # fuel fill-ups + KPL tracking
        │   ├── repair_expenses/       # vehicle repair records
        │   ├── tyre_expenses/
        │   ├── battery_expenses/
        │   ├── service_log/
        │   ├── service_logs/
        │   ├── service_replacement_item/
        │   ├── vehicle_finance/       # loan/EMI tracking
        │   ├── vehicle_market/        # second-hand valuation
        │   ├── receipt/               # customer receipt (199L)
        │   ├── customer_receipt_trip/ # trip allocation rows
        │   ├── payment/               # generic payment (124L)
        │   ├── vendor_payment_trip/   # trip rows in vendor payment
        │   ├── types_of_goods/
        │   ├── regulatory/
        │   └── amazon_trip/
        │
        ├── report/
        │   ├── tms_vendor_payment_summary/
        │   └── tms_vendor_payment_detail/
        │
        ├── print_format/
        │   ├── trip_pod/
        │   ├── salary_slip_tms/
        │   └── salary_slip_2/
        │
        ├── page/fleet_dashboard/      # custom fleet dashboard page
        ├── module_def/
        ├── workspace/
        └── custom/                    # custom field JSON overrides

    public/
    ├── css/
    │   ├── tms_global.css             # global styles (loaded on every page)
    │   └── tms_trip.css               # trip-specific styles
    └── js/
        ├── tms_utils.js               # window.TMS namespace (formatINR, formatINRShort, formatIndianDate)
        ├── session_timer.js           # session expiry countdown + auto-logout warning
        ├── hide_sidebar.js            # responsive sidebar hiding
        ├── tms_zoom.js                # font size scaling control
        ├── default_public_upload.js   # file upload defaults
        ├── tms_home_breadcrumb.js     # breadcrumb customization
        ├── vehicle.js                 # vehicle form enhancements
        ├── customer.js                # customer form field auto-fetch
        └── supplier.js                # supplier TMS-specific logic

    fixtures/
    ├── custom_field.json              # custom fields on standard ERPNext doctypes
    ├── property_setter.json           # field property overrides (hidden, reqd, read_only)
    ├── client_script.json             # browser-side validations
    ├── server_script.json             # server-side automations
    ├── dashboard.json                 # Trip Dashboard + Fleet Dashboard
    ├── dashboard_chart.json           # 18 charts (trip volume, fuel KPL, repairs, etc.)
    ├── number_card.json               # 21 KPI cards
    ├── workspace.json                 # LogiCore workspace
    └── website_settings.json
```

---

## 5. Core Architecture Patterns

### 5.1 Trip State Machine
```
Draft → Submitted → [in-transit → billed → paid → closed] → Cancelled
```
Trip status is NOT a Frappe workflow — it is a custom `status` Select field managed in `trip.py`. Never use Frappe workflow actions for Trip.

### 5.2 TMS Custom RBAC (Do Not Bypass)
`TMS User Group` is the single source of truth for permissions. It mirrors into Frappe `Custom DocPerm` automatically. **Never edit Custom DocPerm directly** — changes will be overwritten. Always modify via TMS User Group.

Flow: `TMS User Group save` → auto-sync → `Custom DocPerm` records per doctype per role.

Hooks that keep this in sync:
```python
doc_events = {
    "Role":          {"on_update": "...sync_role_disabled_to_user_group"},
    "Custom DocPerm": {"on_update": "...sync_custom_docperm_to_user_group",
                       "on_trash":  "...sync_custom_docperm_to_user_group"},
}
```

### 5.3 POD Import Pipeline
```
User uploads files → Trip POD Import V2 (CURRENT, use this)
                   → Batch processing (frappe.enqueue)
                   → PDF extraction + text OCR matching
                   → Ghostscript compression
                   → Match to Trip number
                   → Attach to Trip document
```
Do NOT use `trip_pod_import/` (v1) for new features — it is legacy.

### 5.4 Business Format → Billing Rules
`Business Format` defines freight rates and billing cycle templates per customer. Trip reads from it at load time. Never hardcode rates.

### 5.5 Background Jobs
All heavy operations use `frappe.enqueue()`:
```python
frappe.enqueue(
    "logicore.logicore.api.compress_pod_pdf",
    queue="long",
    job_name=f"compress_pdf_{doc.name}",
    doc_name=doc.name,
)
```
Never run PDF compression, bulk imports, or payroll processing synchronously.

---

## 6. API Endpoints (`api.py`)

All 13 endpoints are `@frappe.whitelist()`. Call from JS via `frappe.call()`.

| Method | Purpose |
|--------|---------|
| `get_trips()` | Paginated trip list with filters |
| `get_trip()` | Single trip detail |
| `create_trip()` | Create new trip |
| `update_trip()` | Update existing trip |
| `delete_trip()` | Delete trip (force=True) |
| `get_trip_operations_summary()` | 13 operation card counts (POD pending, bills, etc.) |
| `get_vendor_pending_summary()` | Vendor-wise outstanding freight balances |
| `get_trip_filter_options()` | Company/branch combos for filter UI |
| `get_fleet_vehicle_fuel()` | Top 15 vehicles by fuel cost |
| `get_fleet_vehicle_expenses()` | Combined expense breakdown per vehicle |
| `enqueue_compress_pod_pdf()` | Queue PDF compression as background job |
| `compress_pod_pdf()` | Background job handler (not called directly) |
| `get_session_expiry()` | Session TTL in seconds |

**Rule:** All new server functions called from JS must be in `api.py` or a doctype controller, decorated with `@frappe.whitelist()`, and validated server-side.

---

## 7. Hooks Wiring (hooks.py)

### Global assets (every page)
```python
app_include_css = ["tms_global.css?v=7", "tms_trip.css?v=8"]
app_include_js  = ["tms_utils.js", "hide_sidebar.js?v=9",
                   "tms_home_breadcrumb.js", "session_timer.js?v=16",
                   "default_public_upload.js?v=4"]
```
**Rule:** Bump `?v=N` version query string whenever you modify a global asset to bust browser cache.

### DocType-specific JS overrides
```python
doctype_js = {
    "doctype": "public/js/vehicle.js",   # note: "doctype" key = Vehicle doctype
    "Supplier": "public/js/supplier.js",
    "Customer": "public/js/customer.js",
}
```

### Document events
```python
doc_events = {
    "Address":       {"after_insert": "...address.after_insert_set_primary"},
    "Role":          {"on_update": "...tms_user_group.sync_role_disabled_to_user_group"},
    "Custom DocPerm": {"on_update": "...sync_custom_docperm_to_user_group",
                       "on_trash":  "...sync_custom_docperm_to_user_group"},
}
```

### Install/migrate hooks
```python
after_install = "logicore.install.after_install"
after_migrate  = "logicore.install.after_migrate"
```
`after_migrate` runs on every `bench migrate` — keep it idempotent.

### Auth hooks
```python
on_login     = ["...login_redirect.set_login_redirect"]
after_request = ["...login_redirect.after_login_redirect"]
```

---

## 8. DocType Reference (42 DocTypes)

### Core Logistics
| DocType | File | Lines | Purpose |
|---------|------|-------|---------|
| **Trip** | `trip/trip.py` | 1,056 | Central shipment doc — state machine, detention calc, billing cycle, vendor TDS |
| **Amazon Trip** | `amazon_trip/` | 146 | Amazon-specific trip variant |
| **Trip Settings** | `trip_settings/trip_settings.py` | 175 | Per-trip-type field visibility + color theming |
| **Trip Type** | `trip_type/` | — | Classification: Primary, RCPL, Secondary, Amazon, Other |
| **Trip Classification** | `trip_classification/` | — | Grouping logic for trip categorization |
| **Trip Field Setting** | `trip_field_setting/` | — | Per-trip-type field-level config rows |

### POD Management
| DocType | File | Lines | Purpose |
|---------|------|-------|---------|
| **Trip POD Import V2** | `trip_pod_import_v2/...py` | 1,598 | **CURRENT** — batch PDF import, OCR matching, background compression |
| **Trip POD Import File V2** | `trip_pod_import_file_v2/` | — | Row records for V2 with status tracking |
| **Trip POD Import** | `trip_pod_import/...py` | 1,535 | **LEGACY** — v1 import engine, do not extend |
| **Trip POD Import File** | `trip_pod_import_file/` | — | Row records for v1 |

### Amazon Integration
| DocType | File | Lines | Purpose |
|---------|------|-------|---------|
| **Amazon Trip Import** | `amazon_trip___import/...py` | 1,533 | CSV parsing, auto-trip creation, rate lookup from Business Format |

### Master Data
| DocType | Purpose |
|---------|---------|
| **Business Format** | Customer billing rules + freight rate matrix |
| **Business Subformat** | Sub-classification within Business Format |
| **City** | City master with geography tagging |
| **Vehicle Type** | Truck / tempo / van / etc. |
| **Types of Goods** | Commodity classification |
| **Regulatory** | Compliance tag definitions |
| **Standard KMs** | Distance master: city-pair → standard KM |

### Fleet Management
| DocType | File | Lines | Purpose |
|---------|------|-------|---------|
| **Vehicle Expense** | `vehicle_expense/` | — | Aggregated maintenance costs |
| **Vehicle Expense Item** | `vehicle_expense_item/` | — | Individual expense line items |
| **Fuel Urea Expenses** | `fuel_urea_expenses/...py` | 85 | Fuel fill-ups + KPL tracking |
| **Repair Expenses** | `repair_expenses/...py` | 91 | Vehicle repair records |
| **Tyre Expenses** | `tyre_expenses/...py` | 90 | Tyre replacement + cost |
| **Battery Expenses** | `battery_expenses/...py` | 91 | Battery replacement (EV) |
| **Service Log** | `service_log/` | — | Preventive maintenance schedule |
| **Service Logs** | `service_logs/` | — | Aggregated service records |
| **Service Replacement Item** | `service_replacement_item/` | — | Parts replaced during service |
| **Compliances** | `compliances/` | — | Insurance / pollution / permit renewal tracking |
| **Vehicle Finance** | `vehicle_finance/` | — | Loan / EMI tracking |
| **Vehicle Market** | `vehicle_market/` | — | Second-hand valuation |

### Staffing & Payroll
| DocType | File | Lines | Purpose |
|---------|------|-------|---------|
| **Staff Attendance** | `staff_attendance/...py` | 165 | Daily shift tracking |
| **Staff Attendance Detail** | `staff_attendance_detail/` | — | Individual staff rows |
| **Staff Payroll** | `staff_payroll/...py` | 395 | Monthly salary: earnings (basic/incentive/bonus) + deductions (advance/leave) |
| **Payroll Earning Detail** | `payroll_earning_detail/` | — | Earnings component template rows |
| **Payroll Deduction Detail** | `payroll_deduction_detail/` | — | Deduction component template rows |

### Payments & Receipts
| DocType | File | Lines | Purpose |
|---------|------|-------|---------|
| **Vendor Payment** | `vendor_payment/...py` | 232 | Freight payment to supplier + TDS calc + GL entry |
| **Vendor Payment Trip** | `vendor_payment_trip/` | — | Trip line items in vendor payment |
| **Payment** | `payment/...py` | 124 | Generic payment recording |
| **Receipt** | `receipt/...py` | 199 | Customer receipt with trip allocation |
| **Customer Receipt Trip** | `customer_receipt_trip/` | — | Trip-level receipt rows |

### Permissions & Access
| DocType | File | Lines | Purpose |
|---------|------|-------|---------|
| **TMS User Group** | `tms_user_group/...py` | 700 | Custom RBAC: mirrors Frappe Roles → Custom DocPerm permission matrix |
| **TMS User Group Permission** | `tms_user_group_permission/` | — | Row-level read/write/submit/amend/delete matrix |

### Telegram Bot
| DocType | File | Purpose |
|---------|------|---------|
| **Telegram Bot Settings** | `telegram_bot_settings/` | Single doctype — paste bot token, save → auto-writes `telegram_bot_token` + generated `telegram_webhook_secret` to site_config.json and registers the webhook with Telegram. URL is auto-detected: manual override → local ngrok tunnel (`http://127.0.0.1:4040`) → this site's own URL. No environment flag — same form works locally and on Frappe Cloud. |
| **Telegram User Map** | `telegram_user_map/` | Maps Telegram chat → Driver/Employee + role |
| **Telegram Session** | `telegram_session/` | Per-chat conversation state machine |

---

## 9. Key Utility Functions

### Python

```python
# Trip calculations
from logicore.utils.trip_utils import detention_days, journey_time_days

# Indian fiscal year
from logicore.utils.date_utils import get_financial_year_start, get_fy_suffix
# FY: April 1 – March 31 (NEVER Jan–Dec)
# get_fy_suffix(date) → "2526" (for FY 2025-26)

# Currency formatting
from logicore.utils.indian_format import format_inr, format_inr_short
# format_inr(1000000)       → "₹10,00,000"
# format_inr_short(1000000) → "₹10.00 L"
# format_inr_short(10000000)→ "₹1.00 Cr"

# Doctype submit/event emails
from logicore.utils.email_template_utils import ensure_email_template, render_and_send_email_template
# ensure_email_template(name, subject, response_html, reference_doctype) -> idempotent seed, call from install.py
# render_and_send_email_template(template_doctype, context, recipients, ...) -> looks up by reference_doctype (not name) + render + send
# See section 21 for when to use this vs. Frappe's built-in Notification doctype.
```

### JavaScript (window.TMS namespace)
```javascript
// Available globally after tms_utils.js loads
TMS.formatINR(1000000)         // → "₹10,00,000"
TMS.formatINRShort(1000000)    // → "₹10.00 L"
TMS.formatIndianDate("2025-05-06")  // → "06-05-2025"
```

---

## 10. Naming Conventions

### Trip document names
Pattern: `{COMPANY_ABBR}-{TRIP_TYPE_CODE}-{MMYY}{SERIES}`
Example: `TMS-P-0526-00001` (Primary trip, May 2026, series 1)

Series counters are FY-based (April reset), shared per financial year across trip types.

### Python files
- DocType controller: same name as doctype folder, snake_case → `trip.py`
- Utilities: descriptive noun → `trip_utils.py`, `date_utils.py`
- Patches: action-describing → `sync_role_and_permissions_to_tms_user_group.py`

### JavaScript
- Global namespace: `window.TMS.*` (defined in `tms_utils.js`)
- Form-level: `frappe.ui.form.on("Trip", { ... })`
- No `var` — use `const` / `let`

---

## 11. Coding Standards

### Universal rules
- **Read the file before editing** — never guess field names, method signatures, or structure
- **Minimal changes** — fix what is asked, nothing more; no opportunistic refactoring
- **No comments on obvious code** — only comment non-obvious invariants or workarounds
- **No docstrings on unchanged code** — new functions get one-line summaries max
- **Business logic → `utils/`** — controllers orchestrate, utilities compute
- **No magic numbers** — use named constants or fetch from Trip Settings / Business Format
- **No CSS in JS** — all styles in `public/css/`, registered in `hooks.py`

### Python-specific
- Use `frappe.db.get_value()` for single lookups, `frappe.db.get_all()` for lists
- Use `frappe.get_doc()` only when you need the full document object
- Wrap DB writes in `doc.save()` / `doc.submit()` — never `frappe.db.set_value()` on submitted docs
- All `@frappe.whitelist()` functions must validate inputs server-side
- Use `frappe.throw()` for user-facing errors, `frappe.log_error()` for system errors
- Background jobs: `frappe.enqueue("module.path.function", queue="long", **kwargs)`

### JavaScript-specific
- Use `frappe.call()` for all server communication — never raw `fetch()`
- Use `frappe.msgprint()` for user messages, `frappe.throw()` for errors
- Dynamic fields: use `frm.set_df_property(field, "hidden", 1)` not DOM manipulation
- Refresh after field changes: `frm.refresh_field(field_name)`
- CSS version bump: increment `?v=N` in hooks.py when modifying global assets

### Frappe-specific patterns
```python
# Correct: read then modify
doc = frappe.get_doc("Trip", trip_name)
doc.status = "Closed"
doc.save()

# Correct: bulk read
trips = frappe.db.get_all("Trip",
    filters={"status": "Open", "company": company},
    fields=["name", "customer", "freight"],
    order_by="creation desc",
    limit=50
)

# Correct: background job
frappe.enqueue(
    "logicore.logicore.api.compress_pod_pdf",
    queue="long",
    job_name=f"compress_{doc.name}",
    doc_name=doc.name,
)
```

---

## 12. Indian UX Requirements (Non-Negotiable)

### Currency
```javascript
// Always Indian grouping
TMS.formatINR(1000000)  // ₹10,00,000  (NOT ₹1,000,000)
TMS.formatINRShort(1500000)  // ₹15.00 L
TMS.formatINRShort(15000000) // ₹1.50 Cr
```

### Dates
- **Store:** `YYYY-MM-DD` (Frappe default, MariaDB native)
- **Display:** `DD-MM-YYYY`
- **Never** use US format `MM/DD/YYYY`

### Fiscal Year
- **Always April 1 – March 31** (Indian FY)
- FY 2025-26 = April 1 2025 to March 31 2026
- Series reset at April 1 every year
- `get_fy_suffix()` returns `"2526"` for any date in FY 2025-26

### Phone
- 10 digits, `+91` optional prefix
- Display without country code in forms

### Form layout
- Top-to-bottom flow matching Indian paper forms
- Company/branch at top, then dates, then party details, then amounts

---

## 13. Responsive UI

All UI must work on desktop (1440px), tablet (768px), and mobile (375px).

```css
@media (min-width: 768px)  { /* tablet */ }
@media (min-width: 992px)  { /* laptop */ }
@media (min-width: 1200px) { /* desktop */ }

/* Fluid sizing — never fixed pixel widths for containers */
width: min(760px, 95vw);
grid-template-columns: minmax(240px, 380px) 1fr;
font-size: clamp(12px, 1.5vw, 16px);
```

---

## 14. Security Rules

- All server functions called from JS → `@frappe.whitelist()` decorator
- Validate all user input server-side — never trust client data
- No hardcoded credentials or API keys anywhere
- Escape user-supplied strings before HTML injection: `frappe.utils.escape_html()`
- Role permissions via TMS User Group only — never edit Custom DocPerm directly
- PDF paths must be validated before passing to Ghostscript subprocess

---

## 15. Token-Saving Rules for AI Agents

These rules make Claude's work faster and cheaper by preventing wasteful patterns:

### DO read these files first for any task
| Task type | Files to read first |
|-----------|-------------------|
| Trip changes | `doctype/trip/trip.py`, `doctype/trip/trip.js` |
| Permissions | `doctype/tms_user_group/tms_user_group.py` |
| API changes | `logicore/api.py` |
| New utility | `utils/trip_utils.py`, `utils/date_utils.py` |
| Hooks/assets | `hooks.py` |
| Install/migrate | `install.py`, `patches/` directory |
| POD imports | `doctype/trip_pod_import_v2/trip_pod_import_v2.py` |
| Payroll | `doctype/staff_payroll/staff_payroll.py` |

### DO NOT
- Do NOT read the entire `trip.js` (4,762 lines) unless the task is specifically about Trip form UI — it is extremely large
- Do NOT edit `fixtures/*.json` manually — use `bench export-fixtures` to regenerate
- Do NOT use `frappe.db.sql()` for simple CRUD — use the ORM methods
- Do NOT create new top-level Python modules outside `utils/`, `overrides/`, or doctype controllers
- Do NOT add `@frappe.whitelist()` to internal utility functions — only entry points
- Do NOT modify `patches/` files after they have run — create new patch files instead
- Do NOT run `frappe.get_doc()` inside loops — use `frappe.db.get_all()` then batch process

### Grep targets for fast navigation
```bash
# Find whitelisted methods
grep -r "@frappe.whitelist" apps/logicore/ --include="*.py"

# Find all doc_events
grep -A5 "doc_events" apps/logicore/logicore/hooks.py

# Find Trip field visibility rules
grep -n "set_df_property" apps/logicore/logicore/doctype/trip/trip.js | head -30

# Find all frappe.enqueue calls
grep -rn "frappe.enqueue" apps/logicore/ --include="*.py"
```

---

## 16. Adding New Features — Checklists

### New API endpoint
1. Add `@frappe.whitelist()` function to `logicore/api.py`
2. Validate all inputs at top of function with `frappe.throw()` if invalid
3. Return dict (auto JSON-serialized by Frappe)
4. Document in this CLAUDE.md section 6

### New DocType
1. Create via Frappe UI → Export JSON → commit
2. Add controller `.py` in `doctype/{name}/`
3. Add `.js` form file if UI needed
4. Run `bench migrate` after JSON export
5. Add to TMS User Group permissions
6. Add to fixtures list in `hooks.py` if it needs to be exported

### New utility function
1. Add to appropriate file in `utils/`
2. Import only where needed — no circular imports

### New patch (data migration)
1. Create `patches/{descriptive_name}.py`
2. Add entry to `patches.txt` at app root
3. Make the patch idempotent (check before modify)
4. Test with `bench --site [site] run-patch logicore.patches.{name}`

### New background job
1. Define the job function in relevant controller or `api.py`
2. Decorate with `@frappe.whitelist()` only if user-triggered
3. Enqueue with `queue="long"` and descriptive `job_name`
4. Add status tracking field to the triggering doctype

### Modifying fixtures (dashboards, workspaces, custom fields)
1. Make changes via Frappe UI
2. Run `bench --site [site] export-fixtures --app logicore`
3. Commit the updated JSON files
4. Never hand-edit fixture JSON

---

## 17. Common Patterns Quick Reference

### Get a document and update a field
```python
doc = frappe.get_doc("Trip", trip_name)
doc.status = "Closed"
doc.closed_date = frappe.utils.today()
doc.save(ignore_permissions=False)
```

### Query with filters
```python
rows = frappe.db.get_all(
    "Trip",
    filters={"status": "Open", "company": company},
    fields=["name", "customer", "total_freight", "creation"],
    order_by="creation desc",
    limit_page_length=50,
)
```

### frappe.call from JS
```javascript
frappe.call({
    method: "logicore.logicore.api.get_trip_operations_summary",
    args: { company: frm.doc.company },
    callback(r) {
        if (r.message) {
            // handle response
        }
    },
});
```

### Show/hide fields in form JS
```javascript
frappe.ui.form.on("Trip", {
    trip_type(frm) {
        const isAmazon = frm.doc.trip_type === "Amazon";
        frm.set_df_property("amazon_order_id", "hidden", isAmazon ? 0 : 1);
        frm.refresh_field("amazon_order_id");
    },
});
```

### Child table rows
```javascript
// Add row
const row = frm.add_child("trip_charges");
row.charge_type = "Detention";
row.amount = detention_amount;
frm.refresh_field("trip_charges");

// Iterate rows
frm.doc.trip_charges.forEach(row => {
    // ...
});
```

### Indian currency display
```javascript
// In Frappe form
frm.set_value("formatted_freight", TMS.formatINR(frm.doc.freight));

// In custom HTML
element.textContent = TMS.formatINRShort(totalAmount);
```

---

## 18. Known Issues & Constraints

- `trip.js` is 4,762 lines — read only the sections you need (search by function name or event)
- CSS version strings in `hooks.py` must be bumped manually (`?v=N`) when global assets change
- Amazon Trip Import CSV format is Amazon-specific — do not generalize the parser
- `TMS User Group` RBAC is completely custom — Frappe's standard role system is bypassed for this app
- POD import v1 (`trip_pod_import`) is legacy — all new POD features go into v2
- Ghostscript must be installed on the server — `install.py` does this, but verify on new deployments
- `after_migrate` in `install.py` runs on every `bench migrate` — all logic there must be idempotent
- Background job timeouts: use `queue="long"` for PDF compression and bulk imports

---

## 19. Fixture Dashboard / Chart Names (for reference)

### Dashboard Charts (18)
```
TMS Trip Volume Monthly        TMS Customer Freight Monthly
TMS Trips by Status            TMS Trips by Trip Type
TMS Trips by Branch            TMS POD Status Distribution
TMS Vendor Freight Monthly     TMS Detention Trend Monthly
TMS Trips by Customer          TMS Trips by Vehicle Type
Fleet Fuel Expenses Monthly    Fleet Fuel KPL Trend
Fleet Repair Expenses Monthly  Fleet Repairs by Category
Fleet Service Cost Monthly     Fleet Compliances by Type
Fleet Tyre Cost Monthly        Fleet Fuel by Vehicle
```

### Number Cards (21)
```
TMS Open Trips           TMS Trips This Month       TMS Customer Freight MTD
TMS POD Pending          TMS Total KM MTD           TMS Vendor Freight MTD
TMS Detention Amount MTD TMS Active Vehicles        TMS Trip Revenue MTD
TMS Amazon Trips Active  Fleet Fuel Cost MTD        Fleet Fuel Liters MTD
Fleet Repair Cost MTD    Fleet Repair Count MTD     Fleet Service Cost MTD
Fleet Tyre Cost MTD      Fleet Battery Count MTD    Fleet Compliance Count
Fleet Outstanding Loans  Fleet EMI Total
```

---

## 20. Agent Instructions

When working on this codebase as an AI agent:

1. **Start with context** — read the relevant doctype controller and JS before proposing changes
2. **Minimal blast radius** — change only what is needed; this is production logistics software
3. **Verify field names** — Frappe field names are exact strings; read the `.json` meta file if unsure
4. **Test commands first** — for any DB-touching change, confirm the site name first: `ls /home/nikunj/logistics-bench/sites/`
5. **Cache clear after every Python/JS change** — `bench --site [site] clear-cache`
6. **Migrate after JSON schema changes** — `bench --site [site] migrate`
7. **Build after CSS/JS changes** — `bench build --app logicore`
8. **Never edit Custom DocPerm directly** — use TMS User Group
9. **Never edit fixture JSON manually** — use export-fixtures
10. **Background jobs for heavy work** — PDF compression, bulk imports, payroll batch — always enqueue
11. **Indian context always** — INR formatting, April FY, DD-MM-YYYY display, 10-digit phones
12. **Security always** — `@frappe.whitelist()` on all server-callable functions, validate inputs server-side

---

## 21. Doctype Email / Notifications

Before writing any doctype-email code, check in this order:

1. **Can Frappe's `Notification` doctype (Setup → Notification) do this with
   zero code?** It covers event (Submit/Save/Cancel/Value Change/Days
   Before-After), a Jinja condition, recipients from a field/role/fixed
   address, and a subject/message that can reference `doc.*` — including
   looping a child table directly in the message body
   (`{% for row in doc.trips %}`). Use this whenever the values needed
   already exist as plain fields on the document.
2. **Only if you need a computed/derived value not directly on the doc** —
   Indian comma-grouped currency (`₹10,00,000`), a per-row sum across two
   child-table fields, a conditional non-blocking UI warning instead of a
   hard failure — use `utils/email_template_utils.py`
   (`ensure_email_template()` + `render_and_send_email_template()`) plus one
   small doctype-specific context-builder function. See
   `utils/vendor_payment_email.py` for the reference shape: a public
   `send_<doctype>_email(doc)` wrapper that try/excepts a private `_send(doc)`
   which builds the context dict and calls `render_and_send_email_template()`.
3. Do not generalize the context-building step itself — field names,
   child-table math, and formatting rules differ per doctype. Each doctype
   keeps its own small `_send()`-style function.
4. The Email Template record's **content** (subject, HTML design) is fully
   UI-editable via Setup → Email → Email Template — that's the entire point.
   `render_and_send_email_template()` looks the record up by its **"Doctype"
   field** (`reference_doctype`), not by name — pass the sending doctype's
   name (e.g. `doc.doctype`), not a fixed string. Renaming the record in the
   UI is always safe. Keep exactly one *enabled* Email Template per
   reference_doctype for any doctype using this automatic-send path — if
   more than one exists, the oldest (first created) wins silently, with no
   further disambiguation.
