import csv
import io
import json
from datetime import date, datetime

import frappe

# Trip / Amazon Trip already have their own dedicated export (with Business Format
# column presets) — this generic exporter must never handle them.
EXCLUDED_DOCTYPES = {"Trip", "Amazon Trip"}

SKIP_FIELDS = {
	"amended_from", "docstatus", "doctype", "owner", "creation", "modified",
	"modified_by", "idx", "_assign", "_comments", "_user_tags", "workflow_state",
}
SKIP_FIELDTYPES = {
	"Section Break", "Column Break", "Tab Break", "Fold",
	"Heading", "HTML", "Button", "Image", "Attach Image",
	"Signature", "Geolocation", "Barcode", "Break", "Table", "Table MultiSelect",
}


def is_export_supported(doctype):
	if not doctype or doctype in EXCLUDED_DOCTYPES:
		return False
	meta = frappe.get_meta(doctype)
	return not meta.istable and not meta.issingle


def _plain_fields(meta):
	"""Non-table columns from a single doctype's own meta (parent or child)."""
	columns = []
	for field in meta.fields:
		if (
			not field.hidden
			and field.fieldname not in SKIP_FIELDS
			and field.fieldtype not in SKIP_FIELDTYPES
			and field.label
		):
			columns.append({
				"fieldname": field.fieldname,
				"label": field.label,
				"checked": field.fieldname == "name" or bool(field.reqd),
				"depends_on": field.depends_on or None,
			})
	return columns


def get_export_columns(doctype):
	"""Every field on the doctype is offered as a column, except hidden fields,
	system/meta fields, and layout fieldtypes (matches Trip/Amazon Trip's own
	export column list, which also offers every field, not just in_list_view ones).
	Child table fields are also offered, prefixed "<table_fieldname>.<child_fieldname>"
	so they can be selected and exported as extra flattened columns (one export row per
	child row), same as Amazon Trip's own Amazon Trip Detail flattening."""
	meta = frappe.get_meta(doctype)
	columns = _plain_fields(meta)

	for field in meta.fields:
		if field.fieldtype != "Table" or not field.options:
			continue
		try:
			child_meta = frappe.get_meta(field.options)
		except Exception:
			continue
		for child_col in _plain_fields(child_meta):
			columns.append({
				"fieldname": f"{field.fieldname}.{child_col['fieldname']}",
				"label": f"{field.label} - {child_col['label']}",
				"checked": False,
				"depends_on": None,
			})

	return columns


def _fmt_val(v):
	if isinstance(v, datetime):
		return v.strftime("%d-%m-%Y %H:%M")
	if isinstance(v, date):
		return v.strftime("%d-%m-%Y")
	return v


def _resolve_naming_series(rows, fields_to_export):
	"""The naming_series field stores the raw autoname template (e.g. "RCT-.YYYY.-.MM.-.#####"),
	not the resolved document number, for existing records — substitute the real docname
	(what actually got generated) instead. Generic: every Frappe doctype that auto-names via
	naming_series uses this exact fieldname, regardless of its custom label (e.g. "Receipt No")."""
	if "naming_series" not in fields_to_export:
		return rows
	for row in rows:
		if row.get("name") is not None:
			row["naming_series"] = row["name"]
	return rows


def _label(meta, fieldname):
	if fieldname == "name":
		return frappe._("ID")
	df = meta.get_field(fieldname)
	return df.label if df else fieldname


def _resolve_link_fields(doctype, rows, fields_to_export):
	"""Generic Link → display-name resolution: for every selected Link field, batch-fetch
	the target doctype's title_field (falling back to name) and substitute it in, instead
	of exporting raw IDs (driver, employee, bank account, vendor, customer, etc.)."""
	if not rows:
		return rows

	meta = frappe.get_meta(doctype)
	link_fields = {}
	for fieldname in fields_to_export:
		df = meta.get_field(fieldname)
		if df and df.fieldtype == "Link" and df.options:
			link_fields[fieldname] = df.options

	for fieldname, target_dt in link_fields.items():
		ids = {row.get(fieldname) for row in rows if row.get(fieldname)}
		if not ids:
			continue

		try:
			target_meta = frappe.get_meta(target_dt)
		except Exception:
			continue

		display_field = target_meta.title_field or "name"
		if display_field == "name":
			continue  # nothing to resolve, already showing the name

		lookup = {
			r["name"]: r.get(display_field)
			for r in frappe.get_all(
				target_dt,
				filters={"name": ["in", list(ids)]},
				fields=["name", display_field],
			)
		}
		for row in rows:
			raw = row.get(fieldname)
			if raw:
				row[fieldname] = lookup.get(raw) or raw

	return rows


