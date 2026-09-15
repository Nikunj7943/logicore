# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import csv
import io
import json
import os
import re
from datetime import datetime as _datetime
from typing import Any

from dateutil import parser
from dateutil.parser import ParserError

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, get_datetime, getdate, now_datetime
from frappe.utils.file_manager import save_file

TEMPLATE_DOCTYPE = "Import Template"
LOG_DOCTYPE = "Import Log"
CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
LAYOUT_FIELD_TYPES = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"Fold",
	"Heading",
	"HTML",
	"Button",
	"Image",
	"Attach Image",
	"Signature",
	"Geolocation",
	"Barcode",
	"Break",
	"Table",
	"Table MultiSelect",
}
INTERNAL_FIELDNAMES = {
	"doctype",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"parent",
	"parentfield",
	"parenttype",
	"idx",
	"_assign",
	"_comments",
	"_liked_by",
	"_seen",
	"_user_tags",
}
# Derived/display-only fields that get silently overwritten from their source
# Link field on every save (see Trip._fill_address_display_fields) — importing
# into these directly would have the value wiped out again on the same save.
DERIVED_DISPLAY_FIELDNAMES = {
	"origin_address_1_full",
	"origin_address_2_full",
	"destination_address_1_full",
	"destination_address_2_full",
}
IMPORT_MODES = {
	"Update Existing Only",
	"Create New Only",
	"Update or Create",
}
STAFF_PAYROLL_OLD_IMPORT_TEMPLATES = {
	"Payroll Import Old - Driver",
	"Payroll Import Old - Employee",
}
STAFF_PAYROLL_OLD_IMPORT_COMPONENTS = {
	"earnings": [
		{"fieldname": "old_basic_salary", "csv_header": "Basic Salary", "component_name": "Basic Salary"},
		{"fieldname": "old_incentive", "csv_header": "Incentive", "component_name": "Incentive"},
		{"fieldname": "old_bonus", "csv_header": "Bonus", "component_name": "Bonus"},
		{"fieldname": "old_reimbursement", "csv_header": "Reimbursement", "component_name": "Reimbursement"},
		{"fieldname": "old_accident_insurance", "csv_header": "Accident Insurance", "component_name": "Accident Insurance"},
		{"fieldname": "old_medical_insurance", "csv_header": "Medical Insurance", "component_name": "Medical Insurance"},
	],
	"deductions": [
		{"fieldname": "old_other_deductions", "csv_header": "Other Deductions", "component_name": "Other Deductions"},
		{"fieldname": "old_leave_deductions", "csv_header": "Leave Deductions", "component_name": "Leave Deductions"},
		{"fieldname": "old_paid_incentive", "csv_header": "Paid Incentive", "component_name": "Paid Incentive"},
	],
}
STAFF_PAYROLL_OLD_IMPORT_FIELD_MAP = {
	item["fieldname"]: {
		"fieldname": item["fieldname"],
		"label": item["csv_header"],
		"fieldtype": "Currency",
		"reqd": 0,
		"read_only": 0,
		"options": "currency",
		"is_virtual_salary_component": 1,
		"salary_component_group": group,
		"salary_component_name": item["component_name"],
	}
	for group, items in STAFF_PAYROLL_OLD_IMPORT_COMPONENTS.items()
	for item in items
}


def _normalize_header(value: str | None) -> str:
	return " ".join(cstr(value).strip().split()).casefold()


def _parse_import_bool(value: str | None) -> bool:
	"""Parse a CSV cell as a boolean flag — used for import-only bypass
	checkboxes like "Ignore Validations" on the grouped bulk importers.
	Case-insensitive and accepts common spreadsheet-export spellings:
	Excel/Sheets write boolean TRUE as "TRUE" (all caps), not "true" —
	an exact-match allow-list silently treats that as false. Root cause of
	a real bug: rows imported with "Ignore Validations" = TRUE in the CSV
	saved as ignore_validations=0, so submitting the record later re-ran
	the exceeds-balance check for real and threw.
	"""
	return cstr(value).strip().casefold() in ("1", "1.0", "true", "yes", "y")


# The Import Template names every CSV column after the target field's *label*,
# and the label of the `ignore_validations` Check field on Vendor Payment /
# Receipt / Supplier Payment is "Ignore Validations (Import Only)" — but the
# three grouped importers below looked the column up as a bare
# "Ignore Validations". Header matching is exact (normalised), so that lookup
# never resolved: cell() returned "" and the flag silently stayed 0 on every
# single import, on every site. Symptom: a CSV with the flag set to 1 still
# ran _validate_trips()/_validate_invoices() and threw "Payment Amount …
# exceeds outstanding balance …". Accept both spellings so the downloaded
# template *and* hand-typed short headers work.
IGNORE_VALIDATIONS_CSV_HEADERS = (
	"Ignore Validations (Import Only)",
	"Ignore Validations",
)


def read_ignore_validations_flag(cell, rows) -> int:
	"""1 if any row in a grouped-import group sets the ignore-validations flag
	under any accepted header spelling. `cell` is the importer's local
	cell(row, column) accessor."""
	return (
		1
		if any(
			_parse_import_bool(cell(row, header))
			for row in rows
			for header in IGNORE_VALIDATIONS_CSV_HEADERS
		)
		else 0
	)


