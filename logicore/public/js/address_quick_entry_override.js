// india_compliance's AddressQuickEntryForm (public/js/quick_entry.js) always
// injects visible "Link Document Type" / "Link Name" fields into every "New
// Address" dialog, everywhere — Trip, Company, Customer, Supplier, Bank, etc.
// Its own set_default_values()/guess_default_party() already resolves and
// fills the correct party link in the background for known contexts
// (Customer/Supplier/Company/Lead/sales/purchase docs); Trip and any other
// doctype simply get no link, which is correct — a Trip address should never
// carry a party link. Since that resolution already happens silently, the
// two fields never need to be user-visible/editable: showing them only
// invites a user to manually pick the wrong doctype (e.g. selecting
// "Customer" from Trip), which mislinks the new Address and — for Customer —
// can even silently hijack that Customer's primary address via
// Address.after_insert_set_primary. So keep them permanently hidden
// everywhere; the underlying auto-link logic is untouched.
frappe.provide("frappe.ui.form");

if (frappe.ui.form.AddressQuickEntryForm) {
	const BaseAddressQuickEntryForm = frappe.ui.form.AddressQuickEntryForm;

	frappe.ui.form.AddressQuickEntryForm = class extends BaseAddressQuickEntryForm {
		get_dynamic_link_fields() {
			const fields = super.get_dynamic_link_fields();
			fields.forEach((field) => {
				if (field.fieldname === "link_doctype" || field.fieldname === "link_name") {
					field.hidden = 1;
					field.reqd = 0;
				}
			});
			return fields;
		}
	};
}
