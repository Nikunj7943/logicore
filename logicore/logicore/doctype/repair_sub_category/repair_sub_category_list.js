frappe.listview_settings["Repair Sub Category"] = Object.assign(
	frappe.listview_settings["Repair Sub Category"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