# Vendor Payment Trip / Customer Receipt Trip child-table columns that
# bulk_import_vendor_payments()/bulk_import_receipts() read directly from the
# CSV (see GROUPED_TRIP_IMPORT_EXTRA_COLUMNS / _process_grouped_trip_import
# further down). get_importable_fields() normally excludes Table fields
# entirely, so without this the Column Builder's field picker — and
# normalize_template_columns()'s validation on save — would have no way to
# know "trip"/"payment_amount" are legitimate columns for these two
# doctypes. Listed here as plain Data fields (same pattern as
# STAFF_PAYROLL_OLD_IMPORT_FIELD_MAP below) purely so they show up and
# validate in the Column Builder; the actual import never reads them via
# columns_json, it parses the raw CSV header by name.
GROUPED_TRIP_IMPORT_VIRTUAL_FIELDS = {
	"Vendor Payment": [
		{"fieldname": "trip", "label": "Trip (Trips)", "fieldtype": "Data", "reqd": 0, "read_only": 0, "options": ""},
		{"fieldname": "payment_amount", "label": "Payment Amount", "fieldtype": "Currency", "reqd": 0, "read_only": 0, "options": ""},
	],
	"Receipt": [
		{"fieldname": "trip", "label": "Trip (Trips)", "fieldtype": "Data", "reqd": 0, "read_only": 0, "options": ""},
		{"fieldname": "received_amount", "label": "Net Receivable Amount", "fieldtype": "Currency", "reqd": 0, "read_only": 0, "options": ""},
	],
	"Supplier Payment": [
		{"fieldname": "supplier_invoice_no", "label": "Supplier Invoice No (Invoices)", "fieldtype": "Data", "reqd": 0, "read_only": 0, "options": ""},
		{"fieldname": "payment_amount", "label": "Payment Amount", "fieldtype": "Currency", "reqd": 0, "read_only": 0, "options": ""},
	],
}


def get_importable_fields(doctype: str) -> list[frappe._dict]:
	"""Returns all fields eligible for import for the given doctype.
	Read-only fields are included so they can be used as match keys,
	but they are skipped during the update phase.
	"""
	meta = frappe.get_meta(doctype)
	fields = [
		frappe._dict(
			fieldname="name",
			label=_("ID"),
			fieldtype="Data",
			reqd=0,
			read_only=1,
			options="",
		)
	]
	for df in meta.fields:
		if not df.fieldname or df.fieldname in INTERNAL_FIELDNAMES:
			continue
		if df.fieldname in DERIVED_DISPLAY_FIELDNAMES:
			continue
		if df.fieldtype in LAYOUT_FIELD_TYPES:
			continue
		fields.append(
			frappe._dict(
				fieldname=df.fieldname,
				label=df.label or df.fieldname,
				fieldtype=df.fieldtype,
				reqd=1 if df.reqd else 0,
				read_only=1 if df.read_only else 0,
				options=df.options or "",
			)
		)
	if doctype == "Staff Payroll":
		for fieldname, field_info in STAFF_PAYROLL_OLD_IMPORT_FIELD_MAP.items():
			fields.append(frappe._dict(field_info))
	if doctype in GROUPED_TRIP_IMPORT_VIRTUAL_FIELDS:
		for field_info in GROUPED_TRIP_IMPORT_VIRTUAL_FIELDS[doctype]:
			fields.append(frappe._dict(field_info))
	return fields


def get_trip_importable_fields_legacy() -> list[frappe._dict]:
	"""Backward-compat wrapper — returns importable fields for Trip."""
	return get_importable_fields("Trip")


def get_importable_field_map(doctype: str) -> dict[str, frappe._dict]:
	return {f.fieldname: f for f in get_importable_fields(doctype)}


def is_staff_payroll_old_import_template(template_doc) -> bool:
	template_name = cstr(getattr(template_doc, "template_name", "")).strip()
	return template_name in STAFF_PAYROLL_OLD_IMPORT_TEMPLATES


def get_trip_importable_field_map_legacy() -> dict[str, frappe._dict]:
	"""Backward-compat wrapper."""
	return get_importable_field_map("Trip")


def parse_columns_json(columns_json: str | list[dict[str, Any]] | None) -> list[dict[str, Any]]:
	if not columns_json:
		return []
	if isinstance(columns_json, str):
		try:
			data = json.loads(columns_json)
		except Exception:
			frappe.throw(_("Columns JSON is not valid JSON."), title=_("Invalid Template"))
	else:
		data = columns_json
	if not isinstance(data, list):
		frappe.throw(_("Columns JSON must be a list of column definitions."), title=_("Invalid Template"))
	return [frappe._dict(row or {}) for row in data]


