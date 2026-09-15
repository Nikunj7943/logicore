frappe.pages["alert-center"] = frappe.pages["alert-center"] || {};

frappe.pages["alert-center"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Alert Center",
		single_column: true,
	});

	page.add_action_item(__("Refresh"), function () {
		render_alert_center(page.main);
		load_alert_center(page.main);
	});

	page.add_action_item(__("Alert Settings"), function () {
		frappe.set_route("Form", "Alert Settings", "Alert Settings");
	});

	inject_styles();
	render_alert_center(page.main);
	load_alert_center(page.main);
};

frappe.pages["alert-center"].on_page_show = function (wrapper) {
	const page = wrapper.page;
	if (page && page.main) {
		render_alert_center(page.main);
		load_alert_center(page.main);
	}
};

function inject_styles() {
	frappe.dom.set_style(`
	.acz { padding: 2px 2px 30px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
	.acz-head {
		background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 60%, #0284c7 100%);
		border-radius: 10px; padding: 12px 18px; color: #fff; margin-bottom: 10px;
		box-shadow: 0 4px 14px rgba(15,23,42,.18);
		display:flex; align-items:center; justify-content:space-between; gap:16px;
	}
	.acz-title { font-size: 16px; font-weight: 800; margin: 0; letter-spacing:-.3px; }
	.acz-sub { font-size: 12px; opacity: .8; line-height: 1.4; margin-top:2px; }
	.acz-pill {
		display:inline-flex; align-items:center; gap:5px; background:rgba(255,255,255,.15);
		border:1px solid rgba(255,255,255,.2); padding: 4px 10px; border-radius:999px;
		font-size:11px; font-weight:700; white-space:nowrap;
	}
	.acz-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(140px,1fr)); gap: 8px; margin: 8px 0 10px; }
	.acz-stat {
		background: var(--card-bg, #fff);
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius:10px; padding:10px 14px;
		box-shadow:0 1px 3px rgba(0,0,0,.04);
	}
	.acz-stat .l { font-size:10px; font-weight:800; color:var(--text-muted, #6b7280); text-transform:uppercase; letter-spacing:.5px; }
	.acz-stat .v { margin-top:4px; font-size:20px; font-weight:900; color:var(--text-color, #111827); }
	.acz-stat .s { margin-top:2px; font-size:11px; color:var(--text-muted, #9ca3af); }
	.acz-section-title {
		font-size:10px; font-weight:900; color:var(--text-muted, #6b7280); text-transform:uppercase; letter-spacing:.7px;
		margin-bottom:5px;
	}
	.acz-filterrow {
		display:flex; justify-content:space-between; align-items:flex-start;
		gap:12px; margin-bottom:10px; flex-wrap:wrap;
	}
	.acz-bar { display:flex; flex-wrap:wrap; gap:6px; margin:0; }
	.acz-chip {
		border:1px solid var(--border-color, #d1d5db);
		background: var(--control-bg, #fff);
		color: var(--text-color, #374151);
		border-radius:999px; padding:4px 10px; font-size:12px; font-weight:700; cursor:pointer; transition:.14s;
	}
	.acz-chip.active { background:#1d4ed8; border-color:#1d4ed8; color:#fff; box-shadow:0 3px 10px rgba(29,78,216,.25); }
	.acz-chip.status.overdue.active  { background:#dc2626; border-color:#dc2626; box-shadow:0 3px 10px rgba(220,38,38,.25); }
	.acz-chip.status.urgent.active   { background:#f59e0b; border-color:#f59e0b; box-shadow:0 3px 10px rgba(245,158,11,.25); }
	.acz-chip.status.upcoming.active { background:#16a34a; border-color:#16a34a; box-shadow:0 3px 10px rgba(22,163,74,.25); }
	.acz-toolbar { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:10px; }
	.acz-search {
		flex:1; min-width:220px; height:34px;
		border:1px solid var(--border-color, #d1d5db);
		border-radius:8px; padding:0 10px; font-size:13px; outline:none;
		background: var(--control-bg, #fff);
		color: var(--text-color, #111827);
	}
	.acz-search:focus { border-color:#2563eb; box-shadow:0 0 0 2px rgba(37,99,235,.15); }
	.acz-table-wrap {
		background: var(--card-bg, #fff);
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius:10px; overflow:hidden;
		box-shadow:0 1px 3px rgba(0,0,0,.06);
	}
	.acz-table { width:100%; border-collapse:collapse; font-size:13px; }
	.acz-table thead tr { background: linear-gradient(90deg,#111827,#1d4ed8); }
	.acz-table th {
		color:#fff; text-align:left; padding:10px 12px; font-size:11px; letter-spacing:.5px;
		text-transform:uppercase; white-space:nowrap;
	}
	.acz-table td { padding:10px 12px; border-bottom:1px solid var(--border-color, #f3f4f6); vertical-align:middle; }
	.acz-table td:nth-child(2) { vertical-align:top; }
	.acz-row { cursor:pointer; transition: background .12s; }
	.acz-row:hover { background: var(--fg-hover-color, rgba(17,24,39,.04)) !important; }

	/* Light theme row tints */
	.acz-row.overdue  { background:#fff5f5; }
	.acz-row.urgent   { background:#fffaf0; }
	.acz-row.upcoming { background:#f8fff9; }

	/* Dark theme row tints */
	[data-theme="dark"] .acz-row.overdue  { background: rgba(220,38,38,.12); }
	[data-theme="dark"] .acz-row.urgent   { background: rgba(245,158,11,.10); }
	[data-theme="dark"] .acz-row.upcoming { background: rgba(22,163,74,.10); }

	.acz-type {
		display:inline-flex; align-items:center; padding:3px 8px; border-radius:999px;
		font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.4px;
	}
	.acz-type.overdue  { background:#fee2e2; color:#b91c1c; }
	.acz-type.urgent   { background:#ffedd5; color:#c2410c; }
	.acz-type.upcoming { background:#dcfce7; color:#166534; }
	[data-theme="dark"] .acz-type.overdue  { background:rgba(220,38,38,.25); color:#fca5a5; }
	[data-theme="dark"] .acz-type.urgent   { background:rgba(245,158,11,.22); color:#fcd34d; }
	[data-theme="dark"] .acz-type.upcoming { background:rgba(22,163,74,.22); color:#86efac; }

	.acz-cat {
		display:inline-flex; margin-top:5px; padding:2px 7px; border-radius:999px;
		font-size:10px; font-weight:800; letter-spacing:.3px; text-transform:uppercase;
		background:#eef2ff; color:#3730a3;
	}
	.acz-cat.Service    { background:#dbeafe; color:#1d4ed8; }
	.acz-cat.Compliance { background:#ede9fe; color:#6d28d9; }
	.acz-cat.Battery    { background:#dcfce7; color:#15803d; }
	.acz-cat.Tyre       { background:#fef3c7; color:#b45309; }
	[data-theme="dark"] .acz-cat            { background:rgba(99,102,241,.2); color:#a5b4fc; }
	[data-theme="dark"] .acz-cat.Service    { background:rgba(29,78,216,.25); color:#93c5fd; }
	[data-theme="dark"] .acz-cat.Compliance { background:rgba(109,40,217,.25); color:#c4b5fd; }
	[data-theme="dark"] .acz-cat.Battery    { background:rgba(21,128,61,.25); color:#86efac; }
	[data-theme="dark"] .acz-cat.Tyre       { background:rgba(180,83,9,.25); color:#fcd34d; }

	.acz-title-cell { font-weight:800; color:var(--text-color, #111827); }
	.acz-veh  { color:var(--text-color, #374151); font-weight:700; }
	.acz-date { font-weight:800; color:var(--text-color, #111827); }
	.acz-days { color:var(--text-muted, #6b7280); font-size:11px; margin-top:2px; }
	.acz-details { color:var(--text-muted, #4b5563); font-size:11px; line-height:1.4; margin-top:3px; }
	.acz-actions { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; }
	.acz-open { white-space:nowrap; }
	.acz-empty {
		padding:18px; text-align:center; color:#15803d; background:#f0fdf4;
		border:1px solid #bbf7d0; border-radius:10px; font-weight:700;
	}
	[data-theme="dark"] .acz-empty { background:rgba(22,163,74,.15); color:#86efac; border-color:rgba(22,163,74,.3); }

	@media (max-width:900px) {
		.acz-table thead { display:none; }
		.acz-table, .acz-table tbody, .acz-table tr, .acz-table td { display:block; width:100%; }
		.acz-table tr { border-bottom:1px solid var(--border-color, #eef2f7); }
		.acz-table td { border-bottom:none; padding:8px 12px; }
	}
	`);
}

