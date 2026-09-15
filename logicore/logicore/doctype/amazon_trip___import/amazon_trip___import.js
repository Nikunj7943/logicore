// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

const AMAZON_IMPORT_TEMPLATE_PREFIX = "Amazon Data for New ERP 2026";
const ATIP_EVENT_PROGRESS = "amazon_trip_import_progress";
const ATIP_POLL_INTERVAL_MS = 1000;
const ATIP_ACTIVE_STATUSES = new Set(["Queued", "Running", "Previewing"]);
const ATIP_TERMINAL_STATUSES = new Set(["Completed", "Failed", "Cancelled"]);

frappe.ui.form.on("Amazon trip - Import", {
	refresh(frm) {
		frm.events.inject_styles(frm);
		frm.set_df_property("file_selection", "allowed_file_types", [".csv"]);
		frm.events.apply_import_defaults(frm);
		frm.set_df_property("importload", "label", __("Import"));
		frm.events.render_banner(frm);
		frm.events.render_last_import_badge(frm);
		frm.events.style_import_button(frm);
		frm.events.render_import_action_area(frm);
		frm.events.render_file_selection_area(frm);
		frm.events.toggle_preview_sections(frm);
		frm.events.render_faq(frm);
		frm.events.init_progress_subscription(frm);
		frm.events.restore_progress_from_doc(frm);
		frm.toggle_enable("file_selection", frm.doc.job_status !== "Completed");
		if (frm.doc.file_selection) {
			frm.toggle_enable(
				"importload",
				!ATIP_ACTIVE_STATUSES.has(frm.doc.job_status) && frm.doc.job_status !== "Completed"
			);
			// Don't re-queue preview if the doc already shows a preview failure
			// (progress_stage = "Preview failed"). The user must clear + re-upload.
			const isPreviewFailed = (frm.doc.progress_stage || "").startsWith("Preview failed");
			if (!isPreviewFailed) {
				frm.events.load_preview(frm, { quiet: true });
			}
		} else {
			frm.events.clear_preview(frm);
		}
		// Ensure form footer (activity / audit trail) is visible
		setTimeout(() => {
			frm.$wrapper.find(".form-footer").show();
			if (frm.footer && frm.footer.$wrapper) frm.footer.$wrapper.show();
			if (frm.timeline && typeof frm.timeline.refresh === "function") frm.timeline.refresh();
		}, 400);
	},

	onload_post_render(frm) {
		frm.events.init_progress_subscription(frm);
		frm.events.style_import_button(frm);
	},

	file_selection(frm) {
		if (frm._atip_attach_wrap) frm._atip_attach_wrap.toggleClass("has-file", Boolean(frm.doc.file_selection));
		if (frm.doc.file_selection) {
			const url = frm.doc.file_selection || "";
			const ext = url.split("?")[0].split(".").pop().toLowerCase();
			if (ext !== "csv") {
				frappe.msgprint({ title: __("Unsupported File"), message: __("Only .csv files are supported. Please export the Amazon report as CSV."), indicator: "red" });
				frm.set_value("file_selection", "");
				return;
			}
			frm.toggle_enable("importload", false);
			frm.events.show_loading(frm);
			if (frm.is_new() || frm.is_dirty()) {
				frm.save().then(() => frm.events.load_preview(frm));
			} else {
				frm.events.load_preview(frm);
			}
		} else {
			frm.events.clear_preview(frm);
		}
	},

	importload(frm) {
		if (frm.doc.job_status === "Completed") {
			frappe.msgprint({
				title: __("Already Imported"),
				message: __("This file has already been imported. Each import record can be processed only once. To re-import, create a new Import record."),
				indicator: "orange",
			});
			return;
		}
		frm.events._show_import_confirm(frm, () => frm.events.import_rows(frm));
	},

	add_download_template_button(frm) {
		frm.add_custom_button(__("Download Template"), () => {
			frm.events.download_template(frm);
		});
	},

	inject_styles(frm) {
		if (document.getElementById("atip-injected-styles")) return;
		const s = document.createElement("style");
		s.id = "atip-injected-styles";
		s.textContent = `
.atip-banner{display:flex;align-items:center;justify-content:space-between;padding:11px 16px;border-radius:10px;background:linear-gradient(135deg,#3730a3 0%,#4f46e5 55%,#6366f1 100%);color:#fff;box-shadow:0 3px 14px rgba(79,70,229,.22);gap:12px;flex-wrap:wrap;position:relative;overflow:hidden;margin-bottom:0;}
.atip-banner::before{content:'';position:absolute;top:-30px;right:-30px;width:100px;height:100px;border-radius:50%;background:rgba(255,255,255,.06);pointer-events:none;}
.atip-banner-left{display:flex;align-items:center;gap:11px;z-index:1;}
.atip-banner-icon{width:36px;height:36px;border-radius:9px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.atip-banner-icon svg{color:#fff;}
.atip-banner-title{font-size:15px;font-weight:700;letter-spacing:-.02em;line-height:1.2;}
.atip-banner-sub{font-size:11.5px;font-weight:400;color:rgba(255,255,255,.72);margin-top:2px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;}
.atip-banner-sub-chip{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.2);border-radius:20px;padding:1px 8px;font-size:10.5px;font-weight:600;}
.atip-banner-right{z-index:1;display:flex;align-items:center;gap:12px;}
.atip-banner-status{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:20px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;border:1.5px solid;white-space:nowrap;}
.atip-banner-status::before{content:'';width:6px;height:6px;border-radius:50%;background:currentColor;display:inline-block;}
.atip-banner-stats{display:flex;gap:14px;z-index:1;}
.atip-banner-stat{text-align:center;}
.atip-banner-stat-val{font-size:14px;font-weight:700;line-height:1;}
.atip-banner-stat-lbl{font-size:9.5px;font-weight:500;color:rgba(255,255,255,.6);margin-top:1px;}
.atip-banner-divider{width:1px;height:28px;background:rgba(255,255,255,.18);align-self:center;}

/* last-import footer inside banner */
.atip-banner-footer{display:flex;align-items:center;gap:8px;padding:7px 12px 0;border-top:1px solid rgba(255,255,255,.14);margin-top:8px;flex-wrap:wrap;width:100%;}
.atip-li-label{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:rgba(255,255,255,.5);white-space:nowrap;}
.atip-li-chip{display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:20px;font-size:10.5px;font-weight:600;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#fff;}
.atip-li-chip.ins{background:rgba(74,222,128,.15);border-color:rgba(74,222,128,.35);color:#86efac;}
.atip-li-chip.upd{background:rgba(147,197,253,.15);border-color:rgba(147,197,253,.35);color:#93c5fd;}
.atip-li-chip.skp{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.15);color:rgba(255,255,255,.6);}
.atip-li-chip.fld{background:rgba(248,113,113,.15);border-color:rgba(248,113,113,.35);color:#fca5a5;}
.atip-li-time{font-size:10px;color:rgba(255,255,255,.45);margin-left:auto;}
/* remove ALL frappe section borders & whitespace */
.layout-main-section .form-section{border:none !important;box-shadow:none !important;outline:none !important;}
.layout-main-section .section-body{border:none !important;box-shadow:none !important;padding-bottom:4px !important;}
.layout-main-section .section-head{border:none !important;border-bottom:none !important;box-shadow:none !important;margin-bottom:4px !important;padding-top:8px !important;}
.layout-main-section .section-head .indicator-pill{display:none !important;}
.page-form .form-section .section-body .form-column{border:none !important;box-shadow:none !important;}
.frappe-control[data-fieldtype="HTML"] .control-value,.frappe-control[data-fieldtype="HTML"]{border:none !important;box-shadow:none !important;padding:0 !important;}
.form-layout .row{margin-bottom:0 !important;}
.form-column{padding-bottom:2px !important;border:none !important;}
.layout-main-section{border:none !important;box-shadow:none !important;}
.page-form{border:none !important;box-shadow:none !important;}

/* import action */
.atip-action-wrap{background:#fafbff;border:1.5px solid #e0e7ff;border-radius:11px;padding:18px 16px 14px;text-align:center;margin-bottom:2px;}
.atip-action-wrap.has-file{border-color:#6366f1;background:#f5f3ff;}
.atip-action-wrap.already-imported{border-color:#bbf7d0;background:#f0fdf4;}
.atip-action-hint{font-size:11.5px;color:#6b7280;margin-bottom:14px;line-height:1.5;}
.atip-action-hint strong{color:#4f46e5;}
.atip-action-wrap.already-imported .atip-action-hint{color:#16a34a;font-weight:600;}
.atip-attach-wrap{background:#fafbff;border:1.5px solid #e0e7ff;border-radius:11px;padding:18px 16px 14px;text-align:center;margin-bottom:2px;display:flex;flex-direction:column;justify-content:center;}
.atip-attach-wrap.has-file{border-color:#6366f1;background:#f5f3ff;}
.atip-attach-wrap .btn-attach{background:#4f46e5;color:#fff;border:none;border-radius:6px;padding:7px 18px;font-size:13px;font-weight:600;cursor:pointer;}
.atip-attach-wrap .btn-attach:hover{background:#4338ca;}
.atip-attach-wrap .atip-attach-hint{font-size:11.5px;color:#6b7280;margin-bottom:14px;line-height:1.5;}
.atip-attach-wrap .control-label,.atip-attach-wrap .help-box{display:none!important;}
/* equal-height file upload row */
[data-fieldname="file_section"] .form-section>.form-column{display:flex;flex-direction:column;}
[data-fieldname="file_section"] .form-section>.form-column .atip-attach-wrap,
[data-fieldname="file_section"] .form-section>.form-column .atip-action-wrap{flex:1;}

/* button */
.atip-import-btn{display:inline-flex !important;align-items:center !important;justify-content:center !important;gap:7px !important;padding:9px 28px !important;font-size:13.5px !important;font-weight:700 !important;color:#fff !important;background:linear-gradient(135deg,#4f46e5,#6366f1) !important;border:none !important;border-radius:8px !important;box-shadow:0 3px 12px rgba(99,102,241,.35) !important;cursor:pointer !important;transition:all .18s ease !important;min-width:160px !important;}
.atip-import-btn:hover:not(:disabled){background:linear-gradient(135deg,#4338ca,#4f46e5) !important;box-shadow:0 5px 18px rgba(99,102,241,.45) !important;transform:translateY(-1px) !important;}
.atip-import-btn:disabled{background:#e5e7eb !important;color:#9ca3af !important;box-shadow:none !important;cursor:not-allowed !important;}

/* section labels — keep Frappe defaults */

/* preview summary — fixed 3-col grid (3×3) */
.atip-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px;}
@media(max-width:600px){.atip-summary{grid-template-columns:repeat(2,1fr);}}
.atip-sum-card{padding:10px 12px;border:1px solid #e0e7ff;border-radius:9px;background:#fff;box-shadow:0 1px 3px rgba(79,70,229,.06);}
.atip-sum-card-label{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#6366f1;margin-bottom:3px;}
.atip-sum-card-val{font-size:17px;font-weight:800;color:#1e1b4b;line-height:1.1;}
.atip-sum-card-val.warn{color:#dc2626;}
.atip-sum-card-val.ok{color:#16a34a;}
.atip-sum-msg{font-size:11px;color:#6b7280;margin-bottom:10px;padding:6px 10px;background:#f8faff;border-radius:7px;border:1px solid #e0e7ff;}
/* skeleton */
.atip-skeleton{background:linear-gradient(90deg,#f0f2ff 25%,#e8eaff 50%,#f0f2ff 75%);background-size:200% 100%;animation:atip-shimmer 1.4s infinite;border-radius:6px;}
@keyframes atip-shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.atip-skel-summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin-bottom:14px;}
.atip-skel-card{padding:10px 12px;border:1px solid #e8eaff;border-radius:9px;background:#f8faff;}
.atip-skel-lbl{height:8px;border-radius:4px;margin-bottom:8px;width:60%;}
.atip-skel-val{height:18px;border-radius:4px;width:40%;}
/* warnings */
.atip-warn-list{display:flex;flex-direction:column;gap:6px;}
.atip-warn-item{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border-radius:8px;font-size:12px;}
.atip-warn-item.error{background:#fef2f2;border:1px solid #fecaca;color:#991b1b;}
.atip-warn-item.warning{background:#fffbeb;border:1px solid #fde68a;color:#92400e;}
.atip-warn-item.info{background:#f0f9ff;border:1px solid #bae6fd;color:#075985;}

/* warnings/errors box (grouped, virtual-scrolled) */
.atip-warnbox{margin-top:10px;}
.atip-warn-summary{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;}
.atip-warn-chip{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:20px;font-size:11px;font-weight:700;border:1.5px solid;cursor:pointer;user-select:none;transition:all .15s ease;}
.atip-warn-chip.error{background:#fef2f2;border-color:#fecaca;color:#991b1b;}
.atip-warn-chip.warning{background:#fffbeb;border-color:#fde68a;color:#92400e;}
.atip-warn-chip.info{background:#f0f9ff;border-color:#bae6fd;color:#075985;}
.atip-warn-chip.active{box-shadow:0 0 0 2px rgba(0,0,0,.08) inset;transform:translateY(1px);}
.atip-warn-total{font-size:11px;color:#6b7280;margin-left:auto;}
.atip-warn-search{margin-bottom:10px;font-size:12.5px;}
.atip-warn-groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:8px;align-items:start;}
.atip-warn-group{border:1px solid #e5e7eb;border-radius:9px;overflow:hidden;background:#fff;}
.atip-warn-group-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 12px;background:#f8faff;user-select:none;}
.atip-warn-group-title{font-size:12.5px;font-weight:700;color:#1e1b4b;}
.atip-warn-group-meta{display:flex;align-items:center;gap:10px;}
.atip-warn-group-cnt{font-size:11px;font-weight:700;padding:2px 9px;border-radius:12px;background:#eef2ff;color:#4f46e5;}
.atip-warn-group-body{display:block;border-top:1px solid #f1f5f9;}
.atip-warn-empty{padding:14px;text-align:center;font-size:12px;color:#9ca3af;}
.atip-warn-vscroll-outer{width:100%;}
@media(max-width:900px){.atip-warn-groups{grid-template-columns:1fr;}}
.atip-warn-vscroll{overflow-y:auto;overflow-x:hidden;position:relative;}
.atip-warn-row-line{display:flex;align-items:center;gap:8px;height:28px;line-height:28px;padding:0 12px;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-bottom:1px solid #f8fafc;}
.atip-warn-row-line.error{color:#991b1b;background:#fef2f2;}
.atip-warn-row-line.warning{color:#92400e;background:#fffbeb;}
.atip-warn-row-line.info{color:#075985;background:#f0f9ff;}
.atip-warn-rowno{flex-shrink:0;font-weight:700;font-size:10.5px;padding:1px 7px;border-radius:10px;background:rgba(0,0,0,.06);}
.atip-warn-msg{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
@media(max-width:600px){.atip-warn-total{margin-left:0;width:100%;}.atip-warn-vscroll{height:220px !important;}}
/* progress panel */
.atip-prog-panel{border:1px solid #e0e7ff;border-radius:10px;padding:14px 16px;background:#fafbff;display:flex;flex-direction:column;gap:10px;margin-bottom:12px;}
.atip-prog-head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;}
.atip-prog-stage{font-weight:700;font-size:13.5px;color:#1e1b4b;}
.atip-prog-bar-wrap{width:100%;height:8px;background:#e5e7eb;border-radius:6px;overflow:hidden;}
.atip-prog-bar{height:100%;background:linear-gradient(90deg,#4f46e5,#6366f1);border-radius:6px;transition:width .3s ease;}
.atip-prog-bar.done{background:linear-gradient(90deg,#16a34a,#22c55e);}
.atip-prog-bar.fail{background:linear-gradient(90deg,#b91c1c,#ef4444);}
.atip-prog-meta{font-size:11.5px;color:#6b7280;display:flex;gap:14px;flex-wrap:wrap;}
.atip-prog-meta strong{color:#111827;}
.atip-prog-counters{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;}
.atip-prog-counter{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;}
.atip-prog-counter span{font-size:11px;color:#6b7280;}
.atip-prog-counter strong{font-size:15px;font-weight:700;}
.atip-cancel-btn{font-size:11px;padding:4px 12px;border-radius:6px;border:1px solid #fca5a5;background:#fff;color:#dc2626;cursor:pointer;font-weight:600;}
.atip-cancel-btn:hover{background:#fef2f2;}

/* ══ RESULT PANEL ══ */
.atip-result{border:1px solid #e5e7eb;border-left-width:4px;border-radius:12px;padding:clamp(14px,1.8vw,20px);margin-top:8px;background:#ffffff;}
.atip-result-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;gap:12px;flex-wrap:wrap;}
.atip-result-status{font-size:clamp(15px,1.7vw,19px);font-weight:700;}
.atip-result-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap;}
.atip-result-time{color:#6b7280;font-size:12px;}
.atip-result-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:18px;}
.atip-result-card{background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;gap:4px;}
.atip-result-card-label{color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;font-weight:600;}
.atip-result-card-val{font-size:clamp(18px,2vw,22px);font-weight:700;line-height:1.1;}
.atip-result-card-val.neutral{color:#111827;}
.atip-no-failures{color:#16a34a;font-weight:600;padding:12px;background:#f0fdf4;border-radius:8px;}
.atip-failures{border-top:1px solid #e5e7eb;padding-top:14px;}
.atip-failures-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px;}
.atip-failures-title{font-weight:700;color:#dc2626;font-size:14px;}
.atip-fail-table-wrap{border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;}
.atip-fail-table-scroll{overflow:auto;position:relative;}
.atip-fail-table{border-collapse:collapse;font-size:13px;}
.atip-fail-table thead{position:sticky;top:0;z-index:2;background:#f3f4f6;}
.atip-fail-table th{padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:600;color:#374151;font-size:12px;}
.atip-fail-table td{padding:6px 10px;border-bottom:1px solid #f1f5f9;vertical-align:top;font-size:12px;}
.atip-fail-table .atip-fail-msg{color:#4b5563;word-break:break-word;}
.atip-fail-badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;}
.atip-fail-badge.error{background:#fef2f2;color:#b91c1c;}
.atip-fail-badge.warning{background:#fffbeb;color:#b45309;}

@media(max-width:768px){.atip-banner{padding:9px 12px;}.atip-banner-title{font-size:13px;}.atip-banner-stats{display:none;}.atip-import-btn{min-width:120px !important;}.atip-prog-counters{grid-template-columns:1fr 1fr;}}

		/* ══ DARK MODE ══ */
		[data-theme="dark"] .atip-result { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-result-time { color: var(--text-muted, #8d99a6); }
		[data-theme="dark"] .atip-result-card { background: var(--subtle-accent, #1a1a2e); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-result-card-label { color: var(--text-muted, #8d99a6); }
		[data-theme="dark"] .atip-result-card-val.neutral { color: var(--text-color, #fff); }
		[data-theme="dark"] .atip-no-failures { background: rgba(22,163,74,.12); color: #4ade80; }
		[data-theme="dark"] .atip-failures { border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-failures-title { color: #f87171; }
		[data-theme="dark"] .atip-fail-table-wrap { border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-fail-table thead { background: var(--subtle-accent, #1a1a2e); }
		[data-theme="dark"] .atip-fail-table th { color: var(--text-color, #fff); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-fail-table td { color: var(--text-color, #fff); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-fail-table .atip-fail-msg { color: var(--text-muted, #c2c8d0); }
		[data-theme="dark"] .atip-fail-table tr:hover td { background: var(--subtle-accent, #1a1a2e); }
		[data-theme="dark"] .atip-fail-badge.error { background: rgba(220, 38, 38, .15); color: #f87171; }
		[data-theme="dark"] .atip-fail-badge.warning { background: rgba(180, 83, 9, .15); color: #fcd34d; }
		[data-theme="dark"] .atip-action-wrap { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-action-wrap.has-file { background: var(--subtle-accent, #1a1a2e); border-color: var(--primary, #6366f1); }
			[data-theme="dark"] .atip-action-wrap.already-imported { background: rgba(22,163,74,.12); border-color: #166534; }
			[data-theme="dark"] .atip-action-wrap.already-imported .atip-action-hint { color: #4ade80; }
		[data-theme="dark"] .atip-action-hint { color: var(--text-muted, #8d99a6); }
		[data-theme="dark"] .atip-attach-wrap { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-attach-wrap.has-file { background: var(--subtle-accent, #1a1a2e); border-color: var(--primary, #6366f1); }
		[data-theme="dark"] .atip-attach-hint { color: var(--text-muted, #8d99a6); }
		[data-theme="dark"] .atip-action-hint strong { color: var(--primary, #6366f1); }
		[data-theme="dark"] .atip-sum-card { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-sum-card-val { color: var(--text-color, #fff); }
		[data-theme="dark"] .atip-sum-msg { background: var(--subtle-accent, #1a1a2e); border-color: var(--border-color, #444); color: var(--text-muted, #8d99a6); }
		[data-theme="dark"] .atip-prog-panel { background: var(--subtle-accent, #1a1a2e); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-prog-stage { color: var(--text-color, #fff); }
		[data-theme="dark"] .atip-prog-meta { color: var(--text-muted, #8d99a6); }
		[data-theme="dark"] .atip-prog-meta strong { color: var(--text-color, #fff); }
		[data-theme="dark"] .atip-prog-counter { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
		[data-theme="dark"] .atip-prog-counter span { color: var(--text-muted, #8d99a6); }
		[data-theme="dark"] .atip-prog-counter strong { color: var(--text-color, #fff); }
		[data-theme="dark"] .atip-cancel-btn { background: transparent; border-color: #ef4444; color: #f87171; }
		[data-theme="dark"] .atip-cancel-btn:hover { background: rgba(239, 68, 68, .1); }
		[data-theme="dark"] .atip-sum-card-label { color: #6e78ff; }
		[data-theme="dark"] .atip-warn-item.error { background: rgba(220, 38, 38, .15); border-color: #7f1d1d; color: #f87171; }
		[data-theme="dark"] .atip-warn-item.warning { background: rgba(180, 83, 9, .15); border-color: #78350f; color: #fcd34d; }
		[data-theme="dark"] .atip-warn-item.info { background: rgba(30, 58, 138, .15); border-color: #1e3a5f; color: #93c5fd; }

			[data-theme="dark"] .atip-warn-chip.error { background: rgba(220, 38, 38, .15); border-color: #7f1d1d; color: #f87171; }
			[data-theme="dark"] .atip-warn-chip.warning { background: rgba(180, 83, 9, .15); border-color: #78350f; color: #fcd34d; }
			[data-theme="dark"] .atip-warn-chip.info { background: rgba(30, 58, 138, .15); border-color: #1e3a5f; color: #93c5fd; }
			[data-theme="dark"] .atip-warn-chip.active { box-shadow: 0 0 0 2px rgba(255,255,255,.15) inset; }
			[data-theme="dark"] .atip-warn-total { color: var(--text-muted, #8d99a6); }
			[data-theme="dark"] .atip-warn-group { background: var(--card-bg, #2d2d4d); border-color: var(--border-color, #444); }
			[data-theme="dark"] .atip-warn-group-head { background: var(--subtle-accent, #1a1a2e); }
			[data-theme="dark"] .atip-warn-group-title { color: var(--text-color, #fff); }
			[data-theme="dark"] .atip-warn-group-cnt { background: var(--subtle-accent, #1a1a2e); color: #8b8fff; }
			[data-theme="dark"] .atip-warn-group-body { border-color: var(--border-color, #444); }
			[data-theme="dark"] .atip-warn-empty { color: var(--text-muted, #8d99a6); }
			[data-theme="dark"] .atip-warn-row-line { border-color: rgba(255,255,255,.04); }
			[data-theme="dark"] .atip-warn-row-line.error { background: rgba(220, 38, 38, .12); color: #f87171; }
			[data-theme="dark"] .atip-warn-row-line.warning { background: rgba(180, 83, 9, .12); color: #fcd34d; }
			[data-theme="dark"] .atip-warn-row-line.info { background: rgba(30, 58, 138, .12); color: #93c5fd; }
			[data-theme="dark"] .atip-warn-rowno { background: rgba(255,255,255,.1); }

			/* ══ FAQ ══ */
			.atip-faq{margin-top:16px;border:1px solid #e0e7ff;border-radius:11px;background:#fff;overflow:hidden;}
			.atip-faq-head{display:flex;align-items:center;gap:10px;padding:12px 16px;background:linear-gradient(135deg,#f5f3ff,#eef2ff);border-bottom:1px solid #e0e7ff;cursor:pointer;user-select:none;}
			.atip-faq-head-icon{width:28px;height:28px;border-radius:8px;background:#fff;border:1px solid #e0e7ff;display:flex;align-items:center;justify-content:center;color:#6366f1;flex-shrink:0;}
			.atip-faq-head-title{font-size:13.5px;font-weight:700;color:#1e1b4b;flex:1;}
			.atip-faq-head-sub{font-size:11px;color:#6b7280;}
			.atip-faq-head-chev{transition:transform .2s ease;color:#6366f1;flex-shrink:0;}
			.atip-faq.open .atip-faq-head-chev{transform:rotate(180deg);}
			.atip-faq-body{display:none;padding:6px 16px 14px;}
			.atip-faq.open .atip-faq-body{display:block;}
			.atip-faq-item{border-bottom:1px solid #f1f5f9;}
			.atip-faq-item:last-child{border-bottom:none;}
			.atip-faq-q{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;text-align:left;background:none;border:none;padding:11px 4px;font-size:12.5px;font-weight:600;color:#1e1b4b;cursor:pointer;}
			.atip-faq-q:hover{color:#4f46e5;}
			.atip-faq-q .atip-faq-q-chev{transition:transform .2s ease;color:#9ca3af;flex-shrink:0;font-size:11px;}
			.atip-faq-item.open .atip-faq-q .atip-faq-q-chev{transform:rotate(180deg);color:#6366f1;}
			.atip-faq-a{display:none;padding:0 4px 13px;font-size:12px;line-height:1.65;color:#374151;}
			.atip-faq-item.open .atip-faq-a{display:block;}
			.atip-faq-a table{width:100%;border-collapse:collapse;margin:8px 0;font-size:11.5px;}
			.atip-faq-a th,.atip-faq-a td{border:1px solid #e5e7eb;padding:5px 8px;text-align:left;vertical-align:top;}
			.atip-faq-a th{background:#f8faff;font-weight:700;color:#4f46e5;}
			.atip-faq-a code{background:#f3f4f6;border-radius:4px;padding:1px 5px;font-size:11px;color:#be123c;}
			.atip-faq-a strong{color:#1e1b4b;}
			.atip-faq-a .ok{color:#16a34a;font-weight:700;}
			.atip-faq-a .bad{color:#dc2626;font-weight:700;}
			.atip-faq-a .atip-act-block{display:inline-block;background:#fee2e2;color:#991b1b;border:1px solid #fecaca;border-radius:8px;padding:1px 8px;font-size:10.5px;font-weight:700;white-space:nowrap;}
			.atip-faq-a .atip-act-skip{display:inline-block;background:#ffedd5;color:#9a3412;border:1px solid #fed7aa;border-radius:8px;padding:1px 8px;font-size:10.5px;font-weight:700;white-space:nowrap;}
			.atip-faq-a .atip-act-warn{display:inline-block;background:#fef9c3;color:#854d0e;border:1px solid #fde68a;border-radius:8px;padding:1px 8px;font-size:10.5px;font-weight:700;white-space:nowrap;}
			.atip-faq-a table.atip-val-table{table-layout:fixed;}
			.atip-faq-a table.atip-val-table th:nth-child(1),.atip-faq-a table.atip-val-table td:nth-child(1){width:44px;text-align:center;}
			.atip-faq-a table.atip-val-table th:nth-child(2),.atip-faq-a table.atip-val-table td:nth-child(2){width:auto;}
			.atip-faq-a table.atip-val-table th:nth-child(3),.atip-faq-a table.atip-val-table td:nth-child(3){width:110px;text-align:center;}
			.atip-faq-a ol,.atip-faq-a ul{margin:6px 0;padding-left:20px;}
			.atip-faq-a li{margin-bottom:3px;}
			@media(max-width:600px){.atip-faq-a{overflow-x:auto;}.atip-faq-a table{font-size:10.5px;}}

			[data-theme="dark"] .atip-faq{background:var(--card-bg,#2d2d4d);border-color:var(--border-color,#444);}
			[data-theme="dark"] .atip-faq-head{background:var(--subtle-accent,#1a1a2e);border-color:var(--border-color,#444);}
			[data-theme="dark"] .atip-faq-head-icon{background:var(--card-bg,#2d2d4d);border-color:var(--border-color,#444);color:#8b8fff;}
			[data-theme="dark"] .atip-faq-head-title{color:var(--text-color,#fff);}
			[data-theme="dark"] .atip-faq-head-sub{color:var(--text-muted,#8d99a6);}
			[data-theme="dark"] .atip-faq-item{border-color:var(--border-color,#444);}
			[data-theme="dark"] .atip-faq-q{color:var(--text-color,#fff);}
			[data-theme="dark"] .atip-faq-q:hover{color:#8b8fff;}
			[data-theme="dark"] .atip-faq-a{color:var(--text-muted,#c2c8d0);}
			[data-theme="dark"] .atip-faq-a th,[data-theme="dark"] .atip-faq-a td{border-color:var(--border-color,#444);}
			[data-theme="dark"] .atip-faq-a th{background:var(--subtle-accent,#1a1a2e);color:#8b8fff;}
			[data-theme="dark"] .atip-faq-a strong{color:var(--text-color,#fff);}
			[data-theme="dark"] .atip-faq-a code{background:var(--subtle-accent,#1a1a2e);color:#fca5a5;}

			/* ══ FORM FOOTER / ACTIVITY TRAIL ══ */
			.form-footer{display:block !important;margin-top:20px;}
			.form-footer .timeline-wrapper{display:block !important;}
			.form-footer .timeline-head{display:flex !important;}

			/* ══ IMPORT CONFIRMATION DIALOG ══ */
			.atip-confirm-body{padding:4px 0 8px;}
			.atip-confirm-intro{font-size:13.5px;color:#374151;margin-bottom:14px;line-height:1.6;}
			.atip-confirm-intro strong{color:#1e1b4b;}
			.atip-confirm-stats{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;}
			.atip-confirm-stat{flex:1;min-width:90px;padding:12px 10px;border-radius:10px;text-align:center;border:1.5px solid;}
			.atip-confirm-stat-ok{background:#f0fdf4;border-color:#bbf7d0;}
			.atip-confirm-stat-err{background:#fef2f2;border-color:#fecaca;}
			.atip-confirm-stat-warn{background:#fffbeb;border-color:#fde68a;}
			.atip-confirm-stat-skip{background:#f9fafb;border-color:#e5e7eb;}
			.atip-confirm-stat-val{font-size:26px;font-weight:800;line-height:1.1;}
			.atip-confirm-stat-ok .atip-confirm-stat-val{color:#16a34a;}
			.atip-confirm-stat-err .atip-confirm-stat-val{color:#dc2626;}
			.atip-confirm-stat-warn .atip-confirm-stat-val{color:#b45309;}
			.atip-confirm-stat-skip .atip-confirm-stat-val{color:#6b7280;}
			.atip-confirm-stat-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-top:4px;color:#6b7280;}
			.atip-confirm-section{border-radius:9px;margin-bottom:10px;overflow:hidden;}
			.atip-confirm-section-error{border:1.5px solid #fecaca;}
			.atip-confirm-section-warn{border:1.5px solid #fde68a;}
			.atip-confirm-section-head{padding:8px 12px;font-size:12px;font-weight:700;letter-spacing:.01em;}
			.atip-confirm-section-error .atip-confirm-section-head{background:#fef2f2;color:#991b1b;}
			.atip-confirm-section-warn .atip-confirm-section-head{background:#fffbeb;color:#92400e;}
			.atip-confirm-section-list{background:#fff;padding:2px 0;}
			.atip-confirm-item{padding:5px 12px;font-size:12px;line-height:1.5;border-bottom:1px solid #f9fafb;}
			.atip-confirm-item:last-child{border-bottom:none;}
			.atip-confirm-item.error{color:#7f1d1d;}
			.atip-confirm-item.warning{color:#78350f;}
			.atip-confirm-more{padding:5px 12px;font-size:11px;font-style:italic;color:#9ca3af;background:#f9fafb;}
			.atip-confirm-clean{padding:12px 14px;background:#f0fdf4;border:1.5px solid #bbf7d0;border-radius:9px;color:#16a34a;font-weight:600;font-size:13px;display:flex;align-items:center;gap:8px;}
			@media(max-width:600px){.atip-confirm-stats{flex-direction:column;}}
			[data-theme="dark"] .atip-confirm-stat-ok{background:rgba(22,163,74,.1);border-color:#166534;}
			[data-theme="dark"] .atip-confirm-stat-err{background:rgba(220,38,38,.1);border-color:#7f1d1d;}
			[data-theme="dark"] .atip-confirm-stat-warn{background:rgba(180,83,9,.1);border-color:#78350f;}
			[data-theme="dark"] .atip-confirm-stat-skip{background:var(--card-bg,#2d2d4d);border-color:var(--border-color,#444);}
			[data-theme="dark"] .atip-confirm-stat-lbl{color:var(--text-muted,#8d99a6);}
			[data-theme="dark"] .atip-confirm-section-error{border-color:#7f1d1d;}
			[data-theme="dark"] .atip-confirm-section-warn{border-color:#78350f;}
			[data-theme="dark"] .atip-confirm-section-error .atip-confirm-section-head{background:rgba(220,38,38,.15);color:#f87171;}
			[data-theme="dark"] .atip-confirm-section-warn .atip-confirm-section-head{background:rgba(180,83,9,.15);color:#fcd34d;}
			[data-theme="dark"] .atip-confirm-section-list{background:var(--card-bg,#2d2d4d);}
			[data-theme="dark"] .atip-confirm-item.error{color:#f87171;}
			[data-theme="dark"] .atip-confirm-item.warning{color:#fcd34d;}
			[data-theme="dark"] .atip-confirm-more{background:var(--subtle-accent,#1a1a2e);color:var(--text-muted,#8d99a6);}
			[data-theme="dark"] .atip-confirm-clean{background:rgba(22,163,74,.1);border-color:#166534;color:#4ade80;}
			[data-theme="dark"] .atip-confirm-intro{color:var(--text-muted,#c2c8d0);}
			[data-theme="dark"] .atip-confirm-intro strong{color:var(--text-color,#fff);}
		`;

		document.head.appendChild(s);
	},

	render_import_action_area(frm) {
		const fd = frm.fields_dict.importload;
		if (!fd || !fd.$wrapper) return;
		const $col = fd.$wrapper.closest(".form-column");

		let $wrap = $col.find(".atip-action-wrap");
		if (!$wrap.length) {
			$wrap = $(`<div class="atip-action-wrap"><div class="atip-action-hint"></div></div>`);
			$col.prepend($wrap);
			$wrap.append(fd.$wrapper);
		}
		frm._atip_action_wrap = $wrap;
		frm.events.update_import_action_state(frm);
	},

	update_import_action_state(frm) {
		const $wrap = frm._atip_action_wrap;
		if (!$wrap || !$wrap.length) return;

		const hasFile = Boolean(frm.doc.file_selection);
		const status = frm.doc.job_status;
		let hint;
		if (status === "Completed") {
			hint = __("This file has already been imported. Each import record can be processed only once.");
		} else if (hasFile) {
			hint = __("File validated. Click <strong>Start Import</strong> to begin processing.");
		} else {
			hint = __("Select a CSV file above, then click <strong>Start Import</strong>.");
		}

		$wrap.find(".atip-action-hint").html(hint);
		$wrap.toggleClass("has-file", hasFile);
		$wrap.toggleClass("already-imported", status === "Completed");
	},

	render_file_selection_area(frm) {
		const fd = frm.fields_dict.file_selection;
		if (!fd || !fd.$wrapper) return;
		const $col = fd.$wrapper.closest(".form-column");
		if (!$col.length) return;

		let $wrap = $col.find(".atip-attach-wrap");
		if (!$wrap.length) {
			$wrap = $(`<div class="atip-attach-wrap">
				<div class="atip-attach-hint">Only <strong>.csv</strong> files are supported. Select your  CSV file.</div>
			</div>`);
			$col.prepend($wrap);
			$wrap.append(fd.$wrapper);
		}
		$wrap.toggleClass("has-file", Boolean(frm.doc.file_selection));
		frm._atip_attach_wrap = $wrap;

		// Rename the attach button and hide redundant label
		setTimeout(() => {
			fd.$wrapper.find(".btn-attach").text(__("Attach File"));
			fd.$wrapper.find(".control-label").hide();
		}, 100);
	},

	render_last_import_badge(frm) {
		const status = frm.doc.job_status;
		const $banner = frm.get_field("import_banner_html").$wrapper.find(".atip-banner");
		$banner.find(".atip-banner-footer").remove();
		if (!ATIP_TERMINAL_STATUSES.has(status)) return;
		const fmt = (n) => Number(n || 0).toLocaleString("en-IN");
		const ins = fmt(frm.doc.inserted_count);
		const upd = fmt(frm.doc.updated_count);
		const skp = fmt(frm.doc.skipped_count);
		const fld = fmt(frm.doc.failed_count);
		const fin = frm.doc.finished_at ? frappe.datetime.str_to_user(frm.doc.finished_at.split(" ")[0]) : "";
		$banner.append(`
			<div class="atip-banner-footer">
				<span class="atip-li-label">Last Import</span>
				<span class="atip-li-chip ins">✓ ${ins} Ins</span>
				<span class="atip-li-chip upd">↑ ${upd} Upd</span>
				<span class="atip-li-chip skp">— ${skp} Skp</span>
				${Number(frm.doc.failed_count||0) > 0 ? `<span class="atip-li-chip fld">✕ ${fld} Fail</span>` : ""}
				${fin ? `<span class="atip-li-time">${fin}</span>` : ""}
			</div>
		`);
	},

	apply_import_defaults(frm) {
		const updates = {};

		if (!frm.doc.import_date) {
			updates.import_date = frappe.datetime.get_today();
		}

		if (!frm.doc.import_by) {
			updates.import_by = frappe.session.user_fullname || frappe.session.user;
		}

		if (Object.keys(updates).length) {
			frm.set_value(updates);
		}
	},

	render_banner(frm) {
		const wrapper = frm.get_field("import_banner_html").$wrapper;
		const importNo = frappe.utils.escape_html(frm.doc.name || __("New Import"));
		const importDate = frm.doc.import_date
			? frappe.datetime.str_to_user(frm.doc.import_date)
			: __("Today");
		// import_type field removed
		const status = frm.doc.job_status || "Draft";
		const importBy = frappe.utils.escape_html(frm.doc.import_by || frappe.session.user_fullname || "—");

		const statusMeta = {
			Draft:      { bg: "rgba(255,255,255,0.15)", border: "rgba(255,255,255,0.3)",  text: "#fff",     icon: "○" },
			Queued:     { bg: "rgba(251,191,36,0.2)",   border: "rgba(251,191,36,0.5)",   text: "#fef3c7",  icon: "⏳" },
			Previewing: { bg: "rgba(96,165,250,0.2)",   border: "rgba(96,165,250,0.5)",   text: "#dbeafe",  icon: "👁" },
			Running:    { bg: "rgba(251,191,36,0.2)",   border: "rgba(251,191,36,0.5)",   text: "#fef3c7",  icon: "▶" },
			Completed:  { bg: "rgba(74,222,128,0.22)",  border: "rgba(74,222,128,0.55)",  text: "#dcfce7",  icon: "✓" },
			Failed:     { bg: "rgba(248,113,113,0.22)", border: "rgba(248,113,113,0.55)", text: "#fecaca",  icon: "✕" },
			Cancelled:  { bg: "rgba(251,191,36,0.2)",   border: "rgba(251,191,36,0.5)",   text: "#fef3c7",  icon: "⊘" },
		};
		const sc = statusMeta[status] || statusMeta.Draft;

		const statsHtml = "";

		wrapper.html(`
			<div class="atip-banner">
				<div class="atip-banner-left">
					<div class="atip-banner-icon">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
							<polyline points="14 2 14 8 20 8"/>
							<line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>
						</svg>
					</div>
					<div>
						<div class="atip-banner-title">${importNo}</div>
						<div class="atip-banner-sub">
							<span>${importDate}</span>
							<span>by ${importBy}</span>
						</div>
					</div>
				</div>
				<div class="atip-banner-right">
					${statsHtml}
					<span class="atip-banner-status" style="background:${sc.bg};border-color:${sc.border};color:${sc.text};">
						${frappe.utils.escape_html(status)}
					</span>
				</div>
			</div>
		`);
	},

	style_import_button(frm) {
		const $btn = frm.fields_dict.importload && frm.fields_dict.importload.$input;
		if (!$btn || !$btn.length) return;
		$btn.addClass("atip-import-btn");
		$btn.html(`
			<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
				<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
				<polyline points="17 8 12 3 7 8"/>
				<line x1="12" y1="3" x2="12" y2="15"/>
			</svg>
			${__("Start Import")}
		`);
	},

	download_template(frm) {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "File",
				filters: [
					["File", "is_folder", "=", 0],
					["File", "file_name", "like", `${AMAZON_IMPORT_TEMPLATE_PREFIX}%`],
				],
				fields: ["name", "file_name", "file_url"],
				order_by: "creation desc",
				limit_page_length: 1,
			},
			freeze: true,
			freeze_message: __("Preparing template download..."),
			callback: (r) => {
				const template = (r.message || [])[0];

				if (!template || !template.file_url) {
					frappe.msgprint({
						title: __("Template Not Found"),
						indicator: "orange",
						message: __(
							"Could not find a template file whose name starts with {0}.",
							[`<strong>${frappe.utils.escape_html(AMAZON_IMPORT_TEMPLATE_PREFIX)}</strong>`]
						),
					});
					return;
				}

				const link = document.createElement("a");
				link.href = frappe.urllib.get_full_url(template.file_url);
				link.download = template.file_name || "";
				link.target = "_blank";
				link.rel = "noopener";
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
			},
		});
	},

	toggle_preview_sections(frm) {
		const has_file = Boolean(frm.doc.file_selection);
		frm.toggle_display("preview_section", true);
		frm.toggle_display("preview_summary_html", has_file);
		frm.toggle_display("preview_html", has_file);
		frm.toggle_display("preview_warnings_html", has_file);
		frm.toggle_display("preview_faq_html", true);
	},

	clear_preview(frm) {
		frm.events.toggle_preview_sections(frm);
		frm.toggle_enable("importload", false);
		frm.get_field("preview_summary_html").$wrapper.empty();
		frm.get_field("preview_html").$wrapper.empty();
		frm.get_field("preview_warnings_html").$wrapper.empty();
		frm.amazon_trip_preview_result = null;

		if (frm.amazon_trip_preview_datatable) {
			try { frm.amazon_trip_preview_datatable.destroy(); } catch(e) {}
			frm.amazon_trip_preview_datatable = null;
		}
	},

	show_loading(frm) {
		frm.events.toggle_preview_sections(frm);
		frm.toggle_enable("importload", false);
		// instant skeleton — 5 placeholder cards
		const skelCards = Array(5).fill(0).map(() => `
			<div class="atip-skel-card">
				<div class="atip-skel-lbl atip-skeleton"></div>
				<div class="atip-skel-val atip-skeleton"></div>
			</div>`).join("");
		frm.get_field("preview_summary_html").$wrapper.html(
			`<div class="atip-skel-summary">${skelCards}</div>`
		);
		frm.get_field("preview_html").$wrapper.html(
			`<div class="atip-skel-summary">${Array(3).fill(0).map(() => `<div class="atip-skel-card" style="height:32px;"><div class="atip-skel-lbl atip-skeleton" style="width:80%;height:100%;margin:0;"></div></div>`).join("")}</div>`
		);
		frm.get_field("preview_warnings_html").$wrapper.empty();
	},

	load_preview(frm, { quiet = false } = {}) {
		if (!frm.doc.file_selection) {
			if (!quiet) {
				frappe.msgprint(__("Please select a CSV file first."));
			}
			frm.events.clear_preview(frm);
			return;
		}

		frm.events.show_loading(frm);
		frappe.call({
			method: "logicore.logicore.doctype.amazon_trip___import.amazon_trip___import.get_import_preview",
			args: {
				docname: frm.is_new() ? null : frm.doc.name,
				file_url: frm.doc.file_selection,
			},
			callback: (r) => {
				const resp = r.message || {};
				if (resp.status === "ready" && resp.preview) {
					frm.events._render_preview(frm, resp.preview);
					return;
				}
				if (resp.status === "queued" || resp.status === "loading") {
					frm.events.render_live_progress(frm, {
						stage: __("Preparing preview…"),
						current: 0,
						total: 0,
					});
					frm.events.start_status_fallback_poll(frm);
					return;
				}
				if (resp.status === "empty") {
					frm.events.clear_preview(frm);
					return;
				}
				frm.events._render_preview(frm, resp);
			},
			error: () => {
				frm.amazon_trip_preview_result = null;
				frm.toggle_enable("importload", false);
				frm.events.render_summary(frm, {}, {});
				frm.events.render_warnings(frm, [
					{ level: "error", message: __("Unable to load preview for the selected file.") },
				]);
				frm.get_field("preview_html").$wrapper.html("");
			},
		});
	},

	_render_preview(frm, preview) {
		frm.amazon_trip_preview_result = preview;
		frm.toggle_enable("importload", Boolean(preview.can_import));
		frm.events.render_summary(frm, preview.summary || {}, preview);
		frm.events.render_preview_table(frm, preview);
		frm.events.render_warnings(frm, preview.warnings || []);
	},

	fetch_cached_preview(frm) {
		frappe.call({
			method: "logicore.logicore.doctype.amazon_trip___import.amazon_trip___import.get_cached_preview",
			args: { docname: frm.doc.name, file_url: frm.doc.file_selection },
			callback: (r) => {
				const resp = r.message || {};
				if (resp.status === "ready" && resp.preview) {
					frm.events._render_preview(frm, resp.preview);
					frm.get_field("live_progress_html").$wrapper.empty();
				}
			},
		});
	},

	render_summary(frm, summary, preview) {
		const fileType = frappe.utils.escape_html(summary.file_type || __("Unknown"));
		const totalRows = Number(summary.total_rows || 0);
		const detectedColumns = Number(summary.detected_columns || 0);
		const mappedColumns = Number(summary.mapped_columns || 0);
		const unknownColumns = Number(summary.unknown_columns || 0);
		const importableRows = Number(summary.importable_rows || 0);
		const failedRows = Number(summary.failed_rows || 0);
		const skippedRows = Number(summary.skipped_rows || 0);
		const newRows = Number(summary.new_rows || 0);
		const existingRows = Number(summary.existing_rows || 0);

		const card = (label, val, cls = "") =>
			`<div class="atip-sum-card"><div class="atip-sum-card-label">${label}</div><div class="atip-sum-card-val ${cls}">${val}</div></div>`;

		frm.get_field("preview_summary_html").$wrapper.html(`
			<div class="atip-summary">
				${card(__("File Type"), fileType)}
				${card(__("Total Rows"), totalRows.toLocaleString("en-IN"))}
				${card(__("Detected Cols"), detectedColumns)}
				${card(__("Mapped Cols"), mappedColumns, "ok")}
				${card(__("Unknown Cols"), unknownColumns, unknownColumns > 0 ? "warn" : "")}
				${card(__("New"), newRows.toLocaleString("en-IN"), "ok")}
				${card(__("Existing"), existingRows.toLocaleString("en-IN"))}
				${card(__("Importable"), importableRows.toLocaleString("en-IN"), "ok")}
				${card(__("Skipped (Blank)"), skippedRows.toLocaleString("en-IN"), skippedRows > 0 ? "warn" : "")}
				${card(__("Errors"), failedRows, failedRows > 0 ? "warn" : "")}
			</div>
		`);
	},

	render_preview_table(frm, preview) {
		const wrapper = frm.get_field("preview_html").$wrapper;
		wrapper.empty();

		if (!preview.data || !preview.data.length) {
			wrapper.html(`<div class="text-muted small">${__("No preview rows available.")}</div>`);
			return;
		}

		const columns = preview.columns || [];
		const data = preview.data;
		const totalRows = preview.total_number_of_rows || data.length;
		const esc = (v) => frappe.utils.escape_html(v == null ? "" : String(v));

		// --- Virtual scroll constants ---
		const ROW_H = 32;       // px per row
		const VIEW_H = 440;     // visible container height
		const BUFFER = 15;      // extra rows above/below viewport

		// Build header HTML (once)
		const theadHtml = `<thead style="position:sticky;top:0;z-index:2;background:#f3f4f6;">
			<tr>
				<th style="width:44px;min-width:44px;text-align:center;padding:6px 4px;font-size:11px;border-right:1px solid #e5e7eb;">#</th>
				${columns.map(c => `<th style="padding:6px 10px;font-size:11px;white-space:nowrap;border-right:1px solid #e5e7eb;">${esc(c.name || c.id)}</th>`).join("")}
			</tr>
		</thead>`;

		// Find the Action column index (first column with id "import_action")
		const actionColIdx = columns.findIndex(c => c && c.id === "import_action");

		// Row renderer — returns HTML string for one row
		const renderRow = (row, ri) => {
			// Determine row status from the Action cell
			const actionVal = actionColIdx >= 0 ? String(row[actionColIdx] || "") : "";
			const isError = /error/i.test(actionVal);
			const isCreate = /create new/i.test(actionVal);
			const isUpdate = /update existing/i.test(actionVal);

			const cells = row.map((cell, ci) => {
				const col = columns[ci] || {};
				let val = esc(cell);

				// Action column — render as a coloured pill
				if (col.id === "import_action" && val) {
					let pillBg = "#e0e7ff", pillColor = "#3730a3", pillBorder = "#c7d2fe";
					if (isError)  { pillBg = "#fee2e2"; pillColor = "#991b1b"; pillBorder = "#fecaca"; }
					else if (isCreate) { pillBg = "#dcfce7"; pillColor = "#166534"; pillBorder = "#bbf7d0"; }
					else if (isUpdate) { pillBg = "#dbeafe"; pillColor = "#1e40af"; pillBorder = "#bfdbfe"; }
					val = `<span style="background:${pillBg};color:${pillColor};border:1px solid ${pillBorder};border-radius:10px;padding:2px 9px;font-size:10.5px;font-weight:700;white-space:nowrap;">${val}</span>`;
				}
				if (col.id === "changed_fields" && val) {
					val = `<span style="background:#fff6db;border-left:3px solid #f0b429;border-radius:4px;padding:2px 6px;font-size:11px;">${val}</span>`;
				}
				// Date fields — display as DD-MM-YYYY (stored as YYYY-MM-DD from Python)
				if (col.fieldtype === "Date" && cell && /^\d{4}-\d{2}-\d{2}$/.test(String(cell))) {
					const [y, m, d] = String(cell).split("-");
					val = `${d}-${m}-${y}`;
				}
				return `<td style="padding:4px 10px;border-right:1px solid #f1f5f9;white-space:nowrap;">${val}</td>`;
			}).join("");

			// Row-level background tint for errors
			let bg = ri % 2 === 0 ? "" : "background:#fafafa;";
			let leftBar = "";
			if (isError) {
				bg = "background:#fef2f2;";
				leftBar = "box-shadow:inset 3px 0 0 #ef4444;";
			}
			return `<tr style="${bg}${leftBar}"><td style="text-align:center;color:#9ca3af;font-size:11px;padding:4px;border-right:1px solid #e5e7eb;">${ri + 1}</td>${cells}</tr>`;
		};

		const countMsg = `<div class="atip-sum-msg" style="margin-top:6px;margin-bottom:0;">${
			__("{0} rows total.", [data.length.toLocaleString("en-IN")])
		}</div>`;

		// Build container
		const $outer = $(`<div style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">`);
		const $scroll = $(`<div style="height:${VIEW_H}px;overflow:auto;position:relative;">`).appendTo($outer);
		const $spacer = $(`<div style="height:${data.length * ROW_H}px;position:relative;">`).appendTo($scroll);
		const $table  = $(`<table style="position:absolute;width:max-content;min-width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed;">`).appendTo($spacer);
		$table.append(theadHtml);
		const $tbody  = $('<tbody>').appendTo($table);

		let lastStart = -1;

		const paint = (scrollTop) => {
			const startIdx = Math.max(0, Math.floor(scrollTop / ROW_H) - BUFFER);
			const endIdx   = Math.min(data.length, startIdx + Math.ceil(VIEW_H / ROW_H) + BUFFER * 2);
			if (startIdx === lastStart) return;
			lastStart = startIdx;
			$tbody.html(data.slice(startIdx, endIdx).map((row, i) => renderRow(row, startIdx + i)).join(""));
			$table.css("top", startIdx * ROW_H + "px");
		};

		$scroll.on("scroll", (e) => paint(e.target.scrollTop));
		paint(0); // initial render

		wrapper.empty();
		wrapper.append($outer);
		wrapper.append(countMsg);
	},

	render_warnings(frm, warnings) {
		const wrapper = frm.get_field("preview_warnings_html").$wrapper;
		wrapper.empty();
		if (!warnings || !warnings.length) return;

		const esc = (v) => frappe.utils.escape_html(v == null ? "" : String(v));

		// Normalize + categorize
		const norm = warnings.map((w) => ({
			lvl: w.level === "error" ? "error" : w.level === "warning" ? "warning" : "info",
			row: w.row || "",
			message: w.message || "",
		}));

		const counts = { error: 0, warning: 0, info: 0 };
		const groupsMap = {};
		const groupOrder = [];
		const addToGroup = (key, label, item) => {
			if (!groupsMap[key]) {
				groupsMap[key] = { label, items: [] };
				groupOrder.push(key);
			}
			groupsMap[key].items.push(item);
		};

		norm.forEach((w) => {
			counts[w.lvl]++;
			if (/^Unknown column:/i.test(w.message)) {
				addToGroup("unknown_columns", __("Unknown Columns"), w);
			} else if (w.row) {
				addToGroup("row_issues", __("Row-level Issues"), w);
			} else {
				addToGroup("general", __("General"), w);
			}
		});

		// Preferred display order
		const preferredOrder = ["row_issues", "unknown_columns", "general"];
		const orderedKeys = preferredOrder.filter((k) => groupsMap[k]).concat(groupOrder.filter((k) => !preferredOrder.includes(k)));

		const chip = (lvl, label) => {
			const n = counts[lvl];
			if (!n) return "";
			return `<span class="atip-warn-chip ${lvl}" data-lvl="${lvl}">${n.toLocaleString("en-IN")} ${label}</span>`;
		};

		const summaryHtml = `
			<div class="atip-warn-summary">
				${chip("error", __("Errors"))}
				${chip("warning", __("Warnings"))}
				${chip("info", __("Info"))}
				<span class="atip-warn-total">${__("{0} total issue(s) — all rows & columns shown, nothing skipped", [norm.length.toLocaleString("en-IN")])}</span>
			</div>
			<input type="text" class="atip-warn-search form-control" placeholder="${__('Search in errors / warnings…')}" />
		`;

		const groupsHtml = orderedKeys.map((key) => {
			const g = groupsMap[key];
			return `
				<div class="atip-warn-group open" data-key="${key}">
					<div class="atip-warn-group-head">
						<span class="atip-warn-group-title">${g.label}</span>
						<span class="atip-warn-group-meta">
							<span class="atip-warn-group-cnt">${g.items.length.toLocaleString("en-IN")}</span>
						</span>
					</div>
					<div class="atip-warn-group-body">
						<div class="atip-warn-empty" style="display:none;">${__("No matching items.")}</div>
						<div class="atip-warn-vscroll-host"></div>
					</div>
				</div>
			`;
		}).join("");

		wrapper.html(`<div class="atip-warnbox">${summaryHtml}<div class="atip-warn-groups">${groupsHtml}</div></div>`);

		// wire a virtual-scroll list per group
		const groupApis = {};
		orderedKeys.forEach((key) => {
			const $group = wrapper.find(`.atip-warn-group[data-key="${key}"]`);
			const $host = $group.find(".atip-warn-vscroll-host");
			groupApis[key] = frm.events._wire_warning_vscroll($host, groupsMap[key].items, esc);
		});

		const updateGroupCount = (key, n) => {
			wrapper.find(`.atip-warn-group[data-key="${key}"] .atip-warn-group-cnt`).text(n.toLocaleString("en-IN"));
			wrapper.find(`.atip-warn-group[data-key="${key}"] .atip-warn-empty`).toggle(n === 0);
			wrapper.find(`.atip-warn-group[data-key="${key}"] .atip-warn-vscroll-host`).toggle(n > 0);
		};

		const applyFilters = () => {
			const q = wrapper.find(".atip-warn-search").val().toLowerCase().trim();
			const activeLvls = wrapper.find(".atip-warn-chip.active").map((_, el) => $(el).data("lvl")).get();

			orderedKeys.forEach((key) => {
				const all = groupsMap[key].items;
				const filtered = all.filter((w) => {
					if (activeLvls.length && !activeLvls.includes(w.lvl)) return false;
					if (q) {
						const hay = `${w.row ? `row ${w.row}` : ""} ${w.message}`.toLowerCase();
						if (!hay.includes(q)) return false;
					}
					return true;
				});
				groupApis[key].setItems(filtered);
				updateGroupCount(key, filtered.length);
			});
		};

		wrapper.find(".atip-warn-chip").on("click", function () {
			$(this).toggleClass("active");
			applyFilters();
		});
		wrapper.find(".atip-warn-search").on("input", () => applyFilters());
	},

	_wire_warning_vscroll($host, items, esc) {
		const ROW_H = 28;
		const VIEW_H = 360;
		const BUFFER = 15;

		let data = items;

		const $outer = $(`<div class="atip-warn-vscroll-outer">`).appendTo($host);
		const $scroll = $(`<div class="atip-warn-vscroll" style="height:${VIEW_H}px;">`).appendTo($outer);
		const $spacer = $(`<div style="position:relative;">`).appendTo($scroll);
		const $list = $(`<div style="position:absolute;left:0;right:0;">`).appendTo($spacer);

		const renderRow = (w) => {
			const rowBadge = w.row ? `<span class="atip-warn-rowno">${__("Row")} ${esc(w.row)}</span>` : "";
			return `<div class="atip-warn-row-line ${w.lvl}" title="${esc((w.row ? `Row ${w.row}: ` : "") + w.message)}">${rowBadge}<span class="atip-warn-msg">${esc(w.message)}</span></div>`;
		};

		let lastStart = -1;
		const paint = (scrollTop) => {
			const startIdx = Math.max(0, Math.floor(scrollTop / ROW_H) - BUFFER);
			const endIdx = Math.min(data.length, startIdx + Math.ceil(VIEW_H / ROW_H) + BUFFER * 2);
			if (startIdx === lastStart) return;
			lastStart = startIdx;
			$list.html(data.slice(startIdx, endIdx).map(renderRow).join(""));
			$list.css("top", startIdx * ROW_H + "px");
		};

		$scroll.on("scroll", (e) => paint(e.target.scrollTop));

		const setItems = (newItems) => {
			data = newItems;
			$spacer.css("height", data.length * ROW_H + "px");
			lastStart = -1;
			$scroll.scrollTop(0);
			paint(0);
		};

		setItems(items);
		return { setItems };
	},

	render_faq(frm) {
		const wrapper = frm.get_field("preview_faq_html").$wrapper;
		if (!wrapper) return;

		const faqs = [
			{
				q: __("Q1. What validations does the import run?"),
				a: `
					<p>${__("Each validation has one of two outcomes")}:</p>
					<ul style="margin:4px 0 12px;">
						<li><span style="background:#fee2e2;color:#991b1b;border:1px solid #fecaca;border-radius:8px;padding:1px 8px;font-size:11px;font-weight:700;">${__("BLOCK")}</span> — ${__("entire import stops, nothing is saved until the error is fixed")}</li>
						<li><span style="background:#fef9c3;color:#854d0e;border:1px solid #fde68a;border-radius:8px;padding:1px 8px;font-size:11px;font-weight:700;">${__("WARN")}</span> — ${__("row is imported, a warning is shown for review")}</li>
					</ul>
					<p><strong>${__("Blocking (File-level) — import stops entirely:")}</strong></p>
					<table class="atip-val-table">
						<tr><th>#</th><th>${__("Validation")}</th><th>${__("Action")}</th></tr>
						<tr><td>1</td><td>${__("File format is not .csv")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
						<tr><td>2</td><td>${__("File is empty or has no data rows")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
						<tr><td>3</td><td>${__("'Tour ID' header column not found in file")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
					</table>
					<p><strong>${__("Blocking (Group-level) — if ANY Tour ID group has these, the whole import is blocked until fixed:")}</strong></p>
					<table class="atip-val-table">
						<tr><th>#</th><th>${__("Validation")}</th><th>${__("Action")}</th></tr>
						<tr><td>4</td><td>${__("Tour ID value is blank in a row")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
						<tr><td>5</td><td>${__("Tour ID does not already exist in Amazon Trip (this import is update-only)")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
						<tr><td>6</td><td>${__("Existing Amazon Trip is missing mandatory Trip Date")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
						<tr><td>7</td><td>${__("Same VR ID appears under two different Tour IDs in the file")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
						<tr><td>8</td><td>${__("VR ID already belongs to another Amazon Trip in the system")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
						<tr><td>9</td><td>${__("Same VR ID repeated within one Tour ID group")}</td><td><span class="atip-act-block">${__("BLOCK")}</span></td></tr>
					</table>
					<p style="margin-top:6px;"><strong>${__("Note")}:</strong> ${__("A VR ID is globally unique — it can belong to only ONE Amazon Trip / Tour ID. This is enforced both on import and on manual entry in the Amazon Trip form.")}</p>
					<p><strong>${__("Row-level Warnings — row is imported, warning is shown:")}</strong></p>
					<table class="atip-val-table">
						<tr><th>#</th><th>${__("Validation")}</th><th>${__("Action")}</th></tr>
						<tr><td>20</td><td>${__("Start Date has invalid format (expected: MM/DD/YYYY HH:MM:SS IST)")}</td><td><span class="atip-act-warn">${__("WARN")}</span></td></tr>
						<tr><td>21</td><td>${__("End Date has invalid format")}</td><td><span class="atip-act-warn">${__("WARN")}</span></td></tr>
						<tr><td>22</td><td>${__("End Date is before Start Date")}</td><td><span class="atip-act-warn">${__("WARN")}</span></td></tr>
						<tr><td>23</td><td>${__("Bill Date has invalid format (expected: DD-MM-YYYY)")}</td><td><span class="atip-act-warn">${__("WARN")}</span></td></tr>
						<tr><td>24</td><td>${__("VR Status is not a valid option (Completed / Cancelled / Dummy)")}</td><td><span class="atip-act-warn">${__("WARN")}</span></td></tr>
						<tr><td>25</td><td>${__("Trip Status is not a valid option (Closed / Unbilled / Under Dispute)")}</td><td><span class="atip-act-warn">${__("WARN")}</span></td></tr>
						<tr><td>26</td><td>${__("Lane is empty for a VR ID row")}</td><td><span class="atip-act-warn">${__("WARN")}</span></td></tr>
						<tr><td>27</td><td>${__("Vehicle No is not found in Vehicle master")}</td><td><span class="atip-act-warn">${__("WARN")}</span></td></tr>
					</table>`,
			},
			{
				q: __("Q2. What file format should I upload?"),
				a: `
					<p>${__("Only")} <strong>.csv</strong> ${__("files are supported. Export the Amazon report as CSV before uploading. The file can have any name; mapping is based on its row-1 headers.")}</p>
					<p><strong>${__("Column mapping is determined by the header name in row 1 — not by column position. Columns can be in any order as long as the header names match.")}</strong></p>
					<table>
						<tr><th>${__("Header Name")}</th><th>${__("Where")}</th></tr>
						<tr><td>Trip Date</td><td>${__("Parent update — existing value is retained when blank")}</td></tr>
						<tr><td>Tour ID</td><td>${__("Parent — identity field")}</td></tr>
						<tr><td>VR ID</td><td>${__("Child row")}</td></tr>
						<tr><td>Start Date</td><td>${__("Child row")}</td></tr>
						<tr><td>Bill Date</td><td>${__("Child row")}</td></tr>
						<tr><td>Trip Status</td><td>${__("Child row")}</td></tr>
					</table>`,
			},
			{
				q: __("Q3. How does the update-only import work?"),
				a: `
					<p>${__("The identity field is the")} <strong>Tour ID</strong> ${__("header. Each unique Tour ID value = one Amazon Trip document.")}</p>
					<ul>
						<li><strong>${__("Tour ID exists")}</strong> — ${__("template fields are updated and old child rows are replaced with rows from the file")}</li>
						<li><strong>${__("Tour ID not found")}</strong> — ${__("the row is blocked; no new Amazon Trip is created")}</li>
					</ul>
					<p><strong>${__("Note")}:</strong> ${__("Company, Customer, Branch and other existing parent values are retained when their columns are absent from the template.")}</p>`,
			},
			{
			q: __("Q4. What date formats are supported?"),
				a: `
					<table>
						<tr><th>${__("Header Name")}</th><th>${__("Expected format")}</th><th>${__("Example")}</th></tr>
						<tr><td>Trip Date</td><td>DD-MM-YYYY</td><td><code>01-05-2026</code></td></tr>
						<tr><td>Start Date / End Date</td><td>MM/DD/YYYY HH:MM:SS IST</td><td><code>05/01/2026 01:00:00 IST</code></td></tr>
						<tr><td>Bill Date</td><td>DD-MM-YYYY</td><td><code>17-05-2026</code></td></tr>
					</table>
					<p>${__("A blank or unreadable Trip Date does not erase the value already stored on the Amazon Trip.")}</p>
					<p><strong>${__("Fix")}:</strong> ${__("Do not change the date format in the template. The import auto-strips 'IST' and parses all supported formats correctly.")}</p>`,
			},
			{
			q: __("Q5. What happens with special value formats (distance, cost, boolean)?"),
				a: `
					<table>
						<tr><th>${__("Header Name")}</th><th>${__("Raw value in Excel")}</th><th>${__("Parsed as")}</th></tr>
						<tr><td>Total Distance</td><td><code>40.84 KM</code></td><td>40.84 (numeric)</td></tr>
						<tr><td>Estimated Cost</td><td><code>35.00 INR</code></td><td>35.00 (currency)</td></tr>
						<tr><td>Is CPT Truck</td><td><code>True / False</code></td><td>1 / 0</td></tr>
						<tr><td>Spot Work</td><td><code>Yes / No</code></td><td>1 / 0</td></tr>
						<tr><td>${__("Any currency field")}</td><td><code>None / blank</code></td><td>0.00</td></tr>
					</table>
					<p>${__("All numeric extraction is automatic — commas, currency symbols, and unit suffixes are stripped.")}</p>`,
			},
			{
				q: __("Q6. What are the Trip Status and VR Status allowed values?"),
				a: `
					<p><strong>VR Status</strong> ${__("(the 'Status' header — one per child / VR ID row)")}:</p>
					<p><code>Completed, Cancelled, Dummy</code></p>
					<p><strong>Trip Status</strong> ${__("(the 'Trip Status' header — one per child / VR ID row)")}:</p>
					<p><code>Closed, Unbilled, Under Dispute</code></p>
					<table>
						<tr><th>${__("Raw value in Excel")}</th><th>${__("Import behaviour")}</th></tr>
						<tr><td><code>COMPLETED</code></td><td class="ok">${__("Auto-normalised to 'Completed' and stored")}</td></tr>
						<tr><td><code>CANCELLED</code></td><td class="ok">${__("Auto-normalised to 'Cancelled' and stored")}</td></tr>
						<tr><td><code>Dummy</code></td><td class="ok">${__("Stored as-is (valid option)")}</td></tr>
						<tr><td><code>XYZ</code> ${__("(not a valid option)")}</td><td><span class="atip-act-warn">${__("WARN")}</span> ${__("— row is still imported, but a warning is shown for review")}</td></tr>
					</table>
					<p><strong>${__("Note")}:</strong> ${__("Invalid status values do NOT block the import. The row imports with a warning so you can correct it later. Use Excel Find & Replace if you want clean values before uploading.")}</p>`,
			},
			{
				q: __("Q7. What happens to child rows when I re-import an existing Tour ID?"),
				a: `
					<p>${__("Old child rows are")} <strong>${__("deleted and replaced")}</strong> ${__("with the new rows from the file.")}</p>
					<p>${__("This means:")}</p>
					<ul>
						<li>${__("If a VR ID was previously in the grid but is missing from the new file → it is removed")}</li>
						<li>${__("If a new VR ID appears in the file → it is added as a new child row")}</li>
						<li>${__("All child fields (Base Rate, Fuel Surcharge, Tax %, Gross Pay, Bill No etc.) are fully overwritten")}</li>
					</ul>
					<p><strong>${__("Note")}:</strong> ${__("Any manually edited child rows will be overwritten on re-import. Review before re-importing.")}</p>`,
			},
			{
				q: __("Q8. How do I fix a large number of failures?"),
				a: `
					<ol>
						<li>${__("Click 'Download Error Report' — it lists row number, Tour ID, and error message for each failure.")}</li>
						<li>${__("Confirm every Tour ID already exists in Amazon Trip; this import never creates a missing trip.")}</li>
						<li>${__("Check that Tour ID values are present and resolve any duplicate VR ID conflicts shown in Preview.")}</li>
						<li>${__("Check date formats: Start/End Date must be MM/DD/YYYY HH:MM:SS IST; Bill Date must be DD-MM-YYYY.")}</li>
						<li>${__("Check status values: VR Status must be Completed/Cancelled/Dummy; Trip Status must be Closed/Unbilled/Under Dispute.")}</li>
						<li>${__("Re-upload the corrected file and Preview again before importing.")}</li>
					</ol>`,
			},
			{
				q: __("Q9. How do I test that the import worked correctly?"),
				a: `
					<ol>
						<li>${__("After import, go to Amazon Trip list and search by Tour ID.")}</li>
						<li>${__("Open the record — check parent fields (Company, Customer, Branch, Trip Date, Driver etc.).")}</li>
						<li>${__("Scroll to 'Amazon Payment Data' section — the child table grid should show one row per VR ID from the Excel file.")}</li>
						<li>${__("Verify: VR ID, Load ID, Start Date, End Date, Lane, Base Rate, Gross Pay Amt, Bill No, Bill Date, Trip Status in the grid.")}</li>
						<li>${__("Check Import Action in Preview: 'Update Existing' is ready; 'Error' means the Tour ID or required data must be fixed first.")}</li>
					</ol>`,
			},
		];

		const itemsHtml = faqs.map((f, i) => `
			<div class="atip-faq-item${i === 0 ? " open" : ""}">
				<button type="button" class="atip-faq-q">
					<span>${f.q}</span>
					<span class="atip-faq-q-chev">▼</span>
				</button>
				<div class="atip-faq-a">${f.a}</div>
			</div>
		`).join("");

		wrapper.html(`
			<div class="atip-faq open">
				<div class="atip-faq-head">
					<div class="atip-faq-head-icon">
						<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
							<circle cx="12" cy="12" r="10"/>
							<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
							<line x1="12" y1="17" x2="12.01" y2="17"/>
						</svg>
					</div>
					<div>
						<div class="atip-faq-head-title">${__("Help & FAQ — Amazon Trip Import")}</div>
						<div class="atip-faq-head-sub">${__("Common validation errors and how to fix them")}</div>
					</div>
					<div class="atip-faq-head-chev">▼</div>
				</div>
				<div class="atip-faq-body">${itemsHtml}</div>
			</div>
		`);

		wrapper.find(".atip-faq-head").off("click").on("click", function () {
			wrapper.find(".atip-faq").toggleClass("open");
		});
		wrapper.find(".atip-faq-q").off("click").on("click", function () {
			$(this).closest(".atip-faq-item").toggleClass("open");
		});
	},

	_show_import_confirm(frm, onConfirm) {
		const preview = frm.amazon_trip_preview_result || {};
		const warnings = (preview.warnings || []).filter(w => w.level !== "info");
		const errors = warnings.filter(w => w.level === "error");
		const warns  = warnings.filter(w => w.level === "warning");
		const s = preview.summary || {};
		const tourIds = preview.tour_id_summary || [];
		const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
		const fmt = (n) => Number(n || 0).toLocaleString("en-IN");

		// Split Tour IDs into importable vs errored
		const importableTourIds = tourIds.filter(t => !t.has_errors);
		const erroredTourIds    = tourIds.filter(t => t.has_errors);
		const failedRows = Number(s.failed_rows || 0);
		const skippedRows = Number(s.skipped_rows || 0);

		// ── Tour ID stats ─────────────────────────────────────────────────
		let statsHtml = `<div class="atip-confirm-stats">
			<div class="atip-confirm-stat atip-confirm-stat-ok">
				<div class="atip-confirm-stat-val">${fmt(importableTourIds.length)}</div>
				<div class="atip-confirm-stat-lbl">${__("Tour ID Ready")}</div>
			</div>`;
		if (erroredTourIds.length > 0) statsHtml += `
			<div class="atip-confirm-stat atip-confirm-stat-err">
				<div class="atip-confirm-stat-val">${fmt(erroredTourIds.length)}</div>
				<div class="atip-confirm-stat-lbl">${__("Tour ID Errors")}</div>
			</div>`;
		if (skippedRows > 0) statsHtml += `
			<div class="atip-confirm-stat atip-confirm-stat-skip">
				<div class="atip-confirm-stat-val">${fmt(skippedRows)}</div>
				<div class="atip-confirm-stat-lbl">${__("Skipped (Blank)")}</div>
			</div>`;
		statsHtml += `</div>`;

		// ── Importable Tour ID list ────────────────────────────────────────
		const actionColor = (action) => {
			if (/create new/i.test(action)) return "#166534";
			if (/update/i.test(action))     return "#1e40af";
			return "#374151";
		};
		const actionBg = (action) => {
			if (/create new/i.test(action)) return "#dcfce7";
			if (/update/i.test(action))     return "#dbeafe";
			return "#f3f4f6";
		};

		const tourIdListHtml = (list) => list.map((t, i) => `
			<div style="display:flex;align-items:center;justify-content:space-between;padding:6px 12px;border-bottom:1px solid #f3f4f6;font-size:12.5px;gap:8px;">
				<span style="flex-shrink:0;min-width:28px;font-size:11px;font-weight:700;color:#9ca3af;text-align:right;">${i + 1}.</span>
				<span style="font-weight:700;color:#1e1b4b;flex:1;">${esc(t.tour_id)}</span>
				<span style="color:#6b7280;font-size:11px;white-space:nowrap;">${fmt(t.vr_count)} VR</span>
				<span style="background:${actionBg(t.import_action)};color:${actionColor(t.import_action)};border-radius:8px;padding:2px 8px;font-size:10.5px;font-weight:700;white-space:nowrap;">${esc(t.import_action)}</span>
			</div>`).join("");

		let issuesHtml = "";
		if (importableTourIds.length > 0) {
			issuesHtml += `<div class="atip-confirm-section" style="border:1.5px solid #bbf7d0;border-radius:9px;margin-bottom:10px;overflow:hidden;">
				<div class="atip-confirm-section-head" style="background:#f0fdf4;color:#166634;padding:8px 12px;font-size:12px;font-weight:700;">
					✓ &nbsp;${importableTourIds.length} Tour ID${importableTourIds.length > 1 ? "s" : ""} — ${__("ready to import")}
				</div>
				<div style="background:#fff;max-height:240px;overflow-y:auto;">
					${tourIdListHtml(importableTourIds)}
				</div>
			</div>`;
		}
		if (erroredTourIds.length > 0) {
			const shown = erroredTourIds.slice(0, 5);
			issuesHtml += `<div class="atip-confirm-section atip-confirm-section-error">
				<div class="atip-confirm-section-head">✕ &nbsp;${erroredTourIds.length} Tour ID${erroredTourIds.length > 1 ? "s" : ""} — ${__("have errors and will be skipped")}</div>
				<div class="atip-confirm-section-list">
					${shown.map(t => `<div class="atip-confirm-item error">${esc(t.tour_id)} <span style="font-size:10.5px;font-weight:600;">(${fmt(t.vr_count)} VR)</span></div>`).join("")}
					${erroredTourIds.length > 5 ? `<div class="atip-confirm-more">… ${__("and {0} more — see Preview", [erroredTourIds.length - 5])}</div>` : ""}
				</div>
			</div>`;
		}
		if (warns.length > 0) {
			const shown = warns.slice(0, 3);
			issuesHtml += `<div class="atip-confirm-section atip-confirm-section-warn">
				<div class="atip-confirm-section-head">⚠ &nbsp;${warns.length} ${warns.length === 1 ? __("Warning") : __("Warnings")} — ${__("will be imported with warnings")}</div>
				<div class="atip-confirm-section-list">
					${shown.map(w => `<div class="atip-confirm-item warning">${esc((w.row ? __("Row {0}", [w.row]) + ": " : "") + w.message)}</div>`).join("")}
					${warns.length > 3 ? `<div class="atip-confirm-more">… ${__("and {0} more — see Preview", [warns.length - 3])}</div>` : ""}
				</div>
			</div>`;
		}
		if (!importableTourIds.length && !erroredTourIds.length && !warns.length) {
			issuesHtml = `<div class="atip-confirm-clean">✓ &nbsp;${__("No errors or warnings — ready to import cleanly.")}</div>`;
		}

		const importCount = importableTourIds.length;
		const bodyHtml = `<div class="atip-confirm-body">
			<p class="atip-confirm-intro">${__("You are about to import <strong>{0} Tour ID{1}</strong> into Amazon Trip. Please review before proceeding.", [importCount, importCount === 1 ? "" : "s"])}</p>
			${statsHtml}
			${issuesHtml}
		</div>`;

		const d = new frappe.ui.Dialog({
			title: __("Confirm Import"),
			fields: [{ fieldtype: "HTML", fieldname: "confirm_html", options: bodyHtml }],
			primary_action_label: __("Yes, Proceed with Import"),
			primary_action() {
				d.hide();
				onConfirm();
			},
			secondary_action_label: __("No, Go Back"),
			secondary_action() { d.hide(); },
		});
		d.show();
		d.$wrapper.find(".btn-primary").css({
			background: "linear-gradient(135deg,#16a34a,#22c55e)",
			"border-color": "transparent",
			color: "#fff",
			"font-weight": "700",
		});
	},

	import_rows(frm) {
		if (!frm.doc.file_selection) {
			frappe.msgprint(__("Please select a CSV file first."));
			return;
		}
		if (frm.is_new() || frm.is_dirty()) {
			frappe.msgprint(__("Please save the Import record before starting the import."));
			return;
		}
		if (ATIP_ACTIVE_STATUSES.has(frm.doc.job_status)) {
			frappe.msgprint(__("An import is already in progress."));
			return;
		}
		if (frm.doc.job_status === "Completed") {
			frappe.msgprint(__("This file has already been imported. Each import record can be processed only once."));
			return;
		}

		frm.toggle_enable("importload", false);
		frm.toggle_display("live_progress_html", true);
		frm.toggle_display("import_result_html", true);
		frm.get_field("import_result_html").$wrapper.empty();
		frm.events.render_live_progress(frm, {
			stage: __("Queued…"),
			current: 0,
			total: 0,
		});

		frappe.call({
			method: "logicore.logicore.doctype.amazon_trip___import.amazon_trip___import.import_amazon_trips",
			args: {
				docname: frm.doc.name,
				file_url: frm.doc.file_selection,
			},
			callback: () => {
				frm.events.start_status_fallback_poll(frm);
			},
			error: () => {
				frm.toggle_enable("importload", true);
				frm.get_field("live_progress_html").$wrapper.empty();
			},
		});
	},

	init_progress_subscription(frm) {
		if (frm._atip_subscribed) return;
		frappe.realtime.on(ATIP_EVENT_PROGRESS, (payload) => {
			if (!payload || payload.docname !== frm.doc.name) return;
			frm.events.render_live_progress(frm, payload);
			if (payload.done) {
				if (payload.phase === "preview" || payload.status === "PreviewReady" || payload.status === "PreviewFailed") {
					frm.events.stop_status_fallback_poll(frm);
					frm.get_field("live_progress_html").$wrapper.empty();
					if (payload.status === "PreviewFailed" || payload.status === "Failed") {
						frm.get_field("import_result_html").$wrapper.empty();
						frm.toggle_enable("importload", false);
						frappe.show_alert({ message: __("Preview failed. Please clear the file and re-upload."), indicator: "orange" });
					} else {
						frm.events.fetch_cached_preview(frm);
					}
				} else {
					frm.events.on_import_complete(frm, payload.status);
				}
			}
		});
		frm._atip_subscribed = true;
	},

	restore_progress_from_doc(frm) {
		const status = frm.doc.job_status;
		// Always ensure progress section fields are visible
		frm.toggle_display("live_progress_html", true);
		frm.toggle_display("import_result_html", true);
		if (!status || status === "Draft") {
			frm.get_field("live_progress_html").$wrapper.empty();
			frm.get_field("import_result_html").$wrapper.empty();
			return;
		}
		frm.events.render_live_progress(frm, {
			stage: frm.doc.progress_stage || status,
			current: frm.doc.progress_current,
			total: frm.doc.progress_total,
			inserted: frm.doc.inserted_count,
			updated: frm.doc.updated_count,
			skipped: frm.doc.skipped_count,
			failed: frm.doc.failed_count,
			throughput: frm.doc.throughput_rows_per_sec,
			done: !ATIP_ACTIVE_STATUSES.has(status),
			status,
		});
		if (ATIP_ACTIVE_STATUSES.has(status)) {
			frm.events.start_status_fallback_poll(frm);
		} else if (ATIP_TERMINAL_STATUSES.has(status)) {
			frm.events.render_result_panel(frm);
		}
	},

	render_live_progress(frm, p) {
		const wrapper = frm.get_field("live_progress_html").$wrapper;
		const total = Number(p.total || 0);
		const current = Number(p.current || 0);
		const pct = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
		const stage = frappe.utils.escape_html(p.stage || "");
		const throughput = Number(p.throughput || 0);
		const eta = Number(p.eta_sec || 0);
		const inserted = Number(p.inserted || 0);
		const updated = Number(p.updated || 0);
		const skipped = Number(p.skipped || 0);
		const failed = Number(p.failed || 0);
		const isDone = Boolean(p.done);
		const statusIsActive = ATIP_ACTIVE_STATUSES.has(p.status || "");
		const showCancel = statusIsActive || (!p.status && !isDone);
		const statusClass =
			p.status === "Failed"
				? "atip-failed"
				: p.status === "Cancelled"
					? "atip-cancelled"
					: isDone || p.status === "Completed" || p.status === "PreviewReady"
						? "atip-completed"
						: "atip-running";

		const fmt = (n) => Number(n || 0).toLocaleString("en-IN");
		const cancelBtn = showCancel
			? `<button type="button" class="atip-cancel-btn atip-cancel">${__("Cancel Import")}</button>`
			: "";
		const etaTxt = eta > 0 && !isDone ? `${__("ETA")} ${eta}s` : "";
		const tpTxt = throughput > 0 ? `${throughput.toFixed(1)} ${__("rows/sec")}` : "";

		const borderColor =
			statusClass === "atip-failed"
				? "#fecaca"
				: statusClass === "atip-cancelled"
					? "#fde68a"
					: statusClass === "atip-completed"
						? "#bbf7d0"
						: "#dbe4ff";
		const bgColor =
			statusClass === "atip-failed"
				? "#fef2f2"
				: statusClass === "atip-cancelled"
					? "#fffbeb"
					: statusClass === "atip-completed"
						? "#f0fdf4"
						: "#f8faff";
		const barFill =
			statusClass === "atip-failed"
				? "linear-gradient(90deg,#b91c1c,#ef4444)"
				: statusClass === "atip-cancelled"
					? "linear-gradient(90deg,#b45309,#f59e0b)"
					: statusClass === "atip-completed"
						? "linear-gradient(90deg,#16a34a,#22c55e)"
						: "linear-gradient(90deg,#4f46e5,#6366f1)";
		const barClass = statusClass === "atip-completed" ? "done" : statusClass === "atip-failed" ? "fail" : "";

		// When done, just show a compact bar — full details in render_result_panel below
		if (isDone) {
			wrapper.html(`
				<div class="atip-prog-panel ${statusClass}" style="gap:6px;padding:10px 14px;">
					<div class="atip-prog-bar-wrap"><div class="atip-prog-bar ${barClass}" style="width:100%"></div></div>
					<div class="atip-prog-meta">
						<span><strong>${fmt(total)} / ${fmt(total)}</strong> ${__("rows")} · 100%</span>
						${tpTxt ? `<span>${tpTxt}</span>` : ""}
					</div>
				</div>
			`);
			return;
		}
		wrapper.html(`
			<div class="atip-prog-panel ${statusClass}">
				<div class="atip-prog-head">
					<div class="atip-prog-stage">${stage}</div>
					${cancelBtn}
				</div>
				<div class="atip-prog-bar-wrap"><div class="atip-prog-bar ${barClass}" style="width:${pct}%"></div></div>
				<div class="atip-prog-meta">
					<span><strong>${fmt(current)} / ${fmt(total)}</strong> ${__("rows")} · ${pct}%</span>
					${tpTxt ? `<span>${tpTxt}</span>` : ""}
					${etaTxt ? `<span>${__("ETA")}: ${etaTxt}</span>` : ""}
				</div>
				<div class="atip-prog-counters">
					<div class="atip-prog-counter"><span>${__("Inserted")}</span><strong style="color:#16a34a">${fmt(inserted)}</strong></div>
					<div class="atip-prog-counter"><span>${__("Updated")}</span><strong style="color:#2563eb">${fmt(updated)}</strong></div>
					<div class="atip-prog-counter"><span>${__("Skipped")}</span><strong style="color:#6b7280">${fmt(skipped)}</strong></div>
					<div class="atip-prog-counter"><span>${__("Failed")}</span><strong style="color:#dc2626">${fmt(failed)}</strong></div>
				</div>
			</div>
		`);
		wrapper.find(".atip-cancel").off("click").on("click", () => frm.events.cancel_import(frm));
	},

	cancel_import(frm) {
		frappe.confirm(
			__("Cancel the running import? Rows already imported will NOT be rolled back."),
			() => {
				frappe.call({
					method: "logicore.logicore.doctype.amazon_trip___import.amazon_trip___import.cancel_amazon_trip_import",
					args: { docname: frm.doc.name },
					callback: (r) => {
						if (!(r.message && r.message.ok)) {
							frappe.show_alert({
								message: (r.message && r.message.reason) || __("Could not cancel."),
								indicator: "orange",
							});
						}
					},
				});
			}
		);
	},

	on_import_complete(frm, status) {
		frm.events.stop_status_fallback_poll(frm);
		frm.reload_doc().then(() => {
			frm.events.render_result_panel(frm);
			frm.toggle_enable("importload", frm.doc.job_status !== "Completed");
			frappe.show_alert({
				message: __("Import {0}", [status || frm.doc.job_status || ""]),
				indicator: status === "Completed" ? "green" : status === "Cancelled" ? "orange" : "red",
			});
		});
	},

	render_result_panel(frm) {
		const status = frm.doc.job_status;
		if (!ATIP_TERMINAL_STATUSES.has(status)) {
			frm.get_field("import_result_html").$wrapper.empty();
			return;
		}

		let failures = [];
		try {
			failures = frm.doc.failure_log_json ? JSON.parse(frm.doc.failure_log_json) : [];
		} catch (e) {
			failures = [];
		}

		const fmt = (n) => Number(n || 0).toLocaleString("en-IN");
		const inserted = fmt(frm.doc.inserted_count);
		const updated = fmt(frm.doc.updated_count);
		const skipped = fmt(frm.doc.skipped_count);
		const failed = fmt(frm.doc.failed_count);
		const total = fmt(frm.doc.progress_total);
		const startedAt = frm.doc.started_at || "";
		const finishedAt = frm.doc.finished_at || "";

		const failuresHtml = failures.length
			? frm.events._build_failures_table_html(failures)
			: `<div class="atip-no-failures">${__("No failed rows.")}</div>`;

		const statusClass =
			status === "Completed" ? "atip-completed" : status === "Cancelled" ? "atip-cancelled" : "atip-failed";

		const downloadLink = frm.doc.failure_csv_attachment
			? `<a class="btn btn-sm btn-default atip-download" href="${frappe.utils.escape_html(frm.doc.failure_csv_attachment)}" target="_blank" rel="noopener" download style="white-space:nowrap;">${__("Download Error Report")}</a>`
			: "";

		const borderLeft =
			status === "Completed" ? "#16a34a" : status === "Cancelled" ? "#f59e0b" : "#dc2626";
		const resultStyle = `border-left:4px solid ${borderLeft};`;
		const statusStyle = `color:${borderLeft};`;
		const cardValStyle = (color) => `color:${color};`;

		frm.get_field("import_result_html").$wrapper.html(`
			<div class="atip-result ${statusClass}" style="${resultStyle}">
				<div class="atip-result-header">
					<div class="atip-result-status" style="${statusStyle}">${frappe.utils.escape_html(status)}</div>
					<div class="atip-result-actions">
						${downloadLink}
						<div class="atip-result-time">${frappe.utils.escape_html(startedAt)} → ${frappe.utils.escape_html(finishedAt)}</div>
					</div>
				</div>
				<div class="atip-result-cards">
					<div class="atip-result-card"><span class="atip-result-card-label">${__("Total Rows")}</span><strong class="atip-result-card-val neutral">${total}</strong></div>
					<div class="atip-result-card"><span class="atip-result-card-label">${__("Inserted")}</span><strong class="atip-result-card-val" style="${cardValStyle("#16a34a")}">${inserted}</strong></div>
					<div class="atip-result-card"><span class="atip-result-card-label">${__("Updated")}</span><strong class="atip-result-card-val" style="${cardValStyle("#2563eb")}">${updated}</strong></div>
					<div class="atip-result-card"><span class="atip-result-card-label">${__("Skipped")}</span><strong class="atip-result-card-val" style="${cardValStyle("#6b7280")}">${skipped}</strong></div>
					<div class="atip-result-card"><span class="atip-result-card-label">${__("Failed")}</span><strong class="atip-result-card-val" style="${cardValStyle("#dc2626")}">${failed}</strong></div>
				</div>
				${failuresHtml}
			</div>
		`);

		const $wrap = frm.get_field("import_result_html").$wrapper;
		if (failures.length) {
			frm.events._wire_failures_vscroll($wrap, failures);
		}
	},

	_build_failures_table_html(failures) {
		// Returns a placeholder div; virtual scroll is wired after DOM insertion via _wire_failures_vscroll
		return `
			<div class="atip-failures">
				<div class="atip-failures-head">
					<div class="atip-failures-title">${__("Failed Rows")} (${failures.length.toLocaleString("en-IN")})</div>
					<input type="text" class="atip-failures-search form-control" style="width:min(320px,100%);" placeholder="${__("Filter failures…")}" />
				</div>
				<div class="atip-fail-vscroll-host"></div>
			</div>
		`;
	},

	_wire_failures_vscroll($wrap, failures) {
		const ROW_H = 36;
		const VIEW_H = 380;
		const BUFFER = 12;
		const esc = (v) => frappe.utils.escape_html(String(v == null ? "" : v));
		const badge = (sev) => {
			const s = String(sev || "Error").toLowerCase();
			const cls = s === "warning" ? "warning" : "error";
			return `<span class="atip-fail-badge ${cls}">${esc(sev)}</span>`;
		};

		let visibleData = failures;

		const $host = $wrap.find(".atip-fail-vscroll-host");
		const $outer = $(`<div class="atip-fail-table-wrap">`).appendTo($host);
		const $scroll = $(`<div class="atip-fail-table-scroll" style="height:${VIEW_H}px;">`).appendTo($outer);

		const theadHtml = `<thead>
			<tr>
				<th style="width:60px;">Row</th>
				<th style="width:110px;">VR ID</th>
				<th style="width:90px;">Severity</th>
				<th style="width:100px;">Type</th>
				<th>Message</th>
			</tr>
		</thead>`;

		const renderRow = (f) =>
			`<tr>
				<td>${esc(f.row)}</td>
				<td>${esc(f.vr_id)}</td>
				<td>${badge(f.severity)}</td>
				<td>${esc(f.error_type)}</td>
				<td class="atip-fail-msg">${esc(f.message)}</td>
			</tr>`;

		const $spacer = $(`<div style="position:relative;">`).appendTo($scroll);
		const $table = $(`<table class="atip-fail-table" style="position:absolute;width:100%;">`).appendTo($spacer);
		$table.append(theadHtml);
		const $tbody = $("<tbody>").appendTo($table);

		let lastStart = -1;

		const paint = (scrollTop) => {
			const startIdx = Math.max(0, Math.floor(scrollTop / ROW_H) - BUFFER);
			const endIdx = Math.min(visibleData.length, startIdx + Math.ceil(VIEW_H / ROW_H) + BUFFER * 2);
			if (startIdx === lastStart) return;
			lastStart = startIdx;
			$tbody.html(visibleData.slice(startIdx, endIdx).map(renderRow).join(""));
			$table.css("top", startIdx * ROW_H + "px");
			$spacer.css("height", visibleData.length * ROW_H + "px");
		};

		$scroll.on("scroll", (e) => paint(e.target.scrollTop));

		const applyFilter = (q) => {
			visibleData = q ? failures.filter(f =>
				String(f.row || "").includes(q) ||
				String(f.vr_id || "").toLowerCase().includes(q) ||
				String(f.message || "").toLowerCase().includes(q) ||
				String(f.error_type || "").toLowerCase().includes(q)
			) : failures;
			lastStart = -1;
			$scroll.scrollTop(0);
			paint(0);
		};

		const $countMsg = $(`<div class="atip-sum-msg" style="margin-top:6px;margin-bottom:0;">${failures.length.toLocaleString("en-IN")} ${__("failed rows total.")}</div>`);
		$host.append($countMsg);

		paint(0);
		$wrap.find(".atip-failures-search").off("input").on("input", (e) => {
			applyFilter(e.target.value.toLowerCase().trim());
			$countMsg.text(`${visibleData.length.toLocaleString("en-IN")} / ${failures.length.toLocaleString("en-IN")} ${__("rows")}`);
		});
	},

	start_status_fallback_poll(frm) {
		if (frm._atip_poll) return;
		frm._atip_poll = setInterval(() => {
			if (!frm.doc || !frm.doc.name) {
				frm.events.stop_status_fallback_poll(frm);
				return;
			}
			frappe.call({
				method: "logicore.logicore.doctype.amazon_trip___import.amazon_trip___import.get_import_status",
				args: { docname: frm.doc.name },
				callback: (r) => {
					const s = r.message || {};
					const status = s.job_status || "";
					if (!status) return;
					const isActive = ATIP_ACTIVE_STATUSES.has(status);
					const isTerminal = ATIP_TERMINAL_STATUSES.has(status);
					frm.events.render_live_progress(frm, {
						stage: s.progress_stage || status,
						current: s.progress_current,
						total: s.progress_total,
						inserted: s.inserted_count,
						updated: s.updated_count,
						skipped: s.skipped_count,
						failed: s.failed_count,
						throughput: s.throughput_rows_per_sec,
						done: !isActive,
						status,
					});
					if (isTerminal) {
						frm.events.on_import_complete(frm, status);
						return;
					}
					// Preview completes back to "Draft" — stop polling + fetch preview.
					if (!isActive && status === "Draft" && s.progress_stage === "Preview ready") {
						frm.events.stop_status_fallback_poll(frm);
						frm.get_field("live_progress_html").$wrapper.empty();
						frm.events.fetch_cached_preview(frm);
						return;
					}
					// Preview job failed — stop polling, show error, do NOT reload doc.
					if (!isActive && status === "Draft" && (s.progress_stage || "").startsWith("Preview failed")) {
						frm.events.stop_status_fallback_poll(frm);
						frm.get_field("live_progress_html").$wrapper.empty();
						frm.get_field("import_result_html").$wrapper.empty();
						frm.toggle_enable("importload", false);
						frappe.show_alert({ message: __("Preview failed. Please clear the file and re-upload."), indicator: "orange" });
					}
				},
			});
		}, ATIP_POLL_INTERVAL_MS);
	},

	stop_status_fallback_poll(frm) {
		if (frm._atip_poll) {
			clearInterval(frm._atip_poll);
			frm._atip_poll = null;
		}
	},
});
