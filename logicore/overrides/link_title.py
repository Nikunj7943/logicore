# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_link_title(doctype, docname):
	"""Override for frappe.desk.search.get_link_title -- identical except it
	doesn't crash when `docname` is blank or doesn't exist.

	Report View calls this once per row for every Link column that has
	show_title_field_in_link on (Employee, Driver, Item, Supplier, Purchase
	Invoice Item here), to resolve a friendly display title instead of the raw
	docname -- automatically, on every page load, no hover or click involved.
	For a blank Link field the value sent is JS `null` stringified to the
	literal text "null"; core's frappe.get_lazy_doc() then throws
	DoesNotExistError, which the client surfaces as a "<Doctype> null not
	found" popup to every user who opens the list. Guarding the lookup here
	the same way frappe.form.formatters.Link's `if (!value) return ""` already
	guards the equivalent Form-view rendering path.
	"""
	if not docname or docname == "null" or not frappe.db.exists(doctype, docname):
		return docname

	meta = frappe.get_meta(doctype)
	if meta.show_title_field_in_link:
		doc = frappe.get_lazy_doc(doctype, docname)
		doc.check_permission()
		return doc.get(meta.title_field)

	return docname
