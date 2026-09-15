frappe.listview_settings["Vendor Payment"] = Object.assign(
	frappe.listview_settings["Vendor Payment"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Vendor Payment", fieldname: "payment_date", label: "Payment Date" });
			// tms_import_dialog.js's global registration wraps whatever onload
			// exists on this doctype's listview_settings *when it runs* — since
			// this file (route-specific) loads after that (global, app_include_js)
			// registration, the Object.assign above replaces its wrapped onload
			// outright instead of extending it. Call it directly here too, same
			// as trip_list.js already does for Trip. (setup_list_button itself
			// positions the button next to Export — see tms_import_dialog.js.)
			if (TMS.import && TMS.import.setup_list_button) {
				TMS.import.setup_list_button(listview);
			}
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Vendor Payment", fieldname: "payment_date" });
		},
	}
);
