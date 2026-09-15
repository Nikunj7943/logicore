// Force full-width layout — set localStorage so Frappe's own boot also picks it up
localStorage.setItem("container_fullwidth", "true");
// Keep left nav sidebar in expanded mode so section-break headers and chevrons remain visible
localStorage.setItem("sidebar-expanded", "true");

// Doctypes whose *_list.js manages its own default filters — skip generic clear
const TMS_FILTER_RESET_EXCLUDE = new Set(["Trip", "Amazon Trip"]);
const TMS_SIDEBAR_DATE_DEFAULTS = {
	"Account Ledger": "posting_date",
	"Amazon trip - Import": "import_date",
	"Battery Expenses": "purchase_date",
	"Compliances": "issue_date",
	"Fuel Urea Expenses": "date",
	"Import Log": "started_at",
	"Payment": "date",
	"Receipt": "payment_date",
	"Repair Expenses": "date",
	"Service Logs": "voucher_date",
	"Staff Attendance": "date",
	"Staff Payroll": "payroll_date",
	"Supplier Payment": "payment_date",
	"TMS Bank Reconciliation": "reconciliation_date",
	"Trip POD Import": "import_date",
	"Vendor Payment": "payment_date",
	"Tyre Expenses": "purchase_date",
};

// Doctypes with a Date-based default sort (instead of ID/name desc).
// Keep in sync with each doctype's own "sort_field"/"sort_order" meta —
// see logicore/scripts/set_default_sort.py.
const TMS_SIDEBAR_SORT_OVERRIDE = {
	"Payment": { sort_by: "date", sort_order: "desc" },
	"Receipt": { sort_by: "payment_date", sort_order: "desc" },
	"Amazon Trip": { sort_by: "trip_date", sort_order: "desc" },
	"Amazon trip - Import": { sort_by: "import_date", sort_order: "desc" },
	"Repair Expenses": { sort_by: "date", sort_order: "desc" },
	"Fuel Urea Expenses": { sort_by: "date", sort_order: "desc" },
	"Battery Expenses": { sort_by: "purchase_date", sort_order: "desc" },
	"Tyre Expenses": { sort_by: "purchase_date", sort_order: "desc" },
	"Service Logs": { sort_by: "voucher_date", sort_order: "desc" },
	"Vehicle Finance": { sort_by: "date_of_emi", sort_order: "desc" },
	"Compliances": { sort_by: "issue_date", sort_order: "desc" },
	"Staff Attendance": { sort_by: "date", sort_order: "desc" },
	"Staff Payroll": { sort_by: "payroll_date", sort_order: "desc" },
	"Purchase Invoice": { sort_by: "posting_date", sort_order: "desc" },
	"Stock Entry": { sort_by: "posting_date", sort_order: "desc" },
	"Payment Entry": { sort_by: "posting_date", sort_order: "desc" },
	"Leave Application": { sort_by: "posting_date", sort_order: "desc" },
	"Trip": { sort_by: "tcntrip_date", sort_order: "desc" },
	"Trip POD Import": { sort_by: "import_date", sort_order: "desc" },
	"Vendor Payment": { sort_by: "payment_date", sort_order: "desc" },
};

function _tmsSortFor(doctype) {
	return TMS_SIDEBAR_SORT_OVERRIDE[doctype] || { sort_by: "name", sort_order: "desc" };
}

// Robustly wipes filters on a ListView instance — works for fresh and cached
// views. Uses clear(true) to also clear standard quick-filter fields (the "ID"
// search slot etc.) and refresh the rows. Then explicitly updates the filter
// button label so the "Filters N" badge resets to "Filters" with no count.
function _tmsClearListFilters(listview) {
	if (!listview || !listview.filter_area) return;
	try { listview.filter_area.clear(true); } catch (e) {}
	try {
		const fl = listview.filter_area.filter_list;
		if (fl) {
			fl.filters = [];
			if (typeof fl.update_filter_button === "function") {
				fl.update_filter_button();
			}
			if (typeof fl.toggle_empty_filters === "function") {
				fl.toggle_empty_filters(true);
			}
		}
	} catch (e) {}
}

