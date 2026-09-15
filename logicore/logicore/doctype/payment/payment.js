// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

const MODE_OF_PAYMENT_OPTIONS = "Cash\nBank Transfer\nCheque\nUPI";
const MODE_OF_PAYMENT_OPTIONS_WITH_ATM = "Cash\nBank Transfer\nCheque\nUPI\nATM";

function toggle_mode_of_payment_atm_option(frm) {
	const is_cash_withdrawal = frm.doc.type === "Cash Withdrawal";
	frm.set_df_property(
		"mode_of_payment", "options",
		is_cash_withdrawal ? MODE_OF_PAYMENT_OPTIONS_WITH_ATM : MODE_OF_PAYMENT_OPTIONS
	);
	// A value only valid under the wider option set (ATM) must not be left
	// silently selected once that set narrows back down for a different type.
	if (!is_cash_withdrawal && frm.doc.mode_of_payment === "ATM") {
		frm.set_value("mode_of_payment", null);
	}
}

frappe.ui.form.on("Payment", {
	setup(frm) {
		frm.set_query("paid_from_account", () => ({
			// ATM withdrawal still comes out of a real bank account — same
			// BANK-group filter as every mode_of_payment other than "Cash".
			filters: { group: frm.doc.mode_of_payment === "Cash" ? "CASH" : "BANK" }
		}));
		// transfer_to_account is always a bank-to-bank leg (Bank Transfer type) —
		// never Cash, so this one intentionally stays fixed to BANK.
		frm.set_query("transfer_to_account", () => ({
			filters: { group: "BANK" }
		}));
		frm.set_query("trip_no", () => ({
			query: "logicore.logicore.doctype.payment.payment.search_trips"
		}));
	},

	mode_of_payment(frm) {
		frm.set_value("paid_from_account", null);
	},

	paid_from_account(frm) {
		check_transfer_accounts_differ(frm);
	},

	transfer_to_account(frm) {
		check_transfer_accounts_differ(frm);
	},

	refresh(frm) {
		frm.add_custom_button(__("Print Payment"), function () {
			frappe.utils.print(frm.doctype, frm.docname, "Payment TMS", frm.doc.language);
		}).addClass("btn-primary");

		style_payment_form(frm);
		set_status_indicator(frm);
		toggle_mode_of_payment_atm_option(frm);

		frm.set_query("select_account", () => {
			if (frm.doc.type === "Employee Advance") return { filters: { group: "Employee Advance" } };
			if (frm.doc.type === "Driver Advance") return { filters: { name1: "Driver Salary Advance" } };
			if (frm.doc.type === "Driver Trip Expense") return { filters: { name1: "Driver Trip Expense" } };
			if (frm.doc.type === "Cash Withdrawal") return { filters: { group: "CASH" } };
			return { filters: { group: "EXPENSE" } };
		});

		const no_trip_types = ["Office/Other Expense", "Employee Advance", "Driver Advance", "Vehicle Finance EMI", "Bank Transfer", "Cash Withdrawal"];
		const is_office = no_trip_types.includes(frm.doc.type);
		toggle_trip_section(frm, !is_office);

		if (!is_office) {
			toggle_trip_summary_table(frm);
			if (frm.doc.trip_no) {
				toggle_trip_detail_fields(frm, true);
				if (frm.doc.docstatus === 0) {
					// Re-fetch live Trip data instead of trusting the snapshot saved
					// on this Payment doc, which goes stale if the Trip is edited later
					// (e.g. vehicle no added after this Payment was first saved).
					// Banner/payments must render only after the fetch resolves, else
					// they render with the still-stale frm.doc values.
					frappe.db.get_doc("Trip", frm.doc.trip_no).then(trip => {
						sync_trip_fields(frm, trip);
						show_trip_info_banner(frm);
						if (frm.doc.type !== "Driver Trip Expense") {
							load_trip_payments(frm);
							show_payment_balance(frm);
						}
					});
				} else {
					show_trip_info_banner(frm);
					if (frm.doc.type !== "Driver Trip Expense") {
						load_trip_payments(frm);
						show_payment_balance(frm);
					}
				}
			} else {
				toggle_trip_detail_fields(frm, false);
				frm.get_field("trip_no").$wrapper.find(".trip-info-banner").remove();
				frm.get_field("trip_payments_html").$wrapper.html("");
			}
		}

		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Mark as Paid"), () => {
				frm.set_value("status", "Paid");
				frm.save();
			}, frm.doc.status !== "Paid" ? undefined : null);
		}
	},

	trip_no(frm) {
		if (frm.doc.trip_no) {
			toggle_trip_detail_fields(frm, true);
			frappe.db.get_doc("Trip", frm.doc.trip_no).then(trip => {
				sync_trip_fields(frm, trip);
				show_trip_info_banner(frm);
				toggle_trip_summary_table(frm);
				if (frm.doc.type !== "Driver Trip Expense") {
					load_trip_payments(frm);
					show_payment_balance(frm);
				}
			});
		} else {
			["trip_tcn_no", "trip_date", "trip_type", "trip_origin", "trip_destination", "trip_vehicle_type"]
				.forEach(f => frm.set_value(f, ""));
			if (frm.doc.type !== "Vehicle Finance EMI") {
				frm.set_value("vf_vehicle", "");
			}
			if (frm.doc.type === "Driver Trip Expense") {
				frm.set_value("vehicle", "");
			}
			frm.set_value("outstanding_balance", 0);
			frm.get_field("trip_no").$wrapper.find(".trip-info-banner").remove();
			frm.get_field("trip_payments_html").$wrapper.html("");
			toggle_trip_detail_fields(frm, false);
		}
	},

	status(frm) {
		set_status_indicator(frm);
	},

	vehicle(frm) {
		// Mirror manual Vehicle selection into vf_vehicle (the list-view "Vehicle No" column)
		// only when there's no Trip — with a Trip, sync_trip_fields() already owns vf_vehicle.
		if (["Driver Trip Expense", "Border Crossing/Vehicle Expense/Toll Tax", "Police Entry"].includes(frm.doc.type) && !frm.doc.trip_no) {
			frm.set_value("vf_vehicle", frm.doc.vehicle || "");
		}
	},

	vehicle_finance(frm) {
		if (!frm.doc.vehicle_finance) {
			["vf_vehicle", "vf_financer", "vf_loan_account", "vf_bank_account", "trip_vehicle_type"].forEach(f => frm.set_value(f, ""));
			frm.set_value("amount", 0);
			frm.set_value("paid_from_account", null);
			return;
		}
		frappe.db.get_doc("Vehicle Finance", frm.doc.vehicle_finance).then(vf => {
			frm.set_value("vf_vehicle", vf.vehicle || "");
			if (vf.vehicle) {
				frappe.db.get_value("Vehicle", vf.vehicle, "custom_vehicle_type").then(r => {
					frm.set_value("trip_vehicle_type", r.message.custom_vehicle_type || "");
				});
			} else {
				frm.set_value("trip_vehicle_type", "");
			}
			frm.set_value("vf_financer", vf.finance || "");
			frm.set_value("vf_loan_account", vf.loan_account || "");
			frm.set_value("amount", vf.emi_amount || 0);
			frm.set_value("mode_of_payment", vf.payment_mode || "Bank Transfer");
			frm.set_value("paid_from_account", vf.bank_name || null);
		});
	},

	type(frm) {
		const no_trip_types = ["Office/Other Expense", "Employee Advance", "Driver Advance", "Vehicle Finance EMI", "Bank Transfer", "Cash Withdrawal"];
		const is_no_trip = no_trip_types.includes(frm.doc.type);
		toggle_trip_section(frm, !is_no_trip);
		toggle_mode_of_payment_atm_option(frm);

		// Re-apply account filter based on new type
		frm.set_query("select_account", () => {
			if (frm.doc.type === "Employee Advance") return { filters: { group: "Employee Advance" } };
			if (frm.doc.type === "Driver Advance") return { filters: { name1: "Driver Salary Advance" } };
			if (frm.doc.type === "Driver Trip Expense") return { filters: { name1: "Driver Trip Expense" } };
			if (frm.doc.type === "Cash Withdrawal") return { filters: { group: "CASH" } };
			return { filters: { group: "EXPENSE" } };
		});
		frm.set_value("select_account", null);

		frm.refresh_fields(["vendor_supplier", "transfer_to_account", "employee", "driver", "select_account"]);
		toggle_trip_summary_table(frm);
		if (!is_no_trip && frm.doc.type !== "Driver Trip Expense") show_payment_balance(frm);
	}
});

