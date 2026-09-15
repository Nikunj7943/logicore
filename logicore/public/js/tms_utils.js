// LogiCore — Shared JS Utilities
// Indian locale: currency, number, date formatting

window.TMS = window.TMS || {};

// ── CURRENCY ─────────────────────────────────────────────────────

TMS.formatINR = function (value) {
	if (value === null || value === undefined || value === "") return "₹0.00";
	return "₹" + Number(value).toLocaleString("en-IN", {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	});
};

TMS.formatINRShort = function (value) {
	const v = Number(value) || 0;
	if (v >= 1e7) return "₹" + (v / 1e7).toFixed(2) + " Cr";
	if (v >= 1e5) return "₹" + (v / 1e5).toFixed(2) + " L";
	return TMS.formatINR(v);
};

// ── DATE ─────────────────────────────────────────────────────────

// Display: DD-MM-YYYY | Storage: YYYY-MM-DD (Frappe standard)
TMS.formatIndianDate = function (dateStr) {
	if (!dateStr) return "";
	const [y, m, d] = String(dateStr).split("-");
	if (!d) return dateStr;
	return `${d}-${m}-${y}`;
};

// ── QUERY REPORT DOWNLOAD (CSV/Excel/PDF) ──────────────────────────
// DISABLED: TMS Stock Ledger/Summary switched to their own self-contained
// download code (matching TDS Report's pattern exactly) after this shared
// version caused a confusing bug — it lives in a bundled global asset, so a
// plain `bench clear-cache` (which is enough for report-local .js files)
// silently kept serving the stale pre-change version until `bench build`
// ran. Kept here, not deleted, in case a future shared version is wanted
// with that caveat understood up front.
//
// TMS.downloadReportData = function (report, fileFormat) {
// 	open_url_post(frappe.request.url, {
// 		cmd: "frappe.desk.query_report.export_query",
// 		report_name: report.report_name,
// 		file_format_type: fileFormat,
// 		filters: frappe.query_report.get_filter_values(true),
// 		visible_idx: [],
// 		ignore_visible_idx: true,
// 	});
// };
//
// TMS.downloadReportPdf = function (report, opts) {
// 	const { title, filenamePrefix, orientation } = opts;
// 	const filters = frappe.query_report.get_filter_values();
// 	const columns = (frappe.query_report.columns || []).filter(
// 		(c) => !c.hidden && !["ref_doctype", "sr_no"].includes(c.fieldname)
// 	);
// 	const data = (frappe.query_report.data || []).filter((row) => row._type !== "total");
// 	const totalRow = (frappe.query_report.data || []).find((row) => row._type === "total");
//
// 	const fmtCur = (v) => {
// 		if (v === null || v === undefined || v === "") return "";
// 		return "₹ " + parseFloat(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
// 	};
//
// 	const companyName = filters.company || "";
// 	const fromDate = filters.from_date ? frappe.datetime.str_to_user(filters.from_date) : "";
// 	const toDate = filters.to_date ? frappe.datetime.str_to_user(filters.to_date) : "";
// 	const period = fromDate || toDate ? `${fromDate || "—"} → ${toDate || "—"}` : "";
//
// 	const pill = (lbl, val) => `<span class="pill"><b>${lbl}:</b> ${frappe.utils.escape_html(String(val))}</span>`;
// 	let pillsHtml = period ? pill("Period", period) : "";
// 	Object.keys(filters).forEach((fieldname) => {
// 		if (["company", "from_date", "to_date"].includes(fieldname)) return;
// 		if (filters[fieldname]) {
// 			pillsHtml += pill(fieldname.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()), filters[fieldname]);
// 		}
// 	});
//
// 	const amtTypes = new Set(["Currency", "Float", "Int", "Percent"]);
// 	const headHtml = columns
// 		.map((col) => `<th${amtTypes.has(col.fieldtype) ? ' class="amt"' : ""}>${col.label}</th>`)
// 		.join("");
//
// 	const rowHtml = (row, isTotal) =>
// 		"<tr" +
// 		(isTotal ? ' class="total-row"' : "") +
// 		">" +
// 		columns
// 			.map((col, idx) => {
// 				const isAmt = amtTypes.has(col.fieldtype);
// 				if (isTotal) {
// 					if (idx === 0) return `<td><strong>${__("Total")}</strong></td>`;
// 					const val = row[col.fieldname];
// 					if (val === null || val === undefined || val === "") return "<td></td>";
// 					const shown = col.fieldtype === "Currency" ? fmtCur(val) : val;
// 					return `<td${isAmt ? ' class="amt"' : ""}><strong>${shown}</strong></td>`;
// 				}
// 				const raw = row[col.fieldname];
// 				const shown = col.fieldtype === "Currency" ? fmtCur(raw) : raw != null ? String(raw) : "";
// 				return `<td${isAmt ? ' class="amt"' : ""}>${frappe.utils.escape_html(shown)}</td>`;
// 			})
// 			.join("") +
// 		"</tr>";
//
// 	let bodyHtml = data.map((row) => rowHtml(row, false)).join("");
// 	if (totalRow) bodyHtml += rowHtml(totalRow, true);
//
// 	const today = frappe.datetime.str_to_user(frappe.datetime.get_today());
//
// 	const html = `<!DOCTYPE html>
// <html>
// <head>
// <meta charset="UTF-8">
// <title>${title} — ${companyName}</title>
// <style>
//   * { box-sizing: border-box; margin: 0; padding: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; color-adjust: exact; }
//   body { font-family: Arial, sans-serif; font-size: 11px; color: #222; background: #fff; padding: 24px 28px; }
//
//   .report-header { text-align: center; margin-bottom: 4px; }
//   .report-header .company { font-size: 15px; font-weight: 700; color: #1a1a2e; }
//   .report-header h2 { font-size: 19px; font-weight: 700; letter-spacing: 0.5px; color: #1a1a2e; margin-top: 2px; }
//   .header-rule { border: none; border-top: 2.5px solid #1a1a2e; margin: 6px auto 10px; width: 55%; }
//
//   .pills { text-align: center; margin-bottom: 16px; }
//   .pill { display: inline-block; background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 20px;
//           padding: 3px 11px; margin: 2px 4px; font-size: 10.5px; color: #3730a3; }
//   .pill b { color: #1e1b4b; }
//
//   table { width: 100%; border-collapse: collapse; font-size: 10px; table-layout: fixed; }
//   thead th { background: #1e3a5f; color: #fff; padding: 6px 6px; border: 1px solid #16304f;
//              font-size: 10px; text-align: left; word-wrap: break-word; overflow-wrap: break-word; }
//   thead th.amt { text-align: right; }
//   tbody td { padding: 4px 6px; border: 1px solid #e5e7eb; vertical-align: middle;
//              word-wrap: break-word; overflow-wrap: break-word; }
//   tbody td.amt { text-align: right; }
//   tbody tr:nth-child(even) td { background: #f8faff; }
//   tbody tr.total-row td { background: #f0f4f8; border-top: 2px solid #64748b; font-weight: 700; }
//
//   .report-footer { margin-top: 14px; display: flex; justify-content: space-between;
//                    font-size: 10px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 6px; }
//
//   @page { margin: 1cm; size: ${orientation === "Portrait" ? "A4 portrait" : "A4 landscape"}; }
// </style>
// </head>
// <body>
//   <div class="report-header">
//     <div class="company">${frappe.utils.escape_html(companyName)}</div>
//     <h2>${title}</h2>
//     <hr class="header-rule">
//   </div>
//   ${pillsHtml ? `<div class="pills">${pillsHtml}</div>` : ""}
//
//   <table>
//     <thead><tr>${headHtml}</tr></thead>
//     <tbody>${bodyHtml}</tbody>
//   </table>
//
//   <div class="report-footer">
//     <span>LogiCore</span>
//     <span>Generated: ${today}</span>
//   </div>
// </body>
// </html>`;
//
// 	frappe.render_pdf(html, {
// 		orientation,
// 		report_name: `${filenamePrefix}_${companyName || "LogiCore"}.pdf`.replace(/\s+/g, "_"),
// 	});
// };