def normalize_template_columns(
	columns_json: str | list[dict[str, Any]] | None,
	match_field: str,
	default_import_mode: str,
	target_doctype: str = "Trip",
) -> list[dict[str, Any]]:
	field_map = get_importable_field_map(target_doctype)
	if match_field and match_field not in field_map:
		frappe.throw(
			_("Match Field '{0}' is not a valid field on {1}.").format(match_field, target_doctype),
			title=_("Invalid Template"),
		)

	raw_columns = parse_columns_json(columns_json)
	normalized: list[dict[str, Any]] = []
	seen_headers: set[str] = set()
	seen_fields: set[str] = set()

	for idx, row in enumerate(raw_columns, start=1):
		csv_header = cstr(row.get("csv_header")).strip()
		fieldname = cstr(row.get("fieldname")).strip()
		if not csv_header and not fieldname:
			continue
		if not csv_header:
			frappe.throw(_("Column #{0}: CSV Header is required.").format(idx), title=_("Invalid Template"))
		if not fieldname:
			frappe.throw(_("Column #{0}: Field is required.").format(idx), title=_("Invalid Template"))
		if fieldname not in field_map:
			frappe.throw(
				_("Column #{0}: Field '{1}' is not importable on {2}.").format(
					idx, frappe.bold(fieldname), target_doctype
				),
				title=_("Invalid Template"),
			)
		header_key = _normalize_header(csv_header)
		if header_key in seen_headers:
			frappe.throw(
				_("CSV Header '{0}' is duplicated.").format(frappe.bold(csv_header)),
				title=_("Invalid Template"),
			)
		if fieldname in seen_fields:
			frappe.throw(
				_("Field '{0}' is duplicated.").format(frappe.bold(fieldname)),
				title=_("Invalid Template"),
			)
		field_info = field_map[fieldname]
		normalized.append(
			{
				"idx": len(normalized) + 1,
				"csv_header": csv_header,
				"fieldname": fieldname,
				"label": field_info.label,
				"fieldtype": field_info.fieldtype,
				"required": 1 if cint(row.get("required")) else 0,
				"default_value": row.get("default_value") if row.get("default_value") is not None else "",
				"is_match_key": 1 if row.get("is_match_key") else 0,
			}
		)
		seen_headers.add(header_key)
		seen_fields.add(fieldname)

	# Ensure primary match_field column exists (backward compat — old templates without is_match_key)
	if match_field:
		match_present = next((c for c in normalized if c["fieldname"] == match_field), None)
		if not match_present:
			field_info = field_map[match_field]
			normalized.insert(
				0,
				{
					"idx": 1,
					"csv_header": field_info.label or match_field,
					"fieldname": match_field,
					"label": field_info.label,
					"fieldtype": field_info.fieldtype,
					"required": 1,
					"default_value": "",
					"is_match_key": 1,
				},
			)
			for idx, row in enumerate(normalized, start=1):
				row["idx"] = idx
			match_present = normalized[0]

		if default_import_mode in {"Update Existing Only", "Update or Create"}:
			match_present["required"] = 1
			# Ensure the primary match_field column is marked as match key
			if not match_present.get("is_match_key"):
				match_present["is_match_key"] = 1

	if not normalized:
		frappe.throw(_("At least one column is required."), title=_("Invalid Template"))

	return normalized


def get_template_doc(template_name: str):
	if not template_name:
		frappe.throw(_("Template is required."))
	doc = frappe.get_doc(TEMPLATE_DOCTYPE, template_name)
	doc.check_permission("read")
	return doc


def get_log_doc(log_name: str, permtype: str = "read"):
	if not log_name:
		frappe.throw(_("Log is required."))
	doc = frappe.get_doc(LOG_DOCTYPE, log_name)
	doc.check_permission(permtype)
	return doc


def _read_csv_rows(file_url: str) -> list[list[str]]:
	if not file_url:
		frappe.throw(_("CSV file is required."))
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	full_path = file_doc.get_full_path()
	extension = os.path.splitext(file_doc.file_name or file_doc.file_url or "")[1].lower()
	if extension != ".csv":
		frappe.throw(_("Only CSV files are supported."), title=_("Unsupported File"))
	last_error = None
	for encoding in CSV_ENCODINGS:
		try:
			with open(full_path, "r", encoding=encoding, errors="strict", newline="") as handle:
				return list(csv.reader(handle))
		except UnicodeDecodeError as exc:
			last_error = exc
			continue
	if last_error:
		raise last_error
	return []


def _normalize_select_options(options: Any) -> list[str]:
	return [cstr(option).strip() for option in cstr(options or "").splitlines() if cstr(option).strip()]


def _strict_import_date(value: Any):
	if isinstance(value, _datetime):
		return value.date().isoformat()
	if hasattr(value, "isoformat") and not isinstance(value, str):
		return cstr(value.isoformat())

	text = cstr(value).strip()
	if not re.fullmatch(r"\d{2}-\d{2}-\d{4}", text):
		frappe.throw(
			_("Date '{0}' must be in dd-mm-yyyy format.").format(frappe.bold(text)),
			title=_("Invalid Date"),
		)
	try:
		return _datetime.strptime(text, "%d-%m-%Y").date().isoformat()
	except ValueError:
		frappe.throw(
			_("Date '{0}' is not valid.").format(frappe.bold(text)),
			title=_("Invalid Date"),
		)


