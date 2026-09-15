# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr
from frappe.utils.file_manager import save_file

from logicore.utils.renaming import apply_pending_rename, capture_rename_target
from logicore.logicore.utils.import_utils import (
	IMPORT_MODES,
	build_template_csv_content,
	get_importable_fields as _get_importable_fields,
	get_template_doc,
	normalize_template_columns,
	parse_columns_json,
)


TMS_IMPORTABLE_DOCTYPES = [
	"Trip",
	"Amazon Trip",
	"City",
	"Business Format",
	"Business Subformat",
	"Standard KM",
	"Vehicle Type",
	"Trip Type",
	"Trip Classification",
	"Types of Goods",
	"Regulatory",
	"Compliances",
	"Vehicle Expense",
	"Fuel Urea Expenses",
	"Repair Expenses",
	"Tyre Expenses",
	"Battery Expenses",
	"Service Log",
	"Service Logs",
	"Vehicle Finance",
	"Vehicle Market",
	"Receipt",
	"Payment",
	"Vendor Payment",
	"Staff Attendance",
	"Staff Payroll",
	"Alert Settings",
]


@frappe.whitelist()
def get_tms_importable_doctypes():
	"""Returns only the doctypes that make sense for bulk import."""
	return TMS_IMPORTABLE_DOCTYPES


@frappe.whitelist()
def can_user_import_doctype(doctype: str):
	"""Server-side permission probe for import buttons.

	We use this instead of trusting only the browser permission cache so the
	TMS list-view button follows the actual current user permissions.
	"""
	if not doctype or not frappe.db.exists("DocType", doctype):
		return False
	meta = frappe.get_meta(doctype)
	if not getattr(meta, "allow_import", 0):
		return False
	return bool(frappe.has_permission(doctype, "import"))


class ImportTemplate(Document):
	def validate(self):
		if not self.target_doctype:
			frappe.throw(_("Select Doc Name is mandatory."))
		if not frappe.db.exists("DocType", self.target_doctype):
			frappe.throw(_("Invalid Doc Name: {0}").format(self.target_doctype))
		if self.default_import_mode not in IMPORT_MODES:
			frappe.throw(_("Default Import Mode is invalid."))
		self.match_field = cstr(self.match_field).strip()
		columns = normalize_template_columns(
			self.columns_json,
			self.match_field,
			self.default_import_mode,
			target_doctype=self.target_doctype,
		)
		self.columns_json = json.dumps(columns, indent=2)

		# Server-side: ensure at least one match key for Update modes
		if self.default_import_mode in ("Update Existing Only", "Update or Create"):
			match_key_cols = [c for c in parse_columns_json(self.columns_json) if cint(c.get("is_match_key"))]
			if not match_key_cols:
				frappe.throw(_("At least one column must be marked as Match Key for Update modes."))

	def before_save(self):
		capture_rename_target(self, "template_name")

	def on_update(self):
		apply_pending_rename(self)


@frappe.whitelist()
def get_import_templates(company: str | None = None, target_doctype: str | None = None):
	filters: dict = {"is_active": 1}
	if company:
		filters["company"] = ["in", [company, ""]]
	if target_doctype:
		filters["target_doctype"] = target_doctype
	rows = frappe.db.get_all(
		"Import Template",
		filters=filters,
		fields=["name", "template_name", "target_doctype", "company", "default_import_mode", "match_field"],
		order_by="template_name asc",
	)
	return rows


@frappe.whitelist()
def get_import_template(template_name: str):
	doc = get_template_doc(template_name)
	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"target_doctype": doc.target_doctype,
		"company": doc.company,
		"match_field": doc.match_field,
		"default_import_mode": doc.default_import_mode,
		"allow_blank_update": cint(doc.allow_blank_update),
		"import_action": doc.import_action or "None",
		"columns": json.loads(doc.columns_json or "[]"),
	}


@frappe.whitelist()
def get_importable_fields(doctype: str | None = None):
	"""Returns importable fields for the given doctype."""
	return _get_importable_fields(doctype or "Trip")


@frappe.whitelist()
def download_import_template(template_name: str):
	doc = get_template_doc(template_name)
	content = build_template_csv_content(doc)
	safe_name = doc.template_name.replace("/", "-").replace("\\", "-")
	filename = f"Import Template - {safe_name}.csv"
	file_doc = save_file(
		filename,
		content,
		doc.doctype,
		doc.name,
		is_private=0,
	)
	doc.db_set("sample_file", file_doc.file_url)
	frappe.response["type"] = "download"
	frappe.response["filename"] = filename
	frappe.response["filecontent"] = content
	frappe.response["display_content_as"] = "attachment"