// ── EXPORT-DIALOG SEARCHABLE DROPDOWN ──────────────────────────────
// Shared by trip_list.js and amazon_trip_list.js's custom "Export" dialogs
// (Company/Branch/Business Format/Trip Type/Customer/Vendor filters).

TMS.injectExportFilterStyles = function () {
	if (document.getElementById("tms-ef-style")) return;
	const s = document.createElement("style");
	s.id = "tms-ef-style";
	s.textContent = `
.tms-ef-wrap{padding:4px 0 6px;}
.tms-ef-title{font-weight:700;font-size:13px;color:var(--primary,#3B4FE4);margin-bottom:10px;}
.tms-ef-grid{display:grid;gap:8px 10px;margin-bottom:10px;}
.tms-ef-g3{grid-template-columns:repeat(3,1fr);}
.tms-ef-g4{grid-template-columns:repeat(4,1fr);}
.tms-ef-g6{grid-template-columns:repeat(6,1fr);}
.tms-ef-item{display:flex;flex-direction:column;gap:2px;}
.tms-ef-lbl{font-size:11px;font-weight:600;color:var(--text-muted,#6B7280);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.tms-ef-ctrl{height:28px;padding:0 6px;font-size:12px;border:1px solid var(--border-color,#CBD5E1);border-radius:4px;background:var(--control-bg,#fff);color:var(--text-color,#1E293B);width:100%;box-sizing:border-box;}
.tms-ef-ctrl:focus{border-color:var(--primary,#3B4FE4);outline:none;box-shadow:0 0 0 2px rgba(59,79,228,0.12);}
.tms-ef-dropdown-wrapper{position:relative;width:100%;}
.tms-ef-search{position:relative;padding-right:28px;}
.tms-ef-search::after{content:'▼';position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:10px;color:var(--text-muted,#6B7280);pointer-events:none;}
/* Custom dropdown list styling — hard show/hide (no height transition) so a scrolled
   list can never leave a visible sliver behind when it closes */
.tms-ef-dropdown-list{display:none;position:absolute;top:100%;left:0;right:0;background:var(--control-bg,#fff);border:1px solid var(--border-color,#CBD5E1);border-top:none;border-bottom-left-radius:4px;border-bottom-right-radius:4px;margin:0;padding:4px 0;max-height:240px;overflow-y:auto;z-index:1000;list-style:none;box-shadow:0 4px 12px rgba(0,0,0,0.15);}
.tms-ef-dropdown-list.tms-ef-dropdown-active{display:block;border-color:var(--primary,#3B4FE4);}
.tms-ef-dropdown-item{padding:8px 10px;font-size:12px;cursor:pointer;color:var(--text-color,#1E293B);transition:background 0.1s ease;}
.tms-ef-dropdown-item:hover,.tms-ef-dropdown-item.tms-ef-dropdown-hover{background:var(--gray-200,#E5E7EB);}
.tms-ef-dropdown-item.tms-ef-dropdown-selected{background:var(--primary,#3B4FE4);color:#fff;font-weight:500;}
	`;
	document.head.appendChild(s);
};