def _fieldtype_cast(value: Any, field_info: frappe._dict | str):
	if value in (None, ""):
		return ""
	if isinstance(field_info, str):
		field_info = frappe._dict(fieldtype=field_info, options="", label=field_info)
	fieldtype = cstr(field_info.get("fieldtype"))
	options = field_info.get("options")
	label = cstr(field_info.get("label") or field_info.get("fieldname") or fieldtype)
	if fieldtype in {"Data", "Small Text", "Text", "Long Text", "Text Editor", "Link", "Dynamic Link"}:
		return cstr(value).strip()
	if fieldtype == "Select":
		selected = cstr(value).strip()
		allowed = _normalize_select_options(options)
		if allowed and selected not in allowed:
			frappe.throw(
				_("'{0}' is not a valid option for {1}. Allowed values: {2}").format(
					frappe.bold(selected),
					frappe.bold(label),
					", ".join(allowed),
				),
				title=_("Invalid Option"),
			)
		return selected
	if fieldtype in {"Int", "Check"}:
		return cint(value)
	if fieldtype in {"Float", "Currency", "Percent"}:
		return flt(value)
	if fieldtype == "Date":
		return _strict_import_date(value)
	if fieldtype == "Datetime":
		if isinstance(value, _datetime):
			return value.strftime("%Y-%m-%d %H:%M:%S")
		try:
			return _datetime.fromisoformat(cstr(value)).strftime("%Y-%m-%d %H:%M:%S")
		except ValueError:
			try:
				return parser.parse(cstr(value), dayfirst=True).strftime("%Y-%m-%d %H:%M:%S")
			except ParserError:
				frappe.throw(
					_("{} is not a valid datetime string.").format(frappe.bold(cstr(value))),
					title=_("Invalid Date"),
				)
	return value


def _validate_link_value(field_info: frappe._dict, value: Any):
	"""Resolves a Link column's CSV value to a real record name (ID).
	Tries an exact ID match first; if that fails, falls back to the target
	doctype's title_field (e.g. Driver.full_name, Employee.employee_name) so
	users can type a human-readable name instead of memorising IDs."""
	if field_info.fieldtype != "Link" or value in (None, ""):
		return value
	target_doctype = field_info.options
	if not target_doctype:
		return value
	if frappe.db.exists(target_doctype, value):
		return value
	title_field = frappe.get_meta(target_doctype).title_field
	if title_field and title_field != "name":
		matches = frappe.db.get_all(target_doctype, filters={title_field: value}, pluck="name")
		if len(matches) == 1:
			return matches[0]
		if len(matches) > 1:
			frappe.throw(
				_("Multiple {0} records are named '{1}' — use the exact ID instead.").format(
					target_doctype, frappe.bold(cstr(value))
				),
				title=_("Ambiguous Link"),
			)
	frappe.throw(
		_("{0} '{1}' was not found.").format(target_doctype or _("Linked record"), frappe.bold(cstr(value))),
		title=_("Invalid Link"),
	)


def _is_blank_row(row: list[Any]) -> bool:
	return all(cstr(cell).strip() == "" for cell in row)


def _get_csv_value(row: list[Any], index_map: dict[str, int], csv_header: str):
	idx = index_map.get(_normalize_header(csv_header))
	if idx is None or idx >= len(row):
		return ""
	return row[idx]


def _get_staff_payroll_virtual_field_info(fieldname: str) -> frappe._dict | None:
	return STAFF_PAYROLL_OLD_IMPORT_FIELD_MAP.get(fieldname)


def _apply_staff_payroll_component_values(doc, component_values: dict[str, dict[str, Any]]):
	if cstr(doc.doctype) != "Staff Payroll":
		return
	for group in ("earnings", "deductions"):
		rows = getattr(doc, f"{group}_table", None) or []
		row_map = {cstr(row.salary_component): row for row in rows if cstr(row.salary_component)}
		for component_name, amount in (component_values.get(group) or {}).items():
			row = row_map.get(component_name)
			if not row:
				row = doc.append(f"{group}_table", {"salary_component": component_name})
				row_map[component_name] = row
			row.amount = flt(amount)


def _get_match_columns(columns: list[dict[str, Any]], match_field: str) -> list[dict[str, Any]]:
	"""Returns columns marked as match keys; falls back to match_field for old templates."""
	match_cols = [c for c in columns if cint(c.get("is_match_key"))]
	if not match_cols and match_field:
		match_cols = [c for c in columns if c["fieldname"] == match_field]
	return match_cols


