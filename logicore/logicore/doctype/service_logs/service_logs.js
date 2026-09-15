// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

function calc_totals(frm) {
	let total_qty = 0, total_amount = 0;
	get_rows(frm).forEach(row => {
		total_qty += row.qty || 0;
		total_amount += row.amount || 0;
	});
	frm.set_value("total_qty", total_qty);
	frm.set_value("total_amount", total_amount);
	frm.refresh_fields(["total_qty", "total_amount"]);
}

function set_if_changed(frm, fieldname, value) {
	const current = frm.doc[fieldname] ?? null;
	const next = value ?? null;
	if (current !== next) {
		frm.set_value(fieldname, next);
	}
}

function fetch_last_service_header(frm) {
	if (!frm.doc.vehicle_no) {
		set_if_changed(frm, "last_service_date", null);
		set_if_changed(frm, "last_service_km", 0);
		return;
	}
	frappe.call({
		method: "logicore.logicore.doctype.service_logs.service_logs.get_last_service_info",
		args: {
			vehicle_no: frm.doc.vehicle_no,
			current_name: frm.doc.name || null,
			current_voucher_date: frm.doc.voucher_date || null,
		},
		callback(r) {
			const d = r.message || {};
			set_if_changed(frm, "last_service_date", d.voucher_date || null);
			set_if_changed(frm, "last_service_km", d.km || 0);
		},
	});
}

function fetch_last_service_item(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	if (!frm.doc.vehicle_no || !row.service_replacement) {
		frappe.model.set_value(cdt, cdn, "last_date", null);
		frappe.model.set_value(cdt, cdn, "last_km", 0);
		return;
	}
	frappe.call({
		method: "logicore.logicore.doctype.service_logs.service_logs.get_last_service_item_info",
		args: {
			vehicle_no: frm.doc.vehicle_no,
			service_replacement: row.service_replacement,
			current_name: frm.doc.name || null,
			current_voucher_date: frm.doc.voucher_date || null,
		},
		callback(r) {
			const d = r.message || {};
			frappe.model.set_value(cdt, cdn, "last_date", d.voucher_date || null);
			frappe.model.set_value(cdt, cdn, "last_km", d.km || 0);
		},
	});
}

frappe.ui.form.on("Service Logs", {
	setup(frm) {
		frm.set_query("bank_name", () => ({
			filters: { group: frm.doc.payment_mode === "Cash" ? "CASH" : "BANK" }
		}));
		frm.set_query("service_replacement", "service_replacement_item", () => ({
			filters: { group: "EXPENSE-SERVICE" }
		}));
	},

	refresh(frm) {
		attach_delete_totals_handler(frm);
		if (frm.doc.vehicle_no && !frm.doc.__islocal) {
			fetch_last_service_header(frm);
		}
	},

	vehicle_no(frm) {
		fetch_last_service_header(frm);
		// refresh last_date/last_km for all existing grid rows
		(frm.doc.service_replacement_item || []).forEach(row => {
			fetch_last_service_item(frm, row.doctype, row.name);
		});
	},

	payment_mode(frm) {
		frm.set_value("bank_name", null);
	},

	after_save(frm){
        setTimeout(()=>{
            frappe.set_route("List", "Service Logs");
        },500);
    }
});

frappe.ui.form.on("Service  Replacement Item", {
	service_replacement(frm, cdt, cdn) {
		fetch_last_service_item(frm, cdt, cdn);
	},
	qty(frm) { calc_totals(frm); },
	amount(frm) { calc_totals(frm); },
	service_replacement_item_remove(frm) { calc_totals(frm); },
	service_replacement_item_delete(frm) { calc_totals(frm); },
});

function get_rows(frm) {
	return frm.fields_dict?.service_replacement_item?.grid?.get_data?.() || frm.doc.service_replacement_item || [];
}

function attach_delete_totals_handler(frm) {
	const grid = frm.fields_dict?.service_replacement_item?.grid;
	if (!grid?.wrapper) return;

	grid.wrapper.off("click.service_logs_totals");
	grid.wrapper.on("click.service_logs_totals", ".grid-remove-rows, .grid-remove-all-rows", () => {
		window.setTimeout(() => calc_totals(frm), 100);
	});
}
