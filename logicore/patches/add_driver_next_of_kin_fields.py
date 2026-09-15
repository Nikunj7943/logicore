from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
    create_custom_field(
        "Driver",
        {
            "fieldname": "next_of_kin_section",
            "label": "Next of Kin Details",
            "fieldtype": "Section Break",
            "insert_after": "driving_license_category",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "next_of_kin",
            "label": "Next of Kin",
            "fieldtype": "Select",
            "options": "\nFather\nMother\nSpouse\nSon\nDaughter\nBrother\nSister\nOther",
            "insert_after": "next_of_kin_section",
            "reqd": 0,
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "nok_col_break_1",
            "fieldtype": "Column Break",
            "insert_after": "next_of_kin",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "nok_name",
            "label": "NOK Name",
            "fieldtype": "Data",
            "insert_after": "nok_col_break_1",
            "reqd": 0,
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "nok_col_break_2",
            "fieldtype": "Column Break",
            "insert_after": "nok_name",
        },
    )
    create_custom_field(
        "Driver",
        {
            "fieldname": "nok_mobile",
            "label": "NOK Mobile",
            "fieldtype": "Data",
            "insert_after": "nok_col_break_2",
            "reqd": 0,
        },
    )
