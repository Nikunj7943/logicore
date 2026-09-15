frappe.ui.form.on("Supplier Payment", {
	refresh(frm) {
		style_fetch_btn(frm);
		attach_delete_totals_handler(frm);
	},

	setup(frm) {
		frm.set_query("paid_from_account", () => ({
			filters: { group: frm.doc.mode_of_payment === "Cash" ? "CASH" : "BANK" }
		}));
	},

	mode_of_payment(frm) {
		frm.set_value("paid_from_account", null);
	},

	fetch_invoices_btn(frm) {
		if (!frm.doc.supplier) {
			frappe.msgprint(__("Please select a Supplier first."));
			return;
		}
		if (!frm.doc.from_date || !frm.doc.to_date) {
			frappe.msgprint(__("Please select From Date and To Date."));
			return;
		}

		frappe.call({
			method: "logicore.logicore.doctype.supplier_payment.supplier_payment.get_unpaid_invoices",
			args: {
				supplier: frm.doc.supplier,
				from_date: frm.doc.from_date,
				to_date: frm.doc.to_date,
				company: frm.doc.company,
			},
			freeze: true,
			freeze_message: __("Fetching invoices..."),
			callback(r) {
				if (!r.message || !r.message.length) {
					frappe.msgprint(__("No unpaid invoices found for this supplier and date range."));
					return;
				}

				frm.clear_table("invoices");

				r.message.forEach((inv) => {
					const row = frm.add_child("invoices");

					row.purchase_invoice = inv.name;
					row.supplier_invoice_no = inv.bill_no;
					row.invoice_date = inv.bill_date || inv.posting_date;
					row.grand_total = flt(inv.grand_total);
					row.net_total = flt(inv.net_total);
					row.paid_amount = flt(inv.custom_total_paid);
					row.balance = flt(inv.balance);

					// Default payment = full balance
					row.payment_amount = row.balance;

					recalc_row(row);
				});

				frm.refresh_field("invoices");
				schedule_recalc_totals(frm);

				frappe.show_alert(
					{ message: __("{0} invoice(s) loaded.", [r.message.length]), indicator: "green" },
					3
				);
			},
		});
	},

	invoices_remove(frm) {
		schedule_recalc_totals(frm);
	},

	invoices_delete(frm) {
		schedule_recalc_totals(frm);
	},
});

frappe.ui.form.on("Payment Invoices", {
	payment_amount(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		frm.refresh_field("invoices");
		recalc_totals(frm);
	},
	tds_amount(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		frm.refresh_field("invoices");
		recalc_totals(frm);
	},
});

function style_fetch_btn(frm) {
	const $field = frm.get_field("fetch_invoices_btn").$wrapper;
	const $btn = $field.find("button");
	// Push button down to align vertically with input fields (compensate for label height)
	$field.css({ "margin-top": "21px" });
	$btn.css({
		"background": "linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%)",
		"color": "#fff",
		"font-weight": "700",
		"font-size": "14px",
		"padding": "10px 32px",
		"border": "none",
		"border-radius": "8px",
		"box-shadow": "0 4px 14px rgba(108,92,231,0.4)",
		"cursor": "pointer",
		"letter-spacing": "0.5px",
		"width": "100%",
		"transition": "all 0.2s ease",
	});
	$btn.on("mouseenter", function() {
		$(this).css({ "transform": "translateY(-1px)", "box-shadow": "0 6px 18px rgba(108,92,231,0.5)" });
	}).on("mouseleave", function() {
		$(this).css({ "transform": "translateY(0)", "box-shadow": "0 4px 14px rgba(108,92,231,0.4)" });
	});
}

function recalc_row(row) {
	const pay = flt(row.payment_amount);
	const tds = flt(row.tds_amount);
	frappe.model.set_value(row.doctype, row.name, "transfer_amount", pay - tds);
}

function recalc_totals(frm) {
	let total_pay = 0,
		total_tds = 0,
		total_xfr = 0;

	const rows = get_invoice_rows(frm);

	rows.forEach((r) => {
		total_pay += flt(r.payment_amount);
		total_tds += flt(r.tds_amount);
		total_xfr += flt(r.transfer_amount);
	});

	frm.set_value("total_payment_amount", total_pay);
	frm.set_value("total_tds_amount", total_tds);
	frm.set_value("total_transfer_amount", total_xfr);
	frm.refresh_fields([
		"total_payment_amount",
		"total_tds_amount",
		"total_transfer_amount",
	]);
}

function schedule_recalc_totals(frm) {
	window.setTimeout(() => recalc_totals(frm), 100);
}

function get_invoice_rows(frm) {
	return frm.fields_dict?.invoices?.grid?.get_data?.() || frm.doc.invoices || [];
}

function attach_delete_totals_handler(frm) {
	const grid = frm.fields_dict?.invoices?.grid;
	if (!grid?.wrapper) return;

	grid.wrapper.off("click.supplier_payment_totals");
	grid.wrapper.on("click.supplier_payment_totals", ".grid-remove-rows, .grid-remove-all-rows", () => {
		schedule_recalc_totals(frm);
	});
}
