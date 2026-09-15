frappe.listview_settings["Trip Settings"] = Object.assign(
	frappe.listview_settings["Trip Settings"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
