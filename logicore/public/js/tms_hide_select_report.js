// Report View's "Select Report" dropdown (frappe/list/list_view_select.js,
// ListViewSelect.setup_views().Report.current_view_handler) lists every
// Query/Script Report linked to the doctype plus a "Report Builder" action.
// Not wanted on any doctype here — suppress it by no-oping the one call site
// that builds it, instead of hiding it with CSS after the fact.
(function () {
	function patch_list_view_select() {
		const ListViewSelect = frappe.views && frappe.views.ListViewSelect;
		if (!ListViewSelect || ListViewSelect.prototype._tms_select_report_patched) {
			return Boolean(ListViewSelect);
		}

		const original = ListViewSelect.prototype.setup_dropdown_in_navbar;
		ListViewSelect.prototype.setup_dropdown_in_navbar = function (view, items, default_action) {
			if (view === "Report") return;
			return original.call(this, view, items, default_action);
		};

		ListViewSelect.prototype._tms_select_report_patched = true;
		return true;
	}

	if (!patch_list_view_select()) {
		const patch_timer = window.setInterval(() => {
			if (patch_list_view_select()) {
				window.clearInterval(patch_timer);
			}
		}, 200);
	}
})();