def _build_preview_row(
	template_doc,
	columns: list[dict[str, Any]],
	header_index_map: dict[str, int],
	row: list[Any],
	row_number: int,
	import_mode: str,
) -> frappe._dict:
	target_doctype = cstr(template_doc.target_doctype).strip() or "Trip"
	field_map = get_importable_field_map(target_doctype)
	match_field = cstr(template_doc.match_field).strip()
	match_columns = _get_match_columns(columns, match_field)
	errors: list[str] = []

	# Build compound match filter — cast values to DB-compatible format
	match_filters: dict[str, Any] = {}
	for mc in match_columns:
		val = cstr(_get_csv_value(row, header_index_map, mc["csv_header"])).strip()
		if not val:
			errors.append(_("Match key '{0}' value is missing.").format(mc["csv_header"]))
		else:
			try:
				match_filters[mc["fieldname"]] = _fieldtype_cast(val, field_map[mc["fieldname"]])
			except Exception:
				match_filters[mc["fieldname"]] = val

	existing_name = ""
	if match_filters and not errors:
		if len(match_filters) == 1 and "name" in match_filters:
			existing_name = (
				match_filters["name"] if frappe.db.exists(target_doctype, match_filters["name"]) else ""
			)
		else:
			existing_name = frappe.db.get_value(target_doctype, match_filters, "name") or ""

	status = "Ready"
	action = "Create"
	if import_mode == "Update Existing Only":
		action = "Update"
		if not existing_name and match_filters:
			errors.append(
				_("Record not found for {0}.").format(
					", ".join(f"{k}={v}" for k, v in match_filters.items())
				)
			)
	elif import_mode == "Create New Only":
		action = "Create"
		if existing_name:
			errors.append(
				_("Record already exists for {0}.").format(
					", ".join(f"{k}={v}" for k, v in match_filters.items())
				)
			)
	elif import_mode == "Update or Create":
		action = "Update" if existing_name else "Create"

	for column in columns:
		raw_value = _get_csv_value(row, header_index_map, column["csv_header"])
		if raw_value in (None, "") and column.get("default_value") not in (None, ""):
			raw_value = column.get("default_value")
		if cint(column.get("required")) and raw_value in (None, ""):
			errors.append(_("'{0}' is required.").format(column["csv_header"]))
			continue
		if raw_value in (None, ""):
			continue
		try:
			casted = _fieldtype_cast(raw_value, field_map[column["fieldname"]])
			_validate_link_value(field_map[column["fieldname"]], casted)
		except Exception as exc:
			errors.append(cstr(exc))

	if errors:
		status = "Issue"
		action = "Blocked"

	return frappe._dict(
		row_number=row_number,
		match_filters=match_filters,
		existing_name=existing_name,
		action=action,
		status=status,
		message="; ".join(dict.fromkeys(errors)) if errors else _("Ready to import."),
	)


def build_preview_payload(template_doc, file_url: str, import_mode: str) -> frappe._dict:
	if import_mode not in IMPORT_MODES:
		frappe.throw(_("Invalid import mode."))
	columns = parse_columns_json(template_doc.columns_json)
	rows = _read_csv_rows(file_url)
	if not rows:
		frappe.throw(_("The uploaded CSV file is empty."))

	headers = [cstr(v).strip() for v in rows[0]]
	header_keys = [_normalize_header(v) for v in headers]
	duplicate_headers = sorted({headers[i] for i, key in enumerate(header_keys) if key and header_keys.count(key) > 1})
	missing_headers = [
		column["csv_header"]
		for column in columns
		if cint(column.get("required")) and _normalize_header(column["csv_header"]) not in header_keys
	]

	blocking_errors = []
	if duplicate_headers:
		blocking_errors.append(_("Duplicate CSV headers found: {0}").format(", ".join(duplicate_headers)))
	if missing_headers:
		blocking_errors.append(_("Missing mandatory headers: {0}").format(", ".join(missing_headers)))

	header_index_map = {_normalize_header(label): idx for idx, label in enumerate(headers)}
	data_rows = rows[1:]
	preview_rows = []
	rows_ready = 0
	rows_with_issues = 0
	create_rows = 0
	update_rows = 0

	for row_number, row in enumerate(data_rows, start=2):
		if _is_blank_row(row):
			if len(preview_rows) < 25:
				preview_rows.append(
					frappe._dict(
						row_number=row_number,
						match_filters={},
						existing_name="",
						action="",
						status="Ignored",
						message=_("Blank row, skipped."),
					)
				)
			continue
		preview = _build_preview_row(template_doc, columns, header_index_map, row, row_number, import_mode)
		if len(preview_rows) < 25:
			preview_rows.append(preview)
		if preview.status == "Issue":
			rows_with_issues += 1
		else:
			rows_ready += 1
		if preview.action == "Create":
			create_rows += 1
		elif preview.action == "Update":
			update_rows += 1

	matched_headers = sum(1 for column in columns if _normalize_header(column["csv_header"]) in header_keys)

	payload = frappe._dict(
		headers=headers,
		columns=columns,
		preview_rows=preview_rows,
		total_rows=len(data_rows),
		matched_headers=matched_headers,
		missing_headers=missing_headers,
		duplicate_headers=duplicate_headers,
		rows_ready=rows_ready,
		rows_with_issues=rows_with_issues,
		create_rows=create_rows,
		update_rows=update_rows,
		blocking_errors=blocking_errors,
		can_import=not blocking_errors,
	)
	return payload


