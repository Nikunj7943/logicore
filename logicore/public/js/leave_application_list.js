frappe.provide("frappe.listview_settings");
frappe.listview_settings["Leave Application"] = frappe.listview_settings["Leave Application"] || {};

frappe.listview_settings["Leave Application"].onload = function (listview) {
	TMS.dateFilterBar.attach(listview, { doctype: "Leave Application", fieldname: "posting_date", label: "Posting Date" });
};

frappe.listview_settings["Leave Application"].refresh = function (listview) {
	TMS.dateFilterBar.refresh(listview, { doctype: "Leave Application", fieldname: "posting_date" });
};