// No longer called by the sidebar click handler below (it used to set
// frappe.route_options from this and let native navigation apply it -- see
// the root-cause comment on the click handler for why that raced under
// rapid clicks and was replaced with a direct filter_area.add() apply).
// Kept, not deleted, in case a genuine non-sidebar route_options producer
// (a dashboard card, a saved link) ever needs the same shape.
// function _tmsDefaultRouteOptionsFor(doctype) {
// 	const fieldname = TMS_SIDEBAR_DATE_DEFAULTS[doctype];
// 	if (!fieldname) return null;
//
// 	const today = frappe.datetime.get_today();
// 	return {
// 		[fieldname]: [
// 			[">=", today],
// 			["<=", today],
// 		],
// 	};
// }

function _tmsApplyDefaultDateRange(view, doctype) {
	const fieldname = TMS_SIDEBAR_DATE_DEFAULTS[doctype];
	if (!view || !fieldname || !view.filter_area) return Promise.resolve(false);

	const today = frappe.datetime.get_today();
	const fa = view.filter_area;

	frappe._tms_df_manual = frappe._tms_df_manual || {};
	frappe._tms_df_manual[doctype] = true;
	TMS.dateFilterBar.clearDateFilters(view, fieldname);

	const addResult = fa.add([
		[doctype, fieldname, ">=", today],
		[doctype, fieldname, "<=", today],
	], true);

	// Callers that need to know the filter has ACTUALLY landed (not just been
	// kicked off) await this returned promise -- see the sidebar-click queue
	// below, which chains the next navigation's work on it.
	return Promise.resolve(addResult)
		.catch((e) => console.error(e))
		.finally(() => {
			setTimeout(() => {
				frappe._tms_df_manual[doctype] = false;
			}, 0);
		});
}

// Poll for `frappe.get_route()` to actually settle on `targetDoctype`'s
// List/Report route. Needed because none of Frappe's own async signals
// (frappe.set_route()'s promise, router "change" event) reliably correlate
// with "before_refresh() has consumed route_options for THIS navigation" --
// see the long comment on the sidebar click handler below for why that
// matters. Polling frappe.get_route() itself is the one thing that's
// unambiguous: it's a plain synchronous property, no timing heuristics.
function _tmsWaitForRoute(targetDoctype, timeoutMs) {
	return new Promise((resolve) => {
		const start = Date.now();
		(function poll() {
			const r = frappe.get_route();
			if (r && r[0] === "List" && r[1] === targetDoctype) {
				resolve(true);
				return;
			}
			if (Date.now() - start > timeoutMs) {
				resolve(false);
				return;
			}
			setTimeout(poll, 30);
		})();
	});
}

// Poll for the actual ListView/ReportView *instance* for targetDoctype to
// exist and have a filter_area -- i.e. the view is far enough along to accept
// a direct filter_area.add() call. cur_list only reflects the doctype whose
// view is currently on screen; frappe.get_list_view() finds a cached instance
// even before it's re-shown, so try both.
function _tmsWaitForView(targetDoctype, timeoutMs) {
	return new Promise((resolve) => {
		const start = Date.now();
		(function poll() {
			const view =
				(window.cur_list && cur_list.doctype === targetDoctype && cur_list) ||
				(frappe.get_list_view && frappe.get_list_view(targetDoctype));
			if (view && view.filter_area) {
				resolve(view);
				return;
			}
			if (Date.now() - start > timeoutMs) {
				resolve(null);
				return;
			}
			setTimeout(poll, 30);
		})();
	});
}

function _tmsMarkReportKeepVisible(doctype) {
	if (!doctype) return;
	frappe._tms_keep_report_visible_doctype = doctype;
	if (frappe._tms_keep_report_visible_timer) {
		clearTimeout(frappe._tms_keep_report_visible_timer);
	}
	frappe._tms_keep_report_visible_timer = setTimeout(function () {
		if (frappe._tms_keep_report_visible_doctype === doctype) {
			frappe._tms_keep_report_visible_doctype = null;
		}
		frappe._tms_keep_report_visible_timer = null;
	}, 5000);
}

