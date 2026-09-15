frappe.listview_settings["Supplier Payment"] = Object.assign(
	frappe.listview_settings["Supplier Payment"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Supplier Payment", fieldname: "payment_date", label: "Payment Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Supplier Payment", fieldname: "payment_date" });
		},
	}
);