def create_validated_log(template_doc, file_url: str, import_mode: str, company: str | None, preview_payload) -> Any:
	log = frappe.get_doc(
		{
			"doctype": LOG_DOCTYPE,
			"template": template_doc.name,
			"template_name": template_doc.template_name,
			"company": company or template_doc.get("company"),
			"import_mode": import_mode,
			"status": "Validated",
			"uploaded_file": file_url,
			"preview_json": json.dumps(preview_payload, indent=2, default=str),
			"summary_json": json.dumps(
				{
					"total_rows": preview_payload.total_rows,
					"rows_ready": preview_payload.rows_ready,
					"rows_with_issues": preview_payload.rows_with_issues,
					"create_rows": preview_payload.create_rows,
					"update_rows": preview_payload.update_rows,
				},
				indent=2,
			),
			"row_result_json": "[]",
			"total_rows": preview_payload.total_rows,
			"imported_by": frappe.session.user,
		}
	)
	log.insert(ignore_permissions=True)
	return log


def _apply_template_defaults(template_doc, values: dict[str, Any], *, for_create: bool):
	if for_create:
		company = template_doc.get("company")
		if company and not values.get("company"):
			values["company"] = company


def _apply_import_action(doc, import_action: str, action: str) -> str:
	"""Execute post-save action and return a human-readable action label for the log."""
	if import_action == "Submit After Update":
		if doc.docstatus != 0:
			frappe.throw(_("Only Draft documents can be submitted. '{0}' is not in Draft state.").format(doc.name))
		doc.submit()
		return action + " + Submit"
	elif import_action == "Cancel Document":
		if doc.docstatus != 1:
			frappe.throw(_("Only Submitted documents can be cancelled. '{0}' is not Submitted.").format(doc.name))
		doc.cancel()
		return "Cancel"
	return action


GROUPED_TRIP_IMPORT_DOCTYPES = ("Vendor Payment", "Receipt", "Supplier Payment")

# Extra per-row columns bulk_import_vendor_payments()/bulk_import_receipts()/
# bulk_import_supplier_payments() read directly from the CSV — never part of
# columns_json (they're Vendor Payment Trip / Customer Receipt Trip / Payment
# Invoices child-table fields, and get_importable_fields excludes Table fields
# entirely, so the engine can't validate/map them). Still needed in the
# downloadable blank template so someone starting from that file knows to add
# them — see build_template_csv_content().
GROUPED_TRIP_IMPORT_EXTRA_COLUMNS = {
	"Vendor Payment": ["Trip (Trips)", "Payment Amount"],
	"Receipt": ["Trip (Trips)", "Net Receivable Amount"],
	"Supplier Payment": ["Supplier Invoice No (Invoices)", "Payment Amount"],
}


def _process_grouped_trip_import(log_doc, template_doc, target_doctype: str) -> frappe._dict:
	"""Vendor Payment / Receipt / Supplier Payment need multiple CSV rows
	(repeated parent columns, one row per trip/invoice) grouped into a single
	document with a child row per row — this engine's per-row loop below has
	no concept of that (or of child tables at all — see
	get_importable_fields' Table exclusion), so delegate entirely to the
	doctype's own grouped bulk-import function
	(bulk_import_vendor_payments/bulk_import_receipts/
	bulk_import_supplier_payments) and translate its per-group results into
	the same row_result_json/summary_json shape the Import Log UI already
	knows how to render.
	"""
	log_doc.status = "Running"
	log_doc.started_at = now_datetime()
	log_doc.save(ignore_permissions=True)

	if target_doctype == "Vendor Payment":
		from logicore.logicore.doctype.vendor_payment.vendor_payment import (
			bulk_import_vendor_payments as run_grouped_import,
		)
	elif target_doctype == "Supplier Payment":
		from logicore.logicore.doctype.supplier_payment.supplier_payment import (
			bulk_import_supplier_payments as run_grouped_import,
		)
	else:
		from logicore.logicore.doctype.receipt.receipt import (
			bulk_import_receipts as run_grouped_import,
		)

	frappe.flags.in_import = True
	try:
		group_results = run_grouped_import(log_doc.uploaded_file)
	except Exception:
		frappe.flags.in_import = False
		log_doc.status = "Failed"
		log_doc.finished_at = now_datetime()
		log_doc.save(ignore_permissions=True)
		raise
	frappe.flags.in_import = False

	# The grouped importers commit/rollback mid-run, so this doc's in-memory
	# `modified` can drift from the row on disk — saving it then throws
	# "Import Log has been modified after you have opened it" and kills the
	# whole run *after* the records were already created. Re-read before
	# writing the results back.
	log_doc.reload()

	status_map = {"Success": "Success", "Skipped": "Ignored", "Failed": "Failed"}
	results = []
	created_count = failed_count = skipped_count = 0
	for row_number, group in enumerate(group_results, start=1):
		status = status_map.get(group["status"], "Failed")
		if status == "Success":
			created_count += 1
		elif status == "Ignored":
			skipped_count += 1
		else:
			failed_count += 1
		results.append({
			"row_number": row_number,
			"status": status,
			"action": "Create" if status != "Ignored" else "",
			"message": group["message"],
			"record_name": group["label"] if status == "Success" else "",
		})

	summary = {
		"total_rows": len(group_results),
		"success_rows": created_count,
		"failed_rows": failed_count,
		"created_count": created_count,
		"updated_count": 0,
		"skipped_count": skipped_count,
	}

	log_doc.status = "Completed With Errors" if failed_count else "Completed"
	log_doc.row_result_json = json.dumps(results, indent=2, default=str)
	log_doc.summary_json = json.dumps(summary, indent=2)
	log_doc.success_rows = created_count
	log_doc.failed_rows = failed_count
	log_doc.created_count = created_count
	log_doc.updated_count = 0
	log_doc.skipped_count = skipped_count
	log_doc.finished_at = now_datetime()
	log_doc.save(ignore_permissions=True)

	template_doc.last_used_on = now_datetime()
	template_doc.last_used_by = frappe.session.user
	template_doc.save(ignore_permissions=True)

	return frappe._dict(summary | {"log_name": log_doc.name, "error_file": "", "results": results[:25]})


