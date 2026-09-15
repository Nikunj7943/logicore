// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Subformat", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.set_df_property("businesssubformate", "hidden", 0);
			frm.refresh_field("businesssubformate");
		}
	},
});
