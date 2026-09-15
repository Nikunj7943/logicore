// ── Trip Export ──────────────────────────────────────────────────────────────
// Fully custom export dialog — no Frappe DataExporter patching required.
// "Trip Export" button opens a plain frappe.ui.Dialog that contains:
//   • 5 collapsible filter sections (same filters as before)
//   • A column-selection table with Up/Down reorder buttons
// On Export: form-POSTs to our Python endpoint which returns a CSV download.
// Works identically on fresh install and after migrate — nothing to register.
// ─────────────────────────────────────────────────────────────────────────────

// Filter field definitions — replaced by flat HTML grid (_tms_build_filter_html)
// const _TMS_FILTER_FIELDS = [ ... ];   // commented out — no longer used
// const _TMS_FILTER_KEYS   = new Set([...]); // commented out — no longer used

function _tms_build_filter_html($wrapper) {
    $wrapper.html(`
<div class="tms-ef-wrap">
  <div class="tms-ef-title">${__("Filters")}</div>

  <!-- Row 1: Company | Branch | Business Format | Trip Type -->
  <div class="tms-ef-grid tms-ef-g4">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Company")}</label>
      <select class="tms-ef-ctrl" data-filter="company"><option value="">ALL</option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Branch")}</label>
      <select class="tms-ef-ctrl" data-filter="branch"><option value="">ALL</option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Business Format")}</label>
      <select class="tms-ef-ctrl" data-filter="business_format"><option value=""></option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Trip Type")}</label>
      <select class="tms-ef-ctrl" data-filter="trip_type"><option value=""></option></select></div>
  </div>

  <!-- Row 2: TCN Date From | TCN Date To | TCN No Start | TCN No End | LR No Start | LR No End -->
  <div class="tms-ef-grid tms-ef-g6">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("TCN Date From")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="date_from"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("TCN Date To")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="date_to"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("TCN No-Start")}</label>
      <input type="text" class="tms-ef-ctrl" data-filter="tcn_no_start"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("TCN No-End")}</label>
      <input type="text" class="tms-ef-ctrl" data-filter="tcn_no_end"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("LR No-Start")}</label>
      <input type="text" class="tms-ef-ctrl" data-filter="lr_no_start"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("LR No-End")}</label>
      <input type="text" class="tms-ef-ctrl" data-filter="lr_no_end"></div>
  </div>

  <!-- Row 3: Origin City 1 | Origin City 2 | Destination City 1 | Destination City 2 -->
  <div class="tms-ef-grid tms-ef-g4">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Origin City 1")}</label>
      <select class="tms-ef-ctrl" data-filter="origin_city"><option value=""></option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Origin City 2")}</label>
      <select class="tms-ef-ctrl" data-filter="origin_city_2"><option value=""></option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Destination City 1")}</label>
      <select class="tms-ef-ctrl" data-filter="destination_city_1"><option value=""></option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Destination City 2")}</label>
      <select class="tms-ef-ctrl" data-filter="destination_city_2"><option value=""></option></select></div>
  </div>

  <!-- Row 4: Customer | Billing Start Date | Billing End Date | Vendor -->
  <div class="tms-ef-grid tms-ef-g4">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Customer")}</label>
      <select class="tms-ef-ctrl" data-filter="customer"><option value=""></option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Billing Start Date")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="billing_start_date_from"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Billing End Date")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="billing_start_date_to"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Vendor")}</label>
      <select class="tms-ef-ctrl" data-filter="vendor"><option value=""></option></select></div>
  </div>

  <!-- Row 5: Dispatch Date | POD Status | Bill No | Bill Date | Date Bill Credited | Status -->
  <div class="tms-ef-grid tms-ef-g6">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Dispatch Date")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="dispatch_date"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("POD Status")}</label>
      <select class="tms-ef-ctrl" data-filter="pod_status">
        <option value=""></option>
        <option value="POD Not Uploaded">${__("POD Not Uploaded")}</option>
        <option value="Original POD Uploaded">${__("Original POD Uploaded")}</option>
        <option value="Duplicate POD Uploaded">${__("Duplicate POD Uploaded")}</option>
      </select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Bill No")}</label>
      <input type="text" class="tms-ef-ctrl" data-filter="bill_no"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Bill Date")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="bill_date"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Date Bill Credited")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="date_bill_credited"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Status")}</label>
      <select class="tms-ef-ctrl" data-filter="trip_status">
        <option value=""></option>
        <option value="Open">${__("Open")}</option>
        <option value="Close">${__("Close")}</option>
        <option value="Cancel">${__("Cancel")}</option>
      </select></div>
  </div>
</div>`);

    // Inject CSS once (shared with amazon_trip_list.js's export dialog)
    TMS.injectExportFilterStyles();

    // Dynamically load dropdown options with optional filters, rendered as a
    // searchable type-to-search dropdown (TMS.makeSearchableSelect).
    const loadOpts = (filterKey, doctype, withAll, filters) => {
        // limit_page_length: 0 = no limit — master lists (e.g. 1000+ Suppliers) must load in full,
        // otherwise entries past the cutoff (alphabetically) silently vanish from the dropdown.
        const args = { doctype, fields: ["name"], limit_page_length: 0, order_by: "name asc" };
        if (filters) args.filters = filters;

        frappe.call({
            method: "frappe.client.get_list",
            args: args,
            callback(r) {
                const $sel = $wrapper.find(`[data-filter="${filterKey}"]`);
                const data = r.message || [];
                const options = data.map(d => d.name);
                TMS.makeSearchableSelect($sel, filterKey, options);
            },
        });
    };

    loadOpts("company",          "Company",         true);
    loadOpts("branch",           "Branch",          true);
    loadOpts("business_format",  "Business Format", false);
    loadOpts("trip_type",        "Trip Type",       false, { applies_to: "Trip", disabled: 0 });
    loadOpts("customer",         "Customer",        false);
    // Vendor: load ALL suppliers (all groups)
    loadOpts("vendor",           "Supplier",        false);
    // City options shared across all 4 city dropdowns
    frappe.call({
        method: "frappe.client.get_list",
        args: { doctype: "City", fields: ["name"], limit_page_length: 0, order_by: "name asc" },
        callback(r) {
            const data = r.message || [];
            const options = data.map(d => d.name);
            ["origin_city","origin_city_2","destination_city_1","destination_city_2"].forEach(k => {
                const $sel = $wrapper.find(`[data-filter="${k}"]`);
                TMS.makeSearchableSelect($sel, k, options);
            });
        },
    });
}

