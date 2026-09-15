// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tyre Expenses", {
	setup(frm) {
		frm.set_query("bank_name", () => ({
			filters: { group: frm.doc.payment_mode === "Cash" ? "CASH" : "BANK" }
		}));
		frm.set_query("warehouse", () => ({
			filters: { is_group: 0 }
		}));
		frm.set_query("tyre_item", "tyre_details", () => ({
			filters: { item_group: "Tyre", is_stock_item: 1, disabled: 0 }
		}));
	},

	payment_mode(frm) {
		frm.set_value("bank_name", null);
	},

	entry_type(frm) {
		if (frm.doc.entry_type === "New Purchase" && frm.doc.stock_entry) {
			frappe.msgprint(
				__("Stock has already been issued via {0}. Entry Type cannot be changed.", [frm.doc.stock_entry])
			);
			frm.set_value("entry_type", "In Stock Use");
			return;
		}

		if (frm.doc.entry_type === "In Stock Use") {
			["vendor", "vendor_ref_no", "payment_mode", "bank_name", "reference_no", "upi_id", "payment_date"]
				.forEach(f => frm.set_value(f, null));
			(frm.doc.tyre_details || []).forEach(row => {
				frappe.model.set_value(row.doctype, row.name, "purchase_cost", null);
			});
			_set_default_warehouse(frm);
		} else {
			frm.set_value("warehouse", null);
			(frm.doc.tyre_details || []).forEach(row => {
				frappe.model.set_value(row.doctype, row.name, "tyre_item", null);
			});
		}

		_toggle_tyre_stock_columns(frm);
	},

	refresh(frm) {
		attach_delete_totals_handler(frm);
		frm.trigger("set_status_indicator");
		frm.trigger("toggle_removal_fields");
		frm.trigger("calc_total_cost");
		_toggle_tyre_stock_columns(frm);

		if (frm.doc.stock_entry) {
			frm.dashboard.add_indicator(__("Stock Issued: {0}", [frm.doc.stock_entry]), "blue");
			frm.add_custom_button(__("View Stock Entry"), () => {
				frappe.set_route("Form", "Stock Entry", frm.doc.stock_entry);
			});
		}
	},

	on_submit(frm) {
		setTimeout(() => {
			frappe.set_route("List", "Tyre Expenses");
		}, 500);
	},

	purchase_date(frm) {
		frm.trigger("recalc_all_warranty_expiry");
		frm.trigger("validate_date_order");
	},

	// ── Recalculate warranty expiry for all child rows when purchase_date changes
	recalc_all_warranty_expiry(frm) {
		(frm.doc.tyre_details || []).forEach((row, idx) => {
			_calc_row_warranty_expiry(frm, row);
		});
		frm.refresh_field("tyre_details");
	},

	// ── Total cost: sum all child purchase_cost ──────────────────────────
	calc_total_cost(frm) {
		const rows = get_rows(frm);
		frm.set_value("total_qty", rows.length);
		const total = rows.reduce((sum, row) => sum + flt(row.purchase_cost), 0);
		frm.set_value("total_cost", total);
		frm.refresh_fields(["total_qty", "total_cost"]);
	},

	// ── Odometer → km_run + cost_per_km ─────────────────────────────────
	fitment_odometer(frm) {
		frm.trigger("validate_odometer_order");
		frm.trigger("calc_km_run");
	},

	removal_odometer(frm) {
		frm.trigger("validate_odometer_order");
		frm.trigger("calc_km_run");
	},

	calc_km_run(frm) {
		const { fitment_odometer, removal_odometer } = frm.doc;
		if (fitment_odometer > 0 && removal_odometer > 0 && removal_odometer > fitment_odometer) {
			const km = removal_odometer - fitment_odometer;
			frm.set_value("km_run", km);
			frm.trigger("calc_cost_per_km");
		} else {
			frm.set_value("km_run", null);
			frm.set_value("cost_per_km", null);
		}
	},

	calc_cost_per_km(frm) {
		const { total_cost, km_run } = frm.doc;
		if (total_cost > 0 && km_run > 0) {
			frm.set_value("cost_per_km", flt(total_cost / km_run, 2));
		} else {
			frm.set_value("cost_per_km", null);
		}
	},

	// ── Removal section visibility ───────────────────────────────────────
	status(frm) {
		frm.trigger("toggle_removal_fields");
		frm.trigger("set_status_indicator");
	},

	toggle_removal_fields(frm) {
		const show = ["Removed", "Damaged", "Scrap"].includes(frm.doc.status);
		frm.toggle_display("section_removal_details", show);
		frm.toggle_reqd("removal_date", show);
		frm.toggle_reqd("removal_odometer", show);
		frm.toggle_reqd("removal_reason", show);
	},

	set_status_indicator(frm) {
		const map = { Active: "green", Removed: "red", Damaged: "orange", Scrap: "gray" };
		const color = map[frm.doc.status] || "blue";
		frm.page.set_indicator(frm.doc.status || "Draft", color);
	},

	// ── Date / odometer order validations ────────────────────────────────
	removal_date(frm) {
		frm.trigger("validate_date_order");
	},

	validate_date_order(frm) {
		const { purchase_date, removal_date } = frm.doc;
		if (removal_date && purchase_date && removal_date < purchase_date) {
			frappe.msgprint({
				title: __("Invalid Date"),
				indicator: "red",
				message: __("Removal Date cannot be before Purchase Date."),
			});
			frm.set_value("removal_date", null);
		}
	},

	validate_odometer_order(frm) {
		const { fitment_odometer, removal_odometer } = frm.doc;
		if (removal_odometer > 0 && fitment_odometer > 0 && removal_odometer <= fitment_odometer) {
			frappe.msgprint({
				title: __("Invalid Odometer"),
				indicator: "red",
				message: __("Removal Odometer must be greater than Fitment Odometer."),
			});
			frm.set_value("removal_odometer", null);
		}
	},
});

