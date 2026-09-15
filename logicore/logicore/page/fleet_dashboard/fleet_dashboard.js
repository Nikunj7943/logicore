frappe.pages["fleet_dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Fleet Dashboard",
		single_column: true,
	});

	page.add_action_item(__("Refresh"), function () {
		render_skeleton(page.main);
		load_all(page.main);
	});

	inject_styles();
	render_skeleton(page.main);
	load_all(page.main);
};

// ─── Styles ───────────────────────────────────────────────────────────────────

function inject_styles() {
	frappe.dom.set_style(`
	.fd {
		padding: 2px 2px 40px;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
	}

	/* Header */
	.fd-header {
		background: linear-gradient(135deg, #0f2444 0%, #1d4ed8 55%, #0284c7 100%);
		border-radius: 14px; padding: 22px 28px; margin-bottom: 22px;
		display: flex; align-items: center; justify-content: space-between;
		box-shadow: 0 6px 24px rgba(15,36,68,.45); color:#fff;
	}
	.fd-header h2 { margin:0 0 3px; font-size:21px; font-weight:800; color:#fff; letter-spacing:-.3px; }
	.fd-header .fd-sub { font-size:12px; opacity:.7; font-weight:500; }
	.fd-header .fd-date-pill {
		background:rgba(255,255,255,.18); border-radius:20px;
		padding:4px 12px; font-size:11px; font-weight:600; color:#fff;
	}
	.fd-header .fd-icon { font-size:50px; opacity:.2; line-height:1; }

	/* Section title */
	.fd-section {
		font-size:11px; font-weight:800; color:#374151;
		margin:22px 0 10px; padding-bottom:8px;
		border-bottom:2px solid #e5e7eb;
		display:flex; align-items:center; gap:8px;
		text-transform:uppercase; letter-spacing:.6px;
	}
	.fd-section .cnt {
		border-radius:20px; padding:1px 9px;
		font-size:10px; font-weight:800; color:#fff;
		background:#ef4444;
	}
	.fd-section .cnt.ok     { background:#10b981; }
	.fd-section .cnt.orange { background:#f97316; }
	.fd-section .cnt.amber  { background:#eab308; }
	.fd-section .cnt.blue   { background:#2563eb; }

	/* ── Alert cards grid ── */
	.fd-alert-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
		gap: 10px;
		margin-bottom: 4px;
	}

	/* Base alert card */
	.fd-alert-card {
		border-radius: 10px;
		padding: 14px 16px;
		border-left: 4px solid;
		display: flex; flex-direction: column; gap: 5px;
		cursor: pointer;
		transition: transform .15s, box-shadow .15s;
		text-decoration: none;
	}
	.fd-alert-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 18px rgba(0,0,0,.13);
	}

	/* Urgency variants */
	.fd-alert-card.overdue  { background:#fef2f2; border-color:#ef4444; }
	.fd-alert-card.urgent   { background:#fff7ed; border-color:#f97316; }
	.fd-alert-card.upcoming { background:#fefce8; border-color:#eab308; }

	/* Alert card inner elements */
	.fd-alert-card .ac-urgency {
		font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.5px;
	}
	.fd-alert-card.overdue  .ac-urgency { color:#dc2626; }
	.fd-alert-card.urgent   .ac-urgency { color:#ea580c; }
	.fd-alert-card.upcoming .ac-urgency { color:#ca8a04; }

	.fd-alert-card .ac-vehicle {
		font-size:14px; font-weight:800; color:#111827;
		display:flex; align-items:center; gap:5px;
	}
	.fd-alert-card .ac-row {
		display:flex; align-items:center; gap:6px;
		font-size:12px; color:#6b7280;
	}
	.fd-alert-card .ac-row strong { color:#374151; font-weight:700; }
	.fd-alert-card .ac-date-row {
		display:flex; align-items:center; gap:6px;
		margin-top:3px;
	}
	.fd-alert-card .ac-date {
		font-size:12px; font-weight:700;
		background:rgba(0,0,0,.06); border-radius:6px;
		padding:2px 8px;
	}
	.fd-alert-card.overdue  .ac-date { color:#ef4444; }
	.fd-alert-card.urgent   .ac-date { color:#f97316; }
	.fd-alert-card.upcoming .ac-date { color:#ca8a04; }
	.fd-alert-card .ac-days {
		font-size:11px; font-weight:600; color:#9ca3af;
	}

	.fd-no-alert {
		background:#f0fdf4; border:1.5px solid #bbf7d0;
		border-radius:10px; padding:16px;
		text-align:center; color:#15803d; font-weight:600; font-size:13px;
	}

	/* KPI cards */
	.fd-kpi-grid {
		display:grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap:13px;
	}
	.fd-kpi {
		background:#fff; border-radius:12px; padding:16px 14px 12px;
		border:1px solid #e5e7eb; border-top:4px solid;
		box-shadow:0 1px 4px rgba(0,0,0,.06);
		transition:box-shadow .15s, transform .15s;
	}
	.fd-kpi:hover { box-shadow:0 6px 16px rgba(0,0,0,.1); transform:translateY(-2px); }
	.fd-kpi .k-icon { font-size:22px; margin-bottom:9px; line-height:1; }
	.fd-kpi .k-lbl  { font-size:10px; color:#6b7280; font-weight:700; text-transform:uppercase; letter-spacing:.4px; margin-bottom:5px; }
	.fd-kpi .k-val  { font-size:20px; font-weight:800; color:#111827; line-height:1; }
	.fd-kpi .k-sub  { font-size:11px; color:#9ca3af; margin-top:4px; }

	/* Fuel table */
	.fd-table-wrap { overflow-x:auto; border-radius:12px; border:1px solid #e5e7eb; }
	.fd-table {
		width:100%; border-collapse:collapse; font-size:13px;
		background:#fff; border-radius:12px; overflow:hidden;
	}
	.fd-table thead tr { background:linear-gradient(90deg,#1e3a5f,#1d4ed8); }
	.fd-table thead th {
		padding:10px 14px; text-align:left; color:#fff;
		font-size:11px; font-weight:700; letter-spacing:.5px;
		text-transform:uppercase; white-space:nowrap;
	}
	.fd-table tbody tr { border-bottom:1px solid #f3f4f6; transition:background .12s; }
	.fd-table tbody tr:last-child { border-bottom:none; }
	.fd-table tbody tr:hover { background:#f8faff; }
	.fd-table td { padding:10px 14px; color:#374151; white-space:nowrap; }
	.fd-table td.rank { font-size:16px; text-align:center; width:36px; }
	.fd-table td.veh  { font-weight:700; color:#111827; max-width:140px; overflow:hidden; text-overflow:ellipsis; }
	.fd-table td.num  { font-weight:600; }
	.fd-table td.cost { font-weight:700; color:#111827; }
	.fd-bar-track { background:#f3f4f6; border-radius:20px; height:8px; overflow:hidden; min-width:80px; }
	.fd-bar       { height:8px; border-radius:20px; transition:width .4s ease; }

	/* Expense breakdown cards */
	.fd-exp-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(280px,1fr)); gap:12px; }
	.fd-exp-card {
		background:#fff; border-radius:12px; padding:16px;
		border:1px solid #e5e7eb; box-shadow:0 1px 4px rgba(0,0,0,.06);
		transition:box-shadow .15s;
	}
	.fd-exp-card:hover { box-shadow:0 6px 16px rgba(0,0,0,.1); }
	.fd-exp-card .ec-veh   { font-size:14px; font-weight:800; color:#111827; margin-bottom:10px; }
	.fd-exp-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
	.fd-exp-row .er-lbl    { font-size:11px; font-weight:600; color:#6b7280; width:54px; flex-shrink:0; }
	.fd-exp-row .er-wrap   { flex:1; background:#f3f4f6; border-radius:20px; height:7px; overflow:hidden; }
	.fd-exp-row .er-bar    { height:7px; border-radius:20px; }
	.fd-exp-row .er-val    { font-size:11px; font-weight:700; width:60px; text-align:right; flex-shrink:0; }
	.fd-exp-total {
		display:flex; justify-content:space-between; align-items:center;
		margin-top:10px; padding-top:8px; border-top:1px solid #f3f4f6;
	}
	.fd-exp-total .et-lbl { font-size:11px; font-weight:700; color:#6b7280; text-transform:uppercase; }
	.fd-exp-total .et-val { font-size:16px; font-weight:800; color:#111827; }

	/* Quick links */
	.fd-links { display:flex; flex-wrap:wrap; gap:9px; }
	.fd-btn {
		display:inline-flex; align-items:center; gap:6px;
		padding:8px 15px; border-radius:8px; font-size:12px; font-weight:700;
		text-decoration:none; transition:all .15s; cursor:pointer;
	}
	.fd-btn:hover { text-decoration:none; transform:translateY(-1px); box-shadow:0 4px 10px rgba(0,0,0,.1); }
	.fd-btn.fuel       { background:#fff7ed; color:#c2410c; border:1.5px solid #fed7aa; }
	.fd-btn.repair     { background:#fef2f2; color:#b91c1c; border:1.5px solid #fecaca; }
	.fd-btn.service    { background:#f0fdf4; color:#15803d; border:1.5px solid #bbf7d0; }
	.fd-btn.tyre       { background:#faf5ff; color:#7c3aed; border:1.5px solid #e9d5ff; }
	.fd-btn.battery    { background:#fffbeb; color:#d97706; border:1.5px solid #fde68a; }
	.fd-btn.compliance { background:#eff6ff; color:#1d4ed8; border:1.5px solid #bfdbfe; }
	.fd-btn.finance    { background:#f0fdfa; color:#0f766e; border:1.5px solid #99f6e4; }

	@media (max-width:768px) {
		.fd-kpi-grid  { grid-template-columns:repeat(2,1fr); }
		.fd-alert-grid { grid-template-columns:1fr; }
		.fd-exp-grid  { grid-template-columns:1fr; }
		.fd-header { flex-direction:column; align-items:flex-start; gap:10px; }
		.fd-header .fd-icon { display:none; }
	}
	`);
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function render_skeleton(main) {
	let today_str = frappe.datetime.str_to_user(frappe.datetime.get_today());
	$(main).html(`
	<div class="fd">

		<!-- Header -->
		<div class="fd-header">
			<div>
				<h2>🚛 Fleet Dashboard</h2>
				<div class="fd-sub">Maintenance · Expenses · Compliance · Vehicle Analytics</div>
			</div>
			<div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px">
				<span class="fd-date-pill">📅 ${today_str}</span>
				<span class="fd-icon">🔧</span>
			</div>
		</div>

		<!-- ── ALERT SECTION 1: Service Due ── -->
		<div class="fd-section" style="border-color:#10b981">
			🛠️ Service Due Alerts
			<span id="fd-svc-cnt" class="cnt ok" style="display:none"></span>
		</div>
		<div id="fd-svc-alerts" class="fd-alert-grid">
			<div style="color:#9ca3af;font-size:13px;padding:6px;grid-column:1/-1">Loading…</div>
		</div>

		<!-- ── ALERT SECTION 2: Compliance Expiry ── -->
		<div class="fd-section" style="border-color:#2563eb">
			📋 Compliance Expiry Alerts
			<span id="fd-comp-cnt" class="cnt blue" style="display:none"></span>
		</div>
		<div id="fd-comp-alerts" class="fd-alert-grid">
			<div style="color:#9ca3af;font-size:13px;padding:6px;grid-column:1/-1">Loading…</div>
		</div>

		<!-- ── ALERT SECTION 3: Battery Replacement ── -->
		<div class="fd-section" style="border-color:#f97316">
			🔋 Battery Replacement Alerts
			<span id="fd-bat-cnt" class="cnt orange" style="display:none"></span>
		</div>
		<div id="fd-bat-alerts" class="fd-alert-grid">
			<div style="color:#9ca3af;font-size:13px;padding:6px;grid-column:1/-1">Loading…</div>
		</div>

		<!-- ── KPI Cards ── -->
		<div class="fd-section">📊 KPIs — Month to Date</div>
		<div id="fd-kpis" class="fd-kpi-grid">${kpi_skeleton()}</div>

		<!-- ── Fuel Consumers ── -->
		<div class="fd-section">
			⛽ Top Fuel Consumers
			<span class="cnt blue">All Time</span>
		</div>
		<div id="fd-fuel-table">
			<div style="color:#9ca3af;font-size:13px;padding:6px">Loading…</div>
		</div>

		<!-- ── Expense Breakdown ── -->
		<div class="fd-section">
			💰 Vehicle Expense Breakdown
			<span class="cnt blue">All Time</span>
		</div>
		<div id="fd-exp-grid" class="fd-exp-grid">
			<div style="color:#9ca3af;font-size:13px;padding:6px">Loading…</div>
		</div>

		<!-- ── Quick Links ── -->
		<div class="fd-section">🔗 Quick Access</div>
		<div class="fd-links">
			<a href="/app/fuel-urea-expenses"  class="fd-btn fuel">⛽ Fuel / Urea</a>
			<a href="/app/repair-expenses"     class="fd-btn repair">🔧 Repair Expenses</a>
			<a href="/app/service-logs"        class="fd-btn service">🛠️ Service Logs</a>
			<a href="/app/tyre-expenses"       class="fd-btn tyre">🛞 Tyre Expenses</a>
			<a href="/app/battery-expenses"    class="fd-btn battery">🔋 Battery Expenses</a>
			<a href="/app/compliances"         class="fd-btn compliance">📋 Compliances</a>
			<a href="/app/vehicle-finance"     class="fd-btn finance">💳 Vehicle Finance</a>
			<a href="/app/alert-settings"      class="fd-btn finance">⚙️ Alert Settings</a>
			<a href="/app/alert-center"        class="fd-btn compliance">🔔 Alert Center</a>
		</div>

	</div>`);
}

function kpi_skeleton() {
	let colors = ["#ff6b35","#ef4444","#10b981","#8b5cf6","#f97316","#2563eb"];
	let icons  = ["⛽","🔧","🛠️","🛞","🔋","💳"];
	return icons.map(function (ic, i) {
		return `<div class="fd-kpi" style="border-top-color:${colors[i]}">
			<div class="k-icon">${ic}</div>
			<div class="k-lbl">Loading…</div>
			<div class="k-val" style="color:#d1d5db">—</div>
		</div>`;
	}).join("");
}

// ─── Master loader ────────────────────────────────────────────────────────────

function load_all(main) {
	load_service_alerts(main);
	load_compliance_alerts(main);
	load_battery_alerts(main);
	load_kpis(main);
	load_fuel_table(main);
	load_expense_breakdown(main);
}

// ─── Helper: urgency class + labels ──────────────────────────────────────────

function get_urgency(date_str, today, in_7) {
	if (date_str < today)    return { cls: "overdue",  icon: "🔴", label: "OVERDUE" };
	if (date_str <= in_7)    return { cls: "urgent",   icon: "🟠", label: "DUE SOON" };
	return                          { cls: "upcoming", icon: "🟡", label: "UPCOMING" };
}

function days_text(date_str, today) {
	let diff = frappe.datetime.get_diff(date_str, today);
	if (diff < 0)   return Math.abs(diff) + " day" + (Math.abs(diff) > 1 ? "s" : "") + " overdue";
	if (diff === 0) return "Due today!";
	return "In " + diff + " day" + (diff > 1 ? "s" : "");
}

function make_alert_card(opts, today, in_7) {
	/*
	  opts: { vehicle, date, name, doctype, rows: [{label, value}] }
	  rows: array of {label, value} detail lines
	*/
	let urg = get_urgency(opts.date, today, in_7);
	let dt  = days_text(opts.date, today);
	let v   = frappe.utils.escape_html(opts.vehicle || "Unknown Vehicle");
	let dn  = frappe.utils.escape_html(opts.doctype);
	let nm  = frappe.utils.escape_html(opts.name);

	let detail_rows = (opts.rows || []).map(function (r) {
		return `<div class="ac-row">
			<span>${frappe.utils.escape_html(r.label)}:</span>
			<strong>${frappe.utils.escape_html(r.value || "—")}</strong>
		</div>`;
	}).join("");

	return `
	<div class="fd-alert-card ${urg.cls}" data-route="Form/${dn}/${nm}">
		<span class="ac-urgency">${urg.icon} ${urg.label}</span>
		<span class="ac-vehicle">🚛 ${v}</span>
		${detail_rows}
		<div class="ac-date-row">
			<span class="ac-date">📅 ${frappe.datetime.str_to_user(opts.date)}</span>
			<span class="ac-days">${dt}</span>
		</div>
	</div>`;
}

function render_alert_section(container_id, badge_id, main, cards_html, count) {
	let $c = $(main).find("#" + container_id);
	let $b = $(main).find("#" + badge_id);

	if (!count) {
		$c.html(`<div class="fd-no-alert">✅ No alerts in the next 30 days</div>`);
		$b.hide();
	} else {
		$c.html(cards_html);
		$b.text(count + " alert" + (count > 1 ? "s" : "")).show();
		$c.find(".fd-alert-card").on("click", function () {
			frappe.set_route($(this).data("route").split("/"));
		});
	}
}

// ─── Alert 1: Service Due (from Service Logs — next_service_date) ─────────────

function load_service_alerts(main) {
	frappe.call({
		method: "logicore.logicore.doctype.alert_settings.alert_settings.get_alert_dashboard_rows",
		args: { limit: 50 },
		callback: function (r) {
			let rows = (r.message || []).filter(function (row) {
				return row.doctype === "Service Logs";
			});
			let today = frappe.datetime.get_today();
			let in_7  = frappe.datetime.add_days(today, 7);
			let cards = rows.map(function (row) {
				let detail_rows = [];
				(row.details || []).forEach(function (item) {
					if (item && item[0])
						detail_rows.push({ label: item[0], value: item[1] });
				});
				return make_alert_card({
					vehicle: row.vehicle_no || row.vehicle || row.parent_name,
					date:    row.date_value || row.next_date || row.next_service_date,
					name:    row.parent_name || row.name,
					doctype: "Service Logs",
					rows:    detail_rows,
				}, today, in_7);
			}).join("");
			render_alert_section("fd-svc-alerts", "fd-svc-cnt", main, cards, rows.length);
		},
		error: function () {
			$(main).find("#fd-svc-alerts").html(
				`<div style="color:#ef4444;font-size:13px;padding:6px">Could not load service alerts.</div>`
			);
		},
	});
}

// ─── Alert 2: Compliance Expiry (from Compliances — expiry_date) ──────────────

function load_compliance_alerts(main) {
	let today = frappe.datetime.get_today();
	let in_7  = frappe.datetime.add_days(today, 7);
	let in_30 = frappe.datetime.add_days(today, 30);

	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Compliances",
			fields: ["name", "vehicle", "expiry_date", "document_type",
			         "issue_date", "amount", "payment_mode"],
			filters: [
				["expiry_date", ">=", "2000-01-01"],
				["expiry_date", "<=", in_30],
			],
			order_by: "expiry_date asc",
			limit: 50,
		},
		callback: function (r) {
			let rows = r.message || [];
			let cards = rows.map(function (row) {
				let detail_rows = [];
				if (row.document_type)
					detail_rows.push({ label: "Document", value: row.document_type });
				if (row.issue_date)
					detail_rows.push({ label: "Issued On", value: frappe.datetime.str_to_user(row.issue_date) });
				if (row.amount)
					detail_rows.push({ label: "Amount Paid", value: fmt_inr(row.amount) });
				if (row.payment_mode)
					detail_rows.push({ label: "Payment", value: row.payment_mode });
				return make_alert_card({
					vehicle: row.vehicle,
					date:    row.expiry_date,
					name:    row.name,
					doctype: "Compliances",
					rows:    detail_rows,
				}, today, in_7);
			}).join("");
			render_alert_section("fd-comp-alerts", "fd-comp-cnt", main, cards, rows.length);
		},
		error: function () {
			$(main).find("#fd-comp-alerts").html(
				`<div style="color:#ef4444;font-size:13px;padding:6px">Could not load compliance alerts.</div>`
			);
		},
	});
}

