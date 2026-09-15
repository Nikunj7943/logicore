// Frappe hides a doctype's own `field:<x>` autoname field once the record is
// saved (funneling users toward Menu > Rename) — see frappe/public/js/frappe/form/form.js
// toggle_display() for meta.autoname starting with "field:". These are standard
// ERPNext/Frappe doctypes we did not create, so we un-hide the field via a global
// client script (app_include_js) instead of touching vendor .js files.
const TMS_NAMING_FIELD_BY_DOCTYPE = {
	Vehicle: "license_plate",
	Company: "company_name",
	UOM: "uom_name",
	"Item Group": "item_group_name",
	Item: "item_code",
	"GST HSN Code": "hsn_code",
	"Supplier Group": "supplier_group_name",
	"Customer Group": "customer_group_name",
	Branch: "branch",
};

Object.entries(TMS_NAMING_FIELD_BY_DOCTYPE).forEach(([doctype, fieldname]) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			if (frm.is_new()) return;
			const unhide = () => {
				frm.set_df_property(fieldname, "hidden", 0);
				frm.refresh_field(fieldname);
			};
			unhide();
			// Some standard doctypes' own controllers re-run refresh_fields() after
			// this trigger (e.g. via a later async callback), which re-hides a
			// `field:<x>` autoname field again. Re-assert once more shortly after,
			// same defensive pattern already used in vehicle.js for last_odometer.
			setTimeout(unhide, 200);
		},
	});
});
