// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

function tms_import_parse_columns(value) {
	if (!value) return [];
	try {
		const rows = JSON.parse(value);
		return Array.isArray(rows) ? rows : [];
	} catch (e) {
		return [];
	}
}

function tms_import_inject_style() {
	if (document.getElementById("tms-import-template-style")) return;
	const style = document.createElement("style");
	style.id = "tms-import-template-style";
	style.textContent = `
.tms-tit-builder-note{margin:10px 0 0;font-size:11px;color:var(--text-muted);}
.tms-ti-builder{border:1px solid var(--border-color);border-radius:14px;background:#fff;overflow:hidden;box-shadow:0 4px 16px rgba(15,23,42,.04);}
.tms-ti-toolbar{display:flex;align-items:center;gap:8px;padding:12px 14px;background:linear-gradient(180deg,#f8fafc 0%,#f1f5f9 100%);border-bottom:1px solid var(--border-color);flex-wrap:wrap;}
.tms-ti-hint{font-size:11px;color:var(--text-muted);}
.tms-ti-table-wrap{overflow:auto;}
.tms-ti-table{width:100%;border-collapse:collapse;font-size:12px;}
.tms-ti-table th,.tms-ti-table td{padding:9px;border-bottom:1px solid var(--border-color);vertical-align:middle;}
.tms-ti-table th{background:#f8fafc;font-weight:800;white-space:nowrap;}
.tms-ti-table input[type="checkbox"]{width:16px;height:16px;min-width:auto;cursor:pointer;}
.tms-ti-table input[type="text"]{width:100%;height:32px;border:1px solid var(--border-color);border-radius:8px;padding:0 8px;font-size:12px;}
.tms-ti-row-actions{display:flex;justify-content:center;align-items:center;gap:4px;}
.tms-ti-combobox{position:relative;display:block;}
.tms-ti-combo-input{width:100%;min-width:160px;height:32px;border:1px solid var(--border-color);border-radius:8px;padding:0 8px;font-size:12px;box-sizing:border-box;background:#fff;font-weight:600;}
.tms-ti-combo-input:focus{border-color:var(--primary,#2490ef);outline:none;box-shadow:0 0 0 2px rgba(36,144,239,.12);}
.tms-ti-field-hint{font-size:10px;color:var(--text-muted);margin-top:2px;padding-left:2px;}
.tms-ti-combo-dropdown{display:none;position:fixed;z-index:99999;background:#fff;border:1px solid var(--border-color);border-radius:8px;max-height:220px;overflow-y:auto;min-width:240px;box-shadow:0 4px 16px rgba(15,23,42,.14);}
.tms-ti-combo-item{padding:7px 10px;cursor:pointer;font-size:12px;font-weight:500;color:var(--text-color);white-space:nowrap;}
.tms-ti-combo-item:hover,.tms-ti-combo-item.tms-ti-combo-active{background:var(--control-bg-on-focus,#e8f0fe);color:var(--primary,#2490ef);}
.tms-ti-combo-empty{padding:8px 10px;font-size:12px;color:var(--text-muted);}
.tms-ti-match-badge{display:inline-block;font-size:10px;background:#fef9c3;color:#a16207;border-radius:4px;padding:1px 6px;margin-left:6px;font-weight:700;vertical-align:middle;}
.tms-ti-table td.tms-td-center{text-align:center;}
	`;
	document.head.appendChild(style);
}

function tms_import_toggle_optional_defaults(frm) {
	frm.toggle_display("overview_html", false);
	frm.toggle_display("sample_file", false);
	frm.toggle_display("match_field", false);
}

function tms_import_toggle_import_action(frm) {
	if (!frm.doc.target_doctype) {
		frm.toggle_display("import_action", false);
		return;
	}
	// Use cached meta if available, else load
	const tryToggle = () => {
		const meta = frappe.get_meta(frm.doc.target_doctype);
		const isSubmittable = !!(meta && meta.is_submittable);
		frm.toggle_display("import_action", isSubmittable);
		if (!isSubmittable) frm.set_value("import_action", "None");
	};
	if (frappe.get_meta(frm.doc.target_doctype)) {
		tryToggle();
	} else {
		frappe.model.with_doctype(frm.doc.target_doctype, tryToggle);
	}
}

