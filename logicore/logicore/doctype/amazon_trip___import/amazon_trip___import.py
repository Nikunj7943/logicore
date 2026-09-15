# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import csv
import json
import os
import re
import time
from functools import lru_cache

import frappe
from frappe import _, scrub
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, get_datetime, getdate, now_datetime, nowdate

# ══════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════

# PREVIEW_ROW_LIMIT = 10_000_000  # removed — all rows are always shown in preview
EMPTY_VALUES = {"", None}
IMPORT_IDENTITY_FIELD = "tour_id_relay"

# Mandatory parent fields — group fails if any of these are blank.
MANDATORY_PARENT_FIELDS = ("trip_date",)

# Valid values for Select fields validated at row level.
VALID_VR_STATUSES    = {"Completed", "Cancelled", "Dummy"}
VALID_TRIP_STATUSES  = {"Closed", "Unbilled", "Under Dispute", ""}
IMPORT_DOCTYPE = "Amazon trip - Import"
TARGET_DOCTYPE = "Amazon Trip"
CHILD_DOCTYPE = "Amazon Trip Detail"
CHILD_PARENTFIELD = "amazon_trip_details"
REALTIME_EVENT = "amazon_trip_import_progress"
PROGRESS_PUBLISH_EVERY_ROWS = 2000
CANCEL_CHECK_EVERY_ROWS = 500
FAILURES_MAX_STORED = 5000
BULK_UPSERT_BATCH_SIZE = 500
TOUR_ID_PREFETCH_CHUNK = 5000
PARSE_CACHE_TTL = 1800  # seconds
PREVIEW_PUBLISH_EVERY_ROWS = 2000

# ── Header-name based maps (keys = Excel/CSV header name strings) ────────────

# Parent fields: taken from the FIRST row of each Tour ID group.
# Keys are the exact column header names expected in the file.
PARENT_HEADER_MAP: dict[str, dict] = {
    "Company Name":                    {"fieldname": "company_name",                  "fieldtype": "Link",     "options": "Company"},
    "Customer":                        {"fieldname": "customer",                      "fieldtype": "Link",     "options": "Customer"},
    "Trip Type":                       {"fieldname": "trip_type",                     "fieldtype": "Link",     "options": "Trip Type"},
    "Branch":                          {"fieldname": "branch",                        "fieldtype": "Link",     "options": "Branch"},
    "Trip Coordinator":                {"fieldname": "trip_coordinator",              "fieldtype": "Employee"},
    "Trip Date":                       {"fieldname": "trip_date",                     "fieldtype": "Date"},
    "Tour ID":                         {"fieldname": "tour_id_relay",                 "fieldtype": "Data"},
    "Facility Sequence":               {"fieldname": "facility_sequence",             "fieldtype": "Data"},
    "CPT":                             {"fieldname": "cpt",                           "fieldtype": "Data"},
    "Is CPT Truck":                    {"fieldname": "is_cpt_truck",                  "fieldtype": "Check"},
    "CR_ID":                           {"fieldname": "cr_id",                         "fieldtype": "Data"},
    "Shipper Accounts":                {"fieldname": "shipper_accounts",              "fieldtype": "Data"},
    "Equipment Type":                  {"fieldname": "equipment_type",                "fieldtype": "Link",     "options": "Vehicle Type"},
    "Estimated Cost":                  {"fieldname": "estimated_cost",                "fieldtype": "Currency"},
    "Tender Status":                   {"fieldname": "tender_status",                 "fieldtype": "Data"},
    "Driver":                          {"fieldname": "driver_relay",                  "fieldtype": "Link",     "options": "Driver"},
    "Vehicle ID":                      {"fieldname": "vehicle_id",                    "fieldtype": "Link",     "options": "Vehicle"},
    "VR Cancellation Date Time (UTC)": {"fieldname": "vr_cancellation_date_time_utc","fieldtype": "Datetime"},
    "Transit Operator Type":           {"fieldname": "transit_operator_type",         "fieldtype": "Data"},
    "Spot Work":                       {"fieldname": "spot_work",                     "fieldtype": "Check"},
    "Customer Freight":                {"fieldname": "freight",                       "fieldtype": "Currency"},
    "RLB Fuel Surcharge1":             {"fieldname": "fuel_surcharge_manual",         "fieldtype": "Currency"},
    "RLB Cancellation Charge1":        {"fieldname": "cancellation_charge_manual",    "fieldtype": "Currency"},
    "RLB Detention Charge1":           {"fieldname": "detention_charge_manual",       "fieldtype": "Currency"},
    "RLB OT Cost1":                    {"fieldname": "ot_cost_manual",                "fieldtype": "Currency"},
    "RLB Extra Distance Cost1":        {"fieldname": "extra_distance_cost_manual",    "fieldtype": "Currency"},
    "RLB Toll-Parking Charges1":       {"fieldname": "toll_parking_charges_manual",   "fieldtype": "Currency"},
    "Vendor":                          {"fieldname": "vendor",                        "fieldtype": "Link",     "options": "Supplier"},
    "Vendor Freight":                  {"fieldname": "vendor_freight",                "fieldtype": "Currency"},
    "Vendor Freight (Extra)":          {"fieldname": "vendor_freight_extra",          "fieldtype": "Currency"},
    "Duplicate Trips":                 {"fieldname": "duplicate_trips",               "fieldtype": "Int"},
    "Duplicate Record No":             {"fieldname": "duplicate_record_no",           "fieldtype": "Data"},
    "Manual Trip":                     {"fieldname": "manual_trip",                   "fieldtype": "Check"},
}

# Child fields: one dict per Excel row → one row in amazon_trip_details.
CHILD_HEADER_MAP: dict[str, dict] = {
    "VR ID":                      {"fieldname": "vr_id",                        "fieldtype": "Data"},
    "Status":                     {"fieldname": "vr_status",                    "fieldtype": "Select"},
    "Load ID":                    {"fieldname": "load_id",                      "fieldtype": "Data"},
    "Vehicle No.":                {"fieldname": "vehicle_no",                   "fieldtype": "Data"},
    "Start Date":                 {"fieldname": "start_date",                   "fieldtype": "Datetime"},
    "End Date":                   {"fieldname": "end_date",                     "fieldtype": "Datetime"},
    "Lane":                       {"fieldname": "lane",                         "fieldtype": "Data"},
    "City":                       {"fieldname": "city",                         "fieldtype": "Data"},
    "Operator Type":              {"fieldname": "operator_type_amazon",         "fieldtype": "Data"},
    "Total Distance":             {"fieldname": "total_distance",               "fieldtype": "Float"},
    "Contract Type":              {"fieldname": "contract_type",                "fieldtype": "Data"},
    "Rate Type":                  {"fieldname": "rate_type",                    "fieldtype": "Data"},
    "Item Type":                  {"fieldname": "item_type",                    "fieldtype": "Data"},
    "Work Type":                  {"fieldname": "work_type",                    "fieldtype": "Data"},
    "Base Rate":                  {"fieldname": "base_rate",                    "fieldtype": "Currency"},
    "Fuel Surcharge":             {"fieldname": "fuel_surcharge_amazon",        "fieldtype": "Currency"},
    "Cancellation Charge":        {"fieldname": "cancellation_charge_amazon",   "fieldtype": "Currency"},
    "Detention Charge":           {"fieldname": "detention_charge_amazon",      "fieldtype": "Currency"},
    "OT Cost":                    {"fieldname": "ot_cost_amazon",               "fieldtype": "Currency"},
    "Extra distance Cost":        {"fieldname": "extra_distance_cost_amazon",   "fieldtype": "Currency"},
    "Toll-Parking Charges":       {"fieldname": "toll_parking_charges_amazon",  "fieldtype": "Currency"},
    "Tax Percent":                {"fieldname": "tax_percent",                  "fieldtype": "Float"},
    "Gross Pay Amt (Excl. Tax)":  {"fieldname": "gross_pay_amt_excl_tax",       "fieldtype": "Currency"},
    "Gross Tax Amt":              {"fieldname": "gross_tax_amt",                "fieldtype": "Currency"},
    "Gross Pay Amt":              {"fieldname": "gross_pay_amt",                "fieldtype": "Currency"},
    "Comments":                   {"fieldname": "comments",                     "fieldtype": "Small Text"},
    "Extra Hours":                {"fieldname": "extra_hours",                  "fieldtype": "Float"},
    "Extra Km":                   {"fieldname": "extra_km",                     "fieldtype": "Float"},
    "Remarks3":                   {"fieldname": "remarks3",                     "fieldtype": "Small Text"},
    "Bill No":                    {"fieldname": "original_sadashiv_bill_no",    "fieldtype": "Data"},
    "Bill Date":                  {"fieldname": "original_bill_date",           "fieldtype": "Date",    "date_format": "DD-MM-YYYY"},
    "Computed Total Freight":     {"fieldname": "computed_total_freight",       "fieldtype": "Currency"},
    "Computed Billed Amount":     {"fieldname": "computed_billed_amount",       "fieldtype": "Currency"},
    "Freight Difference":         {"fieldname": "freight_difference",           "fieldtype": "Currency"},
    "Trip Status":                {"fieldname": "trip_status",                  "fieldtype": "Data"},
}

# Alternate/variant header names → canonical header name (case-insensitive lookup)
HEADER_ALIASES: dict[str, str] = {
    "tour id":                    "Tour ID",
    "vr id":                      "VR ID",
    "vehicle no":                 "Vehicle No.",
    "vehicle no.":                "Vehicle No.",
    "gross pay amt excl tax":     "Gross Pay Amt (Excl. Tax)",
    "extra distance cost":        "Extra distance Cost",
    "operator type":              "Operator Type",
    "status":                     "Status",
    "trip status":                "Trip Status",
    "bill no":                    "Bill No",
    "bill date":                  "Bill Date",
    "customer ":                  "Customer",  # trailing space variant
    "company name":               "Company Name",
}

# VR Status normalisation table (Amazon raw → Select option)
VR_STATUS_MAP = {
    "COMPLETED": "Completed",
    "CANCELLED": "Cancelled",
    "REJECTED":  "Rejected",
    "PENDING":   "Pending",
}


