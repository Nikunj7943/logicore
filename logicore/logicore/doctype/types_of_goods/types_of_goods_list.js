frappe.listview_settings["Types Of Goods"] = Object.assign(
	frappe.listview_settings["Types Of Goods"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
		},
	}
);
