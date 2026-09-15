frappe.listview_settings["Repair Item"] = Object.assign(
	frappe.listview_settings["Repair Item"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
