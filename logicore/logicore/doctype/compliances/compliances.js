// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Compliances", {
	setup(frm) {
		frm.set_query("bank_name", () => ({
			filters: { group: frm.doc.payment_mode === "Cash" ? "CASH" : "BANK" }
		}));
	},

	payment_mode(frm) {
		frm.set_value("bank_name", null);
	},

	issue_date(frm) {
		calculate_expiry_date(frm);
	},
	validity_period_months(frm) {
		if (frm.doc.validity_period_months > 999) {
			frappe.msgprint(__("Validity Period (Months) cannot be more than 999."));
			frm.set_value("validity_period_months", null);
			return;
		}
		calculate_expiry_date(frm);
	},
});

function calculate_expiry_date(frm) {
	if (frm.doc.issue_date && frm.doc.validity_period_months) {
		let expiry = frappe.datetime.add_months(frm.doc.issue_date, frm.doc.validity_period_months);
		expiry = frappe.datetime.add_days(expiry, -1);
		frm.set_value("expiry_date", expiry); 
	}
}
