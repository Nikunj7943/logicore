// ── Amazon Trip Export ────────────────────────────────────────────────────────
// Same pattern as Trip Export in trip_list.js.
// Button opens a dialog with filter controls + two-group column selector
// (Amazon Trip parent fields and Amazon Trip Detail child fields).
// On Export: form-POSTs to Python endpoint → returns CSV download.
// ─────────────────────────────────────────────────────────────────────────────

// Column order matching "Revised Amazon Format for New ERP - 22 Jun 2026.xlsx"
// (parent fields first, cols 1-38, child fields after, cols 39-71). The `checked`
// values below are ignored — _atms_open_amazon_export_dialog() overrides them,
// defaulting to only actually-mandatory Amazon Trip/Detail fields.
const _ATMS_DEFAULT_TEMPLATE_COLS = [
    // ── Amazon Trip (Parent) ─────────────────────────────────────────────────
    { fieldname: "company_name",                  label: "Company Name",                    group: "Amazon Trip",        checked: true },
    { fieldname: "customer",                      label: "Customer",                        group: "Amazon Trip",        checked: true },
    { fieldname: "trip_type",                     label: "Trip Type",                       group: "Amazon Trip",        checked: true },
    { fieldname: "branch",                        label: "Branch",                          group: "Amazon Trip",        checked: true },
    { fieldname: "trip_coordinator",              label: "Trip Coordinator",                group: "Amazon Trip",        checked: true },
    { fieldname: "trip_date",                     label: "Trip Date",                       group: "Amazon Trip",        checked: true },
    { fieldname: "tour_id_relay",                 label: "Tour ID",                         group: "Amazon Trip",        checked: true },
    { fieldname: "vr_id",                         label: "VR ID",                           group: "Amazon Trip",        checked: true },
    { fieldname: "status",                        label: "Status",                          group: "Amazon Trip",        checked: true },
    { fieldname: "facility_sequence",             label: "Facility Sequence",               group: "Amazon Trip",        checked: true },
    { fieldname: "cpt",                           label: "CPT",                             group: "Amazon Trip",        checked: true },
    { fieldname: "is_cpt_truck",                  label: "Is CPT Truck",                    group: "Amazon Trip",        checked: true },
    { fieldname: "cr_id",                         label: "CR_ID",                           group: "Amazon Trip",        checked: true },
    { fieldname: "shipper_accounts",              label: "Shipper Accounts",                group: "Amazon Trip",        checked: true },
    { fieldname: "equipment_type",                label: "Equipment Type",                  group: "Amazon Trip",        checked: true },
    { fieldname: "estimated_cost",                label: "Estimated Cost",                  group: "Amazon Trip",        checked: true },
    { fieldname: "tender_status",                 label: "Tender Status",                   group: "Amazon Trip",        checked: true },
    { fieldname: "driver_relay",                  label: "Driver",                          group: "Amazon Trip",        checked: true },
    { fieldname: "vehicle_id",                    label: "Vehicle ID",                      group: "Amazon Trip",        checked: true },
    { fieldname: "vr_cancellation_date_time_utc", label: "VR Cancellation Date Time (UTC)", group: "Amazon Trip",        checked: true },
    { fieldname: "transit_operator_type",         label: "Transit Operator Type",           group: "Amazon Trip",        checked: true },
    { fieldname: "spot_work",                     label: "Spot Work",                       group: "Amazon Trip",        checked: true },
    { fieldname: "freight",                       label: "Customer Freight",                group: "Amazon Trip",        checked: true },
    { fieldname: "fuel_surcharge_manual",         label: "RLB Fuel Surcharge1",             group: "Amazon Trip",        checked: true },
    { fieldname: "cancellation_charge_manual",    label: "RLB Cancellation Charge1",        group: "Amazon Trip",        checked: true },
    { fieldname: "detention_charge_manual",       label: "RLB Detention Charge1",           group: "Amazon Trip",        checked: true },
    { fieldname: "ot_cost_manual",                label: "RLB OT Cost1",                    group: "Amazon Trip",        checked: true },
    { fieldname: "extra_distance_cost_manual",    label: "RLB Extra Distance Cost1",        group: "Amazon Trip",        checked: true },
    { fieldname: "toll_parking_charges_manual",   label: "RLB Toll-Parking Charges1",       group: "Amazon Trip",        checked: true },
    { fieldname: "trip_cost",                     label: "Total Trip Amount",               group: "Amazon Trip",        checked: true },
    { fieldname: "vendor",                        label: "Vendor",                          group: "Amazon Trip",        checked: true },
    { fieldname: "vendor_freight",                label: "Vendor Freight",                  group: "Amazon Trip",        checked: true },
    { fieldname: "vendor_freight_extra",          label: "Vendor Freight (Extra)",          group: "Amazon Trip",        checked: true },
    { fieldname: "total_vendor_freight",          label: "Total Vendor Freight",            group: "Amazon Trip",        checked: true },
    { fieldname: "remarks_amazon",                label: "Remarks",                         group: "Amazon Trip",        checked: true },
    { fieldname: "duplicate_trips",               label: "Duplicate Trips",                 group: "Amazon Trip",        checked: true },
    { fieldname: "duplicate_record_no",           label: "Duplicate Record No",             group: "Amazon Trip",        checked: true },
    { fieldname: "manual_trip",                   label: "Manual Trip",                     group: "Amazon Trip",        checked: true },
    // ── Amazon Trip Detail (Child) ───────────────────────────────────────────
    { fieldname: "load_id",                       label: "Load ID",                         group: "Amazon Trip Detail", checked: true },
    { fieldname: "vehicle_no",                    label: "Vehicle No.",                     group: "Amazon Trip Detail", checked: true },
    { fieldname: "start_date",                    label: "Start Date",                      group: "Amazon Trip Detail", checked: true },
    { fieldname: "end_date",                      label: "End Date",                        group: "Amazon Trip Detail", checked: true },
    { fieldname: "lane",                          label: "Lane",                            group: "Amazon Trip Detail", checked: true },
    { fieldname: "city",                          label: "City",                            group: "Amazon Trip Detail", checked: true },
    { fieldname: "operator_type_amazon",          label: "Operator Type",                   group: "Amazon Trip Detail", checked: true },
    { fieldname: "total_distance",                label: "Total Distance",                  group: "Amazon Trip Detail", checked: true },
    { fieldname: "contract_type",                 label: "Contract Type",                   group: "Amazon Trip Detail", checked: true },
    { fieldname: "rate_type",                     label: "Rate Type",                       group: "Amazon Trip Detail", checked: true },
    { fieldname: "item_type",                     label: "Item Type",                       group: "Amazon Trip Detail", checked: true },
    { fieldname: "work_type",                     label: "Work Type",                       group: "Amazon Trip Detail", checked: true },
    { fieldname: "base_rate",                     label: "Base Rate",                       group: "Amazon Trip Detail", checked: true },
    { fieldname: "fuel_surcharge_amazon",         label: "Fuel Surcharge",                  group: "Amazon Trip Detail", checked: true },
    { fieldname: "cancellation_charge_amazon",    label: "Cancellation Charge",             group: "Amazon Trip Detail", checked: true },
    { fieldname: "detention_charge_amazon",       label: "Detention Charge",                group: "Amazon Trip Detail", checked: true },
    { fieldname: "ot_cost_amazon",                label: "OT Cost",                         group: "Amazon Trip Detail", checked: true },
    { fieldname: "extra_distance_cost_amazon",    label: "Extra Distance Cost",             group: "Amazon Trip Detail", checked: true },
    { fieldname: "toll_parking_charges_amazon",   label: "Toll-Parking Charges",            group: "Amazon Trip Detail", checked: true },
    { fieldname: "tax_percent",                   label: "Tax Percent",                     group: "Amazon Trip Detail", checked: true },
    { fieldname: "gross_pay_amt_excl_tax",        label: "Gross Pay Amt (Excl. Tax)",       group: "Amazon Trip Detail", checked: true },
    { fieldname: "gross_tax_amt",                 label: "Gross Tax Amt",                   group: "Amazon Trip Detail", checked: true },
    { fieldname: "gross_pay_amt",                 label: "Gross Pay Amt",                   group: "Amazon Trip Detail", checked: true },
    { fieldname: "comments",                      label: "Comments",                        group: "Amazon Trip Detail", checked: true },
    { fieldname: "extra_hours",                   label: "Extra Hours",                     group: "Amazon Trip Detail", checked: true },
    { fieldname: "extra_km",                      label: "Extra Km",                        group: "Amazon Trip Detail", checked: true },
    { fieldname: "remarks3",                      label: "Remarks3",                        group: "Amazon Trip Detail", checked: true },
    { fieldname: "original_sadashiv_bill_no",     label: "Bill No",                         group: "Amazon Trip Detail", checked: true },
    { fieldname: "original_bill_date",            label: "Bill Date",                       group: "Amazon Trip Detail", checked: true },
    { fieldname: "computed_total_freight",        label: "Computed Total Freight",          group: "Amazon Trip Detail", checked: true },
    { fieldname: "computed_billed_amount",        label: "Computed Billed Amount",          group: "Amazon Trip Detail", checked: true },
    { fieldname: "freight_difference",            label: "Freight Difference",              group: "Amazon Trip Detail", checked: true },
    { fieldname: "trip_status",                   label: "Trip Status",                     group: "Amazon Trip Detail", checked: true },
];