function render_alert_center(main) {
	$(main).html(`
	<div class="acz">
		<div class="acz-head">
			<div>
				<div class="acz-title">Alert Center</div>
				<div class="acz-sub">Maintenance alerts, compliance expiry, battery warranty, and tyre expiry.</div>
			</div>
			<div class="acz-pill">🕒 Updated live</div>
		</div>
		<div class="acz-grid" id="acz-stats"></div>
		<div class="acz-filterrow">
			<div>
				<div class="acz-section-title">By Category</div>
				<div class="acz-bar" id="acz-category-filters"></div>
			</div>
			<div>
				<div class="acz-section-title">By Status</div>
				<div class="acz-bar" id="acz-status-filters"></div>
			</div>
		</div>
		<div class="acz-toolbar">
			<input id="acz-search" class="acz-search" type="search" placeholder="Search vehicle, title, document, or details...">
		</div>
		<div id="acz-content">
			<div class="acz-empty">Loading alerts…</div>
		</div>
	</div>`);
}

function load_alert_center(main) {
	frappe.call({
		method: "logicore.logicore.doctype.alert_settings.alert_settings.get_alert_dashboard_rows",
		args: { limit: 200 },
		callback(r) {
			const rows = r.message || [];
			render_alert_center_data(main, rows);
		},
		error() {
			$(main).find("#acz-content").html('<div class="acz-empty" style="color:#b91c1c;background:#fef2f2;border-color:#fecaca">Could not load alerts.</div>');
		},
	});
}