function tms_import_sync_columns(frm) {
	const rows = [];
	frm.get_field("builder_html").$wrapper.find(".tms-ti-row").each(function(index) {
		const $row = $(this);
		const fieldname = ($row.find('[data-key="fieldname"]').val() || "").trim();
		const csv_header = ($row.find('[data-key="csv_header"]').val() || "").trim();
		if (!fieldname && !csv_header) return;
		const fieldMeta = (frm._import_fields || []).find(f => f.fieldname === fieldname) || {};
		rows.push({
			idx: index + 1,
			csv_header: csv_header || fieldMeta.label || fieldname,
			fieldname,
			label: fieldMeta.label || fieldname,
			fieldtype: fieldMeta.fieldtype || "Data",
			required: $row.find('[data-key="required"]').prop("checked") ? 1 : 0,
			default_value: ($row.find('[data-key="default_value"]').val() || "").trim(),
			is_match_key: $row.find('[data-key="is_match_key"]').prop("checked") ? 1 : 0,
		});
	});
	frm.set_value("columns_json", JSON.stringify(rows, null, 2));

	// Keep match_field in sync with first match key column (backward compat)
	const firstMatchKey = rows.find(r => r.is_match_key);
	if (firstMatchKey) frm.set_value("match_field", firstMatchKey.fieldname);

	return rows;
}

function tms_import_attach_field_combobox({ fields, $comboInput, $fieldnameInput, $hint, $dropdown, onSelect }) {
	const positionDropdown = () => {
		const rect = $comboInput[0].getBoundingClientRect();
		$dropdown.css({
			top: rect.bottom + 2,
			left: rect.left,
			width: Math.max(rect.width, 240),
		});
	};

	const showDropdown = (query) => {
		const q = (query || "").toLowerCase();
		const filtered = fields.filter(f =>
			!q || f.label.toLowerCase().includes(q) || f.fieldname.toLowerCase().includes(q)
		);
		$dropdown.empty();
		if (!filtered.length) {
			$dropdown.append(`<div class="tms-ti-combo-empty">${__("No fields found")}</div>`);
		} else {
			filtered.forEach(f => {
				const $item = $(`<div class="tms-ti-combo-item" data-fieldname="${frappe.utils.escape_html(f.fieldname)}">${frappe.utils.escape_html(f.label)}</div>`);
				$item.on("mousedown", function(e) {
					e.preventDefault();
					$dropdown.hide();
					onSelect(f);
				});
				$dropdown.append($item);
			});
		}
		positionDropdown();
		$dropdown.show();
	};

	$comboInput.off(".tms_combo")
		.on("focus.tms_combo", function() { showDropdown($(this).val()); })
		.on("input.tms_combo", function() { showDropdown($(this).val()); })
		.on("blur.tms_combo", function() { setTimeout(() => $dropdown.hide(), 160); })
		.on("keydown.tms_combo", function(e) {
			const $items = $dropdown.find(".tms-ti-combo-item");
			const $active = $items.filter(".tms-ti-combo-active");
			if (e.key === "ArrowDown") {
				e.preventDefault();
				const $next = $active.length ? $active.removeClass("tms-ti-combo-active").next(".tms-ti-combo-item") : $items.first();
				$next.addClass("tms-ti-combo-active");
				$next[0] && $next[0].scrollIntoView({ block: "nearest" });
			} else if (e.key === "ArrowUp") {
				e.preventDefault();
				const $prev = $active.length ? $active.removeClass("tms-ti-combo-active").prev(".tms-ti-combo-item") : $items.last();
				$prev.addClass("tms-ti-combo-active");
				$prev[0] && $prev[0].scrollIntoView({ block: "nearest" });
			} else if (e.key === "Enter") {
				e.preventDefault();
				if ($active.length) {
					$dropdown.hide();
					const fn = $active.data("fieldname");
					const f = fields.find(x => x.fieldname === fn);
					if (f) onSelect(f);
				}
			} else if (e.key === "Escape") {
				$dropdown.hide();
			}
		});
}

