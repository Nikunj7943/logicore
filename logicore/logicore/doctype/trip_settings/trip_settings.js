// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

const TS_VERSION        = "1.0.0";
const CHILD_TABLE_FIELD = "trip_field_settings";

// ── Tab display metadata: icons/colors keyed by tab fieldname ────
// These are UI-only concerns — schema comes from the server dynamically.

const TAB_META = {
	tab_trip_info:         { icon: "🗂️",  color: "#3B4FE4" },
	tab_loading_unloading: { icon: "📦",  color: "#EA580C" },
	tab_km_vendor:         { icon: "🛣️",  color: "#047857" },
	tab_pod_approval:      { icon: "📸",  color: "#7C3AED" },
	tab_billing_payment:   { icon: "💳",  color: "#B45309" },
};

let TRIP_TABS = []; // populated at runtime by load_trip_tabs()

// This doctype's "Trip Type" selector is hand-built HTML (ts-type-select), not a
// standard Frappe field control -- Frappe's native permlevel enforcement only hides
// frm.fields_dict["trip_type"]'s own control, which this code deliberately hides and
// replaces (see refresh()). Without this check, a TMS User Group Hidden/Read Only
// permission on this field would be silently bypassed by this custom UI.
function _tms_trip_type_perm(frm) {
	const df = frm.fields_dict["trip_type"] && frm.fields_dict["trip_type"].df;
	const permlevel = (df && df.permlevel) || 0;
	if (!permlevel) return { read: true, write: true };
	const p = (frm.perm && frm.perm[permlevel]) || {};
	return { read: !!p.read, write: !!p.write };
}

function load_trip_tabs() {
	return new Promise((resolve, reject) => {
		frappe.call({
			method: "logicore.logicore.doctype.trip_settings.trip_settings.get_trip_fields",
			callback(r) {
				if (!r.message) { reject("get_trip_fields returned no data"); return; }
				TRIP_TABS = r.message.map(tab => ({
					key:    tab.tab_key,
					label:  tab.tab_label,
					fields: tab.fields,
					...(TAB_META[tab.tab_key] || { icon: "📋", color: "#64748B" }),
				}));
				resolve(TRIP_TABS);
			},
			error: reject,
		});
	});
}

// ══════════════════════════════════════════════════════════════════
//  STYLES
// ══════════════════════════════════════════════════════════════════