// ── Child table events ───────────────────────────────────────────────────────
frappe.ui.form.on("Tyre Expense Detail", {
	purchase_cost(frm) {
		frm.trigger("calc_total_cost");
	},

	tyre_details_remove(frm) {
		frm.trigger("calc_total_cost");
	},

	tyre_details_delete(frm) {
		frm.trigger("calc_total_cost");
	},

	warranty_months(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		_calc_row_warranty_expiry(frm, row);
		frm.refresh_field("tyre_details");
	},
});

function _calc_row_warranty_expiry(frm, row) {
	if (frm.doc.purchase_date && row.warranty_months > 0) {
		row.warranty_expiry = frappe.datetime.add_months(
			frm.doc.purchase_date,
			row.warranty_months
		);
	} else {
		row.warranty_expiry = null;
	}
}

// ── Grid column visibility for In Stock Use vs New Purchase ──────────────────
// set_column_disp mutates the shared frappe.meta docfield object directly,
// which setup_visible_columns() only re-reads if the grid's own visible-
// columns cache happens to get rebuilt at the right time — unreliable here
// (confirmed: hiding an already-visible column worked, but showing a column
// that starts hidden=1 in the doctype JSON never did). set_column_disp_in_list_view
// is the API actually built for this: it stores the override separately in
// column_disp_overrides and setup_fields() re-applies it fresh on every
// grid.refresh(), so it works the same way in both directions.
function _toggle_tyre_stock_columns(frm) {
	const grid = frm.fields_dict?.tyre_details?.grid;
	if (!grid) return;
	const in_stock_use = frm.doc.entry_type === "In Stock Use";
	grid.set_column_disp_in_list_view("tyre_item", in_stock_use);
	grid.set_column_disp_in_list_view("purchase_cost", !in_stock_use);
	grid.refresh();
}

// Pre-fill from Stock Settings' Default Warehouse — user can still change it.
function _set_default_warehouse(frm) {
	if (frm.doc.warehouse) return;
	frappe.db.get_single_value("Stock Settings", "default_warehouse").then(warehouse => {
		if (warehouse && !frm.doc.warehouse) {
			frm.set_value("warehouse", warehouse);
		}
	});
}

function get_rows(frm) {
	return frm.fields_dict?.tyre_details?.grid?.get_data?.() || frm.doc.tyre_details || [];
}

function attach_delete_totals_handler(frm) {
	const grid = frm.fields_dict?.tyre_details?.grid;
	if (!grid?.wrapper) return;

	grid.wrapper.off("click.tyre_totals");
	grid.wrapper.on("click.tyre_totals", ".grid-remove-rows, .grid-remove-all-rows", () => {
		window.setTimeout(() => frm.trigger("calc_total_cost"), 100);
	});
}
