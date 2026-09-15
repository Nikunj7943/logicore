// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

function tms_try_parse_json(value, fallback) {
	if (!value) return fallback;
	try {
		return JSON.parse(value);
	} catch (e) {
		return fallback;
	}
}

function tms_safe_text(value, fallback = "—") {
	if (value === null || value === undefined || value === "") return fallback;
	return String(value);
}

function tms_fmt_datetime(value) {
	if (!value) return "—";
	try {
		if (frappe.datetime && frappe.datetime.str_to_user) {
			return frappe.datetime.str_to_user(String(value));
		}
	} catch (e) {
		// Fallback to raw value below
	}
	return String(value);
}

function tms_trip_import_log_inject_style() {
	if (document.getElementById("tms-trip-import-log-style")) return;
	const style = document.createElement("style");
	style.id = "tms-trip-import-log-style";
	style.textContent = `
.tms-til-wrap{display:flex;flex-direction:column;gap:14px;}
.tms-til-hero{position:relative;overflow:hidden;border-radius:16px;padding:18px 18px 16px;background:linear-gradient(135deg,#0f172a 0%,#1d4ed8 58%,#38bdf8 100%);color:#fff;box-shadow:0 10px 30px rgba(30,64,175,.18);}
.tms-til-hero:before{content:'';position:absolute;right:-40px;top:-40px;width:160px;height:160px;border-radius:50%;background:rgba(255,255,255,.08);}
.tms-til-hero-top{position:relative;display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;}
.tms-til-title{font-size:20px;font-weight:800;letter-spacing:-.02em;line-height:1.1;margin-bottom:4px;}
.tms-til-sub{font-size:12px;color:rgba(255,255,255,.78);max-width:760px;}
.tms-til-hero-status{display:inline-flex;align-items:center;gap:7px;padding:7px 12px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;}
.tms-til-hero-status:before{content:'';width:8px;height:8px;border-radius:50%;background:currentColor;}
.tms-til-hero-status.ok{color:#86efac;}
.tms-til-hero-status.err{color:#fca5a5;}
.tms-til-hero-status.warn{color:#fde68a;}
.tms-til-overview-grid{position:relative;display:grid;grid-template-columns:1.2fr .8fr;gap:12px;margin-top:16px;}
.tms-til-overview-card{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);border-radius:14px;padding:14px 15px;backdrop-filter:blur(4px);}
.tms-til-overview-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:rgba(255,255,255,.68);margin-bottom:8px;}
.tms-til-meta-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 14px;}
.tms-til-meta-item{min-width:0;}
.tms-til-meta-item .k{font-size:10px;color:rgba(255,255,255,.62);text-transform:uppercase;font-weight:700;margin-bottom:3px;}
.tms-til-meta-item .v{font-size:13px;font-weight:700;color:#fff;word-break:break-word;}
.tms-til-file-links{display:flex;flex-direction:column;gap:8px;}
.tms-til-file-link{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;border-radius:10px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.14);}
.tms-til-file-link .name{font-size:12px;font-weight:700;color:#fff;word-break:break-word;}
.tms-til-file-link a{font-size:11px;font-weight:700;color:#bfdbfe;}
.tms-til-cards{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;}
.tms-til-card{background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);border:1px solid var(--border-color);border-radius:14px;padding:14px 15px;box-shadow:0 4px 14px rgba(15,23,42,.05);}
.tms-til-card .lbl{font-size:10px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:5px;}
.tms-til-card .val{font-size:18px;font-weight:800;color:var(--text-color);}
.tms-til-panel{border:1px solid var(--border-color);border-radius:14px;overflow:hidden;background:#fff;box-shadow:0 4px 16px rgba(15,23,42,.04);}
.tms-til-head{padding:12px 14px;background:linear-gradient(180deg,#f8fafc 0%,#f1f5f9 100%);border-bottom:1px solid var(--border-color);font-weight:800;font-size:12px;letter-spacing:.02em;}
.tms-til-body{padding:14px;}
.tms-til-table-wrap{max-height:320px;overflow:auto;}
.tms-til-table{width:100%;border-collapse:collapse;font-size:12px;}
.tms-til-table th,.tms-til-table td{padding:8px;border-bottom:1px solid var(--border-color);vertical-align:top;text-align:left;}
.tms-til-table th{position:sticky;top:0;background:#f8fafc;z-index:1;font-weight:700;}
.tms-til-pill{display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:700;}
.tms-til-pill.ok{background:#dcfce7;color:#166534;}
.tms-til-pill.err{background:#fee2e2;color:#991b1b;}
.tms-til-pill.warn{background:#fef3c7;color:#92400e;}
.tms-til-pill.muted{background:#f1f5f9;color:#64748b;}
.tms-til-trip-link{color:var(--primary,#2490ef);font-weight:700;text-decoration:none;}
.tms-til-trip-link:hover{text-decoration:underline;}
.tms-til-note{font-size:12px;color:var(--text-muted);}
@media(max-width:900px){.tms-til-overview-grid{grid-template-columns:1fr;}.tms-til-meta-grid{grid-template-columns:1fr;}.tms-til-cards{grid-template-columns:repeat(2,minmax(0,1fr));}}
	`;
	document.head.appendChild(style);
}

