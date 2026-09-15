frappe.listview_settings["Telegram User Map"] = Object.assign(
	frappe.listview_settings["Telegram User Map"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
