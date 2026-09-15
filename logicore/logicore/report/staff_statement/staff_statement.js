// Staff Statement — dynamic filters + row coloring + custom print

frappe.query_reports["Staff Statement"] = {

	_type_options: {
		"Employee": "All\nSalary Advance\nStaff Payroll",
		"Driver":   "All\nDriver Advance\nTrip Expense\nFuel Incentive\nStaff Payroll",
	},

	filters: [
		{
			fieldname: "employee_type",
			label: __("Employee Type"),
			fieldtype: "Select",
			options: "Employee\nDriver",
			default: "Employee",
			reqd: 1,
			on_change: function() {
				const rpt      = frappe.query_reports["Staff Statement"];
				const type     = frappe.query_report.get_filter_value("employee_type");
				const is_driver = type === "Driver";

				// Clear both link filters on type switch
				frappe.query_report.set_filter_value("employee_link", "");
				frappe.query_report.set_filter_value("driver_link", "");

				// Show the correct link filter, hide the other
				const empF = frappe.query_report.get_filter("employee_link");
				const drvF = frappe.query_report.get_filter("driver_link");
				if (empF) empF.$wrapper.toggle(!is_driver);
				if (drvF) drvF.$wrapper.toggle(is_driver);

				// Update data type options
				const dtF = frappe.query_report.get_filter("data_type");
				if (dtF) {
					dtF.df.options = rpt._type_options[type] || "All";
					frappe.query_report.set_filter_value("data_type", "All");
					dtF.refresh();
				}
			}
		},
		{
			fieldname: "employee_link",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "driver_link",
			label: __("Driver"),
			fieldtype: "Link",
			options: "Driver",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "data_type",
			label: __("Data Type"),
			fieldtype: "Select",
			options: "All\nSalary Advance\nStaff Payroll",
			default: "All",
		},
		{
			fieldname: "direction",
			label: __("Show"),
			fieldtype: "Select",
			options: "Both\nGiven\nTaken",
			default: "Both",
		},
		{
			fieldname: "payment_mode_filter",
			label: __("Payment Mode"),
			fieldtype: "Select",
			options: "All\nCash\nBank Transfer\nCheque\nUPI",
			default: "All",
		},
		{
			fieldname: "bank_filter",
			label: __("Bank Account"),
			fieldtype: "Link",
			options: "Account Head",
		},
	],

	// ── Screen formatter ──────────────────────────────────────────
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;

		const fn      = column.fieldname;
		const isTotal = data._type === "total";

		if (fn === "given") {
			if (flt(data.given) > 0) {
				value = `<span style="color:var(--red-500);font-weight:${isTotal?800:600};">${value}</span>`;
			}
		}
		if (fn === "taken") {
			if (flt(data.taken) > 0) {
				value = `<span style="color:var(--green-600);font-weight:${isTotal?800:600};">${value}</span>`;
			}
		}
		if (fn === "balance") {
			if (!isTotal && (data.balance === null || data.balance === undefined)) {
				return `<span style="color:var(--gray-400);">—</span>`;
			}
			value = `<span style="color:var(--orange-500);font-weight:${isTotal?800:700};">${value}</span>`;
		}
		if (fn === "category") {
			const colorMap = {
				advance_given:  "var(--red-500)",
				advance_taken:  "var(--green-600)",
				trip_expense:   "var(--blue-500)",
				fuel_incentive: "var(--purple-500)",
				payroll:        "var(--teal-500)",
			};
			const color = colorMap[data._type];
			const raw   = data.category || "";
			if (color && raw) {
				value = `<span style="color:${color};font-weight:${isTotal?800:600};">${frappe.utils.escape_html(raw)}</span>`;
			}
		}
		if (fn === "bank_account" && isTotal) {
			value = `<strong>${value}</strong>`;
		}

		return value;
	},

	get_datatable_options(options) {
		return Object.assign(options, {
			inlineFilters: false,
			serialNoColumn: false,
			getRowHeight() { return 36; },
		});
	},

	// ── Onload ───────────────────────────────────────────────────
	onload: function(report) {
		setTimeout(() => {
			// Set correct filter visibility based on current employee_type
			const type      = frappe.query_report.get_filter_value("employee_type") || "Employee";
			const is_driver = type === "Driver";
			const empF = frappe.query_report.get_filter("employee_link");
			const drvF = frappe.query_report.get_filter("driver_link");
			if (empF) empF.$wrapper.toggle(!is_driver);
			if (drvF) drvF.$wrapper.toggle(is_driver);
		}, 200);

		// ── Download button (PDF / CSV / Excel) ──────────────────
		const downloadBtn = report.page.add_inner_button(__("Download"), function() {
			const dialog = new frappe.ui.Dialog({
				title: __("Download Staff Statement"),
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
					if (values.format !== "PDF") {
						_ss_download_data(report, values.format);
						return;
					}

					const filters = frappe.query_report.get_filter_values();
					const empType = filters.employee_type || "Employee";
					const empLink = (empType === "Driver" ? filters.driver_link : filters.employee_link) || "";

					if (!empLink) {
						frappe.msgprint(__("Please select an Employee / Driver first."));
						return;
					}

					const nameField = empType === "Driver" ? "full_name" : "employee_name";
					frappe.call({
						method: "frappe.client.get_value",
						args: { doctype: empType, filters: { name: empLink }, fieldname: nameField },
						callback(r) {
							const empName = (r.message && r.message[nameField]) || empLink;
							_ss_download_pdf(filters, empType, empName, values.orientation);
						}
					});
				},
			});
			dialog.show();
		}, null, "primary");
		downloadBtn.css({ "font-weight": "600", "font-size": "13px", padding: "6px 20px" });
	}
};