// Replace a plain <select data-filter="..."> with a type-to-search input + dropdown list.
TMS.makeSearchableSelect = function ($sel, filterKey, options) {
	if (!options.length) return;

	const dropdownId = `tms-dropdown-${filterKey}-${Date.now()}`;

	const $wrapper = $(`
<div class="tms-ef-dropdown-wrapper">
  <input type="text" class="tms-ef-ctrl tms-ef-search" placeholder="Type to search..." data-filter="${filterKey}" autocomplete="off">
  <ul class="tms-ef-dropdown-list" id="${dropdownId}"></ul>
</div>`);

	const $input = $wrapper.find("input");
	const $list = $wrapper.find("ul");

	options.forEach(opt => {
		$list.append(`<li class="tms-ef-dropdown-item" data-value="${opt}">${opt}</li>`);
	});

	$sel.replaceWith($wrapper);

	$input.on("focus", function () {
		$list.addClass("tms-ef-dropdown-active");
	});

	$input.on("input", function () {
		const searchVal = $(this).val().toLowerCase();
		$list.find(".tms-ef-dropdown-item").each(function () {
			const itemText = $(this).text().toLowerCase();
			$(this).toggle(itemText.includes(searchVal));
		});
	});

	// Select item from dropdown. Uses "mousedown" + preventDefault (not "click")
	// so the input never loses focus as a side effect of the click: a plain click
	// handler fires AFTER the browser's own focus-shift/blur, and that blur fires
	// a native "change" event first — with whatever raw text the user had typed
	// (e.g. "vf"), not the actual item being selected (e.g. "RR-VF (GROCERY)").
	//
	// Even with that fixed, if the user typed anything before clicking, the
	// browser still treats the field as "edited" and fires its own native
	// "change" when we call .blur() below — with the correct value this time
	// (we've already set it), but as a second, duplicate event on top of our
	// own manual trigger(). ignoreNextNativeChange swallows exactly that one
	// duplicate (native events carry a real e.originalEvent; our own
	// trigger("change") does not, so the manual one is never suppressed).
	let ignoreNextNativeChange = false;
	$input.on("change", function (e) {
		if (e.originalEvent && ignoreNextNativeChange) {
			ignoreNextNativeChange = false;
			e.stopImmediatePropagation();
		}
	});

	const selectItem = ($li) => {
		const val = $li.data("value");
		ignoreNextNativeChange = true;
		$input.val(val).trigger("change");
		$input.blur();
		ignoreNextNativeChange = false;
	};
	$list.on("mousedown", ".tms-ef-dropdown-item", function (e) {
		e.preventDefault();
		selectItem($(this));
	});

	// Close dropdown on blur — hide instantly and reset scroll so a scrolled-down
	// list always reopens (and closes) cleanly from the top, never mid-scroll.
	$input.on("blur", function () {
		setTimeout(() => {
			$list.removeClass("tms-ef-dropdown-active");
			$list.scrollTop(0);
			$list.find(".tms-ef-dropdown-hover").removeClass("tms-ef-dropdown-hover");
		}, 150);
	});

	$input.on("keydown", function (e) {
		if (e.key === "ArrowDown") {
			e.preventDefault();
			$list.find(".tms-ef-dropdown-item:visible").first().addClass("tms-ef-dropdown-hover");
		} else if (e.key === "ArrowUp") {
			e.preventDefault();
			$list.find(".tms-ef-dropdown-item.tms-ef-dropdown-hover").removeClass("tms-ef-dropdown-hover");
		} else if (e.key === "Enter") {
			e.preventDefault();
			const $hovered = $list.find(".tms-ef-dropdown-item.tms-ef-dropdown-hover");
			if ($hovered.length) {
				selectItem($hovered);
			} else {
				$input.blur();
			}
		} else if (e.key === "Escape") {
			$input.blur();
		}
	});
};