function _atms_build_filter_html($wrapper) {
    $wrapper.html(`
<div class="tms-ef-wrap">
  <div class="tms-ef-title">${__("Filters")}</div>

  <!-- Row 1: Company | Branch | Business Format | Amazon Trip Type -->
  <div class="tms-ef-grid tms-ef-g4">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Company")}</label>
      <select class="tms-ef-ctrl" data-filter="company"><option value="">ALL</option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Branch")}</label>
      <select class="tms-ef-ctrl" data-filter="branch"><option value="">ALL</option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Business Format")}</label>
      <select class="tms-ef-ctrl" data-filter="business_format"><option value=""></option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Amazon Trip Type")}</label>
      <select class="tms-ef-ctrl" data-filter="trip_type"><option value=""></option></select></div>
  </div>

  <!-- Row 2: Trip Date From | Trip Date To | Tour ID -->
  <div class="tms-ef-grid tms-ef-g3">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Trip Date From")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="date_from"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Trip Date To")}</label>
      <input type="date" class="tms-ef-ctrl" data-filter="date_to"></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Tour ID")}</label>
      <input type="text" class="tms-ef-ctrl" data-filter="tour_id" placeholder="partial match"></div>
  </div>

  <!-- Row 3: Customer | Vendor -->
  <div class="tms-ef-grid tms-ef-g3">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Customer")}</label>
      <select class="tms-ef-ctrl" data-filter="customer"><option value=""></option></select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Vendor")}</label>
      <select class="tms-ef-ctrl" data-filter="vendor"><option value=""></option></select></div>
    <div class="tms-ef-item"></div>
  </div>

  <!-- Row 4: Status | Trip Status -->
  <div class="tms-ef-grid tms-ef-g3">
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Status")}</label>
      <select class="tms-ef-ctrl" data-filter="status">
        <option value=""></option>
        <option value="Completed">${__("Completed")}</option>
        <option value="Cancelled">${__("Cancelled")}</option>
        <option value="Dummy">${__("Dummy")}</option>
      </select></div>
    <div class="tms-ef-item"><label class="tms-ef-lbl">${__("Trip Status")}</label>
      <select class="tms-ef-ctrl" data-filter="trip_status">
        <option value=""></option>
        <option value="Closed">${__("Closed")}</option>
        <option value="Unbilled">${__("Unbilled")}</option>
        <option value="Under Dispute">${__("Under Dispute")}</option>
      </select></div>
    <div class="tms-ef-item"></div>
  </div>
</div>`);

    // Inject CSS once (shared with trip_list.js's export dialog)
    TMS.injectExportFilterStyles();

    // Dynamically load dropdown options, rendered as a searchable type-to-search
    // dropdown (TMS.makeSearchableSelect) instead of a plain <select>.
    const loadOpts = (filterKey, doctype, withAll, filters) => {
        const args = { doctype, fields: ["name"], limit_page_length: 0, order_by: "name asc" };
        if (filters) args.filters = filters;
        frappe.call({
            method: "frappe.client.get_list",
            args: args,
            callback(r) {
                const $sel = $wrapper.find(`[data-filter="${filterKey}"]`);
                const options = (r.message || []).map(row => row.name);
                TMS.makeSearchableSelect($sel, filterKey, options);
            },
        });
    };

    loadOpts("company",          "Company",         true);
    loadOpts("branch",           "Branch",          true);
    loadOpts("business_format",  "Business Format", false, { applies_to: "Amazon" });
    loadOpts("trip_type",        "Trip Type",       false, { applies_to: "Amazon", disabled: 0 });
    loadOpts("customer",         "Customer",        false);
    loadOpts("vendor",           "Supplier",        false);
}

