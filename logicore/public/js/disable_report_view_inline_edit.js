// Report View datatable allows double-click cell editing that writes straight to the
// DB, bypassing form validations, client scripts, and server-side controller hooks.
// Patch Frappe's own permission gate (is_editable) so every cell is reported as
// non-editable, forcing users through the full form (frappe.model.can_write / doc
// events / validations) to make any change. Report View itself remains the default
// list view — only inline cell editing is blocked.
(function () {
	if (!frappe.views || !frappe.views.ReportView) return;
	if (frappe.views.ReportView.prototype._tms_inline_edit_disabled) return;

	frappe.views.ReportView.prototype.is_editable = function () {
		return false;
	};
	frappe.views.ReportView.prototype._tms_inline_edit_disabled = true;
})();
