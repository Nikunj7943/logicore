// Reverted per user request — Stock Entry goes back to plain posting_date,
// no custom Payment Date field. Kept here (commented out, not deleted) in
// case the feature is wanted again.
// function sync_posting_date_from_payment_date(frm) {
// 	if (frm.doc.custom_payment_date && frm.doc.posting_date !== frm.doc.custom_payment_date) {
// 		frm.set_value("posting_date", frm.doc.custom_payment_date);
// 	}
// }
//
// frappe.ui.form.on("Stock Entry", {
// 	custom_payment_date(frm) {
// 		sync_posting_date_from_payment_date(frm);
// 	},
//
// 	refresh(frm) {
// 		sync_posting_date_from_payment_date(frm);
// 	},
// });

// ERPNext's stock_controller.js adds a "View > Stock Ledger" button on any
// submitted Stock Entry, routing to Frappe's own built-in "Stock Ledger"
// report — TMS has its own "TMS Stock Ledger" report instead (see
// report/tms_stock_ledger/), so that button must point there instead.
function redirect_stock_ledger_button(frm) {
	if (frm.doc.docstatus < 1) return;
	frm.remove_custom_button(__("Stock Ledger"), __("View"));
	frm.add_custom_button(
		__("Stock Ledger"),
		() => {
			frappe.set_route("query-report", "TMS Stock Ledger", {
				voucher_no: frm.doc.name,
				company: frm.doc.company,
				from_date: "",
				to_date: "",
			});
		},
		__("View")
	);
}

frappe.ui.form.on("Stock Entry", {
	refresh(frm) {
		redirect_stock_ledger_button(frm);
	},
});
