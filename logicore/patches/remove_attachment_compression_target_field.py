import frappe


def execute():
    name = "System Settings-custom_attachment_compression_target_mb"
    if frappe.db.exists("Custom Field", name):
        frappe.delete_doc("Custom Field", name, ignore_permissions=True)
        frappe.clear_cache(doctype="System Settings")
        frappe.db.commit()