function tms_import_init_row_combobox(frm, $row, initialFieldname) {
	const $comboInput = $row.find(".tms-ti-combo-input");
	const $fieldnameInput = $row.find('[data-key="fieldname"]');
	const $hint = $row.find(".tms-ti-field-hint");

	// Move dropdown to body so position:fixed works outside overflow:auto containers
	const $dropdown = $row.find(".tms-ti-combo-dropdown").detach().appendTo(document.body);

	const fields = frm._import_fields || [];

	// Pre-fill if existing column
	if (initialFieldname) {
		const meta = fields.find(f => f.fieldname === initialFieldname);
		if (meta) {
			$comboInput.val(meta.label);
			$fieldnameInput.val(meta.fieldname);
			$hint.html(`<span style="color:var(--text-muted);">${frappe.utils.escape_html(meta.fieldname)}</span>${meta.reqd ? ' <span style="color:#dc2626;">*</span>' : ""}${meta.read_only ? ' <span style="color:#f59e0b;font-size:10px;">(match key only)</span>' : ""}`);
		} else {
			// fieldname exists but not in current field list — show as-is
			$comboInput.val(initialFieldname);
			$fieldnameInput.val(initialFieldname);
			$hint.text(initialFieldname);
		}
	}

	tms_import_attach_field_combobox({
		fields,
		$comboInput,
		$fieldnameInput,
		$hint,
		$dropdown,
		onSelect(f) {
			$comboInput.val(f.label);
			$fieldnameInput.val(f.fieldname);
			// Keep the CSV header label in sync with the newly selected field —
			// otherwise it keeps whatever field's label this row was showing before,
			// which desyncs "Field Label" from "Fieldname" and can collide with
			// another row's header/fieldname on save (server throws "duplicated").
			$row.find('[data-key="csv_header"]').val(f.label);
			// Auto-check Required if field is mandatory
			if (f.reqd) $row.find('[data-key="required"]').prop("checked", true);
			// Show hint for read_only fields
			$hint.html(`<span style="color:var(--text-muted);">${frappe.utils.escape_html(f.fieldname)}</span>${f.reqd ? ' <span style="color:#dc2626;">*</span>' : ""}${f.read_only ? ' <span style="color:#f59e0b;font-size:10px;">(match key only)</span>' : ""}`);
			tms_import_sync_columns(frm);
		},
	});
}

function tms_import_cleanup_dropdowns() {
	$(".tms-ti-combo-dropdown").remove();
}