def _build_frappe_filters(doctype, filters):
	"""Accepts the list view's own get_filters() shape: [[doctype, fieldname, operator, value], ...]
	(fieldname/operator/value triplets are also accepted) or a plain {field: value} dict."""
	if not filters:
		return []

	if isinstance(filters, dict):
		return [[doctype, k, "=", v] for k, v in filters.items() if v not in (None, "")]

	result = []
	for f in filters:
		if not isinstance(f, (list, tuple)):
			continue
		if len(f) == 4:
			result.append([f[0] or doctype, f[1], f[2], f[3]])
		elif len(f) == 3:
			result.append([doctype, f[0], f[1], f[2]])
	return result


@frappe.whitelist()
def export_doctype_filtered(doctype, filters=None, selected_fields=None):
	"""Generic list/report-view CSV export for any doctype in this app other than
	Trip/Amazon Trip (which have their own dedicated export dialogs), Single doctypes,
	and child tables. POSTed from a hidden form so the browser downloads the file directly.
	Link fields are auto-resolved to their target doctype's title_field.
	"""
	if not is_export_supported(doctype):
		frappe.throw(frappe._("Export is not available for {0}.").format(doctype))

	if not frappe.has_permission(doctype, "export"):
		frappe.throw(
			frappe._("Not permitted to export {0}.").format(doctype), frappe.PermissionError
		)

	if isinstance(filters, str):
		filters = json.loads(filters)
	if isinstance(selected_fields, str):
		selected_fields = json.loads(selected_fields)
	selected_fields = list(selected_fields or [])

	if not selected_fields:
		selected_fields = [c["fieldname"] for c in get_export_columns(doctype) if c["checked"]]
	if not selected_fields:
		frappe.throw(frappe._("No exportable columns found for {0}.").format(doctype))

	meta = frappe.get_meta(doctype)
	frappe_filters = _build_frappe_filters(doctype, filters)

	parent_fields = [f for f in selected_fields if "." not in f]
	child_field_specs = [f.split(".", 1) for f in selected_fields if "." in f]

	if child_field_specs:
		table_fieldnames = {spec[0] for spec in child_field_specs}
		if len(table_fieldnames) > 1:
			frappe.throw(
				frappe._("Please export columns from only one child table at a time ({0}).").format(
					", ".join(sorted(table_fieldnames))
				)
			)
		table_fieldname = table_fieldnames.pop()
		table_df = meta.get_field(table_fieldname)
		if not table_df or table_df.fieldtype != "Table":
			frappe.throw(frappe._("{0} is not a child table on {1}.").format(table_fieldname, doctype))

		child_doctype = table_df.options
		child_fieldnames = [spec[1] for spec in child_field_specs]

		headers = [_label(meta, fn) for fn in parent_fields] + [
			_label(frappe.get_meta(child_doctype), fn) for fn in child_fieldnames
		]

		parent_rows = frappe.get_list(
			doctype,
			filters=frappe_filters or {},
			fields=list(dict.fromkeys(["name", *parent_fields])),
			order_by="modified desc",
			limit_page_length=0,
			ignore_permissions=False,
		)
		parent_rows = _resolve_link_fields(doctype, parent_rows, parent_fields)
		parent_rows = _resolve_naming_series(parent_rows, parent_fields)

		csv_rows = [headers]
		for parent in parent_rows:
			children = frappe.get_all(
				child_doctype,
				filters={"parent": parent["name"], "parenttype": doctype, "parentfield": table_fieldname},
				fields=list(dict.fromkeys(["name", *child_fieldnames])),
				order_by="idx asc",
			)
			children = _resolve_link_fields(child_doctype, children, child_fieldnames)

			parent_values = [
				str(_fmt_val(parent.get(fn))) if parent.get(fn) is not None else "" for fn in parent_fields
			]
			if not children:
				csv_rows.append(parent_values + [""] * len(child_fieldnames))
				continue
			for child in children:
				child_values = [
					str(_fmt_val(child.get(fn))) if child.get(fn) is not None else ""
					for fn in child_fieldnames
				]
				csv_rows.append(parent_values + child_values)
	else:
		headers = [_label(meta, fn) for fn in selected_fields]

		query_fields = selected_fields
		if "naming_series" in selected_fields and "name" not in selected_fields:
			query_fields = list(dict.fromkeys([*selected_fields, "name"]))

		rows = frappe.get_list(
			doctype,
			filters=frappe_filters or {},
			fields=query_fields,
			order_by="modified desc",
			limit_page_length=0,
			ignore_permissions=False,
		)
		rows = _resolve_link_fields(doctype, rows, selected_fields)
		rows = _resolve_naming_series(rows, selected_fields)

		csv_rows = [headers]
		for row in rows:
			csv_rows.append(
				[str(_fmt_val(row.get(fn))) if row.get(fn) is not None else "" for fn in selected_fields]
			)

	buf = io.StringIO()
	csv.writer(buf).writerows(csv_rows)

	ts = frappe.utils.now_datetime().strftime("%d-%m-%Y %H%M")
	frappe.response["filename"] = f"{doctype} Export - {ts}.csv"
	frappe.response["filecontent"] = buf.getvalue().encode("utf-8-sig")
	frappe.response["type"] = "binary"
