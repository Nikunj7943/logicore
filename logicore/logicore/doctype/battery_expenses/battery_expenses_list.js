frappe.listview_settings["Battery Expenses"] = Object.assign(
	frappe.listview_settings["Battery Expenses"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Battery Expenses", fieldname: "purchase_date", label: "Purchase Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Battery Expenses", fieldname: "purchase_date" });
		},
	}
);
