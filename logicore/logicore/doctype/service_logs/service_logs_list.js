frappe.listview_settings["Service Logs"] = Object.assign(
	frappe.listview_settings["Service Logs"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Service Logs", fieldname: "voucher_date", label: "Voucher Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Service Logs", fieldname: "voucher_date" });
		},
	}
);