// System fields to exclude from export column list
const _TMS_EXPORT_SKIP_FIELDS = new Set([
    "amended_from", "docstatus", "doctype", "owner", "creation", "modified",
    "modified_by", "idx", "_assign", "_comments", "_user_tags", "workflow_state",
    // Address _full fields are hidden here; Python swaps link → full automatically on export
    "origin_address_1_full", "origin_address_2_full",
    "destination_address_1_full", "destination_address_2_full",
]);

// Layout/non-data fieldtypes — same ones Frappe's default export skips
const _TMS_EXPORT_SKIP_FIELDTYPES = new Set([
    "Section Break", "Column Break", "Tab Break", "Fold",
    "Heading", "HTML", "Button", "Image", "Attach Image",
    "Signature", "Geolocation", "Barcode", "Break",
]);

function _tms_get_export_columns() {
    const meta = frappe.get_meta("Trip");
    const columns = [];
    if (meta && meta.fields) {
        meta.fields.forEach(field => {
            if (
                !_TMS_EXPORT_SKIP_FIELDS.has(field.fieldname) &&
                !_TMS_EXPORT_SKIP_FIELDTYPES.has(field.fieldtype) &&
                field.label  // skip fields with no label
            ) {
                columns.push({
                    fieldname: field.fieldname,
                    label: field.label,
                    // Pre-select mandatory fields + name (ID) by default
                    checked: field.fieldname === "name" || !!field.reqd,
                });
            }
        });
    }
    return columns;
}

// filter key → column fieldname (for auto-check when filter changes)
const _TMS_FILTER_TO_COL = {
    "company":                 "company",
    "branch":                  "branch",
    "business_format":         "business_format",
    "trip_type":               "trip_type",
    "trip_status":             "trip_status",
    "date_from":               "tcntrip_date",
    "date_to":                 "tcntrip_date",
    "billing_start_date_from": "billing_start_date",
    "billing_start_date_to":   "billing_start_date",
    "dispatch_date":           "dispatch_date_time",
    "tcn_no_start":            "name",
    "tcn_no_end":              "name",
    "lr_no_start":             "lr_no",
    "lr_no_end":               "lr_no",
    "origin_city":             "origin_city",
    "origin_city_2":           "origin_city_2",
    "destination_city_1":      "destination_city_1",
    "destination_city_2":      "destination_city_2",
    "customer":                "customer",
    "vendor":                  "vendor",
    "pod_status":              "pod_status",
    "bill_no":                 "bill_nodate",
    "bill_date":               "bill_date",
    "date_bill_credited":      "date_bill_credited",
};

// Fetch Business Format saved columns and apply them to the export column selection
function _tms_apply_business_format_columns(bfName, columns, dialog) {
    frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Business Format", name: bfName },
        callback(r) {
            const doc = r && r.message;
            if (!doc) return;
            const savedCols = doc.trip_export_columns || [];
            if (!savedCols.length) return;

            // Build a set of fieldnames that are selected (selected=1) in Business Format.
            // "business_format" itself is always included — the filter driving this
            // whole preset is on, so its own column must stay ticked regardless of
            // whether that field happens to be part of the saved preset.
            const selectedSet = new Set(
                savedCols.filter(c => c.selected).map(c => c.fieldname)
            );
            selectedSet.add("business_format");

            // Uncheck all columns first, then check only the ones in selectedSet
            columns.forEach(col => {
                col.checked = selectedSet.has(col.fieldname);
            });

            // Re-render the column table to reflect the new state
            const $tbody = dialog.$wrapper.find(".tms-col-tbody");
            $tbody.find("tr").each(function () {
                const fn = $(this).data("fieldname");
                $(this).find(".tms-col-check").prop("checked", !!selectedSet.has(fn));
            });

            // Sync the Select All checkbox
            const total   = columns.length;
            const checked = columns.filter(c => c.checked).length;
            const $sa = dialog.$wrapper.find(".tms-select-all-cols");
            $sa.prop("checked", total > 0 && checked === total);
            $sa.prop("indeterminate", checked > 0 && checked < total);

            frappe.show_alert({
                message: __("Columns auto-selected from Business Format: {0}", [bfName]),
                indicator: "green",
            }, 4);
        },
    });
}

// Fetch Trip Type saved columns and apply them to the export column selection
function _tms_apply_trip_type_columns(typeName, columns, dialog) {
    frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Trip Type", name: typeName },
        callback(r) {
            const doc = r && r.message;
            if (!doc) return;
            const savedCols = doc.trip_export_columns || [];
            if (!savedCols.length) return;

            const selectedSet = new Set(
                savedCols.filter(c => c.selected).map(c => c.fieldname)
            );
            selectedSet.add("trip_type");

            columns.forEach(col => {
                col.checked = selectedSet.has(col.fieldname);
            });

            const $tbody = dialog.$wrapper.find(".tms-col-tbody");
            $tbody.find("tr").each(function () {
                const fn = $(this).data("fieldname");
                $(this).find(".tms-col-check").prop("checked", !!selectedSet.has(fn));
            });

            const total   = columns.length;
            const checked = columns.filter(c => c.checked).length;
            const $sa = dialog.$wrapper.find(".tms-select-all-cols");
            $sa.prop("checked", total > 0 && checked === total);
            $sa.prop("indeterminate", checked > 0 && checked < total);

            frappe.show_alert({
                message: __("Columns auto-selected from Trip Type: {0}", [typeName]),
                indicator: "green",
            }, 4);
        },
    });
}

