// ERPNext's core company.js shows "Delete Transactions" (Manage menu) to anyone
// with the System Manager role. That's wider than intended here — only the
// literal Administrator account should be able to wipe a company's transactions.
// Core file is in the erpnext app (vendor code), so this app removes the button
// after refresh instead of patching it there.
frappe.ui.form.on("Company", {
	refresh(frm) {
		if (frappe.session.user !== "Administrator") {
			frm.remove_custom_button(__("Delete Transactions"), __("Manage"));
		}
	},
});