function tms_import_render_builder(frm) {
	// Clean up any previously body-appended dropdowns before re-rendering
	tms_import_cleanup_dropdowns();
	const wrapper = frm.get_field("builder_html").$wrapper;
	const rows = frm._import_columns || [];
	const targetDoctype = frm.doc.target_doctype || "Trip";

	wrapper.html(`
		<div class="tms-ti-builder">
			<div class="tms-ti-toolbar">
				<button class="btn btn-default btn-xs" data-action="add">${__("Add Column")}</button>
				<button class="btn btn-default btn-xs" data-action="reset">${__("Reset")}</button>
				<span class="tms-ti-hint">${__("Select {0} fields. Required fields auto-fill on selection.", [targetDoctype])}</span>
			</div>
			<div class="tms-ti-table-wrap">
				<table class="tms-ti-table">
					<thead>
						<tr>
							<th style="min-width:200px;">${__("Field")}</th>
							<th style="text-align:center;width:80px;">${__("Match Key")}</th>
							<th style="text-align:center;width:80px;">${__("Required")}</th>
							<th style="min-width:140px;">${__("Default Value")}</th>
							<th style="width:110px;"></th>
						</tr>
					</thead>
					<tbody class="tms-ti-rows"></tbody>
				</table>
			</div>
		</div>
		<div class="tms-tit-builder-note">${__("Mark 'Match Key' on the column(s) used to find existing records. At least one Match Key is required for Update modes.")}</div>
	`);

	const $rows = wrapper.find(".tms-ti-rows");

	const renderRow = (row = {}) => {
		const isMatchKey = row.is_match_key ? "checked" : "";
		const isRequired = row.required ? "checked" : "";
		const $row = $(`
			<tr class="tms-ti-row">
				<td>
					<div class="tms-ti-combobox">
						<input type="text" class="tms-ti-combo-input" placeholder="${__("Select field...")}" autocomplete="off">
						<input type="hidden" data-key="fieldname" value="${frappe.utils.escape_html(row.fieldname || "")}">
						<input type="hidden" data-key="csv_header" value="${frappe.utils.escape_html(row.csv_header || "")}">
						<div class="tms-ti-field-hint"></div>
						<div class="tms-ti-combo-dropdown"></div>
					</div>
				</td>
				<td class="tms-td-center"><input type="checkbox" data-key="is_match_key" ${isMatchKey}></td>
				<td class="tms-td-center"><input type="checkbox" data-key="required" ${isRequired}></td>
				<td><input type="text" data-key="default_value" value="${frappe.utils.escape_html(row.default_value || "")}" placeholder="${__("Optional")}"></td>
				<td class="tms-ti-row-actions">
					<button class="btn btn-default btn-xs" data-action="move-up" title="${__("Move Up")}">↑</button>
					<button class="btn btn-default btn-xs" data-action="move-down" title="${__("Move Down")}">↓</button>
					<button class="btn btn-default btn-xs" data-action="remove">${__("Remove")}</button>
				</td>
			</tr>
		`);
		$rows.append($row);
		tms_import_init_row_combobox(frm, $row, row.fieldname || "");
	};

	(rows.length ? rows : [{}]).forEach(renderRow);

	wrapper.off("click.tmsTi").on("click.tmsTi", "[data-action]", function() {
		const action = $(this).data("action");
		if (action === "add") {
			renderRow();
		} else if (action === "remove") {
			$(this).closest(".tms-ti-row").remove();
			if (!$rows.children().length) renderRow();
		} else if (action === "reset") {
			$rows.empty();
			renderRow();
		} else if (action === "move-up") {
			const $row = $(this).closest(".tms-ti-row");
			const $prev = $row.prev(".tms-ti-row");
			if ($prev.length) $row.insertBefore($prev);
		} else if (action === "move-down") {
			const $row = $(this).closest(".tms-ti-row");
			const $next = $row.next(".tms-ti-row");
			if ($next.length) $row.insertAfter($next);
		}
		tms_import_sync_columns(frm);
	});

	wrapper.off("change.tmsTi").on("change.tmsTi", "input[type='checkbox']", function() {
		// Match Key checked → auto-check Required
		if ($(this).data("key") === "is_match_key" && $(this).prop("checked")) {
			$(this).closest(".tms-ti-row").find('[data-key="required"]').prop("checked", true);
		}
		tms_import_sync_columns(frm);
	});

	wrapper.off("input.tmsTi").on("input.tmsTi", "input[data-key='default_value']", function() {
		tms_import_sync_columns(frm);
	});
}

async function tms_import_load_fields(frm, doctype) {
	frm._import_fields = null;
	const r = await frappe.call({
		method: "logicore.logicore.doctype.import_template.import_template.get_importable_fields",
		args: { doctype: doctype || frm.doc.target_doctype || "Trip" },
	});
	frm._import_fields = r.message || [];
}

// Mandatory doctype fields must always have a column — if the user reassigns
// or removes the row that carried one, re-add it so it can never disappear
// from the template (only matters for modes that create new documents).
function tms_import_ensure_mandatory_columns(frm, { notify = false } = {}) {
	const mode = frm.doc.default_import_mode;
	if (mode !== "Create New Only" && mode !== "Update or Create") return [];

	const allFields = frm._import_fields || [];
	const mandatoryFieldnames = new Set(allFields.filter(f => f.reqd).map(f => f.fieldname));
	if (!mandatoryFieldnames.size) return [];

	const currentCols = tms_import_sync_columns(frm);
	const existing = new Set(currentCols.map(c => c.fieldname));

	const toAdd = [...mandatoryFieldnames]
		.filter(fn => !existing.has(fn))
		.map(fn => allFields.find(f => f.fieldname === fn))
		.filter(Boolean);

	if (!toAdd.length) return [];

	frm._import_columns = [
		...currentCols,
		...toAdd.map(f => ({
			csv_header: f.label,
			fieldname: f.fieldname,
			fieldtype: f.fieldtype,
			label: f.label,
			required: 1,
			default_value: "",
			is_match_key: 0,
		})),
	];
	tms_import_render_builder(frm);
	tms_import_sync_columns(frm);

	// Showing frappe.msgprint() here (mid-save) races with the form's
	// post-save refresh and can render an empty dialog body — the caller
	// decides when/how to surface `toAdd` (e.g. after_save) instead.
	if (notify) {
		frappe.msgprint({
			title: __("Mandatory Columns Added"),
			message: __("The following required columns were added automatically: <b>{0}</b>", [toAdd.map(f => f.label).join(", ")]),
			indicator: "blue",
		});
	}
	return toAdd;
}