// ── Direct CSV/Excel download — bypasses Frappe's own export dialog since
// the format is already chosen in our single Download dialog above.
function _ss_download_data(report, fileFormat) {
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
function _ss_download_pdf(filters, empType, empName, orientation) {
	const data    = frappe.query_report.data || [];
	// Exclude sr_no (we add # manually) + hidden + ref_doctype
	const columns = (frappe.query_report.columns || []).filter(
		c => !c.hidden && !["ref_doctype", "sr_no"].includes(c.fieldname)
	);

	const fromDate = filters.from_date          || "";
	const toDate   = filters.to_date            || "";
	const dtype    = filters.data_type          || "All";
	const dir      = filters.direction          || "Both";
	const pmode    = filters.payment_mode_filter || "All";
	const bank     = filters.bank_filter        || "";

	const catColor = {
		advance_given:  "#c0392b",
		advance_taken:  "#27ae60",
		trip_expense:   "#2980b9",
		fuel_incentive: "#8e44ad",
		payroll:        "#16a085",
	};

	const fmtCur = v => {
		if (v == null || v === "") return "";
		return "₹ " + parseFloat(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	};

	// ── Table header ──
	const amtCols = ["given", "taken", "balance"];
	let headHtml  = `<th class="sr">#</th>`;
	columns.forEach(col => {
		const right = amtCols.includes(col.fieldname);
		headHtml += `<th${right ? ' class="amt"' : ""}>${col.label}</th>`;
	});

	// ── Table rows ──
	let srn = 0;
	let rowsHtml = "";
	data.forEach((row, idx) => {
		const isTotal = row._type === "total";
		const rowCls  = isTotal ? "total-row" : (idx % 2 === 0 ? "" : "alt-row");

		let cells = `<td class="sr">${isTotal ? "" : ++srn}</td>`;

		columns.forEach(col => {
			const fn  = col.fieldname;
			const val = row[fn];
			let inner = "";
			let cls   = "";

			if (fn === "category") {
				cls   = isTotal ? "bold" : "";
				const color = isTotal ? "#222" : (catColor[row._type] || "#222");
				inner = `<span style="color:${color};font-weight:${isTotal?700:600};">${frappe.utils.escape_html(val || "")}</span>`;

			} else if (fn === "given") {
				cls   = "amt";
				const c = parseFloat(val) > 0 ? "#c0392b" : "#bbb";
				inner = `<span style="color:${c};font-weight:${isTotal?700:600};">${fmtCur(val)}</span>`;

			} else if (fn === "taken") {
				cls   = "amt";
				const c = parseFloat(val) > 0 ? "#27ae60" : "#bbb";
				inner = `<span style="color:${c};font-weight:${isTotal?700:600};">${fmtCur(val)}</span>`;

			} else if (fn === "balance") {
				cls   = "amt";
				if (!isTotal && (val === null || val === undefined)) {
					inner = `<span style="color:#ccc;">—</span>`;
				} else {
					inner = `<span style="color:#e67e22;font-weight:${isTotal?700:600};">${fmtCur(val)}</span>`;
				}

			} else if (fn === "bank_account" && isTotal) {
				inner = `<strong>${frappe.utils.escape_html(val || "")}</strong>`;

			} else {
				inner = frappe.utils.escape_html((val != null ? String(val) : ""));
			}

			cells += `<td${cls ? ' class="' + cls + '"' : ""}>${inner}</td>`;
		});

		rowsHtml += `<tr class="${rowCls}">${cells}</tr>`;
	});

	// ── Filter pills ──
	const pill = (lbl, val) => `<span class="pill"><b>${lbl}:</b> ${val}</span>`;
	const period = fromDate || toDate
		? `${fromDate || "—"} &nbsp;→&nbsp; ${toDate || "—"}`
		: "All Dates";

	let pillsHtml = pill(empType, empName) + pill("Period", period);
	if (dtype !== "All")  pillsHtml += pill("Data Type", dtype);
	if (dir   !== "Both") pillsHtml += pill("Show", dir);
	if (pmode !== "All")  pillsHtml += pill("Payment Mode", pmode);
	if (bank)             pillsHtml += pill("Bank", bank);

	const today = new Date().toLocaleDateString("en-IN", { day:"2-digit", month:"short", year:"numeric" });

	const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Staff Statement — ${empName}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; color-adjust: exact; }
  body { font-family: Arial, sans-serif; font-size: 11px; color: #222; background: #fff; padding: 24px 28px; }

  /* Header */
  .report-header { text-align: center; margin-bottom: 4px; }
  .report-header h2 { font-size: 20px; font-weight: 700; letter-spacing: 0.5px; color: #1a1a2e; }
  .header-rule { border: none; border-top: 2.5px solid #1a1a2e; margin: 6px auto 10px; width: 55%; }

  /* Pills */
  .pills { text-align: center; margin-bottom: 16px; }
  .pill { display: inline-block; background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 20px;
          padding: 3px 11px; margin: 2px 4px; font-size: 10.5px; color: #3730a3; }
  .pill b { color: #1e1b4b; }

  /* Table */
  table { width: 100%; border-collapse: collapse; font-size: 10.5px; table-layout: fixed; }
  thead th { background: #1e3a5f; color: #fff; padding: 6px 7px; border: 1px solid #16304f;
             font-size: 10.5px; word-wrap: break-word; overflow-wrap: break-word; }
  thead th.amt { text-align: right; }
  tbody td { padding: 4px 7px; border: 1px solid #e5e7eb; vertical-align: middle;
             word-wrap: break-word; overflow-wrap: break-word; }
  tbody td.amt { text-align: right; }
  tbody td.sr  { text-align: center; color: #9ca3af; width: 34px; }
  tbody tr.alt-row td { background: #f8faff; }
  tbody tr.total-row td { background: #f0f4f8; border-top: 2px solid #64748b; font-weight: 600; }

  /* Footer */
  .report-footer { margin-top: 14px; display: flex; justify-content: space-between;
                   font-size: 10px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 6px; }

  @page { margin: 1cm; size: ${orientation === "Portrait" ? "A4 portrait" : "A4 landscape"}; }
</style>
</head>
<body>
  <div class="report-header">
    <h2>Staff Statement</h2>
    <hr class="header-rule">
  </div>
  <div class="pills">${pillsHtml}</div>

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
		report_name: `Staff_Statement_${empName || empType}.pdf`.replace(/\s+/g, "_"),
	});
}
