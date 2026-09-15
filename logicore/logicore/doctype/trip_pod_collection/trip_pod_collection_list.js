frappe.listview_settings["Trip POD Collection"] = Object.assign(
	frappe.listview_settings["Trip POD Collection"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