// filter key → column fieldname (auto-check column when filter is set)
const _ATMS_FILTER_TO_COL = {
    "company":         "company_name",
    "branch":          "branch",
    "business_format": "amazon_business_format",
    "trip_type":       "trip_type",
    "date_from":    "trip_date",
    "date_to":      "trip_date",
    "tour_id":      "tour_id_relay",
    "customer":     "customer",
    "vendor":       "vendor",
    "status":       "status",
    "trip_status":  "trip_status",
};

// Extra parent columns NOT in the default template — all unchecked by default.
// Only truly parent-specific fields are listed here.
// Hidden parent mirror-fields of child columns are excluded (child rows carry that data).
const _ATMS_EXTRA_PARENT_COLS = [
    // ── Parent-only fields ───────────────────────────────────────────────────
    { fieldname: "name",                       label: "Amazon Trip No",                  group: "Amazon Trip", checked: false },
    { fieldname: "amazon_business_format",     label: "Amazon Business Format",          group: "Amazon Trip", checked: false },
    { fieldname: "vehicle_id_market",          label: "Vehicle ID (Market)",             group: "Amazon Trip", checked: false },
    { fieldname: "driver_market",              label: "Driver (Market)",                 group: "Amazon Trip", checked: false },
    { fieldname: "driver_mobile_market",       label: "Driver Mobile (Market)",          group: "Amazon Trip", checked: false },
    { fieldname: "comments_amazon",            label: "Comments",                        group: "Amazon Trip", checked: false },
    // ── Parent versions of fields that also exist on child ───────────────────
    // Default template already exports the child versions of these.
    // Include parent versions here so users can optionally add them.
    { fieldname: "computed_total_freight",     label: "Computed Total Freight (Parent)", group: "Amazon Trip", checked: false },
    { fieldname: "computed_billed_amount",     label: "Computed Billed Amount (Parent)", group: "Amazon Trip", checked: false },
    { fieldname: "freight_difference",         label: "Freight Difference (Parent)",     group: "Amazon Trip", checked: false },
    { fieldname: "trip_status",                label: "Trip Status (Parent)",            group: "Amazon Trip", checked: false },
    { fieldname: "original_sadashiv_bill_no",  label: "Bill No (Parent)",                group: "Amazon Trip", checked: false },
    { fieldname: "original_bill_date",         label: "Bill Date (Parent)",              group: "Amazon Trip", checked: false },
];

