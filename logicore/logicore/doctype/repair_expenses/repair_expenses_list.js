frappe.listview_settings["Repair Expenses"] = Object.assign(
	frappe.listview_settings["Repair Expenses"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Repair Expenses", fieldname: "date", label: "Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Repair Expenses", fieldname: "date" });
		},
	}
);
