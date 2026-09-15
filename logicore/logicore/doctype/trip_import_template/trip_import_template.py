# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr
from frappe.utils.file_manager import save_file

from logicore.logicore.utils.trip_import_utils import (
	IMPORT_MODES,
	TARGET_DOCTYPE,
	build_template_csv_content,
	get_template_doc,
	get_trip_importable_fields,
	normalize_template_columns,
)


class TripImportTemplate(Document):
	def validate(self):
		self.target_doctype = TARGET_DOCTYPE
		if self.default_import_mode not in IMPORT_MODES:
			frappe.throw(_("Default Import Mode is invalid."))
		self.match_field = cstr(self.match_field).strip()
		columns = normalize_template_columns(self.columns_json, self.match_field, self.default_import_mode)
		self.columns_json = json.dumps(columns, indent=2)


@frappe.whitelist()
def get_trip_import_templates(company: str | None = None):
	filters = {"is_active": 1}
	if company:
		filters["company"] = ["in", [company, ""]]
	rows = frappe.db.get_all(
		"Trip Import Template",
		filters=filters,
		fields=["name", "template_name", "company", "default_import_mode", "match_field"],
		order_by="template_name asc",
	)
	return rows


@frappe.whitelist()
def get_trip_import_template(template_name: str):
	doc = get_template_doc(template_name)
	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"company": doc.company,
		"match_field": doc.match_field,
		"default_import_mode": doc.default_import_mode,
		"allow_blank_update": cint(doc.allow_blank_update),
		"columns": json.loads(doc.columns_json or "[]"),
	}


@frappe.whitelist()
def get_trip_importable_trip_fields():
	return get_trip_importable_fields()


@frappe.whitelist()
def download_trip_import_template(template_name: str):
	doc = get_template_doc(template_name)
	content = build_template_csv_content(doc)
	file_doc = save_file(
		f"Trip Import Template - {doc.template_name}.csv",
		content,
		doc.doctype,
		doc.name,
		is_private=0,
	)
	doc.db_set("sample_file", file_doc.file_url)
	frappe.response["type"] = "download"
	frappe.response["filename"] = f"Trip Import Template - {doc.template_name}.csv"
	frappe.response["filecontent"] = content
	frappe.response["display_content_as"] = "attachment"
