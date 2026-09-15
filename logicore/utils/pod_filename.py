"""
utils/pod_filename.py
Shared POD filename convention: the file name (minus extension) must be exactly
a Trip's TCN/Trip No (or LR No, for Trip Type "Other") -- no hyphens, no
date/time prefix. Mirrors the rule Trip POD Import (bulk) enforces via its own
_extract_reference_no()/_get_trip_match_config(), kept separate there to avoid
touching that file's internals; this module is the single source of truth for
the manual "POD Manager" upload on the Trip form, so both paths reject the
same file names instead of drifting apart.
"""

import os

import frappe
from frappe import _, cstr

PDF_EXTENSION = ".pdf"
TRIP_TYPE_OTHER = "other"


def is_pdf_filename(file_name: str) -> bool:
	return os.path.splitext(cstr(file_name).strip())[1].lower() == PDF_EXTENSION


def extract_reference_no(file_name: str) -> str | None:
	"""File name must be exactly the Reference No (TCN/Trip No or LR No), e.g.
	RC90210521.pdf. Date-time-prefixed names (with hyphens) are not accepted."""
	base_name = os.path.splitext(os.path.basename(cstr(file_name).strip()))[0].strip()
	if not base_name or "-" in base_name:
		return None
	return base_name


def get_trip_match_field(trip_type: str) -> tuple[str, str]:
	"""Return (fieldname, label) used to match a Trip against a parsed reference no."""
	if cstr(trip_type).strip().casefold() == TRIP_TYPE_OTHER:
		return "lr_no", _("LR No")
	return "tcntrip_no", _("TCN/Trip No")


def validate_pod_filename_matches_trip(trip_name: str, file_name: str) -> None:
	"""Raise if `file_name` doesn't follow the Reference No convention, or names a
	reference that doesn't belong to `trip_name`. Used by the manual POD Manager
	upload on the Trip form so it enforces the same naming rule as bulk import,
	instead of silently accepting (and renaming) any file."""
	if not is_pdf_filename(file_name):
		frappe.throw(_("Only PDF files are allowed."))

	reference_no = extract_reference_no(file_name)
	if not reference_no:
		frappe.throw(_(
			"File name must be exactly the TCN/Trip No (or LR No) — no hyphens, date, "
			"or time prefix. Rename the file and try again, e.g. RC90210521.pdf."
		))

	trip_type = frappe.db.get_value("Trip", trip_name, "trip_type")
	match_field, match_label = get_trip_match_field(trip_type)
	trip_reference = cstr(frappe.db.get_value("Trip", trip_name, match_field)).strip()

	if reference_no != trip_reference:
		frappe.throw(_(
			"File name '{0}' does not match this Trip's {1} ('{2}'). Rename the file "
			"to '{2}.pdf' and try again."
		).format(file_name, match_label, trip_reference or _("not set")))