function _tms_open_trip_export_dialog(selected_names) {
    // selected_names: array of Trip names if rows were checked in list view, else []
    const hasSelection = Array.isArray(selected_names) && selected_names.length > 0;
    const columns = _tms_get_export_columns().map(c => ({ ...c }));
    // Snapshot each column's default checked state (mandatory fields + name) before
    // any filter interaction mutates `columns` — used to restore them when Business
    // Format is cleared after its preset had unchecked them.
    const _tmsDefaultChecked = new Map(columns.map(c => [c.fieldname, c.checked]));

    const d = new frappe.ui.Dialog({
        title: __("Export Trips"),
        size: "extra-large",
        fields: [
            { fieldname: "filter_html",       fieldtype: "HTML" },
            { fieldtype: "Section Break",     label: __("Column Selection") },
            { fieldname: "col_selector_html", fieldtype: "HTML" },
        ],
        primary_action_label: __("Export CSV"),
        secondary_action_label: __("Cancel"),
        secondary_action() { d.hide(); },
        primary_action() {
            // Collect filter values from flat HTML inputs/selects
            const filters = {};
            d.get_field("filter_html").$wrapper.find("[data-filter]").each(function () {
                const key = $(this).data("filter");
                const val = $(this).val();
                if (val) filters[key] = val;
            });

            // If rows were selected in list view, add them as a base name filter
            // Python combines this with any form filters (both applied together)
            if (hasSelection) {
                filters.names = selected_names;
            }

            // Collect ordered selected columns (preserves Up/Down order)
            const selected = [];
            d.$wrapper.find(".tms-col-tbody tr").each(function () {
                if ($(this).find(".tms-col-check").prop("checked")) {
                    selected.push($(this).data("fieldname"));
                }
            });

            if (!selected.length) {
                frappe.msgprint(__("Please select at least one column to export."));
                return;
            }

            d.hide();
            _tms_do_export(filters, { Trip: selected });
        },
    });

    const $filterField = d.get_field("filter_html").$wrapper;
    _tms_build_filter_html($filterField);

    // If rows were selected, show an info badge above the filters (filters still apply)
    if (hasSelection) {
        $filterField.prepend(`
<div style="margin-bottom:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
  <span style="display:inline-flex;align-items:center;gap:6px;background:#DCFCE7;color:#15803D;border:1.5px solid #86EFAC;border-radius:8px;padding:5px 12px;font-size:12px;font-weight:700;">
    ✓ ${selected_names.length} ${__("record(s) selected")}
  </span>
  <span style="font-size:11px;color:var(--text-muted);">${__("Filters below will further narrow the selected records.")}</span>
</div>`);
    }

    // Populate column-selector table
    let colTable = { renderRows() {} };
    const $colField = d.get_field("col_selector_html");
    if ($colField && $colField.$wrapper) {
        colTable = _tms_build_col_table($colField.$wrapper, columns);
    }

    // Auto-check/uncheck the mapped column as its filter is set/cleared. Some
    // columns have two filters (e.g. TCN Date From/To both map to tcntrip_date),
    // so a column only unchecks once none of the filters mapped to it still
    // have a value — clearing just one half of a from/to pair must not uncheck
    // a column the other half is still using.
    $filterField.on("change", "[data-filter]", function () {
        const filterKey = $(this).data("filter");
        const colField  = _TMS_FILTER_TO_COL[filterKey];

        if (colField) {
            const relatedKeys = Object.keys(_TMS_FILTER_TO_COL).filter(k => _TMS_FILTER_TO_COL[k] === colField);
            const anyActive = relatedKeys.some(k => !!$filterField.find(`[data-filter="${k}"]`).val());
            const col = columns.find(c => c.fieldname === colField);
            if (col) col.checked = anyActive;
            colTable.renderRows();
        }

        // Business Format: apply its saved export-column preset when selected; when
        // cleared, restore every column to its pre-filter default (mandatory fields +
        // name) instead of leaving them however the preset last left them.
        if (filterKey === "business_format") {
            const bfName = $(this).val();
            if (bfName) {
                _tms_apply_business_format_columns(bfName, columns, d);
            } else {
                columns.forEach(col => { col.checked = !!_tmsDefaultChecked.get(col.fieldname); });
                colTable.renderRows();
            }
        }

        // Trip Type: same preset behavior as Business Format above. Whichever
        // of the two the user changes last simply overwrites `columns[].checked`
        // here, so "last changed wins" falls out naturally — no merge logic needed.
        if (filterKey === "trip_type") {
            const ttName = $(this).val();
            if (ttName) {
                _tms_apply_trip_type_columns(ttName, columns, d);
            } else {
                columns.forEach(col => { col.checked = !!_tmsDefaultChecked.get(col.fieldname); });
                colTable.renderRows();
            }
        }
    });

    d.show();
}

function _tms_build_col_table($wrapper, columns) {
    $wrapper.html(`
<div style="margin:4px 0 0;">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
    <label style="display:flex;align-items:center;gap:6px;font-weight:600;cursor:pointer;font-size:12px;">
      <input type="checkbox" class="tms-select-all-cols" style="width:14px;height:14px;">
      ${__("Select All")}
    </label>
  </div>
  <div style="max-height:320px;overflow-y:auto;border:1px solid var(--border-color);border-radius:6px;">
    <table style="width:100%;border-collapse:collapse;font-size:12px;">
      <thead>
        <tr style="background:var(--subtle-fg,#f3f4f6);position:sticky;top:0;z-index:1;">
          <th style="width:48px;padding:8px 6px;text-align:center;border-bottom:2px solid var(--border-color);font-weight:700;">${__("No")}</th>
          <th style="padding:8px 10px;text-align:left;border-bottom:2px solid var(--border-color);font-weight:700;">${__("Column Name")}</th>
          <th style="width:70px;padding:8px 6px;text-align:center;border-bottom:2px solid var(--border-color);font-weight:700;">${__("Select")}</th>
          <th style="width:130px;padding:8px 6px;text-align:center;border-bottom:2px solid var(--border-color);font-weight:700;">#</th>
        </tr>
      </thead>
      <tbody class="tms-col-tbody"></tbody>
    </table>
  </div>
</div>`);

    const $tbody     = $wrapper.find(".tms-col-tbody");
    const $selectAll = $wrapper.find(".tms-select-all-cols");

    function renderRows() {
        $tbody.empty();
        columns.forEach((col, idx) => {
            $tbody.append(`
<tr data-fieldname="${col.fieldname}" data-idx="${idx}" style="border-bottom:1px solid var(--border-color);">
  <td style="text-align:center;padding:8px 4px;color:var(--text-muted);font-size:11px;">${idx + 1}</td>
  <td style="padding:8px 10px;font-size:12px;">${col.label}</td>
  <td style="text-align:center;padding:8px 4px;">
    <input type="checkbox" class="tms-col-check" style="width:16px;height:16px;cursor:pointer;" ${col.checked ? "checked" : ""}>
  </td>
  <td style="text-align:center;padding:6px 4px;white-space:nowrap;">
    <button class="btn btn-xs btn-default tms-col-up" style="padding:4px 6px;margin-right:2px;background:#1e293b;color:#fff;border:none;" ${idx === 0 ? "disabled" : ""}>&#8593; Up</button>
    <button class="btn btn-xs btn-default tms-col-down" style="padding:4px 6px;background:#1e293b;color:#fff;border:none;" ${idx === columns.length - 1 ? "disabled" : ""}>&#8595; Down</button>
  </td>
</tr>`);
        });
        _syncSelectAll();
    }

    function _syncSelectAll() {
        const total   = columns.length;
        const checked = columns.filter(c => c.checked).length;
        $selectAll.prop("checked",       total > 0 && checked === total);
        $selectAll.prop("indeterminate", checked > 0 && checked < total);
    }

    // Select All / Deselect All
    $selectAll.on("change", function () {
        const v = this.checked;
        columns.forEach(c => c.checked = v);
        $tbody.find(".tms-col-check").prop("checked", v);
        $selectAll.prop("indeterminate", false);
    });

    // Individual checkbox — keep columns array in sync
    $tbody.on("change", ".tms-col-check", function () {
        const fn  = $(this).closest("tr").data("fieldname");
        const col = columns.find(c => c.fieldname === fn);
        if (col) col.checked = this.checked;
        _syncSelectAll();
    });

    // Move row up
    $tbody.on("click", ".tms-col-up", function () {
        const idx = parseInt($(this).closest("tr").data("idx"), 10);
        if (idx > 0) {
            [columns[idx - 1], columns[idx]] = [columns[idx], columns[idx - 1]];
            renderRows();
        }
    });

    // Move row down
    $tbody.on("click", ".tms-col-down", function () {
        const idx = parseInt($(this).closest("tr").data("idx"), 10);
        if (idx < columns.length - 1) {
            [columns[idx], columns[idx + 1]] = [columns[idx + 1], columns[idx]];
            renderRows();
        }
    });

    renderRows();
    return { renderRows };
}

