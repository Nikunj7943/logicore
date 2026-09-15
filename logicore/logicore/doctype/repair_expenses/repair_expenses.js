// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Repair Expenses", {
	setup(frm) {
		frm.set_query("vehicle_id", () => ({}));
		frm.set_query("vendor", () => ({
			filters: { supplier_group: "Vendor" }
		}));
		frm.set_query("bank_name", () => ({
			filters: { group: frm.doc.payment_mode === "Cash" ? "CASH" : "BANK" }
		}));

		frm.set_query("repair_sub_category", "repair_items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			if (!row.repair_category) return {};
			return { filters: { repair_category: row.repair_category } };
		});
		frm.set_query("repair_item", "repair_items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			if (!row.repair_sub_category) return {};
			return { filters: { repair_sub_category: row.repair_sub_category } };
		});
	},

	refresh(frm) {
		attach_delete_totals_handler(frm);
		set_status_indicator(frm);
		calculate_total(frm);

		if (!frm.is_new()) {
			frm.add_custom_button(__("Mark as Paid"), () => {
				frm.set_value("status", "Paid");
				frm.save();
			}, frm.doc.status !== "Paid" ? null : false);

			frm.add_custom_button(__("Cancel Entry"), () => {
				frappe.confirm(
					__("Are you sure you want to cancel this repair entry?"),
					() => { frm.set_value("status", "Cancelled"); frm.save(); }
				);
			}, frm.doc.status === "Cancelled" ? false : null);
		}

		// Pre-fill quick entry defaults when grid cell is focused — use namespace to prevent accumulation
		frm.fields_dict.repair_items.grid.wrapper
			.off("focusin.repair_defaults")
			.on("focusin.repair_defaults", "[data-fieldname='repair_sub_category'] input", function () {
				const row = (frm.doc.repair_items || [])[parseInt($(this).closest(".grid-row").attr("data-idx")) - 1];
				if (row) _set_sub_category_defaults(row);
			})
			.on("focusin.repair_defaults", "[data-fieldname='repair_item'] input", function () {
				const row = (frm.doc.repair_items || [])[parseInt($(this).closest(".grid-row").attr("data-idx")) - 1];
				if (row) _set_item_defaults(row);
			});
	},

	after_save(frm) {
		setTimeout(() => {
			frappe.set_route("List", "Repair Expenses");
		}, 500);
	},

	onload(frm) {
		if (frm.is_new()) {
			frm.set_value("date", frappe.datetime.get_today());
			frm.set_value("status", "Pending");
		}
	},

	status(frm) {
		set_status_indicator(frm);
	},

	payment_mode(frm) {
		frm.set_value("bank_name", null);
		if (!frm.doc.payment_mode) {
			frm.set_value("reference_no", null);
			frm.set_value("upi_id", null);
		}
	},
});

frappe.ui.form.on("Repair Expense Item", {
	repair_category(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "repair_sub_category", null);
		frappe.model.set_value(cdt, cdn, "repair_item", null);
		_set_sub_category_defaults(row);
	},
	repair_sub_category(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "repair_item", null);
		_set_item_defaults(row);
	},
	qty(frm, cdt, cdn) {
		calc_row_amount(frm, cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		calc_row_amount(frm, cdt, cdn);
	},
	repair_items_remove(frm) {
		calculate_total(frm);
	},
	repair_items_delete(frm) {
		calculate_total(frm);
	},
});

function calc_row_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const amount = flt(row.qty) * flt(row.rate);
	frappe.model.set_value(cdt, cdn, "amount", amount);
	calculate_total(frm);
}

function calculate_total(frm) {
	const rows = get_rows(frm);
	const total_qty = rows.reduce((s, r) => s + flt(r.qty), 0);
	const total = rows.reduce((s, r) => s + flt(r.amount), 0);
	frm.set_value("total_qty", total_qty);
	frm.set_value("amount", total);
	render_amount_badge(frm);
	frm.refresh_fields(["total_qty", "amount"]);
}

function get_rows(frm) {
	return frm.fields_dict?.repair_items?.grid?.get_data?.() || frm.doc.repair_items || [];
}

function attach_delete_totals_handler(frm) {
	const grid = frm.fields_dict?.repair_items?.grid;
	if (!grid?.wrapper) return;

	grid.wrapper.off("click.repair_totals");
	grid.wrapper.on("click.repair_totals", ".grid-remove-rows, .grid-remove-all-rows", () => {
		window.setTimeout(() => calculate_total(frm), 100);
	});
}

function set_status_indicator(frm) {
	const map = { "Pending": "orange", "Paid": "green", "Cancelled": "red" };
	frm.page.set_indicator(__(frm.doc.status || "Pending"), map[frm.doc.status] || "grey");
}

function render_amount_badge(frm) {
	frm.set_intro("");
	if (!frm.doc.amount) return;
	const formatted = format_inr(frm.doc.amount);
	frm.set_intro(
		`<span style="font-size:15px;font-weight:600;color:#2e7d32;">Total Amount: ${formatted}</span>`,
		"blue"
	);
}

function format_inr(value) {
	if (!value) return "₹0";
	if (value >= 10000000) return `₹${(value / 10000000).toFixed(2)} Cr`;
	if (value >= 100000)   return `₹${(value / 100000).toFixed(2)} L`;
	return "₹" + Number(value).toLocaleString("en-IN");
}

function _set_sub_category_defaults(row) {
	frappe.model.with_doctype("Repair Sub Category", () => {
		const f = frappe.meta.get_docfield("Repair Sub Category", "repair_category");
		if (f) f.default = row.repair_category || "";
	});
}

function _set_item_defaults(row) {
	frappe.model.with_doctype("Repair Item", () => {
		const fc = frappe.meta.get_docfield("Repair Item", "repair_category");
		if (fc) fc.default = row.repair_category || "";
		const fs = frappe.meta.get_docfield("Repair Item", "repair_sub_category");
		if (fs) fs.default = row.repair_sub_category || "";
	});
}
