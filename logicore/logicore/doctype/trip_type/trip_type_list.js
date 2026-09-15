frappe.listview_settings["Trip Type"] = Object.assign(
	frappe.listview_settings["Trip Type"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
