frappe.listview_settings["Business Subformat"] = Object.assign(
	frappe.listview_settings["Business Subformat"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