function _tmsMarkCurrentViewKeepVisible(doctype) {
	if (!doctype) return;
	frappe._tms_keep_current_view_visible_doctype = doctype;
	if (frappe._tms_keep_current_view_visible_timer) {
		clearTimeout(frappe._tms_keep_current_view_visible_timer);
	}
	frappe._tms_keep_current_view_visible_timer = setTimeout(function () {
		if (frappe._tms_keep_current_view_visible_doctype === doctype) {
			frappe._tms_keep_current_view_visible_doctype = null;
		}
		frappe._tms_keep_current_view_visible_timer = null;
	}, 5000);
}

function _tmsResetRefreshThrottle(doctype) {
	if (!doctype) return;

	try {
		if (window.cur_list && cur_list.doctype === doctype) {
			cur_list.last_args = null;
		}
	} catch (e) {}

	try {
		if (frappe.query_report && frappe.query_report.doctype === doctype) {
			frappe.query_report.last_args = null;
		}
	} catch (e) {}

	try {
		const listview = frappe.get_list_view && frappe.get_list_view(doctype);
		if (listview) {
			listview.last_args = null;
		}
	} catch (e) {}
}

// ── TMS sidebar guard ───────────────────────────────────────────────────────
// Problem: Frappe's set_workspace_sidebar() calls filter_sidebars_from_app()
// using router.meta.module, which may be STALE from a previously visited
// non-TMS page.  That filters out the correct "LogiCore" sidebar, leaving
// sidebars=[], which triggers show_sidebar_for_module() with the wrong module
// and switches the left nav to the wrong sidebar (Dashboards/Reports/Pages).
//
// Fix: after Frappe's handler runs, detect the mismatch and correct it. We
// check boot data — if the current page's entity is listed as a link_to item
// inside "logicore" sidebar but a different sidebar is now active, switch
// back to "LogiCore".
//
// This has to run from two places, not just router.on("change"): Query Report
// (and custom Page) views resolve their doc/module ASYNCHRONOUSLY and only
// then call frappe.app.sidebar.show_sidebar_for_module() — well after the
// router's synchronous "change" listeners have already fired and finished.
// So we also monkey-patch show_sidebar_for_module itself to re-run the guard
// right after Frappe's own (possibly wrong) switch, whenever it happens.
function _tmsEnforceSidebar() {
	var sidebar = frappe.app && frappe.app.sidebar;
	if (!sidebar || !frappe.boot || !frappe.boot.workspace_sidebar_item) return;
	var tmsSidebar = frappe.boot.workspace_sidebar_item["logicore"];
	if (!tmsSidebar) return;
	var route = frappe.get_route();
	if (!route || !route.length) return;
	// entity_name is route[1] for List/Form/query-report routes; route[0] for Pages
	var entityName = route.length >= 2 ? route[1] : route[0];
	var inTms = (tmsSidebar.items || []).some(function (item) {
		return item.link_to === entityName;
	});
	if (inTms && sidebar.sidebar_title !== "LogiCore") {
		sidebar.setup("LogiCore");
	}
}