function inject_ts_styles() {
	if (document.getElementById("ts-styles")) return;
	const s = document.createElement("style");
	s.id = "ts-styles";
	s.textContent = `
/* ══ Trip Settings UI — Professional Compact Theme ══════════ */
#ts-root, #ts-root * { box-sizing: border-box; }
#ts-root {
	font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif;
	padding: 0 0 40px;
	color: #0F172A;
}

/* ─ Trip Type Header ─────────────────────────────────────── */
.ts-type-header {
	background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 55%, #3730a3 100%);
	border-radius: 10px; padding: 14px 20px; margin-bottom: 10px;
	display: flex; align-items: center; gap: 14px;
	box-shadow: 0 2px 14px rgba(30,27,75,.30);
	border: 1px solid rgba(255,255,255,.07);
}
.ts-type-header-icon { font-size: 26px; line-height: 1; flex-shrink: 0; }
.ts-type-header-body {
	flex: 1; min-width: 0; display: flex; align-items: center;
	gap: 20px; flex-wrap: wrap;
}
.ts-type-header-meta { min-width: 0; }
.ts-type-header-eyebrow {
	font-size: 9px; font-weight: 700; color: rgba(255,255,255,.45);
	letter-spacing: .15em; text-transform: uppercase;
}
.ts-type-header-value {
	font-size: 16px; font-weight: 800; color: #fff;
	white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
	letter-spacing: -.01em; margin-top: 1px;
}
.ts-type-header-hint { font-size: 11px; color: rgba(255,255,255,.38); margin-top: 1px; }
#ts-type-display-wrap { white-space: normal; overflow: visible; display: flex; align-items: center; gap: 8px; }
.ts-type-edit-btn {
	background: rgba(255,255,255,.11); border: 1px solid rgba(255,255,255,.24);
	color: #fff; font-size: 12px; line-height: 1; padding: 4px 7px;
	border-radius: 6px; cursor: pointer; flex-shrink: 0;
}
.ts-type-edit-btn:hover { background: rgba(255,255,255,.2); }
.ts-type-select-wrap { flex: 1; min-width: 180px; max-width: 320px; }
.ts-type-select {
	width: 100%; background: rgba(255,255,255,.11);
	border: 1.5px solid rgba(255,255,255,.24); color: #fff;
	font-size: 13px; font-weight: 600;
	padding: 7px 34px 7px 11px; border-radius: 7px; cursor: pointer;
	outline: none; -webkit-appearance: none; appearance: none;
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='rgba(255,255,255,.5)'/%3E%3C/svg%3E");
	background-repeat: no-repeat; background-position: right 10px center;
	transition: border-color .18s, background .18s;
}
.ts-type-select:focus { border-color: rgba(255,255,255,.6); background: rgba(255,255,255,.17); }
.ts-type-select option { background: #1E1B4B; color: #fff; }
.ts-type-badge-large {
	display: inline-flex; align-items: center; gap: 7px;
	background: rgba(255,255,255,.13); border: 1.5px solid rgba(255,255,255,.26);
	border-radius: 8px; padding: 5px 14px;
	font-size: 14px; font-weight: 800; color: #fff;
}

/* ─ Tab switcher nav ─────────────────────────────────────── */
.ts-tabs-bar {
	display: flex; gap: 3px; margin-bottom: 10px;
	background: #EEF2FF; border-radius: 8px; padding: 3px;
	width: fit-content; border: 1px solid #C7D7FF;
}
.ts-tab-nav {
	padding: 5px 16px; border-radius: 6px; border: none; cursor: pointer;
	font-size: 11.5px; font-weight: 700; color: #6B7280;
	background: transparent; transition: all .16s; letter-spacing: .01em;
}
.ts-tab-nav.active {
	background: #fff; color: #1E1B4B;
	box-shadow: 0 1px 4px rgba(0,0,0,.09);
}
.ts-tab-nav:hover:not(.active) { background: rgba(255,255,255,.7); color: #374151; }

/* ─ Toolbar ─────────────────────────────────────────────── */
.ts-toolbar {
	display: flex; align-items: center; justify-content: space-between;
	flex-wrap: wrap; gap: 8px; padding: 11px 16px;
	background: linear-gradient(135deg, #1E1B4B 0%, #3B4FE4 100%);
	border-radius: 9px; margin-bottom: 12px;
	box-shadow: 0 2px 12px rgba(59,79,228,.22);
}
.ts-tb-left  { display: flex; align-items: center; gap: 9px; }
.ts-tb-icon  { font-size: 18px; line-height: 1; }
.ts-tb-title { font-size: 13px; font-weight: 800; color: #fff; line-height: 1.3; }
.ts-tb-sub   { font-size: 10px; color: rgba(255,255,255,.52); margin-top: 1px; }
.ts-tb-right { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

/* ─ Buttons ──────────────────────────────────────────────── */
.ts-btn {
	display: inline-flex; align-items: center; gap: 5px;
	padding: 6px 13px; border-radius: 6px;
	font-size: 11.5px; font-weight: 700; letter-spacing: .02em;
	cursor: pointer; border: none; outline: none;
	transition: all .15s; line-height: 1;
}
.ts-btn-primary {
	background: #fff; color: #3B4FE4;
	box-shadow: 0 1px 6px rgba(0,0,0,.10);
}
.ts-btn-primary:hover {
	background: #EEF2FF; transform: translateY(-1px);
	box-shadow: 0 3px 10px rgba(59,79,228,.20);
}
.ts-btn-ghost   { background: rgba(255,255,255,.13); color: #fff; border: 1.5px solid rgba(255,255,255,.26); }
.ts-btn-ghost:hover { background: rgba(255,255,255,.22); }
.ts-btn-sm { padding: 5px 10px; font-size: 10.5px; }

/* ─ Stats bar ────────────────────────────────────────────── */
.ts-stats {
	display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;
}
.ts-stat-card {
	padding: 9px 14px; border-radius: 8px; border: 1.5px solid;
	display: flex; align-items: center; gap: 9px; flex: 1; min-width: 120px;
}
.ts-stat-card-total   { background: #EEF2FF; border-color: #C7D7FF; }
.ts-stat-card-visible { background: #ECFDF5; border-color: #A7F3D0; }
.ts-stat-card-hidden  { background: #FFF1F2; border-color: #FECDD3; }
.ts-stat-icon  { font-size: 16px; line-height: 1; }
.ts-stat-num   { font-size: 20px; font-weight: 900; line-height: 1; }
.ts-stat-label { font-size: 10px; font-weight: 600; margin-top: 2px; opacity: .75; }
.ts-stat-card-total   .ts-stat-num, .ts-stat-card-total   .ts-stat-label { color: #3B4FE4; }
.ts-stat-card-visible .ts-stat-num, .ts-stat-card-visible .ts-stat-label { color: #047857; }
.ts-stat-card-hidden  .ts-stat-num, .ts-stat-card-hidden  .ts-stat-label { color: #BE185D; }

/* ─ Search ───────────────────────────────────────────────── */
.ts-search-wrap { position: relative; margin-bottom: 12px; }
.ts-search-wrap input {
	width: 100%; padding: 8px 16px 8px 38px;
	border-radius: 8px; border: 1.5px solid #DDE3F0;
	background: #F8FAFF; font-size: 12.5px; color: #1E1B4B;
	outline: none; transition: border .16s, box-shadow .16s;
}
.ts-search-wrap input:focus {
	border-color: #3B4FE4;
	box-shadow: 0 0 0 3px rgba(59,79,228,.09);
}
.ts-search-wrap input::placeholder { color: #A0ABBB; }
.ts-search-icon {
	position: absolute; left: 12px; top: 50%;
	transform: translateY(-50%); font-size: 13px; opacity: .4;
}
.ts-search-clear {
	position: absolute; right: 10px; top: 50%;
	transform: translateY(-50%); font-size: 10px; color: #94A3B8;
	cursor: pointer; display: none; background: #E2E8F0; border-radius: 50%;
	width: 17px; height: 17px; align-items: center; justify-content: center;
	font-weight: 800; border: none; outline: none;
}
.ts-search-clear:hover { background: #CBD5E1; color: #475569; }

/* ─ Tab group card ───────────────────────────────────────── */
.ts-tab-group {
	margin-bottom: 8px; border: 1.5px solid #E8EDF5;
	border-radius: 9px; overflow: hidden;
	box-shadow: 0 1px 4px rgba(0,0,0,.04); background: #fff;
}

/* ─ Tab header ───────────────────────────────────────────── */
.ts-tab-head {
	display: flex; align-items: center; justify-content: space-between;
	padding: 9px 14px; cursor: pointer; user-select: none;
	transition: background .13s; background: #FAFBFE;
}
.ts-tab-head:hover { background: #F3F6FF; }
.ts-tab-head-left  { display: flex; align-items: center; gap: 9px; }
.ts-tab-badge {
	display: inline-flex; align-items: center; justify-content: center;
	width: 28px; height: 28px; border-radius: 7px; font-size: 14px; flex-shrink: 0;
}
.ts-tab-label { font-size: 12.5px; font-weight: 800; color: #1E1B4B; }
.ts-tab-vis-badge {
	font-size: 10px; font-weight: 700; padding: 2px 7px;
	border-radius: 9px; background: #EEF2FF; color: #3B4FE4; margin-left: 4px;
}
.ts-tab-head-right { display: flex; align-items: center; gap: 7px; }
.ts-progress-wrap  { display: flex; align-items: center; gap: 5px; }
.ts-progress-bar   { width: 72px; height: 4px; background: #E2E8F0; border-radius: 3px; overflow: hidden; }
.ts-progress-fill  { height: 100%; border-radius: 3px; transition: width .3s ease; }
.ts-progress-pct   { font-size: 10px; font-weight: 700; color: #64748B; min-width: 28px; }
.ts-tab-all-btn {
	font-size: 10px; font-weight: 700; padding: 3px 9px;
	border-radius: 6px; cursor: pointer; border: 1.5px solid;
	transition: all .13s; background: transparent; outline: none;
}
.ts-chevron {
	font-size: 9px; color: #94A3B8; transition: transform .22s;
	display: inline-flex; align-items: center; justify-content: center;
	width: 16px; height: 16px;
}
.ts-chevron.open { transform: rotate(180deg); }

/* ─ Collapsible body ─────────────────────────────────────── */
.ts-tab-body {
	border-top: 1.5px solid #F1F5F9; overflow: hidden;
	max-height: 9999px; transition: max-height .3s ease;
}

/* ─ Field table ──────────────────────────────────────────── */
.ts-table { width: 100%; border-collapse: collapse; }
.ts-table thead tr { background: #F8FAFC; }
.ts-table thead th {
	padding: 6px 13px;
	font-size: 9px; font-weight: 700; text-transform: uppercase;
	letter-spacing: .10em; color: #94A3B8; text-align: left;
	border-bottom: 1.5px solid #F1F5F9;
}
.ts-table tbody tr { border-bottom: 1px solid #F4F6FA; transition: background .10s; }
.ts-table tbody tr:last-child { border-bottom: none; }
.ts-table tbody tr:hover      { background: #F6F9FF; }
.ts-table tbody tr.ts-hidden  {
	background: repeating-linear-gradient(
		-45deg, #fff8f8, #fff8f8 4px, #fff4f4 4px, #fff4f4 8px
	);
}
.ts-table tbody tr.ts-search-hide { display: none !important; }
.ts-table td { padding: 7px 13px; vertical-align: middle; }

/* ─ Field label ──────────────────────────────────────────── */
.ts-f-label { font-size: 12px; font-weight: 700; color: #1E1B4B; }
.ts-f-name  {
	font-size: 9.5px; font-weight: 500; color: #94A3B8;
	font-family: ui-monospace, 'Cascadia Code', 'Courier New', monospace;
	margin-top: 2px; letter-spacing: .02em;
}

/* ─ Type pill ────────────────────────────────────────────── */
.ts-type {
	display: inline-block; padding: 2px 7px;
	border-radius: 5px; font-size: 9.5px; font-weight: 700; letter-spacing: .04em;
}
.ts-t-Data     { background: #F5F3FF; color: #7C3AED; }
.ts-t-Link     { background: #EEF2FF; color: #4338CA; }
.ts-t-Currency { background: #FFF7ED; color: #C2410C; }
.ts-t-Date     { background: #F0FDF4; color: #15803D; }
.ts-t-Datetime { background: #ECFDF5; color: #047857; }
.ts-t-Int      { background: #FFF1F2; color: #BE185D; }
.ts-t-Float    { background: #FFF1F2; color: #BE185D; }
.ts-t-Select   { background: #FFFBEB; color: #B45309; }
.ts-t-default  { background: #F1F5F9; color: #475569; }

/* ─ Flag badges ──────────────────────────────────────────── */
.ts-flag {
	display: inline-flex; align-items: center; gap: 3px;
	font-size: 9px; font-weight: 700;
	padding: 2px 6px; border-radius: 4px; letter-spacing: .03em; margin-right: 3px;
}
.ts-flag-reqd     { background: #FEE2E2; color: #B91C1C; }
.ts-flag-readonly { background: #EEF2FF; color: #4338CA; }

/* ─ Toggle switch ────────────────────────────────────────── */
.ts-toggle-cell { display: flex; align-items: center; gap: 7px; }
.ts-toggle { position: relative; width: 36px; height: 20px; flex-shrink: 0; }
.ts-toggle input { opacity: 0; width: 0; height: 0; position: absolute; }
.ts-slider {
	position: absolute; inset: 0;
	background: #CBD5E1; border-radius: 20px; cursor: pointer;
	transition: background .2s;
}
.ts-slider::before {
	content: ''; position: absolute;
	width: 14px; height: 14px; left: 3px; bottom: 3px;
	background: #fff; border-radius: 50%;
	transition: transform .2s;
	box-shadow: 0 1px 4px rgba(0,0,0,.18);
}
.ts-toggle input:checked + .ts-slider { background: #3B4FE4; }
.ts-toggle input:checked + .ts-slider::before { transform: translateX(16px); }
.ts-toggle-text {
	font-size: 11px; font-weight: 700; min-width: 40px;
	color: #94A3B8; transition: color .18s;
}
.ts-toggle-text.on { color: #3B4FE4; }

/* ─ No-results ───────────────────────────────────────────── */
.ts-no-results { text-align: center; padding: 28px 20px; color: #94A3B8; display: none; }
.ts-no-results-icon { font-size: 26px; margin-bottom: 6px; }

/* ─ Toast ────────────────────────────────────────────────── */
.ts-toast {
	position: fixed; bottom: 22px; right: 22px;
	background: linear-gradient(135deg, #1E1B4B, #3B4FE4);
	color: #fff; padding: 10px 18px; border-radius: 9px;
	font-size: 12.5px; font-weight: 700;
	box-shadow: 0 5px 22px rgba(59,79,228,.28);
	z-index: 99999; transform: translateY(18px); opacity: 0;
	transition: all .26s cubic-bezier(.34,1.56,.64,1);
	display: flex; align-items: center; gap: 8px;
}
.ts-toast.show { transform: translateY(0); opacity: 1; }

/* ─ Hide search-empty groups ─────────────────────────────── */
.ts-group-hidden { display: none !important; }

/* ─ Regenerate Trip IDs card ─────────────────────────────── */
.ts-regen-card {
	background: linear-gradient(135deg, #7F1D1D 0%, #B91C1C 100%);
	border-radius: 10px; padding: 14px 20px; margin-bottom: 12px;
	display: flex; align-items: center; justify-content: space-between;
	gap: 14px; flex-wrap: wrap;
	box-shadow: 0 2px 14px rgba(185,28,28,.28);
	border: 1px solid rgba(255,255,255,.10);
}
.ts-regen-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
.ts-regen-icon { font-size: 26px; line-height: 1; flex-shrink: 0; }
.ts-regen-title { font-size: 14px; font-weight: 800; color: #fff; letter-spacing: -.01em; }
.ts-regen-sub {
	font-size: 11px; color: rgba(255,255,255,.65); margin-top: 3px;
	font-family: ui-monospace, 'Cascadia Code', monospace; letter-spacing: .02em;
}
.ts-regen-btn {
	display: inline-flex; align-items: center; gap: 6px;
	padding: 9px 20px; border-radius: 7px;
	border: 2px solid rgba(255,255,255,.45);
	background: rgba(255,255,255,.14); color: #fff;
	font-size: 12.5px; font-weight: 800; cursor: pointer;
	transition: all .17s; outline: none; letter-spacing: .02em;
	white-space: nowrap; flex-shrink: 0;
}
.ts-regen-btn:hover:not(:disabled) {
	background: rgba(255,255,255,.28);
	border-color: rgba(255,255,255,.75);
	transform: translateY(-1px);
}
.ts-regen-btn:disabled { opacity: .55; cursor: not-allowed; }

/* ─ Color Settings Panel ─────────────────────────────────── */
.ts-color-section {
	background: #fff; border-radius: 9px; padding: 18px 20px;
	border: 1.5px solid #E2E8F0; margin-bottom: 12px;
}
.ts-color-section-title { font-size: 13px; font-weight: 800; color: #1E1B4B; margin-bottom: 3px; }
.ts-color-section-sub   { font-size: 11.5px; color: #94A3B8; margin-bottom: 14px; }
.ts-color-presets { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 14px; }
.ts-color-swatch {
	width: 26px; height: 26px; border-radius: 50%; cursor: pointer;
	border: 2.5px solid transparent; transition: transform .12s, border-color .12s, box-shadow .12s;
	flex-shrink: 0;
}
.ts-color-swatch:hover { transform: scale(1.22); box-shadow: 0 2px 8px rgba(0,0,0,.18); }
.ts-color-swatch.selected { border-color: #1E1B4B; box-shadow: 0 0 0 2px #fff, 0 0 0 4px #1E1B4B; }
.ts-color-custom-row { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.ts-color-custom-label { font-size: 11.5px; font-weight: 700; color: #64748B; }
.ts-color-custom-input {
	width: 34px; height: 34px; padding: 2px; border-radius: 7px;
	border: 1.5px solid #CBD5E1; cursor: pointer; background: #fff;
}
.ts-color-hex-display { font-size: 12px; font-weight: 700; color: #475569; font-family: monospace; letter-spacing: .04em; }
.ts-color-preview-wrap { margin-bottom: 16px; }
.ts-color-preview-label { font-size: 11px; font-weight: 700; color: #64748B; margin-bottom: 7px; text-transform: uppercase; letter-spacing: .07em; }
.ts-color-preview-card {
	background: #F8FAFC; border-radius: 8px; padding: 10px 14px;
	border: 1.5px solid #E2E8F0; display: flex; align-items: center; gap: 10px;
}
.ts-color-preview-dot { width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0; }
.ts-color-preview-badge {
	display: inline-flex; align-items: center; gap: 5px;
	padding: 4px 11px; border-radius: 14px; font-size: 12px; font-weight: 800;
	color: #fff; letter-spacing: .02em;
}
.ts-color-save-btn {
	display: inline-flex; align-items: center; gap: 6px;
	padding: 8px 20px; border-radius: 7px; border: none; cursor: pointer;
	font-size: 12.5px; font-weight: 800; color: #fff;
	background: linear-gradient(135deg, #1E1B4B, #3B4FE4);
	box-shadow: 0 2px 10px rgba(59,79,228,.22); transition: opacity .17s;
}
.ts-color-save-btn:hover { opacity: .87; }
.ts-color-save-btn:disabled { opacity: .55; cursor: not-allowed; }
	[data-theme="dark"] #ts-root { color: var(--text-color, #e9ecef); }
	[data-theme="dark"] .ts-tabs-bar { background: var(--subtle-accent, #1a1a2e); border-color: var(--border-color, #333); }
	[data-theme="dark"] .ts-tab-nav { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-tab-nav.active { background: var(--control-bg, #2d2d4d); color: var(--text-color, #fff); }
	[data-theme="dark"] .ts-tab-nav:hover:not(.active) { background: rgba(255,255,255,.08); color: var(--text-color, #e9ecef); }
	[data-theme="dark"] .ts-toolbar { background: linear-gradient(135deg, var(--bg-color, #1a1a2e) 0%, var(--card-bg, #2d2d4d) 100%); box-shadow: 0 2px 12px rgba(0,0,0,.35); }
	[data-theme="dark"] .ts-tb-title { color: var(--text-color, #fff); }
	[data-theme="dark"] .ts-tb-sub { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-btn-primary { background: #3B4FE4; color: #fff; }
	[data-theme="dark"] .ts-btn-primary:hover { background: #5566ff; }
	[data-theme="dark"] .ts-btn-ghost { background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.12); color: var(--text-color, #fff); }
	[data-theme="dark"] .ts-btn-ghost:hover { background: rgba(255,255,255,.12); }
	[data-theme="dark"] .ts-stat-card { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
	[data-theme="dark"] .ts-stat-card-total .ts-stat-num, [data-theme="dark"] .ts-stat-card-total .ts-stat-label { color: #6e78ff; }
	[data-theme="dark"] .ts-stat-card-visible .ts-stat-num, [data-theme="dark"] .ts-stat-card-visible .ts-stat-label { color: #5eead4; }
	[data-theme="dark"] .ts-stat-card-hidden .ts-stat-num, [data-theme="dark"] .ts-stat-card-hidden .ts-stat-label { color: #f87171; }
	[data-theme="dark"] .ts-search-wrap input { background: var(--control-bg, #2d2d4d); border-color: var(--border-color, #444); color: var(--text-color, #fff); }
	[data-theme="dark"] .ts-search-wrap input::placeholder { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-search-wrap input:focus { border-color: #3B4FE4; box-shadow: 0 0 0 3px rgba(59,79,228,.14); }
	[data-theme="dark"] .ts-tab-group { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
	[data-theme="dark"] .ts-tab-head { background: var(--subtle-accent, #1a1a2e); }
	[data-theme="dark"] .ts-tab-head:hover { background: rgba(59,79,228,.08); }
	[data-theme="dark"] .ts-tab-label { color: var(--text-color, #fff); }
	[data-theme="dark"] .ts-tab-vis-badge { background: rgba(59,79,228,.15); color: #6e78ff; }
	[data-theme="dark"] .ts-table thead tr { background: var(--subtle-accent, #1a1a2e); }
	[data-theme="dark"] .ts-table thead th { color: var(--text-muted, #8d99a6); border-bottom-color: var(--border-color, #444); }
	[data-theme="dark"] .ts-table tbody tr { border-bottom-color: var(--border-color, #333); }
	[data-theme="dark"] .ts-table tbody tr:hover { background: rgba(59,79,228,.06); }
	[data-theme="dark"] .ts-table tbody tr.ts-hidden { background: repeating-linear-gradient(-45deg, #4a1a1a, #4a1a1a 4px, #3a1010 4px, #3a1010 8px); }
	[data-theme="dark"] .ts-f-label { color: var(--text-color, #fff); }
	[data-theme="dark"] .ts-f-name { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-type { background: rgba(59,79,228,.12) !important; color: #90caf9 !important; }
	[data-theme="dark"] .ts-flag-reqd { background: rgba(220,38,38,.25); color: #f87171; }
	[data-theme="dark"] .ts-flag-readonly { background: rgba(59,79,228,.15); color: #90caf9; }
	[data-theme="dark"] .ts-slider { background: var(--border-color, #555); }
	[data-theme="dark"] .ts-slider::before { background: var(--text-color, #fff); }
	[data-theme="dark"] .ts-toggle input:checked + .ts-slider { background: #3B4FE4; }
	[data-theme="dark"] .ts-toggle-text { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-toggle-text.on { color: #3B4FE4; }
	[data-theme="dark"] .ts-no-results { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-color-section { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
	[data-theme="dark"] .ts-color-section-title { color: var(--text-color, #fff); }
	[data-theme="dark"] .ts-color-section-sub { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-color-swatch.selected { border-color: var(--text-color, #fff); box-shadow: 0 0 0 2px var(--card-bg, #2d2d4d), 0 0 0 4px var(--text-color, #fff); }
	[data-theme="dark"] .ts-color-custom-input { background: var(--control-bg, #2d2d4d); border-color: var(--border-color, #444); }
	[data-theme="dark"] .ts-color-custom-label { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-color-hex-display { color: var(--text-color, #fff); }
	[data-theme="dark"] .ts-color-preview-label { color: var(--text-muted, #8d99a6); }
	[data-theme="dark"] .ts-color-preview-card { background: var(--subtle-accent, #1a1a2e); border-color: var(--border-color, #444); }
`;
	document.head.appendChild(s);
}

