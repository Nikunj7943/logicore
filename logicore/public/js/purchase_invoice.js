// Purchase Invoice — keep the form looking the same in every state.
//
// Out of the box ERPNext grows the form once the invoice is saved: the "More Info"
// and "Connections" tabs appear, and the toolbar picks up the "Create", "Preview"
// and "Get Items From" button groups. LogiCore wants a saved/submitted invoice to
// look exactly like a freshly created one, so those groups are suppressed here.
//
// The two extra tabs are handled by Property Setters (more_info_tab.hidden /
// connections_tab.hidden) in logicore/custom/purchase_invoice.json — only
// the toolbar needs client-side work, because the buttons are added imperatively
// by the ERPNext controller (and some of them asynchronously, after our refresh
// handler has already run).

frappe.provide("logicore");

// Button groups that must never show up on a Purchase Invoice toolbar.
logicore.PI_BLOCKED_BUTTON_GROUPS = ["Create", "Preview", "Get Items From"];

function is_blocked_group(group) {
	if (!group) return false;
	return logicore.PI_BLOCKED_BUTTON_GROUPS.some((g) => group === g || group === __(g));
}

// Wrap frm.add_custom_button on this form instance only (shadows the prototype
// method) so blocked groups are dropped at the source — this also keeps them out
// of the mobile "..." menu, which add_inner_button populates in parallel.
function block_button_groups(frm) {
	if (frm.__logicore_button_filter) return;
	frm.__logicore_button_filter = true;

	const original_add = frm.add_custom_button.bind(frm);
	frm.add_custom_button = function (label, fn, group) {
		if (is_blocked_group(group)) return;
		return original_add(label, fn, group);
	};

	// set_inner_btn_group_as_primary() creates the group if it is missing, so a
	// blocked group could still be re-created as an empty dropdown.
	const page = frm.page;
	const original_primary = page.set_inner_btn_group_as_primary.bind(page);
	page.set_inner_btn_group_as_primary = function (label) {
		if (is_blocked_group(label)) return;
		return original_primary(label);
	};
}

// Safety net: strip any blocked group that slipped in before the wrapper was
// installed (e.g. an app registering its refresh handler ahead of ours).
function strip_blocked_groups(frm) {
	const toolbar = frm.page && frm.page.inner_toolbar;
	if (!toolbar) return;

	logicore.PI_BLOCKED_BUTTON_GROUPS.forEach((group) => {
		[group, __(group)].forEach((label) => {
			toolbar.find(`.inner-group-button[data-label="${encodeURIComponent(label)}"]`).remove();
		});
	});

	if (!toolbar.children().length) {
		toolbar.addClass("hide");
	}
}

// Payment history table — same look as Trip's vendor payment history table
// (doctype/trip/trip.js render_vendor_payment_table): colored header, striped
// rows, rounded card border, dark-mode aware. Injected full-width into the
// section body rather than left in the field's own (half-width) column,
// exactly like Trip does.
function tms_is_dark_theme() {
	return document.documentElement.getAttribute("data-theme-mode") === "dark";
}

function tms_hex_to_rgb(hex) {
	const m = hex.replace("#", "");
	const bigint = parseInt(m.length === 3 ? m.split("").map((c) => c + c).join("") : m, 16);
	return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
}

function tms_hex_alpha(hex, a) {
	try {
		const [r, g, b] = tms_hex_to_rgb(hex);
		return `rgba(${r},${g},${b},${a})`;
	} catch {
		return hex;
	}
}