// ─── Alert 3: Battery Replacement (from Battery Expenses — replacement_date) ──

function load_battery_alerts(main) {
	let today = frappe.datetime.get_today();
	let in_7  = frappe.datetime.add_days(today, 7);
	let in_30 = frappe.datetime.add_days(today, 30);

	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Battery Expenses",
			fields: ["name", "vehicle_id", "replacement_date", "brand",
			         "battery_regn_no", "installation_date",
			         "warranty_months", "actual_life_achieved"],
			filters: [
				["replacement_date", ">=", "2000-01-01"],
				["replacement_date", "<=", in_30],
			],
			order_by: "replacement_date asc",
			limit: 50,
		},
		callback: function (r) {
			let rows = r.message || [];
			let cards = rows.map(function (row) {
				let detail_rows = [];
				if (row.brand)
					detail_rows.push({ label: "Brand", value: row.brand });
				if (row.battery_regn_no)
					detail_rows.push({ label: "Battery No", value: row.battery_regn_no });
				if (row.installation_date)
					detail_rows.push({ label: "Installed On", value: frappe.datetime.str_to_user(row.installation_date) });
				if (row.warranty_months)
					detail_rows.push({ label: "Warranty", value: row.warranty_months + " months" });
				if (row.actual_life_achieved)
					detail_rows.push({ label: "Life Achieved", value: row.actual_life_achieved });
				return make_alert_card({
					vehicle: row.vehicle_id,
					date:    row.replacement_date,
					name:    row.name,
					doctype: "Battery Expenses",
					rows:    detail_rows,
				}, today, in_7);
			}).join("");
			render_alert_section("fd-bat-alerts", "fd-bat-cnt", main, cards, rows.length);
		},
		error: function () {
			$(main).find("#fd-bat-alerts").html(
				`<div style="color:#ef4444;font-size:13px;padding:6px">Could not load battery alerts.</div>`
			);
		},
	});
}

