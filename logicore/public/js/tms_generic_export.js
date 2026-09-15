window.TMS = window.TMS || {};

// Shared implementation behind every non-Trip/Amazon-Trip doctype's "<DocType> Export"
// button. Loaded globally (app_include_js) but does NOT patch any Frappe core class —
// each eligible doctype's own tiny "<name>_list.js" (inside its doctype folder, same
// convention Trip/Amazon Trip use for their own export buttons) calls
// `TMS.genericExport.attach(listview)` from `frappe.listview_settings[doctype].onload`,
// which is the exact same lifecycle point Trip's own onload runs from — so the button
// always lands first/leftmost in the toolbar, before the Report View toggle, exactly
// like Trip's.
(function () {
	const SKIP_FIELDS = new Set([
		"amended_from", "docstatus", "doctype", "owner", "creation", "modified",
		"modified_by", "idx", "_assign", "_comments", "_user_tags", "workflow_state",
	]);
	const SKIP_FIELDTYPES = new Set([
		"Section Break", "Column Break", "Tab Break", "Fold",
		"Heading", "HTML", "Button", "Image", "Attach Image",
		"Signature", "Geolocation", "Barcode", "Break", "Table", "Table MultiSelect",
	]);
	const FILTERABLE_FIELDTYPES = new Set([
		"Link", "Select", "Data", "Date", "Datetime", "Int", "Float", "Currency",
	]);
	const MAX_FILTER_FIELDS = 8;

	// Explicit, doctype-scoped exceptions for fields whose real form visibility is
	// driven by hand-written JS (frm.set_df_property in that doctype's own <name>.js),
	// not declared depends_on metadata — so the generic depends_on-based column
	// narrowing below can't see them on its own. Add entries here only when a user
	// explicitly asks for a specific doctype's custom-JS-driven fields to narrow too;
	// everything else in this feature stays fully generic/doctype-agnostic.
	const FIELD_VISIBILITY_OVERRIDES = {
		// payment.js: toggle_trip_section/toggle_trip_detail_fields hide this whole
		// group when Payment Type is Office/Other Expense, Employee Advance, Driver
		// Advance, or Vehicle Finance EMI (no trip is linked for those types).
		Payment: (() => {
			const NO_TRIP_TYPES = ["Office/Other Expense", "Employee Advance", "Driver Advance", "Vehicle Finance EMI"];
			const fn = (doc) => !NO_TRIP_TYPES.includes(doc.type);
			return {
				trip_no: fn,
				trip_tcn_no: fn,
				trip_date: fn,
				trip_type: fn,
				trip_origin: fn,
				trip_destination: fn,
				trip_vehicle_type: fn,
			};
		})(),
	};

	// Doctype-scoped fields dropped from the export column picker unconditionally —
	// unlike FIELD_VISIBILITY_OVERRIDES (which only narrows once a filter value is
	// picked), these never appear regardless of filters.
	const DOCTYPE_EXPORT_EXCLUDE = {
		"Tyre Expenses": new Set([
			// tyre_expenses.js toggle_removal_fields() gates this whole section on
			// frm.doc.status, but Tyre Expenses declares no "status" field — the
			// check is always false, so the section never renders on the form.
			"removal_date", "removal_odometer", "removal_reason", "km_run", "cost_per_km",
			// Aggregate totals — not useful as export columns.
			"total_qty", "total_cost",
		]),
	};

	function inject_css() {
		if (document.getElementById("tms-generic-export-style")) return;
		const s = document.createElement("style");
		s.id = "tms-generic-export-style";
		s.innerHTML = `
.tms-list-btn.tms-list-btn-export.btn,
.tms-list-btn.tms-list-btn-export.btn.btn-default,
.tms-list-btn.tms-list-btn-export.btn.btn-default:hover,
.tms-list-btn.tms-list-btn-export.btn.btn-default:focus {
	background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%) !important;
	color: #fff !important;
}
.tms-gexp-col-tbody tr { border-bottom: 1px solid var(--border-color); }
`;
		document.head.appendChild(s);
	}

	function plain_fields(meta, doctype) {
		const overrides = FIELD_VISIBILITY_OVERRIDES[doctype] || {};
		const excluded = DOCTYPE_EXPORT_EXCLUDE[doctype] || new Set();
		const columns = [];
		if (meta && meta.fields) {
			meta.fields.forEach((field) => {
				if (
					!field.hidden &&
					!SKIP_FIELDS.has(field.fieldname) &&
					!SKIP_FIELDTYPES.has(field.fieldtype) &&
					!excluded.has(field.fieldname) &&
					field.label
				) {
					columns.push({
						fieldname: field.fieldname,
						label: field.label,
						checked: field.fieldname === "name" || !!field.reqd,
						depends_on: overrides[field.fieldname] || field.depends_on || null,
					});
				}
			});
		}
		return columns;
	}

	// Every field on the doctype, except hidden fields, system/meta fields, and
	// layout fieldtypes — matches Trip/Amazon Trip's own export column list, which
	// also offers every field, not just the ones visible in the list view. Child
	// table fields are also offered, prefixed "<table_fieldname>.<child_fieldname>",
	// so they can be picked and exported as flattened rows (same as Amazon Trip's
	// own Amazon Trip Detail flattening). If a child doctype's meta isn't loaded
	// client-side yet, its columns are silently skipped from the picker (export
	// itself is unaffected — this only limits what shows in the dialog).
	function get_export_columns(doctype) {
		const meta = frappe.get_meta(doctype);
		if (!meta) return [];
		const columns = plain_fields(meta, doctype);

		(meta.fields || []).forEach((field) => {
			if (field.fieldtype !== "Table" || !field.options) return;
			const childMeta = frappe.get_meta(field.options);
			if (!childMeta) return;
			plain_fields(childMeta, field.options).forEach((childCol) => {
				columns.push({
					fieldname: `${field.fieldname}.${childCol.fieldname}`,
					label: `${field.label} - ${childCol.label}`,
					checked: false,
					depends_on: null,
				});
			});
		});

		return columns;
	}

	// Mirrors frappe.ui.form.Layout#evaluate_depends_on_value, standalone (no Layout/form
	// instance needed) — used to narrow the column list to only the fields relevant to
	// the currently-picked filter values, same way a form only shows fields relevant to
	// what's already been filled in. Fields with no depends_on always stay visible.
	function evaluate_depends_on(expression, doc) {
		if (!expression) return true;
		if (typeof expression === "boolean") return expression;
		if (typeof expression === "function") {
			try {
				return !!expression(doc);
			} catch (e) {
				console.error("TMS generic export: depends_on function failed:", e);
				return true;
			}
		}
		if (expression.substr(0, 5) === "eval:") {
			try {
				return !!frappe.utils.eval(expression.substr(5), { doc, parent: doc });
			} catch (e) {
				console.error("TMS generic export: depends_on eval failed:", expression, e);
				return true; // can't evaluate safely — fail-open, keep the column visible
			}
		}
		if (expression.substr(0, 3) === "fn:") return true; // form-script trigger — can't evaluate generically
		const value = doc[expression];
		if (Array.isArray(value)) return !!value.length;
		return !!value;
	}

	// Dynamic filter section, built from the doctype's own meta — mirrors Trip's
	// dedicated filter grid, but generic: fields flagged in_standard_filter (falling
	// back to in_list_view fields) become dialog inputs; Date/Datetime fields become
	// a From/To pair, matching Trip's date_from/date_to convention.
	function build_filter_defs(doctype) {
		const meta = frappe.get_meta(doctype);
		if (!meta || !meta.fields) return [];

		const usable = (f) =>
			FILTERABLE_FIELDTYPES.has(f.fieldtype) &&
			!f.hidden &&
			!SKIP_FIELDS.has(f.fieldname) &&
			f.label;

		let candidates = meta.fields.filter((f) => f.in_standard_filter && usable(f));
		if (candidates.length < 3) {
			const seen = new Set(candidates.map((f) => f.fieldname));
			meta.fields
				.filter((f) => f.in_list_view && usable(f) && !seen.has(f.fieldname))
				.forEach((f) => candidates.push(f));
		}
		candidates = candidates.slice(0, MAX_FILTER_FIELDS);

		const defs = [];
		candidates.forEach((df) => {
			if (df.fieldtype === "Date" || df.fieldtype === "Datetime") {
				defs.push({
					source_fieldname: df.fieldname,
					operator: ">=",
					dialog_field: {
						fieldname: `${df.fieldname}_from`,
						label: __("{0} From", [__(df.label, null, doctype)]),
						fieldtype: df.fieldtype,
					},
				});
				defs.push({
					source_fieldname: df.fieldname,
					operator: "<=",
					dialog_field: {
						fieldname: `${df.fieldname}_to`,
						label: __("{0} To", [__(df.label, null, doctype)]),
						fieldtype: df.fieldtype,
					},
				});
			} else {
				defs.push({
					source_fieldname: df.fieldname,
					operator: df.fieldtype === "Data" ? "like" : "=",
					dialog_field: {
						fieldname: df.fieldname,
						label: __(df.label, null, doctype),
						fieldtype: df.fieldtype,
						options: df.options,
					},
				});
			}
		});
		return defs;
	}

	function build_col_table($wrapper, columns) {
		$wrapper.html(`
<div style="margin:4px 0 0;">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
    <label style="display:flex;align-items:center;gap:6px;font-weight:600;cursor:pointer;font-size:12px;">
      <input type="checkbox" class="tms-gexp-select-all" style="width:14px;height:14px;">
      ${__("Select All")}
    </label>
  </div>
  <div style="max-height:320px;overflow:auto;border:1px solid var(--border-color);border-radius:6px;">
    <table style="width:100%;min-width:420px;border-collapse:collapse;font-size:clamp(11px,1.5vw,12px);">
      <thead>
        <tr style="background:var(--subtle-fg,#f3f4f6);position:sticky;top:0;z-index:1;">
          <th style="width:44px;padding:8px 6px;text-align:center;border-bottom:2px solid var(--border-color);font-weight:700;">${__("No")}</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid var(--border-color);font-weight:700;">${__("Column Name")}</th>
          <th style="width:60px;padding:8px 6px;text-align:center;border-bottom:2px solid var(--border-color);font-weight:700;">${__("Select")}</th>
          <th style="width:120px;padding:8px 6px;text-align:center;border-bottom:2px solid var(--border-color);font-weight:700;">#</th>
        </tr>
      </thead>
      <tbody class="tms-gexp-col-tbody"></tbody>
    </table>
  </div>
</div>`);

		const $tbody = $wrapper.find(".tms-gexp-col-tbody");
		const $selectAll = $wrapper.find(".tms-gexp-select-all");

		// Columns hidden by depends_on filtering (col.visible === false) are skipped
		// from render entirely, but stay in `columns` so they can reappear if the
		// filter that hid them changes again.
		function visibleColumns() {
			return columns.filter((c) => c.visible !== false);
		}

		function syncSelectAll() {
			const visible = visibleColumns();
			const total = visible.length;
			const checked = visible.filter((c) => c.checked).length;
			$selectAll.prop("checked", total > 0 && checked === total);
			$selectAll.prop("indeterminate", checked > 0 && checked < total);
		}

		function renderRows() {
			$tbody.empty();
			const visible = visibleColumns();
			visible.forEach((col, idx) => {
				$tbody.append(`
<tr data-fieldname="${col.fieldname}">
  <td style="text-align:center;padding:8px 4px;color:var(--text-muted);font-size:11px;">${idx + 1}</td>
  <td style="padding:8px 10px;font-size:12px;">${col.label}</td>
  <td style="text-align:center;padding:8px 4px;">
    <input type="checkbox" class="tms-gexp-col-check" style="width:16px;height:16px;cursor:pointer;" ${col.checked ? "checked" : ""}>
  </td>
  <td style="text-align:center;padding:6px 4px;white-space:nowrap;">
    <button class="btn btn-xs btn-default tms-gexp-col-up" style="padding:4px 6px;margin-right:2px;background:#1e293b;color:#fff;border:none;" ${idx === 0 ? "disabled" : ""}>&#8593; Up</button>
    <button class="btn btn-xs btn-default tms-gexp-col-down" style="padding:4px 6px;background:#1e293b;color:#fff;border:none;" ${idx === visible.length - 1 ? "disabled" : ""}>&#8595; Down</button>
  </td>
</tr>`);
			});
			syncSelectAll();
		}

		$selectAll.on("change", function () {
			const v = this.checked;
			visibleColumns().forEach((c) => (c.checked = v));
			$tbody.find(".tms-gexp-col-check").prop("checked", v);
			$selectAll.prop("indeterminate", false);
		});

		$tbody.on("change", ".tms-gexp-col-check", function () {
			const fn = $(this).closest("tr").data("fieldname");
			const col = columns.find((c) => c.fieldname === fn);
			if (col) col.checked = this.checked;
			syncSelectAll();
		});

		$tbody.on("click", ".tms-gexp-col-up", function () {
			const fn = $(this).closest("tr").data("fieldname");
			const visible = visibleColumns();
			const vIdx = visible.findIndex((c) => c.fieldname === fn);
			if (vIdx > 0) {
				const realA = columns.indexOf(visible[vIdx]);
				const realB = columns.indexOf(visible[vIdx - 1]);
				[columns[realA], columns[realB]] = [columns[realB], columns[realA]];
				renderRows();
			}
		});

		$tbody.on("click", ".tms-gexp-col-down", function () {
			const fn = $(this).closest("tr").data("fieldname");
			const visible = visibleColumns();
			const vIdx = visible.findIndex((c) => c.fieldname === fn);
			if (vIdx < visible.length - 1) {
				const realA = columns.indexOf(visible[vIdx]);
				const realB = columns.indexOf(visible[vIdx + 1]);
				[columns[realA], columns[realB]] = [columns[realB], columns[realA]];
				renderRows();
			}
		});

		renderRows();
		return { renderRows };
	}

	function do_export(doctype, filters, selected_fields) {
		const form = document.createElement("form");
		form.method = "POST";
		form.action = "/api/method/logicore.utils.export_utils.export_doctype_filtered";
		form.style.display = "none";

		const inp = (name, val) => {
			const el = document.createElement("input");
			el.type = "hidden";
			el.name = name;
			el.value = val;
			form.appendChild(el);
		};

		inp("doctype", doctype);
		inp("filters", JSON.stringify(filters));
		inp("selected_fields", JSON.stringify(selected_fields));
		inp("csrf_token", frappe.csrf_token);

		document.body.appendChild(form);
		form.submit();
		setTimeout(() => {
			if (form.parentNode) form.parentNode.removeChild(form);
		}, 3000);
	}

	function open_export_dialog(listview) {
		const doctype = listview.doctype;
		const columns = get_export_columns(doctype);
		if (!columns.length) {
			frappe.msgprint(__("No exportable columns found for {0}.", [__(doctype)]));
			return;
		}

		const filterDefs = build_filter_defs(doctype);
		// Report View only builds its internal DataTable once at least one row has
		// rendered — with zero rows (e.g. filters matching nothing) its own
		// get_checked_items() throws reading .rowmanager off an undefined
		// datatable. Treat that the same as "nothing checked" instead of letting
		// it abort the dialog before it opens.
		let checked_names = [];
		try {
			checked_names = (listview.get_checked_items && listview.get_checked_items(true)) || [];
		} catch (e) {
			checked_names = [];
		}

		const dialogFields = [];
		if (filterDefs.length) {
			dialogFields.push({ fieldtype: "Section Break", label: __("Filters") });
			filterDefs.forEach((fd, idx) => {
				dialogFields.push(fd.dialog_field);
				if (idx % 2 === 1) dialogFields.push({ fieldtype: "Column Break" });
			});
		}
		dialogFields.push({ fieldtype: "Section Break", label: __("Column Selection") });
		dialogFields.push({ fieldname: "col_selector_html", fieldtype: "HTML" });

		const d = new frappe.ui.Dialog({
			title: __("Export {0}", [__(doctype)]),
			size: "extra-large",
			fields: dialogFields,
			primary_action_label: __("Export CSV"),
			secondary_action_label: __("Cancel"),
			secondary_action() {
				d.hide();
			},
			primary_action() {
				const selected = [];
				d.$wrapper.find(".tms-gexp-col-tbody tr").each(function () {
					if ($(this).find(".tms-gexp-col-check").prop("checked")) {
						selected.push($(this).data("fieldname"));
					}
				});
				if (!selected.length) {
					frappe.msgprint(__("Please select at least one column to export."));
					return;
				}

				const filters = [];
				filterDefs.forEach((fd) => {
					const val = d.get_value(fd.dialog_field.fieldname);
					if (val) {
						const finalVal = fd.operator === "like" ? `%${val}%` : val;
						filters.push([doctype, fd.source_fieldname, fd.operator, finalVal]);
					}
				});
				if (checked_names.length) {
					filters.push([doctype, "name", "in", checked_names]);
				}

				d.hide();
				do_export(doctype, filters, selected);
			},
		});

		if (checked_names.length) {
			// d.$wrapper is the outer modal container (header+body+footer) — prepending
			// there renders outside the visible card. d.body is the actual scrollable
			// content area, same place Trip's own dialog shows this badge.
			$(d.body).prepend(`
<div style="margin:0 0 10px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
  <span style="display:inline-flex;align-items:center;gap:6px;background:#DCFCE7;color:#15803D;border:1.5px solid #86EFAC;border-radius:8px;padding:5px 12px;font-size:12px;font-weight:700;">
    ✓ ${checked_names.length} ${__("record(s) selected")}
  </span>
  <span style="font-size:11px;color:var(--text-muted);">${__("Filters below will further narrow the selected records.")}</span>
</div>`);
		}

		const colTable = build_col_table(d.get_field("col_selector_html").$wrapper, columns);

		// Narrow the column list to whatever's relevant for the currently-picked filter
		// values (via each field's own depends_on, same as a real form) — only for
		// doctypes that actually declare depends_on in their JSON. If nothing is
		// filtered yet, every column stays visible.
		const hasDependentColumns = columns.some((c) => c.depends_on);
		if (hasDependentColumns && filterDefs.length) {
			const recompute_visibility = () => {
				const filterDoc = {};
				let any_set = false;
				filterDefs.forEach((fd) => {
					const val = d.get_value(fd.dialog_field.fieldname);
					if (val) {
						any_set = true;
						filterDoc[fd.source_fieldname] = val;
					}
				});

				columns.forEach((col) => {
					if (!any_set || !col.depends_on) {
						col.visible = true;
					} else {
						col.visible = evaluate_depends_on(col.depends_on, filterDoc);
						if (!col.visible) col.checked = false;
					}
				});
				colTable.renderRows();
			};
			filterDefs.forEach((fd) => {
				fd.dialog_field.onchange = recompute_visibility;
				const field = d.fields_dict[fd.dialog_field.fieldname];
				if (field) field.df.onchange = recompute_visibility;
			});
			// Primary mechanism: a single delegated native-DOM listener on the dialog
			// body. Native "change" (select/date/data inputs) and "awesomplete-selectcomplete"
			// (Link fields) both bubble, so this catches every filter field regardless of
			// which Frappe control renders it or how its internal df wiring behaves —
			// no dependency on Frappe's own control-class event plumbing.
			$(d.body).on("change awesomplete-selectcomplete", "input, select", recompute_visibility);
		}

		d.show();
	}

	// Adds the "<DocType> Export" button to a list/report view. Called from each
	// eligible doctype's own "<name>_list.js" — never patches any Frappe class.
	function attach(listview) {
		if (!listview || !listview.page || !listview.doctype) return;
		if (!frappe.model.can_export(listview.doctype)) return;

		const label = __("{0} Export", [__(listview.doctype)]);
		// Matched by class, not text: the button's own text gets "📤 " prepended
		// right after creation (below), so a text comparison against the plain
		// label never matches on any later call — which silently defeated this
		// duplicate check and let a second button through whenever attach() ran
		// more than once for the same listview (e.g. the auto-attach fallback
		// below running alongside a doctype's own manual attach() call).
		const already = listview.page.wrapper.find(".page-actions .tms-list-btn-export, .page-head .tms-list-btn-export");
		if (already.length) return;

		const $btn = listview.page.add_button(label, () => {
			// Make sure any child table doctypes' meta are loaded before building the
			// column picker, so their columns actually show up (usually already cached
			// from the list view's own load, this is just a safety net).
			const meta = frappe.get_meta(listview.doctype);
			const childDoctypes = (meta.fields || [])
				.filter((f) => f.fieldtype === "Table" && f.options)
				.map((f) => f.options);
			if (!childDoctypes.length) {
				open_export_dialog(listview);
				return;
			}
			Promise.all(childDoctypes.map((dt) => frappe.model.with_doctype(dt))).then(() =>
				open_export_dialog(listview)
			);
		});
		$btn.addClass("tms-list-btn tms-list-btn-export").prepend("📤 ");
	}

	// Fallback so every eligible doctype gets the button even without its own
	// "<name>_list.js" calling attach() — reads live meta off the current route,
	// so a brand-new doctype (or one nobody wired up yet) gets it automatically,
	// with no per-doctype file required. attach() itself no-ops if a button with
	// this label already exists, so this is safe to run alongside the manual
	// per-doctype attach() calls that already exist.
	function auto_attach_from_route() {
		const route = frappe.get_route();
		if (!route || route[0] !== "List" || !route[1]) return;
		const doctype = route[1];
		if (doctype === "Trip" || doctype === "Amazon Trip") return;

		const meta = frappe.get_meta(doctype);
		if (!meta || meta.istable || meta.issingle) return;

		const listview = cur_list;
		if (!listview || listview.doctype !== doctype || !listview.page) return;

		attach(listview);
	}

	$(document).on("app_ready", () => {
		frappe.router.on("change", () => {
			[200, 500, 900, 1500].forEach((ms) => setTimeout(auto_attach_from_route, ms));
		});
	});
	[200, 500, 900, 1500].forEach((ms) => setTimeout(auto_attach_from_route, ms));

	inject_css();
	TMS.genericExport = { attach };
})();
