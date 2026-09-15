// Staff Attendance Summary Report — one row per Active Employee/Driver with
// attendance status counts for the selected date range.

frappe.query_reports["Staff Attendance Summary Report"] = {
	filters: [
		{
			fieldname: "employee_type",
			label: __("Employee Type"),
			fieldtype: "Select",
			options: "Employee\nDriver",
			default: "Employee",
			reqd: 1,
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
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		const colorMap = {
			present: "var(--green-600)",
			absent: "var(--red-500)",
			on_leave_with_pay: "var(--orange-500)",
			on_leave_without_pay: "var(--orange-500)",
			sunday_holiday: "var(--gray-500)",
		};
		const color = colorMap[column.fieldname];
		if (color && data[column.fieldname]) {
			value = `<span style="color:${color};font-weight:600;">${value}</span>`;
		}

		return value;
	},

	onload: function (report) {
		const downloadBtn = report.page.add_inner_button(
			__("Download"),
			function () {
				const dialog = new frappe.ui.Dialog({
					title: __("Download Staff Attendance Summary Report"),
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
							_sasr_download_pdf(frappe.query_report.get_filter_values(), values.orientation);
						} else {
							_sasr_download_data(report, values.format);
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
function _sasr_download_data(report, fileFormat) {
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
function _sasr_download_pdf(filters, orientation) {
	const data = frappe.query_report.data || [];
	const columns = (frappe.query_report.columns || []).filter(
		(c) => !c.hidden && c.fieldname !== "link_doctype"
	);

	const empType = filters.employee_type || "Employee";
	const fromDate = filters.from_date || "";
	const toDate = filters.to_date || "";

	const statusColor = {
		present: "#16a085",
		absent: "#c0392b",
		on_leave_with_pay: "#e67e22",
		on_leave_without_pay: "#e67e22",
		sunday_holiday: "#7f8c8d",
	};

	const summaryHtml = `<table class="summary-table"><tr><td><div class="summary-value" style="color:#2563eb;">${data.length}</div><div class="summary-label">Total Active ${empType}s</div></td></tr></table>`;

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
			if (fn in statusColor) {
				const color = val ? statusColor[fn] : "#222";
				inner = `<span style="color:${color};font-weight:600;">${val != null ? val : 0}</span>`;
			} else if (fn === "employee_link" && val) {
				const safe = frappe.utils.escape_html(val);
				inner = `<a href="${frappe.utils.get_form_link(empType, val)}" target="_blank" style="color:#3B4FE4;">${safe}</a>`;
			} else {
				inner = frappe.utils.escape_html(val != null ? String(val) : "");
			}
			cells += `<td>${inner}</td>`;
		});
		rowsHtml += `<tr class="${rowCls}">${cells}</tr>`;
	});

	const pill = (lbl, val) => `<span class="pill"><b>${lbl}:</b> ${val}</span>`;
	const period = fromDate || toDate ? `${fromDate || "—"} &nbsp;→&nbsp; ${toDate || "—"}` : "All Dates";
	const pillsHtml = pill("Type", empType) + pill("Period", period);

	const today = new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });

	const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Staff Attendance Summary Report</title>
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
    <h2>Staff Attendance Summary Report</h2>
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
		report_name: "Staff_Attendance_Summary_Report.pdf",
	});
}
