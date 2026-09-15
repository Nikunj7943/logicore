frappe.listview_settings["Telegram Session"] = Object.assign(
	frappe.listview_settings["Telegram Session"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
