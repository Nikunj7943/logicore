frappe.listview_settings["Receipt"] = Object.assign(
	frappe.listview_settings["Receipt"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Receipt", fieldname: "payment_date", label: "Payment Date" });
			// See the matching comment in vendor_payment_list.js — this file's
			// Object.assign replaces tms_import_dialog.js's wrapped onload
			// instead of extending it, so call it directly here too.
			// (setup_list_button itself positions the button next to Export —
			// see tms_import_dialog.js.)
			if (TMS.import && TMS.import.setup_list_button) {
				TMS.import.setup_list_button(listview);
			}
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Receipt", fieldname: "payment_date" });
		},
	}
);
