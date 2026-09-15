// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

const TMS_TRIP_IMPORT_SKIP_FIELDS = new Set(["name"]);

function tms_trip_import_parse_columns(value) {
	if (!value) return [];
	try {
		const rows = JSON.parse(value);
		return Array.isArray(rows) ? rows : [];
	} catch (e) {
		return [];
	}
}

function tms_trip_import_inject_style() {
	if (document.getElementById("tms-trip-import-template-style")) return;
	const style = document.createElement("style");
	style.id = "tms-trip-import-template-style";
	style.textContent = `
.tms-tit-builder-note{margin:10px 0 0;font-size:11px;color:var(--text-muted);}
.tms-ti-builder{border:1px solid var(--border-color);border-radius:14px;background:#fff;overflow:hidden;box-shadow:0 4px 16px rgba(15,23,42,.04);}
.tms-ti-toolbar{display:flex;align-items:center;gap:8px;padding:12px 14px;background:linear-gradient(180deg,#f8fafc 0%,#f1f5f9 100%);border-bottom:1px solid var(--border-color);flex-wrap:wrap;}
.tms-ti-hint{font-size:11px;color:var(--text-muted);}
.tms-ti-table-wrap{overflow:auto;}
.tms-ti-table{width:100%;border-collapse:collapse;font-size:12px;}
.tms-ti-table th,.tms-ti-table td{padding:9px;border-bottom:1px solid var(--border-color);vertical-align:top;}
.tms-ti-table th{background:#f8fafc;font-weight:800;white-space:nowrap;}
.tms-ti-table input,.tms-ti-table select{width:100%;min-width:120px;height:32px;border:1px solid var(--border-color);border-radius:8px;padding:0 8px;font-size:12px;}
.tms-ti-table input[type="checkbox"]{width:16px;height:16px;min-width:auto;margin-top:6px;}
.tms-ti-row-actions{display:flex;justify-content:center;align-items:center;gap:4px;}
.tms-ti-table input[data-key="csv_header"]{font-weight:700;}
.tms-ti-combobox{position:relative;display:block;}
.tms-ti-combo-input{width:100%;min-width:120px;height:32px;border:1px solid var(--border-color);border-radius:8px;padding:0 8px;font-size:12px;box-sizing:border-box;background:#fff;}
.tms-ti-combo-input:focus{border-color:var(--primary,#2490ef);outline:none;}
.tms-ti-combo-dropdown{display:none;position:absolute;z-index:9999;background:#fff;border:1px solid var(--border-color);border-radius:8px;max-height:200px;overflow-y:auto;min-width:220px;width:100%;bottom:calc(100% + 2px);top:auto;left:0;box-shadow:0 -4px 16px rgba(15,23,42,.14);}
.tms-ti-combo-dropdown.tms-drop-down{bottom:auto;top:calc(100% + 2px);box-shadow:0 4px 16px rgba(15,23,42,.14);}
.tms-ti-combo-item{padding:7px 10px;cursor:pointer;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.tms-ti-combo-item:hover,.tms-ti-combo-item.tms-ti-combo-active{background:var(--control-bg-on-focus,#e8f0fe);color:var(--primary,#2490ef);}
.tms-ti-combo-empty{padding:7px 10px;font-size:12px;color:var(--text-muted);}
	`;
	document.head.appendChild(style);
}

function tms_trip_import_toggle_optional_defaults(frm) {
	frm.toggle_display("overview_html", false);
	frm.toggle_display("sample_file", false);
}

function tms_trip_import_sync_columns(frm) {
	const rows = [];
	frm.get_field("builder_html").$wrapper.find(".tms-ti-row").each(function(index) {
		const $row = $(this);
		const csv_header = ($row.find('[data-key="csv_header"]').val() || "").trim();
		const fieldname = ($row.find('[data-key="fieldname"]').val() || "").trim();
		if (!csv_header && !fieldname) return;
		const fieldMeta = (frm._trip_import_fields || []).find(f => f.fieldname === fieldname) || {};
		rows.push({
			idx: index + 1,
			csv_header,
			fieldname,
			label: fieldMeta.label || fieldname,
			fieldtype: fieldMeta.fieldtype || "Data",
			required: $row.find('[data-key="required"]').prop("checked") ? 1 : 0,
			default_value: $row.find('[data-key="default_value"]').val() || "",
		});
	});
	frm.set_value("columns_json", JSON.stringify(rows, null, 2));
	return rows;
}

