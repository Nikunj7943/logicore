import frappe


def execute():
    name = "Driver-next_of_kin"
    if frappe.db.exists("Custom Field", name):
        frappe.db.set_value("Custom Field", name, "fieldtype", "Data")
        frappe.db.set_value("Custom Field", name, "options", "")
        frappe.clear_cache(doctype="Driver")
