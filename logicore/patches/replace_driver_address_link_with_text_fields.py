from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    # Hide the core "address" Link field (dropdown picker into Address doctype)
    # -- replaced below with free-text Current/Permanent Address boxes, same
    # layout as the standard Employee form.
    make_property_setter("Driver", "address", "hidden", "1", "Check")

    create_custom_field(
        "Driver",
        {
            "fieldname": "address_section",
            "label": "Address",
            "fieldtype": "Section Break",
            "insert_after": "address",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "current_address",
            "label": "Current Address",
            "fieldtype": "Small Text",
            "insert_after": "address_section",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "current_accommodation_type",
            "label": "Current Address Is",
            "fieldtype": "Select",
            "options": "\nRented\nOwned",
            "insert_after": "current_address",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "address_column_break",
            "fieldtype": "Column Break",
            "insert_after": "current_accommodation_type",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "permanent_address",
            "label": "Permanent Address",
            "fieldtype": "Small Text",
            "insert_after": "address_column_break",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "permanent_accommodation_type",
            "label": "Permanent Address Is",
            "fieldtype": "Select",
            "options": "\nRented\nOwned",
            "insert_after": "permanent_address",
        },
    )
