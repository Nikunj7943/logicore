# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from frappe.model.naming import make_autoname
from datetime import date as _date

from logicore.utils.renaming import apply_pending_rename, capture_rename_target


def _get_fy_key(trip_date):
    """Return 4-char FY key: e.g. '2526' for Apr 2025 – Mar 2026."""
    y, m = trip_date.year, trip_date.month
    start = y if m >= 4 else y - 1
    return f"{str(start)[2:]}{str(start + 1)[2:]}"


def _compute_trip_name(trip_data):
    """Compute the canonical Trip name for trip_data (dict with tcntrip_date/company/trip_type).
    Calls make_autoname so the FY counter in tabSeries is incremented."""
    td = getdate(trip_data.get("tcntrip_date")) if trip_data.get("tcntrip_date") else _date.today()

    company_abbr = "TMS"
    if trip_data.get("company"):
        abbr = frappe.db.get_value("Company", trip_data["company"], "abbr")
        if abbr:
            company_abbr = abbr.upper()

    type_code = "O"
    if trip_data.get("trip_type"):
        code = frappe.db.get_value("Trip Type", trip_data["trip_type"], "code")
        if code:
            type_code = code.strip().upper()

    mmyy        = td.strftime("%m%y")
    fy_key      = _get_fy_key(td)
    name_prefix = f"{company_abbr}-{type_code}-{mmyy}"   # type in name
    series_key  = f"{company_abbr}-{fy_key}"             # shared counter across all types

    series_name = make_autoname(f"{series_key}.#####")
    counter     = series_name.replace(series_key, "")
    return f"{name_prefix}{counter}"

_LAYOUT_TYPES = frozenset({
	"Section Break", "Column Break", "HTML", "Tab Break",
	"Fold", "Heading", "Image",
})


class TripSettings(Document):
	def before_save(self):
		capture_rename_target(self, "trip_type")

	def on_update(self):
		apply_pending_rename(self)


@frappe.whitelist()
def get_trip_fields():
	"""Return Trip doctype fields grouped by tab, reading live metadata from frappe.get_meta."""
	meta = frappe.get_meta("Trip")
	tabs = []
	current_tab = None

	for field in meta.fields:
		if field.fieldtype == "Tab Break":
			current_tab = {
				"tab_key":   field.fieldname,
				"tab_label": field.label or field.fieldname,
				"fields":    [],
			}
			tabs.append(current_tab)
		elif field.fieldtype not in _LAYOUT_TYPES:
			if current_tab is None:
				current_tab = {"tab_key": "_default", "tab_label": "General", "fields": []}
				tabs.append(current_tab)
			current_tab["fields"].append({
				"fieldname":  field.fieldname,
				"label":      field.label or field.fieldname,
				"fieldtype":  field.fieldtype,
				"reqd":       1 if field.reqd else 0,
				"read_only":  1 if field.read_only else 0,
			})

	return [t for t in tabs if t["fields"]]




@frappe.whitelist()
def get_field_config(trip_type):
	"""Return field visibility config and custom color for the given trip type."""
	if not trip_type:
		return {"fields": [], "trip_color": ""}
	if not frappe.db.exists("Trip Settings", trip_type):
		return {"fields": [], "trip_color": ""}
	doc = frappe.get_doc("Trip Settings", trip_type)
	return {
		"fields": [
			{"fieldname": r.fieldname, "is_visible": r.is_visible}
			for r in doc.trip_field_settings
		],
		"trip_color": doc.trip_color or "",
	}


@frappe.whitelist()
def regenerate_trip_ids():
    """Rename all Trips using FY-based naming. Safe to re-run on stuck trips."""
    frappe.only_for("System Manager")
    import time

    trips = frappe.db.sql("""
        SELECT name, tcntrip_date, company, trip_type
        FROM `tabTrip`
        ORDER BY COALESCE(tcntrip_date, DATE(creation)) ASC, creation ASC
    """, as_dict=True)

    total = len(trips)
    if not total:
        return {"renamed": 0, "total": 0, "errors": []}

    # ── Step 1: clear series so counters restart from 1 ───────────────────────
    # Matches new format (UG-2627) and old format (UG-P-2627) both
    frappe.db.sql(
        "DELETE FROM `tabSeries` WHERE name REGEXP '^[A-Z0-9]+(-[A-Z])?-[0-9]{4}$'"
    )
    frappe.db.commit()

    # ── Step 2: compute ALL new names first (counter increments in date order) ─
    errors   = []
    name_map = {}   # current_db_name -> new_canonical_name
    for t in trips:
        try:
            name_map[t["name"]] = _compute_trip_name(t)
        except Exception as exc:
            frappe.log_error(title="Trip Regen – compute",
                             message=f"{t['name']}: {exc}")
            errors.append({"trip": t["name"], "phase": "compute", "error": str(exc)})
            name_map[t["name"]] = None

    # ── Step 3: phase A — rename to unique temp names (handles stuck trips too) ─
    ts       = str(int(time.time()))[-6:]   # 6-digit epoch suffix, unique per run
    temp_map = {}   # temp_name -> final_name
    renamed  = 0

    for i, (cur, new) in enumerate(name_map.items()):
        if new is None:
            continue
        if cur == new:
            renamed += 1   # already correct, nothing to do
            continue
        temp = f"_RGN{ts}_{i:04d}_"
        try:
            frappe.rename_doc("Trip", cur, temp, force=True, show_alert=False)
            temp_map[temp] = new
        except Exception as exc:
            frappe.log_error(title="Trip Regen – phase A",
                             message=f"{cur} -> {temp}: {exc}")
            errors.append({"trip": cur, "phase": "temp-rename", "error": str(exc)})

    frappe.db.commit()

    # ── Step 4: phase B — rename each temp to its final canonical name ─────────
    for temp, new in temp_map.items():
        try:
            frappe.rename_doc("Trip", temp, new, force=True, show_alert=False)
            renamed += 1
        except Exception as exc:
            frappe.log_error(title="Trip Regen – phase B",
                             message=f"{temp} -> {new}: {exc}")
            errors.append({"trip": temp, "phase": "final-rename",
                           "new_name": new, "error": str(exc)})

    # ── Step 5: sync so_no = name for every trip (rename_doc skips before_save) ─
    frappe.db.sql("UPDATE `tabTrip` SET so_no = name")

    frappe.db.commit()
    return {"renamed": renamed, "total": total, "errors": errors}
