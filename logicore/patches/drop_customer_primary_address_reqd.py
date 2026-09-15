import frappe


def execute():
    stale = "Customer-customer_primary_address-reqd"
    if frappe.db.exists("Property Setter", stale):
        frappe.delete_doc(
            "Property Setter", stale, force=True, ignore_permissions=True
        )
        frappe.clear_cache(doctype="Customer")
        frappe.db.commit()