def process_import_log(log_doc) -> frappe._dict:
	template_doc = frappe.get_doc(TEMPLATE_DOCTYPE, log_doc.template)
	template_doc.check_permission("read")
	target_doctype = cstr(template_doc.target_doctype).strip() or "Trip"

	if target_doctype in GROUPED_TRIP_IMPORT_DOCTYPES:
		return _process_grouped_trip_import(log_doc, template_doc, target_doctype)

	import_action = cstr(template_doc.get("import_action") or "None").strip()
	old_staff_payroll_import = target_doctype == "Staff Payroll" and is_staff_payroll_old_import_template(template_doc)
	columns = parse_columns_json(template_doc.columns_json)
	rows = _read_csv_rows(log_doc.uploaded_file)
	headers = [cstr(v).strip() for v in rows[0]]
	header_index_map = {_normalize_header(label): idx for idx, label in enumerate(headers)}
	field_map = get_importable_field_map(target_doctype)
	import_mode = log_doc.import_mode

	log_doc.status = "Running"
	log_doc.started_at = now_datetime()
	log_doc.save(ignore_permissions=True)

	results = []
	failure_rows = []
	created_count = 0
	updated_count = 0
	failed_count = 0
	skipped_count = 0

	# Mirrors Frappe's own standard Data Import (importer.py), which sets this
	# flag around its row inserts. Doctype controllers (e.g. Staff Payroll)
	# key import-only auto-fetch behaviour off this exact flag, so setting it
	# here lets this custom engine benefit the same way.
	frappe.flags.in_import = True
	try:
		for row_number, row in enumerate(rows[1:], start=2):
			if _is_blank_row(row):
				skipped_count += 1
				results.append(
					{
						"row_number": row_number,
						"status": "Ignored",
						"action": "",
						"message": _("Blank row, skipped."),
						"record_name": "",
					}
				)
				continue
			preview = _build_preview_row(template_doc, columns, header_index_map, row, row_number, import_mode)
			if preview.status == "Issue":
				failed_count += 1
				result = {
					"row_number": row_number,
					"status": "Failed",
					"action": preview.action,
					"message": preview.message,
					"record_name": "",
				}
				results.append(result)
				failure_rows.append(result | {"row_data": row})
				continue

			values: dict[str, Any] = {}
			component_values: dict[str, dict[str, Any]] = {"earnings": {}, "deductions": {}}
			advance_value_provided = False
			for column in columns:
				raw_value = _get_csv_value(row, header_index_map, column["csv_header"])
				if raw_value in (None, "") and column.get("default_value") not in (None, ""):
					raw_value = column.get("default_value")
				if raw_value in (None, ""):
					continue
				try:
					casted = _fieldtype_cast(raw_value, field_map[column["fieldname"]])
					casted = _validate_link_value(field_map[column["fieldname"]], casted)
				except Exception as exc:
					failed_count += 1
					result = {
						"row_number": row_number,
						"status": "Failed",
						"action": preview.action,
						"message": cstr(exc),
						"record_name": "",
					}
					results.append(result)
					failure_rows.append(result | {"row_data": row})
					values = {}
					break
				if column["fieldname"] == "name" and preview.action == "Create":
					continue
				field_info = field_map[column["fieldname"]]
				if old_staff_payroll_import and field_info.get("is_virtual_salary_component"):
					group = cstr(field_info.get("salary_component_group") or "")
					component_name = cstr(field_info.get("salary_component_name") or "")
					if group in component_values and component_name:
						component_values[group][component_name] = casted
						if group == "deductions" and component_name == "Advances":
							advance_value_provided = True
					continue
				# Skip read_only fields — usable as match keys but not updatable
				if cint(column.get("read_only")):
					continue
				values[column["fieldname"]] = casted
			if any(r["row_number"] == row_number and r["status"] == "Failed" for r in results):
				continue

			try:
				if import_action == "Cancel Document":
					# Cancel: only find existing doc, do not update fields
					if not preview.existing_name:
						raise Exception(_("Record not found to cancel."))
					doc = frappe.get_doc(target_doctype, preview.existing_name)
					final_action = _apply_import_action(doc, import_action, "Cancel")
					updated_count += 1
					results.append(
						{
							"row_number": row_number,
							"status": "Success",
							"action": final_action,
							"message": _("Record cancelled successfully."),
							"record_name": doc.name,
						}
					)
				elif preview.action == "Update":
					doc = frappe.get_doc(target_doctype, preview.existing_name)
					if old_staff_payroll_import:
						doc._tms_old_data_import = True
						doc.flags.tms_old_data_import = True
					for fieldname, value in values.items():
						if value in ("", None) and not cint(template_doc.get("allow_blank_update")):
							continue
						doc.set(fieldname, value)
					if old_staff_payroll_import:
						_apply_staff_payroll_component_values(doc, component_values)
						if advance_value_provided:
							doc.flags.tms_old_advance_overridden = True
					doc.save(ignore_permissions=False)
					if old_staff_payroll_import:
						doc.add_comment("Info", "TMS_OLD_DATA_IMPORT")
					final_action = _apply_import_action(doc, import_action, "Update")
					updated_count += 1
					results.append(
						{
							"row_number": row_number,
							"status": "Success",
							"action": final_action,
							"message": _("Record updated successfully."),
							"record_name": doc.name,
						}
					)
				else:
					doc = frappe.get_doc({"doctype": target_doctype})
					if old_staff_payroll_import:
						doc._tms_old_data_import = True
						doc.flags.tms_old_data_import = True
					_apply_template_defaults(template_doc, values, for_create=True)
					for fieldname, value in values.items():
						doc.set(fieldname, value)
					if old_staff_payroll_import:
						_apply_staff_payroll_component_values(doc, component_values)
						if advance_value_provided:
							doc.flags.tms_old_advance_overridden = True
					doc.insert(ignore_permissions=False)
					if old_staff_payroll_import:
						doc.add_comment("Info", "TMS_OLD_DATA_IMPORT")
					final_action = _apply_import_action(doc, import_action, "Create")
					created_count += 1
					results.append(
						{
							"row_number": row_number,
							"status": "Success",
							"action": final_action,
							"message": _("Record created successfully."),
							"record_name": doc.name,
						}
					)
			except Exception as exc:
				failed_count += 1
				results.append(
					{
						"row_number": row_number,
						"status": "Failed",
						"action": preview.action,
						"message": cstr(exc),
						"record_name": "",
					}
				)
				failure_rows.append({"row_number": row_number, "message": cstr(exc), "row_data": row})

		success_rows = created_count + updated_count
		summary = {
			"total_rows": len(rows) - 1,
			"success_rows": success_rows,
			"failed_rows": failed_count,
			"created_count": created_count,
			"updated_count": updated_count,
			"skipped_count": skipped_count,
		}

		error_file = ""
		if failure_rows:
			buffer = io.StringIO()
			writer = csv.writer(buffer)
			writer.writerow(["row_number", "message", *headers])
			for failure in failure_rows:
				writer.writerow([failure["row_number"], failure["message"], *(failure.get("row_data") or [])])
			file_doc = save_file(
				f"import_errors_{log_doc.name}.csv",
				buffer.getvalue().encode(),
				LOG_DOCTYPE,
				log_doc.name,
				is_private=0,
			)
			error_file = file_doc.file_url

		log_doc.status = "Completed With Errors" if failed_count else "Completed"
		log_doc.error_file = error_file
		log_doc.row_result_json = json.dumps(results, indent=2, default=str)
		log_doc.summary_json = json.dumps(summary, indent=2)
		log_doc.success_rows = success_rows
		log_doc.failed_rows = failed_count
		log_doc.created_count = created_count
		log_doc.updated_count = updated_count
		log_doc.skipped_count = skipped_count
		log_doc.finished_at = now_datetime()
		log_doc.save(ignore_permissions=True)

		template_doc.last_used_on = now_datetime()
		template_doc.last_used_by = frappe.session.user
		template_doc.save(ignore_permissions=True)

		frappe.flags.in_import = False
		return frappe._dict(summary | {"log_name": log_doc.name, "error_file": error_file, "results": results[:25]})
	except Exception:
		frappe.flags.in_import = False
		log_doc.status = "Failed"
		log_doc.finished_at = now_datetime()
		log_doc.row_result_json = json.dumps(results, indent=2, default=str)
		log_doc.summary_json = json.dumps(
			{
				"total_rows": len(rows) - 1,
				"success_rows": created_count + updated_count,
				"failed_rows": failed_count,
				"created_count": created_count,
				"updated_count": updated_count,
				"skipped_count": skipped_count,
			},
			indent=2,
		)
		log_doc.save(ignore_permissions=True)
		raise


def build_template_csv_content(template_doc) -> bytes:
	columns = parse_columns_json(template_doc.columns_json)
	headers = [column["csv_header"] for column in columns]

	target_doctype = cstr(template_doc.target_doctype).strip()
	for extra_header in GROUPED_TRIP_IMPORT_EXTRA_COLUMNS.get(target_doctype, []):
		if extra_header not in headers:
			headers.append(extra_header)

	buffer = io.StringIO()
	writer = csv.writer(buffer)
	writer.writerow(headers)
	return buffer.getvalue().encode("utf-8")