$(document).on("app_ready", function () {
	// Apply immediately after boot
	document.body.classList.add("full-width");

	if (frappe.app && frappe.app.sidebar && frappe.app.sidebar.show_sidebar_for_module) {
		var _origShowSidebarForModule = frappe.app.sidebar.show_sidebar_for_module.bind(frappe.app.sidebar);
		frappe.app.sidebar.show_sidebar_for_module = function (module) {
			_origShowSidebarForModule(module);
			_tmsEnforceSidebar();
		};
	}

	if (frappe.views && frappe.views.BaseList && !frappe.views.BaseList.prototype._tms_keep_visible_patched) {
		const _origShowSkeleton = frappe.views.BaseList.prototype.show_skeleton;
		frappe.views.BaseList.prototype.show_skeleton = function () {
			if (frappe._tms_keep_current_view_visible_doctype === this.doctype) {
				return;
			}
			return _origShowSkeleton.call(this);
		};
		frappe.views.BaseList.prototype._tms_keep_visible_patched = true;
	}

	if (frappe.views && frappe.views.QueryReport && !frappe.views.QueryReport.prototype._tms_keep_visible_patched) {
		const _origRefreshReport = frappe.views.QueryReport.prototype.refresh_report;
		frappe.views.QueryReport.prototype.refresh_report = function (route_options) {
			const keepVisible = frappe._tms_keep_report_visible_doctype === this.doctype;
			if (!keepVisible) {
				return _origRefreshReport.call(this, route_options);
			}

			const originalToggleMessage = this.toggle_message;
			const originalShowLoadingScreen = this.show_loading_screen;
			const originalToggleReport = this.toggle_report;
			this.toggle_message = function (flag, message) {
				// Suppress only the blank loading-state message. Real error / no-data
				// messages still go through because they provide a message body.
				if (flag && message === undefined) {
					return;
				}
				return originalToggleMessage.call(this, flag, message);
			};
			this.show_loading_screen = function () {};
			this.toggle_report = function (flag) {
				if (flag) {
					return originalToggleReport.call(this, flag);
				}
			};

			const result = _origRefreshReport.call(this, route_options);
			Promise.resolve(result).finally(() => {
				this.toggle_message = originalToggleMessage;
				this.show_loading_screen = originalShowLoadingScreen;
				this.toggle_report = originalToggleReport;
				frappe._tms_keep_report_visible_doctype = null;
			});
			return result;
		};
		frappe.views.QueryReport.prototype._tms_keep_visible_patched = true;
	}

	// Watch body class: if anything removes full-width, add it straight back
	new MutationObserver(function (mutations) {
		for (var m of mutations) {
			if (m.attributeName === "class" && !document.body.classList.contains("full-width")) {
				document.body.classList.add("full-width");
				localStorage.setItem("container_fullwidth", "true");
			}
		}
	}).observe(document.body, { attributes: true });

	// Auto-hide form sidebar on every form open — manual Toggle Sidebar still works
	if (frappe.ui && frappe.ui.form && frappe.ui.form.Sidebar) {
		var _orig = frappe.ui.form.Sidebar.prototype.refresh;
		frappe.ui.form.Sidebar.prototype.refresh = function () {
			_orig.call(this);
			// Hide after Frappe's own refresh (which shows it for saved docs)
			this.page.sidebar.hide();
		};
	}

	// ── Sidebar-nav: reset sort to each doctype's default on cached list views ──
	// For cached (already-constructed) list views, ListView.prototype.refresh is
	// called when the page is shown again.  We intercept it once, apply the sort
	// reset if the flag is set, then hand off to the original method.
	if (frappe.views && frappe.views.ListView) {
		const _origListRefresh = frappe.views.ListView.prototype.refresh;
		frappe.views.ListView.prototype.refresh = function (refresh_header) {
			if (frappe._tms_sidebar_sort_reset_doctype === this.doctype) {
				frappe._tms_sidebar_sort_reset_doctype = null; // consume once
				const s = _tmsSortFor(this.doctype);
				this.sort_by    = s.sort_by;
				this.sort_order = s.sort_order;
				// set_value() updates both internal properties AND the DOM label/icon
				if (this.sort_selector) {
					this.sort_selector.set_value(s.sort_by, s.sort_order);
				}
			}
			if (frappe._tms_sidebar_clear_filters_doctype === this.doctype) {
				frappe._tms_sidebar_clear_filters_doctype = null; // consume once
				_tmsClearListFilters(this);
			}
			return _origListRefresh.call(this, refresh_header);
		};
	}
});