// ══════════════════════════════════════════════════════════════════
//  FRAPPE FORM
// ══════════════════════════════════════════════════════════════════

frappe.ui.form.on("Trip Settings", {

	onload(frm) {
		inject_ts_styles();
	},

	refresh(frm) {
		inject_ts_styles();

		if (frm.fields_dict[CHILD_TABLE_FIELD]) {
			frm.fields_dict[CHILD_TABLE_FIELD].$wrapper
				.closest(".form-section, .section-body, .frappe-control")
				.hide();
		}
		if (frm.fields_dict["trip_type"]) {
			frm.fields_dict["trip_type"].$wrapper
				.closest(".form-group, .frappe-control")
				.hide();
		}

		frm.disable_save();
		frm.$wrapper.find("#ts-root").remove();

		const saved_map = {};
		(frm.doc[CHILD_TABLE_FIELD] || []).forEach(r => {
			saved_map[r.fieldname] = r.is_visible ? true : false;
		});

		const mount_selectors = [
			".layout-main-section",
			".page-content .container",
			".page-content",
			".form-layout",
			".page-form",
		];
		let $mount = null;
		for (const sel of mount_selectors) {
			const $el = frm.$wrapper.find(sel).first();
			if ($el.length) { $mount = $el; break; }
		}
		if (!$mount) $mount = frm.$wrapper;

		const $root = $('<div id="ts-root"></div>');
		$mount.prepend($root);

		$root.html('<div style="padding:32px;text-align:center;color:#6B7280;font-size:13px;">Loading Trip fields…</div>');
		load_trip_tabs()
			.then(() => {
				$root.empty();
				build_ui(frm, $root, saved_map);
			})
			.catch(err => {
				$root.html(`<div style="padding:24px;color:#DC2626;">Failed to load Trip fields: ${frappe.utils.escape_html(String(err))}</div>`);
			});
	},
	//  after_save(frm) {
    //     // This will now trigger because we used frm.save()
    //     frappe.show_alert({ message: __("Settings saved successfully"), indicator: "green" });
        
    //     // Brief delay before reload so the user sees the success message
    //     setTimeout(() => {
    //         window.location.reload();
    //     }, 1000);
    // }
	
});

