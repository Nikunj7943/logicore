// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Repair Sub Category", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Repair Sub Category", {
	refresh(frm) {
		if (frm.in_dialog) {
			setTimeout(() => {
				const $input = frm.get_field("sub_category_name").$input;
				if ($input) $input.focus();
			}, 100);
		}
	},
});
