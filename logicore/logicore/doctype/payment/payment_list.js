frappe.listview_settings["Payment"] = Object.assign(
	frappe.listview_settings["Payment"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Payment", fieldname: "date", label: "Payment Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Payment", fieldname: "date" });
		},
	}
);
