frappe.listview_settings["Import Log"] = Object.assign(
	frappe.listview_settings["Import Log"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Import Log", fieldname: "started_at", label: "Started At" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Import Log", fieldname: "started_at" });
		},
	}
);