// ─── KPI Cards ────────────────────────────────────────────────────────────────

function load_kpis(main) {
	let today       = frappe.datetime.get_today();
	let month_start = frappe.datetime.month_start();

	let kpis = [
		{ icon:"⛽", label:"Fuel Cost MTD",     color:"#ff6b35", doctype:"Fuel Urea Expenses", field:"expense_amount", date_f:"date",          sub:"Fuel & Urea" },
		{ icon:"🔧", label:"Repair Cost MTD",   color:"#ef4444", doctype:"Repair Expenses",    field:"amount",         date_f:"date",          sub:"All repairs" },
		{ icon:"🛠️", label:"Service Cost MTD", color:"#10b981", doctype:"Service Logs",       field:"total_amount",   date_f:"voucher_date",   sub:"Vehicle services" },
		{ icon:"🛞", label:"Tyre Cost MTD",     color:"#8b5cf6", doctype:"Tyre Expenses",      field:"cost",           date_f:"purchase_date", sub:"Tyre purchases" },
		{ icon:"🔋", label:"Batteries MTD",     color:"#f97316", doctype:"Battery Expenses",   field:null,             date_f:"purchase_date", sub:"Replacements", count_only:true },
		{ icon:"💳", label:"Outstanding Loans", color:"#2563eb", doctype:"Vehicle Finance",    field:"outstanding_loan", date_f:null,          sub:"Total outstanding" },
	];

	let html = kpis.map(function (k, i) {
		return `<div class="fd-kpi" id="fd-kpi-${i}" style="border-top-color:${k.color}">
			<div class="k-icon">${k.icon}</div>
			<div class="k-lbl">${k.label}</div>
			<div class="k-val" style="color:${k.color}">…</div>
			<div class="k-sub">${k.sub}</div>
		</div>`;
	}).join("");
	$(main).find("#fd-kpis").html(html);

	kpis.forEach(function (k, i) {
		let filters = [];
		if (k.date_f) {
			filters.push([k.date_f, ">=", month_start]);
			filters.push([k.date_f, "<=", today]);
		}
		if (k.count_only) {
			frappe.call({
				method: "frappe.client.get_count",
				args: { doctype: k.doctype, filters: filters },
				callback: function (r) {
					$(main).find("#fd-kpi-" + i + " .k-val").text((r.message || 0) + " units");
				},
			});
		} else {
			frappe.call({
				method: "frappe.client.get_list",
				args: { doctype: k.doctype, fields: [k.field], filters: filters, limit: 0 },
				callback: function (r) {
					let total = (r.message || []).reduce(function (s, row) {
						return s + (parseFloat(row[k.field]) || 0);
					}, 0);
					$(main).find("#fd-kpi-" + i + " .k-val").text(fmt_inr(total));
				},
			});
		}
	});
}

