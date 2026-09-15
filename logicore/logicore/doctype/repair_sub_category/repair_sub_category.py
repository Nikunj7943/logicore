import frappe
from frappe import _
from frappe.model.document import Document


class RepairSubCategory(Document):
    def validate(self):
        count = frappe.db.sql("""
            SELECT COUNT(*) FROM `tabRepair Sub Category`
            WHERE repair_category = %s
              AND sub_category_name = %s
              AND name != %s
        """, (
            self.repair_category,
            self.sub_category_name,
            self.name or "",
        ))[0][0]

        if count:
            frappe.throw(
                _("Repair Sub Category <b>{0}</b> already exists under category <b>{1}</b>.").format(
                    self.sub_category_name, self.repair_category
                )
            )
