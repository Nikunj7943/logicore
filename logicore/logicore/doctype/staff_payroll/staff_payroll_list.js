frappe.listview_settings["Staff Payroll"] = Object.assign(
	frappe.listview_settings["Staff Payroll"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Staff Payroll", fieldname: "payroll_date", label: "Payroll Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Staff Payroll", fieldname: "payroll_date" });
		},
	}
);
