window.TMS = window.TMS || {};

// Shared "quick date-range" bar for list views — same UI/behavior as Trip's own
// bar (trip_list.js), generalized so every date-driven doctype can opt in with
// two calls instead of copy-pasting the ~150-line implementation per doctype.
//
// Usage, inside `frappe.listview_settings[doctype]`:
//   onload(listview)  { TMS.dateFilterBar.attach(listview, { doctype: "X", fieldname: "y", label: "Y Date" }); }
//   refresh(listview) { TMS.dateFilterBar.refresh(listview, { doctype: "X", fieldname: "y" }); }
//
// Behavior: the bar always defaults to TODAY (both from/to) on a plain sidebar
// visit — never a stale range left over from a previous manual Apply, and
// never whatever Frappe auto-restored from __UserSettings. A dashboard/report
// link that sets `frappe.route_options[fieldname]` (or a reloaded URL that
// already carries filters) is respected instead of being overwritten.
//
// Design note — why refresh() re-checks everything fresh instead of relying on
// a captured "did a sidebar navigation just happen" flag: an earlier version
// used frappe.router.on("change") to stamp a timestamp, and refresh() only
// forced "today" if that stamp was fresh (<2s old). In practice that event did
// not reliably fire on every sidebar revisit of an already-cached page (stale,
// unconsumed stamps were observed 30-40s old), so genuine navigations were
// silently skipped — the bar showed "today" while the grid quietly kept
// whatever was last fetched (often unfiltered). Frappe's own base_list.js
// *always* calls this module's refresh(listview) hook at the end of every
// single data render — first load and every subsequent revisit alike — so
// that call is the one thing that's actually reliable. refresh() now uses that
// guarantee directly: unless this exact refresh() was triggered by our OWN
// manual Apply/Clear click (tracked via a plain synchronous flag, not an
// event) or genuine dashboard route_options/URL filters are present right now,
// it unconditionally forces the filter back to today. No timing window, no
// event-listener reliability to depend on.
//
// Why the loading overlay exists: Frappe's ListView.show() always runs its OWN
// first data fetch (unfiltered) as part of page setup, strictly BEFORE this
// module's filter gets a chance to apply — `onload()` is called as a bare
// synchronous function (its return value/promise is never awaited by the
// framework), so nothing done inside onload() can delay that first fetch. The
// overlay masks the grid the instant we know a navigation is happening and is
// only removed once our own filtered fetch has actually completed.
(function () {
	function slugify(doctype) {
		return doctype.toLowerCase().replace(/[^a-z0-9]+/g, "-");
	}

	function injectStyle() {
		if (document.getElementById("tms-date-filter-bar-style")) return;
		const style = document.createElement("style");
		style.id = "tms-date-filter-bar-style";
		style.textContent = `
.tms-date-filter-bar { display:flex; align-items:center; gap:8px; flex-wrap:wrap; padding:7px 14px 6px; background:var(--subtle-accent,#EEF2FF); border-bottom:1.5px solid var(--border-color,#C7D7FF); font-size:12px; }
.tms-df-label { font-weight:700; color:var(--text-color,#3730A3); white-space:nowrap; font-size:11px; }
.tms-df-inp { height:28px; padding:0 8px; border:1.5px solid var(--border-color,#A5B4FC); border-radius:6px; background:var(--control-bg,#fff); color:var(--text-color,#1E1B4B); font-size:11px; outline:none; cursor:pointer; }
.tms-df-inp:focus { border-color:var(--primary,#3B4FE4); box-shadow:0 0 0 2px rgba(59,79,228,0.14); }
.tms-df-apply { height:28px; padding:0 16px; background:#3B4FE4; color:#fff; border:none; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer; transition:background 0.14s; }
.tms-df-apply:hover { background:#2D3DB8; }
.tms-df-clear { height:28px; padding:0 12px; background:var(--btn-default-bg,#F1F5F9); color:var(--text-muted,#475569); border:1.5px solid var(--border-color,#CBD5E1); border-radius:6px; font-size:11px; font-weight:600; cursor:pointer; transition:background 0.14s; }
.tms-df-clear:hover { background:var(--control-bg,#E2E8F0); }
.tms-df-badge { display:none; font-size:10px; font-weight:700; background:#DCFCE7; color:#15803D; border:1.5px solid #86EFAC; border-radius:12px; padding:2px 10px; white-space:nowrap; }
[data-theme="dark"] .tms-df-badge { background:#14532d; color:#86efac; border-color:#166534; }
.tms-df-sep { color:var(--text-muted,#94A3B8); font-size:11px; }
/* Loading-overlay spinner rules — no longer used (showLoadingOverlay/
hideLoadingOverlay are now no-ops, see the JS below for why), kept here
rather than deleted in case the masking approach is ever needed again.
.tms-df-loading-overlay { position:absolute; inset:0; z-index:60; background:var(--fg-color,#fff); display:flex; align-items:center; justify-content:center; }
[data-theme="dark"] .tms-df-loading-overlay { background:#1F2937; }
.tms-df-loading-overlay .tms-df-spinner { width:22px; height:22px; border-radius:50%; border:2.5px solid var(--border-color,#C7D7FF); border-top-color:#3B4FE4; animation: tms-df-spin 0.7s linear infinite; }
@keyframes tms-df-spin { to { transform: rotate(360deg); } }
*/
		`;
		document.head.appendChild(style);
	}

	// Registered per-doctype so the router "change" handler (best-effort early
	// masking only — see design note above; refresh() itself never depends on
	// it for correctness) can mask the grid before Frappe's own fetch/render
	// for a cached-page revisit, without needing a fresh onload() call to hand
	// it a $page.
	frappe._tms_df_page = frappe._tms_df_page || {};

	// True while a manual Apply/Clear click's own filter_area.add()/refresh()
	// cycle is in flight for that doctype — refresh() checks this so it never
	// fights the user's own just-clicked custom range.
	frappe._tms_df_manual = frappe._tms_df_manual || {};

	// Intentionally no-ops: an earlier version of this masked the grid with a
	// custom spinner overlay while the corrective refresh (below) ran, to
	// guarantee unfiltered data was never visible even briefly. The actual
	// root causes (filter_area.add()'s async ordering, ListView.refresh()'s
	// 1s throttle silently dropping the correction, route_options vs. stale
	// URL confusion) are now fixed directly, so the custom loader is no
	// longer needed for correctness — and it looked visually different from
	// Frappe's own default list/report loading state, which is what these
	// exist as no-ops (not deleted, all call sites elsewhere still call them)
	// to restore. Every doctype's page now loads exactly as vanilla Frappe
	// would.
	function showLoadingOverlay() {}

	function hideLoadingOverlay() {}

	// Injected unconditionally at load time (not lazily inside attach()) so the
	// overlay CSS is available even to doctypes with their own bespoke bar
	// implementation (Trip, Amazon Trip) that reuse showOverlay/hideOverlay/
	// registerPage below but never call attach() itself.
	injectStyle();

	// Same limitation as Trip's original: FilterList.get_filter() only returns
	// the first matching row, so a single filter_area.remove(fieldname) call
	// always leaves one row behind when the range is stored as two rows
	// (>= and <=) sharing the same fieldname. Loop until none remain.
	function clearDateFilters(view, fieldname) {
		if (!view || !view.filter_area) return;
		const fl = view.filter_area.filter_list;
		while (fl && fl.get_filter && fl.get_filter(fieldname)) {
			view.filter_area.remove(fieldname);
		}
	}

	function extractFromTo(op, val) {
		op = (op || "").toLowerCase();
		if (op === "between" && Array.isArray(val)) return val;
		if (op === ">=" || op === ">") return [val, ""];
		if (op === "<=" || op === "<") return ["", val];
		if (op === "=") return [val, val];
		return ["", ""];
	}

	const fmt_dd = (d) => d.split("-").reverse().join("-");

	TMS.dateFilterBar = {
		attach(listview, opts) {
			const doctype = opts.doctype;
			const fieldname = opts.fieldname;
			const label = opts.label || fieldname;
			const slug = slugify(doctype);
			const idFrom = `tms-df-from-${slug}`;
			const idTo = `tms-df-to-${slug}`;
			const idApply = `tms-df-apply-${slug}`;
			const idClear = `tms-df-clear-${slug}`;
			const idBadge = `tms-df-badge-${slug}`;

			const today = frappe.datetime.get_today();

			// Register the page + mask the grid IMMEDIATELY (before the bar is even
			// built) — this runs synchronously inside onload(), which itself runs
			// strictly before Frappe's own first (unfiltered) data fetch for this
			// page, so the overlay is guaranteed to be in place before anything
			// wrong ever paints.
			frappe._tms_df_page[doctype] = listview.$page;
			showLoadingOverlay(doctype);

			injectStyle();

			const $bar = $(`
				<div class="tms-date-filter-bar">
					<span class="tms-df-label">🗓 ${frappe.utils.escape_html(label)}:</span>
					<input type="date" class="tms-df-inp" id="${idFrom}" value="${today}" title="From Date">
					<span class="tms-df-sep">→</span>
					<input type="date" class="tms-df-inp" id="${idTo}" value="${today}" title="To Date">
					<button class="tms-df-apply" id="${idApply}">Apply</button>
					<button class="tms-df-clear" id="${idClear}">Clear</button>
					<span class="tms-df-badge" id="${idBadge}"></span>
				</div>
			`);
			listview.$page.find(".layout-main-section").prepend($bar);

			function getView() {
				return cur_list || listview;
			}

			function applyBadge(from, to) {
				$(`#${idBadge}`).text(`${fmt_dd(from)}  →  ${fmt_dd(to)}`).show();
			}

			function applyFilter() {
				const from = $(`#${idFrom}`).val();
				const to = $(`#${idTo}`).val();
				if (!from || !to) {
					frappe.show_alert({ message: "⚠️ Select both From and To dates.", indicator: "orange" }, 3);
					hideLoadingOverlay(doctype);
					return;
				}
				if (from > to) {
					frappe.show_alert({ message: "⚠️ From date cannot be after To date.", indicator: "orange" }, 3);
					hideLoadingOverlay(doctype);
					return;
				}

				const view = getView();
				if (!view) { hideLoadingOverlay(doctype); return; }

				frappe._tms_df_manual[doctype] = true;

				// Matches Trip's own (more reliable) bar: set the filter directly on
				// filter_list first, synchronously, before the async .add() below.
				// .add() alone has been observed to leave some doctypes' ListView in
				// a state where filter_area reports the new range correctly but the
				// visible grid doesn't — this direct set gives the DataTable/report
				// machinery the value up front instead of relying solely on add()'s
				// own (async, throttle-prone) path to propagate it.
				if (view.filter_area && view.filter_area.filter_list) {
					const existing = (view.get_filters ? view.get_filters() : [])
						.filter((f) => f[1] !== fieldname);
					view.filter_area.filter_list.set_filter_value &&
						view.filter_area.filter_list.set_filter_value([
							...existing,
							[doctype, fieldname, ">=", from],
							[doctype, fieldname, "<=", to],
						]);
				}

				clearDateFilters(view, fieldname);
				// filter_area.add() is asynchronous (it resolves standard-filter fields
				// then adds the filter rows before resolving) — passing `true` here lets
				// it trigger list_view.refresh() itself once the filter is actually
				// registered, instead of us calling refresh() synchronously right after
				// .add() returns, which re-fetches with the OLD filter state and leaves
				// the badge showing a date range the grid was never actually filtered by.
				if (view.filter_area) {
					Promise.resolve(view.filter_area.add([
						[doctype, fieldname, ">=", from],
						[doctype, fieldname, "<=", to],
					], true)).then(() => {
						applyBadge(from, to);
						frappe._tms_df_manual[doctype] = false;
						// Do NOT hide the overlay yet — see the matching comment in
						// refresh() below. ListView.prototype.refresh() is throttled to
						// one real call per second, so on a fresh page load (where
						// Frappe's own natural unfiltered fetch may have just consumed
						// that window) this filtered refresh can update listview.data
						// without the DataTable actually repainting yet. Keep the
						// overlay up until the safety-net refresh below both confirms
						// AND paints the correct state.
						setTimeout(() => {
							const p = view.refresh && view.refresh();
							Promise.resolve(p).then(() => hideLoadingOverlay(doctype));
						}, 1100);
					});
				} else {
					view.refresh ? view.refresh() : (view.run && view.run());
					applyBadge(from, to);
					hideLoadingOverlay(doctype);
					frappe._tms_df_manual[doctype] = false;
				}
			}

			function clearFilter() {
				$(`#${idFrom}`).val(today);
				$(`#${idTo}`).val(today);
				const view = getView();
				if (view) {
					frappe._tms_df_manual[doctype] = true;
					clearDateFilters(view, fieldname);
					view.refresh ? view.refresh() : (view.run && view.run());
					setTimeout(() => { frappe._tms_df_manual[doctype] = false; }, 0);
				}
				$(`#${idBadge}`).hide();
			}

			$(`#${idApply}`).on("click", applyFilter);
			$(`#${idClear}`).on("click", clearFilter);
			$bar.find(".tms-df-inp").on("keydown", (e) => { if (e.key === "Enter") applyFilter(); });

			// Strip every other filter from this doctype's list __UserSettings save
			// so a manually-applied non-date filter never persists and silently
			// reappears on a later plain sidebar visit.
			frappe._tms_df_guards = frappe._tms_df_guards || {};
			if (!frappe._tms_df_guards[doctype]) {
				frappe._tms_df_guards[doctype] = true;
				const _origSave = frappe.model.user_settings.save.bind(frappe.model.user_settings);
				frappe.model.user_settings.save = function (dt, key, value, user) {
					if (dt === doctype && key === "List" && value && Array.isArray(value.filters)) {
						value = Object.assign({}, value, {
							filters: value.filters.filter((f) => Array.isArray(f) && f[1] === fieldname),
						});
					}
					return _origSave(dt, key, value, user);
				};
			}

			// Best-effort ONLY: masks the grid as early as possible on a cached-page
			// revisit, before Frappe's own refresh() for it even starts. refresh()
			// below does NOT depend on this having fired — see the module header.
			frappe._tms_df_nav_guards = frappe._tms_df_nav_guards || {};
			if (!frappe._tms_df_nav_guards[doctype]) {
				frappe._tms_df_nav_guards[doctype] = true;
				frappe.router.on("change", function () {
					const r = frappe.get_route();
					if (r && r[0] === "List" && r[1] === doctype && !frappe._tms_df_manual[doctype]) {
						// Mask unconditionally — hide_sidebar.js's own click handler
						// now pre-sets frappe.route_options to today's range before
						// EVERY sidebar click on a tracked doctype, so route_options
						// being present no longer means "skip masking, Frappe will
						// render it correctly on its own"; the same DOM-repaint race
						// this overlay guards against can still happen either way.
						showLoadingOverlay(doctype);
					}
				});
			}

			function syncBar(routeDateFilter) {
				// Same DOM-repaint race as applyFilter()/refresh() below: Frappe's
				// own route_options-driven fetch can update listview.data correctly
				// without the DataTable actually repainting the visible rows. Force
				// one more real refresh past the throttle window and only reveal
				// the grid once THAT has actually resolved.
				function confirmAndReveal() {
					const view = getView();
					setTimeout(() => {
						const p = view && view.refresh && view.refresh();
						Promise.resolve(p).then(() => hideLoadingOverlay(doctype));
					}, 1100);
				}
				if (Array.isArray(routeDateFilter)) {
					const [from, to] = extractFromTo(routeDateFilter[0], routeDateFilter[1]);
					if (from || to) {
						if (from) $(`#${idFrom}`).val(from);
						if (to) $(`#${idTo}`).val(to);
						applyBadge(from || to, to || from);
						confirmAndReveal();
						return;
					}
				}
				const fa = getView().filter_area;
				const dateFilters = fa && fa.get ? fa.get().filter((f) => f[1] === fieldname) : [];
				let from = "", to = "";
				dateFilters.forEach((f) => {
					const [f2, t2] = extractFromTo(f[2], f[3]);
					from = f2 || from;
					to = t2 || to;
				});
				if (from || to) applyBadge(from || to, to || from);
				confirmAndReveal();
			}

			// onload only fires on first page creation. ROOT CAUSE FIX: this used
			// to unconditionally re-apply "today" here via applyFilter() (its own
			// clear+add+refresh cycle), racing Frappe's OWN native mechanism for
			// exactly this — frappe.route_options consumed inside
			// ListView.prototype.before_refresh() (parse_filters_from_route_options
			// -> filter_area.set()), which the framework guarantees runs before
			// the very FIRST fetch, for both ListView and ReportView.
			//
			// The two paths race because they DON'T fire at the same point for
			// both view types: ListView calls onload() from setup_view() (before
			// its first fetch); ReportView overrides setup_view() and instead
			// calls onload() later, from setup_result_area() (see report_view.js).
			// So on a Report View doctype (e.g. Trip POD Import's default view),
			// the native route_options-driven fetch could already be filtered and
			// rendered by the time this 300ms timer fires — and this block's own
			// redundant clear+add+refresh would then either get silently
			// throttled by BaseList's 3s no_change() de-dupe, or genuinely re-run
			// and repaint out of order, sometimes leaving stale unfiltered rows
			// on screen while the bar's own UI (badge/inputs) already showed
			// "today" (client-side DOM state, unrelated to what actually got
			// fetched/rendered).
			//
			// Fix: check first whether `fieldname` is ALREADY filtered (native
			// route_options already did the job, or a manual apply already ran).
			// Only fall back to forcing "today" for a genuinely bare visit with
			// no filter at all — never re-issue a redundant second query on top
			// of an already-correct render.
			setTimeout(() => {
				const view = getView();
				const fl = view && view.filter_area && view.filter_area.filter_list;
				if (fl && fl.filters) {
					fl.filters
						.filter((f) => f.fieldname !== fieldname)
						.forEach((f) => { try { f.$filter && f.$filter.remove(); } catch (e) {} });
					fl.filters = fl.filters.filter((f) => f.fieldname === fieldname);
				}

				const existingDateFilters = (view && view.get_filters ? view.get_filters() : [])
					.filter((f) => f[1] === fieldname);
				if (existingDateFilters.length) {
					let from = "", to = "";
					existingDateFilters.forEach((f) => {
						const [f2, t2] = extractFromTo(f[2], f[3]);
						from = f2 || from;
						to = t2 || to;
					});
					if (from) $(`#${idFrom}`).val(from);
					if (to) $(`#${idTo}`).val(to);
					if (from || to) applyBadge(from || to, to || from);
					hideLoadingOverlay(doctype);
					return;
				}

				applyFilter();
			}, 300);
		},

		// refresh() fires on EVERY navigation to this list (cached or new) — this
		// is guaranteed by Frappe's own base_list.js (it calls this hook at the
		// end of every single data render), so unlike onload() it is safe to rely
		// on for repeat/cached-page visits. Unless this call was triggered by our
		// own manual Apply/Clear (frappe._tms_df_manual) or genuine dashboard
		// filters are present right now, force the range back to today.
		refresh(listview, opts) {
			const doctype = opts.doctype;
			const fieldname = opts.fieldname;
			const slug = slugify(doctype);
			const idFrom = `tms-df-from-${slug}`;
			const idTo = `tms-df-to-${slug}`;
			const idBadge = `tms-df-badge-${slug}`;

			frappe._tms_df_page[doctype] = listview.$page;

			if (frappe._tms_df_manual[doctype]) {
				// Our own click's filter_area.add() is what triggered this refresh —
				// don't fight the range the user just applied.
				hideLoadingOverlay(doctype);
				return;
			}

			// Only force "today" when this refresh was triggered by a genuine
			// sidebar navigation. hide_sidebar.js stamps frappe._tms_sidebar_click_ts
			// (capture-phase, on every sidebar-link click, before the route even
			// changes) — the one reliable "a real navigation just happened" signal.
			// Any OTHER refresh — the user clearing the filter and applying a
			// different one via Frappe's own filter UI, an unrelated re-render,
			// a background poll — must NOT be fought back to today, or a manual
			// Clear followed by a custom filter would keep silently reverting.
			const navTs = frappe._tms_sidebar_click_ts || 0;
			const isGenuineNav = Date.now() - navTs < 800;
			if (!isGenuineNav) {
				// Not a forced-today moment, but the bar's own inputs/badge must
				// still reflect whatever filter is ACTUALLY applied right now —
				// e.g. the user cleared/changed the date filter from Frappe's own
				// native Filters panel instead of this bar's Clear/Apply buttons.
				// Both surfaces read/write the same filter_area, so just mirror
				// its current state onto the bar instead of leaving it stale.
				const view = cur_list || listview;
				const fa2 = view && view.filter_area;
				const dateFilters = fa2 && fa2.get ? fa2.get().filter((f) => f[1] === fieldname) : [];
				let from = "", to = "";
				dateFilters.forEach((f) => {
					const [f2, t2] = extractFromTo(f[2], f[3]);
					from = f2 || from;
					to = t2 || to;
				});
				if (from || to) {
					if (from) $(`#${idFrom}`).val(from);
					if (to) $(`#${idTo}`).val(to);
					$(`#${idBadge}`).text(`${fmt_dd(from || to)}  →  ${fmt_dd(to || from)}`).show();
				} else {
					$(`#${idBadge}`).hide();
				}
				hideLoadingOverlay(doctype);
				return;
			}
			// Consume it — a second refresh() call inside the same navigation
			// window (e.g. our own corrective setTimeout below) must not force
			// today a second time and stomp on a Clear/custom-filter that
			// happened to land in that same 800ms window.
			frappe._tms_sidebar_click_ts = 0;

			const today = frappe.datetime.get_today();

			// ROOT CAUSE FIX (same race as attach()'s onload, see the comment
			// there): if `fieldname` is already filtered to exactly today's range,
			// Frappe's native frappe.route_options -> before_refresh() pipeline
			// already applied it before this fetch ran — don't re-issue a
			// redundant clear+add+refresh cycle on top of an already-correct
			// render, that's what raced and left stale rows on screen before.
			const alreadyTodayFilters = (listview.get_filters ? listview.get_filters() : [])
				.filter((f) => f[1] === fieldname);
			let alreadyFrom = "", alreadyTo = "";
			alreadyTodayFilters.forEach((f) => {
				const [f2, t2] = extractFromTo(f[2], f[3]);
				alreadyFrom = f2 || alreadyFrom;
				alreadyTo = t2 || alreadyTo;
			});
			if (alreadyFrom === today && alreadyTo === today) {
				$(`#${idFrom}`).val(today);
				$(`#${idTo}`).val(today);
				// NOTE: applyBadge() is scoped inside attach()'s closure, not
				// available here in refresh() — match the existing direct-jQuery
				// pattern this function already uses below for the badge.
				$(`#${idBadge}`).text(`${fmt_dd(today)}  →  ${fmt_dd(today)}`).show();
				hideLoadingOverlay(doctype);
				return;
			}

			$(`#${idFrom}`).val(today);
			$(`#${idTo}`).val(today);

			const fa = listview.filter_area;
			const fl = fa && fa.filter_list;
			if (fa && fl) {
				const nonDateFields = (fa.get ? fa.get() : [])
					.filter((f) => f[1] !== fieldname)
					.map((f) => f[1]);
				if (nonDateFields.length) {
					const origOnChange = fl.on_change;
					fl.on_change = function () {};
					nonDateFields.forEach((fn) => { try { fa.remove(fn); } catch (e) {} });
					fl.on_change = origOnChange;
				}
			}

			setTimeout(() => {
				const from = $(`#${idFrom}`).val();
				const to = $(`#${idTo}`).val();
				if (!from || !to) { hideLoadingOverlay(doctype); return; }

				// See the matching comment in attach()'s applyFilter() — set the
				// filter directly on filter_list first, synchronously, matching
				// Trip's own (more reliable) bar, before the async .add() below.
				if (listview.filter_area && listview.filter_area.filter_list) {
					const existing = (listview.get_filters ? listview.get_filters() : [])
						.filter((f) => f[1] !== fieldname);
					listview.filter_area.filter_list.set_filter_value &&
						listview.filter_area.filter_list.set_filter_value([
							...existing,
							[doctype, fieldname, ">=", from],
							[doctype, fieldname, "<=", to],
						]);
				}

				clearDateFilters(listview, fieldname);
				// See the matching comment in attach()'s applyFilter() — `true` lets
				// filter_area.add() trigger the refresh itself once the filter is
				// actually registered, instead of racing ahead of its own promise chain.
				if (listview.filter_area) {
					Promise.resolve(listview.filter_area.add([
						[doctype, fieldname, ">=", from],
						[doctype, fieldname, "<=", to],
					], true)).then(() => {
						$(`#${idBadge}`).text(`${fmt_dd(from)}  →  ${fmt_dd(to)}`).show();
						// Do NOT hide the overlay yet. On a cached-page revisit, Frappe's
						// own natural refresh() (unfiltered, using whatever filter
						// existed before this hook ran) has ALREADY completed its
						// fetch+render by the time this hook is even called — see the
						// module header. The filter_area.add() above then triggers a
						// second refresh() for the corrected range, and that one has
						// been observed (verified live via devtools) to occasionally
						// update listview.data correctly WITHOUT the DataTable actually
						// repainting the visible rows — i.e. the grid can still show the
						// wrong data even after this .then() resolves. Keep the overlay
						// up and let the safety-net refresh below both confirm AND paint
						// the correct state before ever revealing the grid again.
						// ListView.prototype.refresh() is throttled to one real call per
						// second, so calling it again immediately would be silently
						// dropped; scheduling it past that window guarantees a real
						// fetch+render cycle runs against the now-correct filter.
						setTimeout(() => {
							const p = listview.refresh && listview.refresh();
							Promise.resolve(p).then(() => hideLoadingOverlay(doctype));
						}, 1100);
					});
				} else {
					listview.refresh();
					$(`#${idBadge}`).text(`${fmt_dd(from)}  →  ${fmt_dd(to)}`).show();
					hideLoadingOverlay(doctype);
				}
			}, 0);
		},

		// Small reusable primitives for doctypes with their own bespoke bar
		// implementation (Trip, Amazon Trip) that don't call attach()/refresh()
		// above but want the same "never show unfiltered data, even briefly"
		// masking. registerPage MUST be called (with the current listview's
		// $page) from both onload() and refresh(), same as attach()/refresh() do
		// internally, so the router "change" handler below has a $page to act on
		// for cached-page revisits.
		registerPage(doctype, $page) {
			frappe._tms_df_page[doctype] = $page;
		},
		showOverlay: showLoadingOverlay,
		hideOverlay: hideLoadingOverlay,
		// Exposed for hide_sidebar.js's capture-phase sidebar-click handler,
		// which applies the default date range directly against the current
		// (already-active) listview when re-clicking the sidebar item you're
		// already on — that path never goes through attach()/refresh() above.
		clearDateFilters: clearDateFilters,
	};
})();