// ─── Fuel Consumers Table ─────────────────────────────────────────────────────

function load_fuel_table(main) {
	frappe.call({
		method: "logicore.logicore.api.get_fleet_vehicle_fuel",
		callback: function (r) {
			let rows = r.message || [];
			if (!rows.length) {
				$(main).find("#fd-fuel-table").html(
					`<div style="color:#9ca3af;font-size:13px;padding:10px">No fuel data available yet.</div>`
				);
				return;
			}
			let max_cost = rows[0].total_cost || 1;
			let medals   = ["🥇","🥈","🥉"];

			let tr_html = rows.map(function (row, i) {
				let pct       = Math.round((row.total_cost / max_cost) * 100);
				let kpl_color = row.avg_kpl >= 5 ? "#10b981" : row.avg_kpl >= 3.5 ? "#f59e0b" : "#ef4444";
				return `<tr>
					<td class="rank">${medals[i] || (i + 1)}</td>
					<td class="veh" title="${frappe.utils.escape_html(row.vehicle)}">${frappe.utils.escape_html(row.vehicle)}</td>
					<td class="num">${row.fills || 0}</td>
					<td class="num">${fmt_liters(row.total_liters)}</td>
					<td class="num" style="color:${kpl_color};font-weight:700">${row.avg_kpl ? row.avg_kpl.toFixed(2) : "—"}</td>
					<td class="cost">${fmt_inr(row.total_cost)}</td>
					<td style="min-width:100px">
						<div class="fd-bar-track">
							<div class="fd-bar" style="width:${pct}%;background:#ff6b35"></div>
						</div>
					</td>
				</tr>`;
			}).join("");

			$(main).find("#fd-fuel-table").html(`
			<div class="fd-table-wrap">
				<table class="fd-table">
					<thead><tr>
						<th>#</th><th>Vehicle</th><th>Fills</th>
						<th>Total Liters</th><th>Avg KPL</th>
						<th>Fuel Cost</th><th style="min-width:100px">Cost Bar</th>
					</tr></thead>
					<tbody>${tr_html}</tbody>
				</table>
			</div>`);
		},
	});
}

