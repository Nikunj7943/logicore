import json

import frappe


def execute():
    # Two earlier patches (move_driver_basic_fields_into_driver_details,
    # move_driver_details_section_to_top) wrote directly to the field_order
    # Property Setter via frappe.db.set_value, which skips doc_events -- so
    # the app's auto-export-fixtures-on-change hook never fired, and the
    # checked-in fixture file (custom/driver.json) stayed on the old order.
    # A later `bench migrate` re-imported that stale fixture and reverted
    # both the section move and its label back. Re-apply the intended final
    # order directly (idempotent regardless of current state) as the fix.
    fo_name = "Driver-main-field_order"
    final_order = [
        "custom_demo_tag",
        "naming_series",
        "custom_employment_section",
        "full_name",
        "status",
        "transporter",
        "custom_company",
        "custom_col_break_emp",
        "custom_branch",
        "cell_number",
        "custom_ctc",
        "column_break_2",
        "employee",
        "address",
        "user",
        "license_details",
        "license_number",
        "column_break_8",
        "issuing_date",
        "column_break_10",
        "expiry_date",
        "driving_license_categories",
        "driving_license_category",
    ]
    if frappe.db.exists("Property Setter", fo_name):
        frappe.db.set_value("Property Setter", fo_name, "value", json.dumps(final_order))

    section_field = "Driver-custom_employment_section"
    if frappe.db.exists("Custom Field", section_field):
        frappe.db.set_value("Custom Field", section_field, "label", "Driver Details")

    frappe.clear_cache(doctype="Driver")
    frappe.db.commit()
