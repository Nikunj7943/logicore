frappe.listview_settings["Vehicle Finance"] = Object.assign(
	frappe.listview_settings["Vehicle Finance"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
