// Two paths can create an address from a NEW (unsaved) Customer:
//   1. Customer Primary Address Link field → "+ Create a new Address" dialog
//   2. Address & Contact tab → address_html "+ New Address" button
//
// In both, Frappe pre-fills the new Address's Dynamic Link with the parent's
// temporary local docname (e.g. "new-customer-xxx"). On save, validation fails
// with: "Could not find Row #1: Link Name: new-customer-xxx".
//
// This patch:
//   • Overrides each Link field's `new_doc()` so the Customer is saved first
//     (giving it a real name) before the Quick Entry dialog opens.
//   • Intercepts capture-phase clicks on the address_html / contact_html
//     "+ New" buttons so they also save Customer first (when user reaches them
//     after the Customer is saved and edits a sibling, or in any future case).
//
// Frappe's default render-on-save behavior for address_html / contact_html is
// preserved — those sections only become visible once the Customer is saved.
//
// The Address form & all custom fields (custom_address_code, custom_cityname,
// custom_postal_code, etc.) remain unchanged.

frappe.ui.form.on("Customer", {
	refresh(frm) {
		_logicore_patch_link_new_doc(frm, "customer_primary_address", "Address");
		_logicore_patch_link_new_doc(frm, "customer_primary_contact", "Contact");
		_logicore_intercept_html_btn(frm, "address_html", "Address");
		_logicore_intercept_html_btn(frm, "contact_html", "Contact");
	},
});

async function _logicore_ensure_saved(frm) {
	if (!frm.is_new()) return true;
	if (!frm.doc.customer_name) {
		frappe.msgprint({
			title: __("Customer Name Required"),
			message: __("Please enter Customer Name before adding an address or contact."),
			indicator: "orange",
		});
		return false;
	}
	// Silent backend save — required so the new Address's Dynamic Link can
	// resolve to a real Customer name. No popup or confirmation; the user
	// implicitly authorised it by clicking "+ Create a new Address". Their
	// remaining edits on the Customer form are saved as part of this call.
	try {
		await frm.save();
		return !frm.is_new();
	} catch (err) {
		return false; // Frappe surfaces the actual validation error to the user
	}
}

function _logicore_patch_link_new_doc(frm, fieldname, child_dt) {
	const field = frm.get_field(fieldname);
	if (!field || field._logicore_patched) return;
	if (typeof field.new_doc !== "function") return;
	field._logicore_patched = true;

	// Frappe's stock ControlLink.new_doc() does NOT auto-fill the Dynamic
	// Link (links table) unless the docfield defines get_route_options_for_new_doc.
	// Without this, the Address/Contact created from this field is never
	// linked back to the Customer, so it can't become customer_primary_address.
	field.df.get_route_options_for_new_doc = () => ({
		links: [{ link_doctype: "Customer", link_name: frm.docname }],
	});

	const original = field.new_doc.bind(field);
	field.new_doc = async function () {
		const ok = await _logicore_ensure_saved(frm);
		if (!ok) return;
		return original();
	};
}

function _logicore_intercept_html_btn(frm, html_field, child_dt) {
	const dict = frm.fields_dict && frm.fields_dict[html_field];
	if (!dict || !dict.wrapper) return;
	const el = dict.wrapper;
	if (el._logicore_btn_patched) return;
	el._logicore_btn_patched = true;

	el.addEventListener(
		"click",
		async function (e) {
			const sel =
				child_dt === "Address"
					? ".btn-address.new, .btn-new-address, .btn-address, [data-action='new_address'], a.new-address"
					: ".btn-contact.new, .btn-new-contact, .btn-contact, [data-action='new_contact'], a.new-contact";
			const target = e.target.closest(sel);
			if (!target) return;
			if (!frm.is_new()) return; // saved Customer → standard Frappe flow

			e.preventDefault();
			e.stopImmediatePropagation();

			const ok = await _logicore_ensure_saved(frm);
			if (!ok) return;

			frappe.new_doc(child_dt, {
				links: [{ link_doctype: "Customer", link_name: frm.docname }],
			});
		},
		true // capture phase — runs before Frappe's bubble-phase handler
	);
}

