(function () {
	function get_alert_settings() {
		return (frappe.boot && frappe.boot.tms_alert_settings) || { enabled: 0, rules: [] };
	}

	function indicator_for_doc(rule, doc) {
		const value = doc[rule.date_field];
		if (!value) return null;
		const diff = frappe.datetime.get_diff(value, frappe.datetime.get_today());
		if (diff < 0) return [__("Overdue"), "red",    `${rule.date_field},<,${frappe.datetime.get_today()}`];
		if (diff === 0) return [__("Urgent"),  "orange", `${rule.date_field},=,${frappe.datetime.get_today()}`];
		if (diff <= (rule.alert_before_days || 7)) return [__("Upcoming"), "green", `${rule.date_field},>,${frappe.datetime.get_today()}`];
		return null;
	}

	function register_list_indicators() {
		// Alert list indicators are intentionally disabled for now.
		// Keep the alert settings data intact, but do not tag records with
		// Upcoming / Urgent / Overdue badges until we revisit the UX later.
		return;
	}

	if (frappe.boot) {
		register_list_indicators();
	} else {
		$(document).on("app_ready", register_list_indicators);
	}
})();
