# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, date_diff, flt, getdate


class TyreExpenses(Document):
	def validate(self):
		self._calc_child_warranty_expiry()
		self._sync_warranty_expiry()
		self._calc_total_cost()
		self._validate_odometers()
		self._validate_removal_dates()
		self._calc_km_run()
		self._calc_cost_per_km()
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

	# ── Stock issue (In Stock Use) ───────────────────────────────────────
	def _validate_stock_use_mandatory(self):
		if not self.warehouse:
			frappe.throw(_("Issue From Warehouse is mandatory for In Stock Use entries."))
		for row in self.tyre_details or []:
			if not row.tyre_item:
				frappe.throw(_("Row {0}: Tyre Item is mandatory for In Stock Use entries.").format(row.idx))

	def _tyre_item_quantities(self):
		# One tyre_details row = one physical tyre = qty 1 of its item, but two
		# rows can share the same tyre_item (e.g. two tyres of the same model
		# replaced together) — combine those into a single qty before touching
		# stock, so the resulting Stock Entry/ledger has one line/row per item
		# instead of N duplicate qty=1 rows for the same item+warehouse+voucher.
		quantities = {}
		for row in self.tyre_details or []:
			quantities[row.tyre_item] = quantities.get(row.tyre_item, 0) + 1
		return quantities

	def _validate_bin_availability(self):
		if self.stock_entry:
			# Already issued for this record; availability was already validated at issue time.
			return
		for item_code, qty in self._tyre_item_quantities().items():
			available = frappe.db.get_value(
				"Bin", {"item_code": item_code, "warehouse": self.warehouse}, "actual_qty"
			) or 0
			if available < qty:
				frappe.throw(_("Not enough stock for {0} in {1}: need {2}, have {3}.").format(
					item_code, self.warehouse, qty, available
				))

	def _create_stock_issue_entry(self):
		# Fresh DB read (not self.stock_entry) guards against a stale in-memory
		# copy re-triggering a second deduction on a rapid double-save.
		existing = frappe.db.get_value("Tyre Expenses", self.name, "stock_entry")
		if existing:
			return
		if not self.tyre_details:
			return

		savepoint = f"tyre_stock_issue_{frappe.generate_hash(length=8)}"
		frappe.db.savepoint(savepoint)
		try:
			items = []
			for item_code, qty in self._tyre_item_quantities().items():
				available = frappe.db.get_value(
					"Bin", {"item_code": item_code, "warehouse": self.warehouse}, "actual_qty"
				) or 0
				if available < qty:
					frappe.throw(_("Not enough stock for {0} in {1}: need {2}, have {3}.").format(
						item_code, self.warehouse, qty, available
					))
				stock_uom = frappe.db.get_value("Item", item_code, "stock_uom")
				items.append({
					"item_code": item_code,
					"s_warehouse": self.warehouse,
					"qty": qty,
					"uom": stock_uom,
				})

			company = frappe.db.get_value("Warehouse", self.warehouse, "company")

			se = frappe.get_doc({
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Issue",
				"purpose": "Material Issue",
				"company": company,
				"items": items,
				"remarks": _("Auto-created from Tyre Expenses {0} (In Stock Use)").format(self.name),
			})
			se.flags.ignore_permissions = True
			se.insert()
			se.submit()

			frappe.db.set_value("Tyre Expenses", self.name, "stock_entry", se.name)
			self.db_set("stock_entry", se.name, update_modified=False)
		except Exception:
			frappe.db.rollback(save_point=savepoint)
			frappe.log_error(frappe.get_traceback(), "Tyre Expenses stock issue failed")
			frappe.throw(_("Could not deduct tyre stock: {0}").format(frappe.get_traceback(0)))

	def _validate_reference_no_unique(self):
		if not self.reference_no:
			return
		duplicate = frappe.db.get_value(
			"Tyre Expenses",
			{"reference_no": self.reference_no, "name": ("!=", self.name or "")},
			"name",
		)
		if duplicate:
			frappe.throw(_("Reference No. {0} already used in {1}.").format(self.reference_no, duplicate))

	# ── Child table: auto-fill warranty expiry per row ───────────────────
	def _calc_child_warranty_expiry(self):
		for row in self.tyre_details or []:
			if self.purchase_date and row.warranty_months and row.warranty_months > 0:
				row.warranty_expiry = add_months(self.purchase_date, row.warranty_months)
			else:
				row.warranty_expiry = None

	# ── Parent-level mirror: earliest warranty expiry across all tyres ────
	# Drives the list-view alert indicator (see tms_alerts.js) the same way
	# Battery Expenses/Compliances/Vehicle Finance use a plain parent field.
	def _sync_warranty_expiry(self):
		dates = [row.warranty_expiry for row in self.tyre_details or [] if row.warranty_expiry]
		self.warranty_expiry = min(dates) if dates else None

	# ── Total cost = sum of all child purchase_cost ──────────────────────
	def _calc_total_cost(self):
		self.total_qty = len(self.tyre_details or [])
		self.total_cost = sum(flt(r.purchase_cost) for r in self.tyre_details or [])

	# ── Odometer validations ─────────────────────────────────────────────
	def _validate_odometers(self):
		removal_odo = self._parse_int_field("removal_odometer")
		fitment_odo = self.fitment_odometer or 0

		if fitment_odo < 0:
			frappe.throw(_("Fitment Odometer cannot be negative."))

		if removal_odo is not None and removal_odo < 0:
			frappe.throw(_("Removal Odometer cannot be negative."))

		if removal_odo and fitment_odo and removal_odo <= fitment_odo:
			frappe.throw(
				_("Removal Odometer ({0} km) must be greater than Fitment Odometer ({1} km).").format(
					removal_odo, fitment_odo
				)
			)

	# ── Removal date validations ─────────────────────────────────────────
	def _validate_removal_dates(self):
		if self.removal_date and self.purchase_date:
			if getdate(self.removal_date) < getdate(self.purchase_date):
				frappe.throw(_("Removal Date cannot be before Purchase Date."))

	# ── Auto-calculations ────────────────────────────────────────────────
	def _parse_int_field(self, fieldname):
		val = self.get(fieldname)
		if not val:
			return None
		try:
			return int(str(val).replace(",", "").strip())
		except (ValueError, TypeError):
			frappe.throw(_("Invalid numeric value for {0}: {1}").format(fieldname, val))

	def _calc_km_run(self):
		removal_odo = self._parse_int_field("removal_odometer")
		fitment_odo = self.fitment_odometer or 0
		if removal_odo and fitment_odo and removal_odo > fitment_odo:
			self.km_run = removal_odo - fitment_odo
		else:
			self.km_run = None

	def _calc_cost_per_km(self):
		if self.total_cost and self.km_run and self.km_run > 0:
			self.cost_per_km = flt(self.total_cost / self.km_run, 2)
		else:
			self.cost_per_km = None