# ══════════════════════════════════════════════════════════════════
#  DocType Controller
# ══════════════════════════════════════════════════════════════════

class AmazontripImport(Document):
    def autoname(self):
        from frappe.model.naming import make_autoname

        import_no = make_autoname("IMP-.YYYY.-.#####", doc=self)
        self.import_no = import_no
        self.name = import_no

    def before_insert(self):
        self._set_import_defaults()

    def validate(self):
        self._set_import_defaults()

    def _set_import_defaults(self):
        if self.name and self.import_no != self.name:
            self.import_no = self.name

        if not self.import_date:
            self.import_date = nowdate()

        if not self.import_by:
            self.import_by = frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user


# ══════════════════════════════════════════════════════════════════
#  FILE FINGERPRINT / CACHE HELPERS
# ══════════════════════════════════════════════════════════════════

def _file_fingerprint(file_url: str) -> str:
    """Cheap cache-key fingerprint: path + size + mtime. Avoids reading file."""
    import hashlib

    file_doc = frappe.get_doc("File", {"file_url": file_url})
    full_path = file_doc.get_full_path()
    try:
        st = os.stat(full_path)
        raw = f"{full_path}|{st.st_size}|{st.st_mtime_ns}"
    except OSError:
        raw = full_path
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_cache_key(fingerprint: str) -> str:
    return f"atip_parse::{fingerprint}"


def _cache_parsed(fingerprint: str, payload: dict) -> None:
    try:
        frappe.cache().set_value(_parse_cache_key(fingerprint), payload, expires_in_sec=PARSE_CACHE_TTL)
    except Exception:
        pass


def _cache_get_parsed(fingerprint: str):
    try:
        return frappe.cache().get_value(_parse_cache_key(fingerprint))
    except Exception:
        return None


def _active_fp_key(docname: str) -> str:
    return f"atip_active_fp::{docname}"


def _set_active_fingerprint(docname: str, fingerprint: str) -> None:
    try:
        frappe.cache().set_value(_active_fp_key(docname), fingerprint, expires_in_sec=PARSE_CACHE_TTL)
    except Exception:
        pass


def _get_active_fingerprint(docname: str):
    try:
        return frappe.cache().get_value(_active_fp_key(docname))
    except Exception:
        return None


def _job_is_active(job_id: str) -> bool:
    """Check if an RQ job is still queued/running (not lost/finished/failed)."""
    if not job_id:
        return False
    try:
        from rq.job import Job

        from frappe.utils.background_jobs import get_redis_conn

        job = Job.fetch(job_id, connection=get_redis_conn())
        return job.get_status() in ("queued", "started", "deferred", "scheduled")
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════
#  VALUE PARSING HELPERS
# ══════════════════════════════════════════════════════════════════

def _extract_numeric(text_value: str) -> str:
    """Extract numeric portion from strings like '35.00 INR', '40.84 KM '."""
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", cstr(text_value))
    if not match:
        raise ValueError(f"No numeric value in: {text_value!r}")
    return match.group(0).replace(",", "")


