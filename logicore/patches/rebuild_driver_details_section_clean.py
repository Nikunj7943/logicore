import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
    # Field order kept getting reverted because earlier fixes used raw
    # frappe.db.set_value (bypasses on_update hooks -> never auto-exported to
    # the fixture file -> the next migrate's "Syncing customizations" step
    # re-imported the stale file and wiped the change). On top of that, a
    # manual Customize Form edit ended up deleting the "Driver Details"
    # section break + its column break entirely and creating a stray empty
    # duplicate section instead. This rebuilds everything from scratch and
    # saves via the ORM (not db.set_value) so it finally sticks.

    # 1. Remove the stray empty duplicate section created by mistake.
    stray = "Driver-custom_drivers__details"
    if frappe.db.exists("Custom Field", stray):
        frappe.delete_doc("Custom Field", stray, ignore_permissions=True, force=True)

    # 2. Recreate the section break + column break if they got deleted.
    if not frappe.db.exists("Custom Field", "Driver-custom_employment_section"):
        create_custom_field(
            "Driver",
            {
                "fieldname": "custom_employment_section",
                "label": "Driver Details",
                "fieldtype": "Section Break",
                "insert_after": "naming_series",
            },
        )
    else:
        cf = frappe.get_doc("Custom Field", "Driver-custom_employment_section")
        cf.label = "Driver Details"
        cf.save(ignore_permissions=True)

    if not frappe.db.exists("Custom Field", "Driver-custom_col_break_emp"):
        create_custom_field(
            "Driver",
            {
                "fieldname": "custom_col_break_emp",
                "fieldtype": "Column Break",
                "insert_after": "custom_company",
            },
        )

    # 3. Pin the full, correct field order and save through the ORM so the
    # auto-export-fixtures-on-change hook actually fires this time.
    final_order = [
        "custom_demo_tag",
        "naming_series",
        "custom_employment_section",
        "full_name",
        "status",
        "transporter",
        "disabled",
        "custom_company",
        "custom_col_break_emp",
        "custom_branch",
        "cell_number",
        "custom_ctc",
        "column_break_2",
        "employee",
        "address",
        "user",
        "address_section",
        "current_address",
        "current_accommodation_type",
        "address_column_break",
        "permanent_address",
        "permanent_accommodation_type",
        "license_details",
        "license_number",
        "column_break_8",
        "issuing_date",
        "column_break_10",
        "expiry_date",
        "driving_license_categories",
        "driving_license_category",
        "next_of_kin_section",
        "next_of_kin",
        "nok_col_break_1",
        "nok_name",
        "nok_col_break_2",
        "nok_mobile",
        "bank_details_section",
        "bank_name",
        "bank_col_break_1",
        "bank_account_no",
        "bank_col_break_2",
        "bank_ifsc_code",
    ]

    fo_name = "Driver-main-field_order"
    if frappe.db.exists("Property Setter", fo_name):
        ps = frappe.get_doc("Property Setter", fo_name)
        ps.value = json.dumps(final_order)
        ps.save(ignore_permissions=True)
    else:
        from frappe.custom.doctype.property_setter.property_setter import make_property_setter

        make_property_setter(
            "Driver", None, "field_order", json.dumps(final_order), "Data", for_doctype=True
        )

    frappe.clear_cache(doctype="Driver")
    frappe.db.commit()