function _tms_do_export(filters, selected_fields) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/api/method/logicore.overrides.trip_export.export_trips_filtered";
    form.style.display = "none";

    const inp = (name, val) => {
        const el = document.createElement("input");
        el.type  = "hidden";
        el.name  = name;
        el.value = val;
        form.appendChild(el);
    };

    inp("filters",         JSON.stringify(filters));
    inp("selected_fields", JSON.stringify(selected_fields));
    inp("csrf_token",      frappe.csrf_token);

    document.body.appendChild(form);
    form.submit();
    setTimeout(() => { if (form.parentNode) form.parentNode.removeChild(form); }, 3000);
}
// ── End Trip Export ───────────────────────────────────────────────────────────

function _tms_can_open_trip_import() {
    return frappe.model.can_import("Trip", null, frappe.get_meta("Trip")) && frappe.model.can_create("Import Log");
}

function _tms_upload_trip_import_csv(file) {
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

function _tms_trip_import_styles() {
    if (document.getElementById("tms-trip-import-style")) return;
    const style = document.createElement("style");
    style.id = "tms-trip-import-style";
    style.textContent = `
.tms-ti-dialog{display:flex;flex-direction:column;gap:12px;}
.tms-ti-banner{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 16px;border-radius:12px;background:linear-gradient(135deg,#0f766e,#14b8a6);color:#fff;flex-wrap:wrap;}
.tms-ti-banner strong{font-size:16px;display:block;}
.tms-ti-banner span{font-size:11px;color:rgba(255,255,255,.84);}
.tms-ti-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;}
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
@media(max-width:900px){.tms-ti-grid{grid-template-columns:1fr;}.tms-ti-card-grid{grid-template-columns:repeat(2,1fr);}}
    `;
    document.head.appendChild(style);
}

function _tms_render_trip_import_preview(dialog, payload) {
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
    dialog._tripImportCanRun = !!preview.can_import;
    dialog._tripImportLogName = payload.log_name || "";
}

function _tms_render_trip_import_result(dialog, result) {
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
}

function _tms_open_trip_import_dialog(listview) {
    _tms_trip_import_styles();
    const d = new frappe.ui.Dialog({
        title: __("Import Trips"),
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
                fieldname: "template",
                fieldtype: "Link",
                label: __("Import Template"),
                options: "Import Template",
                reqd: 1,
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
            if (!d._tripImportCanRun || !d._tripImportLogName) {
                frappe.msgprint(__("Please validate the file before importing."));
                return;
            }
            const values = d.get_values();
            const response = await frappe.call({
                method: "logicore.logicore.doctype.import_log.import_log.run_import",
                args: {
                    template_name: values.template,
                    import_mode: values.import_mode,
                    log_name: d._tripImportLogName,
                    company: values.company || "",
                },
                freeze: true,
                freeze_message: __("Importing trips..."),
            });
            _tms_render_trip_import_result(d, response.message || {});
            listview.refresh();
        },
    });

    d.get_field("intro_html").$wrapper.html(`
        <div class="tms-ti-dialog">
            <div class="tms-ti-banner">
                <div><strong>${__("Dynamic Trip Import")}</strong><span>${__("Select a template, upload CSV, validate, and import without leaving the Trip list.")}</span></div>
            </div>
        </div>
    `);
    d.get_field("upload_html").$wrapper.html(`
        <div class="tms-ti-upload">
            <div class="tms-ti-upload-row">
                <input type="file" id="tms-trip-import-file" accept=".csv,text/csv">
                <button class="btn btn-default btn-sm" id="tms-trip-import-download">${__("Download Template")}</button>
                <button class="btn btn-primary btn-sm" id="tms-trip-import-validate">${__("Validate File")}</button>
                <span id="tms-trip-import-file-name" class="text-muted"></span>
            </div>
        </div>
    `);

    d._tripImportUploadedFile = "";
    d._tripImportCanRun = false;
    d._tripImportLogName = "";

    d.fields_dict.template.df.get_query = () => ({
        filters: Object.assign(
            { is_active: 1 },
            d.get_value("company") ? { company: ["in", [d.get_value("company"), ""]] } : {}
        ),
    });

    d.fields_dict.template.df.onchange = async () => {
        const tpl = d.get_value("template");
        const modeField = d.fields_dict.import_mode;
        if (!tpl) {
            modeField.df.read_only = 0;
            modeField.refresh();
            d.set_value("import_mode", "");
            return;
        }
        const res = await frappe.db.get_value("Import Template", tpl, "default_import_mode");
        const mode = res && res.message && res.message.default_import_mode;
        if (mode) {
            d.set_value("import_mode", mode);
            modeField.df.read_only = 1;
            modeField.refresh();
        }
    };

    d.$wrapper.on("change", "#tms-trip-import-file", function() {
        const file = this.files && this.files[0];
        d._tripImportSelectedFile = file || null;
        d.$wrapper.find("#tms-trip-import-file-name").text(file ? file.name : "");
        d._tripImportCanRun = false;
        d._tripImportLogName = "";
    });

    d.$wrapper.on("click", "#tms-trip-import-download", function(e) {
        e.preventDefault();
        const values = d.get_values();
        if (!values || !values.template) {
            frappe.msgprint(__("Please select an import template first."));
            return;
        }
        const url = `/api/method/logicore.logicore.doctype.import_template.import_template.download_import_template?template_name=${encodeURIComponent(values.template)}`;
        window.open(url, "_blank");
    });

    d.$wrapper.on("click", "#tms-trip-import-validate", async function(e) {
        e.preventDefault();
        const values = d.get_values();
        if (!values || !values.template || !values.import_mode) {
            frappe.msgprint(__("Please select template and import mode first."));
            return;
        }
        if (!d._tripImportSelectedFile) {
            frappe.msgprint(__("Please choose a CSV file."));
            return;
        }
        frappe.dom.freeze(__("Uploading and validating CSV..."));
        try {
            const fileDoc = await _tms_upload_trip_import_csv(d._tripImportSelectedFile);
            d._tripImportUploadedFile = fileDoc.file_url;
            const response = await frappe.call({
                method: "logicore.logicore.doctype.import_log.import_log.upload_and_preview_import",
                args: {
                    template_name: values.template,
                    import_mode: values.import_mode,
                    file_url: d._tripImportUploadedFile,
                    company: values.company || "",
                },
            });
            _tms_render_trip_import_preview(d, response.message || {});
        } finally {
            frappe.dom.unfreeze();
        }
    });

    d.fields_dict.template.$input.on("change", async () => {
        const values = d.get_values();
        d._tripImportCanRun = false;
        d._tripImportLogName = "";
        if (!values || !values.template) return;
        const response = await frappe.call({
            method: "logicore.logicore.doctype.import_template.import_template.get_import_template",
            args: { template_name: values.template },
        });
        const template = response.message || {};
        if (template.default_import_mode) {
            d.set_value("import_mode", template.default_import_mode);
        }
        const columns = template.columns || [];
        d.get_field("expected_columns_html").$wrapper.html(
            columns.length
                ? `<div class="tms-ti-columns"><strong>${__("Expected Columns")}:</strong> ${columns.map(col => frappe.utils.escape_html(col.csv_header)).join(", ")}</div>`
                : ""
        );
    });

    d.show();
}

