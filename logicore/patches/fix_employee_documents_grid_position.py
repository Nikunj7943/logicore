import json

import frappe


def execute():
    # create_custom_field's insert_after logic pushed our new Section Break
    # past the next Tab Break and landed it on the *next* Section Break it
    # found (the pre-existing "Next of Kind" section in the Profile tab)
    # instead of staying in Personal Details. Pin the exact position via the
    # field_order Property Setter instead of relying on insert_after.
    fo_name = "Employee-main-field_order"
    if not frappe.db.exists("Property Setter", fo_name):
        return
    ps = frappe.get_doc("Property Setter", fo_name)
    order = json.loads(ps.value)

    block = ["employee_documents_section", "employee_documents"]
    for fieldname in block:
        if fieldname in order:
            order.remove(fieldname)

    anchor = "custom_license_expiry_date"
    idx = order.index(anchor) + 1 if anchor in order else len(order)
    for offset, fieldname in enumerate(block):
        order.insert(idx + offset, fieldname)

    # Use save() (not db.set_value) so on_update hooks fire and this gets
    # auto-exported to the fixture file -- a raw db.set_value here would
    # silently drop out of sync with disk again, same as happened with
    # Driver-main-field_order earlier.
    ps.value = json.dumps(order)
    ps.save(ignore_permissions=True)
    frappe.clear_cache(doctype="Employee")
    frappe.db.commit()