function render_payment_history(frm) {
	const field = frm.fields_dict.payment_history_html;
	if (!field || !field.$wrapper) return;

	field.$wrapper.html("").closest(".form-column").css("display", "none");
	$("#tms-pi-payment-table").remove();

	if (frm.is_new()) return;

	frappe.call({
		method: "logicore.logicore.doctype.supplier_payment.supplier_payment.get_payment_history",
		args: { purchase_invoice: frm.doc.name },
		callback(r) {
			const payments = r.message || [];
			if (!payments.length) return;

			const isDark = tms_is_dark_theme();
			const pri = "#3B4FE4";
			const secBdr = isDark ? tms_hex_alpha(pri, 0.2) : tms_hex_alpha(pri, 0.28);
			const fldBg = tms_hex_alpha(pri, 0.05);
			const hdgClr = "#1E1B4B";
			const lblClr = "#3730A3";
			const radius = "10px";
			const cardBg = isDark ? "#1F2937" : "#FFFFFF";
			const rowBgA = isDark ? cardBg : "#FFFFFF";
			const rowBgB = isDark ? tms_hex_alpha(pri, 0.12) : fldBg;
			const textClr = isDark ? "#E5E7EB" : hdgClr;
			const mutedClr = isDark ? "#94A3B8" : lblClr;
			const footerBg = isDark ? tms_hex_alpha("#FFFFFF", 0.04) : fldBg;
			const footerBorder = isDark ? tms_hex_alpha("#FFFFFF", 0.1) : secBdr;
			const accentClr = isDark ? "#34D399" : "#00b894";

			const fmt_inr = (v) => {
				const n = flt(v);
				const abs = Math.abs(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
				return (n < 0 ? "− ₹" : "₹ ") + abs;
			};

			const TH = `padding:9px 12px;font-size:10px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.6px;white-space:nowrap;`;
			const THL = TH + `text-align:left;`;
			const THR = TH + `text-align:right;`;
			const TD = `padding:8px 12px;border-bottom:1px solid ${secBdr};font-size:12px;color:${textClr};white-space:nowrap;`;
			const TDM = TD + `color:${mutedClr};font-size:11px;`;
			const TDR = TD + `text-align:right;font-variant-numeric:tabular-nums;font-weight:600;`;

			const rows_html = payments
				.map((p, i) => {
					const date = p.payment_date ? frappe.datetime.str_to_user(p.payment_date) : "—";
					const mode = frappe.utils.escape_html(p.mode_of_payment || "—");
					return `<tr style="background:${i % 2 === 0 ? rowBgA : rowBgB};">
						<td style="${TD}">
							<a href="/app/supplier-payment/${p.name}" style="color:${pri};font-weight:600;text-decoration:none;"
							   onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">${p.name}</a>
						</td>
						<td style="${TDM}">${frappe.utils.escape_html(date)}</td>
						<td style="${TDM}">${mode}</td>
						<td style="${TDR}">${fmt_inr(p.payment_amount)}</td>
						<td style="${TDR}${flt(p.tds_amount) ? "color:#ef4444;" : `color:${mutedClr};font-weight:400;`}">${flt(p.tds_amount) ? fmt_inr(p.tds_amount) : "—"}</td>
						<td style="${TDR}color:${accentClr};font-weight:700;">${fmt_inr(p.transfer_amount)}</td>
					</tr>`;
				})
				.join("");

			const totalPayment = payments.reduce((s, p) => s + flt(p.payment_amount), 0);
			const totalTds = payments.reduce((s, p) => s + flt(p.tds_amount), 0);
			const totalTransfer = payments.reduce((s, p) => s + flt(p.transfer_amount), 0);

			const footer_html = `<tfoot><tr>
					<td colspan="3" style="padding:9px 12px;font-size:11px;font-weight:700;background:${footerBg};border-top:2px solid ${footerBorder};color:${mutedClr};">
						${__("Total")} (${payments.length} ${payments.length !== 1 ? __("payments") : __("payment")})
					</td>
					<td style="padding:9px 12px;font-size:12px;font-weight:700;background:${footerBg};border-top:2px solid ${footerBorder};text-align:right;color:${textClr};">${fmt_inr(totalPayment)}</td>
					<td style="padding:9px 12px;font-size:12px;font-weight:700;background:${footerBg};border-top:2px solid ${footerBorder};text-align:right;color:${totalTds ? "#ef4444" : mutedClr};">${totalTds ? fmt_inr(totalTds) : "—"}</td>
					<td style="padding:9px 12px;font-size:13px;font-weight:800;background:${footerBg};border-top:2px solid ${footerBorder};text-align:right;color:${accentClr};">${fmt_inr(totalTransfer)}</td>
				</tr></tfoot>`;

			const tableHtml = `
				<div id="tms-pi-payment-table" style="width:100%;padding:0 15px 4px;">
					<div style="border:1.5px solid ${secBdr};border-radius:${radius};overflow:hidden;background:${cardBg};">
						<table style="width:100%;border-collapse:collapse;">
							<thead>
								<tr style="background:${pri};">
									<th style="${THL}width:22%;">${__("Supplier Payment")}</th>
									<th style="${THL}width:16%;">${__("Date")}</th>
									<th style="${THL}width:16%;">${__("Mode")}</th>
									<th style="${THR}width:16%;">${__("Amount")}</th>
									<th style="${THR}width:14%;">${__("TDS")}</th>
									<th style="${THR}width:16%;">${__("Transferred")}</th>
								</tr>
							</thead>
							<tbody>${rows_html}</tbody>
							${footer_html}
						</table>
					</div>
				</div>`;

			const $section = field.$wrapper.closest(".form-section").find(".section-body").first();
			$section.append(tableHtml);
		},
	});
}

// Live preview of what's owed — before the first save, not just after.
// custom_total_paid is only ever written server-side (by Supplier Payment,
// which requires a submitted invoice), so it's safe to treat as read-only
// here and just re-derive balance/status from whatever the form already has.
function sync_payment_fields_client(frm) {
	const total_paid = flt(frm.doc.custom_total_paid);
	const balance = flt(frm.doc.grand_total) - total_paid;

	let status;
	if (balance <= 0 && frm.doc.grand_total) {
		status = "Paid";
	} else if (total_paid > 0) {
		status = "Partially Paid";
	} else {
		status = "Unpaid";
	}

	frm.set_value("custom_payment_status", status);
	frm.set_value("custom_balance_amount", Math.max(balance, 0));
	frm.set_value("custom_outstanding_balance", Math.max(balance, 0));
}

// ERPNext recalculates grand_total by writing frm.doc.grand_total directly
// (calculate_taxes_and_totals in erpnext/public/js/controllers/taxes_and_totals.js),
// which does not fire a "grand_total" field-change trigger — so that alone
// never catches a real item being added through the grid. Item row edits and
// add/remove are what actually happen on user interaction, so trigger the
// sync from those instead, after a tick so ERPNext's own recalculation (bound
// to the same events) has already run.
function queue_sync_payment_fields(frm) {
	setTimeout(() => sync_payment_fields_client(frm), 300);
}

// ERPNext's own "status" indicator (Draft/Unpaid/Paid/Overdue...) is driven by
// the general ledger, which this app deliberately never touches — so it keeps
// showing "Unpaid" even once fully paid via Supplier Payment. ERPNext's own
// refresh handler sets the title-bar badge directly via frm.page.set_indicator
// (not the docfield formatter, which only affects status shown as a field
// value elsewhere, e.g. in list views) — so the badge has to be overridden
// the same way, after ERPNext's own handler has already run.
function set_payment_status_indicator(frm) {
	if (frm.doc.docstatus !== 1) return;

	let color = "orange";
	if (frm.doc.custom_payment_status === "Paid") color = "green";

	frm.page.set_indicator(__(frm.doc.custom_payment_status || "Unpaid"), color);
}

// India Compliance renders its GSTR-2A/2B match state as the description of the
// `bill_no` field. LogiCore reconciles against the bank statement, not the GST
// return, so that indicator is replaced with the TMS bank reconciliation status.
//
// The swap has to be deferred: sites/apps.txt lists logicore before
// india_compliance, so their refresh handler runs after ours and would re-set the
// description. A zero-delay timeout lands after the whole refresh chain.
const BANK_RECON_COLORS = {
	Reconciled: "green",
	"Partially Reconciled": "orange",
	Unreconciled: "red",
};

function set_bank_reconciliation_indicator(frm) {
	if (frm.doc.docstatus !== 1) return;

	setTimeout(() => {
		const field = frm.get_field("bill_no");
		if (!field) return;
		const status = frm.doc.custom_bank_reconciliation_status || "Unreconciled";
		const color = BANK_RECON_COLORS[status] || "grey";
		field.set_description(
			`<div class="d-flex indicator ${color}">${__("Bank Recon")}:&nbsp;<strong>${__(
				status
			)}</strong></div>`
		);
	}, 0);
}

// ERPNext's stock_controller.js adds a "View > Stock Ledger" button on any
// submitted stock-impacting document, routing to Frappe's own built-in
// "Stock Ledger" report — TMS has its own "TMS Stock Ledger" report instead
// (see report/tms_stock_ledger/), so that button must point there instead.
function redirect_stock_ledger_button(frm) {
	if (frm.doc.docstatus < 1) return;
	frm.remove_custom_button(__("Stock Ledger"), __("View"));
	frm.add_custom_button(
		__("Stock Ledger"),
		() => {
			frappe.set_route("query-report", "TMS Stock Ledger", {
				voucher_no: frm.doc.name,
				company: frm.doc.company,
				from_date: "",
				to_date: "",
			});
		},
		__("View")
	);
}

// Reverted per user request — Purchase Invoice goes back to plain
// posting_date, no custom Payment Date field. Kept here (commented out, not
// deleted) in case the feature is wanted again.
// function sync_posting_date_from_purchase_date(frm) {
// 	if (frm.doc.custom_purchase_date && frm.doc.posting_date !== frm.doc.custom_purchase_date) {
// 		frm.set_value("posting_date", frm.doc.custom_purchase_date);
// 	}
// }

frappe.ui.form.on("Purchase Invoice", {
	onload(frm) {
		block_button_groups(frm);
		if (frm.is_new() && !frm.doc.set_warehouse) {
			frappe.db.get_single_value("Stock Settings", "default_warehouse").then((warehouse) => {
				if (warehouse && frm.is_new() && !frm.doc.set_warehouse) {
					frm.set_value("set_warehouse", warehouse);
				}
			});
		}
	},

	items_add(frm) {
		queue_sync_payment_fields(frm);
	},

	items_remove(frm) {
		queue_sync_payment_fields(frm);
	},

	refresh(frm) {
		block_button_groups(frm);
		strip_blocked_groups(frm);
		render_payment_history(frm);
		sync_payment_fields_client(frm);
		set_payment_status_indicator(frm);
		set_bank_reconciliation_indicator(frm);
		redirect_stock_ledger_button(frm);
	},

	grand_total(frm) {
		sync_payment_fields_client(frm);
	},
});

frappe.ui.form.on("Purchase Invoice Item", {
	qty(frm) {
		queue_sync_payment_fields(frm);
	},
	rate(frm) {
		queue_sync_payment_fields(frm);
	},
	item_code(frm) {
		queue_sync_payment_fields(frm);
	},
});