function _tms_fmt_dd(d) {
    return d ? d.split("-").reverse().join("-") : "";
}

function _tms_apply_bar_dates(from, to) {
    if (!from && !to) return false;
    if (from) $("#tms-from-date").val(from);
    if (to)   $("#tms-to-date").val(to);
    const label = from && to
        ? `${_tms_fmt_dd(from)}  →  ${_tms_fmt_dd(to)}`
        : _tms_fmt_dd(from || to);
    $("#tms-date-badge").text(label).show();
    return true;
}

// Fully removes every tcntrip_date filter row. The bar always represents one
// date range as TWO rows (>= and <=) sharing the same fieldname, but Frappe's
// filter_area.remove(fieldname) only removes the FIRST row matching that
// fieldname (FilterList.get_filter() returns filters[0]) — a single call
// always leaves one row behind, which then stacks up with every subsequent
// Apply/Clear/navigation instead of being replaced.
function _tms_clear_tcntrip_filters(view) {
    if (!view || !view.filter_area) return;
    const fl = view.filter_area.filter_list;
    while (fl && fl.get_filter && fl.get_filter("tcntrip_date")) {
        view.filter_area.remove("tcntrip_date");
    }
}

// Normalizes a [operator, value] pair (as found in both frappe.route_options
// and filter_area.get() tuples) into a [from, to] date pair.
function _tms_extract_from_to(op, val) {
    op = (op || "").toLowerCase();
    if (op === "between" && Array.isArray(val)) return val;
    if (op === ">=" || op === ">") return [val, ""];
    if (op === "<=" || op === "<") return ["", val];
    if (op === "=") return [val, val];
    return ["", ""];
}

// Reflects the tcntrip_date filter onto the quick-filter bar's inputs/badge
// so the bar always shows the date range that is actually applied to the
// list. `routeDateFilter` (frappe.route_options.tcntrip_date) is used when
// available — e.g. a fresh navigation from the Trip Operations dashboard
// widgets. It is empty on a plain browser reload (route_options doesn't
// survive a reload), so in that case we fall back to reading whatever
// tcntrip_date filter Frappe has already restored onto the list view from
// the URL, which is the actual filter still shown in the Filters panel.
function _tms_sync_date_bar(listview, routeDateFilter) {
    if (Array.isArray(routeDateFilter)) {
        const [from, to] = _tms_extract_from_to(routeDateFilter[0], routeDateFilter[1]);
        if (_tms_apply_bar_dates(from, to)) return;
    }
    const fa = listview && listview.filter_area;
    const dateFilters = fa && fa.get ? fa.get().filter(f => f[1] === "tcntrip_date") : [];
    let from = "", to = "";
    dateFilters.forEach(f => {
        const [f2, t2] = _tms_extract_from_to(f[2], f[3]);
        from = f2 || from;
        to   = t2 || to;
    });
    if (!_tms_apply_bar_dates(from, to)) {
        // No tcntrip_date filter actually applied (e.g. cleared via Frappe's
        // own native Filters panel) — the badge must not keep showing a
        // stale range that no longer reflects what's on screen.
        $("#tms-date-badge").hide();
    }
}