// ── ADDRESS QUICK ENTRY ───────────────────────────────────────────
// DISABLED: this override replaced india_compliance's AddressQuickEntryForm,
// which provides the Link Document Type / Link Name fields, GSTIN autofill,
// and auto-linking of the Address to the Customer/Supplier it was created
// from. Losing that broke "new Customer → Primary Address" linking.
// city/state filtering is unnecessary anyway: both fields are read_only via
// Property Setter, so Quick Entry already excludes them from meta docfields,
// and the server fills them from custom_cityname in before_validate.
// frappe.provide("frappe.ui.form");
// frappe.ui.form.AddressQuickEntryForm = class AddressQuickEntryForm extends frappe.ui.form.QuickEntryForm {
// 	set_meta_and_mandatory_fields() {
// 		super.set_meta_and_mandatory_fields();
// 		this.docfields = this.docfields.filter(
// 			(df) => !["city", "state"].includes(df.fieldname)
// 		);
// 	}
// };

// ACTIVE: city/state are auto-filled server-side from custom_cityname
// (before_validate hook), so hide them in Quick Entry — but extend
// india_compliance's AddressQuickEntryForm (not the base QuickEntryForm)
// to keep its Link Document Type / Link Name fields, party auto-fill
// and links-table mapping.
frappe.provide("frappe.ui.form");
if (frappe.ui.form.AddressQuickEntryForm) {
	// india_compliance.set_state_options assumes a "state" field exists in
	// the dialog; guard it since we remove that field below.
	if (window.india_compliance && india_compliance.set_state_options) {
		const _tms_orig_set_state_options = india_compliance.set_state_options;
		india_compliance.set_state_options = function (frm) {
			if (!frm.get_field || !frm.get_field("state")) return;
			return _tms_orig_set_state_options.call(this, frm);
		};
	}

	frappe.ui.form.AddressQuickEntryForm = class TMSAddressQuickEntryForm extends (
		frappe.ui.form.AddressQuickEntryForm
	) {
		get_address_fields() {
			const fields = super.get_address_fields().filter(
				(df) => !["city", "state"].includes(df.fieldname)
			);
			// move address_line2 into the second column (after country) so
			// Address Line 1 and Address Line 2 render side by side
			const line2_idx = fields.findIndex((df) => df.fieldname === "address_line2");
			if (line2_idx > -1) {
				const [line2] = fields.splice(line2_idx, 1);
				const country_idx = fields.findIndex((df) => df.fieldname === "country");
				fields.splice(country_idx > -1 ? country_idx + 1 : fields.length, 0, line2);
			}
			return fields;
		}
	};
}

