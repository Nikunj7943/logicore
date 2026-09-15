# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class FuelUreaExpenses(Document):
# 	pass
# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FuelUreaExpenses(Document):

    def before_insert(self):
        self._set_naming_series()

    def before_save(self):
        self._fetch_last_odometer()
        self._calc_distance()
        self._fetch_pending_partial_liters()
        self._calc_kpl()
        self._calc_incentive()

    def after_insert(self):
        # Rename to proper naming series after insert (suppress notification)
        new_name = self._generate_naming_series()
        if new_name and new_name != self.name:
            old_name = self.name
            # Clear any existing messages to suppress rename notification
            frappe.local.message_log = []
            frappe.rename_doc("Fuel Urea Expenses", old_name, new_name, merge=False)
            self.name = new_name

    def validate(self):
        self._validate_no_pending_draft()
        self._validate_fuelurea_lock()
        self._fetch_fixed_kpl_from_vehicle()
        self._fetch_last_odometer()
        self._validate_odometer()
        self._calc_distance()
        self._fetch_pending_partial_liters()
        self._calc_kpl()
        self._calc_incentive()
        self._validate_reference_no_unique()
        self._validate_driver_payment_reference_unique()
        if self.fuelurea == "Urea" and self.entry_type == "In Stock Use":
            self._validate_stock_use_mandatory()
            self._validate_bin_availability()

    def on_submit(self):
        if self.fuelurea == "Urea" and self.entry_type == "In Stock Use" and not self.stock_entry:
            self._create_stock_issue_entry()

    def on_cancel(self):
        self._cancel_linked_stock_entry()
        self._update_vehicle_odometer()

    def on_trash(self):
        # Only reachable for Draft (never deducted) or already-Cancelled
        # (already reversed by on_cancel) records — Frappe blocks deleting a
        # Submitted document outright — but kept as a defensive fallback.
        self._cancel_linked_stock_entry()

    # ── Stock issue (Urea In Stock Use) ──────────────────────────────────────
    def _validate_stock_use_mandatory(self):
        if not self.urea_item:
            frappe.throw(_("Urea Item is mandatory for In Stock Use entries."))
        if not self.warehouse:
            frappe.throw(_("Issue From Warehouse is mandatory for In Stock Use entries."))
        if not self.liters or float(self.liters) <= 0:
            frappe.throw(_("Fuel / Urea Liters must be greater than 0 for In Stock Use entries."))

    def _validate_bin_availability(self):
        if self.stock_entry:
            # Already issued for this record; availability was already validated at issue time.
            return
        available = frappe.db.get_value(
            "Bin", {"item_code": self.urea_item, "warehouse": self.warehouse}, "actual_qty"
        ) or 0
        if available < float(self.liters or 0):
            frappe.throw(_("Not enough stock for {0} in {1}: need {2}, have {3}.").format(
                self.urea_item, self.warehouse, self.liters, available
            ))

    def _create_stock_issue_entry(self):
        # Fresh DB read (not self.stock_entry) guards against a stale in-memory
        # copy re-triggering a second deduction on a rapid double-save.
        existing = frappe.db.get_value("Fuel Urea Expenses", self.name, "stock_entry")
        if existing:
            return

        savepoint = f"urea_stock_issue_{frappe.generate_hash(length=8)}"
        frappe.db.savepoint(savepoint)
        try:
            qty = float(self.liters or 0)
            available = frappe.db.get_value(
                "Bin", {"item_code": self.urea_item, "warehouse": self.warehouse}, "actual_qty"
            ) or 0
            if available < qty:
                frappe.throw(_("Not enough stock for {0} in {1}: need {2}, have {3}.").format(
                    self.urea_item, self.warehouse, qty, available
                ))

            company = frappe.db.get_value("Warehouse", self.warehouse, "company")
            stock_uom = frappe.db.get_value("Item", self.urea_item, "stock_uom")

            se = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Material Issue",
                "purpose": "Material Issue",
                "company": company,
                "items": [{
                    "item_code": self.urea_item,
                    "s_warehouse": self.warehouse,
                    "qty": qty,
                    "uom": stock_uom,
                }],
                "remarks": _("Auto-created from Fuel Urea Expenses {0} (In Stock Use)").format(self.name),
            })
            se.flags.ignore_permissions = True
            se.insert()
            se.submit()

            frappe.db.set_value("Fuel Urea Expenses", self.name, "stock_entry", se.name)
            self.db_set("stock_entry", se.name, update_modified=False)
        except Exception:
            frappe.db.rollback(save_point=savepoint)
            frappe.log_error(frappe.get_traceback(), "Fuel Urea Expenses stock issue failed")
            frappe.throw(_("Could not deduct urea stock: {0}").format(frappe.get_traceback(0)))

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

    def _validate_reference_no_unique(self):
        if not self.reference_no:
            return
        duplicate = frappe.db.get_value(
            "Fuel Urea Expenses",
            {"reference_no": self.reference_no, "name": ("!=", self.name or "")},
            "name",
        )
        if duplicate:
            frappe.throw(_("Reference No. {0} already used in {1}.").format(self.reference_no, duplicate))

    def _validate_driver_payment_reference_unique(self):
        if not self.driver_payment_reference:
            return
        duplicate = frappe.db.get_value(
            "Fuel Urea Expenses",
            {"driver_payment_reference": self.driver_payment_reference, "name": ("!=", self.name or "")},
            "name",
        )
        if duplicate:
            frappe.throw(_("Driver Payment Reference {0} already used in {1}.").format(self.driver_payment_reference, duplicate))

    def on_update(self):
        self._update_vehicle_odometer()

    def _update_vehicle_odometer(self):
        # Sirf Diesel/Petrol Top Up pe Vehicle.last_odometer update hoga
        # Partial Refill pe Vehicle.last_odometer KABHI update nahi hoga
        # Isse Vehicle.last_odometer hamesha last Top Up ka odometer rahega
        if not self.vehicle or self.fuelurea == "Urea":
            return
        if self.fill_type == "Partial Refill":
            return
        max_odo = frappe.db.sql(
            """SELECT MAX(current_odometer) FROM `tabFuel Urea Expenses`
               WHERE vehicle = %s AND fuelurea != 'Urea'
                 AND fill_type = 'Top Up (Full Tank)'
                 AND docstatus != 2""",
            self.vehicle
        )
        max_val = float((max_odo[0][0] or 0)) if max_odo else 0
        if max_val > 0:
            frappe.db.set_value(
                "Vehicle", self.vehicle, "last_odometer", max_val,
                update_modified=False
            )

    def _fetch_fixed_kpl_from_vehicle(self):
        if not self.vehicle or float(self.fixed_kpl or 0) > 0:
            return
        kpl = frappe.db.get_value("Vehicle", self.vehicle, "custom_fixed_kpl")
        if kpl:
            self.fixed_kpl = round(float(kpl), 2)

    def _fetch_last_odometer(self):
        # Top Up: last odometer = last Top Up (tank-to-tank cycle, unaffected by Partial Refills)
        # Partial Refill: last odometer = immediately previous entry, chahe wo Top Up ho ya Partial
        #                 (apna exclusive distance segment, na ki last-Top-Up-se-cumulative)
        if not self.vehicle or self.fuelurea == "Urea":
            return

        fill_type_filter = "AND fill_type = 'Top Up (Full Tank)'" if self.fill_type == "Top Up (Full Tank)" else ""
        result = frappe.db.sql(
            f"""SELECT MAX(current_odometer) FROM `tabFuel Urea Expenses`
                WHERE vehicle = %s AND fuelurea != 'Urea'
                  AND docstatus != 2
                  AND current_odometer < %s
                  AND name != %s
                  {fill_type_filter}""",
            (self.vehicle, float(self.current_odometer or 0), self.name or ""),
        )
        last_odo = float(result[0][0] or 0)
        if not last_odo:
            # No prior Fuel/Urea entry for this vehicle yet — fall back to the
            # baseline odometer recorded on the Vehicle master.
            last_odo = float(frappe.db.get_value("Vehicle", self.vehicle, "last_odometer") or 0)
        self.last_odoometer = last_odo

    def _fetch_pending_partial_liters(self):
        # Sirf Top Up (Full Tank) Diesel/Petrol entries pe kaam karta hai
        if self.fuelurea == "Urea" or self.fill_type != "Top Up (Full Tank)":
            self.partial_liters_carried = 0.0
            self.effective_liters = round(float(self.liters or 0), 2)
            return

        # self.last_odoometer = Vehicle.last_odometer = last Top Up ka odometer
        # (Partial Refill pe Vehicle.last_odometer update nahi hota)
        # Isliye last_topup_odo ke liye alag DB query ki zaroorat nahi
        last_topup_odo = float(self.last_odoometer or 0)

        # Un sabhi Partial Refill entries ka liters sum karo jo last Top Up aur current ke beech mein hain
        result = frappe.db.sql(
            """SELECT COALESCE(SUM(liters), 0) FROM `tabFuel Urea Expenses`
               WHERE vehicle = %s AND fuelurea != 'Urea'
                 AND fill_type = 'Partial Refill'
                 AND docstatus != 2
                 AND current_odometer > %s
                 AND current_odometer < %s
                 AND name != %s""",
            (self.vehicle, last_topup_odo, float(self.current_odometer or 0), self.name or "")
        )
        self.partial_liters_carried = round(float(result[0][0] or 0), 2)
        self.effective_liters = round(float(self.liters or 0) + self.partial_liters_carried, 2)

    # ── private helpers ──────────────────────────────────────────────────────

    def _set_naming_series(self):
        # Set name before insert
        new_name = self._generate_naming_series()
        if new_name:
            self.name = new_name

    def _generate_naming_series(self):
        # Generate the proper naming series based on fuel/urea type
        try:
            # Determine the base series from fuel/urea type
            base_series = "UREA" if self.fuelurea == "Urea" else "FUEL"

            from datetime import datetime
            year_suffix = datetime.now().strftime("%Y")

            # Build search pattern - format: "UREA-2026-"
            pattern = f"{base_series}-{year_suffix}-%"

            # Find the last document with this series in this year
            result = frappe.db.sql(
                """SELECT name FROM `tabFuel Urea Expenses`
                   WHERE name LIKE %s AND docstatus != 2
                   ORDER BY name DESC LIMIT 1""",
                (pattern,),
                as_dict=True
            )

            seq_num = 1
            if result:
                last_name = result[0]["name"]
                try:
                    # Extract sequence number from the name
                    # Format: "FUEL-2026-00005" → get "00005"
                    last_seq = int(last_name.split("-")[-1])
                    seq_num = last_seq + 1
                except (ValueError, IndexError, AttributeError):
                    seq_num = 1

            # Generate and return the new name in simpler format
            return f"{base_series}-{year_suffix}-{seq_num:05d}"

        except Exception as e:
            frappe.log_error(f"Error generating naming series: {str(e)}", "Fuel Urea Expenses")
            return None

    def _validate_fuelurea_lock(self):
        if self.is_new():
            return

        old_doc = frappe.get_doc("Fuel Urea Expenses", self.name)
        # Only lock if the OLD value was Urea (user cannot change Urea to Petrol/Diesel)
        if old_doc.fuelurea == "Urea" and old_doc.fuelurea != self.fuelurea:
            frappe.throw(_("Urea entries cannot be changed to another fuel type. Once saved as Urea, the fuel/urea type is locked."))

    def _validate_no_pending_draft(self):
        # Jab tak vehicle ki purani (earlier odometer wali) entry Draft mein padi hai,
        # tab tak usi fuel/urea group ki nayi entry save nahi hone deni
        # (Diesel/Petrol ek group hai, Urea alag group hai)
        if not self.vehicle or not self.current_odometer:
            return

        is_urea = self.fuelurea == "Urea"
        fuelurea_condition = "fuelurea = 'Urea'" if is_urea else "fuelurea != 'Urea'"

        pending = frappe.db.sql(
            f"""SELECT name FROM `tabFuel Urea Expenses`
                WHERE vehicle = %s AND {fuelurea_condition}
                  AND docstatus = 0
                  AND current_odometer < %s
                  AND name != %s
                ORDER BY current_odometer ASC
                LIMIT 1""",
            (self.vehicle, float(self.current_odometer or 0), self.name or ""),
        )
        if pending:
            pending_name = pending[0][0]
            pending_link = frappe.utils.get_link_to_form("Fuel Urea Expenses", pending_name)
            frappe.throw(
                _(
                    "The previous entry {0} for vehicle {1} is still in Draft (not Submitted). "
                    "Please Submit it first before saving a new Fuel/Urea entry for this vehicle."
                ).format(pending_link, self.vehicle)
            )

    def _validate_odometer(self):
        cur  = float(self.current_odometer or 0)
        last = float(self.last_odoometer   or 0)

        if cur <= 0:
            frappe.throw(_("Current Odometer must be greater than 0."))

        if last > 0 and cur <= last:
            frappe.throw(
                _("Current Odometer ({0} km) must be greater than Last Odometer ({1} km).").format(cur, last)
            )

    def _calc_distance(self):
        cur  = float(self.current_odometer or 0)
        last = float(self.last_odoometer   or 0)
        self.distance = round(cur - last, 2) if cur > last else 0.0

    def _calc_kpl(self):
        # Partial Refill bhi apna KPL dikhata hai (apne exclusive odometer segment se) —
        # sirf Excess/Short + Incentive Partial pe locked rehte hain, see _calc_incentive()
        eff_liters = float(self.effective_liters or self.liters or 0)
        dist       = float(self.distance or 0)
        self.kpl = round(dist / eff_liters, 2) if eff_liters > 0 else 0.0

    def _calc_incentive(self):
        if self.fill_type == "Partial Refill":
            self.excessshort_fuel = 0.0
            self.fuel_incentive   = 0.0
            return
        dist         = float(self.distance             or 0)
        actual_liters = float(self.effective_liters or self.liters or 0)  # includes partial refills carried
        fixed_kpl    = float(self.fixed_kpl            or 0)
        rate         = float(self.excessshort_fuel_rate or 0)

        if fixed_kpl > 0 and dist > 0:
            expected              = round(dist / fixed_kpl, 2)
            self.excessshort_fuel = round(expected - actual_liters, 2)
            self.fuel_incentive   = round(self.excessshort_fuel * rate, 2)
        else:
            self.excessshort_fuel = 0.0
            self.fuel_incentive   = 0.0


