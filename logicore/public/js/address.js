// The "Links" (Dynamic Link) table is hidden by default for everyone
// (Address-links-hidden property setter) so ordinary users never manually
// mislink an address via the full form or Quick Entry — see
// address_quick_entry_override.js for the Quick Entry side of this.
// Administrator / System Manager still need to see + edit it on the full
// form, to correct any address that got wrongly linked before the fix.
frappe.ui.form.on("Address", {
	refresh(frm) {
		const can_manage_links =
			frappe.user.has_role("System Manager") || frappe.user.has_role("Administrator");
		const hidden = can_manage_links ? 0 : 1;
		// "linked_with" is the ("Reference") section break wrapping "links" —
		// also hidden by its own property setter, so it must be un-hidden too.
		frm.set_df_property("linked_with", "hidden", hidden);
		frm.set_df_property("links", "hidden", hidden);
		frm.refresh_field("linked_with");
		frm.refresh_field("links");
	},
});
