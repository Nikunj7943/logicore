// Staff Attendance Report — Employee/Driver toggle + multi-select filters

// Driver/Employee don't have "Show title field in link" enabled, so the
// default frappe.db.get_link_options() falls back to showing the ID instead
// of the name. Query directly and build the label ourselves instead.
//
// Also: whatever is already selected (e.g. restored from the report's URL on
// page load) must resolve to its name even if it isn't in the default
// top-20 alphabetical list — otherwise the collapsed filter chip shows the
// raw ID until the user happens to search for it. So every call fetches the
// currently selected values by name too, and merges them in.
function _sar_link_search(doctype, name_field, txt, fieldname) {
	const selected =
		(fieldname && frappe.query_report && frappe.query_report.get_filter_value(fieldname)) || [];

	const fetch = (args) =>
		frappe
			.call({
				method: "frappe.client.get_list",
				args: Object.assign({ doctype, fields: ["name", name_field], order_by: `${name_field} asc` }, args),
			})
			.then((r) => r.message || []);

	const calls = [
		txt
			? fetch({
					or_filters: [
						["name", "like", `%${txt}%`],
						[name_field, "like", `%${txt}%`],
					],
					limit_page_length: 20,
			  })
			: fetch({ filters: [], limit_page_length: 20 }),
	];
	if (selected.length) {
		calls.push(fetch({ filters: [["name", "in", selected]], limit_page_length: selected.length }));
	}

	return Promise.all(calls).then((results) => {
		const seen = new Set();
		const merged = [];
		results.flat().forEach((d) => {
			if (seen.has(d.name)) return;
			seen.add(d.name);
			merged.push({ value: d.name, label: d[name_field] || d.name, description: d.name });
		});
		return merged;
	});
}

frappe.query_reports["Staff Attendance Report"] = {
	filters: [
		{
			fieldname: "employee_type",
			label: __("Employee Type"),
			fieldtype: "Select",
			options: "Employee\nDriver",
			default: "Employee",
			reqd: 1,
			on_change: function () {
				const type = frappe.query_report.get_filter_value("employee_type");
				const is_driver = type === "Driver";

				frappe.query_report.set_filter_value("employee", []);
				frappe.query_report.set_filter_value("driver", []);

				const empF = frappe.query_report.get_filter("employee");
				const drvF = frappe.query_report.get_filter("driver");
				if (empF) empF.$wrapper.toggle(!is_driver);
				if (drvF) drvF.$wrapper.toggle(is_driver);
			},
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "MultiSelectList",
			options: "Employee",
			get_data: function (txt) {
				return _sar_link_search("Employee", "employee_name", txt, "employee");
			},
		},
		{
			fieldname: "driver",
			label: __("Driver"),
			fieldtype: "MultiSelectList",
			options: "Driver",
			get_data: function (txt) {
				return _sar_link_search("Driver", "full_name", txt, "driver");
			},
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				const options = [
					"Present",
					"Absent",
					"On Leave With Pay",
					"On Leave Without Pay",
					"Sunday/Holiday",
				];
				return options
					.filter((o) => o.toLowerCase().includes((txt || "").toLowerCase()))
					.map((o) => ({ value: o, label: o, description: "" }));
			},
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		if (column.fieldname === "status") {
			const colorMap = {
				Present: "var(--green-600)",
				Absent: "var(--red-500)",
				"On Leave With Pay": "var(--orange-500)",
				"On Leave Without Pay": "var(--orange-500)",
				"Sunday/Holiday": "var(--gray-500)",
			};
			const color = colorMap[data.status];
			if (color) {
				value = `<span style="color:${color};font-weight:600;">${value}</span>`;
			}
		}

		return value;
	},

	onload: function (report) {
		setTimeout(() => {
			const type = frappe.query_report.get_filter_value("employee_type") || "Employee";
			const is_driver = type === "Driver";
			const empF = frappe.query_report.get_filter("employee");
			const drvF = frappe.query_report.get_filter("driver");
			if (empF) empF.$wrapper.toggle(!is_driver);
			if (drvF) drvF.$wrapper.toggle(is_driver);

			// A value restored from the report's URL (e.g. on page load/refresh)
			// is set before the MultiSelectList has ever fetched its options, so
			// the chip shows the raw ID until the dropdown is opened once. Force
			// that fetch now so the name shows immediately.
			[
				["employee", empF],
				["driver", drvF],
			].forEach(([fieldname, f]) => {
				if (f && (frappe.query_report.get_filter_value(fieldname) || []).length) {
					f.set_options().then(() => f.update_status());
				}
			});
		}, 200);

		const downloadBtn = report.page.add_inner_button(
			__("Download"),
			function () {
				const dialog = new frappe.ui.Dialog({
					title: __("Download Staff Attendance Report"),
					fields: [
						{
							fieldname: "format",
							label: __("File Format"),
							fieldtype: "Select",
							options: "PDF\nCSV\nExcel",
							default: "PDF",
							reqd: 1,
						},
						{
							fieldname: "orientation",
							label: __("Orientation"),
							fieldtype: "Select",
							options: "Portrait\nLandscape",
							default: "Landscape",
							depends_on: "eval:doc.format=='PDF'",
						},
					],
					primary_action_label: __("Download"),
					primary_action: (values) => {
						dialog.hide();
						if (values.format === "PDF") {
							_sar_download_pdf(frappe.query_report.get_filter_values(), values.orientation);
						} else {
							_sar_download_data(report, values.format);
						}
					},
				});
				dialog.show();
			},
			null,
			"primary"
		);
		downloadBtn.css({ "font-weight": "600", "font-size": "13px", padding: "6px 20px" });
	},

	after_refresh: function (report) {
		const $summary = $(report.page.wrapper).find(".report-summary");
		$summary.css({ "flex-wrap": "nowrap", "overflow-x": "auto" });
		$summary.find(".summary-item").css({ "min-width": "auto", margin: "0 12px" });
	},
};

