// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Finance", {
	setup(frm) {
		frm.set_query("bank_name", () => ({
			filters: { group: frm.doc.payment_mode === "Cash" ? "CASH" : "BANK" }
		}));
	},

	refresh(frm) {
		if (!frm.doc.__islocal) {
			load_emi_summary(frm);
		}
	},

	payment_mode(frm) {
		frm.set_value("bank_name", null);
	},

	after_save(frm) {
        setTimeout(()=>{
            frappe.set_route("List","Vehicle Finance");
        },500);
	},
});

function load_emi_summary(frm) {
	frappe.call({
		method: "logicore.logicore.doctype.vehicle_finance.vehicle_finance.get_emi_payment_summary",
		args: { vehicle_finance: frm.doc.name },
		callback(r) {
			if (!r.message) return;
			const { emis_paid, emis_balance, amount_paid, amount_pending, payments } = r.message;
			const wrapper = frm.get_field("emi_payments_html").$wrapper;
			wrapper.html(build_emi_summary_html(emis_paid, emis_balance, amount_paid, amount_pending, payments));
		}
	});
}

function build_emi_summary_html(emis_paid, emis_balance, amount_paid, amount_pending, payments) {
	const fmt = v => "₹ " + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2 });

	const cards = `
		<style>
			.vf-cards-grid {
				display: grid;
				grid-template-columns: repeat(4, 1fr);
				gap: 12px;
				margin-bottom: 20px;
			}
			@media (max-width: 768px) { .vf-cards-grid { grid-template-columns: repeat(2, 1fr); } }
			@media (max-width: 480px) { .vf-cards-grid { grid-template-columns: 1fr; } }
			.vf-card {
				background: var(--card-bg);
				border: 1px solid var(--border-color);
				border-radius: 8px;
				padding: 14px 16px;
				text-align: center;
			}
			.vf-card-label {
				font-size: 11px;
				color: var(--text-muted);
				text-transform: uppercase;
				letter-spacing: .6px;
				margin-bottom: 6px;
			}
			.vf-emi-table { width: 100%; border-collapse: collapse; font-size: 13px; }
			.vf-emi-table thead tr { background: #1a73e8; color: #fff; }
			.vf-emi-table th { padding: 10px 14px; text-align: left; font-weight: 600; }
			.vf-emi-table td { padding: 10px 14px; border-bottom: 1px solid var(--border-color); color: var(--text-color); white-space: nowrap; }
			.vf-emi-table tbody tr:hover { background: var(--control-bg); }
			.vf-emi-table tfoot td { padding: 10px 14px; border-top: 2px solid var(--border-color); background: var(--control-bg); font-weight: 700; }
		</style>
		<div class="vf-cards-grid">
			${card("EMIs Paid",      emis_paid,           "var(--green)")}
			${card("EMIs Balance",   emis_balance,        "var(--orange)")}
			${card("Amount Paid",    fmt(amount_paid),    "var(--blue)")}
			${card("Amount Pending", fmt(amount_pending), "var(--red)")}
		</div>
	`;

	if (!payments || !payments.length) {
		return cards + `<p style="color:var(--text-muted); font-size:13px;">No EMI payments found.</p>`;
	}

	const rows = payments.map(p => {
		const status_color = p.docstatus === 1 ? "var(--green)" : p.docstatus === 2 ? "var(--red)" : "var(--orange)";
		const status_label = p.docstatus === 1 ? "Paid" : p.docstatus === 2 ? "Cancelled" : "Draft";
		const ref  = p.reference_no ? frappe.utils.escape_html(p.reference_no) : "—";
		const date = p.date ? frappe.datetime.str_to_user(p.date) : "—";
		return `<tr>
			<td>
				<a href="/app/payment/${frappe.utils.escape_html(p.name)}"
				   style="color:#1a73e8; font-weight:600; text-decoration:none;">
					${frappe.utils.escape_html(p.name)}
				</a>
			</td>
			<td>${date}</td>
			<td style="color:var(--text-muted)">${ref}</td>
			<td style="font-weight:600; color:${status_color}">${status_label}</td>
			<td style="text-align:right; font-weight:600;">${fmt(p.amount)}</td>
		</tr>`;
	}).join("");

	const total_paid = payments.filter(p => p.docstatus === 1).reduce((s, p) => s + flt(p.amount), 0);

	return cards + `
		<div style="overflow-x:auto; border-radius:6px; border:1px solid var(--border-color);">
			<table class="vf-emi-table">
				<thead>
					<tr>
						<th>Payment No</th>
						<th>Date</th>
						<th>Reference No</th>
						<th>Status</th>
						<th style="text-align:right">Amount</th>
					</tr>
				</thead>
				<tbody>${rows}</tbody>
				<tfoot>
					<tr>
						<td colspan="3"></td>
						<td style="text-align:right; color:var(--text-muted)">Total Paid</td>
						<td style="text-align:right; color:var(--green)">₹ ${flt(total_paid).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
					</tr>
				</tfoot>
			</table>
		</div>
	`;
}

function card(label, value, color) {
	return `
		<div class="vf-card" style="border-top: 3px solid ${color};">
			<div class="vf-card-label">${label}</div>
			<div style="font-size:20px; font-weight:700; color:${color};">${value}</div>
		</div>
	`;
}
