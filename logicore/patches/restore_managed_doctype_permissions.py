import frappe

from logicore.install import _restore_managed_doctype_permissions


def execute():
	_restore_managed_doctype_permissions()
	frappe.clear_cache()