// ── Direct CSV/Excel download — bypasses Frappe's own export dialog since
// the format is already chosen in our single Download dialog above.
function _sar_download_data(report, fileFormat) {
	open_url_post(frappe.request.url, {
		cmd: "frappe.desk.query_report.export_query",
		report_name: report.report_name,
		file_format_type: fileFormat,
		filters: frappe.query_report.get_filter_values(true),
		visible_idx: [],
		ignore_visible_idx: true,
	});
}

// ── Direct PDF download (no preview window) ────────────────────────
function _sar_download_pdf(filters, orientation) {
	const data = frappe.query_report.data || [];
	const columns = (frappe.query_report.columns || []).filter(
		(c) => !c.hidden && c.fieldname !== "link_doctype"
	);

	const empType = filters.employee_type || "Employee";
	const fromDate = filters.from_date || "";
	const toDate = filters.to_date || "";
	const selected = (empType === "Driver" ? filters.driver : filters.employee) || [];
	const statuses = filters.status || [];

	const statusColor = {
		Present: "#16a085",
		Absent: "#c0392b",
		"On Leave With Pay": "#e67e22",
		"On Leave Without Pay": "#e67e22",
		"Sunday/Holiday": "#7f8c8d",
	};

	const statusCounts = {};
	Object.keys(statusColor).forEach((s) => (statusCounts[s] = 0));
	data.forEach((row) => {
		if (row.status in statusCounts) statusCounts[row.status]++;
	});
	// A flex-based card row renders fine in the browser but wkhtmltopdf (the
	// server-side PDF engine) doesn't shrink/distribute flex items reliably —
	// each card ends up taking the full row width and stacking vertically. An
	// HTML table forces a real horizontal layout in both renderers.
	const summaryCells =
		`<td><div class="summary-value" style="color:#2563eb;">${data.length}</div><div class="summary-label">Total Attendance Marked</div></td>` +
		Object.keys(statusColor)
			.map(
				(status) =>
					`<td><div class="summary-value" style="color:${statusColor[status]};">${statusCounts[status]}</div><div class="summary-label">${status}</div></td>`
			)
			.join("");
	const summaryHtml = `<table class="summary-table"><tr>${summaryCells}</tr></table>`;

	let headHtml = "";
	columns.forEach((col) => {
		headHtml += `<th>${col.label}</th>`;
	});

	let rowsHtml = "";
	data.forEach((row, idx) => {
		const rowCls = idx % 2 === 0 ? "" : "alt-row";
		let cells = "";
		columns.forEach((col) => {
			const fn = col.fieldname;
			const val = row[fn];
			let inner;
			if (fn === "status") {
				const color = statusColor[val] || "#222";
				inner = `<span style="color:${color};font-weight:600;">${frappe.utils.escape_html(val || "")}</span>`;
			} else if (fn === "date") {
				inner = val ? TMS.formatIndianDate(val) : "";
			} else if (fn === "attendance_no" && val) {
				const safe = frappe.utils.escape_html(val);
				inner = `<a href="${frappe.utils.get_form_link("Staff Attendance", val)}" target="_blank" style="color:#3B4FE4;">${safe}</a>`;
			} else {
				inner = frappe.utils.escape_html(val != null ? String(val) : "");
			}
			cells += `<td>${inner}</td>`;
		});
		rowsHtml += `<tr class="${rowCls}">${cells}</tr>`;
	});

	const pill = (lbl, val) => `<span class="pill"><b>${lbl}:</b> ${val}</span>`;
	const period = fromDate || toDate ? `${fromDate || "—"} &nbsp;→&nbsp; ${toDate || "—"}` : "All Dates";

	let pillsHtml = pill("Type", empType) + pill("Period", period);
	if (selected.length) pillsHtml += pill(empType, selected.join(", "));
	if (statuses.length) pillsHtml += pill("Status", statuses.join(", "));

	const today = new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });

	const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Staff Attendance Report</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; color-adjust: exact; }
  html, body { height: auto; }
  body { font-family: Arial, sans-serif; font-size: 11px; color: #222; background: #fff; padding: 16px 20px; }
  .report-header { text-align: center; margin-bottom: 2px; }
  .report-header h2 { font-size: 18px; font-weight: 700; color: #1a1a2e; }
  .header-rule { border: none; border-top: 2px solid #1a1a2e; margin: 4px auto 8px; width: 55%; }
  .pills { text-align: center; margin-bottom: 10px; page-break-inside: avoid; }
  .pill { display: inline-block; background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 20px;
          padding: 2px 10px; margin: 2px 3px; font-size: 10px; color: #3730a3; }
  .pill b { color: #1e1b4b; }
  .summary-table { width: 100%; border-collapse: separate; border-spacing: 4px 0; table-layout: fixed;
                    margin-bottom: 10px; page-break-inside: avoid; }
  .summary-table td { border: 1px solid #e5e7eb; border-radius: 8px; padding: 5px 4px; text-align: center; }
  .summary-value { font-size: 14px; font-weight: 700; }
  .summary-label { font-size: 8px; color: #6b7280; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  table { width: 100%; border-collapse: collapse; font-size: 10.5px; table-layout: fixed; }
  thead { display: table-header-group; }
  thead th { background: #1e3a5f; color: #fff; padding: 5px 6px; border: 1px solid #16304f;
             font-size: 10.5px; text-align: left; word-wrap: break-word; overflow-wrap: break-word; }
  tbody td { padding: 3px 6px; border: 1px solid #e5e7eb; vertical-align: middle;
             word-wrap: break-word; overflow-wrap: break-word; }
  tbody tr.alt-row td { background: #f8faff; }
  .report-footer { margin-top: 8px; display: flex; justify-content: space-between;
                   font-size: 9px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 4px;
                   page-break-inside: avoid; }
  @page { margin: 1cm; size: ${orientation === "Portrait" ? "A4 portrait" : "A4 landscape"}; }
</style>
</head>
<body>
  <div class="report-header">
    <h2>Staff Attendance Report</h2>
    <hr class="header-rule">
  </div>
  <div class="pills">${pillsHtml}</div>
  <div class="summary-row">${summaryHtml}</div>
  <table>
    <thead><tr>${headHtml}</tr></thead>
    <tbody>${rowsHtml}</tbody>
  </table>
  <div class="report-footer">
    <span>LogiCore</span>
    <span>Generated: ${today}</span>
  </div>
</body>
</html>`;

	frappe.render_pdf(html, {
		orientation,
		report_name: "Staff_Attendance_Report.pdf",
	});
}
