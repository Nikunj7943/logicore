// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

const LARGE_BATCH_THRESHOLD = 500;
const DEFAULT_BATCH_SIZE = 10;
const READY_STATUS = "Ready";
const JOB_STATUS_PENDING = "Pending";
const JOB_STATUS_QUEUED = "Queued";
const JOB_STATUS_RUNNING = "Running";
const JOB_STATUS_COMPLETED = "Completed";
const JOB_STATUS_FAILED = "Failed";
const STATUS_POLL_DELAY_MS = 1000;
const STATUS_POLL_ERROR_DELAY_MS = 4000;

// System Settings > Max File Size (MB), the same limit Frappe's File doctype
// enforces server-side — frappe.boot.max_file_size is already loaded at desk
// boot, so no extra round-trip is needed to keep this in sync with the admin's setting.
function pod_max_file_size_mb() {
    return Math.round((frappe.boot.max_file_size || 26214400) / (1024 * 1024));
}

// Status display config: maps backend preview_status → badge class + icon + label
const POD_STATUS_CONFIG = {
    "Ready":            { cls: "s-ready",     icon: "⏳", label: "Ready" },
    "Imported":         { cls: "s-imported",  icon: "✅", label: "Imported" },
    "Failed":           { cls: "s-failed",    icon: "❌", label: "Failed" },
    "No Match":         { cls: "s-no-match",  icon: "⚠️", label: "No Match" },
    "Multiple Matches": { cls: "s-multi",     icon: "🔀", label: "Multi Match" },
    "Duplicate Target": { cls: "s-duplicate", icon: "🔁", label: "Duplicate" },
    "Invalid File":     { cls: "s-invalid",   icon: "✗",  label: "Invalid File" },
    "Invalid Filename": { cls: "s-invalid",   icon: "✗",  label: "Bad Filename" },
};

