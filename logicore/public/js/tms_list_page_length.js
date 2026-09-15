window.TMS = window.TMS || {};

// CAPA FIX: Frappe's List View defaults to 20 records per page
// (frappe/public/js/frappe/list/base_list.js setup_defaults), forcing
// users to click "500" every time they open a list. Patch the default
// to 500 for every doctype's List View across the app.
(function () {
	const DEFAULT_LIST_PAGE_LENGTH = 500;

	function patch_default_page_length() {
		const ListView = frappe.views && frappe.views.ListView;
		if (!ListView || ListView.prototype._tms_page_length_patched) {
			return Boolean(ListView);
		}

		const original_setup_defaults = ListView.prototype.setup_defaults;

		ListView.prototype.setup_defaults = function () {
			const result = original_setup_defaults.apply(this, arguments);
			this.page_length = DEFAULT_LIST_PAGE_LENGTH;
			this.selected_page_count = DEFAULT_LIST_PAGE_LENGTH;
			return result;
		};

		ListView.prototype._tms_page_length_patched = true;
		return true;
	}

	// CAPA FIX: also drop the "20" paging button itself so users can't
	// accidentally switch back down to it. Only 100 / 500 / 2500 remain.
	function patch_paging_buttons() {
		const ListView = frappe.views && frappe.views.ListView;
		if (!ListView || ListView.prototype._tms_paging_buttons_patched) {
			return Boolean(ListView);
		}

		const original_setup_paging_area = ListView.prototype.setup_paging_area;

		ListView.prototype.setup_paging_area = function () {
			const result = original_setup_paging_area.apply(this, arguments);
			this.$paging_area && this.$paging_area.find('.btn-paging[data-value="20"]').remove();
			return result;
		};

		ListView.prototype._tms_paging_buttons_patched = true;
		return true;
	}

	/* DISABLED per user request — the pinned top scrollbar (below) was not
	   rendering usably on the user's real browser (kept coming out too
	   narrow / not visible despite working correctly in testing) and they
	   asked to remove it rather than keep debugging it. Left commented out,
	   not deleted, in case this is revisited later.

	// CAPA FIX: the real horizontal scrollbar only appears at the bottom of
	// the (possibly very tall) row area, so reaching it always meant
	// scrolling down first — and any height-based fix for that is inherently
	// fragile (zoom, screen size, per-doctype toolbar height all change how
	// tall the row area actually is; see the resize listener below for what
	// that fragility looks like). Instead, add a second, always-visible
	// scrollbar pinned directly above the column headers, synced 1:1 with
	// the real one. It never depends on how tall anything is.
	function setup_top_scrollbar(list_view) {
		const $result = list_view.$result;
		if (!$result || !$result.length) return;
		const rcEl = $result.parent(".result-container")[0];
		if (!rcEl) return;

		let bar = rcEl.parentNode.querySelector(":scope > .tms-top-hscroll");
		if (!bar) {
			bar = document.createElement("div");
			bar.className = "tms-top-hscroll";
			const inner = document.createElement("div");
			inner.className = "tms-top-hscroll-inner";
			bar.appendChild(inner);
			rcEl.parentNode.insertBefore(bar, rcEl);
		}

		// Re-bind whenever the scrolled element has actually changed (e.g.
		// a fresh render replaced it) so we never sync against a detached,
		// no-longer-visible element — that's what made dragging the bar
		// silently do nothing.
		if (bar._tms_bound_target !== rcEl) {
			let syncing = false;
			bar.addEventListener("scroll", () => {
				if (syncing) return;
				syncing = true;
				rcEl.scrollLeft = bar.scrollLeft;
				syncing = false;
			});
			rcEl.addEventListener("scroll", () => {
				if (syncing) return;
				syncing = true;
				bar.scrollLeft = rcEl.scrollLeft;
				syncing = false;
			});
			bar._tms_bound_target = rcEl;
		}

		// Always visible — even a single narrow column shows the bar. Its
		// scroll range matches the real content exactly (no padding), so
		// when it does show a partial thumb, dragging it always moves real
		// columns 1:1 instead of scrolling a fake, disconnected range.
		//
		// Width is forced explicitly (not left to default block behavior) —
		// on some layouts .tms-top-hscroll was rendering shrink-to-content
		// width (a couple hundred px) instead of the full row width, which
		// is what made it look broken/unusably narrow.
		const inner = bar.querySelector(".tms-top-hscroll-inner");
		bar.style.display = "block";
		bar.style.width = rcEl.clientWidth + "px";
		inner.style.width = Math.max(rcEl.scrollWidth, rcEl.clientWidth) + "px";
	}

	function patch_top_scrollbar() {
		const ListView = frappe.views && frappe.views.ListView;
		if (!ListView || ListView.prototype._tms_top_scrollbar_patched) {
			return Boolean(ListView);
		}

		const original_render = ListView.prototype.render;
		ListView.prototype.render = function () {
			const result = original_render.apply(this, arguments);
			setup_top_scrollbar(this);
			return result;
		};

		ListView.prototype._tms_top_scrollbar_patched = true;
		return true;
	}

	// CAPA FIX: Report View (frappe-datatable) is a completely separate
	// component from List View — it doesn't inherit ListView.render, so the
	// patch above never runs for it. It already keeps its own scrollbar
	// within the viewport (frappe-datatable bounds .dt-scrollable itself),
	// but that's still only reachable at the bottom of the visible rows.
	// Same pinned-top-bar treatment, synced to .dt-scrollable instead.
	function setup_top_scrollbar_report(report_view) {
		const wrapper = report_view.$datatable_wrapper;
		if (!wrapper || !wrapper.length) return;
		const scrollable = wrapper[0].querySelector(".dt-scrollable");
		if (!scrollable) return;

		let bar = wrapper[0].parentNode.querySelector(":scope > .tms-top-hscroll");
		if (!bar) {
			bar = document.createElement("div");
			bar.className = "tms-top-hscroll";
			const inner = document.createElement("div");
			inner.className = "tms-top-hscroll-inner";
			bar.appendChild(inner);
			wrapper[0].parentNode.insertBefore(bar, wrapper[0]);
		}

		// frappe-datatable rebuilds .dt-scrollable on a full re-render, so
		// re-bind whenever the underlying element has actually changed.
		if (bar._tms_bound_target !== scrollable) {
			let syncing = false;
			bar.addEventListener("scroll", () => {
				if (syncing) return;
				syncing = true;
				scrollable.scrollLeft = bar.scrollLeft;
				syncing = false;
			});
			scrollable.addEventListener("scroll", () => {
				if (syncing) return;
				syncing = true;
				bar.scrollLeft = scrollable.scrollLeft;
				syncing = false;
			});
			bar._tms_bound_target = scrollable;
		}

		// Always visible; range matches real content exactly (see the List
		// View bar above for why the fake-padding version was wrong). Width
		// forced explicitly, same reasoning as the List View bar above.
		const inner = bar.querySelector(".tms-top-hscroll-inner");
		bar.style.display = "block";
		bar.style.width = scrollable.clientWidth + "px";
		inner.style.width = Math.max(scrollable.scrollWidth, scrollable.clientWidth) + "px";
	}

	function patch_report_view_top_scrollbar() {
		const ReportView = frappe.views && frappe.views.ReportView;
		if (!ReportView || ReportView.prototype._tms_top_scrollbar_patched) {
			return Boolean(ReportView);
		}

		const original_render = ReportView.prototype.render;
		ReportView.prototype.render = function () {
			const result = original_render.apply(this, arguments);
			// frappe-datatable finishes its own layout async; defer a tick.
			window.setTimeout(() => setup_top_scrollbar_report(this), 50);
			return result;
		};

		ReportView.prototype._tms_top_scrollbar_patched = true;
		return true;
	}

	TMS.patch_list_view_for_tms_top_scrollbar = patch_top_scrollbar;
	TMS.patch_report_view_for_tms_top_scrollbar = patch_report_view_top_scrollbar;
	*/

	TMS.patch_list_view_for_tms_page_length = patch_default_page_length;
	TMS.patch_list_view_for_tms_paging_buttons = patch_paging_buttons;

	function patch_all() {
		const default_patched = patch_default_page_length();
		const buttons_patched = patch_paging_buttons();
		return default_patched && buttons_patched;
	}

	if (!patch_all()) {
		const patch_timer = window.setInterval(() => {
			if (patch_all()) {
				window.clearInterval(patch_timer);
			}
		}, 200);
	}

	/* REVERTED per user request — no UI/layout behavior beyond the default
	   page length + removed "20" button above. This just re-ran Frappe's own
	   existing height calc on resize; harmless on its own but not part of
	   what was asked for now.
	let resize_timer = null;
	window.addEventListener("resize", () => {
		window.clearTimeout(resize_timer);
		resize_timer = window.setTimeout(() => {
			if (window.cur_list && typeof cur_list.set_result_height === "function") {
				cur_list.set_result_height();
			}
		}, 100);
	});
	*/
})();
