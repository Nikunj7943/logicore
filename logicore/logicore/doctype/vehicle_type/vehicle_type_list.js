frappe.listview_settings["Vehicle Type"] = Object.assign(
	frappe.listview_settings["Vehicle Type"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