function sync_trip_fields(frm, trip) {
	frm.set_value("trip_tcn_no", trip.tcntrip_no || "");
	frm.set_value("trip_date", trip.tcntrip_date || "");
	frm.set_value("trip_type", trip.trip_type || "");
	frm.set_value("trip_origin", trip.origin_city || "");
	frm.set_value("trip_destination", trip.destination_city_1 || "");
	frm.set_value("trip_vehicle_type", trip.vehicle_type || "");
	if (frm.doc.type !== "Vehicle Finance EMI") {
		frm.set_value("vf_vehicle", trip.vehicle_no || trip.vehicle_market || "");
	}
	if (frm.doc.type === "Driver Trip Expense") {
		// Only a registered fleet Vehicle can populate this Link field;
		// a market/hired vehicle (free text, no Vehicle master record) leaves it blank.
		frm.set_value("vehicle", trip.vehicle_no || "");
	}
}

function toggle_trip_summary_table(frm) {
	const show = !!(frm.doc.trip_no) && frm.doc.type !== "Driver Trip Expense";
	frm.set_df_property("trip_payments_html", "hidden", show ? 0 : 1);
	frm.refresh_field("trip_payments_html");
	if (!show) frm.get_field("trip_payments_html").$wrapper.html("");
}

function toggle_trip_section(frm, show) {
	const section_fields = ["section_break_trip", "trip_no", "trip_payments_html"];
	section_fields.forEach(f => frm.set_df_property(f, "hidden", show ? 0 : 1));
	if (!show) {
		toggle_trip_detail_fields(frm, false);
		frm.get_field("trip_no").$wrapper.find(".trip-info-banner").remove();
		frm.get_field("trip_payments_html").$wrapper.html("");
	}
	frm.refresh_fields(section_fields);
}

