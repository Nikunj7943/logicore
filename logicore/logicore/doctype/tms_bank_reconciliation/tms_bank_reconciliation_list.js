frappe.listview_settings["TMS Bank Reconciliation"] = Object.assign(
	frappe.listview_settings["TMS Bank Reconciliation"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "TMS Bank Reconciliation", fieldname: "reconciliation_date", label: "Reconciliation Date" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "TMS Bank Reconciliation", fieldname: "reconciliation_date" });
		},
	}
);
