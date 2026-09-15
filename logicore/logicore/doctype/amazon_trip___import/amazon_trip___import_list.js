frappe.listview_settings["Amazon trip - Import"] = Object.assign(
	frappe.listview_settings["Amazon trip - Import"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Amazon trip - Import", fieldname: "import_date", label: "Import Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Amazon trip - Import", fieldname: "import_date" });
		},
	}
);
