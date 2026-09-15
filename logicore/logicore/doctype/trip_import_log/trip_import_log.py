# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe.model.document import Document

from logicore.logicore.utils.trip_import_utils import (
	build_preview_payload,
	create_validated_log,
	get_log_doc,
	get_template_doc,
	process_import_log,
)


class TripImportLog(Document):
	pass


@frappe.whitelist()
def upload_and_preview_trip_import(template_name: str, import_mode: str, file_url: str, company: str | None = None):
	template_doc = get_template_doc(template_name)
	template_doc.check_permission("read")
	if not frappe.has_permission("Trip Import Log", "create"):
		frappe.throw("Not permitted to create Trip Import Log.")
	preview = build_preview_payload(template_doc, file_url, import_mode)
	response = {
		"template_name": template_doc.template_name,
		"preview": preview,
	}
	if preview.can_import:
		log = create_validated_log(template_doc, file_url, import_mode, company, preview)
		response["log_name"] = log.name
	return response


@frappe.whitelist()
def run_trip_import(template_name: str, import_mode: str, file_url: str | None = None, company: str | None = None, log_name: str | None = None):
	if log_name:
		log_doc = get_log_doc(log_name, permtype="write")
	else:
		template_doc = get_template_doc(template_name)
		preview = build_preview_payload(template_doc, file_url, import_mode)
		if not preview.can_import:
			frappe.throw("Fix the validation errors before importing.")
		log_doc = create_validated_log(template_doc, file_url, import_mode, company, preview)
	return process_import_log(log_doc)


@frappe.whitelist()
def get_trip_import_log(log_name: str):
	doc = get_log_doc(log_name)
	return {
		"name": doc.name,
		"status": doc.status,
		"summary": json.loads(doc.summary_json or "{}"),
		"preview": json.loads(doc.preview_json or "{}"),
		"rows": json.loads(doc.row_result_json or "[]"),
		"error_file": doc.error_file,
	}