frappe.listview_settings["Trip"] = {

    onload(listview) {
        const today      = frappe.datetime.get_today();
        const todayStart = today;

        // Mask the grid IMMEDIATELY — before Frappe's own first (unfiltered)
        // fetch for this page ever paints. See tms_date_filter_bar.js's header
        // comment for why this can't be prevented any other way.
        frappe._tms_df_manual = frappe._tms_df_manual || {};
        TMS.dateFilterBar.registerPage("Trip", listview.$page);
        TMS.dateFilterBar.showOverlay("Trip");

        const $bar = $(`
            <div class="tms-date-filter-bar" style="
                display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
                padding: 7px 14px 6px;
                background: var(--subtle-accent,#EEF2FF);
                border-bottom: 1.5px solid var(--border-color,#C7D7FF);
                font-size: 12px;
            ">
                <style>
                    .list-subject-head, .list-subject { min-width: 180px !important; }
                    .tms-df-label { font-weight:700; color:var(--text-color,#3730A3); white-space:nowrap; font-size:11px; }
                    .tms-df-inp {
                        height:28px; padding:0 8px;
                        border:1.5px solid var(--border-color,#A5B4FC); border-radius:6px;
                        background:var(--control-bg,#fff); color:var(--text-color,#1E1B4B); font-size:11px;
                        outline:none; cursor:pointer;
                    }
                    .tms-df-inp:focus { border-color:var(--primary,#3B4FE4); box-shadow:0 0 0 2px rgba(59,79,228,0.14); }
                    .tms-df-apply {
                        height:28px; padding:0 16px;
                        background:#3B4FE4; color:#fff;
                        border:none; border-radius:6px;
                        font-size:11px; font-weight:700; cursor:pointer;
                        transition:background 0.14s;
                    }
                    .tms-df-apply:hover { background:#2D3DB8; }
                    .tms-df-clear {
                        height:28px; padding:0 12px;
                        background:var(--btn-default-bg,#F1F5F9); color:var(--text-muted,#475569);
                        border:1.5px solid var(--border-color,#CBD5E1); border-radius:6px;
                        font-size:11px; font-weight:600; cursor:pointer;
                        transition:background 0.14s;
                    }
                    .tms-df-clear:hover { background:var(--control-bg,#E2E8F0); }
                    .tms-df-badge {
                        display:none;
                        font-size:10px; font-weight:700;
                        background:#DCFCE7; color:#15803D;
                        border:1.5px solid #86EFAC; border-radius:12px;
                        padding:2px 10px; white-space:nowrap;
                    }
                    [data-theme="dark"] .tms-df-badge { background:#14532d; color:#86efac; border-color:#166534; }
                    .tms-df-sep { color:var(--text-muted,#94A3B8); font-size:11px; }
                </style>
                <span class="tms-df-label">🗓 Trip Date:</span>
                <input type="date" class="tms-df-inp" id="tms-from-date" value="${todayStart}" title="From Date">
                <span class="tms-df-sep">→</span>
                <input type="date" class="tms-df-inp" id="tms-to-date" value="${today}" title="To Date">
                <button class="tms-df-apply" id="tms-apply-date">Apply</button>
                <button class="tms-df-clear" id="tms-clear-date">Clear</button>
                <span class="tms-df-badge" id="tms-date-badge"></span>
            </div>
        `);

        listview.$page.find(".layout-main-section").prepend($bar);

        // ── Trip Export / Import styled buttons ──────────────────────────────
        if (!document.getElementById("tms-list-btn-style")) {
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
.tms-list-btn-export.btn,
.tms-list-btn-export.btn.btn-default,
.tms-list-btn-export.btn.btn-default:hover,
.tms-list-btn-export.btn.btn-default:focus {
    background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%) !important;
    color: #fff !important;
}
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

        if (frappe.model.can_export("Trip")) {
            listview.page.add_button(__("Trip Export"), () => {
                try {
                    // Report View never creates `datatable` when the grid has zero rows
                    // (e.g. filters matched nothing) — calling get_checked_items() in that
                    // state throws inside Frappe core (rowmanager read on undefined).
                    const checked = listview.datatable ? (listview.get_checked_items(true) || []) : [];
                    _tms_open_trip_export_dialog(checked);
                } catch (e) {
                    console.error("Trip Export dialog failed to open:", e);
                    frappe.msgprint({
                        title: __("Trip Export Error"),
                        indicator: "red",
                        message: __("Could not open the export dialog: {0}", [e.message || e]),
                    });
                }
            });

            // Style the Export button after it's added to the DOM
            setTimeout(() => {
                listview.page.wrapper.find(".page-actions .btn, .page-head .btn").filter(function() {
                    return $(this).text().trim() === __("Trip Export");
                }).addClass("tms-list-btn tms-list-btn-export").prepend("📤 ");
            }, 100);

            // // Remove the standard "Export" from the Actions dropdown for Trip —
            // // it only appeared after selecting rows; the button above replaces it.
            // const _exportActionLabel = __("Export", null, "Button in list view actions menu");
            // listview.page.actions
            //     .find(`[data-label="${encodeURIComponent(_exportActionLabel)}"]`)
            //     .remove();
        }
        // setup_list_button itself positions the button next to Trip Export —
        // see tms_import_dialog.js.
        TMS.import.setup_list_button(listview);

        const fmt_dd = d => d.split("-").reverse().join("-");

        function getView() {
            return cur_list || listview;
        }

        function applyFilter() {
            const from = $("#tms-from-date").val();
            const to   = $("#tms-to-date").val();
            if (!from || !to) {
                frappe.show_alert({ message: "⚠️ Select both From and To dates.", indicator: "orange" }, 3);
                TMS.dateFilterBar.hideOverlay("Trip");
                return;
            }
            if (from > to) {
                frappe.show_alert({ message: "⚠️ From date cannot be after To date.", indicator: "orange" }, 3);
                TMS.dateFilterBar.hideOverlay("Trip");
                return;
            }

            const view = getView();
            if (!view) { TMS.dateFilterBar.hideOverlay("Trip"); return; }

            const existing = (view.get_filters ? view.get_filters() : [])
                .filter(f => f[1] !== "tcntrip_date");

            if (view.filter_area && view.filter_area.filter_list) {
                view.filter_area.filter_list.set_filter_value &&
                    view.filter_area.filter_list.set_filter_value([
                        ...existing,
                        ["Trip", "tcntrip_date", ">=", from],
                        ["Trip", "tcntrip_date", "<=", to],
                    ]);
            }

            _tms_clear_tcntrip_filters(view);

            // Tell refresh() (below) this call's own filter_area.add() is what's
            // about to trigger it, so it doesn't fight the range just set here.
            frappe._tms_df_manual["Trip"] = true;

            // filter_area.add() is asynchronous (resolves standard-filter fields
            // then adds the filter rows before resolving) — passing `true` lets it
            // trigger view.refresh() itself once the filter is actually registered,
            // instead of us calling refresh() synchronously right after .add()
            // returns, which re-fetches with the OLD filter state and leaves the
            // badge showing a date range the grid was never actually filtered by.
            if (view.filter_area) {
                Promise.resolve(view.filter_area.add([
                    ["Trip", "tcntrip_date", ">=", from],
                    ["Trip", "tcntrip_date", "<=", to],
                ], true)).then(() => {
                    $("#tms-date-badge").text(`${fmt_dd(from)}  →  ${fmt_dd(to)}`).show();
                    frappe._tms_df_manual["Trip"] = false;
                    // Do NOT hide the overlay yet. ListView.prototype.refresh() is
                    // throttled to one real call per second, so on a fresh page load
                    // (where Frappe's own natural unfiltered fetch may have just
                    // consumed that window) this filtered refresh can update
                    // listview.data without the DataTable actually repainting yet
                    // (verified live via devtools). Keep the overlay up until the
                    // safety-net refresh below both confirms AND paints the correct
                    // state, so wrong rows are never visible even briefly.
                    setTimeout(() => {
                        const p = view.refresh && view.refresh();
                        Promise.resolve(p).then(() => TMS.dateFilterBar.hideOverlay("Trip"));
                    }, 1100);
                });
            } else {
                view.refresh ? view.refresh() : (view.run && view.run());
                $("#tms-date-badge").text(`${fmt_dd(from)}  →  ${fmt_dd(to)}`).show();
                TMS.dateFilterBar.hideOverlay("Trip");
                frappe._tms_df_manual["Trip"] = false;
            }
        }

        function clearFilter() {
            // Reset the bar's inputs to the default month-to-date range (so
            // they don't keep showing stale custom/dashboard dates), but
            // actually remove the tcntrip_date filter — both from the
            // Filters panel and the bar/badge — rather than re-applying that
            // default range as a still-active filter.
            $("#tms-from-date").val(todayStart);
            $("#tms-to-date").val(today);

            const view = getView();
            if (view) {
                frappe._tms_df_manual["Trip"] = true;
                _tms_clear_tcntrip_filters(view);
                view.refresh ? view.refresh() : (view.run && view.run());
                setTimeout(() => { frappe._tms_df_manual["Trip"] = false; }, 0);
            }
            $("#tms-date-badge").hide();
        }

        $("#tms-apply-date").on("click", applyFilter);
        $("#tms-clear-date").on("click", clearFilter);
        $bar.find(".tms-df-inp").on("keydown", e => { if (e.key === "Enter") applyFilter(); });

        // ── Save guard (once per session) ────────────────────────────────────
        // Strip non-date Trip list filters from every user_settings save so that
        // dashboard card filters never persist to __UserSettings.
        if (!frappe.model.user_settings._tms_trip_guard) {
            frappe.model.user_settings._tms_trip_guard = true;
            const _origSave = frappe.model.user_settings.save.bind(frappe.model.user_settings);
            frappe.model.user_settings.save = function(doctype, key, value, user) {
                if (doctype === "Trip" && key === "List" && value && Array.isArray(value.filters)) {
                    value = Object.assign({}, value, {
                        filters: value.filters.filter(f => Array.isArray(f) && f[1] === "tcntrip_date"),
                    });
                }
                return _origSave(doctype, key, value, user);
            };
        }

        // ── [Commented out] Hide internal _full fields from Frappe MultiCheck ──
        // Was needed when the old Frappe DataExporter dialog was reused.
        // The custom export dialog (_tms_open_trip_export_dialog) now owns its
        // own column list directly, so this CSS injection is no longer required.
        // if (!document.getElementById("tms-hide-link-export-fields")) {
        //     const style = document.createElement("style");
        //     style.id = "tms-hide-link-export-fields";
        //     style.textContent = [
        //         "origin_address_1",
        //         "origin_address_2",
        //         "destination_address_1",
        //         "destination_address_2",
        //     ].map(f => `.unit-checkbox:has(input[data-unit="${f}"])`).join(",\n") + " { display: none !important; }";
        //     document.head.appendChild(style);
        // }

        // ── Route change handler (once per session) — best-effort early masking
        // ONLY. refresh() below re-checks route_options/URL/manual-flag fresh
        // every time it runs and does NOT depend on this handler having fired;
        // an earlier design relied on a timestamped flag this handler set, but
        // that "change" event was observed to not reliably fire on every
        // cached-page sidebar revisit, silently leaving stale/unfiltered data
        // on screen. Kept only because it fires before Frappe's own fetch, so
        // when it DOES fire it masks the grid a little earlier than refresh()
        // otherwise could.
        if (!frappe._tms_trip_nav_guard) {
            frappe._tms_trip_nav_guard = true;
            frappe.router.on("change", function() {
                const r = frappe.get_route();
                if (r && r[0] === "List" && r[1] === "Trip" && !frappe._tms_df_manual["Trip"]) {
                    const hasRouteOpts = !!(frappe.route_options && Object.keys(frappe.route_options).length > 0);
                    if (!hasRouteOpts) TMS.dateFilterBar.showOverlay("Trip");
                }
            });
        }

        // ── Initial load (onload only fires on first page creation) ──────────
        // Only a genuine frappe.route_options (set explicitly by a
        // dashboard/report link right before navigating) counts as "respect
        // this filter" — the URL query string is NOT used as a signal: Frappe's
        // own update_url_with_filters() stamps whatever filter is currently
        // applied into the URL on every navigation (not just reloads), so a
        // stale custom range from a previous manual Apply would otherwise look
        // identical to a genuine dashboard link and survive forever instead of
        // resetting to today on the next plain sidebar visit.
        const _fromDashboard  = frappe.route_options && Object.keys(frappe.route_options).length > 0;
        const _dashboardDateFilter = frappe.route_options && frappe.route_options.tcntrip_date;
        setTimeout(() => {
            if (_fromDashboard) {
                // Filters already applied (via route_options, or restored by
                // Frappe from the URL on reload) — just reflect the real
                // date range onto the quick-filter bar/badge.
                _tms_sync_date_bar(getView(), _dashboardDateFilter);
                TMS.dateFilterBar.hideOverlay("Trip");
                return;
            }
            const _view = getView();
            const fl = _view && _view.filter_area && _view.filter_area.filter_list;
            if (fl && fl.filters) {
                fl.filters
                    .filter(f => f.fieldname !== "tcntrip_date")
                    .forEach(f => { try { f.$filter && f.$filter.remove(); } catch(e) {} });
                fl.filters = fl.filters.filter(f => f.fieldname === "tcntrip_date");
            }
            applyFilter();
        }, 300);

        // ── Fix Report View's extra page-level scrollbar ──────────────────────
        // report.scss sizes .layout-main-section as
        // `calc(100vh - var(--page-head-height))`, where --page-head-height is a
        // global constant (48px) that assumes a single-row toolbar. Trip's
        // toolbar (Export/Import buttons, Saved Filters, + this date bar) renders
        // taller than that, so .layout-main-section comes out a few px too tall
        // and the whole page grows a second, page-level scrollbar alongside the
        // DataTable's own internal one. Measure the real .page-head height and
        // correct the variable, scoped to this page only (not global).
        function _tms_fix_report_view_height() {
            const $wrapper = listview.page && listview.page.wrapper;
            const $head = $wrapper && $wrapper.find(".page-head").first();
            if (!$wrapper || !$head || !$head.length) return;
            $wrapper[0].style.setProperty("--page-head-height", $head[0].offsetHeight + "px");
        }
        setTimeout(_tms_fix_report_view_height, 350);
        $(window).off("resize.tms-trip-head").on("resize.tms-trip-head", _tms_fix_report_view_height);
    },

    // refresh() fires on EVERY navigation to the Trip list (cached or new) —
    // guaranteed by Frappe's own base_list.js, unlike the router "change"
    // event above (best-effort only). Re-checks route_options/URL/manual-flag
    // fresh every single time instead of trusting a pre-captured flag, so a
    // missed "change" event can never leave stale/unfiltered data on screen.
    refresh(listview) {
        frappe._tms_df_manual = frappe._tms_df_manual || {};
        TMS.dateFilterBar.registerPage("Trip", listview.$page);

        if (frappe._tms_df_manual["Trip"]) {
            // Our own click's filter_area.add() is what triggered this refresh —
            // don't fight the range the user just applied.
            TMS.dateFilterBar.hideOverlay("Trip");
            return;
        }

        // Only genuine route_options count here — NOT window.location.search.
        // Frappe stamps the current filter into the URL on every navigation
        // (not just reloads), so treating a leftover URL as "respect this"
        // would let a stale manually-applied range survive forever instead of
        // resetting to today on the next plain sidebar visit.
        const hasRouteOpts = !!(frappe.route_options && Object.keys(frappe.route_options).length > 0);
        if (hasRouteOpts) {
            // Dashboard/report link set this filter right before navigating —
            // reflect it onto the bar instead of forcing today.
            _tms_sync_date_bar(listview, frappe.route_options ? frappe.route_options.tcntrip_date : null);
            TMS.dateFilterBar.hideOverlay("Trip");
            return;
        }

        // Only force "today" when this refresh was triggered by a genuine
        // sidebar navigation. hide_sidebar.js stamps frappe._tms_sidebar_click_ts
        // (capture-phase, on every sidebar-link click, before the route even
        // changes) — the one reliable "a real navigation just happened" signal.
        // Any OTHER refresh (the user clearing the filter and applying a
        // different one via Frappe's own filter UI, an unrelated re-render)
        // must NOT be fought back to today, or a manual Clear followed by a
        // custom filter would keep silently reverting.
        const navTs = frappe._tms_sidebar_click_ts || 0;
        const isGenuineNav = (Date.now() - navTs) < 800;
        if (!isGenuineNav) {
            // Not a forced-today moment, but the bar's own inputs/badge must
            // still reflect whatever filter is ACTUALLY applied right now —
            // e.g. the user cleared/changed the date filter from Frappe's own
            // native Filters panel instead of this bar's Clear/Apply buttons.
            _tms_sync_date_bar(listview, null);
            TMS.dateFilterBar.hideOverlay("Trip");
            return;
        }
        // Consume it — a second refresh() call inside the same navigation
        // window (e.g. our own corrective setTimeout below) must not force
        // today a second time and stomp on a Clear/custom-filter that
        // happened to land in that same 800ms window.
        frappe._tms_sidebar_click_ts = 0;

        {
            // Plain sidebar navigation (no dashboard route_options / URL
            // filters) — always reset the bar back to the default
            // month-to-date range instead of re-applying whatever custom
            // range was left over in the inputs from a previous manual Apply.
            const _today      = frappe.datetime.get_today();
            const _todayStart = _today;
            $("#tms-from-date").val(_todayStart);
            $("#tms-to-date").val(_today);

            const fa = listview.filter_area;
            const fl = fa && fa.filter_list;
            if (fa && fl) {
                const nonDateFields = (fa.get ? fa.get() : [])
                    .filter(f => f[1] !== "tcntrip_date")
                    .map(f => f[1]);

                if (nonDateFields.length) {
                    // Suppress on_change to batch all removals into a single refresh below.
                    const origOnChange = fl.on_change;
                    fl.on_change = function() {};
                    nonDateFields.forEach(fn => { try { fa.remove(fn); } catch(e) {} });
                    fl.on_change = origOnChange;
                }
            }

            // Re-fetch with only the date filter (setTimeout avoids re-entrant refresh).
            setTimeout(() => {
                const from = $("#tms-from-date").val();
                const to   = $("#tms-to-date").val();
                if (!from || !to) { TMS.dateFilterBar.hideOverlay("Trip"); return; }
                _tms_clear_tcntrip_filters(listview);
                // See the matching comment in applyFilter() — `true` lets
                // filter_area.add() trigger the refresh itself once the filter is
                // actually registered, instead of racing ahead of its own promise chain.
                if (listview.filter_area) {
                    Promise.resolve(listview.filter_area.add([
                        ["Trip", "tcntrip_date", ">=", from],
                        ["Trip", "tcntrip_date", "<=", to],
                    ], true)).then(() => {
                        // The filter above is silently reapplied on every cached-page
                        // sidebar visit — reflect it on the badge too, otherwise the
                        // bar looks unfiltered even though the list actually is.
                        _tms_apply_bar_dates(from, to);
                        // Do NOT hide the overlay yet — see the matching comment in
                        // applyFilter() above: keep it up until the safety-net
                        // refresh below both confirms AND paints the correct state,
                        // so wrong rows are never visible even briefly.
                        setTimeout(() => {
                            const p = listview.refresh && listview.refresh();
                            Promise.resolve(p).then(() => TMS.dateFilterBar.hideOverlay("Trip"));
                        }, 1100);
                    });
                } else {
                    listview.refresh();
                    _tms_apply_bar_dates(from, to);
                    TMS.dateFilterBar.hideOverlay("Trip");
                }
            }, 0);
        }
    },

    get_indicator(doc) {
        const map = { Open: "green", Close: "blue", Cancel: "red", Draft: "grey" };
        return [
            doc.trip_status || "Draft",
            map[doc.trip_status] || "grey",
            "trip_status,=," + (doc.trip_status || "Draft"),
        ];
    },

    formatters: {
        tcntrip_date(value) {
            if (!value) return "";
            const p = String(value).split("-");
            return p.length === 3 ? `${p[2]}-${p[1]}-${p[0]}` : value;
        },
    },

    add_fields: ["pod_status"],

    button: {
        // get_label()/get_description() are called by Frappe for every row
        // unconditionally (even when show() is false) — guard against
        // TMS.pod not being loaded yet so one bad row can never break the
        // whole list render.
        show(doc) {
            return Boolean(window.TMS && TMS.pod) && TMS.pod.UPLOADED_STATUSES.includes(doc.pod_status);
        },
        get_label() {
            return (window.TMS && TMS.pod) ? TMS.pod.render_button_span() : "";
        },
        get_description(doc) { return __("Download POD for {0}", [doc.name]); },
        action(doc) {
            if (window.TMS && TMS.pod) TMS.pod.download(doc.name);
        },
    },
};
