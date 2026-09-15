// Override: Navbar home icon → LogiCore workspace
frappe.breadcrumbs.clear = function () {
	this.$breadcrumbs = $(".navbar-breadcrumbs").empty();
	this.append_breadcrumb_element("/app/logicore-tms", frappe.utils.icon("home"));
};

// Redirect "Home" workspace → LogiCore so the desk never shows ERPNext module cards
(function () {
	const TMS_WORKSPACE_SLUG = "logicore-tms";
	const TMS_WORKSPACE_NAME = "LogiCore";

	// Non-TMS workspace slugs that should silently redirect to TMS home
	const HOME_SLUGS = new Set(["home", "", undefined, null]);

	function redirectIfHome() {
		const route = frappe.get_route();
		// Only act when we are inside the Workspaces page
		if (!route || route[0] !== "Workspaces") return;
		const slug = (route[1] || "").toLowerCase();
		if (HOME_SLUGS.has(slug)) {
			// Replace so the back-button doesn't loop
			frappe.route_flags.replace_route = true;
			frappe.set_route(TMS_WORKSPACE_SLUG);
		}
	}

	// Pin localStorage so Frappe's own get_page_to_show() defaults to TMS
	function pinLocalStorage() {
		try {
			if (localStorage.getItem("current_page") !== TMS_WORKSPACE_NAME) {
				const route = frappe.get_route();
				// Only override when not navigating to another specific workspace
				if (!route || !route[1] || HOME_SLUGS.has((route[1] || "").toLowerCase())) {
					localStorage.setItem("current_page", TMS_WORKSPACE_NAME);
					localStorage.setItem("is_current_page_public", "true");
				}
			}
		} catch (e) {}
	}

	$(document).on("app_ready", function () {
		pinLocalStorage();
		redirectIfHome();
	});

	frappe.router.on("change", function () {
		redirectIfHome();
	});
})();
