// Salary Advance Report — filter switching + row coloring

frappe.query_reports["Salary Advance Report"] = {
	filters: [
		{
			fieldname: "employee_type",
			label: __("Employee Type"),
			fieldtype: "Select",
			options: "Employee\nDriver",
			default: "Employee",
			reqd: 1,
			on_change: function() {
				const type = frappe.query_report.get_filter_value("employee_type");
				const f = frappe.query_report.get_filter("employee_link");
				if (!f) return;
				// Clear previous value
				frappe.query_report.set_filter_value("employee_link", "");
				// Swap label + linked doctype
				if (type === "Driver") {
					f.df.label   = __("Driver");
					f.df.options = "Driver";
				} else {
					f.df.label   = __("Employee");
					f.df.options = "Employee";
				}
				f.df.placeholder = __(f.df.label);
				f.set_value("");
				f.refresh();
				setTimeout(() => {
					f.$wrapper.find("input").first()
						.attr("placeholder", __(f.df.label))
						.attr("data-doctype", f.df.options);
				}, 100);
			}
		},
		{
			fieldname: "employee_link",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
	],

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		// Total row — bold everything
		if (data._type === "total") {
			value = `<strong>${value}</strong>`;
		}

		// Balance column — red if > 0, green if 0
		if (column.fieldname === "balance" && data._type !== "total") {
			const color = flt(data.balance) > 0 ? "var(--red-500)" : "var(--green-500)";
			value = `<span style="font-weight:700;color:${color};">${value}</span>`;
		}

		// Description — color by type
		if (column.fieldname === "description") {
			if (data._type === "given") {
				value = `<span style="color:var(--blue-500);font-weight:600;">${frappe.utils.escape_html(data.description || "")}</span>`;
			} else if (data._type === "taken") {
				value = `<span style="color:var(--green-600);font-weight:600;">${frappe.utils.escape_html(data.description || "")}</span>`;
			} else if (data._type === "total") {
				value = `<strong style="color:var(--text-color);">${frappe.utils.escape_html(data.description || "")}</strong>`;
			}
		}

		return value;
	},

	get_datatable_options(options) {
		return Object.assign(options, {
			getRowHeight(row) {
				return 36;
			}
		});
	},

	onload: function(report) {
		// Ensure placeholder is correct on initial load (default = Employee)
		setTimeout(() => {
			const f = frappe.query_report.get_filter("employee_link");
			if (f) {
				f.$wrapper.find("input").first()
					.attr("placeholder", __("Employee"))
					.attr("data-doctype", "Employee");
			}
		}, 200);
	}
};
