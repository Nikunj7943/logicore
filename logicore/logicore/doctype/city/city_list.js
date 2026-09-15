frappe.listview_settings["City"] = Object.assign(
	frappe.listview_settings["City"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
