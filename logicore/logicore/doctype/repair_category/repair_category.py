from frappe.model.document import Document

from logicore.utils.renaming import apply_pending_rename, capture_rename_target


class RepairCategory(Document):
    def before_save(self):
        capture_rename_target(self, "category_name")

    def on_update(self):
        apply_pending_rename(self)
