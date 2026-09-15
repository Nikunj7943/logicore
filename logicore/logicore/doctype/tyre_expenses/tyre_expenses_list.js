frappe.listview_settings["Tyre Expenses"] = Object.assign(
	frappe.listview_settings["Tyre Expenses"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Tyre Expenses", fieldname: "purchase_date", label: "Purchase Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Tyre Expenses", fieldname: "purchase_date" });
		},
	}
);
