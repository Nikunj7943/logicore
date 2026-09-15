import json

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.model import no_value_fields

from logicore.tms_report_menu import is_tms_report_menu_admin

# A password box / file / signature / map picker isn't usable as a filter input even
# though it technically holds a value. Kept in sync with public/js/tms_quick_filter_override.js.
NON_FILTERABLE_FIELDTYPES = {"Password", "Signature", "Attach", "Attach Image", "Geolocation"}


def is_filterable_fieldtype(fieldtype):
	"""Any field that can hold a value is a valid quick filter candidate — only layout
	fields (Section Break, Table, HTML, Button, ...) and the blocklist above are excluded.
	"""
	return fieldtype not in no_value_fields and fieldtype not in NON_FILTERABLE_FIELDTYPES


def save_tms_quick_filter_fields(doctype, parent_fields, child_entries):
	if not doctype:
		frappe.throw(_("DocType is required"))

	if not is_tms_report_menu_admin():
		raise frappe.PermissionError

	parent_fields = frappe.parse_json(parent_fields) or []
	child_entries = frappe.parse_json(child_entries) or []

	_set_parent_standard_filters(doctype, parent_fields)
	cleaned_child_entries = _set_child_quick_filters(doctype, child_entries)

	frappe.clear_cache(doctype=doctype)
	return {"parent_fields": parent_fields, "child_entries": cleaned_child_entries}


def _set_parent_standard_filters(doctype, parent_fields):
	meta = frappe.get_meta(doctype)
	candidate_fields = [df for df in meta.fields if is_filterable_fieldtype(df.fieldtype)]

	for df in candidate_fields:
		target = df.fieldname in parent_fields
		if bool(df.in_standard_filter) != target:
			_set_property_setter(doctype, df.fieldname, "in_standard_filter", "1" if target else "0")


def _set_property_setter(doctype, fieldname, property_name, value):
	property_setter = frappe.db.get_value(
		"Property Setter",
		{"doc_type": doctype, "field_name": fieldname, "property": property_name},
	)
	if property_setter:
		doc = frappe.get_doc("Property Setter", property_setter)
		doc.value = value
		doc.save(ignore_permissions=True)
		return

	make_property_setter(
		doctype,
		fieldname,
		property_name,
		value,
		"Check",
		validate_fields_for_doctype=False,
	)


def _set_child_quick_filters(doctype, child_entries):
	meta = frappe.get_meta(doctype)
	child_doctypes = {df.options for df in meta.fields if df.fieldtype in ("Table", "Table MultiSelect")}

	cleaned = []
	for entry in child_entries:
		child_doctype = entry.get("doctype")
		fieldname = entry.get("fieldname")
		if not child_doctype or not fieldname:
			continue
		if child_doctype not in child_doctypes:
			frappe.throw(_("{0} is not a child table of {1}").format(child_doctype, doctype))
		child_field = frappe.get_meta(child_doctype).get_field(fieldname)
		if not child_field:
			frappe.throw(_("{0} is not a field of {1}").format(fieldname, child_doctype))
		if not is_filterable_fieldtype(child_field.fieldtype):
			frappe.throw(_("{0} cannot be used as a filter").format(fieldname))
		cleaned.append({"doctype": child_doctype, "fieldname": fieldname})

	if frappe.db.exists("List View Settings", doctype):
		doc = frappe.get_doc("List View Settings", doctype)
	else:
		doc = frappe.new_doc("List View Settings")
		doc.name = doctype

	doc.tms_quick_filter_fields = json.dumps(cleaned)
	doc.save(ignore_permissions=True)
	return cleaned


@frappe.whitelist()
def save_tms_quick_filter_fields_api(doctype, parent_fields, child_entries):
	return save_tms_quick_filter_fields(doctype, parent_fields, child_entries)