// Re-apply full-width on every route change (workspace, form, list).
// Also: if arriving at a list view from a sidebar click, pre-set sort to the
// doctype's default (see TMS_SIDEBAR_SORT_OVERRIDE) so the ListView
// constructor and cached-view refresh both get it. Applies to both List and
// Report views — ReportView extends ListView and doesn't override refresh(),
// so this prototype patch runs for both.
frappe.router.on("change", function () {
	document.body.classList.add("full-width");

	if (frappe._tms_sidebar_click_ts && (Date.now() - frappe._tms_sidebar_click_ts) < 500) {
		const route = frappe.get_route();
		if (route && route[0] === "List" && route[1]) {
			const doctype = route[1];
			// Pre-set user_settings so a newly-constructed ListView reads ID DESC.
			// Sort is stored under the view-name key ("List"), not at the top level.
			if (frappe.model && frappe.model.user_settings) {
				if (!frappe.model.user_settings[doctype]) {
					frappe.model.user_settings[doctype] = {};
				}
				if (!frappe.model.user_settings[doctype]["List"]) {
					frappe.model.user_settings[doctype]["List"] = {};
				}
				const s = _tmsSortFor(doctype);
				frappe.model.user_settings[doctype]["List"].sort_by    = s.sort_by;
				frappe.model.user_settings[doctype]["List"].sort_order = s.sort_order;
				// Clear filters for non-excluded doctypes (Trip / Amazon Trip have
				// their own *_list.js logic that manages tcntrip_date / trip_date).
				// Doctypes in TMS_SIDEBAR_DATE_DEFAULTS are ALSO excluded here: their
				// "default" on a sidebar visit is a filter (today's date range), not
				// "no filter" -- this blanket clear used to run 120ms/350ms after
				// EVERY sidebar navigation to these doctypes regardless, racing the
				// direct filter_area.add() the click handler below performs (which,
				// under rapid consecutive clicks, can still be in flight or only just
				// landed at that point) and silently wiping the date filter straight
				// back out from under it. Reproduced live with 4 rapid sidebar clicks
				// in a row (Payment -> Receipt -> Vendor Payment -> POD Import): the
				// filter was applied correctly, then wiped a few hundred ms later by
				// this exact scheduled clear.
				if (!TMS_FILTER_RESET_EXCLUDE.has(doctype) && !TMS_SIDEBAR_DATE_DEFAULTS[doctype]) {
					frappe.model.user_settings[doctype]["List"].filters = [];
					frappe._tms_sidebar_clear_filters_doctype = doctype;
					// Direct safety-net: cached page-show often skips ListView.refresh,
					// so the prototype wrap above never fires. Schedule a couple of
					// delayed clears against cur_list to catch both fast and slow mounts.
					[120, 350].forEach(function (delay) {
						setTimeout(function () {
							if (window.cur_list && cur_list.doctype === doctype) {
								_tmsClearListFilters(cur_list);
							}
						}, delay);
					});
				}
			}
			// Flag for the prototype wrap above (handles cached list views).
			frappe._tms_sidebar_sort_reset_doctype = doctype;
		}
	}

	// Runs immediately after route change; the show_sidebar_for_module patch
	// above catches the later async override that this alone can't.
	_tmsEnforceSidebar();
});

// Backup: also hide via form-refresh event (fires after all run_serially steps)
$(document).on("form-refresh", function (e, frm) {
	if (frm && frm.page && frm.page.sidebar) {
		frm.page.sidebar.addClass("hide-sidebar");
	}
});

