frappe.listview_settings["Compliances"] = Object.assign(
	frappe.listview_settings["Compliances"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Compliances", fieldname: "issue_date", label: "Issue Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Compliances", fieldname: "issue_date" });
		},
	}
);