// ══════════════════════════════════════════════════════════════════
//  BUILD FULL UI
// ══════════════════════════════════════════════════════════════════

function build_ui(frm, $root, saved_map) {

	const total_fields = TRIP_TABS.reduce((a, t) => a + t.fields.length, 0);
	const state = {};
	TRIP_TABS.forEach(tab => {
		tab.fields.forEach(f => {
			state[f.fieldname] = (f.fieldname in saved_map) ? saved_map[f.fieldname] : true;
		});
	});

	// ── Regenerate Trip IDs card — visible to Administrator only ─────
	if (frappe.session.user === "Administrator") {

		// Build dynamic format example using today's date
		const _now      = new Date();
		const _mm       = String(_now.getMonth() + 1).padStart(2, "0");
		const _yy       = String(_now.getFullYear()).slice(-2);
		const _mmyy     = _mm + _yy;
		// Determine FY label dynamically (Apr–Mar)
		const _fyStart  = _now.getMonth() >= 3 ? _now.getFullYear() : _now.getFullYear() - 1;
		const _fyEnd    = _fyStart + 1;
		const _fyLabel  = `${String(_fyStart).slice(-2)}${String(_fyEnd).slice(-2)}`;
		const _example  = `CO\u2011TYPE\u2011${_mmyy}00001`;   // \u2011 = non-breaking hyphen
		const _seriesEx = `CO\u2011${_fyLabel}`;

		$root.append(`
			<div class="ts-regen-card">
				<div class="ts-regen-left">
					<div class="ts-regen-icon">🔄</div>
					<div>
						<div class="ts-regen-title">Regenerate All Trip IDs</div>
						<div class="ts-regen-sub">
							Format: CO&#8209;TYPE&#8209;${_mmyy}#####
							&nbsp;·&nbsp; FY counter series: ${_seriesEx}
							&nbsp;·&nbsp; Resets every April 1
						</div>
					</div>
				</div>
				<button class="ts-regen-btn" id="ts-regen-btn">🔄 Regenerate Trip IDs</button>
			</div>
		`);

		$root.on("click", "#ts-regen-btn", function () {
			frappe.confirm(
				`<div style="text-align:center;padding:8px 0 4px;">
					<div style="font-size:32px;margin-bottom:10px;">⚠️</div>
					<div style="font-size:15px;font-weight:800;color:#B91C1C;margin-bottom:10px;">
						Regenerate ALL Trip IDs?
					</div>
					<div style="font-size:12.5px;color:#374151;line-height:1.8;text-align:left;
						background:#FFF7ED;border:1.5px solid #FCD34D;border-radius:8px;padding:12px 16px;">
						• All existing trips will be <b>renamed</b> in date order<br>
						• Format:
						  <code style="background:#F1F5F9;padding:1px 7px;border-radius:4px;
						               font-size:11.5px;font-weight:700;letter-spacing:.02em;">
						    ${_example}
						  </code><br>
						• FY series key: <code style="background:#F1F5F9;padding:1px 7px;border-radius:4px;
						                        font-size:11px;">${_seriesEx}</code>
						  (Apr ${_fyStart} – Mar ${_fyEnd})<br>
						• Counter resets every <b>April 1</b> (Indian financial year)<br>
						• All linked documents updated automatically<br>
						• <b style="color:#DC2626;">Take a database backup before proceeding.</b>
					</div>
				</div>`,
				() => {
					const $btn = $("#ts-regen-btn").text("⏳ Regenerating…").prop("disabled", true);
					frappe.call({
						method: "logicore.logicore.doctype.trip_settings.trip_settings.regenerate_trip_ids",
						freeze: true,
						freeze_message: "Regenerating Trip IDs… This may take a few minutes for large datasets.",
						callback(r) {
							$btn.text("🔄 Regenerate Trip IDs").prop("disabled", false);
							if (!r.message) return;
							const m = r.message;
							const hasErrors = m.errors && m.errors.length > 0;
							frappe.msgprint({
								title: hasErrors ? "Regeneration Completed with Errors" : "Regeneration Complete",
								indicator: hasErrors ? "orange" : "green",
								message: `
									<div style="font-size:13px;line-height:1.8;">
										<b>✅ Renamed:</b> ${m.renamed} / ${m.total} trips<br>
										${hasErrors
											? `<b style="color:#DC2626;">⚠️ Errors:</b> ${m.errors.length} trip(s) failed
											   <br><small style="color:#6B7280;">Check browser console for details.</small>`
											: "<b style='color:#16A34A;'>No errors.</b>"
										}
									</div>
								`,
							});
							if (hasErrors) console.error("Trip ID regen errors:", m.errors);
						},
						error() {
							$btn.text("🔄 Regenerate Trip IDs").prop("disabled", false);
						},
					});
				}
			);
		});

	} // end Administrator-only block

	const tripTypePerm = _tms_trip_type_perm(frm);
	if (tripTypePerm.read) {
		if (frm.is_new()) {
			$root.append(`
				<div class="ts-type-header">
					<div class="ts-type-header-icon">🚛</div>
					<div class="ts-type-header-body">
						<div class="ts-type-header-meta">
							<div class="ts-type-header-eyebrow">Trip Type Configuration</div>
							<div class="ts-type-header-value" id="ts-type-display">${
								frm.doc.trip_type
									? frappe.utils.escape_html(frm.doc.trip_type)
									: "Select a Trip Type"
							}</div>
							<div class="ts-type-header-hint">Choose which trip type to configure field visibility for</div>
						</div>
						<div class="ts-type-select-wrap">
							<select class="ts-type-select" id="ts-type-select" ${tripTypePerm.write ? "" : "disabled"}>
								<option value="">-- Select Trip Type --</option>
							</select>
						</div>
					</div>
				</div>
			`);
			frappe.call({
				method: "frappe.client.get_list",
				args: { doctype: "Trip Type", fields: ["name"], limit_page_length: 100 },
				callback(r) {
					if (r.message) {
						const $sel = $root.find("#ts-type-select");
						r.message.forEach(tt => {
							const escaped = frappe.utils.escape_html(tt.name);
							$sel.append(`<option value="${escaped}">${escaped}</option>`);
						});
						if (frm.doc.trip_type) $sel.val(frm.doc.trip_type);
					}
				},
			});
			if (tripTypePerm.write) {
				$root.on("change", "#ts-type-select", function () {
					const val = this.value;
					frm.set_value("trip_type", val);
					$root.find("#ts-type-display").text(val || "Select a Trip Type");
				});
			}
		} else {
			$root.append(`
				<div class="ts-type-header">
					<div class="ts-type-header-icon">🚛</div>
					<div class="ts-type-header-body">
						<div class="ts-type-header-meta">
							<div class="ts-type-header-eyebrow">Configuring Trip Type</div>
							<div class="ts-type-header-value" id="ts-type-display-wrap">
								<span class="ts-type-badge-large">✦ ${frappe.utils.escape_html(frm.doc.trip_type)}</span>
								${tripTypePerm.write ? `<button type="button" class="ts-type-edit-btn" id="ts-type-edit-btn" title="${__("Change Trip Type")}">✏️</button>` : ""}
							</div>
							<div class="ts-type-header-hint">Field visibility settings for this trip type</div>
						</div>
						<div class="ts-type-select-wrap" id="ts-type-select-wrap" style="display:none;">
							<select class="ts-type-select" id="ts-type-select-existing">
								<option value="">-- Select Trip Type --</option>
							</select>
						</div>
					</div>
				</div>
			`);

			if (tripTypePerm.write) {
				$root.on("click", "#ts-type-edit-btn", function () {
					$root.find("#ts-type-display-wrap").hide();
					const $wrap = $root.find("#ts-type-select-wrap").show();
					const $sel = $wrap.find("#ts-type-select-existing");
					if ($sel.data("loaded")) return;
					$sel.data("loaded", true);
					frappe.call({
						method: "frappe.client.get_list",
						args: { doctype: "Trip Type", fields: ["name"], limit_page_length: 100 },
						callback(r) {
							if (r.message) {
								r.message.forEach(tt => {
									const escaped = frappe.utils.escape_html(tt.name);
									$sel.append(`<option value="${escaped}">${escaped}</option>`);
								});
								$sel.val(frm.doc.trip_type);
							}
						},
					});
				});

				$root.on("change", "#ts-type-select-existing", function () {
					const val = this.value;
					const $sel = $(this);
					if (!val || val === frm.doc.trip_type) return;
					frappe.confirm(
						__("Change this settings record from {0} to {1}? Its field visibility settings will move to the new Trip Type.", [frm.doc.trip_type, val]),
						() => {
							frm.set_value("trip_type", val);
							frm.save().then(() => {
								frappe.set_route("Form", "Trip Settings", val);
							});
						},
						() => {
							$sel.val(frm.doc.trip_type);
						}
					);
				});
			}
		}
	}

	$root.append(`
		<div class="ts-tabs-bar" id="ts-tabs-bar">
			<button class="ts-tab-nav active" data-tab="fields">⚙️ Field Settings</button>
			<button class="ts-tab-nav"        data-tab="colors">🎨 Color Settings</button>
		</div>
	`);

	const $fp = $('<div id="ts-panel-fields"></div>');
	const $cp = $('<div id="ts-panel-colors" style="display:none"></div>');
	$root.append($fp).append($cp);

	$root.on("click", ".ts-tab-nav", function () {
		$root.find(".ts-tab-nav").removeClass("active");
		$(this).addClass("active");
		const tab = $(this).data("tab");
		$fp.toggle(tab === "fields");
		$cp.toggle(tab === "colors");
	});

	// ══ FIELD SETTINGS PANEL ══════════════════════════════════════

	$fp.append(`
		<div class="ts-toolbar">
			<div class="ts-tb-left">
				<span class="ts-tb-icon">⚙️</span>
				<div>
					<div class="ts-tb-title">Trip Field Visibility Settings</div>
					<div class="ts-tb-sub">${total_fields} fields across ${TRIP_TABS.length} tabs · v${TS_VERSION}</div>
				</div>
			</div>
			<div class="ts-tb-right">
				<button class="ts-btn ts-btn-ghost ts-btn-sm" id="ts-show-all">👁️ Show All</button>
				<button class="ts-btn ts-btn-ghost ts-btn-sm" id="ts-hide-all">🙈 Hide All</button>
				<button class="ts-btn ts-btn-primary"         id="ts-save"    >💾 Save Settings</button>
			</div>
		</div>
	`);

	$fp.append(`
		<div class="ts-stats" id="ts-stats">
			<div class="ts-stat-card ts-stat-card-total">
				<div class="ts-stat-icon">📋</div>
				<div>
					<div class="ts-stat-num" id="ts-s-total">${total_fields}</div>
					<div class="ts-stat-label">Total Fields</div>
				</div>
			</div>
			<div class="ts-stat-card ts-stat-card-visible">
				<div class="ts-stat-icon">👁️</div>
				<div>
					<div class="ts-stat-num" id="ts-s-visible">0</div>
					<div class="ts-stat-label">Visible on Trip Form</div>
				</div>
			</div>
			<div class="ts-stat-card ts-stat-card-hidden">
				<div class="ts-stat-icon">🙈</div>
				<div>
					<div class="ts-stat-num" id="ts-s-hidden">0</div>
					<div class="ts-stat-label">Hidden from Trip Form</div>
				</div>
			</div>
		</div>
	`);

	$fp.append(`
		<div class="ts-search-wrap">
			<span class="ts-search-icon">🔍</span>
			<input id="ts-search" type="text"
				placeholder="Search by field label or fieldname…" autocomplete="off" />
			<button id="ts-search-clear" class="ts-search-clear">✕</button>
		</div>
		<div class="ts-no-results" id="ts-no-results">
			<div class="ts-no-results-icon">🔎</div>
			<div style="font-weight:700;font-size:14px;color:#374151;margin-top:6px;">No fields match your search</div>
			<div style="font-size:12px;color:#9CA3AF;margin-top:4px;">Try a different keyword</div>
		</div>
	`);

	TRIP_TABS.forEach(tab => {
		$fp.append(build_tab_group($root, tab, state));
	});

	$root.find("#ts-show-all").on("click", () => bulk_toggle($root, state, true));
	$root.find("#ts-hide-all").on("click", () => bulk_toggle($root, state, false));
	$root.find("#ts-save").on("click",     () => save_settings(frm, state));

	const $input = $root.find("#ts-search");
	const $clear = $root.find("#ts-search-clear");

	$input.on("input", function () {
		const q = $(this).val().trim().toLowerCase();
		$clear.toggle(!!q).css("display", q ? "inline-flex" : "none");
		run_search($root, q);
	});
	$clear.on("click", () => {
		$input.val("").trigger("input").focus();
	});

	update_stats($root, state);

	// ══ COLOR SETTINGS PANEL ══════════════════════════════════════
	build_color_panel($cp, frm);
}