// Extra child columns NOT in the default template — all unchecked by default.
const _ATMS_EXTRA_DETAIL_COLS = [];

function _atms_build_col_table($wrapper, allCols) {

    $wrapper.html(`
<div style="margin:4px 0 0;">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
    <label style="display:flex;align-items:center;gap:6px;font-weight:600;cursor:pointer;font-size:12px;">
      <input type="checkbox" class="atms-select-all-cols" style="width:14px;height:14px;">
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
      <tbody class="atms-col-tbody"></tbody>
    </table>
  </div>
</div>`);

    const $tbody     = $wrapper.find(".atms-col-tbody");
    const $selectAll = $wrapper.find(".atms-select-all-cols");

    function _syncSelectAll() {
        const total   = allCols.length;
        const checked = allCols.filter(c => c.checked).length;
        $selectAll.prop("checked",       total > 0 && checked === total);
        $selectAll.prop("indeterminate", checked > 0 && checked < total);
    }

    function renderRows() {
        $tbody.empty();
        allCols.forEach((col, idx) => {
            $tbody.append(`
<tr data-fieldname="${col.fieldname}" data-idx="${idx}" data-grp="${col.group}" style="border-bottom:1px solid var(--border-color);">
  <td style="text-align:center;padding:8px 4px;color:var(--text-muted);font-size:11px;">${idx + 1}</td>
  <td style="padding:8px 10px;font-size:12px;">${col.label}</td>
  <td style="text-align:center;padding:8px 4px;">
    <input type="checkbox" class="atms-col-check" style="width:16px;height:16px;cursor:pointer;" ${col.checked ? "checked" : ""}>
  </td>
  <td style="text-align:center;padding:6px 4px;white-space:nowrap;">
    <button class="btn btn-xs btn-default atms-col-up" style="padding:4px 6px;margin-right:2px;background:#1e293b;color:#fff;border:none;" ${idx === 0 ? "disabled" : ""}>&#8593; Up</button>
    <button class="btn btn-xs btn-default atms-col-down" style="padding:4px 6px;background:#1e293b;color:#fff;border:none;" ${idx === allCols.length - 1 ? "disabled" : ""}>&#8595; Down</button>
  </td>
</tr>`);
        });
        _syncSelectAll();
    }

    $selectAll.on("change", function () {
        const v = this.checked;
        allCols.forEach(c => c.checked = v);
        $tbody.find(".atms-col-check").prop("checked", v);
        $selectAll.prop("indeterminate", false);
    });

    $tbody.on("change", ".atms-col-check", function () {
        const fn  = $(this).closest("tr").data("fieldname");
        const grp = $(this).closest("tr").data("grp");
        const col = allCols.find(c => c.fieldname === fn && c.group === grp);
        if (col) col.checked = this.checked;
        _syncSelectAll();
    });

    $tbody.on("click", ".atms-col-up", function () {
        const idx = parseInt($(this).closest("tr").data("idx"), 10);
        if (idx > 0) {
            [allCols[idx - 1], allCols[idx]] = [allCols[idx], allCols[idx - 1]];
            renderRows();
        }
    });

    $tbody.on("click", ".atms-col-down", function () {
        const idx = parseInt($(this).closest("tr").data("idx"), 10);
        if (idx < allCols.length - 1) {
            [allCols[idx], allCols[idx + 1]] = [allCols[idx + 1], allCols[idx]];
            renderRows();
        }
    });

    renderRows();

    // Expose allCols so the dialog's filter-change handler can auto-check rows
    $wrapper[0]._atmsAllCols = allCols;

    return { renderRows };
}

// Fetch a Business Format / Trip Type's saved Trip Export Columns preset (only
// ever built from Amazon Trip's own — parent — fields, see business_format.js /
// trip_type.js) and apply it to the dialog's "Amazon Trip" column group. Amazon
// Trip Detail (child) columns are untouched — presets don't cover child fields.
function _atms_apply_columns_preset(doctype, name, allCols, colTable, dialog) {
    frappe.call({
        method: "frappe.client.get",
        args: { doctype, name },
        callback(r) {
            const doc = r && r.message;
            if (!doc) return;
            const savedCols = doc.trip_export_columns || [];
            if (!savedCols.length) return;

            const selectedSet = new Set(savedCols.filter(c => c.selected).map(c => c.fieldname));

            allCols.forEach(col => {
                if (col.group === "Amazon Trip") {
                    col.checked = selectedSet.has(col.fieldname);
                }
            });
            colTable.renderRows();

            frappe.show_alert({
                message: __("Columns auto-selected from {0}: {1}", [doctype, name]),
                indicator: "green",
            }, 4);
        },
    });
}