function tms_trip_import_attach_combobox({ fields, $input, $dropdown, skipFields, onSelect }) {
	const showDropdown = (query) => {
		const q = (query || "").toLowerCase();
		const filtered = fields.filter(f =>
			(!skipFields || !skipFields.has(f.fieldname)) &&
			(!q || f.label.toLowerCase().includes(q) || f.fieldname.toLowerCase().includes(q))
		);
		$dropdown.empty();
		if (!filtered.length) {
			$dropdown.append(`<div class="tms-ti-combo-empty">${__("No fields found")}</div>`);
		} else {
			filtered.forEach(f => {
				const $item = $(`<div class="tms-ti-combo-item" data-fieldname="${frappe.utils.escape_html(f.fieldname)}">${frappe.utils.escape_html(f.label)} <span style="color:var(--text-muted);font-size:11px;">(${frappe.utils.escape_html(f.fieldname)})</span></div>`);
				$item.on("mousedown", function(e) {
					e.preventDefault();
					$dropdown.hide();
					onSelect(f.fieldname);
				});
				$dropdown.append($item);
			});
		}
		$dropdown.show();
	};

	$input.off(".tms_combo").on("focus.tms_combo", function() {
		showDropdown($(this).val());
	}).on("input.tms_combo", function() {
		showDropdown($(this).val());
	}).on("blur.tms_combo", function() {
		setTimeout(() => $dropdown.hide(), 150);
	}).on("keydown.tms_combo", function(e) {
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
				onSelect($active.data("fieldname"));
			}
		} else if (e.key === "Escape") {
			$dropdown.hide();
		}
	});
}

function tms_trip_import_init_combobox(frm, $row, initialFieldname) {
	const $input = $row.find(".tms-ti-combo-input");
	const $dropdown = $row.find(".tms-ti-combo-dropdown");
	tms_trip_import_attach_combobox({
		fields: frm._trip_import_fields || [],
		$input,
		$dropdown,
		skipFields: new Set([...TMS_TRIP_IMPORT_SKIP_FIELDS].filter(fn => fn !== frm.doc.match_field)),
		onSelect(fieldname) {
			$input.val(fieldname).trigger("change");
		},
	});
	if (initialFieldname) $input.val(initialFieldname);
}

function tms_trip_import_enhance_match_field(frm) {
	setTimeout(() => {
		const field = frm.get_field("match_field");
		if (!field || !field.$input) return;
		const $input = field.$input;
		$input.siblings(".tms-match-dropdown").remove();
		const $dropdown = $('<div class="tms-ti-combo-dropdown tms-drop-down tms-match-dropdown"></div>');
		$input.parent().css("position", "relative").append($dropdown);
		tms_trip_import_attach_combobox({
			fields: frm._trip_import_fields || [],
			$input,
			$dropdown,
			skipFields: null,
			onSelect(fieldname) {
				frm.set_value("match_field", fieldname);
				$dropdown.hide();
			},
		});
	}, 300);
}

function tms_trip_import_render_builder(frm) {
	const wrapper = frm.get_field("builder_html").$wrapper;
	const rows = frm._trip_import_columns || [];
	const fieldOptions = (frm._trip_import_fields || [])
		.filter(f => !TMS_TRIP_IMPORT_SKIP_FIELDS.has(f.fieldname) || f.fieldname === frm.doc.match_field)
		.map(f => `<option value="${frappe.utils.escape_html(f.fieldname)}">${frappe.utils.escape_html(f.label)} (${frappe.utils.escape_html(f.fieldname)})</option>`)
		.join("");

	wrapper.html(`
		<div class="tms-ti-builder">
			<div class="tms-ti-toolbar">
				<button class="btn btn-default btn-xs" data-action="add">${__("Add Column")}</button>
				<button class="btn btn-default btn-xs" data-action="reset">${__("Reset")}</button>
				<span class="tms-ti-hint">${__("Build CSV headers and map them to Trip fields.")}</span>
			</div>
			<div class="tms-ti-table-wrap">
				<table class="tms-ti-table">
					<thead>
						<tr>
							<th>${__("CSV Header")}</th>
							<th>${__("Trip Field")}</th>
							<th>${__("Required")}</th>
							<th>${__("Default Value")}</th>
							<th></th>
						</tr>
					</thead>
					<tbody class="tms-ti-rows"></tbody>
				</table>
			</div>
		</div>
		<div class="tms-tit-builder-note">${__("Keep CSV Header user-friendly, and select the exact Trip field that should receive the value during import.")}</div>
	`);

	const $rows = wrapper.find(".tms-ti-rows");
	const renderRow = (row = {}) => {
		const $row = $(`
			<tr class="tms-ti-row">
				<td><input type="text" data-key="csv_header" value="${frappe.utils.escape_html(row.csv_header || "")}"></td>
				<td>
					<div class="tms-ti-combobox">
						<input type="text" class="tms-ti-combo-input" data-key="fieldname" placeholder="${__("Type or select field...")}" autocomplete="off">
						<div class="tms-ti-combo-dropdown"></div>
					</div>
				</td>
				<td><input type="checkbox" data-key="required" ${row.required ? "checked" : ""}></td>
				<td><input type="text" data-key="default_value" value="${frappe.utils.escape_html(row.default_value || "")}"></td>
				<td class="tms-ti-row-actions">
				<button class="btn btn-default btn-xs" data-action="move-up" title="${__("Move Up")}">↑</button>
				<button class="btn btn-default btn-xs" data-action="move-down" title="${__("Move Down")}">↓</button>
				<button class="btn btn-default btn-xs" data-action="remove">${__("Remove")}</button>
			</td>
			</tr>
		`);
		$rows.append($row);
		tms_trip_import_init_combobox(frm, $row, row.fieldname || "");
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
		tms_trip_import_sync_columns(frm);
	});

	wrapper.off("change.tmsTi").on("change.tmsTi", "input", function() {
		tms_trip_import_sync_columns(frm);
	});
}

