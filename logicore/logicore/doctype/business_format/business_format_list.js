frappe.listview_settings["Business Format"] = Object.assign(
	frappe.listview_settings["Business Format"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