function _atms_open_amazon_export_dialog(selected_names) {
    const hasSelection = Array.isArray(selected_names) && selected_names.length > 0;
    // Build full column list (order: template parent, template child, extra
    // parent, extra child). Only actually-mandatory fields default-checked —
    // everything else starts unchecked regardless of which list it came from.
    const allCols = [
        ..._ATMS_DEFAULT_TEMPLATE_COLS.filter(c => c.group === "Amazon Trip").map(c => ({ ...c })),
        ..._ATMS_DEFAULT_TEMPLATE_COLS.filter(c => c.group === "Amazon Trip Detail").map(c => ({ ...c })),
        ..._ATMS_EXTRA_PARENT_COLS.map(c => ({ ...c })),
        ..._ATMS_EXTRA_DETAIL_COLS.map(c => ({ ...c })),
    ];

    allCols.forEach(col => {
        const doctype = col.group === "Amazon Trip Detail" ? "Amazon Trip Detail" : "Amazon Trip";
        const df = frappe.meta.get_field(doctype, col.fieldname);
        col.checked = !!(df && df.reqd);
    });
    // Snapshot mandatory-only defaults before any preset/interaction mutates
    // `allCols` — used to restore the "Amazon Trip" group when a Business
    // Format / Trip Type preset filter is cleared.
    const _atmsDefaultChecked = new Map(allCols.map(c => [`${c.fieldname}|${c.group}`, c.checked]));

    const d = new frappe.ui.Dialog({
        title: __("Export Amazon Trips"),
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
            const filters = {};
            d.get_field("filter_html").$wrapper.find("[data-filter]").each(function () {
                const key = $(this).data("filter");
                const val = $(this).val();
                if (val) filters[key] = val;
            });

            if (hasSelection) {
                filters.names = selected_names;
            }

            const selectedParent = [];
            const selectedDetail = [];
            d.$wrapper.find(".atms-col-tbody tr").each(function () {
                if ($(this).find(".atms-col-check").prop("checked")) {
                    const fn  = $(this).data("fieldname");
                    const grp = $(this).data("grp");
                    if (grp === "Amazon Trip Detail") {
                        selectedDetail.push(fn);
                    } else {
                        selectedParent.push(fn);
                    }
                }
            });

            if (!selectedParent.length) {
                frappe.msgprint(__("Please select at least one Amazon Trip column to export."));
                return;
            }

            d.hide();
            _atms_do_amazon_export(filters, {
                "Amazon Trip": selectedParent,
                "Amazon Trip Detail": selectedDetail,
            });
        },
    });

    const $filterField = d.get_field("filter_html").$wrapper;
    _atms_build_filter_html($filterField);

    if (hasSelection) {
        $filterField.prepend(`
<div style="margin-bottom:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
  <span style="display:inline-flex;align-items:center;gap:6px;background:#DCFCE7;color:#15803D;border:1.5px solid #86EFAC;border-radius:8px;padding:5px 12px;font-size:12px;font-weight:700;">
    ✓ ${selected_names.length} ${__("record(s) selected")}
  </span>
  <span style="font-size:11px;color:var(--text-muted);">${__("Filters below will further narrow the selected records.")}</span>
</div>`);
    }

    let colTable = { renderRows() {} };
    const $colField = d.get_field("col_selector_html");
    if ($colField && $colField.$wrapper) {
        colTable = _atms_build_col_table($colField.$wrapper, allCols);
    }

    // Auto-check the corresponding column when a filter value is set
    $filterField.on("change", "[data-filter]", function () {
        const filterKey = $(this).data("filter");
        const colField  = _ATMS_FILTER_TO_COL[filterKey];

        if (colField && $(this).val()) {
            const $row = d.$wrapper.find(`.atms-col-tbody tr[data-fieldname="${colField}"]`);
            if ($row.length) {
                $row.first().find(".atms-col-check").prop("checked", true);
                const col = allCols.find(c => c.fieldname === colField);
                if (col) col.checked = true;
                const $sa = d.$wrapper.find(".atms-select-all-cols");
                const total   = d.$wrapper.find(".atms-col-tbody tr").length;
                const checked = d.$wrapper.find(".atms-col-tbody .atms-col-check:checked").length;
                $sa.prop("checked",       total > 0 && checked === total);
                $sa.prop("indeterminate", checked > 0 && checked < total);
            }
        }

        // Business Format / Trip Type: apply their saved export-column preset
        // (Amazon Trip fields only) when selected; restore mandatory-only
        // defaults for that group when cleared. Whichever of the two the user
        // changes last simply overwrites `col.checked` here, so "last changed
        // wins" falls out naturally if both are set — no merge logic needed.
        if (filterKey === "business_format" || filterKey === "trip_type") {
            const presetDoctype = filterKey === "business_format" ? "Business Format" : "Trip Type";
            const val = $(this).val();
            if (val) {
                _atms_apply_columns_preset(presetDoctype, val, allCols, colTable, d);
            } else {
                allCols.forEach(col => {
                    if (col.group === "Amazon Trip") {
                        col.checked = !!_atmsDefaultChecked.get(`${col.fieldname}|${col.group}`);
                    }
                });
                colTable.renderRows();
            }
        }
    });

    d.show();
}

