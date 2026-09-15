frappe.listview_settings["Staff Attendance"] = Object.assign(
	frappe.listview_settings["Staff Attendance"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Staff Attendance", fieldname: "date", label: "Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Staff Attendance", fieldname: "date" });
		},
	}
);
