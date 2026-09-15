from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
    # Same document grid as the Driver form (Document Type / Description /
    # Issuing Date / Expiry Date / Document Attached), reusing the same
    # "Driving License Category" child doctype -- it's already a generic
    # document row, no need for a second near-identical child doctype.
    # Placed at the end of the "Personal Details" tab, after the existing
    # Aadhar/Driving License number fields.
    create_custom_field(
        "Employee",
        {
            "fieldname": "employee_documents_section",
            "label": "Employee Documents",
            "fieldtype": "Section Break",
            "insert_after": "custom_license_expiry_date",
        },
    )
    create_custom_field(
        "Employee",
        {
            "fieldname": "employee_documents",
            "label": "",
            "fieldtype": "Table",
            "options": "Driving License Category",
            "insert_after": "employee_documents_section",
        },
    )
