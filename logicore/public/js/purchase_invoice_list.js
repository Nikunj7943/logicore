// Override ERPNext's own List/Report View indicator (erpnext/.../purchase_invoice_list.js)
// which colors the "Status" column from the GL-driven `status` field. This app
// tracks payment purely via Supplier Payment (custom_payment_status), so the
// list/report indicator needs to read that instead, once submitted.
//
// ERPNext's own doctype_list_js defines the whole frappe.listview_settings
// entry, so this only reassigns get_indicator on it — it must run after that
// file loads (app load order: erpnext before logicore).
frappe.provide("frappe.listview_settings");
frappe.listview_settings["Purchase Invoice"] = frappe.listview_settings["Purchase Invoice"] || {};

frappe.listview_settings["Purchase Invoice"].onload = function (listview) {
	TMS.dateFilterBar.attach(listview, { doctype: "Purchase Invoice", fieldname: "posting_date", label: "Purchase Date" });
};

frappe.listview_settings["Purchase Invoice"].refresh = function (listview) {
	TMS.dateFilterBar.refresh(listview, { doctype: "Purchase Invoice", fieldname: "posting_date" });
};

frappe.listview_settings["Purchase Invoice"].get_indicator = function (doc) {
	if (doc.docstatus === 1) {
		const status_colors = {
			Unpaid: "orange",
			"Partially Paid": "yellow",
			Paid: "green",
		};
		const status = doc.custom_payment_status || "Unpaid";
		return [__(status), status_colors[status] || "orange", "custom_payment_status,=," + status];
	}

	if (doc.docstatus === 0) {
		return [__("Draft"), "red", "docstatus,=,0"];
	}

	return [__("Cancelled"), "red", "docstatus,=,2"];
};
