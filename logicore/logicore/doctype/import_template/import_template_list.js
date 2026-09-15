frappe.listview_settings["Import Template"] = Object.assign(
	frappe.listview_settings["Import Template"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