// ── AUTO-REFRESH PARENT ON NEW ADDRESS/CONTACT ───────────────────
// Frappe's stock "+ New" button in the Address & Contacts section
// (address_html / contact_html) only reloads the parent form when Address
// Autocomplete (Geolocation Settings) is enabled — see
// frappe/public/js/frappe/utils/address_and_contact.js new_record(). With
// it disabled (this site's default), frappe.new_doc() opens the quick
// entry with no after-save callback, so a freshly created Address/Contact
// never appears on Customer/Supplier/Company/etc. until a manual reload.
// This works for ANY doctype with these fields, so it's a wildcard "*"
// hook instead of duplicating it per doctype. Only saved (non-new) parent
// docs are handled here — new/unsaved docs go through their own
// doctype-specific flow (e.g. customer.js's _logicore_ensure_saved).
frappe.ui.form.on("*", {
	refresh(frm) {
		TMS.hook_address_contact_reload(frm, "address_html", "Address");
		TMS.hook_address_contact_reload(frm, "contact_html", "Contact");
	},
});

TMS.hook_address_contact_reload = function (frm, fieldname, doctype) {
	const field = frm.fields_dict && frm.fields_dict[fieldname];
	if (!field || !field.wrapper || field.wrapper._tms_reload_patched) return;
	field.wrapper._tms_reload_patched = true;

	const btn_selector = doctype === "Address" ? ".btn-address" : ".btn-contact";

	field.wrapper.addEventListener(
		"click",
		function (e) {
			if (frm.is_new()) return;
			if (doctype === "Address" && frappe.boot.enable_address_autocompletion === 1) return;

			const target = e.target.closest(btn_selector);
			if (!target) return;

			e.preventDefault();
			e.stopImmediatePropagation();

			frappe.dynamic_link = { doctype: frm.doc.doctype, doc: frm.doc, fieldname: "name" };
			frappe.ui.form.make_quick_entry(doctype, () => frm.reload_doc(), null, null, false, false);
		},
		true
	);
};

// Frappe's Report/List View sort selector does not reliably pick up a
// doctype's sort_field on every SPA navigation — observed on Account Ledger:
// a fresh full page load (or the very first visit this session) correctly
// resolves it, but navigating to another Report View and back via the
// sidebar can leave the selector on "name" instead, even though
// frappe.get_meta(doctype).sort_field is correct the whole time and a hard
// reload immediately fixes it. Root cause is inside sort_selector.js's
// options/state handling, not anything in this app's own config — same
// class of issue tms_date_filter_bar.js already works around for date
// filters (see its refresh() design note), so re-applying on every refresh()
// (not just onload()) matches the pattern known to actually hold up.
TMS.enforceDefaultSort = function (listview, { fieldname, order }) {
	const selector = listview.sort_selector;
	if (!selector) return;
	if (selector.sort_by === fieldname && selector.sort_order === order) return;
	if (listview._tms_sort_correcting) return;
	listview._tms_sort_correcting = true;
	selector.set_value(fieldname, order);
	listview.on_sort_change(fieldname, order);
	listview._tms_sort_correcting = false;
};
