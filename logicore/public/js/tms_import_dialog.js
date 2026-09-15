// Copyright (c) 2026, LogiCore and contributors
// Generic import dialog for any TMS DocType that has an active Import Template.

frappe.provide("TMS.import");

// All non-table TMS doctypes that should show the Import button on their list views
const _TMS_IMPORT_DOCTYPES = [
	"Trip", "Amazon Trip", "Business Format", "Business Subformat",
	"City", "Vehicle Type", "Trip Type", "Trip Classification", "Trip Field Setting",
	"Standard KM", "Compliances",
	"Vehicle Expense", "Fuel Urea Expenses", "Repair Expenses",
	"Tyre Expenses", "Battery Expenses", "Service Log", "Service Logs",
	"Vehicle Finance", "Vehicle Market",
	"Receipt", "Payment", "Vendor Payment", "Supplier Payment",
	"Types of Goods", "Regulatory",
	"Staff Attendance", "Staff Payroll",
	"Alert Settings",
];

function _tms_import_inject_list_btn_style() {
	if (document.getElementById("tms-list-btn-style")) return;
	const s = document.createElement("style");
	s.id = "tms-list-btn-style";
	s.textContent = `
.tms-list-btn.btn.btn-default,
.tms-list-btn.btn {
    display: inline-flex !important; align-items: center !important; gap: 6px !important;
    height: 30px !important; padding: 0 14px !important;
    border: none !important; border-radius: 8px !important;
    font-size: 12px !important; font-weight: 700 !important; cursor: pointer !important;
    letter-spacing: 0.3px !important;
    transition: transform 0.12s, box-shadow 0.12s, filter 0.12s !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18) !important;
    white-space: nowrap !important;
}
.tms-list-btn.btn:hover { transform: translateY(-1px) !important; filter: brightness(1.08) !important; box-shadow: 0 4px 14px rgba(0,0,0,0.22) !important; }
.tms-list-btn.btn:active { transform: translateY(0) !important; filter: brightness(0.96) !important; }
.tms-list-btn-import.btn,
.tms-list-btn-import.btn.btn-default,
.tms-list-btn-import.btn.btn-default:hover,
.tms-list-btn-import.btn.btn-default:focus {
    background: linear-gradient(135deg, #0891B2 0%, #0D9488 100%) !important;
    color: #fff !important;
}
	`;
	document.head.appendChild(s);
}

function _tms_import_inject_dialog_style() {
	if (document.getElementById("tms-import-dialog-style")) return;
	const style = document.createElement("style");
	style.id = "tms-import-dialog-style";
	style.textContent = `
.tms-ti-dialog{display:flex;flex-direction:column;gap:12px;}
.tms-ti-banner{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 16px;border-radius:12px;background:linear-gradient(135deg,#0f766e,#14b8a6);color:#fff;flex-wrap:wrap;}
.tms-ti-banner strong{font-size:16px;display:block;}
.tms-ti-banner span{font-size:11px;color:rgba(255,255,255,.84);}
.tms-ti-card-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;}
.tms-ti-card{border:1px solid var(--border-color);border-radius:10px;padding:10px;background:#fff;}
.tms-ti-card .lbl{font-size:10px;color:var(--text-muted);text-transform:uppercase;font-weight:700;margin-bottom:4px;}
.tms-ti-card .val{font-size:16px;font-weight:700;color:var(--text-color);}
.tms-ti-upload{border:1.5px dashed var(--border-color);border-radius:12px;padding:16px;background:#f8fafc;}
.tms-ti-upload-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.tms-ti-columns{font-size:11px;color:var(--text-muted);padding:8px 10px;border-radius:8px;background:#f8fafc;border:1px solid var(--border-color);}
.tms-ti-preview-table{max-height:280px;overflow:auto;border:1px solid var(--border-color);border-radius:10px;}
.tms-ti-preview-table table{width:100%;border-collapse:collapse;font-size:12px;}
.tms-ti-preview-table th,.tms-ti-preview-table td{padding:8px;border-bottom:1px solid var(--border-color);vertical-align:top;}
.tms-ti-preview-table th{position:sticky;top:0;background:#f8fafc;z-index:1;}
.tms-ti-msg{font-size:12px;padding:10px 12px;border-radius:8px;}
.tms-ti-msg.ok{background:#ecfdf5;color:#166534;border:1px solid #86efac;}
.tms-ti-msg.err{background:#fef2f2;color:#991b1b;border:1px solid #fecaca;}
@media(max-width:900px){.tms-ti-card-grid{grid-template-columns:repeat(2,1fr);}}
	`;
	document.head.appendChild(style);
}

