// Same bug/fix as customer.js: creating an Address/Contact from a NEW
// (unsaved) Supplier pre-fills the Dynamic Link with the temporary local
// docname (e.g. "new-supplier-xxx"), which fails validation on save with
// "Could not find Row #1: Link Name: new-supplier-xxx". This patch saves
// the Supplier first (silently) so the link resolves to a real name.
frappe.ui.form.on("Supplier", {
	refresh(frm) {
		_logicore_supplier_patch_link_new_doc(frm, "supplier_primary_address", "Address");
		_logicore_supplier_patch_link_new_doc(frm, "supplier_primary_contact", "Contact");
		_logicore_supplier_intercept_html_btn(frm, "address_html", "Address");
		_logicore_supplier_intercept_html_btn(frm, "contact_html", "Contact");
	},
});

async function _logicore_supplier_ensure_saved(frm) {
	if (!frm.is_new()) return true;
	if (!frm.doc.supplier_name) {
		frappe.msgprint({
			title: __("Supplier Name Required"),
			message: __("Please enter Supplier Name before adding an address or contact."),
			indicator: "orange",
		});
		return false;
	}
	try {
		await frm.save();
		return !frm.is_new();
	} catch (err) {
		return false; // Frappe surfaces the actual validation error to the user
	}
}

function _logicore_supplier_patch_link_new_doc(frm, fieldname, child_dt) {
	const field = frm.get_field(fieldname);
	if (!field || field._logicore_patched) return;
	if (typeof field.new_doc !== "function") return;
	field._logicore_patched = true;

	field.df.get_route_options_for_new_doc = () => ({
		links: [{ link_doctype: "Supplier", link_name: frm.docname }],
	});

	const original = field.new_doc.bind(field);
	field.new_doc = async function () {
		const ok = await _logicore_supplier_ensure_saved(frm);
		if (!ok) return;
		return original();
	};
}

function _logicore_supplier_intercept_html_btn(frm, html_field, child_dt) {
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
			if (!frm.is_new()) return; // saved Supplier → standard Frappe flow

			e.preventDefault();
			e.stopImmediatePropagation();

			const ok = await _logicore_supplier_ensure_saved(frm);
			if (!ok) return;

			frappe.new_doc(child_dt, {
				links: [{ link_doctype: "Supplier", link_name: frm.docname }],
			});
		},
		true // capture phase — runs before Frappe's bubble-phase handler
	);
}

frappe.ui.form.on("Supplier", {
	onload: function (frm) {
		if (frm.is_new() && !frm.doc.custom_company) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "User",
					filters: { name: frappe.session.user },
					fieldname: "last_active",
				},
				callback: function () {
					const default_company = frappe.defaults.get_user_default("company");
					if (default_company) {
						frm.set_value("custom_company", default_company);
					} else {
						const global_company = frappe.defaults.get_global_default("company");
						if (global_company) {
							frm.set_value("custom_company", global_company);
						}
					}
				},
			});
		}
	},

	refresh: function (frm) {
		if (frm.is_new() && !frm.doc.custom_company) {
			const default_company =
				frappe.defaults.get_user_default("company") ||
				frappe.defaults.get_global_default("company");
			if (default_company) {
				frm.set_value("custom_company", default_company);
			}
		}
	},
});
