// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Repair Category", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.set_df_property("category_name", "hidden", 0);
			frm.refresh_field("category_name");
		}
	},
});