function _tms_upload_import_file(file) {
	return new Promise((resolve, reject) => {
		const fd = new FormData();
		fd.append("file", file, file.name);
		fd.append("folder", "Home/Attachments");
		fd.append("is_private", "0");
		fetch("/api/method/upload_file", {
			method: "POST",
			headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
			body: fd,
		})
		.then(r => r.json())
		.then(data => {
			if (data.exc || !data.message) {
				reject(new Error(__("File upload failed.")));
				return;
			}
			resolve(data.message);
		})
		.catch(reject);
	});
}

function _tms_render_import_preview(dialog, payload) {
	const preview = (payload && payload.preview) || {};
	const columns = preview.columns || [];
	dialog.get_field("expected_columns_html").$wrapper.html(
		columns.length
			? `<div class="tms-ti-columns"><strong>${__("Expected Columns")}:</strong> ${columns.map(col => frappe.utils.escape_html(col.csv_header)).join(", ")}</div>`
			: ""
	);

	const stats = [
		["Total Rows", preview.total_rows || 0],
		["Matched Headers", preview.matched_headers || 0],
		["Missing Headers", (preview.missing_headers || []).length],
		["Duplicate Headers", (preview.duplicate_headers || []).length],
		["Rows Ready", preview.rows_ready || 0],
		["Rows With Issues", preview.rows_with_issues || 0],
	];
	dialog.get_field("preview_summary_html").$wrapper.html(`
		<div class="tms-ti-card-grid">
			${stats.map(([label, value]) => `<div class="tms-ti-card"><div class="lbl">${__(label)}</div><div class="val">${value}</div></div>`).join("")}
		</div>
	`);

	const blocking = preview.blocking_errors || [];
	const messageHtml = blocking.length
		? `<div class="tms-ti-msg err">${blocking.map(msg => frappe.utils.escape_html(msg)).join("<br>")}</div>`
		: `<div class="tms-ti-msg ok">${__("Validation complete. Review preview rows below and click Import Data.")}</div>`;
	const rows = preview.preview_rows || [];
	const tableHtml = rows.length
		? `<div class="tms-ti-preview-table"><table><thead><tr><th>${__("Row")}</th><th>${__("Action")}</th><th>${__("Status")}</th><th>${__("Message")}</th></tr></thead><tbody>${rows.map(row => {
			const s = row.status || "";
			const rowStyle = s === "Ignored" ? "background:#f8fafc;" : "";
			const statusStyle = s === "Ready" ? "color:#166534;font-weight:700;" : s === "Issue" ? "color:#991b1b;font-weight:700;" : s === "Ignored" ? "color:#94a3b8;" : "";
			return `<tr style="${rowStyle}"><td style="${s === "Ignored" ? "color:#94a3b8;" : ""}">${row.row_number}</td><td style="${s === "Ignored" ? "color:#94a3b8;" : ""}">${frappe.utils.escape_html(row.action || "—")}</td><td><span style="${statusStyle}">${frappe.utils.escape_html(s)}</span></td><td style="${s === "Ignored" ? "color:#94a3b8;font-style:italic;" : ""}">${frappe.utils.escape_html(row.message || "")}</td></tr>`;
		}).join("")}</tbody></table></div>`
		: `<div class="text-muted">${__("No preview rows available.")}</div>`;
	dialog.get_field("preview_table_html").$wrapper.html(messageHtml + tableHtml);
	dialog._tmsImportCanRun = !!preview.can_import;
	dialog._tmsImportLogName = payload.log_name || "";
}

function _tms_render_import_result(dialog, result, listview) {
	const cards = [
		["Success Rows", result.success_rows || 0],
		["Failed Rows", result.failed_rows || 0],
		["Created", result.created_count || 0],
		["Updated", result.updated_count || 0],
	];
	const logLink = result.log_name
		? `<a href="/app/import-log/${encodeURIComponent(result.log_name)}" target="_blank">${__("View Full Log")}</a>`
		: "";
	const errorLink = result.error_file
		? `<a href="${frappe.utils.escape_html(result.error_file)}" target="_blank">${__("Download Error CSV")}</a>`
		: "";
	dialog.get_field("result_html").$wrapper.html(`
		<div class="tms-ti-card-grid" style="margin-bottom:10px;">
			${cards.map(([label, value]) => `<div class="tms-ti-card"><div class="lbl">${__(label)}</div><div class="val">${value}</div></div>`).join("")}
		</div>
		<div class="tms-ti-msg ${result.failed_rows ? "err" : "ok"}">
			${result.failed_rows ? __("Import completed with some row failures.") : __("Import completed successfully.")}
			<div style="margin-top:8px;display:flex;gap:14px;flex-wrap:wrap;">${logLink}${errorLink}</div>
		</div>
	`);
	if (listview && listview.refresh) listview.refresh();
}

function _tms_can_import_doctype(doctype) {
	return frappe.call({
		method: "logicore.logicore.doctype.import_template.import_template.can_user_import_doctype",
		args: { doctype },
	}).then(r => !!(r.message));
}

TMS.import.open_dialog = function(doctype, listview) {
	_tms_import_inject_dialog_style();
	const d = new frappe.ui.Dialog({
		title: __("{0} Import", [doctype]),
		size: "extra-large",
		fields: [
			{ fieldname: "intro_html", fieldtype: "HTML" },
			{
				fieldname: "company",
				fieldtype: "Link",
				label: __("Company"),
				options: "Company",
			},
			{
				fieldname: "old_data_import",
				fieldtype: "Check",
				label: __("Old Data Import"),
				onchange: function() {
					d.set_value("template", "");
					d.get_field("expected_columns_html").$wrapper.html("");
					d.get_field("upload_html").$wrapper.find("#tms-import-file-name").text("");
					d._tmsImportSelectedFile = null;
					d._tmsImportCanRun = false;
					d._tmsImportLogName = "";
				},
			},
			{
				fieldname: "template",
				fieldtype: "Link",
				label: __("Import Template"),
				options: "Import Template",
				reqd: 1,
				get_query: () => ({
					filters: Object.assign(
						{
							is_active: 1,
							target_doctype: doctype,
							template_name: d.get_value("old_data_import")
								? ["like", "Payroll Import Old -%"]
								: ["not like", "Payroll Import Old -%"],
						},
						d.get_value("company") ? { company: ["in", [d.get_value("company"), ""]] } : {}
					),
				}),
				onchange: async function() {
					const tpl = d.get_value("template");
					d._tmsImportCanRun = false;
					d._tmsImportLogName = "";
					d._tmsImportAction = "None";
					const modeField = d.fields_dict.import_mode;

					if (!tpl) {
						d.get_field("expected_columns_html").$wrapper.html("");
						modeField.df.read_only = 0;
						modeField.refresh();
						d.set_value("import_mode", "");
						return;
					}
					const response = await frappe.call({
						method: "logicore.logicore.doctype.import_template.import_template.get_import_template",
						args: { template_name: tpl },
					});
					const template = response.message || {};
					if (template.default_import_mode) {
						d.set_value("import_mode", template.default_import_mode);
						modeField.df.read_only = 1;
						modeField.refresh();
					}
					d._tmsImportAction = template.import_action || "None";

					const columns = template.columns || [];
					const columnsHtml = columns.length
						? `<div class="tms-ti-columns"><strong>${__("Expected Columns")}:</strong> ${columns.map(col => frappe.utils.escape_html(col.csv_header)).join(", ")}</div>`
						: "";

					let warningHtml = "";
					if (d._tmsImportAction === "Submit After Update") {
						warningHtml = `<div style="margin-top:8px;padding:10px 12px;border-radius:8px;background:#fefce8;border:1px solid #fde68a;color:#92400e;font-size:12px;">⚠️ <strong>${__("Submit After Update is enabled.")}</strong> ${__("All successfully imported records will be automatically submitted. This cannot be undone.")}</div>`;
					} else if (d._tmsImportAction === "Cancel Document") {
						warningHtml = `<div style="margin-top:8px;padding:10px 12px;border-radius:8px;background:#fef2f2;border:1px solid #fecaca;color:#991b1b;font-size:12px;">⚠️ <strong>${__("Cancel Document is enabled.")}</strong> ${__("All matched records will be cancelled. Fields will NOT be updated. This cannot be undone.")}</div>`;
					}
					d.get_field("expected_columns_html").$wrapper.html(columnsHtml + warningHtml);
				},
			},
			{
				fieldname: "import_mode",
				fieldtype: "Select",
				label: __("Import Mode"),
				options: "Update Existing Only\nCreate New Only\nUpdate or Create",
				reqd: 1,
			},
			{ fieldname: "expected_columns_html", fieldtype: "HTML" },
			{ fieldname: "upload_html", fieldtype: "HTML" },
			{ fieldname: "preview_summary_html", fieldtype: "HTML" },
			{ fieldname: "preview_table_html", fieldtype: "HTML" },
			{ fieldname: "result_html", fieldtype: "HTML" },
		],
		primary_action_label: __("Import Data"),
		primary_action: async () => {
			if (!d._tmsImportCanRun || !d._tmsImportLogName) {
				frappe.msgprint(__("Please validate the file before importing."));
				return;
			}
			const values = d.get_values();
			const response = await frappe.call({
				method: "logicore.logicore.doctype.import_log.import_log.run_import",
				args: {
					template_name: values.template,
					import_mode: values.import_mode,
					log_name: d._tmsImportLogName,
					company: values.company || "",
				},
				freeze: true,
				freeze_message: d._tmsImportAction === "Submit After Update"
					? __("Importing and submitting records...")
					: d._tmsImportAction === "Cancel Document"
						? __("Cancelling records...")
						: __("Importing records..."),
			});
			_tms_render_import_result(d, response.message || {}, listview);
		},
	});

	d.get_field("intro_html").$wrapper.html(`
		<div class="tms-ti-dialog">
			<div class="tms-ti-banner">
				<div>
					<strong>${__("{0} Import", [doctype])}</strong>
					<span>${__("Select a template, upload CSV, validate, and import without leaving the {0} list.", [doctype])}</span>
				</div>
			</div>
		</div>
	`);

	d.get_field("upload_html").$wrapper.html(`
		<div class="tms-ti-upload">
			<div class="tms-ti-upload-row">
				<input type="file" id="tms-import-file" accept=".csv,text/csv">
				<button class="btn btn-default btn-sm" id="tms-import-download">${__("Download Template")}</button>
				<button class="btn btn-primary btn-sm" id="tms-import-validate">${__("Validate File")}</button>
				<span id="tms-import-file-name" class="text-muted"></span>
			</div>
		</div>
	`);

	d._tmsImportSelectedFile = null;
	d._tmsImportCanRun = false;
	d._tmsImportLogName = "";

	// onchange for template is now defined inside the field definition above

	d.$wrapper.on("change", "#tms-import-file", function() {
		const file = this.files && this.files[0];
		d._tmsImportSelectedFile = file || null;
		d.$wrapper.find("#tms-import-file-name").text(file ? file.name : "");
		d._tmsImportCanRun = false;
		d._tmsImportLogName = "";
	});

	d.$wrapper.on("click", "#tms-import-download", function(e) {
		e.preventDefault();
		const values = d.get_values();
		if (!values || !values.template) {
			frappe.msgprint(__("Please select an import template first."));
			return;
		}
		const url = `/api/method/logicore.logicore.doctype.import_template.import_template.download_import_template?template_name=${encodeURIComponent(values.template)}`;
		window.open(url, "_blank");
	});

	d.$wrapper.on("click", "#tms-import-validate", async function(e) {
		e.preventDefault();
		const values = d.get_values();
		if (!values || !values.template || !values.import_mode) {
			frappe.msgprint(__("Please select template and import mode first."));
			return;
		}
		if (!d._tmsImportSelectedFile) {
			frappe.msgprint(__("Please choose a CSV file."));
			return;
		}
		frappe.dom.freeze(__("Uploading and validating CSV..."));
		try {
			const fileDoc = await _tms_upload_import_file(d._tmsImportSelectedFile);
			const response = await frappe.call({
				method: "logicore.logicore.doctype.import_log.import_log.upload_and_preview_import",
				args: {
					template_name: values.template,
					import_mode: values.import_mode,
					file_url: fileDoc.file_url,
					company: values.company || "",
				},
			});
			_tms_render_import_preview(d, response.message || {});
		} finally {
			frappe.dom.unfreeze();
		}
	});

	d.show();

	// Auto-fill company from user default
	const defaultCompany = frappe.defaults.get_user_defaults("company");
	if (defaultCompany) {
		const company = Array.isArray(defaultCompany) ? defaultCompany[0] : defaultCompany;
		if (company) d.set_value("company", company);
	}
};

TMS.import.setup_list_button = function(listview) {
	const doctype = listview.doctype;
	if (!frappe.model.can_create("Import Log")) return;
	const btnLabel = __("{0} Import", [doctype]);

	Promise.all([
		_tms_can_import_doctype(doctype),
		frappe.db.get_list("Import Template", {
			filters: { target_doctype: doctype, is_active: 1 },
			fields: ["name"],
			limit_page_length: 1,
		}),
	]).then(([canImport, rows]) => {
		if (!canImport) return;
		if (!rows || !rows.length) return;

		_tms_import_inject_list_btn_style();

		// add_button returns the button element directly — apply style immediately
		const $btn = listview.page.add_button(btnLabel, () => {
			TMS.import.open_dialog(doctype, listview);
		});
		$btn.addClass("tms-list-btn tms-list-btn-import").prepend("📥 ");

		// Position: next to this doctype's own Export button if it has one
		// (any doctype's list.js — genericExport or a bespoke one like Trip's —
		// tags its button .tms-list-btn-export), so every current and future
		// Import Template automatically lands there without per-doctype code.
		// Falls back to sitting immediately BEFORE the "List View" custom-btn-
		// group when there's no Export button to pair with.
		// Retried a few times: it can race against the Export button (and
		// "Report View") still being added to the same toolbar.
		const reposition = () => {
			const $export = listview.page.custom_actions.find(".tms-list-btn-export").first();
			if ($export.length) {
				$btn.insertAfter($export);
				return;
			}
			const $listViewGroup = listview.page.custom_actions
				.find(".custom-btn-group")
				.filter(function() {
					return $(this).find(".custom-btn-group-label").text().trim() === __("List View");
				}).first();
			if ($listViewGroup.length) {
				$btn.insertBefore($listViewGroup);
			}
		};
		[300, 600, 1000].forEach((ms) => setTimeout(reposition, ms));
	}).catch(() => {});
};

// Register Import button setup on all TMS doctype list views.
// For Trip, trip_list.js already wires the Import button inline —
// this registration handles all other TMS doctypes.
(function _tms_register_import_list_buttons() {
	_TMS_IMPORT_DOCTYPES.forEach(dt => {
		if (dt === "Trip") return; // Trip handled by trip_list.js
		frappe.listview_settings[dt] = frappe.listview_settings[dt] || {};
		const prevOnload = frappe.listview_settings[dt].onload;
		frappe.listview_settings[dt].onload = function(listview) {
			if (prevOnload) prevOnload.call(this, listview);
			TMS.import.setup_list_button(listview);
		};
	});
})();
