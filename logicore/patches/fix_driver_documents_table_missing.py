import frappe


def execute():
    correct_dt = "Driving License Category"
    wrong_dt = "Driver Documents"

    # Most likely cause: while renaming the field/section labels via
    # Customize Form in the browser, the "Options" box on the
    # "driving_license_category" Table field (which stores the *child
    # doctype name*, not the display label) got overwritten to "Driver
    # Documents" -- a doctype/table that never actually exists. Reset it.
    ps_name = "Driver-driving_license_category-options"
    if frappe.db.exists("Property Setter", ps_name):
        value = frappe.db.get_value("Property Setter", ps_name, "value")
        if value != correct_dt:
            frappe.db.set_value("Property Setter", ps_name, "value", correct_dt)

    # Less likely, but if the DocType itself got renamed (not just the field
    # options), rename it back so the physical table lines up with every
    # place in core/ERPNext code that still refers to "Driving License
    # Category" by name.
    if frappe.db.exists("DocType", wrong_dt) and not frappe.db.exists("DocType", correct_dt):
        frappe.rename_doc("DocType", wrong_dt, correct_dt, force=True, ignore_permissions=True)

    frappe.clear_cache(doctype="Driver")
    frappe.clear_cache(doctype=correct_dt)
    frappe.clear_cache()
    frappe.db.commit()