function render_alert_center_data(main, rows) {
	const normalized = (rows || []).map(function (row) {
		const dateValue = row.date_value || row.next_date || row.next_service_date || row.expiry_date || row.replacement_date;
		const daysDelta = row.days_delta;
		const urgency = row.urgency || (daysDelta < 0 ? "overdue" : daysDelta === 0 ? "urgent" : "upcoming");
		const category = category_label(row.doctype);
		return Object.assign({}, row, { dateValue, urgency, category });
	});

	const stats = {
		total: normalized.length,
		overdue: normalized.filter(row => row.urgency === "overdue").length,
		urgent: normalized.filter(row => row.urgency === "urgent").length,
		upcoming: normalized.filter(row => row.urgency === "upcoming").length,
	};

	$(main).find("#acz-stats").html([
		stat_card("Total Alerts", stats.total, "Across all alert types"),
		stat_card("Overdue", stats.overdue, "Needs attention now"),
		stat_card("Due Soon", stats.urgent, "Within the alert window"),
		stat_card("Upcoming", stats.upcoming, "Still before due date"),
	].join(""));

	// Category chips are derived from whatever doctypes actually have alert rows —
	// so any Source DocType added in Alert Settings shows up here automatically.
	const doctypes_present = Array.from(new Set(normalized.map(row => row.doctype).filter(Boolean)));
	const filters = [{ key: "all", label: "All" }].concat(
		doctypes_present.map(dt => ({ key: dt, label: category_label(dt) }))
	);

	const status_filters = [
		{ key: "all", label: "All Status" },
		{ key: "overdue", label: "Overdue" },
		{ key: "urgent", label: "Due Soon" },
		{ key: "upcoming", label: "Upcoming" },
	];

	$(main).find("#acz-category-filters").html(filters.map((f, i) => `<button class="acz-chip category ${i === 0 ? "active" : ""}" data-filter="${f.key}">${f.label}</button>`).join(""));
	$(main).find("#acz-status-filters").html(status_filters.map((f, i) => `<button class="acz-chip status ${f.key} ${i === 0 ? "active" : ""}" data-filter="${f.key}">${f.label}</button>`).join(""));

	const $search = $(main).find("#acz-search");
	let currentCategory = "all";
	let currentStatus = "all";

	function apply_filter() {
		const q = ($search.val() || "").toLowerCase().trim();
		const filtered = normalized.filter(function (row) {
			const searchable = [
				row.doctype,
				row.title,
				row.vehicle_no,
				row.vehicle,
				row.parent_name,
				row.description,
				(row.details || []).map(function (item) { return Array.isArray(item) ? item.join(" ") : ""; }).join(" "),
			].join(" ").toLowerCase();

			const matchesCategory = currentCategory === "all" || row.doctype === currentCategory;
			const matchesStatus = currentStatus === "all" || row.urgency === currentStatus;
			return matchesCategory && matchesStatus && (!q || searchable.includes(q));
		});

		$(main).find("#acz-content").html(render_table(filtered));
		attach_row_actions(main);
	}

	$(main).find("#acz-category-filters .acz-chip").off("click").on("click", function () {
		$(main).find("#acz-category-filters .acz-chip").removeClass("active");
		$(this).addClass("active");
		currentCategory = $(this).data("filter");
		apply_filter();
	});

	$(main).find("#acz-status-filters .acz-chip").off("click").on("click", function () {
		$(main).find("#acz-status-filters .acz-chip").removeClass("active");
		$(this).addClass("active");
		currentStatus = $(this).data("filter");
		apply_filter();
	});

	$search.off("input").on("input", apply_filter);
	apply_filter();
}

