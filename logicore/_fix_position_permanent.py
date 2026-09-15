import frappe
import json

BLOCK = [
    "tms_payment_section", "custom_invoice_amount", "column_break_tms_payment_0",
    "custom_payment_status", "column_break_tms_payment", "custom_balance_amount",
    "column_break_tms_payment_2", "custom_total_paid", "column_break_tms_payment_3",
    "payment_history_html",
]


def run():
    # Fix each custom field's OWN stored insert_after so future Custom Field
    # creation (which regenerates field_order from these chains) doesn't
    # silently move this whole block back to its original position again.
    anchor = "supplied_items"
    for fieldname in BLOCK:
        cf_name = f"Purchase Invoice-{fieldname}"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.db.set_value("Custom Field", cf_name, "insert_after", anchor)
            anchor = fieldname

    ps_name = frappe.db.get_value(
        "Property Setter",
        {"doc_type": "Purchase Invoice", "property": "field_order"},
        "name",
    )
    ps = frappe.get_doc("Property Setter", ps_name)
    fo = json.loads(ps.value)

    for f in BLOCK:
        fo.remove(f)

    idx = fo.index("payments_tab")
    for i, f in enumerate(BLOCK):
        fo.insert(idx + i, f)

    ps.value = json.dumps(fo)
    ps.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache(doctype="Purchase Invoice")

    meta = frappe.get_meta("Purchase Invoice")
    fresh_fo = [f.fieldname for f in meta.fields]
    idx2 = fresh_fo.index("tms_payment_section")
    print(fresh_fo[idx2-2:idx2+12])
