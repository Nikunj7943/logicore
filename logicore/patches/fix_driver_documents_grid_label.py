import frappe


def execute():
    # The Table field's own label duplicated the section heading right above
    # it ("Driver Documents" shown twice). Blank the field label so only the
    # section title remains.
    name = "Driver-driving_license_category-label"
    if frappe.db.exists("Property Setter", name):
        frappe.db.set_value("Property Setter", name, "value", "")
    else:
        from frappe.custom.doctype.property_setter.property_setter import make_property_setter

        make_property_setter("Driver", "driving_license_category", "label", "", "Data")

    frappe.clear_cache(doctype="Driver")
