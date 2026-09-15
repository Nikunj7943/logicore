import frappe


def execute():
    name = "Driver-next_of_kin_section"
    if frappe.db.exists("Custom Field", name):
        frappe.db.set_value("Custom Field", name, "label", "Next of Kind Details")
        frappe.clear_cache(doctype="Driver")
