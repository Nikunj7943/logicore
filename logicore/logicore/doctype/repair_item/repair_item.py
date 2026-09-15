import frappe
from frappe import _
from frappe.model.document import Document


class RepairItem(Document):
    def validate(self):
        count = frappe.db.sql("""
            SELECT COUNT(*) FROM `tabRepair Item`
            WHERE repair_category = %s
              AND repair_sub_category = %s
              AND item_name = %s
              AND name != %s
        """, (
            self.repair_category,
            self.repair_sub_category,
            self.item_name,
            self.name or "",
        ))[0][0]

        if count:
            frappe.throw(
                _("Repair Item <b>{0}</b> already exists under <b>{1}</b> → <b>{2}</b>.").format(
                    self.item_name, self.repair_category, self.repair_sub_category
                )
            )
