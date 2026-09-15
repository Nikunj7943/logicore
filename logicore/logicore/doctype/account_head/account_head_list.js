frappe.listview_settings["Account Head"] = Object.assign(
	frappe.listview_settings["Account Head"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
