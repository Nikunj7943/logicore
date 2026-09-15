frappe.query_reports["TMS Stock Ledger"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "voucher_no",
			label: __("Voucher No"),
			fieldtype: "Data",
		},
		{
			fieldname: "vehicle",
			label: __("Vehicle No"),
			fieldtype: "Link",
			options: "Vehicle",
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
		if (column.fieldname === "in_qty" && data && flt(data.in_qty) > 0) {
			value = `<span style="color:var(--green-600);font-weight:600;">${value}</span>`;
		} else if (column.fieldname === "out_qty" && data && flt(data.out_qty) > 0) {
			value = `<span style="color:var(--red-500);font-weight:600;">${value}</span>`;
		} else if (column.fieldname === "balance_qty" && data) {
			const color = flt(data.balance_qty) < 0 ? "var(--red-500)" : "var(--gray-800)";
			value = `<span style="color:${color};font-weight:600;">${value}</span>`;
		} else if (column.fieldname === "stock_value_difference" && data) {
			const color = flt(data.stock_value_difference) < 0 ? "var(--red-500)" : "var(--green-600)";
			value = `<span style="color:${color};">${value}</span>`;
		}
		return value;
	},

	onload: function (report) {
		const downloadBtn = report.page.add_inner_button(
			__("Download"),
			function () {
				const dialog = new frappe.ui.Dialog({
					title: __("Download TMS Stock Ledger"),
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
							_tms_stock_ledger_download_pdf(report, values.orientation);
						} else {
							_tms_stock_ledger_download_data(report, values.format);
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
function _tms_stock_ledger_download_data(report, fileFormat) {
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
// Reads columns/data generically since this report's column set can change.
function _tms_stock_ledger_download_pdf(report, orientation) {
	const filters = frappe.query_report.get_filter_values();
	const columns = (frappe.query_report.columns || []).filter(
		(c) => !c.hidden && !["ref_doctype", "sr_no"].includes(c.fieldname)
	);
	const data = (frappe.query_report.data || []).filter((row) => row._type !== "total");
	const totalRow = (frappe.query_report.data || []).find((row) => row._type === "total");

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
	const pillFilters = [
		["item_code", "Item"],
		["item_group", "Item Group"],
		["warehouse", "Warehouse"],
		["voucher_no", "Voucher No"],
		["vehicle", "Vehicle No"],
	];
	pillFilters.forEach(([fieldname, label]) => {
		if (filters[fieldname]) pillsHtml += pill(label, filters[fieldname]);
	});

	const amtTypes = new Set(["Currency", "Float", "Int", "Percent"]);
	const headHtml = columns
		.map((col) => `<th${amtTypes.has(col.fieldtype) ? ' class="amt"' : ""}>${col.label}</th>`)
		.join("");

	// Mirrors the on-screen `formatter` colors so the PDF matches what the
	// report actually shows — green/red are the fixed hex equivalents of the
	// var(--green-600)/var(--red-500) theme tokens (PDF rendering has no CSS
	// variable context to resolve those against).
	const cellColor = (fieldname, row) => {
		if (fieldname === "in_qty" && flt(row.in_qty) > 0) return "#16a34a";
		if (fieldname === "out_qty" && flt(row.out_qty) > 0) return "#ef4444";
		if (fieldname === "balance_qty") return flt(row.balance_qty) < 0 ? "#ef4444" : null;
		if (fieldname === "stock_value_difference") return flt(row.stock_value_difference) < 0 ? "#ef4444" : "#16a34a";
		return null;
	};

	const rowHtml = (row, isTotal) =>
		"<tr" +
		(isTotal ? ' class="total-row"' : "") +
		">" +
		columns
			.map((col, idx) => {
				const isAmt = amtTypes.has(col.fieldtype);
				if (isTotal) {
					if (idx === 0) return `<td><strong>${__("Total")}</strong></td>`;
					const val = row[col.fieldname];
					if (val === null || val === undefined || val === "") return "<td></td>";
					const shown = col.fieldtype === "Currency" ? fmtCur(val) : val;
					return `<td${isAmt ? ' class="amt"' : ""}><strong>${shown}</strong></td>`;
				}
				const raw = row[col.fieldname];
				const shown = col.fieldtype === "Currency" ? fmtCur(raw) : raw != null ? String(raw) : "";
				const color = cellColor(col.fieldname, row);
				const text = frappe.utils.escape_html(shown);
				const cell = color ? `<span style="color:${color};font-weight:600;">${text}</span>` : text;
				return `<td${isAmt ? ' class="amt"' : ""}>${cell}</td>`;
			})
			.join("") +
		"</tr>";

	let bodyHtml = data.map((row) => rowHtml(row, false)).join("");
	if (totalRow) bodyHtml += rowHtml(totalRow, true);

	const today = frappe.datetime.str_to_user(frappe.datetime.get_today());

	const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>TMS Stock Ledger — ${companyName}</title>
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

  table { width: 100%; border-collapse: collapse; font-size: 10px; table-layout: fixed; }
  thead th { background: #1e3a5f; color: #fff; padding: 6px 6px; border: 1px solid #16304f;
             font-size: 10px; text-align: left; word-wrap: break-word; overflow-wrap: break-word; }
  thead th.amt { text-align: right; }
  tbody td { padding: 4px 6px; border: 1px solid #e5e7eb; vertical-align: middle;
             word-wrap: break-word; overflow-wrap: break-word; }
  tbody td.amt { text-align: right; }
  tbody tr:nth-child(even) td { background: #f8faff; }
  tbody tr.total-row td { background: #f0f4f8; border-top: 2px solid #64748b; font-weight: 700; }

  .report-footer { margin-top: 14px; display: flex; justify-content: flex-end;
                   font-size: 10px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 6px; }

  @page { margin: 1cm; size: ${orientation === "Portrait" ? "A4 portrait" : "A4 landscape"}; }
</style>
</head>
<body>
  <div class="report-header">
    <div class="company">${frappe.utils.escape_html(companyName)}</div>
    <h2>TMS Stock Ledger</h2>
    <hr class="header-rule">
  </div>
  <div class="pills">${pillsHtml}</div>

  <table>
    <thead><tr>${headHtml}</tr></thead>
    <tbody>${bodyHtml}</tbody>
  </table>

  <div class="report-footer">
    <span>Generated: ${today}</span>
  </div>
</body>
</html>`;

	frappe.render_pdf(html, {
		orientation,
		report_name: `TMS_Stock_Ledger_${companyName || "LogiCore"}.pdf`.replace(/\s+/g, "_"),
	});
}
