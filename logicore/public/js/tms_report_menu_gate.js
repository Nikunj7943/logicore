// Report View's menu (any doctype, "Report" view) exposes Toggle Chart / Pick
// Columns / Setup Auto Email / Save As to every user by default. Only a TMS
// Admin (TMS User Group is_admin=1, or a real site admin -- Administrator /
// System Manager) should see these; everyone else gets the same report view
// minus these 4 actions. frappe.boot.tms_can_use_admin_report_menu is computed
// server-side per user in tms_report_menu.py (boot_session hook).
(function () {
	const HIDDEN_LABELS = new Set([
		__("Toggle Chart"),
		__("Pick Columns"),
		__("Setup Auto Email"),
		__("Save As"),
	]);

	function patch_report_view() {
		const ReportView = frappe.views && frappe.views.ReportView;
		if (!ReportView || ReportView.prototype._tms_report_menu_gate_patched) {
			return Boolean(ReportView);
		}

		const original_report_menu_items = ReportView.prototype.report_menu_items;

		ReportView.prototype.report_menu_items = function () {
			const items = original_report_menu_items.call(this) || [];
			if (frappe.boot && frappe.boot.tms_can_use_admin_report_menu) {
				return items;
			}
			return items.filter((item) => !HIDDEN_LABELS.has(item.label));
		};

		ReportView.prototype._tms_report_menu_gate_patched = true;
		return true;
	}

	if (!patch_report_view()) {
		const patch_timer = window.setInterval(() => {
			if (patch_report_view()) {
				window.clearInterval(patch_timer);
			}
		}, 200);
	}
})();
