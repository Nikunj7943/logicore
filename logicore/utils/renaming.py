# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe


def capture_rename_target(doc, fieldname):
	"""Call from before_save on a `field:<fieldname>` autoname doctype.

	Frappe's autoname sync only runs name -> field, so editing the naming
	field directly and saving silently reverts it back to match `name`
	(see base_document._sync_autoname_field). Here we stash the edited value
	and reset the field to the current name so this save proceeds normally
	under the old name; the actual rename is applied afterwards in
	on_update via apply_pending_rename(), once other field changes are safe
	in the DB.
	"""
	doc._rename_target = None
	if not doc.is_new() and doc.get(fieldname) != doc.name:
		doc._rename_target = doc.get(fieldname)
		doc.set(fieldname, doc.name)


def apply_pending_rename(doc):
	"""Call from on_update. Performs the rename queued by capture_rename_target().

	Returns True if a rename was performed.
	"""
	target = getattr(doc, "_rename_target", None)
	if not target:
		return False
	frappe.rename_doc(doc.doctype, doc.name, target, force=True)
	frappe.clear_cache()
	return True
