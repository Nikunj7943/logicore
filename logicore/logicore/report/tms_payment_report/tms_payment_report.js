frappe.query_reports["TMS Payment Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
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
			fieldname: "type",
			label: __("Payment Type"),
			fieldtype: "Select",
			options: [
				"",
				"Loading",
				"Unloading",
				"Extra Expense",
				"Border Crossing/Vehicle Expense/Toll Tax",
				"Office",
				"Other Expense",
				"Police Entry",
				"Employee Advance",
				"Employee Incentive",
				"Driver Advance",
				"Driver Trip Expense",
				"Vehicle Finance EMI",
				"Fuel Incentive",
				"Vendor Payment",
				"Bank Transfer",
				"Cash Withdrawal",
				"Supplier Payment",
			].join("\n"),
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDraft\nPaid\nCancelled",
		},
		{
			fieldname: "mode_of_payment",
			label: __("Mode of Payment"),
			fieldtype: "Select",
			options: "\nCash\nBank Transfer\nCheque\nUPI",
		},
		{
			fieldname: "paid_from_account",
			label: __("Paid From Account"),
			fieldtype: "Link",
			options: "Account Head",
		},
		{
			fieldname: "trip_no",
			label: __("Trip No"),
			fieldtype: "Link",
			options: "Trip",
		},
		{
			fieldname: "driver",
			label: __("Driver"),
			fieldtype: "Link",
			options: "Driver",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "vendor_supplier",
			label: __("Vendor / Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "tcn_no",
			label: __("TCN / Trip No"),
			fieldtype: "Data",
		},
		{
			fieldname: "origin",
			label: __("Origin"),
			fieldtype: "Data",
		},
		{
			fieldname: "destination",
			label: __("Destination"),
			fieldtype: "Data",
		},
		{
			fieldname: "vehicle_type",
			label: __("Vehicle Type"),
			fieldtype: "Link",
			options: "Vehicle Type",
		},
		{
			fieldname: "vehicle_finance",
			label: __("Vehicle Finance"),
			fieldtype: "Link",
			options: "Vehicle Finance",
		},
		{
			fieldname: "vf_vehicle",
			label: __("Vehicle No"),
			fieldtype: "Link",
			options: "Vehicle",
		},
		{
			fieldname: "financer",
			label: __("Financer / Bank"),
			fieldtype: "Data",
		},
		{
			fieldname: "loan_account",
			label: __("Loan Account"),
			fieldtype: "Data",
		},
		{
			fieldname: "select_account",
			label: __("Expense Account"),
			fieldtype: "Link",
			options: "Account Head",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		// Total row: `data` is not available for footer cells (a datatable quirk), so
		// this branches on the raw pre-format value instead of a `data.is_total` flag.
		// `value` here is the raw cell content computed by report_column_total — it is
		// blank ("" / null) for columns marked `disable_total` in the column definition,
		// or for non-numeric columns with nothing to sum.
		if (!data) {
			if (value === "" || value === null || value === undefined) {
				if (column.show_total_label) {
					return `<strong style="font-size:13px;">${__("Total")}</strong>`;
				}
				return "";
			}
			value = default_formatter(value, row, column, data);
			if (column.fieldtype === "Currency") {
				return `<strong style="color:var(--green-700);font-size:13px;">${value}</strong>`;
			}
			return `<strong style="font-size:13px;">${value}</strong>`;
		}

		value = default_formatter(value, row, column, data);

		// Highlight Cancelled rows in muted red
		if (data.status === "Cancelled") {
			value = `<span style="color:var(--red-400);">${value}</span>`;
		}

		// Currency columns — bold green always
		if (column.fieldtype === "Currency") {
			value = `<strong style="color:var(--green-600);">${value}</strong>`;
		}

		return value;
	},

	onload: function (report) {
		const downloadBtn = report.page.add_inner_button(
			__("Download"),
			function () {
				const dialog = new frappe.ui.Dialog({
					title: __("Download TMS Payment Report"),
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
							_tms_payment_download_pdf(report, values.orientation);
						} else {
							_tms_payment_download_data(report, values.format);
						}
					},
				});
				dialog.show();
			},
			null,
			"primary"
		);
		downloadBtn.css({ "font-weight": "600", "font-size": "13px", padding: "6px 20px" });

		// frappe-datatable measures each row's height once, from a canvas-based
		// text measurement, at render time — on some machines/zoom levels that
		// measurement comes out shorter than the actual rendered text height, so
		// the row's own overflow gets clipped instead of the row growing to fit
		// it (looks "squished", varies by screen/zoom instead of being reliably
		// fixed). Auto-height + visible-overflow is a pure-CSS override — it
		// doesn't depend on any particular screen size, zoom level, or render
		// timing, so it holds on every machine, unlike a resize-retrigger hack.
		if (!document.getElementById("tms-payment-report-datatable-fix")) {
			const style = document.createElement("style");
			style.id = "tms-payment-report-datatable-fix";
			style.textContent = `
				.dt-scrollable .dt-row {
					height: auto !important;
					min-height: 30px !important;
				}
				.dt-scrollable .dt-cell {
					height: auto !important;
					overflow: visible !important;
				}
				.dt-scrollable .dt-cell__content {
					white-space: normal !important;
					overflow: visible !important;
					text-overflow: clip !important;
				}
				/* frappe-datatable sizes .dt-scrollable to fit exactly N rows, with no
				   allowance for its own horizontal scrollbar — with few rows and many
				   columns (this report needs horizontal scroll), that scrollbar renders
				   on top of the last row's bottom edge instead of below it, clipping the
				   text. Reserve real space for it so it never overlaps row content. */
				.dt-scrollable {
					padding-bottom: 22px !important;
					box-sizing: content-box !important;
				}
			`;
			document.head.appendChild(style);
		}
	},

	after_datatable_render: function (datatable) {
		// The row-number column's width is auto-measured once from the row count's
		// text width (frappe-datatable's getRowIndexColumnWidth). That measurement
		// can end up too narrow for 2-3 digit row counts — e.g. under a page zoom
		// level, canvas-based text measurement doesn't account for the CSS zoom
		// factor the rest of the page renders at — so the numbers get ellipsis-
		// truncated ("1..." instead of "10"). Force a wider, fixed width every time
		// the table (re)renders so it never depends on that measurement being right.
		try {
			const idx = datatable.datamanager.getColumnIndexById("_rowIndex");
			if (idx > -1) {
				datatable.columnmanager.setColumnWidth(idx, 45);
			}
		} catch (e) {
			// Cosmetic only — never let this break the report if datatable internals change.
		}

		// Under browser/OS display zoom (e.g. Windows scaling != 100%), frappe-
		// datatable's own canvas-based row-height measurement can run before the
		// zoomed layout has settled, leaving rows rendered too short — the row's
		// text gets clipped instead of the row growing to fit it. Re-triggering a
		// resize on the next tick makes the datatable re-measure against the
		// already-settled DOM, which fixes the row heights without changing any
		// data. Guarded/best-effort — never let this break the report.
		try {
			setTimeout(() => {
				window.dispatchEvent(new Event("resize"));
			}, 0);
		} catch (e) {
			// Cosmetic only.
		}
	},
};

