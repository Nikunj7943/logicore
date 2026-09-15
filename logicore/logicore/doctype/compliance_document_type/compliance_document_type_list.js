frappe.listview_settings["Compliance Document Type"] = Object.assign(
	frappe.listview_settings["Compliance Document Type"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