// ─── Vehicle Expense Breakdown ────────────────────────────────────────────────

function load_expense_breakdown(main) {
	frappe.call({
		method: "logicore.logicore.api.get_fleet_vehicle_expenses",
		callback: function (r) {
			let rows = r.message || [];
			if (!rows.length) {
				$(main).find("#fd-exp-grid").html(
					`<div style="color:#9ca3af;font-size:13px;padding:10px">No expense data available yet.</div>`
				);
				return;
			}
			let max_total = rows[0].total || 1;
			let exp_cfg   = [
				{ key:"fuel",    color:"#ff6b35", label:"Fuel" },
				{ key:"repair",  color:"#ef4444", label:"Repair" },
				{ key:"service", color:"#10b981", label:"Service" },
				{ key:"tyre",    color:"#8b5cf6", label:"Tyre" },
			];

			let cards = rows.map(function (row) {
				let bars = exp_cfg.map(function (cfg) {
					let pct = row.total > 0 ? Math.round((row[cfg.key] / row.total) * 100) : 0;
					return `<div class="fd-exp-row">
						<span class="er-lbl">${cfg.label}</span>
						<div class="er-wrap"><div class="er-bar" style="width:${pct}%;background:${cfg.color}"></div></div>
						<span class="er-val" style="color:${cfg.color}">${fmt_inr(row[cfg.key])}</span>
					</div>`;
				}).join("");

				let total_pct = Math.round((row.total / max_total) * 100);
				let v_safe    = frappe.utils.escape_html(row.vehicle);
				return `<div class="fd-exp-card">
					<div class="ec-veh">🚛 ${v_safe}</div>
					${bars}
					<div class="fd-exp-total">
						<div>
							<div class="et-lbl">Total Expense</div>
							<div class="fd-bar-track" style="width:80px;margin-top:4px">
								<div class="fd-bar" style="width:${total_pct}%;background:#1d4ed8"></div>
							</div>
						</div>
						<div class="et-val">${fmt_inr(row.total)}</div>
					</div>
				</div>`;
			}).join("");

			$(main).find("#fd-exp-grid").html(cards);
		},
	});
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmt_inr(value) {
	let num = parseFloat(value) || 0;
	if (num === 0) return "₹0";
	if (num >= 10000000) return "₹" + (num / 10000000).toFixed(2) + " Cr";
	if (num >= 100000)   return "₹" + (num / 100000).toFixed(2) + " L";
	return "₹" + num.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function fmt_liters(value) {
	let n = parseFloat(value) || 0;
	if (n === 0) return "0 L";
	if (n >= 1000) return (n / 1000).toFixed(1) + " kL";
	return n.toFixed(0) + " L";
}

function fmt_num(value) {
	let n = parseFloat(value) || 0;
	return n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}
