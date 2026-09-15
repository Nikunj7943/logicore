# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, date_diff, getdate, nowdate


class BatteryExpenses(Document):

    def validate(self):
        self._validate_mandatory()
        self._validate_dates()
        self._calc_warranty_expiry()
        self._calc_actual_life()
        self._update_warranty_status()
        self._validate_reference_no_unique()
        if self.entry_type == "In Stock Use":
            self._validate_stock_use_mandatory()
            self._validate_bin_availability()

    def on_submit(self):
        if self.entry_type == "In Stock Use" and not self.stock_entry:
            self._create_stock_issue_entry()

    def on_cancel(self):
        self._cancel_linked_stock_entry()

    def on_trash(self):
        # Only reachable for Draft (never deducted) or already-Cancelled
        # (already reversed by on_cancel) records — Frappe blocks deleting a
        # Submitted document outright — but kept as a defensive fallback.
        self._cancel_linked_stock_entry()

    def _cancel_linked_stock_entry(self):
        if self.stock_entry and frappe.db.exists("Stock Entry", self.stock_entry):
            se = frappe.get_doc("Stock Entry", self.stock_entry)
            if se.docstatus == 1:
                try:
                    se.flags.ignore_permissions = True
                    se.cancel()
                except Exception:
                    frappe.throw(
                        _("Cannot cancel/delete: linked Stock Entry {0} could not be cancelled. {1}").format(
                            self.stock_entry, frappe.get_traceback(0)
                        )
                    )

    # ── Stock issue (In Stock Use) ─────────────────────────────────────────────
    def _validate_stock_use_mandatory(self):
        required = {"battery_item": "Battery Item", "warehouse": "Issue From Warehouse"}
        for fieldname, label in required.items():
            if not self.get(fieldname):
                frappe.throw(_("{0} is mandatory for In Stock Use entries.").format(label))

    def _validate_bin_availability(self):
        if self.stock_entry:
            # Already issued for this record; availability was already validated at issue time.
            return
        available = frappe.db.get_value(
            "Bin", {"item_code": self.battery_item, "warehouse": self.warehouse}, "actual_qty"
        ) or 0
        if available <= 0:
            frappe.throw(_("No available stock for {0} in {1}.").format(self.battery_item, self.warehouse))

    def _create_stock_issue_entry(self):
        # Fresh DB read (not self.stock_entry) guards against a stale in-memory
        # copy re-triggering a second deduction on a rapid double-save.
        existing = frappe.db.get_value("Battery Expenses", self.name, "stock_entry")
        if existing:
            return

        savepoint = f"battery_stock_issue_{frappe.generate_hash(length=8)}"
        frappe.db.savepoint(savepoint)
        try:
            available = frappe.db.get_value(
                "Bin", {"item_code": self.battery_item, "warehouse": self.warehouse}, "actual_qty"
            ) or 0
            if available <= 0:
                frappe.throw(_("No available stock for {0} in {1}.").format(self.battery_item, self.warehouse))

            company = frappe.db.get_value("Warehouse", self.warehouse, "company")
            stock_uom = frappe.db.get_value("Item", self.battery_item, "stock_uom")

            se = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Material Issue",
                "purpose": "Material Issue",
                "company": company,
                "items": [{
                    "item_code": self.battery_item,
                    "s_warehouse": self.warehouse,
                    "qty": 1,
                    "uom": stock_uom,
                }],
                "remarks": _("Auto-created from Battery Expenses {0} (In Stock Use)").format(self.name),
            })
            se.flags.ignore_permissions = True
            se.insert()
            se.submit()

            frappe.db.set_value("Battery Expenses", self.name, "stock_entry", se.name)
            self.db_set("stock_entry", se.name, update_modified=False)
        except Exception:
            frappe.db.rollback(save_point=savepoint)
            frappe.log_error(frappe.get_traceback(), "Battery Expenses stock issue failed")
            frappe.throw(_("Could not deduct battery stock: {0}").format(frappe.get_traceback(0)))

    def _validate_reference_no_unique(self):
        if not self.reference_no:
            return
        duplicate = frappe.db.get_value(
            "Battery Expenses",
            {"reference_no": self.reference_no, "name": ("!=", self.name or "")},
            "name",
        )
        if duplicate:
            frappe.throw(_("Reference No. {0} already used in {1}.").format(self.reference_no, duplicate))

    # ── Mandatory check (belt-and-suspenders over JSON reqd) ──────────────────
    def _validate_mandatory(self):
        required = {
            "vehicle_id": "Vehicle",
            "brand": "Brand",
            "battery_regn_no": "Battery Registration No.",
            "purchase_date": "Purchase / Installation Date",
            "installation_date": "Installation Date",
        }
        for fieldname, label in required.items():
            if not self.get(fieldname):
                frappe.throw(_("{0} is mandatory.").format(label))

    # ── Date logic ────────────────────────────────────────────────────────────
    def _validate_dates(self):
        if self.installation_date and self.purchase_date:
            if getdate(self.installation_date) < getdate(self.purchase_date):
                frappe.throw(
                    _("Installation Date ({0}) cannot be before Purchase Date ({1}).").format(
                        self.installation_date, self.purchase_date
                    )
                )

        if self.replacement_date and self.installation_date:
            if getdate(self.replacement_date) <= getdate(self.installation_date):
                frappe.throw(
                    _("Replacement Date ({0}) must be after Installation Date ({1}).").format(
                        self.replacement_date, self.installation_date
                    )
                )

        if self.purchase_date and getdate(self.purchase_date) > getdate(nowdate()):
            frappe.throw(_("Purchase Date cannot be a future date."))

    def _calc_warranty_expiry(self):
        if self.purchase_date and self.warranty_months and int(self.warranty_months) > 0:
            self.warranty_expiry_date = add_months(self.purchase_date, int(self.warranty_months))
        else:
            self.warranty_expiry_date = None

    def _calc_actual_life(self):
        if not self.installation_date:
            self.actual_life_achieved = ""
            return

        today = getdate(nowdate())
        replaced = getdate(self.replacement_date) if self.replacement_date else None

        # If replacement date is future or not set → battery still active
        is_active = not replaced or replaced > today
        end_date = today if is_active else replaced

        days = date_diff(end_date, self.installation_date)
        months = days // 30
        rem = days % 30
        suffix = " (Active)" if is_active else ""
        self.actual_life_achieved = f"{months} month(s) {rem} day(s){suffix}"

    def _update_warranty_status(self):
        today = getdate(nowdate())
        replaced = getdate(self.replacement_date) if self.replacement_date else None

        # Battery physically replaced (past date) → warranty no longer applicable
        if replaced and replaced <= today:
            self.warranty_status = "No Warranty"
            return

        if not self.warranty_expiry_date or not self.warranty_months:
            self.warranty_status = "No Warranty"
        elif getdate(self.warranty_expiry_date) >= today:
            self.warranty_status = "Under Warranty"
        else:
            self.warranty_status = "Expired"