@frappe.whitelist()
def get_last_odometer(vehicle, fill_type, current_odometer=0, exclude_name=""):
    """Return the previous entry's odometer for live display.
    Top Up -> last Top Up. Partial Refill -> immediately previous entry (any type).
    current_odometer not yet known (0) -> latest entry overall, no upper bound
    (preview right after Vehicle/Fill Type is picked). Once known -> bounded to
    entries before it (correct even when backfilling an older-dated entry)."""
    fill_type_filter = "AND fill_type = 'Top Up (Full Tank)'" if fill_type == "Top Up (Full Tank)" else ""
    bound_filter = "AND current_odometer < %(current_odometer)s" if float(current_odometer or 0) > 0 else ""
    result = frappe.db.sql(
        f"""SELECT MAX(current_odometer) FROM `tabFuel Urea Expenses`
            WHERE vehicle = %(vehicle)s AND fuelurea != 'Urea'
              AND docstatus != 2
              AND name != %(exclude_name)s
              {bound_filter}
              {fill_type_filter}""",
        {
            "vehicle": vehicle,
            "current_odometer": float(current_odometer or 0),
            "exclude_name": exclude_name or "",
        },
    )
    last_odo = float(result[0][0] or 0)
    if not last_odo:
        # No prior Fuel/Urea entry for this vehicle yet — fall back to the
        # baseline odometer recorded on the Vehicle master.
        last_odo = float(frappe.db.get_value("Vehicle", vehicle, "last_odometer") or 0)
    return last_odo


