frappe.listview_settings["Trip Clasification"] = Object.assign(
	frappe.listview_settings["Trip Clasification"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