frappe.ui.form.on("Trip Import Template", {
	async refresh(frm) {
		tms_trip_import_inject_style();
		if (!frm._trip_import_fields) {
			const r = await frappe.call({
				method: "logicore.logicore.doctype.trip_import_template.trip_import_template.get_trip_importable_trip_fields",
			});
			frm._trip_import_fields = r.message || [];
		}
		frm.set_df_property(
			"match_field",
			"options",
			(frm._trip_import_fields || []).map(f => f.fieldname).join("\n")
		);
		tms_trip_import_toggle_optional_defaults(frm);
		frm._trip_import_columns = tms_trip_import_parse_columns(frm.doc.columns_json);
		tms_trip_import_render_builder(frm);
		tms_trip_import_enhance_match_field(frm);

		if (!frm.is_new()) {
			frm.add_custom_button(__("Download Template CSV"), () => {
				const url = `/api/method/logicore.logicore.doctype.trip_import_template.trip_import_template.download_trip_import_template?template_name=${encodeURIComponent(frm.doc.name)}`;
				window.open(url, "_blank");
			});
			frm.add_custom_button(__("Preview Columns"), () => {
				const rows = tms_trip_import_sync_columns(frm);
				const body = rows.length
					? `<div style="max-height:320px;overflow:auto;"><table class="table table-bordered"><thead><tr><th>#</th><th>${__("Header")}</th><th>${__("Field")}</th><th>${__("Type")}</th><th>${__("Required")}</th></tr></thead><tbody>${rows.map((row, index) => `<tr><td>${index + 1}</td><td>${frappe.utils.escape_html(row.csv_header)}</td><td>${frappe.utils.escape_html(row.fieldname)}</td><td>${frappe.utils.escape_html(row.fieldtype)}</td><td>${row.required ? "Yes" : "No"}</td></tr>`).join("")}</tbody></table></div>`
					: `<div class="text-muted">${__("No columns configured yet.")}</div>`;
				frappe.msgprint({ title: __("Template Columns"), message: body });
			});
		}
	},

	default_import_mode(frm) {
		tms_trip_import_toggle_optional_defaults(frm);

		const mode = frm.doc.default_import_mode;
		if (mode !== "Create New Only" && mode !== "Update or Create") return;

		const allFields = frm._trip_import_fields || [];
		const mandatoryFieldnames = new Set(
			allFields.filter(f => f.reqd).map(f => f.fieldname)
		);

		// match field column bhi zaruri hai create mode mein
		if (frm.doc.match_field) mandatoryFieldnames.add(frm.doc.match_field);

		const currentCols = tms_trip_import_sync_columns(frm);
		const existing = new Set(currentCols.map(c => c.fieldname));

		const toAdd = [...mandatoryFieldnames]
			.filter(fn => !existing.has(fn))
			.map(fn => allFields.find(f => f.fieldname === fn))
			.filter(Boolean);

		if (!toAdd.length) return;

		frm._trip_import_columns = [
			...currentCols,
			...toAdd.map(f => ({
				csv_header: f.label,
				fieldname: f.fieldname,
				fieldtype: f.fieldtype,
				label: f.label,
				required: 1,
				default_value: "",
			})),
		];
		tms_trip_import_render_builder(frm);
		tms_trip_import_sync_columns(frm);

		frappe.msgprint({
			title: __("Mandatory Columns Added"),
			message: __(
				"The following required columns were added automatically: <b>{0}</b>",
				[toAdd.map(f => f.label).join(", ")]
			),
			indicator: "blue",
		});
	},

	before_save(frm) {
		const rows = tms_trip_import_sync_columns(frm);
		frm._trip_import_columns = rows;
	},
});