function tms_import_show_run_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Upload & Run Import — {0}", [frm.doc.template_name]),
		fields: [
			{
				fieldname: "uploaded_file",
				fieldtype: "Attach",
				label: __("CSV File"),
				reqd: 1,
			},
			{
				fieldname: "import_mode",
				fieldtype: "Select",
				label: __("Import Mode"),
				options: ["Update Existing Only", "Create New Only", "Update or Create"].join("\n"),
				default: frm.doc.default_import_mode || "Create New Only",
				reqd: 1,
			},
		],
		primary_action_label: __("Run Import"),
		primary_action(values) {
			dialog.set_df_property("uploaded_file", "read_only", 1);
			dialog.get_primary_btn().prop("disabled", true).text(__("Running..."));
			frappe.call({
				method: "logicore.logicore.doctype.import_log.import_log.run_import",
				args: {
					template_name: frm.doc.name,
					import_mode: values.import_mode,
					file_url: values.uploaded_file,
					company: frm.doc.company,
				},
				callback(r) {
					dialog.hide();
					const summary = r.message || {};
					if (summary.log_name) {
						frappe.set_route("Form", "Import Log", summary.log_name);
					}
					frappe.msgprint({
						title: __("Import Finished"),
						message: __("Created: {0}, Updated: {1}, Failed: {2}", [
							summary.created_count ?? 0,
							summary.updated_count ?? 0,
							summary.failed_rows ?? 0,
						]),
						indicator: summary.failed_rows ? "orange" : "green",
					});
				},
				error() {
					dialog.set_df_property("uploaded_file", "read_only", 0);
					dialog.get_primary_btn().prop("disabled", false).text(__("Run Import"));
				},
			});
		},
	});
	dialog.show();
}

