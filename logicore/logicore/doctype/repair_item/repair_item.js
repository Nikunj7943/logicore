// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Repair Item", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Repair Item", {
	refresh(frm) {
		// When opened as quick entry, focus the empty Repair Item field directly
		if (frm.in_dialog) {
			setTimeout(() => {
				const $input = frm.get_field("item_name").$input;
				if ($input) $input.focus();
			}, 100);
		}
	},
});