// ══════════════════════════════════════════════════════════════════
//  BUILD ONE TAB GROUP
// ══════════════════════════════════════════════════════════════════

function build_tab_group($root, tab, state) {
	const total    = tab.fields.length;
	const group_id = `ts-g-${tab.key}`;
	const $group   = $(`<div class="ts-tab-group" id="${group_id}"></div>`);

	const $head = $(`
		<div class="ts-tab-head">
			<div class="ts-tab-head-left">
				<div class="ts-tab-badge" style="background:${rgba(tab.color,.13)};color:${tab.color};">
					${tab.icon}
				</div>
				<span class="ts-tab-label">${tab.label}</span>
				<span class="ts-tab-vis-badge ts-tvc-${tab.key}">— / ${total}</span>
			</div>
			<div class="ts-tab-head-right">
				<div class="ts-progress-wrap">
					<div class="ts-progress-bar">
						<div class="ts-progress-fill ts-pf-${tab.key}"
							style="width:0%;background:${tab.color};"></div>
					</div>
					<span class="ts-progress-pct ts-pp-${tab.key}">0%</span>
				</div>
				<button class="ts-tab-all-btn ts-ta-${tab.key}"
					style="color:${tab.color};border-color:${rgba(tab.color,.35)};background:${rgba(tab.color,.07)};"
				>All Off</button>
				<span class="ts-chevron open">▼</span>
			</div>
		</div>
	`);

	const $body = $(`<div class="ts-tab-body"></div>`);

	const $table = $(`
		<table class="ts-table">
			<thead>
				<tr>
					<th style="width:34%">Field Label</th>
					<th style="width:15%">Type</th>
					<th style="width:24%">Flags</th>
					<th style="width:27%">Visibility on Trip Form</th>
				</tr>
			</thead>
			<tbody></tbody>
		</table>
	`);
	const $tbody = $table.find("tbody");

	tab.fields.forEach(f => {
		const is_vis    = state[f.fieldname];
		const type_key  = (f.fieldtype || "Data").replace(/\s+/g,"");
		const type_cls  = `ts-t-${["Data","Link","Currency","Date","Datetime","Int","Float","Select"].includes(type_key) ? type_key : "default"}`;
		const flags_html = [
			f.reqd      ? `<span class="ts-flag ts-flag-reqd">● required</span>`    : "",
			f.read_only ? `<span class="ts-flag ts-flag-readonly">🔒 read only</span>` : "",
		].join("") || `<span style="color:#CBD5E1;font-size:11px;">—</span>`;

		const $row = $(`
			<tr data-fn="${f.fieldname}"
				data-q="${(f.label||"").toLowerCase()} ${f.fieldname.toLowerCase()}"
				class="${is_vis ? "" : "ts-hidden"}">
				<td>
					<div class="ts-f-label">${frappe.utils.escape_html(f.label || f.fieldname)}</div>
					<div class="ts-f-name">${f.fieldname}</div>
				</td>
				<td><span class="ts-type ${type_cls}">${f.fieldtype}</span></td>
				<td>${flags_html}</td>
				<td>
					<div class="ts-toggle-cell">
						<label class="ts-toggle">
							<input type="checkbox" data-fn="${f.fieldname}" ${is_vis ? "checked" : ""} />
							<span class="ts-slider"></span>
						</label>
						<span class="ts-toggle-text ${is_vis ? "on" : ""}">${is_vis ? "Visible" : "Hidden"}</span>
					</div>
				</td>
			</tr>
		`);

		$row.find("input").on("change", function () {
			const fn  = $(this).data("fn");
			const on  = $(this).prop("checked");
			state[fn] = on;
			$(this).closest(".ts-toggle-cell").find(".ts-toggle-text")
				.text(on ? "Visible" : "Hidden")
				.toggleClass("on", on);
			$row.toggleClass("ts-hidden", !on);
			update_tab_stats($group, tab, state);
			update_stats($root, state);
		});

		$tbody.append($row);
	});

	$body.append($table);
	$group.append($head).append($body);

	$head.on("click", e => {
		if ($(e.target).closest(".ts-tab-all-btn").length) return;
		const open = $head.find(".ts-chevron").hasClass("open");
		$body.css("max-height", open ? "0" : "9999px");
		$head.find(".ts-chevron").toggleClass("open", !open);
	});

	$head.find(".ts-tab-all-btn").on("click", function () {
		const all_on  = tab.fields.every(f => state[f.fieldname]);
		const new_val = !all_on;
		tab.fields.forEach(f => {
			state[f.fieldname] = new_val;
			const $inp = $group.find(`input[data-fn="${f.fieldname}"]`);
			$inp.prop("checked", new_val);
			$inp.closest(".ts-toggle-cell").find(".ts-toggle-text")
				.text(new_val ? "Visible" : "Hidden")
				.toggleClass("on", new_val);
			$inp.closest("tr").toggleClass("ts-hidden", !new_val);
		});
		update_tab_stats($group, tab, state);
		update_stats($root, state);
	});

	update_tab_stats($group, tab, state);
	return $group;
}

