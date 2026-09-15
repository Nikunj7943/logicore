frappe.ui.form.on("Salary Structure", {
	refresh: function (frm) {
		if (frm.doc.docstatus !== 1) return;

		const can_edit =
			frappe.session.user === "Administrator" ||
			frappe.user.has_role("System Manager") ||
			frappe.user.has_role("TMS ADMIN");

		["earnings", "deductions"].forEach((fieldname) => {
			frm.set_df_property(fieldname, "read_only", can_edit ? 0 : 1);
			frm.fields_dict[fieldname].grid.refresh();
		});
	},
});