// ── Track sidebar clicks for sort-reset detection ─────────────────────────
// Use capture phase so this fires BEFORE Frappe's body-level router click
// handler (which triggers route "change" synchronously).  Without capture,
// the timestamp would be set after the route change already fired.
document.addEventListener("click", function (e) {
	const anchor = e.target.closest(".standard-sidebar-item a");
	if (anchor) {
		frappe._tms_sidebar_click_ts = Date.now();

		try {
			const href = anchor.getAttribute("href") || "";
			if (href) {
				const subPath = frappe.router.get_sub_path_string(href);
				const targetSlug = (subPath || "").split("/")[0];
				const currentRoute = frappe.get_route() || [];
				const currentDoctype = currentRoute[1];
				// ROOT CAUSE FIX: must also confirm the router itself says we're on a
				// List/Report route right now, not just that a stale window.cur_list
				// happens to reference this doctype. cur_list is never cleared when
				// navigating to a Form (or any other) view, so re-clicking this same
				// doctype's sidebar item from its Form view used to match "sameView"
				// here, preventDefault()+stopImmediatePropagation() the click, and
				// silently do nothing — no navigation, no URL change, no filter apply
				// (the exact "sidebar click karne par path change nahi hota" case).
				const onListOrReportRoute = currentRoute[0] === "List" && currentDoctype;
				if (targetSlug && onListOrReportRoute && frappe.router.slug(currentDoctype) === targetSlug) {
					const sameView = window.cur_list && cur_list.doctype === currentDoctype;
					if (sameView) {
						const targetDoctype = currentDoctype;
						if (TMS_SIDEBAR_DATE_DEFAULTS[targetDoctype]) {
							e.preventDefault();
							e.stopImmediatePropagation();
							_tmsApplyDefaultDateRange(cur_list, targetDoctype);
							return;
						}
					}
				}

				if (targetSlug) {
					const targetDoctype = Object.keys(TMS_SIDEBAR_DATE_DEFAULTS).find(
						(doctype) => frappe.router.slug(doctype) === targetSlug
					);
					if (targetDoctype) {
						// ROOT CAUSE FIX: frappe.route_options is a single global slot that
						// Frappe's own router.js destructively consumes+nulls inside
						// before_refresh() -- see list_view.js's before_refresh(). It has no
						// concept of "which navigation" a given route_options belongs to. If
						// a second sidebar click (on a different tracked doctype) lands here
						// while the FIRST click's frappe.set_route() -> route() async chain
						// is still in flight, the two navigations race on that same global:
						// whichever view's before_refresh() happens to run first consumes+
						// nulls it, so the OTHER navigation's before_refresh() finds
						// frappe.route_options already null and applies no filter at all --
						// silently, with no console error. Reproduced live: POD Import click
						// immediately followed by Vendor Payment click left Vendor Payment
						// showing all 225 unfiltered rows with no ?payment_date= in the URL.
						//
						// An earlier version of this fix serialized navigations through a
						// queue chained on frappe.set_route()'s own promise, on the theory
						// that it only resolves once before_refresh() has already run. That
						// promise is actually just a 100ms timer + "no ajax in flight" check
						// -- neither is genuinely tied to whether THIS navigation's
						// before_refresh() has executed. It closed the gap for two rapid
						// clicks but a third rapid click (Trip -> Vendor Payment -> POD
						// Import, all fired back-to-back) still lost the race, reproduced
						// live the same way.
						//
						// Real fix: stop writing to frappe.route_options for sidebar clicks
						// entirely. Navigate, then POLL for unambiguous, non-heuristic
						// signals -- frappe.get_route() actually settled on this doctype,
						// then a live view instance with a filter_area actually exists --
						// and only then apply the filter DIRECTLY against that instance via
						// _tmsApplyDefaultDateRange(), the same direct filter_area.add()
						// path already used for the "re-click the page you're on" case
						// above, which was never affected by this race because it never
						// touches route_options at all. Queue still serializes the queued
						// steps one at a time, but each step now only unblocks the next
						// once its own filter has actually, confirmedly landed -- not once
						// a generic timer says "probably done by now".
						e.preventDefault();
						e.stopImmediatePropagation();
						frappe._tms_nav_queue = (frappe._tms_nav_queue || Promise.resolve()).then(
							async () => {
								_tmsResetRefreshThrottle(targetDoctype);
								_tmsMarkReportKeepVisible(targetDoctype);
								_tmsMarkCurrentViewKeepVisible(targetDoctype);
								await frappe.set_route(subPath);

								const onRoute = await _tmsWaitForRoute(targetDoctype, 3000);
								if (!onRoute) return; // user moved on elsewhere meanwhile; don't force a stale doctype's filter

								const view = await _tmsWaitForView(targetDoctype, 3000);
								if (!view) return;

								await _tmsApplyDefaultDateRange(view, targetDoctype);
							},
							() => {} // swallow a prior queued navigation's rejection so this one still runs
						);
					}
				}
			}
		} catch (err) {
			console.error(err);
		}
	}
}, true);