function toggle_trip_detail_fields(frm, show) {
	const fields = [
		"column_break_trip", "trip_tcn_no", "trip_date",
		"section_break_trip_route", "trip_type", "trip_origin",
		"column_break_trip_route", "trip_destination", "trip_vehicle_type"
	];
	fields.forEach(f => frm.set_df_property(f, "hidden", show ? 0 : 1));
	frm.refresh_fields(fields);
}

function show_payment_balance(frm) {
	const wrapper = frm.get_field("trip_payments_html").$wrapper;
	wrapper.find(".balance-banner").remove();

	const trip_no = frm.doc.trip_no;
	const type = frm.doc.type;
	if (!trip_no || !["Loading", "Unloading", "Loading/Unloading", "Extra Expense"].includes(type)) {
		frm.set_value("outstanding_balance", 0);
		return;
	}

	frappe.call({
		method: "logicore.logicore.doctype.payment.payment.get_trip_payment_balance",
		// Exclude self only when draft (docstatus=0) to avoid double-counting.
		// For submitted docs, include self so "Already Paid" reflects reality.
		args: { trip_no, payment_type: type, exclude_payment: frm.doc.docstatus === 0 ? (frm.doc.name || "") : "" },
		callback(r) {
			if (!r.message) return;
			const { limit, already_paid, balance } = r.message;
			frm.set_value("outstanding_balance", balance);
			const fmt = v => "₹ " + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2 });
			const color = balance <= 0 ? "#2e7d32" : already_paid > 0 ? "#e65100" : "#c62828";
			const bg    = balance <= 0 ? "#e8f5e9" : already_paid > 0 ? "#fff3e0" : "#ffebee";
			const banner = $(`
				<div class="balance-banner" style="display:grid; grid-template-columns:1fr 1fr 1fr;
					background:${bg}; border:1px solid ${color}55; border-radius:5px;
					font-size:12px; margin-bottom:10px; overflow:hidden;">
					<div style="padding:7px 12px; border-right:1px solid ${color}33;">
						<div style="color:#888; font-size:11px;">Trip Amount</div>
						<div style="font-weight:700; color:#333;">${fmt(limit)}</div>
					</div>
					<div style="padding:7px 12px; border-right:1px solid ${color}33;">
						<div style="color:#888; font-size:11px;">Already Paid</div>
						<div style="font-weight:700; color:#333;">${fmt(already_paid)}</div>
					</div>
					<div style="padding:7px 12px;">
						<div style="color:#888; font-size:11px;">Available Balance</div>
						<div style="font-weight:700; color:${color}; font-size:13px;">${fmt(balance)}</div>
					</div>
				</div>
			`);
			wrapper.prepend(banner);
		}
	});
}

function show_trip_info_banner(frm) {
	const field = frm.get_field("trip_no");
	field.$wrapper.find(".trip-info-banner").remove();

	if (!frm.doc.trip_tcn_no && !frm.doc.trip_type) return;

	const origin = frm.doc.trip_origin || "—";
	const dest = frm.doc.trip_destination || "—";
	const tcn = frm.doc.trip_tcn_no || "—";
	const ttype = frm.doc.trip_type || "—";
	const vtype = frm.doc.trip_vehicle_type || "—";
	const vno = frm.doc.vf_vehicle || "—";
	const tdate = frm.doc.trip_date ? frappe.datetime.str_to_user(frm.doc.trip_date) : "—";

	const banner = $(`
		<div class="trip-info-banner" style="
			margin-top: 8px;
			padding: 10px 14px;
			background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
			border: 1px solid #b3d7f7;
			border-left: 4px solid #1a73e8;
			border-radius: 6px;
			font-size: 12px;
			color: #333;
		">
			<div style="display:flex; flex-wrap:wrap; gap: 12px 24px; align-items:center;">
				<span><b style="color:#1a73e8">TCN/Trip:</b> ${frappe.utils.escape_html(tcn)}</span>
				<span><b style="color:#1a73e8">Date:</b> ${frappe.utils.escape_html(tdate)}</span>
				<span><b style="color:#1a73e8">Type:</b> ${frappe.utils.escape_html(ttype)}</span>
				<span><b style="color:#1a73e8">Vehicle No:</b> ${frappe.utils.escape_html(vno)}</span>
				<span><b style="color:#1a73e8">Vehicle Type:</b> ${frappe.utils.escape_html(vtype)}</span>
				<span><b style="color:#1a73e8">Route:</b> ${frappe.utils.escape_html(origin)} → ${frappe.utils.escape_html(dest)}</span>
			</div>
		</div>
	`);

	field.$wrapper.append(banner);
}