def _parse_ist_datetime(raw) -> str | None:
    """Parse '05/01/2026 01:00:00 IST' (MM/DD/YYYY) → '2026-05-01 01:00:00'."""
    if raw in EMPTY_VALUES:
        return None
    text = cstr(raw).strip()
    if not text or text in ("None", "nan"):
        return None
    # Strip trailing timezone label (IST, UTC, etc.)
    text = re.sub(r"\s+[A-Z]{2,4}$", "", text).strip()
    try:
        # MM/DD/YYYY HH:MM:SS
        from datetime import datetime
        dt = datetime.strptime(text, "%m/%d/%Y %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Fall back to Frappe's get_datetime
        try:
            return cstr(get_datetime(text))
        except Exception:
            return None


def _parse_dmy_date(raw) -> str | None:
    """Parse '17-05-2026' (DD-MM-YYYY) → '2026-05-17'."""
    if raw in EMPTY_VALUES:
        return None
    text = cstr(raw).strip()
    if not text or text in ("None", "nan"):
        return None
    try:
        from datetime import datetime
        dt = datetime.strptime(text, "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
            return cstr(getdate(text))
        except Exception:
            return None


def _parse_trip_date(raw) -> str | None:
    """Parse Trip Date from the final template's DD-MM-YYYY format."""
    if raw in EMPTY_VALUES:
        return None
    if hasattr(raw, "date"):
        # Already a datetime object from openpyxl
        return raw.date().isoformat()
    text = cstr(raw).strip()
    if not text or text in ("None", "nan"):
        return None
    try:
        from datetime import datetime
        return datetime.strptime(text, "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _parse_cpt(raw) -> str | None:
    """CPT is stored as Data — store string representation."""
    if raw in EMPTY_VALUES:
        return None
    if hasattr(raw, "strftime"):
        return raw.strftime("%Y-%m-%d %H:%M:%S")
    text = cstr(raw).strip()
    if not text or text in ("None", "nan", " "):
        return None
    return text


def _parse_cancellation_datetime(raw) -> str | None:
    """VR Cancellation Date Time (UTC) — may be blank/space."""
    if raw in EMPTY_VALUES:
        return None
    if hasattr(raw, "strftime"):
        return raw.strftime("%Y-%m-%d %H:%M:%S")
    text = cstr(raw).strip()
    if not text or text in ("None", "nan"):
        return None
    try:
        return cstr(get_datetime(text))
    except Exception:
        return None


def _parse_check(raw) -> int:
    """Parse True/False/Yes/No/1/0 → 1 or 0."""
    if raw in (True, 1):
        return 1
    if raw in (False, 0):
        return 0
    text = cstr(raw).strip().lower()
    if text in ("yes", "true", "1"):
        return 1
    return 0


def _parse_currency(raw) -> float:
    """Parse currency: None → 0.0; '35.00 INR' → 35.0; 426.4 → 426.4."""
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return flt(raw)
    text = cstr(raw).strip()
    if not text or text in ("None", "nan"):
        return 0.0
    try:
        return flt(_extract_numeric(text))
    except ValueError:
        return 0.0


def _parse_float(raw) -> float:
    """Parse float: '40.84 KM ' → 40.84."""
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return flt(raw)
    text = cstr(raw).strip()
    if not text or text in ("None", "nan"):
        return 0.0
    try:
        return flt(_extract_numeric(text))
    except ValueError:
        return 0.0


def _parse_int(raw) -> int:
    """Parse int from raw value."""
    if raw is None:
        return 0
    if isinstance(raw, (int, float)):
        return cint(raw)
    text = cstr(raw).strip()
    if not text or text in ("None", "nan"):
        return 0
    try:
        return cint(_extract_numeric(text))
    except ValueError:
        return 0


def _parse_data(raw) -> str | None:
    """Parse Data field — return None for blank/null values."""
    if raw is None:
        return None
    text = cstr(raw).strip()
    if not text or text in ("None", "nan"):
        return None
    return text


def _parse_vr_status(raw) -> str | None:
    """Normalise VR Status from Amazon raw value."""
    text = _parse_data(raw)
    if not text:
        return None
    upper = text.upper()
    return VR_STATUS_MAP.get(upper, text.capitalize())


# ══════════════════════════════════════════════════════════════════
#  LINK LOOKUP
# ══════════════════════════════════════════════════════════════════

DEFAULT_LINK_LOOKUP_FIELDS = (
    "full_name",
    "customer_name",
    "company_name",
    "branch",
    "title",
    "user_name",
    "username",
    "email",
)

# In-memory link lookup cache keyed by doctype → {raw_value: resolved_name | None}
_link_cache: dict[str, dict[str, str | None]] = {}


def _init_link_cache() -> None:
    """Call once before parsing a file to reset the per-run cache."""
    _link_cache.clear()


@lru_cache(maxsize=128)
def _get_link_lookup_fields(link_doctype: str) -> tuple[str, ...]:
    meta = frappe.get_meta(link_doctype)
    lookup_fields = ["name"]

    if meta.title_field:
        lookup_fields.append(meta.title_field)

    for fieldname in cstr(meta.search_fields or "").split(","):
        fieldname = fieldname.strip()
        if fieldname:
            lookup_fields.append(fieldname)

    for fieldname in DEFAULT_LINK_LOOKUP_FIELDS:
        if meta.get_field(fieldname):
            lookup_fields.append(fieldname)

    seen = set()
    ordered_fields = []
    for fieldname in lookup_fields:
        if fieldname and fieldname not in seen:
            seen.add(fieldname)
            ordered_fields.append(fieldname)

    return tuple(ordered_fields)


def _resolve_link_value(link_doctype: str, raw_value) -> str | None:
    """Resolve a raw cell value to an existing docname. Returns None if not found."""
    value = cstr(raw_value).strip() if raw_value is not None else ""
    if not value or value in ("None", "nan"):
        return None

    bucket = _link_cache.setdefault(link_doctype, {})
    if value in bucket:
        return bucket[value]

    # Exact name match first (single indexed lookup)
    if frappe.db.exists(link_doctype, value):
        bucket[value] = value
        return value

    # Fuzzy lookup via configured search fields
    resolved = None
    for fieldname in _get_link_lookup_fields(link_doctype):
        if fieldname == "name":
            continue
        matches = frappe.get_all(link_doctype, filters={fieldname: value}, pluck="name", limit=2)
        if len(matches) == 1:
            resolved = matches[0]
            break
        if len(matches) > 1:
            frappe.throw(
                _("Multiple {0} records match {1} using {2}.").format(link_doctype, value, fieldname),
                title=_("Ambiguous Link Value"),
            )
    bucket[value] = resolved
    return resolved


def _resolve_employee_by_name(raw_value) -> str | None:
    """Resolve employee by full_name or name."""
    value = cstr(raw_value).strip() if raw_value is not None else ""
    if not value or value in ("None", "nan"):
        return None

    bucket = _link_cache.setdefault("Employee", {})
    if value in bucket:
        return bucket[value]

    # Exact name
    if frappe.db.exists("Employee", value):
        bucket[value] = value
        return value

    # Match by employee_name (full_name)
    matches = frappe.get_all("Employee", filters={"employee_name": value}, pluck="name", limit=2)
    if len(matches) == 1:
        bucket[value] = matches[0]
        return matches[0]
    if len(matches) > 1:
        # Take first — coordinator name match is best-effort
        bucket[value] = matches[0]
        return matches[0]

    bucket[value] = None
    return None


# ══════════════════════════════════════════════════════════════════
#  HEADER DETECTION — build dynamic column index maps
# ══════════════════════════════════════════════════════════════════

def _canonicalize_header(raw_header: str) -> str:
    """Resolve a raw header cell to a canonical header name.

    Tries exact match first, then case-insensitive alias lookup,
    then case-insensitive direct match against PARENT_HEADER_MAP / CHILD_HEADER_MAP keys.
    Returns the canonical name if matched, or the stripped raw value if not.
    """
    stripped = cstr(raw_header).strip()
    if not stripped:
        return stripped

    # Exact match (fast path)
    if stripped in PARENT_HEADER_MAP or stripped in CHILD_HEADER_MAP:
        return stripped

    # Case-insensitive alias lookup
    lower = stripped.lower()
    alias_match = HEADER_ALIASES.get(lower)
    if alias_match:
        return alias_match

    # Case-insensitive direct match against all known headers
    for known in list(PARENT_HEADER_MAP.keys()) + list(CHILD_HEADER_MAP.keys()):
        if known.lower() == lower:
            return known

    return stripped


def _build_col_idx_maps(
    header_row: list,
) -> tuple[dict[str, int], dict[str, int], list[str]]:
    """Build two dicts: fieldname → column_index, one for parent fields and one for child fields.

    Scans header_row, canonicalizes each header name, then maps to the fieldname
    from PARENT_HEADER_MAP or CHILD_HEADER_MAP.

    Returns (parent_col_idx, child_col_idx, unknown_headers).
    ``unknown_headers`` = list of raw header names that did not map to any field.
    """
    parent_col_idx: dict[str, int] = {}  # fieldname → col index
    child_col_idx: dict[str, int] = {}   # fieldname → col index
    unknown_headers: list[str] = []

    for col_idx, raw_header in enumerate(header_row):
        canonical = _canonicalize_header(raw_header)
        raw_label = cstr(raw_header).strip()
        if not canonical:
            # Blank header cell — only flag if the cell actually had something
            if raw_label:
                unknown_headers.append(raw_label)
            continue

        if canonical in PARENT_HEADER_MAP:
            spec = PARENT_HEADER_MAP[canonical]
            fn = spec["fieldname"]
            if fn not in parent_col_idx:  # first occurrence wins
                parent_col_idx[fn] = col_idx

        elif canonical in CHILD_HEADER_MAP:
            spec = CHILD_HEADER_MAP[canonical]
            fn = spec["fieldname"]
            if fn not in child_col_idx:  # first occurrence wins
                child_col_idx[fn] = col_idx

        else:
            # Header that matched no known field
            unknown_headers.append(raw_label or canonical)

    return parent_col_idx, child_col_idx, unknown_headers


# ══════════════════════════════════════════════════════════════════
#  ROW VALUE EXTRACTION
# ══════════════════════════════════════════════════════════════════

def _extract_parent_values(row: list, parent_col_idx: dict[str, int]) -> dict:
    """Extract parent field values from a single Excel row using dynamic column indices.

    Returns a dict of {fieldname: parsed_value}.
    """
    vals: dict = {}

    # Iterate in PARENT_HEADER_MAP order (insertion order) for consistent processing
    for header_name, spec in PARENT_HEADER_MAP.items():
        fn = spec["fieldname"]
        col_idx = parent_col_idx.get(fn)
        if col_idx is None:
            continue  # column not present in this file

        raw = row[col_idx] if col_idx < len(row) else None
        ft = spec["fieldtype"]

        if ft == "Link":
            link_doctype = spec.get("options", "")
            resolved = _resolve_link_value(link_doctype, raw) if link_doctype else _parse_data(raw)
            if resolved is not None:
                vals[fn] = resolved
            # keep raw display name for preview if it differs from the resolved ID
            raw_name = _parse_data(raw)
            if raw_name and raw_name != resolved:
                vals[f"_preview_{fn}"] = raw_name
        elif ft == "Employee":
            resolved = _resolve_employee_by_name(raw)
            if resolved is not None:
                vals[fn] = resolved
            # keep raw name for preview display
            raw_name = _parse_data(raw)
            if raw_name:
                vals[f"_preview_{fn}"] = raw_name
        elif ft == "Date":
            parsed = _parse_trip_date(raw)
            if parsed is not None:
                vals[fn] = parsed
        elif ft == "Datetime":
            parsed = _parse_cancellation_datetime(raw)
            if parsed is not None:
                vals[fn] = parsed
        elif ft == "Check":
            vals[fn] = _parse_check(raw)
        elif ft == "Currency":
            vals[fn] = _parse_currency(raw)
        elif ft == "Int":
            v = _parse_int(raw)
            if v:
                vals[fn] = v
        elif ft == "Data":
            if fn == "cpt":
                parsed = _parse_cpt(raw)
            else:
                parsed = _parse_data(raw)
            if parsed is not None:
                vals[fn] = parsed
        else:
            parsed = _parse_data(raw)
            if parsed is not None:
                vals[fn] = parsed

    return vals


def _extract_child_values(row: list, child_col_idx: dict[str, int], idx: int) -> dict:
    """Extract child field values from a single Excel row using dynamic column indices.

    ``idx`` is the 1-based child row index (for the ``idx`` column).
    Returns a dict ready for INSERT into tabAmazon Trip Detail.
    """
    vals: dict = {"idx": idx}

    # Iterate in CHILD_HEADER_MAP order (insertion order) for consistent processing
    for header_name, spec in CHILD_HEADER_MAP.items():
        fn = spec["fieldname"]
        col_idx = child_col_idx.get(fn)
        if col_idx is None:
            continue  # column not present in this file

        raw = row[col_idx] if col_idx < len(row) else None
        ft = spec["fieldtype"]

        if ft == "Select":
            parsed = _parse_vr_status(raw)
            if parsed is not None:
                vals[fn] = parsed
        elif ft == "Datetime":
            parsed = _parse_ist_datetime(raw)
            if parsed is not None:
                vals[fn] = parsed
        elif ft == "Date":
            date_format = spec.get("date_format", "")
            if date_format == "DD-MM-YYYY":
                parsed = _parse_dmy_date(raw)
            else:
                parsed = _parse_trip_date(raw)
            if parsed is not None:
                vals[fn] = parsed
        elif ft == "Currency":
            vals[fn] = _parse_currency(raw)
        elif ft == "Float":
            vals[fn] = _parse_float(raw)
        elif ft == "Small Text":
            parsed = _parse_data(raw)
            if parsed is not None:
                vals[fn] = parsed
        else:
            parsed = _parse_data(raw)
            if parsed is not None:
                vals[fn] = parsed

    return vals


# ══════════════════════════════════════════════════════════════════
#  FILE ITERATION
# ══════════════════════════════════════════════════════════════════

def _iter_file_rows(file_url: str):
    """Streaming file reader — yields (row_index, row_list, extension).

    Row 0 is the header. Only .csv is supported.
    All values are returned as strings.
    """
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    full_path = file_doc.get_full_path()
    extension = os.path.splitext(file_doc.file_name or file_doc.file_url or "")[1].lower()

    if extension == ".csv":
        with open(full_path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            reader = csv.reader(f)
            for idx, row in enumerate(reader):
                yield idx, row, extension

    else:
        frappe.throw(
            _("Unsupported file format: {0}. Only .csv files are supported. Please export the Amazon report as CSV.").format(extension),
            title=_("Unsupported File"),
        )


def _get_file_extension(file_url: str) -> str:
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    return os.path.splitext(file_doc.file_name or file_doc.file_url or "")[1].lower()


# ══════════════════════════════════════════════════════════════════
#  PREFETCH EXISTING RECORDS
# ══════════════════════════════════════════════════════════════════

def _prefetch_existing_by_tour_id(tour_ids: list[str]) -> dict[str, str]:
    """Return {tour_id_relay: name} for existing Amazon Trip records in batched queries."""
    unique_ids = [v for v in set(tour_ids) if v]
    if not unique_ids:
        return {}

    result: dict[str, str] = {}
    for i in range(0, len(unique_ids), TOUR_ID_PREFETCH_CHUNK):
        chunk = unique_ids[i : i + TOUR_ID_PREFETCH_CHUNK]
        rows = frappe.db.sql(
            "SELECT name, tour_id_relay "
            "FROM `tab" + TARGET_DOCTYPE + "` "
            "WHERE tour_id_relay IN %(ids)s",
            {"ids": tuple(chunk)},
            as_dict=True,
        )
        for r in rows:
            if r["tour_id_relay"] and r["tour_id_relay"] not in result:
                result[r["tour_id_relay"]] = r["name"]
    return result


# ══════════════════════════════════════════════════════════════════
#  PREVIEW RESPONSE HELPERS
# ══════════════════════════════════════════════════════════════════

def _build_warning(message: str, *, row: int | None = None, level: str = "warning") -> frappe._dict:
    warning = frappe._dict(message=message, level=level)
    if row is not None:
        warning.row = row
    return warning


def _empty_preview_response(file_type: str = "") -> frappe._dict:
    return frappe._dict(
        columns=[],
        data=[],
        warnings=[],
        summary=frappe._dict(
            file_type=file_type,
            total_rows=0,
            preview_rows=0,
            detected_columns=0,
            mapped_columns=0,
            unknown_columns=0,
            importable_rows=0,
            failed_rows=0,
            skipped_rows=0,
            new_rows=0,
            existing_rows=0,
        ),
        total_number_of_rows=0,
        can_import=False,
        import_groups=[],
        blocking_errors=[],
    )


# ══════════════════════════════════════════════════════════════════
#  MAIN PARSE / PREPARE IMPORT DATA
# ══════════════════════════════════════════════════════════════════

def _prepare_import_data(file_url: str) -> frappe._dict:
    """Stream-parse the XLSX/CSV file and group rows by Tour ID.

    Returns a frappe._dict with:
      - import_groups: list of frappe._dict, one per Tour ID, with
          tour_id, parent_values, child_rows, existing_docname, errors, skip
      - summary, warnings, blocking_errors, columns, data, can_import
    """
    _init_link_cache()

    extension = ""
    row_iter = _iter_file_rows(file_url)

    try:
        first = next(row_iter)
    except StopIteration:
        out = _empty_preview_response("")
        out.warnings.append(_build_warning(_("The selected file is empty."), level="error"))
        out.blocking_errors.append(_("The selected file is empty."))
        return out

    _header_idx, header_row, extension = first
    out = _empty_preview_response(extension.lstrip(".").upper())

    # ── Build dynamic column index maps from the header row ─────────
    parent_col_idx, child_col_idx, unknown_headers = _build_col_idx_maps(header_row)

    # ── Warn about each unmapped (unknown) column by name ───────────
    for uh in unknown_headers:
        out.warnings.append(
            _build_warning(
                _("Unknown column: '{0}' — this column will not be imported.").format(uh),
                level="warning",
            )
        )

    # ── Blocking check: Tour ID column must be present ───────────────
    if "tour_id_relay" not in parent_col_idx:
        msg = _("Tour ID column not found in file. Please ensure the file has a 'Tour ID' header column.")
        out.warnings.append(_build_warning(msg, level="error"))
        out.blocking_errors.append(msg)
        return out

    tour_id_col = parent_col_idx["tour_id_relay"]

    # ── collect all data rows ──────────────────────────────────────
    all_data_rows: list[tuple[int, list]] = []  # (excel_row_number, row)
    for row_idx, row, _ext in row_iter:
        # row_idx is 0-based; row 0 = header, row 1+ = data
        all_data_rows.append((row_idx, row))

    if not all_data_rows:
        msg = _("No data rows found in the selected file.")
        out.warnings.append(_build_warning(msg, level="error"))
        out.blocking_errors.append(msg)
        return out

    # ── group rows by Tour ID (using dynamic column index) ────────────
    # Ordered dict to preserve first-occurrence order
    groups_ordered: list[str] = []                    # tour_ids in order
    groups_map: dict[str, list[tuple[int, list]]] = {}  # tour_id → rows

    non_empty_count = 0
    for excel_row_number, row in all_data_rows:
        # Skip fully empty rows
        if not any(v is not None and cstr(v).strip() for v in row):
            continue
        non_empty_count += 1

        tour_id_raw = row[tour_id_col] if len(row) > tour_id_col else None
        tour_id = cstr(tour_id_raw).strip() if tour_id_raw is not None else ""
        if not tour_id or tour_id in ("None", "nan"):
            tour_id = f"__MISSING_{excel_row_number}__"

        if tour_id not in groups_map:
            groups_ordered.append(tour_id)
            groups_map[tour_id] = []
        groups_map[tour_id].append((excel_row_number, row))

    if non_empty_count == 0:
        msg = _("No data rows found in the selected file.")
        out.warnings.append(_build_warning(msg, level="error"))
        out.blocking_errors.append(msg)
        return out

    # ── prefetch existing Amazon Trips by tour_id_relay ───────────
    real_tour_ids = [tid for tid in groups_ordered if not tid.startswith("__MISSING_")]
    existing_map = _prefetch_existing_by_tour_id(real_tour_ids)

    # ── prefetch existing VR IDs from DB → {vr_id: parent_amazon_trip} ──
    # Used to block a VR ID that already belongs to a DIFFERENT Amazon Trip.
    # VR IDs under a Tour ID we are about to update are excluded (their rows
    # get replaced anyway).
    updating_trip_names = set(existing_map.values())
    existing_vr_map: dict[str, str] = {}
    _all_db_vr = frappe.db.sql(
        """
        SELECT vr_id, parent FROM `tabAmazon Trip Detail`
        WHERE parenttype = 'Amazon Trip' AND vr_id IS NOT NULL AND vr_id != ''
        """,
        as_dict=True,
    )
    for _r in _all_db_vr:
        if _r["parent"] not in updating_trip_names:
            existing_vr_map[cstr(_r["vr_id"]).strip()] = _r["parent"]

    # File-wide VR ID tracker → {vr_id: (tour_id, excel_row)} for cross-group dup detection
    seen_vr_ids_in_file: dict[str, tuple] = {}

    # ── build import_groups ────────────────────────────────────────
    importable = 0
    failed = 0
    skipped = 0
    new_rows = 0
    existing_rows = 0

    # Preview table: one row per Excel data row, ALL columns shown
    # Build column list based on DETECTED columns in the file, in file order
    def _field_label(fieldname: str) -> str:
        try:
            df = frappe.get_meta("Amazon Trip").get_field(fieldname)
            if df and df.label:
                return df.label
        except Exception:
            pass
        try:
            df = frappe.get_meta("Amazon Trip Detail").get_field(fieldname)
            if df and df.label:
                return df.label
        except Exception:
            pass
        return fieldname.replace("_", " ").title()

    preview_columns = [
        frappe._dict(id="import_action", name=_("Action"), fieldname="import_action", fieldtype="Data", skip_import=True),
    ]

    # Build a reverse map: fieldname → spec (for both maps)
    _fn_to_parent_spec = {spec["fieldname"]: spec for spec in PARENT_HEADER_MAP.values()}
    _fn_to_child_spec  = {spec["fieldname"]: spec for spec in CHILD_HEADER_MAP.values()}

    # Merge ALL detected columns (parent + child) sorted by their actual file column index
    # so preview matches the template column order exactly (interleaved, not parent-first).
    _all_detected_cols: list[tuple[str, int, bool]] = []  # (fieldname, col_idx, is_parent)
    for fn, col_idx in parent_col_idx.items():
        _all_detected_cols.append((fn, col_idx, True))
    for fn, col_idx in child_col_idx.items():
        _all_detected_cols.append((fn, col_idx, False))
    _all_detected_cols.sort(key=lambda x: x[1])

    for fn, _col_idx, is_parent in _all_detected_cols:
        spec = (_fn_to_parent_spec if is_parent else _fn_to_child_spec).get(fn, {})
        preview_columns.append(frappe._dict(
            id=fn, name=_field_label(fn), fieldname=fn,
            fieldtype=spec.get("fieldtype", "Data"), skip_import=False,
        ))
    out.columns = preview_columns

    # Rebuild ordered lists for downstream use (preserved for child/parent data routing)
    _detected_parent_fields_ordered = [fn for fn, _, is_p in _all_detected_cols if is_p]
    _detected_child_fields_ordered  = [fn for fn, _, is_p in _all_detected_cols if not is_p]

    # Pre-build ordered field name lists for fast row assembly
    _all_preview_fields = [c.fieldname for c in preview_columns if c.fieldname != "import_action"]
    _parent_field_set  = set(_detected_parent_fields_ordered)
    _child_field_set   = set(_detected_child_fields_ordered)

    # Batch-prefetch parent field values for all existing Amazon Trips in one query
    # instead of one frappe.db.get_value per group (avoids N round-trips to DB).
    _parent_cache: dict[str, dict] = {}
    try:
        _existing_names = list(set(v for v in existing_map.values() if v))
        if _existing_names:
            _field_list = ", ".join(f"`{f}`" for f in PARENT_WRITE_FIELDS)
            _in_clause = ", ".join(["%s"] * len(_existing_names))
            _parent_rows = frappe.db.sql(
                f"SELECT `name`, {_field_list} FROM `tab{TARGET_DOCTYPE}` WHERE `name` IN ({_in_clause})",
                tuple(_existing_names),
                as_dict=True,
            )
            for _r in _parent_rows:
                _parent_cache[_r["name"]] = _r
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Amazon Trip Import: batch prefetch failed, falling back to per-group lookup")
        _parent_cache = {}

    # Track Tour IDs seen in this file to detect duplicates
    seen_tour_ids_in_file: dict[str, int] = {}
    # Cache vehicle_no existence checks (True = exists, False = not in master)
    _vehicle_no_cache: dict[str, bool] = {}

    for tour_id in groups_ordered:
        rows_for_group = groups_map[tour_id]
        first_row_num, first_row = rows_for_group[0]
        errors: list[str] = []
        row_warnings: list[str] = []
        existing_docname = existing_map.get(tour_id)

        # ── BLOCKING: Tour ID missing ──────────────────────────────
        if tour_id.startswith("__MISSING_"):
            errors.append(f"Tour ID column is missing a value for row {first_row_num}.")
            failed += 1
            grp = frappe._dict(
                tour_id=tour_id,
                parent_values={},
                child_rows=[],
                existing_docname=None,
                errors=errors,
                row_warnings=[],
                skip=False,
                import_action="Error — Missing Tour ID",
                excel_row_number=first_row_num,
                vr_count=len(rows_for_group),
            )
            out.import_groups.append(grp)
            out.warnings.append(_build_warning(errors[0], row=first_row_num, level="error"))
            # Add a preview row for every raw CSV row in this group so the user
            # can see the blank-Tour-ID row in the preview table as an error.
            for chi, (_rn, raw_row) in enumerate(rows_for_group):
                row_data = ["Error — Missing Tour ID" if chi == 0 else ""]
                for fn in _all_preview_fields:
                    col = parent_col_idx.get(fn) if fn in _parent_field_set else child_col_idx.get(fn)
                    val = raw_row[col] if col is not None and col < len(raw_row) else ""
                    row_data.append(cstr(val))
                out.data.append(row_data)
            continue

        # ── BUSINESS LOGIC: Duplicate Tour ID in same file ─────────
        if tour_id in seen_tour_ids_in_file:
            row_warnings.append(
                f"Tour ID '{tour_id}' appears in rows {seen_tour_ids_in_file[tour_id]} and {first_row_num}. "
                f"All VR IDs will be merged under one Amazon Trip."
            )
            out.warnings.append(_build_warning(row_warnings[-1], row=first_row_num, level="warning"))
        else:
            seen_tour_ids_in_file[tour_id] = first_row_num

        # This final Amazon sheet is an update feed. The trip and its mandatory
        # master data must already have been entered by the user.
        if not existing_docname:
            errors.append(
                f"Tour ID '{tour_id}' does not exist in Amazon Trip. "
                "Create the trip and enter its mandatory details before importing this file."
            )

        # ── Extract parent values from first row ───────────────────
        parent_values: dict = {}
        _parent_link_warnings: list[tuple[str, str]] = []  # populated below; used in child row loop
        if existing_docname:
            try:
                existing_values = _parent_cache.get(existing_docname)
                if existing_values is None:
                    # cache miss (batch prefetch may have failed) — fall back to single DB call
                    existing_values = frappe.db.get_value(
                        TARGET_DOCTYPE, existing_docname, PARENT_WRITE_FIELDS, as_dict=True
                    ) or {}
                parent_values.update(existing_values)
                _csv_extracted = _extract_parent_values(first_row, parent_col_idx)
                parent_values.update(_csv_extracted)
                # Warn when a Link/Employee value was in CSV but not found in master.
                # Check _csv_extracted (not merged parent_values) so existing-doc values
                # don't mask unresolved CSV values.
                # Collect unresolved parent link messages to repeat on every child row.
                for _hdr, _spec in PARENT_HEADER_MAP.items():
                    _fn = _spec["fieldname"]
                    if _spec.get("fieldtype") not in ("Link", "Employee"):
                        continue
                    if _fn not in parent_col_idx:
                        continue  # column not in this file
                    _preview_key = f"_preview_{_fn}"
                    if _preview_key not in _csv_extracted:
                        continue  # cell was blank — nothing to warn about
                    if _fn in _csv_extracted:
                        continue  # CSV value resolved successfully
                    _raw_val = _csv_extracted.get(_preview_key)
                    if not _raw_val:
                        continue
                    _link_dt = _spec.get("options") or "Employee"
                    _parent_link_warnings.append(
                        (f"{_hdr} '{_raw_val}' not found in {_link_dt} master — this field will not be updated.", _link_dt)
                    )
            except Exception as e:
                errors.append(f"Error reading parent fields for Tour ID '{tour_id}': {cstr(e)}")
                frappe.log_error(frappe.get_traceback(), f"Amazon Trip Import parent parse error: tour_id={tour_id}")

        # ── GROUP-LEVEL: Mandatory field checks ────────────────────
        if not errors:
            MANDATORY_LABELS = {
                "trip_date": "Trip Date",
            }
            for mf in MANDATORY_PARENT_FIELDS:
                if parent_values.get(mf) in EMPTY_VALUES:
                    ml = MANDATORY_LABELS.get(mf, mf.replace("_", " ").title())
                    errors.append(f"{ml} is required for Tour ID '{tour_id}' (row {first_row_num}).")

        # ── Extract child rows with row-level validations ──────────
        child_rows: list[dict] = []
        if not errors:
            for child_idx, (row_num, row) in enumerate(rows_for_group, start=1):
                try:
                    child_vals = _extract_child_values(row, child_col_idx, child_idx)
                    child_rows.append(child_vals)

                    vr_id_val = (child_vals.get("vr_id") or "").strip()

                    # ── VR ID GLOBAL UNIQUENESS (blocking) ─────────────
                    if vr_id_val:
                        # (a) same VR ID in another Tour ID group in THIS file
                        if vr_id_val in seen_vr_ids_in_file:
                            prev_tour, prev_row = seen_vr_ids_in_file[vr_id_val]
                            if prev_tour != tour_id:
                                errors.append(
                                    f"VR ID '{vr_id_val}' (row {row_num}) already appears under a "
                                    f"different Tour ID '{prev_tour}' (row {prev_row}) in this file. "
                                    f"A VR ID can belong to only one Tour ID."
                                )
                            else:
                                errors.append(
                                    f"VR ID '{vr_id_val}' is duplicated within Tour ID '{tour_id}' "
                                    f"(rows {prev_row} and {row_num})."
                                )
                        else:
                            seen_vr_ids_in_file[vr_id_val] = (tour_id, row_num)

                        # (b) VR ID already used by a DIFFERENT Amazon Trip in DB
                        clash_trip = existing_vr_map.get(vr_id_val)
                        if clash_trip:
                            errors.append(
                                f"VR ID '{vr_id_val}' (row {row_num}) already exists in another "
                                f"Amazon Trip '{clash_trip}'. A VR ID can belong to only one Amazon Trip."
                            )

                    # Start Date invalid — check raw value via dynamic index
                    _start_date_col = child_col_idx.get("start_date")
                    if _start_date_col is not None:
                        raw_start = cstr(row[_start_date_col] if len(row) > _start_date_col else "").strip()
                        if raw_start and not child_vals.get("start_date"):
                            msg = f"Row {row_num} (VR ID: {vr_id_val}): Start Date '{raw_start}' has invalid format. Expected: MM/DD/YYYY HH:MM:SS IST."
                            row_warnings.append(msg)
                            out.warnings.append(_build_warning(msg, row=row_num, level="warning"))

                    # End Date invalid
                    _end_date_col = child_col_idx.get("end_date")
                    if _end_date_col is not None:
                        raw_end = cstr(row[_end_date_col] if len(row) > _end_date_col else "").strip()
                        if raw_end and not child_vals.get("end_date"):
                            msg = f"Row {row_num} (VR ID: {vr_id_val}): End Date '{raw_end}' has invalid format. Expected: MM/DD/YYYY HH:MM:SS IST."
                            row_warnings.append(msg)
                            out.warnings.append(_build_warning(msg, row=row_num, level="warning"))

                    # End Date < Start Date
                    if child_vals.get("start_date") and child_vals.get("end_date"):
                        try:
                            from frappe.utils import get_datetime as _gdt
                            if _gdt(child_vals["end_date"]) < _gdt(child_vals["start_date"]):
                                msg = f"Row {row_num} (VR ID: {vr_id_val}): End Date is before Start Date."
                                row_warnings.append(msg)
                                out.warnings.append(_build_warning(msg, row=row_num, level="warning"))
                        except Exception:
                            pass

                    # Bill Date invalid
                    _bill_date_col = child_col_idx.get("original_bill_date")
                    if _bill_date_col is not None:
                        raw_bill_date = cstr(row[_bill_date_col] if len(row) > _bill_date_col else "").strip()
                        if raw_bill_date and not child_vals.get("original_bill_date"):
                            msg = f"Row {row_num} (VR ID: {vr_id_val}): Bill Date '{raw_bill_date}' has invalid format. Expected: DD-MM-YYYY."
                            row_warnings.append(msg)
                            out.warnings.append(_build_warning(msg, row=row_num, level="warning"))

                    # VR Status invalid
                    _vr_status_col = child_col_idx.get("vr_status")
                    if _vr_status_col is not None:
                        raw_vr_status = cstr(row[_vr_status_col] if len(row) > _vr_status_col else "").strip()
                        if raw_vr_status:
                            parsed_status = child_vals.get("vr_status") or ""
                            if parsed_status not in VALID_VR_STATUSES:
                                msg = f"Row {row_num} (VR ID: {vr_id_val}): VR Status '{raw_vr_status}' is not valid. Allowed values: Completed, Cancelled, Dummy."
                                row_warnings.append(msg)
                                out.warnings.append(_build_warning(msg, row=row_num, level="warning"))

                    # Trip Status (child row) invalid
                    _trip_status_col = child_col_idx.get("trip_status")
                    if _trip_status_col is not None:
                        raw_trip_status = cstr(row[_trip_status_col] if len(row) > _trip_status_col else "").strip()
                        if raw_trip_status and raw_trip_status not in VALID_TRIP_STATUSES:
                            msg = f"Row {row_num} (VR ID: {vr_id_val}): Trip Status '{raw_trip_status}' is not valid. Allowed values: Closed, Unbilled, Under Dispute."
                            row_warnings.append(msg)
                            out.warnings.append(_build_warning(msg, row=row_num, level="warning"))

                    # Lane empty when VR ID present
                    if vr_id_val and not child_vals.get("lane"):
                        msg = f"Row {row_num} (VR ID: {vr_id_val}): Lane is empty."
                        row_warnings.append(msg)
                        out.warnings.append(_build_warning(msg, row=row_num, level="warning"))

                    # Vehicle No not in Vehicle master — warn for every row that has this value
                    _vno_col = child_col_idx.get("vehicle_no")
                    if _vno_col is not None:
                        _raw_vno = cstr(row[_vno_col] if len(row) > _vno_col else "").strip()
                        if _raw_vno and _raw_vno not in ("None", "nan"):
                            if _raw_vno not in _vehicle_no_cache:
                                _vehicle_no_cache[_raw_vno] = bool(frappe.db.exists("Vehicle", _raw_vno))
                            if not _vehicle_no_cache[_raw_vno]:
                                _vno_msg = f"Row {row_num} (VR ID: {vr_id_val}): Vehicle No '{_raw_vno}' not found in Vehicle master."
                                out.warnings.append(_build_warning(_vno_msg, row=row_num, level="warning"))

                    # Parent Link field warnings — emit on every child row so user sees
                    # which rows are affected when a master value is missing.
                    # NOTE: do NOT name the throwaway "_" here — that would shadow the
                    # module-level translation function _() and break _("...") calls
                    # elsewhere in this function (UnboundLocalError).
                    for _plw_msg, _plw_dt in _parent_link_warnings:
                        out.warnings.append(_build_warning(
                            f"Row {row_num} (VR ID: {vr_id_val}): {_plw_msg}",
                            row=row_num,
                            level="warning",
                        ))

                except Exception as e:
                    errors.append(f"Error processing row {row_num}: {cstr(e)}")

            # BUSINESS LOGIC: No child rows (no VR IDs)
            if not child_rows and not errors:
                errors.append(f"Tour ID '{tour_id}' has no valid VR ID rows to import.")

            # ── Roll up Bill No / Bill Date / Trip Status to the PARENT ──
            # If every child row shares the same value, copy it to the parent
            # (these fields exist on both the Amazon Trip parent and each child).
            if child_rows and not errors:
                # trip_status intentionally excluded — never derived from the file;
                # the user sets it manually on the trip.
                for _rollup_field in ("original_sadashiv_bill_no", "original_bill_date"):  # "trip_status" removed
                    _child_vals = [c.get(_rollup_field) for c in child_rows if c.get(_rollup_field) not in EMPTY_VALUES]
                    if _child_vals and len(set(cstr(v) for v in _child_vals)) == 1:
                        parent_values[_rollup_field] = _child_vals[0]

                # ── Rollup parent computed amounts ──────────────────────────────
                # computed_total_freight = trip_cost (set in _apply_before_save_calcs)
                # computed_billed_amount = first non-zero child row value (Amazon repeats
                #   the tour-level billed amount on every VR row — do not sum).
                # freight_difference is derived later in _apply_before_save_calcs.
                parent_values["computed_billed_amount"] = next(
                    (flt(c.get("computed_billed_amount") or 0) for c in child_rows
                     if flt(c.get("computed_billed_amount") or 0)),
                    0.0,
                )

        # ── Determine action ───────────────────────────────────────
        skip = False
        existing_docname = existing_map.get(tour_id) if not errors else None
        if errors:
            import_action = _("Error")
            failed += 1
        else:
            import_action = _("Update Existing")
            existing_rows += 1
            importable += 1

        grp = frappe._dict(
            tour_id=tour_id,
            parent_values=parent_values if not errors else {},
            child_rows=child_rows,
            existing_docname=existing_docname,
            errors=errors,
            skip=skip,
            import_action=import_action,
            excel_row_number=first_row_num,
            vr_count=len(rows_for_group),
        )
        out.import_groups.append(grp)

        for err in errors:
            out.warnings.append(_build_warning(err, row=first_row_num, level="error"))
            # Group-level errors are blocking — the entire import stops if ANY group fails.
            out.blocking_errors.append(err)

        # Preview rows: one per Excel data row (individual VR ID), all columns
        pv = parent_values if not errors else {}
        rows_to_preview = child_rows if child_rows else [{}]
        for child_idx_p, child_row_p in enumerate(rows_to_preview):
            row_data = [import_action if child_idx_p == 0 else ""]
            for fn in _all_preview_fields:
                if fn in _parent_field_set:
                    # use raw display value if stored (e.g. employee name instead of ID)
                    val = pv.get(f"_preview_{fn}") or pv.get(fn) or ""
                    row_data.append(cstr(val))
                else:
                    row_data.append(cstr(child_row_p.get(fn) or ""))
            out.data.append(row_data)

    total_groups = len(out.import_groups)
    if total_groups == 0:
        msg = _("No importable Tour ID groups found in the file.")
        out.warnings.append(_build_warning(msg, level="error"))
        out.blocking_errors.append(msg)

    out.summary.total_rows = non_empty_count
    out.summary.preview_rows = len(out.data)
    out.summary.detected_columns = len(header_row) if header_row else 0
    out.summary.mapped_columns = len(parent_col_idx) + len(child_col_idx)
    out.summary.unknown_columns = max(0, len(header_row) - out.summary.mapped_columns) if header_row else 0
    out.summary.importable_rows = importable
    out.summary.failed_rows = failed
    out.summary.skipped_rows = skipped
    out.summary.new_rows = new_rows
    out.summary.existing_rows = existing_rows
    out.total_number_of_rows = non_empty_count
    out.total_groups = total_groups
    out.can_import = bool(not out.blocking_errors and importable > 0)

    # Lightweight Tour ID summary for the confirmation dialog (no child-row data).
    out.tour_id_summary = [
        {
            "tour_id": grp.tour_id if not cstr(grp.tour_id).startswith("__MISSING_") else "(blank)",
            "import_action": grp.import_action or "",
            "vr_count": grp.vr_count or 0,
            "has_errors": bool(grp.errors),
        }
        for grp in out.import_groups
    ]

    return out


def _preview_payload_from_parsed(parsed: dict) -> dict:
    """Strip heavy import_groups before returning to UI. tour_id_summary is kept (lightweight)."""
    out = frappe._dict(parsed)
    out.pop("import_groups", None)
    out.pop("blocking_errors", None)
    return out


# ══════════════════════════════════════════════════════════════════
#  BEFORE-SAVE CALCULATIONS (mirrored from AmazonTrip.before_save)
# ══════════════════════════════════════════════════════════════════

def _apply_before_save_calcs(parent_values: dict) -> None:
    """Compute derived parent fields in-memory before bulk insert.

    Fields computed:
      - trip_cost = sum of all manual charges + freight
      - total_vendor_freight = vendor_freight + vendor_freight_extra

    trip_status is NOT auto-computed here (user sets it manually on the form).
    freight_difference on parent is NOT computed here (it lives in child rows).
    """
    # trip_cost
    parent_values["trip_cost"] = (
        flt(parent_values.get("freight") or 0)
        + flt(parent_values.get("fuel_surcharge_manual") or 0)
        + flt(parent_values.get("cancellation_charge_manual") or 0)
        + flt(parent_values.get("detention_charge_manual") or 0)
        + flt(parent_values.get("ot_cost_manual") or 0)
        + flt(parent_values.get("extra_distance_cost_manual") or 0)
        + flt(parent_values.get("toll_parking_charges_manual") or 0)
    )

    # total_vendor_freight
    parent_values["total_vendor_freight"] = (
        flt(parent_values.get("vendor_freight") or 0)
        + flt(parent_values.get("vendor_freight_extra") or 0)
    )

    # freight_difference = computed_billed_amount - computed_total_freight
    # (mirrors AmazonTrip._calc_freight_difference; the two computed amounts are
    #  summed from child VR ID rows in _prepare_import_data.)
    parent_values["freight_difference"] = (
        flt(parent_values.get("computed_billed_amount") or 0)
        - flt(parent_values.get("computed_total_freight") or 0)
    )


# ══════════════════════════════════════════════════════════════════
#  AUTONAME RESERVATION
# ══════════════════════════════════════════════════════════════════

def _get_current_fy_short() -> str:
    """Match AmazonTrip.autoname — 'YY-YY' for April-start fiscal year."""
    d = getdate(nowdate())
    fy_start = d.year if d.month >= 4 else d.year - 1
    return f"{str(fy_start)[-2:]}-{str(fy_start + 1)[-2:]}"


def _reserve_autonames(count: int, fy_short: str) -> list[str]:
    """Atomically reserve ``count`` consecutive autonames from tabSeries.

    Matches AmazonTrip.autoname pattern: AT-{fy_short}-.#####
    """
    if count <= 0:
        return []

    prefix = f"AT-{fy_short}-"

    frappe.db.sql(
        """
        INSERT INTO `tabSeries` (name, `current`)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE `current` = `current` + VALUES(`current`)
        """,
        (prefix, count),
    )
    row = frappe.db.sql(
        "SELECT `current` FROM `tabSeries` WHERE name = %s",
        (prefix,),
        as_dict=True,
    )
    end_num = int(row[0]["current"]) if row else count
    start_num = end_num - count + 1
    return [f"{prefix}{i:05d}" for i in range(start_num, end_num + 1)]


# ══════════════════════════════════════════════════════════════════
#  BULK UPSERT — PARENT
# ══════════════════════════════════════════════════════════════════

# All writable parent fields (excluding computed/system fields that are not in import)
PARENT_WRITE_FIELDS = [
    "company_name", "customer", "trip_type", "branch", "trip_coordinator",
    "trip_date", "tour_id_relay", "facility_sequence", "cpt", "is_cpt_truck",
    "cr_id", "shipper_accounts", "equipment_type", "estimated_cost",
    "tender_status", "driver_relay", "vehicle_id", "vr_cancellation_date_time_utc",
    "transit_operator_type", "spot_work", "freight", "fuel_surcharge_manual",
    "cancellation_charge_manual", "detention_charge_manual", "ot_cost_manual",
    "extra_distance_cost_manual", "toll_parking_charges_manual",
    "vendor", "vendor_freight", "vendor_freight_extra",
    "duplicate_trips", "duplicate_record_no", "manual_trip",
    # rolled up from child rows when all VR IDs share the same value
    "original_sadashiv_bill_no", "original_bill_date",  # "trip_status" removed — never written by import; user sets it manually
    # summed from all VR ID child rows in _prepare_import_data (Template cols 32 & 33)
    "computed_total_freight", "computed_billed_amount",
    # computed by _apply_before_save_calcs
    "trip_cost", "total_vendor_freight", "freight_difference",
]


def _bulk_upsert_amazon_trip(
    batch: list[dict],
    *,
    user: str,
    now: str,
) -> None:
    """Execute one multi-row INSERT ... ON DUPLICATE KEY UPDATE for the parent batch.

    Each item in ``batch`` must be a dict with:
      - name: str (document name)
      - is_new: bool
      - values: dict of {fieldname: value}
    """
    if not batch:
        return

    sys_cols = ["name", "creation", "modified", "modified_by", "owner", "docstatus", "idx"]
    all_cols = sys_cols + PARENT_WRITE_FIELDS
    col_sql = ", ".join(f"`{c}`" for c in all_cols)
    placeholder_row = "(" + ", ".join(["%s"] * len(all_cols)) + ")"

    values_sql_parts: list[str] = []
    params: list = []

    for row in batch:
        values_sql_parts.append(placeholder_row)
        fv = row["values"]
        params.extend([
            row["name"],
            now,   # creation — ignored on UPDATE
            now,   # modified
            user,  # modified_by
            user,  # owner — ignored on UPDATE
            0,     # docstatus
            0,     # idx
        ])
        for fname in PARENT_WRITE_FIELDS:
            params.append(fv.get(fname))

    odku_cols = ["modified", "modified_by", *PARENT_WRITE_FIELDS]
    odku_sql = ", ".join(f"`{c}` = VALUES(`{c}`)" for c in odku_cols)

    sql = (
        f"INSERT INTO `tab{TARGET_DOCTYPE}` ({col_sql}) "
        f"VALUES {', '.join(values_sql_parts)} "
        f"ON DUPLICATE KEY UPDATE {odku_sql}"
    )
    frappe.db.sql(sql, params)


# ══════════════════════════════════════════════════════════════════
#  CHILD TABLE INSERT / REPLACE
# ══════════════════════════════════════════════════════════════════

CHILD_WRITE_FIELDS = [
    "vr_id", "vr_status", "load_id", "vehicle_no", "start_date", "end_date",
    "lane", "city", "operator_type_amazon", "total_distance", "contract_type",
    "rate_type", "item_type", "work_type", "base_rate", "fuel_surcharge_amazon",
    "cancellation_charge_amazon", "detention_charge_amazon", "ot_cost_amazon",
    "extra_distance_cost_amazon", "toll_parking_charges_amazon", "tax_percent",
    "gross_pay_amt_excl_tax", "gross_tax_amt", "gross_pay_amt", "comments",
    "extra_hours", "extra_km", "remarks3", "original_sadashiv_bill_no",
    "original_bill_date", "computed_total_freight", "computed_billed_amount",
    "freight_difference", "trip_status",
]


def _delete_child_rows(parent_name: str) -> None:
    """Delete all existing child rows for an Amazon Trip parent."""
    frappe.db.sql(
        "DELETE FROM `tab" + CHILD_DOCTYPE + "` WHERE parent = %s AND parenttype = %s",
        (parent_name, TARGET_DOCTYPE),
    )


def _bulk_insert_child_rows(
    parent_name: str,
    child_rows: list[dict],
    *,
    user: str,
    now: str,
) -> None:
    """Bulk INSERT child rows into tabAmazon Trip Detail."""
    if not child_rows:
        return

    sys_cols = ["name", "creation", "modified", "modified_by", "owner",
                "docstatus", "idx", "parent", "parenttype", "parentfield"]
    all_cols = sys_cols + CHILD_WRITE_FIELDS
    col_sql = ", ".join(f"`{c}`" for c in all_cols)
    placeholder_row = "(" + ", ".join(["%s"] * len(all_cols)) + ")"

    values_sql_parts: list[str] = []
    params: list = []

    for child_row in child_rows:
        values_sql_parts.append(placeholder_row)
        child_name = frappe.generate_hash(length=10)
        params.extend([
            child_name,
            now,
            now,
            user,
            user,
            0,                    # docstatus
            child_row.get("idx", 1),
            parent_name,
            TARGET_DOCTYPE,
            CHILD_PARENTFIELD,
        ])
        for fname in CHILD_WRITE_FIELDS:
            params.append(child_row.get(fname))

    sql = (
        f"INSERT INTO `tab{CHILD_DOCTYPE}` ({col_sql}) "
        f"VALUES {', '.join(values_sql_parts)}"
    )
    frappe.db.sql(sql, params)


# ══════════════════════════════════════════════════════════════════
#  PROGRESS / STATE HELPERS
# ══════════════════════════════════════════════════════════════════

_PROGRESS_FIELDS = (
    "job_status",
    "job_id",
    "started_at",
    "finished_at",
    "progress_stage",
    "progress_current",
    "progress_total",
    "inserted_count",
    "updated_count",
    "skipped_count",
    "failed_count",
    "throughput_rows_per_sec",
    "cancel_requested",
    "failure_log_json",
    "failure_csv_attachment",
)


def _set_state(docname: str, **fields) -> None:
    if not fields:
        return
    frappe.db.set_value(IMPORT_DOCTYPE, docname, fields, update_modified=False)


def _publish(docname: str, user: str | None, payload: dict) -> None:
    payload = {**payload, "docname": docname}
    frappe.publish_realtime(
        event=REALTIME_EVENT,
        message=payload,
        doctype=IMPORT_DOCTYPE,
        docname=docname,
        user=user,
    )


def _is_cancelled(docname: str) -> bool:
    return bool(frappe.db.get_value(IMPORT_DOCTYPE, docname, "cancel_requested"))


def _reset_state(docname: str) -> None:
    _set_state(
        docname,
        job_status="Queued",
        job_id="",
        started_at=None,
        finished_at=None,
        progress_stage="Queued",
        progress_current=0,
        progress_total=0,
        inserted_count=0,
        updated_count=0,
        skipped_count=0,
        failed_count=0,
        throughput_rows_per_sec=0,
        cancel_requested=0,
        failure_log_json="",
        failure_csv_attachment="",
    )
    frappe.db.commit()


# ══════════════════════════════════════════════════════════════════
#  PUBLIC WHITELISTED API
# ══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_import_preview(docname: str | None = None, file_url: str | None = None):
    """Async preview — returns cached payload instantly, else enqueues a worker.

    Response shape:
      * ``{status: "ready", preview: {...}}``  — preview available inline
      * ``{status: "queued", job_id}``         — worker started; subscribe to realtime
      * ``{status: "loading", job_id}``        — job already running for this doc
      * ``{status: "empty"}``                  — no file selected yet
    """
    if docname:
        doc = frappe.get_doc(IMPORT_DOCTYPE, docname)
        doc.check_permission("read")
        file_url = file_url or doc.file_selection
    else:
        frappe.has_permission(IMPORT_DOCTYPE, "read", throw=True)

    if not file_url:
        return {"status": "empty"}

    fingerprint = _file_fingerprint(file_url)
    cached = _cache_get_parsed(fingerprint)
    if cached:
        return {"status": "ready", "preview": _preview_payload_from_parsed(cached)}

    if docname:
        current_status = frappe.db.get_value(IMPORT_DOCTYPE, docname, "job_status")
        active_fp = _get_active_fingerprint(docname)
        if current_status in ("Queued", "Previewing", "Running") and active_fp == fingerprint:
            job_id = frappe.db.get_value(IMPORT_DOCTYPE, docname, "job_id") or ""
            if _job_is_active(job_id):
                return {"status": "loading", "job_id": job_id}
            # Job was lost — fall through and re-enqueue.

    if docname:
        _reset_state(docname)
        _set_state(docname, job_status="Previewing", progress_stage="Preparing preview…")
        _set_active_fingerprint(docname, fingerprint)
        frappe.db.commit()
        job = frappe.enqueue(
            "logicore.logicore.doctype.amazon_trip___import.amazon_trip___import._run_preview_job",
            queue="short",
            timeout=300,
            job_name=f"amazon_trip_preview::{docname}",
            docname=docname,
            file_url=file_url,
            fingerprint=fingerprint,
            user=frappe.session.user,
        )
        job_id = getattr(job, "id", "") or ""
        _set_state(docname, job_id=job_id)
        frappe.db.commit()
        return {"status": "queued", "job_id": job_id, "docname": docname}

    # No docname: fall back to sync parse (kept for legacy callers).
    parsed = _prepare_import_data(file_url)
    _cache_parsed(fingerprint, dict(parsed))
    return {"status": "ready", "preview": _preview_payload_from_parsed(parsed)}


@frappe.whitelist()
def get_cached_preview(docname: str | None = None, file_url: str | None = None):
    if docname:
        doc = frappe.get_doc(IMPORT_DOCTYPE, docname)
        doc.check_permission("read")
        file_url = file_url or doc.file_selection
    if not file_url:
        return {"status": "empty"}
    fingerprint = _file_fingerprint(file_url)
    cached = _cache_get_parsed(fingerprint)
    if cached:
        return {"status": "ready", "preview": _preview_payload_from_parsed(cached)}
    return {"status": "missing"}


@frappe.whitelist()
def import_amazon_trips(docname: str | None = None, file_url: str | None = None):
    """Enqueue the import job and return immediately with job_id."""
    if not docname:
        frappe.throw(_("Please save the Import record before importing."))

    doc = frappe.get_doc(IMPORT_DOCTYPE, docname)
    doc.check_permission("write")
    file_url = file_url or doc.file_selection

    if not file_url:
        frappe.throw(_("Please select a CSV or Excel file first."))

    if doc.job_status in ("Queued", "Running", "Previewing"):
        frappe.throw(
            _("An import is already {0} for this record. Please cancel it first.").format(doc.job_status),
            title=_("Import In Progress"),
        )

    _reset_state(docname)

    job = frappe.enqueue(
        "logicore.logicore.doctype.amazon_trip___import.amazon_trip___import._run_import_job",
        queue="long",
        timeout=1800,
        job_name=f"amazon_trip_import::{docname}",
        docname=docname,
        file_url=file_url,
        user=frappe.session.user,
    )
    job_id = getattr(job, "id", "") or ""
    _set_state(docname, job_id=job_id)
    frappe.db.commit()

    return {"job_id": job_id, "status": "Queued", "docname": docname}


@frappe.whitelist()
def cancel_amazon_trip_import(docname: str):
    doc = frappe.get_doc(IMPORT_DOCTYPE, docname)
    doc.check_permission("write")

    if frappe.session.user != doc.owner:
        frappe.throw(
            _("Only the user who started this import ({0}) can cancel it.").format(doc.owner),
            title=_("Not Allowed"),
        )

    if doc.job_status not in ("Queued", "Running", "Previewing"):
        return {"ok": False, "reason": f"Job is already {doc.job_status}"}

    _set_state(docname, cancel_requested=1)
    frappe.db.commit()
    _publish(docname, doc.owner, {"stage": "Cancelling…", "cancel_requested": 1})
    return {"ok": True}


@frappe.whitelist()
def get_import_status(docname: str):
    doc = frappe.get_doc(IMPORT_DOCTYPE, docname)
    doc.check_permission("read")
    return {f: doc.get(f) for f in _PROGRESS_FIELDS}


# ══════════════════════════════════════════════════════════════════
#  BACKGROUND WORKERS
# ══════════════════════════════════════════════════════════════════

def _run_preview_job(docname: str, file_url: str, fingerprint: str, user: str) -> None:
    """Worker: stream-parse the file, cache the payload, publish progress."""
    try:
        frappe.set_user(user)
    except Exception:
        pass

    started = time.time()
    _set_state(docname, job_status="Previewing", progress_stage="Preparing preview…")
    frappe.db.commit()
    _publish(docname, user, {"stage": "Preparing preview…", "current": 0, "total": 0, "phase": "preview"})

    try:
        parsed = _prepare_import_data(file_url)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Amazon Trip preview failed: {docname}")
        # Use job_status="Draft" (not "Failed") so the JS does not treat this as an
        # import failure and does not trigger reload_doc → refresh → re-queue loop.
        _set_state(
            docname,
            job_status="Draft",
            finished_at=now_datetime(),
            progress_stage="Preview failed",
        )
        frappe.db.commit()
        _publish(docname, user, {
            "stage": "Preview failed",
            "done": True,
            "status": "PreviewFailed",
            "error": cstr(e),
            "phase": "preview",
        })
        return

    _cache_parsed(fingerprint, dict(parsed))
    total = parsed.summary.total_rows
    _set_state(
        docname,
        job_status="Draft",
        finished_at=now_datetime(),
        progress_stage="Preview ready",
        progress_total=total,
        progress_current=total,
    )
    frappe.db.commit()
    elapsed = max(time.time() - started, 0.001)
    _publish(
        docname,
        user,
        {
            "stage": "Preview ready",
            "current": total,
            "total": total,
            "done": True,
            "status": "PreviewReady",
            "phase": "preview",
            "throughput": round(total / elapsed, 2),
        },
    )


def _run_import_job(docname: str, file_url: str, user: str) -> None:
    """Background worker entry point — streaming parse + batched bulk upsert (parent + child)."""
    try:
        frappe.set_user(user)
    except Exception:
        pass

    started = time.time()
    _set_state(
        docname,
        job_status="Running",
        started_at=now_datetime(),
        progress_stage="Parsing file…",
    )
    frappe.db.commit()
    _publish(docname, user, {"stage": "Parsing file…", "current": 0, "total": 0})

    fingerprint = ""
    try:
        fingerprint = _file_fingerprint(file_url)
    except Exception:
        pass

    parsed = None
    cached = _cache_get_parsed(fingerprint) if fingerprint else None
    if cached and cached.get("_parsed_with_links"):
        parsed = frappe._dict(cached)
        parsed.import_groups = [frappe._dict(r) for r in parsed.import_groups]
        _publish(docname, user, {"stage": "Using cached parse…", "current": 0, "total": parsed.summary.total_rows})

    if parsed is None:
        try:
            parsed = _prepare_import_data(file_url)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Amazon Trip Import parse failed: {docname}")
            _finalize_failed(docname, user, cstr(e))
            return
        if fingerprint:
            to_cache = dict(parsed)
            to_cache["_parsed_with_links"] = True
            _cache_parsed(fingerprint, to_cache)

    if parsed.blocking_errors:
        _finalize_failed(docname, user, "; ".join(parsed.blocking_errors))
        return

    groups = parsed.import_groups or []
    total = len(groups)
    _set_state(
        docname,
        progress_total=total,
        progress_current=0,
        progress_stage=f"Importing 0 of {total} Tour ID groups",
    )
    frappe.db.commit()
    _publish(
        docname,
        user,
        {
            "stage": f"Importing 0 of {total} Tour ID groups",
            "current": 0,
            "total": total,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "throughput": 0,
            "eta_sec": 0,
        },
    )

    now_str = cstr(now_datetime())

    inserted = 0
    updated = 0
    skipped = 0
    failures: list[dict] = []
    cancelled = False

    pending_update: list[dict] = []  # groups with existing parent name

    processed = 0

    def _publish_tick(final: bool = False) -> None:
        elapsed = max(time.time() - started, 0.001)
        rps = processed / elapsed
        eta = int((total - processed) / rps) if rps > 0 and not final else 0
        _set_state(
            docname,
            progress_current=processed,
            progress_stage=f"Importing ({processed} of {total} groups)",
            inserted_count=inserted,
            updated_count=updated,
            skipped_count=skipped,
            failed_count=len(failures),
            throughput_rows_per_sec=rps,
        )
        frappe.db.commit()
        _publish(
            docname,
            user,
            {
                "stage": f"Importing ({processed} of {total} groups)",
                "current": processed,
                "total": total,
                "inserted": inserted,
                "updated": updated,
                "skipped": skipped,
                "failed": len(failures),
                "throughput": round(rps, 2),
                "eta_sec": eta,
            },
        )

    def _flush_batch(update_batch: list[dict]) -> int:
        """Flush a batch of existing Amazon Trip updates."""
        nonlocal failures

        if not update_batch:
            return 0

        # Apply before-save calcs
        for grp in update_batch:
            _apply_before_save_calcs(grp["parent_values"])

        upd_count = len(update_batch)

        try:
            # 1. Bulk upsert parent rows
            parent_batch = [
                {"name": grp["name"], "is_new": grp["is_new"], "values": grp["parent_values"]}
                for grp in update_batch
            ]
            _bulk_upsert_amazon_trip(parent_batch, user=user, now=now_str)

            # 2. For each group: delete old child rows + insert new ones
            for grp in update_batch:
                _delete_child_rows(grp["name"])
                _bulk_insert_child_rows(
                    grp["name"],
                    grp["child_rows"],
                    user=user,
                    now=now_str,
                )

            frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), f"Amazon Trip Import batch failed: {docname}")
            msg = cstr(exc)

            # Fall back to per-group ORM save
            inner_upd = 0
            for grp in update_batch:
                try:
                    doc = frappe.get_doc(TARGET_DOCTYPE, grp["name"])
                    doc.update(grp["parent_values"])
                    # Rebuild child table
                    doc.set(CHILD_PARENTFIELD, [])
                    for child_vals in grp["child_rows"]:
                        row = doc.append(CHILD_PARENTFIELD, {})
                        row.update(child_vals)
                    # Skip Link validation — imported values (Vehicle No, etc.) may not
                    # exist in masters yet; bulk SQL already bypasses this normally.
                    doc.flags.ignore_links = True
                    doc.save(ignore_permissions=True)
                    inner_upd += 1
                except Exception as e2:
                    if len(failures) < FAILURES_MAX_STORED:
                        failures.append({
                            "row": grp.get("excel_row_number", 0),
                            "tour_id": grp["tour_id"],
                            "severity": "Error",
                            "error_type": "DB",
                            "message": cstr(e2),
                        })
            frappe.db.commit()
            return inner_upd

        return upd_count

    for i, grp in enumerate(groups, start=1):
        if i % CANCEL_CHECK_EVERY_ROWS == 0 and _is_cancelled(docname):
            cancelled = True
            break

        processed = i

        if grp.skip:
            skipped += 1
        elif grp.errors:
            if len(failures) < FAILURES_MAX_STORED:
                failures.append({
                    "row": grp.excel_row_number,
                    "tour_id": grp.tour_id,
                    "severity": "Error",
                    "error_type": "Validation",
                    "message": "; ".join(grp.errors),
                })
        else:
            if not grp.existing_docname:
                if len(failures) < FAILURES_MAX_STORED:
                    failures.append({
                        "row": grp.excel_row_number,
                        "tour_id": grp.tour_id,
                        "severity": "Error",
                        "error_type": "Validation",
                        "message": f"Tour ID '{grp.tour_id}' does not exist in Amazon Trip; update-only import cannot create it.",
                    })
                continue

            entry = {
                "tour_id": grp.tour_id,
                "name": grp.existing_docname,
                "is_new": False,
                "parent_values": dict(grp.parent_values),
                "child_rows": list(grp.child_rows),
                "excel_row_number": grp.excel_row_number,
            }
            pending_update.append(entry)

            # Flush when batch is full
            if len(pending_update) >= BULK_UPSERT_BATCH_SIZE:
                updated += _flush_batch(pending_update)
                pending_update = []

        if i % PROGRESS_PUBLISH_EVERY_ROWS == 0 or i == total:
            _publish_tick()

    # Final flush
    if not cancelled and pending_update:
        updated += _flush_batch(pending_update)
        _publish_tick(final=True)

    frappe.db.commit()

    _finalize(
        docname,
        user,
        status="Cancelled" if cancelled else "Completed",
        inserted=inserted,
        updated=updated,
        skipped=skipped,
        failures=failures,
        total=total,
    )


# ══════════════════════════════════════════════════════════════════
#  FINALIZE HELPERS
# ══════════════════════════════════════════════════════════════════

def _generate_failure_csv(docname: str, failures: list[dict]) -> str | None:
    """Generate a private File attachment containing failure rows. Returns file_url."""
    if not failures:
        return None
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["row", "tour_id", "severity", "error_type", "message"])
    for f in failures:
        writer.writerow([
            f.get("row") or "",
            f.get("tour_id") or "",
            f.get("severity") or "Error",
            f.get("error_type") or "",
            f.get("message") or "",
        ])
    content = buf.getvalue().encode("utf-8")

    try:
        # Remove prior attachment if any
        old = frappe.db.get_value(IMPORT_DOCTYPE, docname, "failure_csv_attachment")
        if old:
            for old_name in frappe.get_all("File", filters={"file_url": old}, pluck="name"):
                try:
                    frappe.delete_doc("File", old_name, ignore_permissions=True, force=True)
                except Exception:
                    pass

        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"{docname}-failures.csv",
            "attached_to_doctype": IMPORT_DOCTYPE,
            "attached_to_name": docname,
            "content": content,
            "is_private": 0,
        }).insert(ignore_permissions=True)
        return file_doc.file_url
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Amazon Trip Import failure CSV write failed: {docname}")
        return None


