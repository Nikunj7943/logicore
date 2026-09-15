frappe.listview_settings["Fuel Urea Expenses"] = Object.assign(
	frappe.listview_settings["Fuel Urea Expenses"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Fuel Urea Expenses", fieldname: "date", label: "Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Fuel Urea Expenses", fieldname: "date" });
		},
	}
);
