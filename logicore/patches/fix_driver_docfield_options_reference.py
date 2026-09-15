import frappe


def execute():
    # The core DocField row itself (not a Property Setter) still has its
    # "options" pointing at "Driver Documents" -- a leftover from the earlier
    # accidental DocType rename. The real doctype/table is correctly named
    # "Driving License Category" again, so just repoint this one reference.
    correct_dt = "Driving License Category"
    frappe.db.set_value(
        "DocField",
        {"parent": "Driver", "fieldname": "driving_license_category"},
        "options",
        correct_dt,
    )
    frappe.clear_cache(doctype="Driver")
    frappe.clear_cache()
    frappe.db.commit()