// ══════════════════════════════════════════════════════════════════
//  COLOR SETTINGS PANEL  ← FIXED: won't accidentally override combo
// ══════════════════════════════════════════════════════════════════

const COLOR_PRESETS = [
	{ hex: "#3B4FE4", name: "Indigo"  },
	{ hex: "#2563EB", name: "Blue"    },
	{ hex: "#0EA5E9", name: "Sky"     },
	{ hex: "#0D9488", name: "Teal"    },
	{ hex: "#16A34A", name: "Green"   },
	{ hex: "#65A30D", name: "Lime"    },
	{ hex: "#D97706", name: "Amber"   },
	{ hex: "#EA580C", name: "Orange"  },
	{ hex: "#DC2626", name: "Red"     },
	{ hex: "#BE185D", name: "Pink"    },
	{ hex: "#7C3AED", name: "Violet"  },
	{ hex: "#475569", name: "Slate"   },
	{ hex: "#0F172A", name: "Navy"    },
	{ hex: "#059669", name: "Emerald" },
	{ hex: "#B45309", name: "Brown"   },
	{ hex: "#6B21A8", name: "Purple"  },
];

function build_color_panel($cp, frm) {
	// ── Start with whatever is saved (may be empty/null) ───────────
	// Empty = "use combo default" — do NOT pre-select any swatch
	let selectedColor = (frm.doc.trip_color || "").trim() || null;

	const swatchHtml = COLOR_PRESETS.map(p => `
		<div class="ts-color-swatch${selectedColor === p.hex ? " selected" : ""}"
			style="background:${p.hex};" data-color="${p.hex}" title="${p.name}"></div>
	`).join("");

	const tripLabel    = frappe.utils.escape_html(frm.doc.trip_type || "Trip Type");
	const previewColor = selectedColor || "#94A3B8";

	$cp.append(`
		<div class="ts-color-section">
			<div class="ts-color-section-title">🎨 Trip Type Accent Color</div>
			<div class="ts-color-section-sub">
				Optionally set a custom color override for this trip type.
				If blank, the Trip form will use the <strong>automatic combo theme</strong> for this type — no action needed.
			</div>

			${!selectedColor ? `
			<div id="ts-cp-none-note" style="
				display:flex;align-items:center;gap:10px;
				background:#FFFBEB;border:1.5px solid #FCD34D;border-radius:10px;
				padding:12px 16px;margin-bottom:18px;font-size:12px;font-weight:700;color:#92400E;">
				<span style="font-size:18px;">ℹ️</span>
				No custom color set — Trip form is using the <em>automatic combo theme</em> for this type. Pick a color below only if you want a custom override.
			</div>` : ""}

			<div class="ts-color-presets" id="ts-cp-swatches">${swatchHtml}</div>

			<div class="ts-color-custom-row">
				<span class="ts-color-custom-label">Custom Color</span>
				<input type="color" class="ts-color-custom-input" id="ts-cp-picker"
					value="${selectedColor || "#3B4FE4"}" />
				<span class="ts-color-hex-display" id="ts-cp-hex">
					${selectedColor ? selectedColor.toUpperCase() : "— none selected —"}
				</span>
			</div>

			<div class="ts-color-preview-wrap">
				<div class="ts-color-preview-label">Preview</div>
				<div class="ts-color-preview-card">
					<div class="ts-color-preview-dot" id="ts-cp-dot" style="background:${previewColor};"></div>
					<span class="ts-color-preview-badge" id="ts-cp-badge" style="background:${previewColor};">
						🚛 ${tripLabel}
					</span>
					<span id="ts-cp-hint" style="font-size:12px;color:#94A3B8;margin-left:8px;">
						${selectedColor ? "— how this trip type appears in lists" : "— select a color to preview"}
					</span>
				</div>
			</div>

			<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
				<button class="ts-color-save-btn" id="ts-cp-save">🎨 Save Color</button>
				${selectedColor ? `
				<button id="ts-cp-clear" style="
					padding:11px 20px;border-radius:10px;border:1.5px solid #CBD5E1;
					background:#fff;color:#64748B;font-size:13px;font-weight:700;cursor:pointer;
					transition:all .2s;display:inline-flex;align-items:center;gap:6px;">
					🗑️ Clear (Use Default Combo)
				</button>` : ""}
			</div>
		</div>
	`);

	function applyColor(hex) {
		selectedColor = hex;
		$cp.find(".ts-color-swatch").removeClass("selected");
		$cp.find(`.ts-color-swatch[data-color="${hex}"]`).addClass("selected");
		$cp.find("#ts-cp-picker").val(hex);
		$cp.find("#ts-cp-hex").text(hex.toUpperCase());
		$cp.find("#ts-cp-dot").css("background", hex);
		$cp.find("#ts-cp-badge").css("background", hex);
		$cp.find("#ts-cp-hint").text("— how this trip type will appear");
		$cp.find("#ts-cp-none-note").hide();
	}

	$cp.on("click", ".ts-color-swatch", function () {
		applyColor($(this).data("color"));
	});

	$cp.on("input", "#ts-cp-picker", function () {
		applyColor(this.value);
	});

	// ── Save custom color ──────────────────────────────────────────
// Replace the #ts-cp-save click handler with this:
$cp.on("click", "#ts-cp-save", function () {
    if (!selectedColor) {
        frappe.show_alert({ message: "Please select a color first.", indicator: "orange" });
        return;
    }
    const $btn = $(this).text("⏳ Saving...").prop("disabled", true);
    
    // Set value in the form
    frm.set_value("trip_color", selectedColor);

    // Use frm.save() instead of frappe.call
    frm.save().then(() => {
        $btn.text("🎨 Save Color").prop("disabled", false);
    }).catch(() => {
        $btn.text("🎨 Save Color").prop("disabled", false);
    });
});

	// ── Clear color → revert to auto combo ────────────────────────
	$cp.on("click", "#ts-cp-clear", function () {
		frappe.confirm(
			"Remove the custom color?<br>The Trip form will automatically use the <b>default combo theme</b> for this trip type.",
			() => {
				const $btn = $(this).text("⏳ Clearing…").prop("disabled", true);
				frm.doc.trip_color = "";
				selectedColor      = null;

				$cp.find(".ts-color-swatch").removeClass("selected");
				$cp.find("#ts-cp-hex").text("— none selected —");
				$cp.find("#ts-cp-dot").css("background", "#94A3B8");
				$cp.find("#ts-cp-badge").css("background", "#94A3B8");
				$cp.find("#ts-cp-hint").text("— select a color to preview");
				$cp.find("#ts-cp-none-note").length
					? $cp.find("#ts-cp-none-note").show()
					: $cp.find(".ts-color-section-sub").after(`
						<div id="ts-cp-none-note" style="
							display:flex;align-items:center;gap:10px;
							background:#FFFBEB;border:1.5px solid #FCD34D;border-radius:10px;
							padding:12px 16px;margin-bottom:18px;font-size:12px;font-weight:700;color:#92400E;">
							<span style="font-size:18px;">ℹ️</span>
							No custom color set — Trip form is using the automatic combo theme.
						</div>`);

				frappe.call({
					method: "frappe.client.save",
					args:   { doc: frm.doc },
					freeze: false,
					callback(r) {
						$btn.remove(); // remove clear button since nothing to clear
						if (!r.exc) {
							show_toast("✅ Custom color removed — using combo default.");
							frappe.show_alert({ message: "Color cleared.", indicator: "green" }, 4);
						}
					},
					error() {
						$btn.text("🗑️ Clear (Use Default Combo)").prop("disabled", false);
					},
				});
			}
		);
	});
}

