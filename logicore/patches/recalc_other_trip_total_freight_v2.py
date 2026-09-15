import frappe
from frappe.utils import flt


def execute():
    # v2: case-insensitive fix — handles "Other", "OTHER", "other" etc.
    trips = frappe.db.sql(
        """SELECT name, customer_freight, brokerage_amount, lr_money,
                  tds_deducted_by_customer, total_trip_amount
           FROM `tabTrip` WHERE LOWER(TRIM(trip_type)) = 'other'""",
        as_dict=True,
    )
    for t in trips:
        correct = (
            flt(t.customer_freight) - flt(t.brokerage_amount)
            - flt(t.lr_money) - flt(t.tds_deducted_by_customer)
        )
        if flt(t.total_trip_amount) != correct:
            frappe.db.set_value("Trip", t.name, "total_trip_amount", correct,
                                update_modified=False)
    frappe.db.commit()