frappe.ui.form.on("Import Template", {
	async refresh(frm) {
		tms_import_inject_style();
		tms_import_toggle_optional_defaults(frm);

		if (!frm.is_new()) {
			frm.set_df_property("template_name", "hidden", 0);
			frm.refresh_field("template_name");
		}

		// Filter target_doctype to show only curated importable TMS doctypes
		if (!frm._tms_importable_doctypes) {
			const r = await frappe.call({
				method: "logicore.logicore.doctype.import_template.import_template.get_tms_importable_doctypes",
			});
			frm._tms_importable_doctypes = r.message || [];
		}
		frm.set_query("target_doctype", () => ({
			filters: { name: ["in", frm._tms_importable_doctypes] },
		}));

		// Load fields for the currently selected doctype
		if (!frm._import_fields || frm._import_last_doctype !== (frm.doc.target_doctype || "Trip")) {
			await tms_import_load_fields(frm, frm.doc.target_doctype || "Trip");
			frm._import_last_doctype = frm.doc.target_doctype || "Trip";
		}

		frm._import_columns = tms_import_parse_columns(frm.doc.columns_json);

		// Backward compat: old columns_json has no is_match_key → auto-mark match_field column
		const hasAnyMatchKey = (frm._import_columns || []).some(c => c.is_match_key);
		if (!hasAnyMatchKey && frm.doc.match_field) {
			(frm._import_columns || []).forEach(c => {
				if (c.fieldname === frm.doc.match_field) c.is_match_key = 1;
			});
		}

		tms_import_toggle_import_action(frm);
		tms_import_render_builder(frm);
		tms_import_ensure_mandatory_columns(frm);

		if (!frm.is_new()) {
			frm.add_custom_button(__("Download Template CSV"), () => {
				const url = `/api/method/logicore.logicore.doctype.import_template.import_template.download_import_template?template_name=${encodeURIComponent(frm.doc.name)}`;
				window.open(url, "_blank");
			});
			frm.add_custom_button(__("Preview Columns"), () => {
				const rows = tms_import_sync_columns(frm);
				const body = rows.length
					? `<div style="max-height:320px;overflow:auto;"><table class="table table-bordered"><thead><tr><th>#</th><th>${__("Field Label")}</th><th>${__("Fieldname")}</th><th>${__("Type")}</th><th>${__("Match Key")}</th><th>${__("Required")}</th></tr></thead><tbody>${rows.map((row, i) => `<tr><td>${i + 1}</td><td>${frappe.utils.escape_html(row.csv_header)}</td><td>${frappe.utils.escape_html(row.fieldname)}</td><td>${frappe.utils.escape_html(row.fieldtype)}</td><td>${row.is_match_key ? "✓" : ""}</td><td>${row.required ? "✓" : ""}</td></tr>`).join("")}</tbody></table></div>`
					: `<div class="text-muted">${__("No columns configured yet.")}</div>`;
				frappe.msgprint({ title: __("Template Columns"), message: body });
			});

			// Gate visibility on the same "import" permission bit TMS User Group
			// already syncs into Custom DocPerm for the target doctype — do not
			// show an upload/run entry point the user isn't allowed to use.
			if (frappe.perm.has_perm(frm.doc.target_doctype, 0, "import")) {
				frm.add_custom_button(__(frm.doc.template_name), () => {
					tms_import_show_run_dialog(frm);
				}).addClass("btn-primary");
			}
		}
	},

	async target_doctype(frm) {
		if (!frm.doc.target_doctype) return;
		if (frm._import_last_doctype === frm.doc.target_doctype) return;

		// Clear existing columns when doctype changes
		frm._import_columns = [];
		frm.set_value("columns_json", "[]");
		frm.set_value("match_field", "");

		await tms_import_load_fields(frm, frm.doc.target_doctype);
		frm._import_last_doctype = frm.doc.target_doctype;

		tms_import_toggle_import_action(frm);
		tms_import_render_builder(frm);
		tms_import_ensure_mandatory_columns(frm);
	},

	default_import_mode(frm) {
		tms_import_toggle_optional_defaults(frm);
		tms_import_ensure_mandatory_columns(frm, { notify: true });
	},

	before_save(frm) {
		// Silent here — the doc isn't saved yet, and a mid-save dialog races
		// with the post-save refresh. Stash the labels and notify in after_save.
		const added = tms_import_ensure_mandatory_columns(frm);
		frm._tms_mandatory_added_labels = added.map(f => f.label);

		const rows = tms_import_sync_columns(frm);
		frm._import_columns = rows;

		// Validate: no duplicate fieldnames
		const seen = new Set();
		for (const row of rows) {
			if (!row.fieldname) continue;
			if (seen.has(row.fieldname)) {
				frappe.throw(__("Column '{0}' is added more than once. Each field can only appear once.", [row.csv_header || row.fieldname]));
			}
			seen.add(row.fieldname);
		}

		// Validate: Update modes must have at least one match key
		const mode = frm.doc.default_import_mode;
		if (["Update Existing Only", "Update or Create"].includes(mode)) {
			const matchKeys = rows.filter(r => r.is_match_key);
			if (!matchKeys.length) {
				frappe.throw(__("At least one column must be marked as 'Match Key' for Update modes."));
			}
		}
	},

	after_save(frm) {
		const labels = frm._tms_mandatory_added_labels;
		frm._tms_mandatory_added_labels = null;
		if (!labels || !labels.length) return;
		frappe.msgprint({
			title: __("Mandatory Columns Added"),
			message: __("The following required columns were added automatically: <b>{0}</b>", [labels.join(", ")]),
			indicator: "blue",
		});
	},
});
