import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    # Driver form: "Driving License Categories" section + "Driving License Category"
    # table field -> renamed to "Driver Documents" since the grid now holds an
    # attached file per row, not just license class info.
    make_property_setter(
        "Driver", "driving_license_categories", "label", "Driver Documents", "Data"
    )
    make_property_setter(
        "Driver", "driving_license_category", "label", "Driver Documents", "Data"
    )

    # Child table "Driving License Category": rename the "class" column from
    # "Driver licence class" to "Document Type".
    make_property_setter(
        "Driving License Category", "class", "label", "Document Type", "Data"
    )

    # Add an optional attachment column for the uploaded document.
    create_custom_field(
        "Driving License Category",
        {
            "fieldname": "document_attached",
            "label": "Document Attached",
            "fieldtype": "Attach",
            "insert_after": "expiry_date",
            "reqd": 0,
            "in_list_view": 1,
        },
    )

    frappe.clear_cache(doctype="Driver")
    frappe.clear_cache(doctype="Driving License Category")
