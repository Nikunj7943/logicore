frappe.ui.form.on("Email Template", {
	onload(frm) {
		// A creation flow that already knows which doctype this template is
		// for (e.g. Trip's "+ New Template" button, which passes
		// {reference_doctype: "Trip"} to frappe.new_doc) pre-fills the field —
		// lock it so the user can't pick a different doctype by mistake.
		// Every other entry point (Email Template list "+ Add", Customize
		// Form, etc.) leaves it blank and fully editable.
		if (frm.is_new() && frm.doc.reference_doctype) {
			frm.set_df_property("reference_doctype", "read_only", 1);
		}
	},
});
