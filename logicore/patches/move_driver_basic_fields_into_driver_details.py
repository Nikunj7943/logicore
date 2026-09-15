import json

import frappe


def execute():
    # Move Full Name / Status / Transporter (currently in the unlabeled top
    # section of the Driver form) into the "Drivers Details" section, right
    # after the section break, alongside Company/Branch.
    fo_name = "Driver-main-field_order"
    value = frappe.db.get_value("Property Setter", fo_name, "value")
    if value:
        order = json.loads(value)
        moved_fields = ["full_name", "status", "transporter"]
        for fieldname in moved_fields:
            if fieldname in order:
                order.remove(fieldname)

        anchor = "custom_employment_section"
        if anchor in order:
            idx = order.index(anchor) + 1
            for offset, fieldname in enumerate(moved_fields):
                order.insert(idx + offset, fieldname)

        frappe.db.set_value("Property Setter", fo_name, "value", json.dumps(order))

    # Rename that section from "Drivers  Details" to "Driver Details".
    section_field = "Driver-custom_employment_section"
    if frappe.db.exists("Custom Field", section_field):
        frappe.db.set_value("Custom Field", section_field, "label", "Driver Details")

    frappe.clear_cache(doctype="Driver")