// ── Direct CSV/Excel download — bypasses Frappe's own export dialog since
// the format is already chosen in our single Download dialog above.
function _tms_payment_download_data(report, fileFormat) {
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
// Reads columns/data generically since this report's column set changes
// with the Payment Type filter (Fuel Incentive / Vendor Payment / Supplier
// Payment / All Types).
function _tms_payment_download_pdf(report, orientation) {
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
		["type", "Payment Type"],
		["status", "Status"],
		["mode_of_payment", "Mode of Payment"],
		["trip_no", "Trip No"],
		["driver", "Driver"],
		["employee", "Employee"],
		["vendor_supplier", "Vendor / Supplier"],
	];
	pillFilters.forEach(([fieldname, label]) => {
		if (filters[fieldname]) pillsHtml += pill(label, filters[fieldname]);
	});

	const amtTypes = new Set(["Currency", "Float", "Int", "Percent"]);
	const headHtml = columns
		.map((col) => `<th${amtTypes.has(col.fieldtype) ? ' class="amt"' : ""}>${col.label}</th>`)
		.join("");

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
				return `<td${isAmt ? ' class="amt"' : ""}>${frappe.utils.escape_html(shown)}</td>`;
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
<title>TMS Payment Report — ${companyName}</title>
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

  .report-footer { margin-top: 14px; display: flex; justify-content: space-between;
                   font-size: 10px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 6px; }

  @page { margin: 1cm; size: ${orientation === "Portrait" ? "A4 portrait" : "A4 landscape"}; }
</style>
</head>
<body>
  <div class="report-header">
    <div class="company">${frappe.utils.escape_html(companyName)}</div>
    <h2>TMS Payment Report</h2>
    <hr class="header-rule">
  </div>
  <div class="pills">${pillsHtml}</div>

  <table>
    <thead><tr>${headHtml}</tr></thead>
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
		report_name: `TMS_Payment_Report_${companyName || "LogiCore"}.pdf`.replace(/\s+/g, "_"),
	});
}
