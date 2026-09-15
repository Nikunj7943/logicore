frappe.query_reports["TDS Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "vendor",
			label: __("Vendor"),
			fieldtype: "Link",
			options: "Supplier",
			get_query: () => ({ filters: { supplier_group: "Vendor" } }),
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "trips" && data && data.vendor) {
			const filters = frappe.query_report.get_filter_values();
			const route_filters = {
				vendor: data.vendor,
				trip_status: ["!=", "Cancel"],
			};
			if (filters.company) route_filters.company = filters.company;
			if (filters.from_date && filters.to_date) {
				route_filters.tcntrip_date = ["between", [filters.from_date, filters.to_date]];
			}
			const query = Object.entries(route_filters)
				.map(([k, v]) => {
					const encoded = Array.isArray(v) ? JSON.stringify(v) : v;
					return `${encodeURIComponent(k)}=${encodeURIComponent(encoded)}`;
				})
				.join("&");
			return `<a href="/app/trip?${query}" target="_blank" style="color:var(--blue-500);text-decoration:underline;">${value}</a>`;
		}
		return value;
	},

	onload: function (report) {
		const downloadBtn = report.page.add_inner_button(
			__("Download"),
			function () {
				const dialog = new frappe.ui.Dialog({
					title: __("Download TDS Report"),
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
							_tds_download_pdf(report, values.orientation);
						} else {
							_tds_download_data(report, values.format);
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
};

// ── Direct CSV/Excel download — bypasses Frappe's own export dialog since
// the format is already chosen in our single Download dialog above.
function _tds_download_data(report, fileFormat) {
	open_url_post(frappe.request.url, {
		cmd: "frappe.desk.query_report.export_query",
		report_name: report.report_name,
		file_format_type: fileFormat,
		filters: frappe.query_report.get_filter_values(true),
		visible_idx: [],
		ignore_visible_idx: true,
	});
}

// ── Direct PDF download (no preview window) — builds a branded, page-fit
// HTML table and hands it straight to Frappe's server-side PDF renderer.
function _tds_download_pdf(report, orientation) {
	const filters = frappe.query_report.get_filter_values();
	const data = (report.data || []).filter((row) => row._type !== "total");
	const totalRow = (report.data || []).find((row) => row._type === "total");

	const fmtCur = (v) => {
		if (v === null || v === undefined || v === "") return "";
		return "₹ " + parseFloat(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	};

	const companyName = filters.company || "";
	const fromDate = filters.from_date ? frappe.datetime.str_to_user(filters.from_date) : "";
	const toDate = filters.to_date ? frappe.datetime.str_to_user(filters.to_date) : "";
	const period = fromDate || toDate ? `${fromDate || "—"} → ${toDate || "—"}` : "All Dates";

	const pill = (lbl, val) => `<span class="pill"><b>${lbl}:</b> ${frappe.utils.escape_html(String(val))}</span>`;
	let pillsHtml = pill("Period", period);
	if (filters.vendor) pillsHtml += pill("Vendor", filters.vendor);

	const headCols = [
		{ label: "Transporter", cls: "", width: "18%" },
		{ label: "Trips", cls: "amt", width: "6%" },
		{ label: "Sum of Total Vendor Freight", cls: "amt", width: "16%" },
		{ label: "Sum of Vendor Tds To Be Deducted", cls: "amt", width: "17%" },
		{ label: "PAN", cls: "", width: "13%" },
		{ label: "GSTIN", cls: "", width: "17%" },
		{ label: "TDS Rate", cls: "amt", width: "8%" },
	];

	const rowHtml = (row, isTotal) => `
		<tr class="${isTotal ? "total-row" : ""}">
			<td>${isTotal ? "<strong>Total</strong>" : frappe.utils.escape_html(row.vendor_name || row.vendor || "")}</td>
			<td class="amt">${isTotal ? "" : row.trips ?? ""}</td>
			<td class="amt">${fmtCur(row.total_vendor_freight)}</td>
			<td class="amt">${fmtCur(row.total_tds)}</td>
			<td>${isTotal ? "" : frappe.utils.escape_html(row.pan || "")}</td>
			<td>${isTotal ? "" : frappe.utils.escape_html(row.gstin || "")}</td>
			<td class="amt">${isTotal ? "" : row.tds_rate || ""}</td>
		</tr>`;

	let bodyHtml = data.map((row) => rowHtml(row, false)).join("");
	if (totalRow) bodyHtml += rowHtml(totalRow, true);

	const today = frappe.datetime.str_to_user(frappe.datetime.get_today());
	const pageSize = orientation === "Portrait" ? "A4 portrait" : "A4 landscape";

	const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>TDS Report — ${companyName}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; color-adjust: exact; }
  body { font-family: Arial, sans-serif; font-size: 11px; color: #222; background: #fff; padding: 24px 28px; }

  .report-header { text-align: center; margin-bottom: 4px; }
  .report-header .company { font-size: 15px; font-weight: 700; color: #1a1a2e; }
  .report-header h2 { font-size: 19px; font-weight: 700; letter-spacing: 0.5px; color: #1a1a2e; margin-top: 2px; }
  .header-rule { border: none; border-top: 2.5px solid #1a1a2e; margin: 6px auto 10px; width: 55%; }

  .pills { text-align: center; margin-bottom: 16px; }
  .pill { display: inline-block; background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 20px;
          padding: 3px 11px; margin: 2px 4px; font-size: 10.5px; color: #3730a3; }
  .pill b { color: #1e1b4b; }

  table { width: 100%; border-collapse: collapse; font-size: 10.5px; table-layout: fixed; }
  thead th { background: #1e3a5f; color: #fff; padding: 6px 7px; border: 1px solid #16304f;
             font-size: 10.5px; text-align: left; word-wrap: break-word; overflow-wrap: break-word; }
  thead th.amt { text-align: right; }
  tbody td { padding: 4px 7px; border: 1px solid #e5e7eb; vertical-align: middle;
             word-wrap: break-word; overflow-wrap: break-word; }
  tbody td.amt { text-align: right; }
  tbody tr:nth-child(even) td { background: #f8faff; }
  tbody tr.total-row td { background: #f0f4f8; border-top: 2px solid #64748b; font-weight: 700; }

  .report-footer { margin-top: 14px; display: flex; justify-content: space-between;
                   font-size: 10px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 6px; }

  @page { margin: 1cm; size: ${pageSize}; }
</style>
</head>
<body>
  <div class="report-header">
    <h2>TDS Report</h2>
    <hr class="header-rule">
  </div>
  <div class="pills">${pillsHtml}</div>

  <table>
    <colgroup>${headCols.map((c) => `<col style="width:${c.width}">`).join("")}</colgroup>
    <thead><tr>${headCols.map((c) => `<th${c.cls ? ` class="${c.cls}"` : ""}>${c.label}</th>`).join("")}</tr></thead>
    <tbody>${bodyHtml}</tbody>
  </table>

  <div class="report-footer">
    <span>LogiCore</span>
    <span>Generated: ${today}</span>
  </div>
</body>
</html>`;

	frappe.render_pdf(html, {
		orientation,
		report_name: `TDS_Report_${companyName || "LogiCore"}.pdf`.replace(/\s+/g, "_"),
	});
}
