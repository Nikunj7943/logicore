frappe.listview_settings["Trip POD Import"] = Object.assign(
	frappe.listview_settings["Trip POD Import"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Trip POD Import", fieldname: "import_date", label: "Import Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Trip POD Import", fieldname: "import_date" });
		},
	}
);