// ══════════════════════════════════════════════════════════════════
//  STAT / PROGRESS HELPERS
// ══════════════════════════════════════════════════════════════════

function update_tab_stats($group, tab, state) {
	const total = tab.fields.length;
	const vis   = tab.fields.filter(f => state[f.fieldname]).length;
	const pct   = Math.round((vis / total) * 100);
	$group.find(`.ts-pf-${tab.key}`).css("width", pct + "%");
	$group.find(`.ts-pp-${tab.key}`).text(pct + "%");
	$group.find(`.ts-tvc-${tab.key}`).text(`${vis} / ${total} visible`);
	const all_on = vis === total;
	$group.find(`.ts-ta-${tab.key}`).text(all_on ? "All Off" : "All On");
}

function update_stats($root, state) {
	const vals = Object.values(state);
	const vis  = vals.filter(Boolean).length;
	$root.find("#ts-s-visible").text(vis);
	$root.find("#ts-s-hidden").text(vals.length - vis);
}

// ══════════════════════════════════════════════════════════════════
//  BULK TOGGLE
// ══════════════════════════════════════════════════════════════════

function bulk_toggle($root, state, on) {
	TRIP_TABS.forEach(tab => {
		tab.fields.forEach(f => {
			state[f.fieldname] = on;
			const $inp = $root.find(`input[data-fn="${f.fieldname}"]`);
			$inp.prop("checked", on);
			$inp.closest(".ts-toggle-cell").find(".ts-toggle-text")
				.text(on ? "Visible" : "Hidden").toggleClass("on", on);
			$inp.closest("tr").toggleClass("ts-hidden", !on);
		});
		const $group = $root.find(`#ts-g-${tab.key}`);
		update_tab_stats($group, tab, state);
	});
	update_stats($root, state);
}

