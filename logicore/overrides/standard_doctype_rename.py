# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

"""Lets users rename standard ERPNext/Frappe `field:<x>` autoname doctypes by
editing the naming field directly and saving, instead of using Menu > Rename.
Paired with public/js/tms_naming_field_unhide.js, which un-hides the field on
the form (core hides it once saved). See logicore/utils/renaming.py for
the underlying mechanism — same pattern already used by our own TMS doctypes.
"""

from logicore.utils.renaming import apply_pending_rename, capture_rename_target

NAMING_FIELD_BY_DOCTYPE = {
	"Vehicle": "license_plate",
	"Company": "company_name",
	"UOM": "uom_name",
	"Item Group": "item_group_name",
	"Item": "item_code",
	"GST HSN Code": "hsn_code",
	"Supplier Group": "supplier_group_name",
	"Customer Group": "customer_group_name",
	"Branch": "branch",
}


def before_save(doc, method=None):
	fieldname = NAMING_FIELD_BY_DOCTYPE.get(doc.doctype)
	if fieldname:
		capture_rename_target(doc, fieldname)


def on_update(doc, method=None):
	fieldname = NAMING_FIELD_BY_DOCTYPE.get(doc.doctype)
	if fieldname:
		apply_pending_rename(doc)
