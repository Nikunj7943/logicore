# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document

from logicore.logicore.utils.import_utils import (
	build_preview_payload,
	create_validated_log,
	get_log_doc,
	get_template_doc,
	process_import_log,
)


class ImportLog(Document):
	pass


def _check_target_doctype_import_permission(template_doc):
	"""Enforce the same "import" permission bit TMS User Group syncs into
	Custom DocPerm for the template's target doctype — mirrors what gates
	Frappe's own standard Data Import button, so this custom tool can't be
	used to bypass it."""
	target_doctype = template_doc.target_doctype
	if not frappe.has_permission(target_doctype, "import"):
		frappe.throw(_("Not permitted to import {0} records.").format(target_doctype))


@frappe.whitelist()
def upload_and_preview_import(template_name: str, import_mode: str, file_url: str, company: str | None = None):
	template_doc = get_template_doc(template_name)
	template_doc.check_permission("read")
	_check_target_doctype_import_permission(template_doc)
	if not frappe.has_permission("Import Log", "create"):
		frappe.throw(_("Not permitted to create Import Log."))
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
def run_import(template_name: str, import_mode: str, file_url: str | None = None, company: str | None = None, log_name: str | None = None):
	if log_name:
		log_doc = get_log_doc(log_name, permtype="write")
		_check_target_doctype_import_permission(get_template_doc(log_doc.template))
	else:
		template_doc = get_template_doc(template_name)
		_check_target_doctype_import_permission(template_doc)
		preview = build_preview_payload(template_doc, file_url, import_mode)
		if not preview.can_import:
			frappe.throw(_("Fix the validation errors before importing."))
		log_doc = create_validated_log(template_doc, file_url, import_mode, company, preview)
	return process_import_log(log_doc)


@frappe.whitelist()
def get_import_log(log_name: str):
	doc = get_log_doc(log_name)
	return {
		"name": doc.name,
		"status": doc.status,
		"summary": json.loads(doc.summary_json or "{}"),
		"preview": json.loads(doc.preview_json or "{}"),
		"rows": json.loads(doc.row_result_json or "[]"),
		"error_file": doc.error_file,
	}