// ══════════════════════════════════════════════════════════════════
//  SEARCH
// ══════════════════════════════════════════════════════════════════

function run_search($root, q) {
	let any_visible = false;
	$root.find(".ts-tab-group").each(function () {
		const $grp = $(this);
		let grp_vis = 0;
		$grp.find("tbody tr").each(function () {
			const match = !q || $(this).data("q").includes(q);
			$(this).toggleClass("ts-search-hide", !match);
			if (match) grp_vis++;
		});
		$grp.toggleClass("ts-group-hidden", grp_vis === 0);
		if (grp_vis) any_visible = true;
		if (q && grp_vis > 0) {
			$grp.find(".ts-tab-body").css("max-height", "9999px");
			$grp.find(".ts-chevron").addClass("open");
		}
	});
	$root.find("#ts-no-results").toggle(!any_visible && !!q);
}

// ══════════════════════════════════════════════════════════════════
//  SAVE FIELD SETTINGS
// ══════════════════════════════════════════════════════════════════

function save_settings(frm, state) {
    const $btn = $("#ts-save").text("⏳ Saving...").prop("disabled", true);

    // 1. Clear and rebuild the child table in the local doc object
    frm.clear_table(CHILD_TABLE_FIELD);
    
    TRIP_TABS.forEach(tab => {
        tab.fields.forEach(f => {
            let row = frm.add_child(CHILD_TABLE_FIELD);
            row.fieldname = f.fieldname;
            row.label = f.label || f.fieldname;
            row.fieldtype = f.fieldtype;
            row.is_visible = state[f.fieldname] ? 1 : 0;
        });
    });

    // 2. Use the standard Frappe save method
    // This correctly updates the 'modified' timestamp and prevents the error
    frm.save().then(() => {
        $btn.text("💾 Save Settings").prop("disabled", false);
        // Page reload will be handled in the after_save trigger below
    }).catch(() => {
        $btn.text("💾 Save Settings").prop("disabled", false);
    });
}

// ══════════════════════════════════════════════════════════════════
//  UTILS
// ══════════════════════════════════════════════════════════════════

function rgba(hex, a) {
	try {
		const h = hex.replace("#","");
		return `rgba(${parseInt(h.slice(0,2),16)},${parseInt(h.slice(2,4),16)},${parseInt(h.slice(4,6),16)},${a})`;
	} catch(_){ return hex; }
}

function show_toast(msg) {
	$(".ts-toast").remove();
	const $t = $(`<div class="ts-toast">${msg}</div>`).appendTo("body");
	setTimeout(() => $t.addClass("show"), 20);
	setTimeout(() => { $t.removeClass("show"); setTimeout(() => $t.remove(), 350); }, 3200);
}