frappe.ui.form.on("Trip POD Import", {
    refresh(frm) {
        frm.events.ensure_local_session_state(frm);
        frm.events.apply_import_defaults(frm);
        frm.events.configure_actions(frm);
        frm.events.configure_grid(frm);
        frm.events.render_from_doc(frm);
    },

    async trip_type(frm) {
        if (frm.is_new()) {
            frm.events.render_from_doc(frm);
            return;
        }

        await frm.events.ensure_saved(frm);

        if (frm.events.has_local_selection(frm)) {
            await frm.events.request_preview_from_local_files(frm);
            return;
        }

        frm.events.render_from_doc(frm);
    },

    upload_pdfs(frm) {
        frm.events.select_browser_folder(frm);
    },

    importload(frm) {
        frm.events.import_all_batches(frm);
    },

    ensure_local_session_state(frm) {
        if (!(frm.trip_pod_local_files instanceof Map)) {
            frm.trip_pod_local_files = new Map();
        }
        if (typeof frm.trip_pod_selection_summary === "undefined") {
            frm.trip_pod_selection_summary = null;
        }
        if (!frm.trip_pod_runtime_summary) {
            frm.trip_pod_runtime_summary = null;
        }
        if (typeof frm.trip_pod_folder_locked === "undefined") {
            frm.trip_pod_folder_locked = false;
        }
        if (typeof frm.trip_pod_import_in_progress === "undefined") {
            frm.trip_pod_import_in_progress = false;
        }
        if (typeof frm.trip_pod_background_job_started === "undefined") {
            frm.trip_pod_background_job_started = false;
        }
        if (!frm.trip_pod_import_progress) {
            frm.trip_pod_import_progress = null;
        }
        if (typeof frm.trip_pod_status_poll_timer === "undefined") {
            frm.trip_pod_status_poll_timer = null;
        }
        if (typeof frm.trip_pod_status_poll_in_flight === "undefined") {
            frm.trip_pod_status_poll_in_flight = false;
        }
        if (!Array.isArray(frm.trip_pod_selection_rows)) {
            frm.trip_pod_selection_rows = [];
        }
    },

    apply_import_defaults(frm) {
        const updates = {};
        if (!frm.doc.import_date) {
            updates.import_date = frappe.datetime.get_today();
        }
        if (!frm.doc.import_by) {
            updates.import_by = frappe.session.user_fullname || frappe.session.user;
        }
        if (!frm.doc.batch || Number(frm.doc.batch) < 1) {
            updates.batch = DEFAULT_BATCH_SIZE;
        }
        if (typeof frm.doc.source_mode !== "undefined" && frm.doc.source_mode !== "Browser Folder") {
            updates.source_mode = "Browser Folder";
        }
        if (frm.doc.source_folder_path) {
            updates.source_folder_path = "";
        }
        if (Object.keys(updates).length) {
            frm.set_value(updates);
        }
    },

    configure_actions(frm) {
        [
            "source_mode",
            "source_folder_path",
            "status_section",
            "scan_status",
            "import_status",
            "result_report_file",
            "summary_section",
            "total_files_count",
            "ready_files_count",
            "imported_files_count",
            "failed_files_count",
            "unmatched_files_count",
            "duplicate_match_files_count",
            "duplicate_target_files_count",
            "invalid_files_count",
            // Always hide the default Frappe grid — custom HTML table is used instead
            "pod_files_section",
            "pod_files",
        ].forEach((fieldname) => frm.toggle_display(fieldname, false));

        frm.set_df_property("upload_pdfs", "label", __("Select Folder"));
        frm.set_df_property("importload", "label", __("Import"));
        frm.events.apply_post_save_lock(frm);

        // Style the action buttons after Frappe renders them
        frappe.after_ajax(() => frm.events.style_action_buttons(frm));
    },

    style_action_buttons(frm) {
        const selectCtrl = frm.get_field("upload_pdfs");
        const importCtrl = frm.get_field("importload");
        if (!selectCtrl?.$wrapper || !importCtrl?.$wrapper) return;

        selectCtrl.$wrapper.find("button, .btn")
            .addClass("pod-import-btn pod-import-btn-select")
            .html('<span class="pod-btn-icon">📁</span> ' + __("Select Folder"));

        importCtrl.$wrapper.find("button, .btn")
            .addClass("pod-import-btn pod-import-btn-import")
            .html('<span class="pod-btn-icon">🚀</span> ' + __("Import POD"));

        // Place both buttons side-by-side in a flex row (only wrap once)
        let btnGroup = selectCtrl.$wrapper.parent();
        if (!btnGroup.hasClass("pod-btn-group")) {
            const $sectionBody = selectCtrl.$wrapper.closest(".section-body");
            btnGroup = $('<div class="pod-btn-group"></div>')
                .insertBefore(selectCtrl.$wrapper)
                .append(selectCtrl.$wrapper)
                .append(importCtrl.$wrapper);

            // Move the button row out of the Trip Type column and append it
            // to the section body so it spans the full width of the section
            // (below both the Trip Type and Batch columns).
            if ($sectionBody.length) {
                btnGroup.appendTo($sectionBody);
            }
        }

        frm.events.render_faq_help(frm, btnGroup);
    },

    render_faq_help(frm, btnGroup) {
        frm.events.inject_faq_styles();

        // FAQ panel always lives at the very bottom of the form, always visible
        let $panel = frm.$wrapper.find(".pod-faq-panel");
        if (!$panel.length) {
            $panel = $(frm.events.faq_html()).addClass("open").appendTo(frm.layout.wrapper);
            $panel.find(".pod-faq-q").off("click").on("click", function () {
                $(this).closest(".pod-faq-item").toggleClass("open");
            });
        }

        if (!btnGroup.find(".pod-help-btn").length) {
            const $helpBtn = $(`<button type="button" class="pod-import-btn pod-help-btn">
                <span class="pod-btn-icon">❓</span> ${__("Help")}
            </button>`);
            btnGroup.append($helpBtn);

            $helpBtn.on("click", () => {
                $panel[0].scrollIntoView({ behavior: "smooth", block: "start" });
            });
        }
    },

    inject_faq_styles() {
        if (document.getElementById("pod-faq-injected-styles")) return;
        const s = document.createElement("style");
        s.id = "pod-faq-injected-styles";
        s.textContent = `
.pod-btn-group{flex:0 0 100% !important;width:100% !important;max-width:100% !important;order:999;margin-top:8px;}
.pod-help-btn{background:linear-gradient(135deg,#7b61ff,#6366f1) !important;color:#fff !important;border:none !important;box-shadow:0 2px 8px rgba(99,102,241,0.30);}
.pod-help-btn:hover,.pod-help-btn.active{background:linear-gradient(135deg,#6d54ff,#4f46e5) !important;box-shadow:0 4px 14px rgba(99,102,241,0.40);transform:translateY(-1px);}
[data-theme="dark"] .pod-help-btn{background:linear-gradient(135deg,#7b61ff,#6366f1) !important;color:#fff !important;}
[data-theme="dark"] .pod-help-btn:hover,[data-theme="dark"] .pod-help-btn.active{background:linear-gradient(135deg,#6d54ff,#4f46e5) !important;}

.pod-faq-panel{margin-top:16px;border:1px solid #e0e7ff;border-radius:11px;background:#fff;overflow:hidden;max-height:0;opacity:0;transition:max-height .25s ease,opacity .2s ease;}
.pod-faq-panel.open{max-height:3000px;opacity:1;}
.pod-faq-head{display:flex;align-items:center;gap:10px;padding:12px 16px;background:linear-gradient(135deg,#f5f3ff,#eef2ff);border-bottom:1px solid #e0e7ff;}
.pod-faq-head-icon{width:28px;height:28px;border-radius:8px;background:#fff;border:1px solid #e0e7ff;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;}
.pod-faq-head-title{font-size:13.5px;font-weight:700;color:#1e1b4b;}
.pod-faq-head-sub{font-size:11px;color:#6b7280;}
.pod-faq-body{padding:6px 16px 14px;}
.pod-faq-item{border-bottom:1px solid #f1f5f9;}
.pod-faq-item:last-child{border-bottom:none;}
.pod-faq-q{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;text-align:left;background:none;border:none;padding:11px 4px;font-size:12.5px;font-weight:600;color:#1e1b4b;cursor:pointer;}
.pod-faq-q:hover{color:#4f46e5;}
.pod-faq-q .pod-faq-q-chev{transition:transform .2s ease;color:#9ca3af;flex-shrink:0;font-size:11px;}
.pod-faq-item.open .pod-faq-q .pod-faq-q-chev{transform:rotate(180deg);color:#6366f1;}
.pod-faq-a{display:none;padding:0 4px 13px;font-size:12px;line-height:1.65;color:#374151;}
.pod-faq-item.open .pod-faq-a{display:block;}
.pod-faq-a table{width:100%;border-collapse:collapse;margin:8px 0;font-size:11.5px;}
.pod-faq-a th,.pod-faq-a td{border:1px solid #e5e7eb;padding:5px 8px;text-align:left;vertical-align:top;}
.pod-faq-a th{background:#f8faff;font-weight:700;color:#4f46e5;}
.pod-faq-a code{background:#f3f4f6;border-radius:4px;padding:1px 5px;font-size:11px;color:#be123c;}
.pod-faq-a strong{color:#1e1b4b;}
.pod-faq-a .ok{color:#16a34a;font-weight:700;}
.pod-faq-a .bad{color:#dc2626;font-weight:700;}
.pod-faq-a ol,.pod-faq-a ul{margin:6px 0;padding-left:20px;}
.pod-faq-a li{margin-bottom:3px;}
@media(max-width:600px){.pod-faq-a{overflow-x:auto;}.pod-faq-a table{font-size:10.5px;}}

[data-theme="dark"] .pod-faq-panel{background:var(--card-bg,#2d2d4d);border-color:var(--border-color,#444);}
[data-theme="dark"] .pod-faq-head{background:var(--subtle-accent,#1a1a2e);border-color:var(--border-color,#444);}
[data-theme="dark"] .pod-faq-head-icon{background:var(--card-bg,#2d2d4d);border-color:var(--border-color,#444);color:#8b8fff;}
[data-theme="dark"] .pod-faq-head-title{color:var(--text-color,#fff);}
[data-theme="dark"] .pod-faq-head-sub{color:var(--text-muted,#8d99a6);}
[data-theme="dark"] .pod-faq-item{border-color:var(--border-color,#444);}
[data-theme="dark"] .pod-faq-q{color:var(--text-color,#fff);}
[data-theme="dark"] .pod-faq-q:hover{color:#8b8fff;}
[data-theme="dark"] .pod-faq-a{color:var(--text-muted,#c2c8d0);}
[data-theme="dark"] .pod-faq-a th,[data-theme="dark"] .pod-faq-a td{border-color:var(--border-color,#444);}
[data-theme="dark"] .pod-faq-a th{background:var(--subtle-accent,#1a1a2e);color:#8b8fff;}
[data-theme="dark"] .pod-faq-a strong{color:var(--text-color,#fff);}
[data-theme="dark"] .pod-faq-a code{background:var(--subtle-accent,#1a1a2e);color:#fca5a5;}
        `;
        document.head.appendChild(s);
    },

    faq_html() {
        const faqs = [
            {
                q: __("Q1. How many validation checks run, and what do they check — summary?"),
                a: `
                    <p>${__("Before importing, two required fields must be set: <strong>Trip Type</strong> and <strong>POD Type</strong> (Original POD or Duplicate POD).")}</p>
                    <table>
                        <tr><th>#</th><th>${__("Validation")}</th><th>${__("Type")}</th></tr>
                        <tr><td>1</td><td>${__("Trip Type must be selected")}</td><td>${__("Blocking")}</td></tr>
                        <tr><td>2</td><td>${__("POD Type must be selected (Original POD or Duplicate POD)")}</td><td>${__("Blocking")}</td></tr>
                        <tr><td>3</td><td>${__("File name must be exactly &lt;ReferenceNo&gt;.pdf — no hyphens, date or time prefix allowed")}</td><td>${__("Blocking")}</td></tr>
                        <tr><td>4</td><td>${__("File must be a PDF")}</td><td>${__("Blocking")}</td></tr>
                        <tr><td>5</td><td>${__("File size ≤ {0} MB", [pod_max_file_size_mb()])}</td><td>${__("Blocking")}</td></tr>
                        <tr><td>6</td><td>${__("Reference No must match a Trip's TCN/Trip No (or LR No if Trip Type = \"Other\")")}</td><td>${__("Match check")}</td></tr>
                        <tr><td>7</td><td>${__("Only one PDF allowed per matched Trip (Duplicate Target)")}</td><td>${__("Error")}</td></tr>
                        <tr><td>8</td><td>${__("Trip must not already have a POD uploaded")}</td><td>${__("Error")}</td></tr>
                        <tr><td>9</td><td>${__("Arrival Date/Time and Release Date/Time must be filled (per Trip Settings for that Trip Type)")}</td><td>${__("Error")}</td></tr>
                    </table>`,
            },
            {
                q: __("Q2. What is the POD Type field and how does it work?"),
                a: `
                    <p>${__("The <strong>POD Type</strong> field controls which type of POD is recorded on each matched Trip when files are imported:")}</p>
                    <table>
                        <tr><th>${__("POD Type selected")}</th><th>${__("What happens on the Trip")}</th></tr>
                        <tr><td><strong>${__("Original POD")}</strong></td><td>${__("Trip's <em>Uploaded Original/Duplicate Pod</em> is set to <strong>Original</strong> and Pod Status is set to <strong>Original POD Uploaded</strong>")}</td></tr>
                        <tr><td><strong>${__("Duplicate POD")}</strong></td><td>${__("Trip's <em>Uploaded Original/Duplicate Pod</em> is set to <strong>Duplicate</strong> and Pod Status is set to <strong>Duplicate POD Uploaded</strong>")}</td></tr>
                    </table>
                    <p><strong>${__("Default")}:</strong> ${__("Original POD. Change to Duplicate POD only when importing duplicate copies.")}</p>
                    <p><strong>${__("Steps")}:</strong></p>
                    <ol>
                        <li>${__("Select Trip Type")}</li>
                        <li>${__("Select POD Type (Original POD or Duplicate POD)")}</li>
                        <li>${__("Click Select Folder → Import POD")}</li>
                    </ol>`,
            },            
            {
                q: __("Q3. How should the PDF file be named? What's the matching field per Trip Type?"),
                a: `
                    <p>${__("The file name (without extension) must be exactly the Reference No — no hyphens, no date/time prefix or suffix. It is looked up against Trips of the selected Trip Type:")}</p>
                    <table>
                        <tr><th>${__("Trip Type")}</th><th>${__("Matched against field")}</th><th>${__("Example Trip value")}</th><th>${__("Correct file name")}</th></tr>
                        <tr><td>PRIMARY</td><td>TCN/Trip No</td><td><code>RC90210521</code></td><td><code>RC90210521.pdf</code></td></tr>
                        <tr><td>SECONDARY DEDICATED</td><td>TCN/Trip No</td><td><code>R103750764</code></td><td><code>R103750764.pdf</code></td></tr>
                        <tr><td>SECONDARY MARKET</td><td>TCN/Trip No</td><td><code>R103750764</code></td><td><code>R103750764.pdf</code></td></tr>
                        <tr><td>OTHER</td><td><strong>LR No</strong></td><td><code>123456</code></td><td><code>123456.pdf</code></td></tr>
                    </table>
                    <p><span class="bad">${__("Wrong")}:</span> <code>01-04-2026-13-40-03-RC90210521.pdf</code> — ${__("contains hyphens/date-time")} → <em>"Could not parse the reference value from the file name."</em></p>
                    <p><span class="bad">${__("Wrong (for PRIMARY trip)")}:</span> ${__("naming the file with LR No instead of TCN/Trip No")} → <em>"No Trip found..."</em> ${__("since PRIMARY/SECONDARY match on TCN/Trip No, not LR No.")}</p>
                    <p><strong>${__("Fix")}:</strong></p>
                    <ol>
                        <li>${__("Rename the PDF to exactly &lt;ReferenceNo&gt;.pdf — remove any date/time, hyphens or extra prefix/suffix.")}</li>
                        <li>${__("The Reference No must exactly equal the Trip's TCN/Trip No — except for Trip Type \"Other\", where it must equal the LR No.")}</li>
                    </ol>`,
            },
            {
                q: __("Q4. \"No Trip found for TCN/Trip No {X} with Trip Type {Y}\" — what does this mean?"),
                a: `
                    <p>${__("The Reference No (the file name itself, without extension) didn't match any Trip's TCN/Trip No (or LR No, for \"Other\") under the selected Trip Type.")}</p>
                    <p><strong>${__("Fix")}:</strong></p>
                    <ol>
                        <li>${__("Confirm the correct Trip Type is selected (PRIMARY / SECONDARY DEDICATED / SECONDARY MARKET / OTHER).")}</li>
                        <li>${__("Open the Trip list and verify the TCN/Trip No (or LR No for \"Other\") exactly matches the number at the end of the file name — including leading letters like RC or R.")}</li>
                    </ol>`,
            },
            {
                q: __("Q5. \"Multiple Trips found for TCN/Trip No {X}...\" — what does this mean?"),
                a: `
                    <p>${__("The same TCN/Trip No (or LR No) is duplicated across two or more Trips.")}</p>
                    <p><strong>${__("Fix")}:</strong> ${__("Go to the Trip list and correct the duplicate TCN/LR No — every Trip's number must be unique.")}</p>`,
            },
            {
                q: __("Q6. \"Multiple uploaded PDFs map to Trip {X}. Keep only one file per Trip.\" — what to do?"),
                a: `
                    <p>${__("Two or more selected PDFs resolve to the same Trip (same Reference No).")}</p>
                    <p><strong>${__("Fix")}:</strong> ${__("Keep only one POD file per Trip in your selection — remove the extra duplicates.")}</p>`,
            },
            {
                q: __("Q7. \"Trip {X} already has a POD uploaded. Delete the existing POD before importing a new one.\""),
                a: `
                    <p>${__("That Trip already has a POD attached (date_pod_uploaded_on_erp is set). This check applies regardless of the POD Type selected — whether you are importing Original POD or Duplicate POD, the Trip must not have an existing POD.")}</p>
                    <p><strong>${__("Fix")}:</strong> ${__("Open the Trip → delete the existing POD attachment and clear the date fields → save → click Select Folder again to re-scan, then Import POD.")}</p>
                    <p><em>${__("Note: If you need to import Duplicate POD for a Trip that already has Original POD, delete the Original POD first, then run a new import with POD Type set to Duplicate POD.")}</em></p>`,
            },
            {
                q: __("Q8. \"Trip {X}: Arrival Date/Time and Release Date/Time must be filled before POD can be imported.\""),
                a: `
                    <p>${__("Per Trip Settings for this Trip Type, these date fields are mandatory before a POD can be imported.")}</p>
                    <p><strong>${__("Fix")}:</strong> ${__("Open the Trip → fill Arrival Date/Time and Release Date/Time → save → click Select Folder again to re-scan, then Import POD.")}</p>`,
            },
            {
                q: __("Q9. \"File '{X}' is {Y} MB — maximum allowed is {Z} MB.\""),
                a: `
                    <p>${__("PDF file size exceeds the {0} MB limit set in System Settings.", [pod_max_file_size_mb()])}</p>
                    <p><strong>${__("Fix")}:</strong> ${__("Compress the PDF (Ghostscript or an online tool) or scan at lower resolution, then re-upload.")}</p>`,
            },
            {
                q: __("Q10. \"Only PDF files are allowed.\""),
                a: `
                    <p>${__("Image (JPG/PNG) or other document formats can't be imported.")}</p>
                    <p><strong>${__("Fix")}:</strong> ${__("Convert the file to PDF before uploading.")}</p>`,
            },
            {
                q: __("Q11. How do I fix a large batch of failed files (e.g., 30/30 failed)?"),
                a: `
                    <ol>
                        <li>${__("Read the Message column for each failed row — reasons can differ per file.")}</li>
                        <li>${__("Most common cause: linked Trips are missing Arrival/Release Date/Time → bulk-update those Trips.")}</li>
                        <li>${__("For \"No Match\" rows — double check Trip Type and verify TCN/Trip No (or LR No for \"Other\") in the Trip list.")}</li>
                        <li>${__("After fixing, click Select Folder again to re-scan — fixed rows turn to \"Ready\".")}</li>
                        <li>${__("Then click Import POD.")}</li>
                    </ol>`,
            },
        ];

        const itemsHtml = faqs.map((f) => `
            <div class="pod-faq-item">
                <button type="button" class="pod-faq-q">
                    <span>${f.q}</span>
                    <span class="pod-faq-q-chev">▼</span>
                </button>
                <div class="pod-faq-a">${f.a}</div>
            </div>
        `).join("");

        return `
            <div class="pod-faq-panel">
                <div class="pod-faq-head">
                    <span class="pod-faq-head-icon">📖</span>
                    <div>
                        <div class="pod-faq-head-title">${__("Help & FAQ — Bulk POD Import")}</div>
                        <div class="pod-faq-head-sub">${__("File naming rules, validation errors and how to fix them")}</div>
                    </div>
                </div>
                <div class="pod-faq-body">${itemsHtml}</div>
            </div>`;
    },

    set_import_controls_enabled(frm, enabled) {
        frm.events.sync_folder_lock_state(frm);
        frm.events.set_button_enabled(
            frm,
            "upload_pdfs",
            Boolean(enabled && !frm.trip_pod_import_in_progress && !frm.events.is_folder_locked(frm))
        );
        frm.events.set_button_enabled(frm, "importload", Boolean(enabled && frm.events.can_import(frm)));
    },

    set_button_enabled(frm, fieldname, enabled) {
        frm.toggle_enable(fieldname, enabled);
        const field = frm.get_field(fieldname);
        if (!field?.$wrapper) return;

        field.$wrapper
            .find("button, .btn")
            .prop("disabled", !enabled)
            .attr("aria-disabled", enabled ? "false" : "true")
            .toggleClass("disabled", !enabled)
            .css("pointer-events", enabled ? "" : "none");
    },

    apply_post_save_lock(frm) {
        // No field locks — user can change trip_type or batch and re-select folder at any time
    },

    configure_grid(frm) {
        const grid = frm.get_field("pod_files").grid;
        grid.cannot_add_rows = true;
        grid.wrapper.find(".grid-add-row, .grid-add-multiple-rows").hide();
    },

    render_from_doc(frm) {
        frm.events.sync_folder_lock_state(frm);
        const summary = frm.events.get_display_summary(frm);
        const hasFiles = Number(summary.total_files || 0) > 0;

        // Always show the preview section — it drives the entire UI
        frm.toggle_display("preview_section", true);
        frm.toggle_display("preview_summary_html", true);

        frm.events.render_summary(frm, summary, { hasFiles });
        frm.events.set_import_controls_enabled(frm, !frm.trip_pod_import_in_progress);

        // Re-apply button styles after each render (Frappe may re-render buttons)
        frappe.after_ajax(() => frm.events.style_action_buttons(frm));

        frm.events.sync_job_polling(frm);
    },

    render_summary(frm, summary, { hasFiles = false } = {}) {
        const wrapper = frm.get_field("preview_summary_html").$wrapper;
        const selectionSummary = frm.trip_pod_selection_summary;
        const rows = frm.doc.pod_files || [];

        if (!hasFiles && !selectionSummary && !frm.trip_pod_import_in_progress) {
            wrapper.html(frm.events._help_card(frm));
            return;
        }

        let html = "";

        // ── Stat cards ────────────────────────────────────────────────────
        if (hasFiles) {
            const cards = [
                { label: __("Total"),    value: Number(summary.total_files || 0),      color: "#495057", bg: "#f8f9fa", border: "#adb5bd40" },
                { label: __("Ready"),    value: Number(summary.importable_files || 0), color: "#1e7a46", bg: "#edfbf0", border: "#27ae6040" },
                { label: __("Imported"), value: Number(summary.imported_files || 0),   color: "#1a5f9c", bg: "#e8f4fd", border: "#2980b940" },
                { label: __("Failed"),   value: Number(summary.failed_files || 0),     color: "#9b2317", bg: "#fdecea", border: "#e74c3c40" },
            ];
            html += `<div class="pod-stat-grid">
                ${cards.map(({ label, value, color, bg, border }) => `
                    <div class="pod-stat-card" style="background:${bg};border-color:${border};">
                        <div class="pod-stat-label" style="color:${color};">${frappe.utils.escape_html(label)}</div>
                        <div class="pod-stat-value" style="color:${color};">${frappe.utils.escape_html(String(value))}</div>
                    </div>`).join("")}
            </div>`;
        }

        // ── Selection summary (files chosen in browser, not yet staged) ───
        if (selectionSummary) {
            const selTotal     = Number(selectionSummary.total_files || 0);
            const selReady     = Number(selectionSummary.importable_files || 0);
            const selUnmatched = Number(selectionSummary.unmatched_files || 0);
            const selDupMatch  = Number(selectionSummary.duplicate_match_files || 0);
            const selDupTarget = Number(selectionSummary.duplicate_target_files || 0);
            const selInvalid   = Number(selectionSummary.invalid_files || 0);
            const selFailed    = Number(selectionSummary.failed_files || 0);
            const selIgnored   = selTotal - selReady;

            if (!hasFiles) {
                const statCards = [
                    { label: __("Selected PDFs"), value: selTotal,   color: "#495057", bg: "#f8f9fa", border: "#adb5bd40" },
                    { label: __("Matched"),        value: selReady,   color: "#1e7a46", bg: "#edfbf0", border: "#27ae6040" },
                ];
                if (selFailed > 0) {
                    statCards.push({ label: __("Failed"), value: selFailed, color: "#9b2317", bg: "#fdecea", border: "#e74c3c40" });
                }
                statCards.push({ label: __("Skipped"), value: selIgnored - selFailed, color: "#8a5a00", bg: "#fef5e4", border: "#f39c1240" });
                html += `<div class="pod-stat-grid">
                    ${statCards.map(({ label, value, color, bg, border }) => `
                        <div class="pod-stat-card" style="background:${bg};border-color:${border};">
                            <div class="pod-stat-label" style="color:${color};">${frappe.utils.escape_html(label)}</div>
                            <div class="pod-stat-value" style="color:${color};">${frappe.utils.escape_html(String(value))}</div>
                        </div>`).join("")}
                </div>`;
            }

            if (selIgnored > 0) {
                const parts = [];
                if (selUnmatched) parts.push(`${selUnmatched} ${__("No Trip Match")}`);
                if (selDupMatch)  parts.push(`${selDupMatch} ${__("Multiple Trips Found")}`);
                if (selDupTarget) parts.push(`${selDupTarget} ${__("Duplicate Target")}`);
                if (selInvalid)   parts.push(`${selInvalid} ${__("Invalid Filename")}`);
                if (selFailed)    parts.push(`${selFailed} ${__("Validation Failed")}`);
                html += frm.events._alert("warning", "⚠️",
                    `<strong>${__("Skipped files")}:</strong> ${parts.map((p) => frappe.utils.escape_html(p)).join(" &nbsp;·&nbsp; ")}`);
            }

            if (selFailed > 0) {
                const failedRows = (frm.trip_pod_selection_rows || []).filter(
                    (r) => String(r.preview_status || "").trim() === "Failed"
                );
                const failLines = failedRows.slice(0, 5).map((r) =>
                    `<div style="margin-top:4px;">📄 <b>${frappe.utils.escape_html(r.file_name || "")}</b> — ${frappe.utils.escape_html(r.status_message || "")}</div>`
                ).join("");
                const moreCount = failedRows.length > 5 ? `<div style="margin-top:4px;font-size:11px;color:#9b2317;">…and ${failedRows.length - 5} more</div>` : "";
                html += frm.events._alert("danger", "❌",
                    `<strong>${__("Validation errors prevented {0} file(s) from being imported:").replace("{0}", selFailed)}</strong>${failLines}${moreCount}`);
            }

            if (selReady === 0 && selTotal > 0 && selFailed === 0) {
                const sampleRefs = (selectionSummary._sample_unmatched_refs || []).slice(0, 5);
                const sampleHtml = sampleRefs.length
                    ? ` <br><span style="font-size:11px;">${__("Sample extracted refs")}: <code style="background:#fdecea;padding:1px 5px;border-radius:3px;">${sampleRefs.map((r) => frappe.utils.escape_html(r)).join(", ")}</code></span>`
                    : "";
                html += frm.events._alert("danger", "❌",
                    `<strong>${__("No files matched any Trip.")}</strong> ` +
                    frappe.utils.escape_html(__("Check that PDF filenames are just the TCN/LR No (e.g. RC90210521.pdf) and that the Trip Type matches.")) +
                    sampleHtml);
            }
        }

        // ── Alert strips ──────────────────────────────────────────────────
        const alerts = [];

        if (frm.trip_pod_import_in_progress && frm.trip_pod_import_progress) {
            const prog  = frm.trip_pod_import_progress;
            const total = Math.max(Number(prog.total || 0), 1);
            const done  = Number(prog.staged || 0) + Number(prog.failed || 0);
            const pct   = Math.round((done / total) * 100);
            alerts.push({
                type: "info", icon: "⏳",
                msg: `<strong>${__("Staging in progress")}</strong> — ${__("Batch")} ${prog.chunks || 0}: ${prog.staged || 0} ${__("staged")}, ${prog.failed || 0} ${__("failed")} (${pct}%).
                    <div class="pod-progress-strip" style="margin-top:6px;">
                        <div class="pod-progress-fill" style="width:${pct}%;"></div>
                    </div>`,
            });
        }

        if (frm.events.has_running_job(frm)) {
            alerts.push({ type: "info", icon: "🔄", msg: frappe.utils.escape_html(__("Import is running in the background. This page will refresh automatically.")) });
        }

        if (frm.doc.import_status && ![JOB_STATUS_PENDING, JOB_STATUS_RUNNING, JOB_STATUS_QUEUED].includes(frm.doc.import_status)) {
            const ok = frm.doc.import_status === JOB_STATUS_COMPLETED;
            alerts.push({
                type: ok ? "success" : "danger",
                icon: ok ? "✅" : "❌",
                msg: frappe.utils.escape_html(`${__("Import Status")}: ${__(frm.doc.import_status)}`),
            });
        }

        if (hasFiles && frm.events.has_local_selection(frm) && !frm.trip_pod_import_in_progress && !frm.events.has_running_job(frm) && Number(summary.importable_files || 0) > 0) {
            alerts.push({ type: "success", icon: "🚀", msg: frappe.utils.escape_html(__("Folder selected. Click Import PDFs to upload all ready files and complete the Trip import in one run.")) });
        }

        if (hasFiles && !frm.events.has_local_selection(frm) && Number(summary.importable_files || 0) > 0 && !frm.events.has_running_job(frm)) {
            alerts.push({ type: "warning", icon: "📂", msg: frappe.utils.escape_html(__("Local folder files are no longer available in this browser tab. Click Select Folder to re-select and import.")) });
        }

        const allRowsFailed = hasFiles && rows.length > 0 && rows.every((r) => String(r.preview_status || "").trim() === "Failed");
        if (allRowsFailed && !frm.trip_pod_import_in_progress && !frm.events.has_running_job(frm) && !frm.events.has_local_selection(frm)) {
            alerts.push({ type: "info", icon: "🔄", msg: frappe.utils.escape_html(__("All files failed. Fix the issues on the Trip records, then click Select Folder to retry.")) });
        }

        const stagedFileCount = frm.events.get_staged_file_count(frm);
        if (stagedFileCount) {
            alerts.push({ type: "info", icon: "💾", msg: frappe.utils.escape_html(`${__("Temporarily staged PDFs")}: ${stagedFileCount}`) });
        }

        html += alerts.map(({ type, icon, msg }) => frm.events._alert(type, icon, msg)).join("");

        // ── File preview table (ALL pod files) ────────────────────────────
        if (rows.length) {
            html += frm.events._file_table_html(rows);
        }

        // ── Footer ────────────────────────────────────────────────────────
        html += `<div style="font-size:11px;color:#6c757d;margin-top:12px;padding-top:8px;border-top:1px solid #e9ecef;">
            ${__("Batch Size")}: <strong>${frappe.utils.escape_html(String(frm.events.get_batch_size(frm)))}</strong>
        </div>`;

        wrapper.html(html);
    },

    // ── Rendering helpers ──────────────────────────────────────────────────

    _status_badge(status) {
        const cfg = POD_STATUS_CONFIG[status] || { cls: "s-unknown", icon: "•", label: status || "—" };
        return `<span class="pod-status-badge ${cfg.cls}">${cfg.icon} ${frappe.utils.escape_html(cfg.label)}</span>`;
    },

    _file_table_html(rows) {
        const thead = `<thead><tr>
            <th class="col-num">#</th>
            <th>${__("File Name")}</th>
            <th class="col-ref">${__("Ref No")}</th>
            <th class="col-trip">${__("Matched Trip")}</th>
            <th>${__("Status")}</th>
            <th class="col-msg">${__("Message")}</th>
        </tr></thead>`;

        const tbody = rows.map((row, idx) => {
            const status = String(row.preview_status || "").trim();
            const fname  = frappe.utils.escape_html(String(row.file_name || "—"));
            const refno  = frappe.utils.escape_html(String(row.reference_no || "—"));
            const trip   = frappe.utils.escape_html(String(row.matched_trip || ""));
            const msg    = frappe.utils.escape_html(String(row.status_message || ""));
            const dimRow = status === "Imported" ? " style='opacity:0.65;'" : "";
            const tripCell = trip
                ? `<a href="/app/trip/${encodeURIComponent(trip)}" target="_blank" style="color:#4361ee;text-decoration:none;font-weight:600;">${trip}</a>`
                : `<span style="color:#adb5bd;">—</span>`;
            return `<tr${dimRow}>
                <td class="col-num">${idx + 1}</td>
                <td class="col-file">${fname}</td>
                <td class="col-ref">${refno}</td>
                <td class="col-trip">${tripCell}</td>
                <td>${frm_status_badge(status)}</td>
                <td class="col-msg">${msg}</td>
            </tr>`;
        }).join("");

        return `<div class="pod-file-table-wrap">
            <div class="pod-file-table-header">
                <span class="pod-file-table-title">📋 ${__("POD Files Preview")}</span>
                <span class="pod-file-table-count">${rows.length} ${__("files")}</span>
            </div>
            <div class="pod-file-table-scroll">
                <table class="pod-file-table">${thead}<tbody>${tbody}</tbody></table>
            </div>
        </div>`;

        function frm_status_badge(status) {
            const cfg = POD_STATUS_CONFIG[status] || { cls: "s-unknown", icon: "•", label: status || "—" };
            return `<span class="pod-status-badge ${cfg.cls}">${cfg.icon} ${frappe.utils.escape_html(cfg.label)}</span>`;
        }
    },

    _alert(type, icon, msg) {
        return `<div class="pod-alert ${type}">
            <span class="pod-alert-icon">${icon}</span>
            <span>${msg}</span>
        </div>`;
    },

    _help_card(frm) {
        const tripType = String(frm.doc.trip_type || "").trim().toLowerCase();
        let detail;
        if (!frm.doc.trip_type) {
            detail = __("Select Trip Type first, then click Select Folder.");
        } else if (tripType === "other") {
            detail = __("Click Select Folder — files will be matched by LR No.");
        } else {
            detail = __("Click Select Folder — files will be matched by TCN / Trip No.");
        }
        return `<div class="pod-help-card">
            <div class="pod-help-icon">📂</div>
            <div class="pod-help-title">${__("How to Import POD Files")}</div>
            <div class="pod-help-text">
                ${frappe.utils.escape_html(__("1. Set Trip Type  →  2. Set POD Type  →  3. Click Select Folder  →  4. Click Import PDFs"))}<br>
                <em>${frappe.utils.escape_html(detail)}</em>
            </div>
        </div>`;
    },

    // ── Folder selection ───────────────────────────────────────────────────

    create_folder_input() {
        return $('<input type="file" style="display:none;" multiple accept=".pdf">')
            .attr("webkitdirectory", true)
            .attr("directory", true)
            .appendTo("body");
    },

    async select_browser_folder(frm) {
        if (!frm.doc.trip_type) {
            frappe.msgprint(__("Please select Trip Type before choosing a folder."));
            return;
        }

        await frm.events.ensure_saved(frm);
        const input = frm.events.create_folder_input();
        input.on("change", async () => {
            const selectedFiles = Array.from(input[0].files || []);
            input.remove();
            await frm.events.preview_selected_folder(frm, selectedFiles);
        });
        input.trigger("click");
    },

    async preview_selected_folder(frm, files) {
        const previewFiles = frm.events.prepare_preview_files(files || []);
        if (!previewFiles.length) {
            frappe.msgprint(__("The selected folder does not contain any PDF files."));
            return;
        }

        frm.trip_pod_folder_locked = true;
        frm.trip_pod_local_files = new Map(previewFiles.map((item) => [item.client_row_key, item.file]));
        frm.trip_pod_selection_summary = null;
        frm.events.render_from_doc(frm);

        await frm.events.request_preview(frm, previewFiles);
    },

    async request_preview_from_local_files(frm) {
        const previewFiles = Array.from(frm.trip_pod_local_files.entries())
            .map(([client_row_key, file]) => ({
                client_row_key,
                file_name: file.name,
            }))
            .sort((a, b) =>
                a.file_name.localeCompare(b.file_name, undefined, { sensitivity: "base" }) ||
                a.client_row_key.localeCompare(b.client_row_key)
            );

        if (!previewFiles.length) {
            frm.events.render_from_doc(frm);
            return;
        }

        await frm.events.request_preview(frm, previewFiles);
    },

    async request_preview(frm, previewFiles) {
        return frappe.call({
            method: "logicore.logicore.doctype.trip_pod_import.trip_pod_import.preview_local_folder_trip_pods",
            args: {
                docname: frm.doc.name,
                trip_type: frm.doc.trip_type,
                files: JSON.stringify(
                    previewFiles.map((item) => ({
                        client_row_key: item.client_row_key,
                        file_name: item.file_name,
                    }))
                ),
            },
            freeze: true,
            freeze_message: __("Scanning folder and matching trips…"),
            callback: (r) => {
                frm.events.apply_status_payload(frm, r.message || {});
            },
        });
    },

    prepare_preview_files(files) {
        const pdfFiles = (files || []).filter((file) => /\.pdf$/i.test(file.name || ""));
        return pdfFiles
            .slice()
            .sort((a, b) => {
                const ap = String(a.webkitRelativePath || "");
                const bp = String(b.webkitRelativePath || "");
                return (
                    String(a.name || "").localeCompare(String(b.name || ""), undefined, { sensitivity: "base" }) ||
                    ap.localeCompare(bp, undefined, { sensitivity: "base" })
                );
            })
            .map((file, index) => ({
                client_row_key: `row_${index + 1}`,
                file_name: file.name,
                file,
            }));
    },

    // ── Import ─────────────────────────────────────────────────────────────

    async import_all_batches(frm) {
        if (!frm.doc.name) {
            frappe.msgprint(__("Please save the import document before importing."));
            return;
        }
        if (!frm.doc.trip_type) {
            frappe.msgprint(__("Please select Trip Type before importing POD files."));
            return;
        }
        if (!frm.events.has_local_selection(frm)) {
            frappe.msgprint(__("Select Folder again in this tab before importing."));
            return;
        }
        if (frm.trip_pod_import_in_progress) {
            return;
        }

        await frm.events.ensure_saved(frm);
        const initialRows = frm.events.get_batch_candidate_rows(frm);
        if (!initialRows.length) {
            frappe.msgprint(__("No mapped files are ready to import for the current folder selection."));
            return;
        }

        frm.trip_pod_import_in_progress = true;
        frm.trip_pod_import_progress = { chunks: 0, staged: 0, failed: 0, total: initialRows.length };
        frm.events.render_from_doc(frm);

        try {
            while (true) {
                const batchRows = frm.events.get_batch_candidate_rows(frm).slice(0, frm.events.get_batch_size(frm));
                if (!batchRows.length) break;

                const payload = await frm.events.stage_selected_batch(frm, batchRows);
                frm.events.apply_status_payload(frm, payload);
                frm.events.remove_processed_files_from_session(frm, batchRows);
                frm.trip_pod_import_progress.chunks += 1;
                frm.trip_pod_import_progress.staged += Number(payload.staged_count || 0);
                frm.trip_pod_import_progress.failed += Number(payload.failed_count || 0);

                if (Number(payload.failed_count || 0)) {
                    throw new Error(frm.events.build_failure_message(payload.failures || [], __("Failed to stage one or more PDFs. The Trip import was not started.")));
                }

                const processed = Number(frm.trip_pod_import_progress.staged || 0) + Number(frm.trip_pod_import_progress.failed || 0);
                const total     = Math.max(Number(frm.trip_pod_import_progress.total || 0), 1);
                frappe.show_progress(
                    __("Staging POD PDFs"),
                    processed,
                    total,
                    __("Batch {0}: staged {1}, failed {2}, remaining {3}", [
                        frm.trip_pod_import_progress.chunks,
                        frm.trip_pod_import_progress.staged,
                        frm.trip_pod_import_progress.failed,
                        Number(payload.summary?.importable_files || 0),
                    ]),
                    true
                );
            }

            frappe.hide_progress();
            const importPayload = await frm.events.import_staged_trip_pods(frm);
            frm.events.apply_status_payload(frm, importPayload);
            frm.trip_pod_import_progress.imported = Number(importPayload.imported_count || 0);
            frm.trip_pod_import_progress.failed   = Number(importPayload.failed_count || 0);
            frm.events.show_import_run_result(frm, importPayload);
        } catch (error) {
            frappe.hide_progress();
            frappe.msgprint(error?.message || __("Import failed. Please try again."));
        } finally {
            frm.trip_pod_import_in_progress = false;
            frm.trip_pod_import_progress    = null;
            frm.trip_pod_local_files        = new Map();
            frm.events.render_from_doc(frm);
        }
    },

    stage_selected_batch(frm, batchRows) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open(
                "POST",
                "/api/method/logicore.logicore.doctype.trip_pod_import.trip_pod_import.stage_local_folder_trip_pods",
                true
            );
            xhr.setRequestHeader("Accept", "application/json");
            xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);

            xhr.onreadystatechange = () => {
                if (xhr.readyState !== XMLHttpRequest.DONE) return;

                if (xhr.status !== 200) {
                    reject(new Error(frm.events.extract_xhr_error_message(xhr, __("Failed to upload one staging batch. Try a smaller Batch size."))));
                    return;
                }

                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response.message || {});
                } catch (e) {
                    reject(e);
                }
            };

            xhr.onerror = () => reject(new Error(__("Staging request failed. Try a smaller Batch size.")));

            const formData = new FormData();
            formData.append("docname", frm.doc.name);
            formData.append("trip_type", frm.doc.trip_type);
            formData.append(
                "batch_rows",
                JSON.stringify(batchRows.map((row) => ({
                    client_row_key: row.client_row_key,
                    file_name: row.file_name,
                    matched_trip: row.matched_trip,
                    reference_no: row.reference_no,
                })))
            );

            batchRows.forEach((row) => {
                const file = frm.trip_pod_local_files.get(row.client_row_key);
                if (file) formData.append(`file__${row.client_row_key}`, file, row.file_name);
            });

            frappe.dom.freeze(__("Uploading POD batch…"));
            xhr.onloadend = () => frappe.dom.unfreeze();
            xhr.send(formData);
        });
    },

    queue_background_import(frm) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: "logicore.logicore.doctype.trip_pod_import.trip_pod_import.queue_import_trip_pods",
                args: { docname: frm.doc.name, trip_type: frm.doc.trip_type },
                freeze: true,
                freeze_message: __("Queueing background import…"),
                callback: (r) => resolve(r.message || {}),
                error: (r) => reject(new Error(r?.message || r?.exc || __("Could not queue the background import. Please try again."))),
            });
        });
    },

    import_staged_trip_pods(frm) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: "logicore.logicore.doctype.trip_pod_import.trip_pod_import.import_staged_trip_pods",
                args: { docname: frm.doc.name, trip_type: frm.doc.trip_type },
                freeze: true,
                freeze_message: __("Attaching PDFs to Trip records…"),
                callback: (r) => resolve(r.message || {}),
                error: (r) => reject(new Error(r?.message || r?.exc || __("Could not complete the Trip import. Please try again."))),
            });
        });
    },

    remove_processed_files_from_session(frm, batchRows) {
        batchRows.forEach((row) => frm.trip_pod_local_files.delete(row.client_row_key));
    },

    // ── Result dialogs ─────────────────────────────────────────────────────

    show_import_run_result(frm, payload) {
        frappe.hide_progress();
        const importedCount  = Number(payload?.imported_count || frm.trip_pod_import_progress?.imported || 0);
        const failedCount    = Number(payload?.failed_count   || frm.trip_pod_import_progress?.failed   || 0);
        const remainingReady = Number(payload?.summary?.importable_files || 0);
        const failures       = Array.isArray(payload?.failures) ? payload.failures : [];

        frm.events._show_result_dialog({ importedCount, failedCount, remainingReady, failures });
    },

    show_import_result(payload) {
        frappe.hide_progress();
        const importedCount  = Number(payload.imported_count || 0);
        const failedCount    = Number(payload.failed_count || 0);
        const remainingReady = Number(payload.summary?.importable_files || 0);
        const failures       = Array.isArray(payload?.failures) ? payload.failures : [];

        // Delegate to shared result dialog (no frm context needed here)
        const evts = frappe.ui.form.get_open_form()?.events;
        if (evts?._show_result_dialog) {
            evts._show_result_dialog({ importedCount, failedCount, remainingReady, failures });
        } else {
            frappe.msgprint({
                title: __("Trip POD Import Result"),
                indicator: failedCount ? "orange" : "green",
                message: `<div><strong>${__("Imported")}</strong>: ${importedCount}</div>
                          <div><strong>${__("Failed")}</strong>: ${failedCount}</div>`,
            });
        }
    },

    show_background_job_result(frm, payload) {
        frappe.hide_progress();
        const summary        = payload?.summary || frm.events.get_display_summary(frm);
        const importedCount  = Number(summary.imported_files || 0);
        const failedCount    = Number(summary.failed_files || 0);
        const remainingReady = Number(summary.importable_files || 0);

        frm.events._show_result_dialog({ importedCount, failedCount, remainingReady, failures: [] });
    },

    _show_result_dialog({ importedCount, failedCount, remainingReady, failures = [] }) {
        const allOk     = failedCount === 0 && importedCount > 0;
        const allFailed = importedCount === 0 && failedCount > 0;

        const bannerClass = allOk ? "success" : allFailed ? "fail" : "partial";
        const bannerIcon  = allOk ? "🎉" : allFailed ? "❌" : "⚠️";
        const bannerTitle = allOk
            ? __("Import Completed Successfully!")
            : allFailed
                ? __("Import Failed")
                : __("Import Completed with Errors");
        const bannerSub = allOk
            ? `${importedCount} ${__("POD file(s) attached to trips.")}`
            : `${importedCount} ${__("imported")}, ${failedCount} ${__("failed")}.`;

        const statsHtml = `<div class="pod-result-stats">
            <div class="pod-result-stat imported">
                <div class="pod-rs-num">${importedCount}</div>
                <div class="pod-rs-lbl">${__("Imported")}</div>
            </div>
            <div class="pod-result-stat failed">
                <div class="pod-rs-num">${failedCount}</div>
                <div class="pod-rs-lbl">${__("Failed")}</div>
            </div>
            <div class="pod-result-stat remaining">
                <div class="pod-rs-num">${remainingReady}</div>
                <div class="pod-rs-lbl">${__("Remaining")}</div>
            </div>
        </div>`;

        let errorsHtml = "";
        if (failures.length) {
            const errorRows = failures.slice(0, 20).map((f) => `
                <div class="pod-result-error-row">
                    <span class="err-icon">❌</span>
                    <div>
                        <div class="err-file">${frappe.utils.escape_html(String(f.file_name || ""))}</div>
                        ${f.message ? `<div class="err-msg">${frappe.utils.escape_html(String(f.message))}</div>` : ""}
                    </div>
                </div>`).join("");
            const overflow = failures.length > 20
                ? `<div style="font-size:11px;color:#6c757d;margin-top:6px;">… and ${failures.length - 20} more</div>`
                : "";
            errorsHtml = `<div class="pod-result-errors">
                <div class="pod-result-errors-title">❌ ${__("Failed Files")}</div>
                ${errorRows}${overflow}
            </div>`;
        }

        const msgHtml = `<div class="pod-result-wrap">
            <div class="pod-result-banner ${bannerClass}">
                <span class="pod-result-banner-icon">${bannerIcon}</span>
                <div class="pod-result-banner-text">
                    <strong>${frappe.utils.escape_html(bannerTitle)}</strong>
                    <span>${frappe.utils.escape_html(bannerSub)}</span>
                </div>
            </div>
            ${statsHtml}
            ${errorsHtml}
        </div>`;

        frappe.msgprint({
            title: __("Trip POD Import Result"),
            indicator: allOk ? "green" : failedCount ? "orange" : "blue",
            message: msgHtml,
        });
    },

    // ── State helpers ──────────────────────────────────────────────────────

    apply_status_payload(frm, payload) {
        if (payload.summary) {
            frm.trip_pod_runtime_summary = payload.summary;
        }
        if (payload.scan_status) {
            frm.doc.scan_status = payload.scan_status;
        }
        if (payload.import_status) {
            frm.doc.import_status = payload.import_status;
        }
        if (typeof payload.result_report_file !== "undefined") {
            frm.doc.result_report_file = payload.result_report_file || "";
        }
        frm.events.apply_server_doc(frm, payload);
        if (payload.selection_summary) {
            frm.trip_pod_selection_summary = payload.selection_summary;
            frm.trip_pod_selection_summary._sample_unmatched_refs = payload.sample_unmatched_refs || [];
            frm.trip_pod_selection_rows = payload.selection_failed_rows || [];
        }
        if (payload.doc) {
            frm.trip_pod_runtime_summary = null;
        }
        frm.refresh_fields(["trip_type", "batch"]);
        frm.events.render_from_doc(frm);
    },

    apply_server_doc(frm, payload) {
        if (payload?.doc) {
            frappe.model.sync(payload.doc);
            const syncedDoc = locals[frm.doctype] && locals[frm.doctype][frm.docname];
            if (syncedDoc) frm.doc = syncedDoc;
        }
        frm.events.sync_server_modified(frm, payload);
    },

    get_batch_candidate_rows(frm) {
        return (frm.doc.pod_files || []).filter(
            (row) =>
                Number(row.can_import || 0) &&
                String(row.preview_status || "").trim() === READY_STATUS &&
                frm.trip_pod_local_files.has(String(row.client_row_key || "").trim())
        );
    },

    get_batch_size(frm) {
        return Math.max(Number(frm.doc.batch || DEFAULT_BATCH_SIZE), 1);
    },

    get_staged_file_count(frm) {
        return (frm.doc.pod_files || []).filter((row) => String(row.pod_file || "").trim()).length;
    },

    get_display_summary(frm) {
        return frm.trip_pod_runtime_summary || frm.events.summary_from_doc(frm.doc);
    },

    has_local_selection(frm) {
        return frm.trip_pod_local_files instanceof Map && frm.trip_pod_local_files.size > 0;
    },

    has_running_job(frm, payload = null) {
        const scanStatus   = String(payload?.scan_status   || frm.doc.scan_status   || JOB_STATUS_PENDING).trim();
        const importStatus = String(payload?.import_status || frm.doc.import_status || JOB_STATUS_PENDING).trim();
        return [JOB_STATUS_QUEUED, JOB_STATUS_RUNNING].includes(scanStatus) ||
               [JOB_STATUS_QUEUED, JOB_STATUS_RUNNING].includes(importStatus);
    },

    is_folder_locked(frm) {
        return Boolean(frm.trip_pod_folder_locked);
    },

    sync_folder_lock_state(frm) {
        // Only lock while an import is actively running
        frm.trip_pod_folder_locked = Boolean(frm.trip_pod_import_in_progress);
    },

    summary_from_doc(doc) {
        const rows = doc.pod_files || [];
        return {
            total_files:      rows.length,
            importable_files: rows.filter((row) => Number(row.can_import || 0)).length,
            imported_files:   rows.filter((row) => String(row.preview_status || "").trim() === "Imported").length,
            failed_files:     rows.filter((row) => String(row.preview_status || "").trim() === "Failed").length,
        };
    },

    can_import(frm) {
        return Boolean(
            frm.doc.trip_type &&
            frm.doc.name &&
            !frm.trip_pod_import_in_progress &&
            !frm.events.has_running_job(frm) &&
            frm.events.get_batch_candidate_rows(frm).length
        );
    },

    is_large_batch(summary) {
        return Number(summary.total_files || 0) > LARGE_BATCH_THRESHOLD;
    },

    sync_server_modified(frm, payload) {
        if (payload?.doc_modified)    frm.doc.modified    = payload.doc_modified;
        if (payload?.doc_modified_by) frm.doc.modified_by = payload.doc_modified_by;
    },

    // ── Job polling ────────────────────────────────────────────────────────

    sync_job_polling(frm) {
        if (frm.events.has_running_job(frm)) {
            frm.events.start_status_polling(frm);
        } else {
            frm.events.stop_status_polling(frm);
        }
    },

    start_status_polling(frm) {
        if (!frm.doc.name || frm.trip_pod_status_poll_in_flight || frm.trip_pod_status_poll_timer || !frm.events.has_running_job(frm)) {
            return;
        }

        frm.trip_pod_status_poll_in_flight = true;
        frappe.call({
            method: "logicore.logicore.doctype.trip_pod_import.trip_pod_import.get_import_job_status",
            args: { docname: frm.doc.name },
            freeze: false,
            callback: (r) => {
                const payload = r.message || {};
                frm.events.apply_status_payload(frm, payload);
                if (frm.events.has_running_job(frm, payload)) {
                    frm.events.schedule_status_poll(frm, STATUS_POLL_DELAY_MS);
                    return;
                }
                frappe.hide_progress();
                if (frm.trip_pod_background_job_started) {
                    frm.events.show_background_job_result(frm, payload);
                    frm.trip_pod_background_job_started = false;
                }
            },
            error: () => {
                if (frm.events.has_running_job(frm)) {
                    frm.events.schedule_status_poll(frm, STATUS_POLL_ERROR_DELAY_MS);
                    return;
                }
                frappe.hide_progress();
            },
            always: () => {
                frm.trip_pod_status_poll_in_flight = false;
            },
        });
    },

    schedule_status_poll(frm, delay) {
        frm.events.stop_status_polling(frm);
        frm.trip_pod_status_poll_timer = window.setTimeout(() => {
            frm.trip_pod_status_poll_timer = null;
            frm.events.start_status_polling(frm);
        }, delay);
    },

    stop_status_polling(frm) {
        if (frm.trip_pod_status_poll_timer) {
            window.clearTimeout(frm.trip_pod_status_poll_timer);
            frm.trip_pod_status_poll_timer = null;
        }
    },

    // ── Error utilities ────────────────────────────────────────────────────

    extract_xhr_error_message(xhr, fallbackMessage) {
        try {
            const response = JSON.parse(xhr.responseText || "{}");
            if (response?._server_messages) {
                const serverMessages = JSON.parse(response._server_messages);
                if (serverMessages?.length) {
                    const firstMessage = JSON.parse(serverMessages[0]);
                    if (firstMessage?.message) return firstMessage.message;
                }
            }
            if (response?.message) {
                return typeof response.message === "string" ? response.message : response.message.message || fallbackMessage;
            }
            if (response?.exception) return response.exception;
        } catch (_) {
            // fall through to fallback
        }
        return xhr.statusText || fallbackMessage;
    },

    build_failure_message(failures, fallbackMessage) {
        if (!Array.isArray(failures) || !failures.length) return fallbackMessage;
        const f = failures[0] || {};
        return [f.file_name, f.message].filter(Boolean).join(": ") || fallbackMessage;
    },

    async ensure_saved(frm) {
        if (frm.is_new() || frm.is_dirty()) {
            await frm.save();
        }
    },
});