function load_trip_payments(frm) {
	if (!frm.doc.trip_no) return;
	frappe.call({
		method: "logicore.logicore.doctype.payment.payment.get_trip_payments",
		args: { trip_no: frm.doc.trip_no },
		callback(r) {
			const rows = r.message || [];
			const wrapper = frm.get_field("trip_payments_html").$wrapper;
			if (!rows.length) { wrapper.html(""); return; }

			let total = rows.reduce((s, p) => s + flt(p.amount), 0);
			let html = `<div style="margin-top:8px">
				<table class="table table-bordered table-condensed" style="font-size:12px;margin-bottom:4px">
					<thead style="background:#6c5ce7;color:#fff">
						<tr>
							<th>Reference</th><th>Date</th><th>Vendor / Employee</th>
							<th>Type</th><th style="text-align:right">Amount</th>
						</tr>
					</thead><tbody>`;
			rows.forEach(p => {
				html += `<tr>
					<td><a href="/app/payment/${frappe.utils.escape_html(p.name)}">${frappe.utils.escape_html(p.name)}</a></td>
					<td>${frappe.datetime.str_to_user(p.date)}</td>
					<td>${frappe.utils.escape_html(p.party || "—")}</td>
					<td>${frappe.utils.escape_html(p.type)}</td>
					<td style="text-align:right">₹ ${flt(p.amount).toLocaleString("en-IN", {minimumFractionDigits:2})}</td>
				</tr>`;
			});
			html += `</tbody><tfoot>
				<tr style="font-weight:700">
					<td colspan="4">Total (${rows.length} payment${rows.length > 1 ? "s" : ""})</td>
					<td style="text-align:right;color:#6c5ce7">₹ ${flt(total).toLocaleString("en-IN", {minimumFractionDigits:2})}</td>
				</tr></tfoot></table></div>`;
			wrapper.html(html);
		}
	});
}

function check_transfer_accounts_differ(frm) {
	if (
		frm.doc.type === "Bank Transfer" &&
		frm.doc.paid_from_account &&
		frm.doc.transfer_to_account &&
		frm.doc.paid_from_account === frm.doc.transfer_to_account
	) {
		frappe.msgprint(__("Paid From Account and Transfer To (Bank Account) cannot be the same."));
		frm.set_value("transfer_to_account", null);
	}
}

function set_status_indicator(frm) {
	const colors = { Draft: "yellow", Paid: "green", Cancelled: "red" };
	const color = colors[frm.doc.status] || "grey";
	frm.page.set_indicator(frm.doc.status || "Draft", color);
}

function style_payment_form(frm) {
	if (frm.$wrapper.find(".pmt-style-injected").length) return;
	frm.$wrapper.append('<span class="pmt-style-injected" style="display:none"></span>');

	frappe.dom.set_style(`
		.payment-form-header {
			background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
			color: white;
			padding: 12px 16px;
			border-radius: 6px;
			margin-bottom: 12px;
		}
		[data-fieldname="payment_no"] .control-value,
		[data-fieldname="payment_no"] input {
			font-size: 16px;
			font-weight: 700;
			color: #1a73e8;
			letter-spacing: 0.5px;
		}
		[data-fieldname="amount"] .control-value,
		[data-fieldname="amount"] input {
			font-size: 18px;
			font-weight: 700;
			color: #2e7d32;
		}
		[data-fieldname="section_break_payee"] .section-head,
		[data-fieldname="section_break_trip"] .section-head,
		[data-fieldname="section_break_trip_route"] .section-head {
			font-weight: 700;
			color: #1a73e8;
			border-bottom: 2px solid #e3f2fd;
			padding-bottom: 4px;
			margin-bottom: 8px;
		}
		[data-fieldname="trip_tcn_no"] .control-value {
			font-weight: 700;
			color: #e65100;
			font-size: 14px;
		}
		[data-fieldname="status"] .control-value {
			font-weight: 600;
		}
	`);
}
