frappe.provide("frappe.listview_settings");
frappe.listview_settings["Stock Entry"] = frappe.listview_settings["Stock Entry"] || {};

frappe.listview_settings["Stock Entry"].onload = function (listview) {
	TMS.dateFilterBar.attach(listview, { doctype: "Stock Entry", fieldname: "posting_date", label: "Posting Date" });
};

frappe.listview_settings["Stock Entry"].refresh = function (listview) {
	TMS.dateFilterBar.refresh(listview, { doctype: "Stock Entry", fieldname: "posting_date" });
};