def _finalize(
    docname: str,
    user: str,
    *,
    status: str,
    inserted: int,
    updated: int,
    skipped: int,
    failures: list[dict],
    total: int,
) -> None:
    stored = failures[:FAILURES_MAX_STORED]
    failure_url = _generate_failure_csv(docname, failures) if failures else None
    _set_state(
        docname,
        job_status=status,
        finished_at=now_datetime(),
        progress_stage=status,
        progress_current=total,
        inserted_count=inserted,
        updated_count=updated,
        skipped_count=skipped,
        failed_count=len(failures),
        failure_log_json=json.dumps(stored) if stored else "",
        failure_csv_attachment=failure_url or "",
    )
    frappe.db.commit()
    _publish(
        docname,
        user,
        {
            "stage": status,
            "current": total,
            "total": total,
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "failed": len(failures),
            "done": True,
            "status": status,
        },
    )


def _finalize_failed(docname: str, user: str, message: str) -> None:
    _set_state(
        docname,
        job_status="Failed",
        finished_at=now_datetime(),
        progress_stage="Failed",
        failure_log_json=json.dumps(
            [{"row": 0, "severity": "Error", "error_type": "Fatal", "message": message, "tour_id": ""}]
        ),
    )
    frappe.db.commit()
    _publish(
        docname,
        user,
        {"stage": "Failed", "done": True, "status": "Failed", "error": message},
    )
