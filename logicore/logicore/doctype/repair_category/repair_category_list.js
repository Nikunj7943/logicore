frappe.listview_settings["Repair Category"] = Object.assign(
	frappe.listview_settings["Repair Category"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
