frappe.listview_settings["Standard KMs"] = Object.assign(
	frappe.listview_settings["Standard KMs"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
