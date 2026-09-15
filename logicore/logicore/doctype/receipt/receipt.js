frappe.ui.form.on("Receipt", {
	refresh(frm) {
		style_fetch_btn(frm);
		attach_delete_totals_handler(frm);
		recalc_totals(frm);

		frm.add_custom_button(__("Print Receipt"), function () {
			frappe.utils.print(frm.doctype, frm.docname, "Receipt TMS", frm.doc.language);
		}).addClass("btn-primary");
	},

	setup(frm) {
		frm.set_query("paid_from_account", () => ({
			filters: { group: frm.doc.mode_of_payment === "Cash" ? "CASH" : "BANK" }
		}));
	},

	receipt_type(frm) {
		if (frm.doc.receipt_type === "Other Receipt") {
			frm.set_value("total_brokerage_amount", 0);
			frm.set_value("total_lr_money", 0);
			frm.set_value("total_tds_amount", 0);
		}
	},

	mode_of_payment(frm) {
		frm.set_value("paid_from_account", null);
	},

	fetch_trips_btn(frm) {
		if (!frm.doc.customer) {
			frappe.msgprint(__("Please select a Customer first."));
			return;
		}
		if (!frm.doc.from_date || !frm.doc.to_date) {
			frappe.msgprint(__("Please select From Date and To Date."));
			return;
		}
		if (!frm.doc.trip_type) {
			frappe.msgprint(__("Please select a Trip Type first."));
			return;
		}

		frappe.call({
			method: "logicore.logicore.doctype.receipt.receipt.get_unreceived_trips",
			args: {
				customer: frm.doc.customer,
				from_date: frm.doc.from_date,
				to_date: frm.doc.to_date,
				company: frm.doc.company,
				trip_type: frm.doc.trip_type || null,
			},
			freeze: true,
			freeze_message: __("Fetching trips..."),
			callback(r) {
				if (!r.message || !r.message.length) {
					frappe.msgprint(__("No pending trips found for this customer and date range."));
					return;
				}

				frm.clear_table("trips");

				r.message.forEach((t) => {
					const row = frm.add_child("trips");
					const is_other_trip = (t.trip_type || "").trim().toUpperCase() === "OTHER";

					row.trip              = t.name;
					row.trip_date         = t.tcntrip_date;
					row.tcntrip_no        = t.tcntrip_no;
					row.lr_no             = t.lr_no;
					row.vehicle_no        = t.vehicle_no || t.vehicle_market;
					row.origin_city       = t.origin_city;
					row.destination_city  = t.destination_city_1;

					const net_balance     = flt(t.customer_balance_amount);
					const brokerage       = is_other_trip ? flt(t.brokerage_amount) : 0;
					const lr              = is_other_trip ? flt(t.lr_money) : 0;
					const tds             = flt(t.tds_deducted_by_customer);

					row.customer_freight      = flt(t.customer_freight);
					row.approved_addl_amount  = flt(t.total_approved_addl_amount);
					row.invoice_amount        = flt(t.net_invoice_amount);
					row.brokerage_amount      = brokerage;
					row.lr_money              = lr;
					row.tds_amount            = tds;
					row.balance               = net_balance;
					row.received_amount       = net_balance;
					row.payment_advice_no = t.payment_advice_no || "";
					row.utr_no            = t.utr_no || "";

					recalc_row(row);
				});

				frm.refresh_field("trips");
				recalc_totals(frm);

				frappe.show_alert(
					{ message: __("{0} trip(s) loaded.", [r.message.length]), indicator: "green" },
					3
				);
			},
		});
	},

	trips_remove(frm) {
		recalc_totals(frm);
	},

	trips_delete(frm) {
		recalc_totals(frm);
	},
});

frappe.ui.form.on("Customer Receipt Trip", {
	trip(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.trip) return;
		frappe.db.get_value("Trip", row.trip, ["vehicle_no", "vehicle_market"]).then((r) => {
			const vehicle_no = (r.message && (r.message.vehicle_no || r.message.vehicle_market)) || "";
			frappe.model.set_value(cdt, cdn, "vehicle_no", vehicle_no);
		});
	},
	received_amount(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		frm.refresh_field("trips");
		recalc_totals(frm);
	},
	brokerage_amount(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		frm.refresh_field("trips");
		recalc_totals(frm);
	},
	lr_money(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		frm.refresh_field("trips");
		recalc_totals(frm);
	},
	tds_amount(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		frm.refresh_field("trips");
		recalc_totals(frm);
	},
});

function style_fetch_btn(frm) {
	const $field = frm.get_field("fetch_trips_btn").$wrapper;
	const $btn = $field.find("button");
	$field.css({ "margin-top": "21px" });
	$btn.css({
		"background": "linear-gradient(135deg, #00b894 0%, #00cec9 100%)",
		"color": "#fff",
		"font-weight": "700",
		"font-size": "14px",
		"padding": "10px 32px",
		"border": "none",
		"border-radius": "8px",
		"box-shadow": "0 4px 14px rgba(0,184,148,0.4)",
		"cursor": "pointer",
		"letter-spacing": "0.5px",
		"width": "100%",
		"transition": "all 0.2s ease",
	});
	$btn.on("mouseenter", function() {
		$(this).css({ "transform": "translateY(-1px)", "box-shadow": "0 6px 18px rgba(0,184,148,0.5)" });
	}).on("mouseleave", function() {
		$(this).css({ "transform": "translateY(0)", "box-shadow": "0 4px 14px rgba(0,184,148,0.4)" });
	});
}

function recalc_row(row) {
	frappe.model.set_value(row.doctype, row.name, "net_received", flt(row.received_amount));
}

function recalc_totals(frm) {
	if (frm.doc.receipt_type === "Other Receipt") return;

	let total_invoice = 0,
		total_brokerage = 0,
		total_lr_money = 0,
		total_tds = 0,
		total_received = 0;

	get_trip_rows(frm).forEach((r) => {
		total_invoice  += flt(r.invoice_amount);
		total_brokerage += flt(r.brokerage_amount);
		total_lr_money += flt(r.lr_money);
		total_tds      += flt(r.tds_amount);
		total_received += flt(r.received_amount);
	});

	frm.set_value("total_invoice_amount", total_invoice);
	frm.set_value("total_brokerage_amount", total_brokerage);
	frm.set_value("total_lr_money", total_lr_money);
	frm.set_value("total_tds_amount", total_tds);
	frm.set_value("total_received_amount", total_received);
	frm.set_value("total_outstanding_amount", total_invoice - total_received);
	frm.refresh_fields([
		"total_invoice_amount",
		"total_brokerage_amount",
		"total_lr_money",
		"total_tds_amount",
		"total_received_amount",
		"total_outstanding_amount",
	]);
}

function get_trip_rows(frm) {
	return frm.fields_dict?.trips?.grid?.get_data?.() || frm.doc.trips || [];
}

function attach_delete_totals_handler(frm) {
	const grid = frm.fields_dict?.trips?.grid;
	if (!grid?.wrapper) return;

	grid.wrapper.off("click.receipt_totals");
	grid.wrapper.on("click.receipt_totals", ".grid-remove-rows, .grid-remove-all-rows", () => {
		window.setTimeout(() => recalc_totals(frm), 100);
	});
}
