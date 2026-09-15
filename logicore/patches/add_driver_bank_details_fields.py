from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
    create_custom_field(
        "Driver",
        {
            "fieldname": "bank_details_section",
            "label": "Bank Details",
            "fieldtype": "Section Break",
            "insert_after": "nok_mobile",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "bank_name",
            "label": "Bank Name",
            "fieldtype": "Data",
            "insert_after": "bank_details_section",
            "reqd": 0,
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "bank_col_break_1",
            "fieldtype": "Column Break",
            "insert_after": "bank_name",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "bank_account_no",
            "label": "Bank Account No",
            "fieldtype": "Data",
            "insert_after": "bank_col_break_1",
            "reqd": 0,
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "bank_col_break_2",
            "fieldtype": "Column Break",
            "insert_after": "bank_account_no",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "bank_ifsc_code",
            "label": "Bank IFSC Code",
            "fieldtype": "Data",
            "insert_after": "bank_col_break_2",
            "reqd": 0,
        },
    )