function tms_trip_import_log_hide_native_fields(frm) {
	[
		"template",
		"template_name",
		"company",
		"import_mode",
		"status",
		"uploaded_file",
		"error_file",
		"total_rows",
		"success_rows",
		"failed_rows",
		"created_count",
		"updated_count",
		"skipped_count",
		"started_at",
		"finished_at",
		"imported_by",
		"preview_json",
		"summary_json",
		"row_result_json",
	].forEach(fieldname => frm.toggle_display(fieldname, false));
	["raw_data_section", "stats_section"].forEach(section => frm.toggle_display(section, false));
}

function tms_trip_import_log_render_overview(frm, summary) {
	const wrapper = frm.get_field("overview_html").$wrapper;
	const statusClass = ["Completed", "Validated"].includes(frm.doc.status)
		? "ok"
		: frm.doc.status === "Completed With Errors" || frm.doc.status === "Failed"
			? "err"
			: "warn";
	const meta = [
		[__("Template"), tms_safe_text(frm.doc.template_name || frm.doc.template)],
		[__("Company"), tms_safe_text(frm.doc.company)],
		[__("Import Mode"), tms_safe_text(frm.doc.import_mode)],
		[__("Imported By"), tms_safe_text(frm.doc.imported_by)],
		[__("Started At"), tms_fmt_datetime(frm.doc.started_at)],
		[__("Finished At"), tms_fmt_datetime(frm.doc.finished_at)],
	];
	const fileRows = [
		frm.doc.uploaded_file ? { label: __("Uploaded File"), url: frm.doc.uploaded_file } : null,
		frm.doc.error_file ? { label: __("Error File"), url: frm.doc.error_file } : null,
	].filter(Boolean);
	wrapper.html(`
		<div class="tms-til-hero">
			<div class="tms-til-hero-top">
				<div>
					<div class="tms-til-title">${frappe.utils.escape_html(frm.doc.template_name || __("Trip Import Log"))}</div>
					<div class="tms-til-sub">${__("A clean summary of the imported file, mapped template columns, and row-wise outcomes for this trip import run.")}</div>
				</div>
				<div class="tms-til-hero-status ${statusClass}">${frappe.utils.escape_html(frm.doc.status || __("Draft"))}</div>
			</div>
			<div class="tms-til-overview-grid">
				<div class="tms-til-overview-card">
					<div class="tms-til-overview-label">${__("Import Details")}</div>
					<div class="tms-til-meta-grid">
						${meta.map(([k, v]) => `
							<div class="tms-til-meta-item">
								<div class="k">${k}</div>
								<div class="v">${frappe.utils.escape_html(v)}</div>
							</div>
						`).join("")}
					</div>
				</div>
				<div class="tms-til-overview-card">
					<div class="tms-til-overview-label">${__("Files")}</div>
					<div class="tms-til-file-links">
						${fileRows.length ? fileRows.map(file => `
							<div class="tms-til-file-link">
								<div>
									<div class="k" style="font-size:10px;color:rgba(255,255,255,.62);text-transform:uppercase;font-weight:700;">${file.label}</div>
									<div class="name">${frappe.utils.escape_html(file.url)}</div>
								</div>
								<a href="${frappe.utils.escape_html(file.url)}" target="_blank">${__("Open")}</a>
							</div>
						`).join("") : `<div class="tms-til-note" style="color:rgba(255,255,255,.7);">${__("No attached files available.")}</div>`}
					</div>
				</div>
			</div>
		</div>
	`);
}

function tms_trip_import_log_render_summary(frm, preview, summary, rows) {
	const wrapper = frm.get_field("summary_html").$wrapper;
	const cards = [
		{ label: __("Total Rows"), value: summary.total_rows ?? frm.doc.total_rows ?? 0 },
		{ label: __("Success Rows"), value: summary.success_rows ?? frm.doc.success_rows ?? 0 },
		{ label: __("Failed Rows"), value: summary.failed_rows ?? frm.doc.failed_rows ?? 0 },
		{ label: __("Created"), value: summary.created_count ?? frm.doc.created_count ?? 0 },
		{ label: __("Updated"), value: summary.updated_count ?? frm.doc.updated_count ?? 0 },
	];
	wrapper.html(`
		<div class="tms-til-wrap">
			<div class="tms-til-note">${__("Preview and result counters are consolidated here to avoid duplicate values elsewhere on the form.")}</div>
			<div class="tms-til-cards">
				${cards.map(card => `<div class="tms-til-card"><div class="lbl">${card.label}</div><div class="val">${card.value}</div></div>`).join("")}
			</div>
		</div>
	`);
}

