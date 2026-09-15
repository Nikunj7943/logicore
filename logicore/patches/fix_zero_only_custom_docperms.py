import frappe

from logicore.install import _cleanup_zero_only_custom_docperms


def execute():
	"""Delete Custom DocPerm rows that block native access without granting any access.

	When every Custom DocPerm row on a doctype has read=0, Frappe's permission resolver
	uses the Custom DocPerm table (returning no access) instead of falling back to the
	file-based DocPerm rows — locking out System Manager and Administrator.

	For non-TMS-managed doctypes (e.g. Role, DocType) these zero rows were created by
	ERPNext/HRMS at install time and serve no purpose — removing them restores native
	DocPerm behaviour immediately.
	"""
	_cleanup_zero_only_custom_docperms()
	frappe.clear_cache()