const CATEGORY_LABELS = {
	"Service Logs": "Service",
	"Compliances": "Compliance",
	"Battery Expenses": "Battery",
	"Tyre Expenses": "Tyre",
};

function category_label(doctype) {
	return CATEGORY_LABELS[doctype] || doctype || "Alert";
}

function stat_card(label, value, sub) {
	return `
	<div class="acz-stat">
		<div class="l">${frappe.utils.escape_html(label)}</div>
		<div class="v">${frappe.utils.escape_html(String(value || 0))}</div>
		<div class="s">${frappe.utils.escape_html(sub)}</div>
	</div>`;
}

function render_table(rows) {
	if (!rows.length) {
		return '<div class="acz-empty">No alerts match the current filter.</div>';
	}

	const body = rows.map(function (row) {
		const urgency = row.urgency || "upcoming";
		const row_route = frappe.utils.escape_html(row.route || "");
		const details = (row.details || []).map(function (item) {
			if (Array.isArray(item)) {
				return `<div><strong>${frappe.utils.escape_html(item[0])}:</strong> ${frappe.utils.escape_html(item[1] || "—")}</div>`;
			}
			return "";
		}).join("");

		return `
		<tr class="acz-row ${urgency}" data-route="${row_route}">
			<td>
				<span class="acz-type ${urgency}">${frappe.utils.escape_html(urgency)}</span>
			</td>
			<td>
				<div class="acz-title-cell">${frappe.utils.escape_html(row.title || row.parent_name || row.name || "Alert")}</div>
				<div class="acz-cat ${frappe.utils.escape_html(row.category || category_label(row.doctype))}">${frappe.utils.escape_html(row.category || category_label(row.doctype))}</div>
				<div class="acz-details">${details || "—"}</div>
			</td>
			<td class="acz-veh">${frappe.utils.escape_html(row.vehicle_no || row.vehicle_id || row.vehicle || "—")}</td>
			<td>
				<div class="acz-date">${row.dateValue ? frappe.datetime.str_to_user(row.dateValue) : "—"}</div>
				<div class="acz-days">${day_text(row.days_delta)}</div>
			</td>
			<td>
				<div class="acz-actions">
					<button class="btn btn-xs btn-primary acz-open" data-route="${row_route}">Open</button>
				</div>
			</td>
		</tr>`;
	}).join("");

	return `
	<div class="acz-table-wrap">
		<table class="acz-table">
			<thead>
				<tr>
					<th>Status</th>
					<th>Alert</th>
					<th>Vehicle</th>
					<th>Due Date</th>
					<th>Action</th>
				</tr>
			</thead>
			<tbody>${body}</tbody>
		</table>
	</div>`;
}

function attach_row_actions(main) {
	$(main).find(".acz-open").off("click").on("click", function (event) {
		event.stopPropagation();
		const route = $(this).data("route");
		if (route) frappe.set_route(route.split("/"));
	});

	$(main).find(".acz-row").off("click").on("click", function () {
		const route = $(this).data("route");
		if (route) frappe.set_route(route.split("/"));
	});
}

function day_text(days_delta) {
	if (days_delta < 0) {
		const d = Math.abs(days_delta);
		return `${d} day${d !== 1 ? "s" : ""} overdue`;
	}
	if (days_delta === 0) return "Due today";
	return `In ${days_delta} day${days_delta !== 1 ? "s" : ""}`;
}
