// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Type", {
	refresh(frm) {
		update_detention_labels(frm);
		if (!frm.is_new()) {
			frm.set_df_property("name1", "hidden", 0);
			frm.refresh_field("name1");
		}
	},
	upto_day(frm) {
		update_detention_labels(frm);
	},
});

// Quick Entry dialog does not run the standard frm triggers above, so it
// needs its own field-level onchange hook to keep the labels live.
frappe.ui.form.VehicleTypeQuickEntryForm = class VehicleTypeQuickEntryForm extends (
	frappe.ui.form.QuickEntryForm
) {
	render_dialog() {
		super.render_dialog();
		update_quick_entry_detention_labels(this);

		const upto_day_field = this.fields_dict.upto_day;
		if (upto_day_field && upto_day_field.$input) {
			// react on every keystroke, not just on blur
			upto_day_field.$input.on("input change", () => update_quick_entry_detention_labels(this));
		}
	}
};

function detention_labels(upto_day) {
	const days = cint(upto_day);
	return {
		first: `Detention/Day Rate (First ${days} Days)`,
		onwards: `Detention/Day (From ${ordinal(days + 1)} Day Onwards)`,
	};
}

function update_detention_labels(frm) {
	const labels = detention_labels(frm.doc.upto_day);
	frm.set_df_property("detention_per_day_first", "label", labels.first);
	frm.set_df_property("detention_per_day_onwards", "label", labels.onwards);
	frm.refresh_field("detention_per_day_first");
	frm.refresh_field("detention_per_day_onwards");
}

function update_quick_entry_detention_labels(qe) {
	const upto_day_field = qe.fields_dict.upto_day;
	const raw_value = upto_day_field && upto_day_field.$input ? upto_day_field.$input.val() : qe.get_value("upto_day");
	const labels = detention_labels(raw_value);
	qe.set_df_property("detention_per_day_first", "label", labels.first);
	qe.set_df_property("detention_per_day_onwards", "label", labels.onwards);
}

function ordinal(n) {
	const suffixes = ["th", "st", "nd", "rd"];
	const v = n % 100;
	return n + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
}
