// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// Each Autocomplete field is filled from the target doctype's own fields, so the
// user picks by label instead of having to remember raw fieldnames.
const FIELD_PICKERS = [
	{
		fieldname: "date_fieldname",
		matches: (df) => ["Date", "Datetime"].includes(df.fieldtype),
		empty_message: __("This doctype has no Date or Datetime field."),
	},
	{
		fieldname: "amount_fieldname",
		matches: (df) => ["Currency", "Float", "Int"].includes(df.fieldtype),
		empty_message: __("This doctype has no Currency, Float or Int field."),
	},
	{
		fieldname: "account_fieldname",
		matches: (df) => df.fieldtype === "Link" && df.options === "Account Head",
		empty_message: __("This doctype has no Link field pointing to Account Head."),
	},
	{
		fieldname: "reconciled_fieldname",
		matches: (df) => df.fieldtype === "Check",
		empty_message: __("This doctype has no Check field. Add an 'is_reconciled' field to it first."),
	},
	{
		fieldname: "reconciliation_link_fieldname",
		matches: (df) => df.fieldtype === "Link" && df.options === "TMS Bank Reconciliation",
		empty_message: __(
			"This doctype has no Link field pointing to TMS Bank Reconciliation. Add a 'bank_reconciliation' field to it first."
		),
	},
	{
		fieldname: "credit_account_fieldname",
		matches: (df) => df.fieldtype === "Link" && df.options === "Account Head",
		empty_message: __("This doctype has no Link field pointing to Account Head."),
	},
	{
		fieldname: "credit_reconciled_fieldname",
		matches: (df) => df.fieldtype === "Check",
		empty_message: __("This doctype has no Check field."),
	},
	{
		fieldname: "credit_reconciliation_link_fieldname",
		matches: (df) => df.fieldtype === "Link" && df.options === "TMS Bank Reconciliation",
		empty_message: __("This doctype has no Link field pointing to TMS Bank Reconciliation."),
	},
];

// set_df_property("options", ...) alone does NOT refresh the Autocomplete
// control's internal label lookup (ControlAutocomplete#_data, populated only
// by #set_data) — so the closed input kept showing the raw fieldname instead
// of the label. Calling set_data() directly on the control keeps that lookup
// in sync; the subsequent refresh_field() then re-renders the current value
// through it.
function set_picker_options(frm, fieldname, options) {
	frm.fields_dict[fieldname].df.options = options;
	frm.fields_dict[fieldname].set_data(options);
}

function populate_field_pickers(frm) {
	if (!frm.doc.target_doctype) {
		FIELD_PICKERS.forEach((picker) => {
			set_picker_options(frm, picker.fieldname, []);
			frm.refresh_field(picker.fieldname);
		});
		return;
	}

	frappe.model.with_doctype(frm.doc.target_doctype, () => {
		const meta_fields = frappe.get_meta(frm.doc.target_doctype).fields || [];

		FIELD_PICKERS.forEach((picker) => {
			const options = meta_fields.filter(picker.matches).map((df) => ({
				value: df.fieldname,
				// Label is what the user recognises and what gets shown; the
				// fieldname is what actually gets stored and matched against,
				// so keep it visible as secondary text to stay verifiable.
				label: df.label || df.fieldname,
				description: df.fieldname,
			}));

			// Remember the schema description once, before any empty_message overwrites it.
			if (picker.original_description === undefined) {
				picker.original_description = frm.fields_dict[picker.fieldname].df.description || "";
			}

			set_picker_options(frm, picker.fieldname, options);
			frm.set_df_property(
				picker.fieldname,
				"description",
				options.length ? picker.original_description : picker.empty_message
			);
			frm.refresh_field(picker.fieldname);
		});

		populate_display_fieldnames_hint(frm, meta_fields);
	});
}

let display_fieldnames_original_description;

function populate_display_fieldnames_hint(frm, meta_fields) {
	// display_fieldnames is freeform (comma-separated), unlike the single-select
	// FIELD_PICKERS above, so it just gets a hint listing what is available to
	// type rather than a strict dropdown.
	if (display_fieldnames_original_description === undefined) {
		display_fieldnames_original_description = frm.fields_dict.display_fieldnames.df.description || "";
	}
	const available = meta_fields
		.filter((field) => !field.hidden && field.fieldname && field.label)
		.map((field) => `${field.fieldname} (${field.label})`)
		.join(", ");
	frm.set_df_property(
		"display_fieldnames",
		"description",
		available
			? `${display_fieldnames_original_description} Available on ${frm.doc.target_doctype}: ${available}`
			: display_fieldnames_original_description
	);
}

frappe.ui.form.on("TMS Reconciliation Source", {
	refresh(frm) {
		populate_field_pickers(frm);
	},

	target_doctype(frm) {
		// Fieldnames from the previous doctype almost certainly do not exist on the
		// new one, so clear them rather than leave silently-broken config behind.
		FIELD_PICKERS.forEach((picker) => frm.set_value(picker.fieldname, null));
		frm.set_value("display_fieldnames", null);
		populate_field_pickers(frm);
	},
});