@frappe.whitelist()
def get_partial_liters(vehicle, last_odoometer, current_odometer, exclude_name=""):
    """Return sum of Partial Refill liters for vehicle between last Top Up and current odometer.
    Called from JS form to show live partial_liters_carried before save."""
    result = frappe.db.sql(
        """SELECT COALESCE(SUM(liters), 0) FROM `tabFuel Urea Expenses`
           WHERE vehicle = %s AND fuelurea != 'Urea'
             AND fill_type = 'Partial Refill'
             AND docstatus != 2
             AND current_odometer > %s
             AND current_odometer < %s
             AND name != %s""",
        (vehicle, float(last_odoometer or 0), float(current_odometer or 0), exclude_name or "")
    )
    return float(result[0][0] or 0)


@frappe.whitelist()
def get_vehicle_fuel_history(vehicle, from_date=None, to_date=None, exclude_name=""):
    """Return submitted Fuel/Urea entries for a vehicle within a date range.
    Called from JS form to render the Fuel History panel below the form."""
    frappe.has_permission("Fuel Urea Expenses", "read", throw=True)

    if not vehicle:
        frappe.throw(_("Vehicle is required."))

    to_date = to_date or frappe.utils.today()
    from_date = from_date or frappe.utils.add_months(to_date, -1)

    filters = {
        "vehicle": vehicle,
        "docstatus": 1,
        "date": ["between", [from_date, to_date]],
    }
    if exclude_name:
        filters["name"] = ["!=", exclude_name]

    rows = frappe.db.get_all(
        "Fuel Urea Expenses",
        filters=filters,
        fields=[
            "name", "date", "vehicle", "fuelurea", "fill_type", "driver_id",
            "last_odoometer", "current_odometer", "distance",
            "kpl", "liters", "fuelurea_amount",
        ],
        order_by="date desc, creation desc",
    )

    driver_ids = {row.driver_id for row in rows if row.driver_id}
    driver_names = frappe.db.get_all(
        "Driver", filters={"name": ["in", list(driver_ids)]}, fields=["name", "full_name"]
    ) if driver_ids else []
    driver_name_map = {d.name: d.full_name for d in driver_names}

    for row in rows:
        row["driver_name"] = driver_name_map.get(row.driver_id, row.driver_id)

    return rows