function tms_trip_import_log_render_columns(frm, preview) {
	const wrapper = frm.get_field("preview_columns_html").$wrapper;
	const columns = preview.columns || [];
	const missing = preview.missing_headers || [];
	const duplicates = preview.duplicate_headers || [];
	if (!columns.length) {
		wrapper.html(`<div class="tms-til-note">${__("No preview column information available.")}</div>`);
		return;
	}
	wrapper.html(`
		<div class="tms-til-panel">
			<div class="tms-til-head">${__("Mapped CSV Columns")}</div>
			<div class="tms-til-body">
				<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
					<span class="tms-til-pill ${missing.length ? "err" : "ok"}">${__("Missing Headers")}: ${missing.length}</span>
					<span class="tms-til-pill ${duplicates.length ? "err" : "ok"}">${__("Duplicate Headers")}: ${duplicates.length}</span>
					<span class="tms-til-pill ok">${__("Matched Headers")}: ${preview.matched_headers || 0}</span>
				</div>
				<div class="tms-til-table-wrap">
					<table class="tms-til-table">
						<thead>
							<tr>
								<th>${__("No")}</th>
								<th>${__("CSV Header")}</th>
								<th>${__("Trip Field")}</th>
								<th>${__("Field Type")}</th>
								<th>${__("Required")}</th>
							</tr>
						</thead>
						<tbody>
							${columns.map((col, idx) => `
								<tr>
									<td>${idx + 1}</td>
									<td>${frappe.utils.escape_html(col.csv_header || "")}</td>
									<td>${frappe.utils.escape_html(col.fieldname || "")}</td>
									<td>${frappe.utils.escape_html(col.fieldtype || "")}</td>
									<td>${col.required ? __("Yes") : __("No")}</td>
								</tr>
							`).join("")}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	`);
}

function tms_trip_import_log_render_rows(frm, rows) {
	const wrapper = frm.get_field("row_results_html").$wrapper;
	if (!rows.length) {
		wrapper.html(`<div class="tms-til-note">${__("No row-level results available yet.")}</div>`);
		return;
	}
	wrapper.html(`
		<div class="tms-til-panel">
			<div class="tms-til-head">${__("Row Results")}</div>
			<div class="tms-til-body">
				<div class="tms-til-table-wrap">
					<table class="tms-til-table">
						<thead>
							<tr>
								<th>${__("Row")}</th>
								<th>${__("Status")}</th>
								<th>${__("Action")}</th>
								<th>${__("Trip")}</th>
								<th>${__("Message")}</th>
							</tr>
						</thead>
						<tbody>
							${rows.map(row => {
								const status = row.status || "";
								const pillClass = status === "Success" ? "ok" : status === "Failed" ? "err" : status === "Ignored" ? "muted" : "warn";
								const tripCell = row.trip_name
									? `<a class="tms-til-trip-link" href="${frappe.utils.get_form_link("Trip", row.trip_name)}" target="_blank">${frappe.utils.escape_html(row.trip_name)}</a>`
									: "—";
								return `
									<tr>
										<td>${row.row_number ?? ""}</td>
										<td><span class="tms-til-pill ${pillClass}">${frappe.utils.escape_html(status)}</span></td>
										<td>${frappe.utils.escape_html(row.action || "—")}</td>
										<td>${tripCell}</td>
										<td>${frappe.utils.escape_html(row.message || "")}</td>
									</tr>
								`;
							}).join("")}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	`);
}

frappe.ui.form.on("Trip Import Log", {
	refresh(frm) {
		try {
			tms_trip_import_log_inject_style();
			tms_trip_import_log_hide_native_fields(frm);
			const preview = tms_try_parse_json(frm.doc.preview_json, {});
			const summary = tms_try_parse_json(frm.doc.summary_json, {});
			const rows = tms_try_parse_json(frm.doc.row_result_json, []);
			tms_trip_import_log_render_overview(frm, summary);
			tms_trip_import_log_render_summary(frm, preview, summary, rows);
			tms_trip_import_log_render_columns(frm, preview);
			tms_trip_import_log_render_rows(frm, rows);
		} catch (e) {
			console.error("[TMS] Trip Import Log render failed:", e);
			const wrapper = frm.get_field("overview_html").$wrapper;
			wrapper.html(`
				<div style="padding:14px;border:1px solid #fecaca;background:#fef2f2;color:#991b1b;border-radius:12px;font-size:13px;">
					<strong>${__("Trip Import Log UI could not render.")}</strong><br>
					${__("Please refresh once. If it still happens, check browser console for the exact error.")}
				</div>
			`);
		}
	},
});
