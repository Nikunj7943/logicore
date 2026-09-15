import json

import frappe


def execute():
    # Move the whole "Driver Details" section block (heading + its fields) to
    # right after naming_series, i.e. the very top of the form, and pull
    # Cellphone Number + Per Month Salary into that section as well.
    fo_name = "Driver-main-field_order"
    value = frappe.db.get_value("Property Setter", fo_name, "value")
    if not value:
        return
    order = json.loads(value)

    block = [
        "custom_employment_section",
        "full_name",
        "status",
        "transporter",
        "custom_company",
        "custom_col_break_emp",
        "custom_branch",
    ]
    extra_fields = ["cell_number", "custom_ctc"]

    for fieldname in block + extra_fields:
        if fieldname in order:
            order.remove(fieldname)

    new_block = block + extra_fields

    anchor = "naming_series"
    idx = order.index(anchor) + 1 if anchor in order else 0

    for offset, fieldname in enumerate(new_block):
        order.insert(idx + offset, fieldname)

    frappe.db.set_value("Property Setter", fo_name, "value", json.dumps(order))
    frappe.clear_cache(doctype="Driver")