function _atms_do_amazon_export(filters, selected_fields) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/api/method/logicore.overrides.amazon_trip_export.export_amazon_trips_filtered";
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
// ── End Amazon Trip Export ────────────────────────────────────────────────────

// Fully removes every trip_date filter row. The bar always represents one
// date range as TWO rows (>= and <=) sharing the same fieldname, but Frappe's
// filter_area.remove(fieldname) only removes the FIRST row matching that
// fieldname (FilterList.get_filter() returns filters[0]) — a single call
// always leaves one row behind, which then stacks up with every subsequent
// Apply/Clear/navigation instead of being replaced.
function _atms_clear_date_filters(view) {
    if (!view || !view.filter_area) return;
    const fl = view.filter_area.filter_list;
    while (fl && fl.get_filter && fl.get_filter("trip_date")) {
        view.filter_area.remove("trip_date");
    }
}

frappe.listview_settings["Amazon Trip"] = {

    onload(listview) {
        const today      = frappe.datetime.get_today();
        const todayStart = today;

        // Mask the grid IMMEDIATELY — before Frappe's own first (unfiltered)
        // fetch for this page ever paints. See tms_date_filter_bar.js's header
        // comment for why this can't be prevented any other way.
        frappe._tms_df_manual = frappe._tms_df_manual || {};
        TMS.dateFilterBar.registerPage("Amazon Trip", listview.$page);
        TMS.dateFilterBar.showOverlay("Amazon Trip");

        const $bar = $(`
            <div class="tms-date-filter-bar" style="
                display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
                padding: 7px 14px 6px;
                background: var(--subtle-accent,#EEF2FF);
                border-bottom: 1.5px solid var(--border-color,#C7D7FF);
                font-size: 12px;
            ">
                <style>
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
                <input type="date" class="tms-df-inp" id="atms-from-date" value="${todayStart}" title="From Date">
                <span class="tms-df-sep">→</span>
                <input type="date" class="tms-df-inp" id="atms-to-date" value="${today}" title="To Date">
                <button class="tms-df-apply" id="atms-apply-date">Apply</button>
                <button class="tms-df-clear" id="atms-clear-date">Clear</button>
                <span class="tms-df-badge" id="atms-date-badge"></span>
            </div>
        `);

        listview.$page.find(".layout-main-section").prepend($bar);

        // ── Amazon Trip Export styled button ─────────────────────────────────
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
            `;
            document.head.appendChild(s);
        }

        if (frappe.model.can_export("Amazon Trip")) {
            listview.page.add_button(__("Amazon Trip Export"), () => {
                try {
                    // Report View never creates `datatable` when the grid has zero rows —
                    // calling get_checked_items() in that state throws inside Frappe core.
                    const checked = listview.datatable ? (listview.get_checked_items(true) || []) : [];
                    _atms_open_amazon_export_dialog(checked);
                } catch (e) {
                    console.error("Amazon Trip Export dialog failed to open:", e);
                    frappe.msgprint({
                        title: __("Amazon Trip Export Error"),
                        indicator: "red",
                        message: __("Could not open the export dialog: {0}", [e.message || e]),
                    });
                }
            });

            setTimeout(() => {
                listview.page.wrapper.find(".page-actions .btn, .page-head .btn").filter(function() {
                    return $(this).text().trim() === __("Amazon Trip Export");
                }).addClass("tms-list-btn tms-list-btn-export").prepend("📤 ");
            }, 100);
        }

        const fmt_dd = d => d.split("-").reverse().join("-");

        function getView() {
            return cur_list || listview;
        }

        function applyFilter() {
            const from = $("#atms-from-date").val();
            const to   = $("#atms-to-date").val();
            if (!from || !to) {
                frappe.show_alert({ message: "⚠️ Select both From and To dates.", indicator: "orange" }, 3);
                TMS.dateFilterBar.hideOverlay("Amazon Trip");
                return;
            }
            if (from > to) {
                frappe.show_alert({ message: "⚠️ From date cannot be after To date.", indicator: "orange" }, 3);
                TMS.dateFilterBar.hideOverlay("Amazon Trip");
                return;
            }

            const view = getView();
            if (!view) { TMS.dateFilterBar.hideOverlay("Amazon Trip"); return; }

            _atms_clear_date_filters(view);

            // Tell refresh() (below) this call's own filter_area.add() is what's
            // about to trigger it, so it doesn't fight the range just set here.
            frappe._tms_df_manual["Amazon Trip"] = true;

            // filter_area.add() is asynchronous — passing `true` lets it trigger
            // view.refresh() itself once the filter is actually registered, instead
            // of us calling refresh() synchronously right after .add() returns,
            // which re-fetches with the OLD filter state and leaves the badge
            // showing a date range the grid was never actually filtered by.
            if (view.filter_area) {
                Promise.resolve(view.filter_area.add([
                    ["Amazon Trip", "trip_date", ">=", from],
                    ["Amazon Trip", "trip_date", "<=", to],
                ], true)).then(() => {
                    $("#atms-date-badge").text(`${fmt_dd(from)}  →  ${fmt_dd(to)}`).show();
                    frappe._tms_df_manual["Amazon Trip"] = false;
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
                        Promise.resolve(p).then(() => TMS.dateFilterBar.hideOverlay("Amazon Trip"));
                    }, 1100);
                });
            } else {
                view.refresh ? view.refresh() : (view.run && view.run());
                $("#atms-date-badge").text(`${fmt_dd(from)}  →  ${fmt_dd(to)}`).show();
                TMS.dateFilterBar.hideOverlay("Amazon Trip");
                frappe._tms_df_manual["Amazon Trip"] = false;
            }
        }

        function clearFilter() {
            // Reset the bar's inputs to the default month-to-date range (so
            // they don't keep showing a stale custom date), but actually
            // remove the trip_date filter rather than re-applying that
            // default range as a still-active filter.
            $("#atms-from-date").val(todayStart);
            $("#atms-to-date").val(today);

            const view = getView();
            if (!view) return;
            frappe._tms_df_manual["Amazon Trip"] = true;
            _atms_clear_date_filters(view);
            view.refresh ? view.refresh() : (view.run && view.run());
            setTimeout(() => { frappe._tms_df_manual["Amazon Trip"] = false; }, 0);
            $("#atms-date-badge").hide();
        }

        $("#atms-apply-date").on("click", applyFilter);
        $("#atms-clear-date").on("click", clearFilter);
        $bar.find(".tms-df-inp").on("keydown", e => { if (e.key === "Enter") applyFilter(); });

        // ── Save guard (once per session) ────────────────────────────────────
        if (!frappe.model.user_settings._tms_amazon_guard) {
            frappe.model.user_settings._tms_amazon_guard = true;
            const _origSave = frappe.model.user_settings.save.bind(frappe.model.user_settings);
            frappe.model.user_settings.save = function(doctype, key, value, user) {
                if (doctype === "Amazon Trip" && key === "List" && value && Array.isArray(value.filters)) {
                    value = Object.assign({}, value, {
                        filters: value.filters.filter(f => Array.isArray(f) && f[1] === "trip_date"),
                    });
                }
                return _origSave(doctype, key, value, user);
            };
        }

        // ── Route change handler (once per session) — best-effort early masking
        // ONLY. refresh() below re-checks route_options/URL/manual-flag fresh
        // every time it runs and does NOT depend on this handler having fired;
        // an earlier design relied on a timestamped flag this handler set, but
        // that "change" event was observed to not reliably fire on every
        // cached-page sidebar revisit, silently leaving stale/unfiltered data
        // on screen.
        if (!frappe._tms_amazon_nav_guard) {
            frappe._tms_amazon_nav_guard = true;
            frappe.router.on("change", function() {
                const r = frappe.get_route();
                if (r && r[0] === "List" && r[1] === "Amazon Trip" && !frappe._tms_df_manual["Amazon Trip"]) {
                    const hasRouteOpts = !!(frappe.route_options && Object.keys(frappe.route_options).length > 0);
                    if (!hasRouteOpts) TMS.dateFilterBar.showOverlay("Amazon Trip");
                }
            });
        }

        // ── Initial load ─────────────────────────────────────────────────────
        const _fromDashboard = frappe.route_options && Object.keys(frappe.route_options).length > 0;
        setTimeout(() => {
            if (!_fromDashboard) {
                const _view = getView();
                const fl = _view && _view.filter_area && _view.filter_area.filter_list;
                if (fl && fl.filters) {
                    fl.filters
                        .filter(f => f.fieldname !== "trip_date")
                        .forEach(f => { try { f.$filter && f.$filter.remove(); } catch(e) {} });
                    fl.filters = fl.filters.filter(f => f.fieldname === "trip_date");
                }
            }
            applyFilter();
        }, 300);
    },

    // refresh() fires on EVERY navigation to this list (cached or new) —
    // guaranteed by Frappe's own base_list.js, unlike the router "change"
    // event above (best-effort only). Re-checks route_options/manual-flag
    // fresh every single time instead of trusting a pre-captured flag, so a
    // missed "change" event can never leave stale/unfiltered data on screen.
    refresh(listview) {
        frappe._tms_df_manual = frappe._tms_df_manual || {};
        TMS.dateFilterBar.registerPage("Amazon Trip", listview.$page);

        if (frappe._tms_df_manual["Amazon Trip"]) {
            TMS.dateFilterBar.hideOverlay("Amazon Trip");
            return;
        }

        const hasRouteOpts = !!(frappe.route_options && Object.keys(frappe.route_options).length > 0);
        if (hasRouteOpts) {
            TMS.dateFilterBar.hideOverlay("Amazon Trip");
        }

        if (!hasRouteOpts) {
            // Only force "today" when this refresh was triggered by a genuine
            // sidebar navigation — hide_sidebar.js stamps
            // frappe._tms_sidebar_click_ts (capture-phase, on every
            // sidebar-link click, before the route even changes). Any OTHER
            // refresh (user clearing the filter and applying a different one)
            // must NOT be fought back to today.
            const navTs = frappe._tms_sidebar_click_ts || 0;
            const isGenuineNav = (Date.now() - navTs) < 800;
            if (!isGenuineNav) {
                // Not a forced-today moment, but the bar's own inputs/badge must
                // still reflect whatever filter is ACTUALLY applied right now —
                // e.g. the user cleared/changed the date filter from Frappe's
                // own native Filters panel instead of this bar's own buttons.
                const fa2 = listview.filter_area;
                const dateFilters = fa2 && fa2.get ? fa2.get().filter(f => f[1] === "trip_date") : [];
                let _from = "", _to = "";
                dateFilters.forEach(f => {
                    const op = (f[2] || "").toLowerCase();
                    if (op === "between" && Array.isArray(f[3])) { _from = f[3][0]; _to = f[3][1]; }
                    else if (op === ">=" || op === ">") _from = f[3];
                    else if (op === "<=" || op === "<") _to = f[3];
                    else if (op === "=") { _from = f[3]; _to = f[3]; }
                });
                if (_from || _to) {
                    if (_from) $("#atms-from-date").val(_from);
                    if (_to)   $("#atms-to-date").val(_to);
                    $("#atms-date-badge").text(`${_from.split("-").reverse().join("-")}  →  ${_to.split("-").reverse().join("-")}`).show();
                } else {
                    $("#atms-date-badge").hide();
                }
                TMS.dateFilterBar.hideOverlay("Amazon Trip");
                return;
            }
            frappe._tms_sidebar_click_ts = 0;

            // Plain sidebar navigation (no dashboard route_options) — always
            // reset the bar back to the default month-to-date range instead
            // of re-applying whatever custom range was left over in the
            // inputs from a previous manual Apply.
            const _today      = frappe.datetime.get_today();
            const _todayStart = _today;
            $("#atms-from-date").val(_todayStart);
            $("#atms-to-date").val(_today);

            const fa = listview.filter_area;
            const fl = fa && fa.filter_list;
            if (fa && fl) {
                const nonDateFields = (fa.get ? fa.get() : [])
                    .filter(f => f[1] !== "trip_date")
                    .map(f => f[1]);

                if (nonDateFields.length) {
                    const origOnChange = fl.on_change;
                    fl.on_change = function() {};
                    nonDateFields.forEach(fn => { try { fa.remove(fn); } catch(e) {} });
                    fl.on_change = origOnChange;
                }
            }

            setTimeout(() => {
                const from = $("#atms-from-date").val();
                const to   = $("#atms-to-date").val();
                if (!from || !to) { TMS.dateFilterBar.hideOverlay("Amazon Trip"); return; }
                _atms_clear_date_filters(listview);
                // See the matching comment in applyFilter() — `true` lets
                // filter_area.add() trigger the refresh itself once the filter is
                // actually registered, instead of racing ahead of its own promise chain.
                if (listview.filter_area) {
                    Promise.resolve(listview.filter_area.add([
                        ["Amazon Trip", "trip_date", ">=", from],
                        ["Amazon Trip", "trip_date", "<=", to],
                    ], true)).then(() => {
                        $("#atms-date-badge")
                            .text(`${from.split("-").reverse().join("-")}  →  ${to.split("-").reverse().join("-")}`)
                            .show();
                        // Do NOT hide the overlay yet — see the matching comment in
                        // applyFilter() above: keep it up until the safety-net
                        // refresh below both confirms AND paints the correct state,
                        // so wrong rows are never visible even briefly.
                        setTimeout(() => {
                            const p = listview.refresh && listview.refresh();
                            Promise.resolve(p).then(() => TMS.dateFilterBar.hideOverlay("Amazon Trip"));
                        }, 1100);
                    });
                } else {
                    listview.refresh();
                    $("#atms-date-badge")
                        .text(`${from.split("-").reverse().join("-")}  →  ${to.split("-").reverse().join("-")}`)
                        .show();
                    TMS.dateFilterBar.hideOverlay("Amazon Trip");
                }
            }, 0);
        }
    },
};
