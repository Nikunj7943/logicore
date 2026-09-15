// Keeps the "LogiCore" sidebar pinned on every route — list/report views,
// query reports, dashboards, forms, print, etc. Frappe's own
// set_workspace_sidebar() switches to a *different* sidebar whenever the
// current page isn't listed as an item inside "LogiCore" (e.g. any stock
// ERPNext report belongs to its own module's sidebar), which is what made
// the sidebar silently flip away on every report/dashboard open. Only an
// explicit route straight to another workspace (List/<Workspace>) is still
// honoured, matching Frappe's own direct-navigation rule.
(function () {
	const PINNED_SIDEBAR = "LogiCore";

	function patch() {
		const proto = frappe.ui && frappe.ui.Sidebar && frappe.ui.Sidebar.prototype;
		if (!proto || proto.__tms_pinned_sidebar_patch) return;

		const original_set_workspace_sidebar = proto.set_workspace_sidebar;

		proto.set_workspace_sidebar = function (router) {
			try {
				const route = frappe.get_route();
				const is_direct_workspace_route =
					route.length === 2 &&
					frappe.boot.workspace_sidebar_item &&
					frappe.boot.workspace_sidebar_item[route[1].toLowerCase()];
				const pinned_available =
					frappe.boot.workspace_sidebar_item &&
					frappe.boot.workspace_sidebar_item[PINNED_SIDEBAR.toLowerCase()];

				if (!is_direct_workspace_route && pinned_available) {
					if (this.sidebar_title !== PINNED_SIDEBAR) {
						frappe.app.sidebar.setup(PINNED_SIDEBAR);
					}
					this.set_active_workspace_item();
					return;
				}
			} catch (e) {
				console.error(e);
			}

			return original_set_workspace_sidebar.call(this, router);
		};

		proto.__tms_pinned_sidebar_patch = true;
	}

	if (frappe.ui && frappe.ui.Sidebar) {
		patch();
	} else {
		$(document).on("app_ready", patch);
	}
})();
