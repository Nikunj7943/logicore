// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// Must stay in sync with _TMS_EXPORT_SKIP_FIELDS in trip_list.js
const _BF_SKIP_FIELDS = new Set([
	"amended_from", "docstatus", "doctype", "owner", "creation", "modified",
	"modified_by", "idx", "_assign", "_comments", "_user_tags", "workflow_state",
	"origin_address_1_full", "origin_address_2_full",
	"destination_address_1_full", "destination_address_2_full",
]);

const _BF_SKIP_FIELDTYPES = new Set([
	"Section Break", "Column Break", "Tab Break", "Fold",
	"Heading", "HTML", "Button", "Image", "Attach Image",
	"Signature", "Geolocation", "Barcode", "Break",
]);

// "Applies To" (Trip / Amazon) decides which doctype's fields populate the
// Trip Export Columns table — same as Trip Type's own preset table.
function _bf_target_doctype(frm) {
	return frm.doc.applies_to === "Amazon" ? "Amazon Trip" : "Trip";
}

function _bf_build_cols_from_meta(doctype) {
	const meta = frappe.get_meta(doctype);
	if (!meta || !meta.fields) return [];
	return meta.fields.filter(f =>
		!_BF_SKIP_FIELDS.has(f.fieldname) &&
		!_BF_SKIP_FIELDTYPES.has(f.fieldtype) &&
		f.label
	).map(f => ({ fieldname: f.fieldname, label: f.label }));
}

// Section Break headings and a Table field's own label are both baked into the
// DOM once at construction time — set_df_property()/refresh_field() update the
// meta object but never touch that already-rendered text, so both need a direct
// DOM update here instead.
function _bf_update_section_label(frm) {
	const label = frm.doc.applies_to === "Amazon" ? __("Amazon Trip Export Columns") : __("Trip Export Columns");

	frm.set_df_property("section_break_trip_cols", "label", label);
	frm.set_df_property("trip_export_columns", "label", label);

	const section = (frm.layout && frm.layout.sections || [])
		.find(s => s.df && s.df.fieldname === "section_break_trip_cols");
	if (section) section.set_label(label);

	// grid.wrapper IS the ".grid-field" div itself (not a parent of it) — the
	// label is a direct child, not a ".grid-field" descendant.
	const gridField = frm.fields_dict.trip_export_columns;
	if (gridField && gridField.grid && gridField.grid.wrapper) {
		gridField.grid.wrapper.find(".control-label").first().text(label);
	}
}

// True when most of this record's saved columns don't belong to the target
// doctype's field set (e.g. a record saved before "Applies To" drove this
// table) — a signal the table needs rebuilding. Trip and Amazon Trip share a
// few field names (branch, customer, ...), so "at least one match" isn't a
// safe test — require a majority to actually belong to the target doctype.
function _bf_columns_mismatch(frm, targetDoctype) {
	const rows = frm.doc.trip_export_columns || [];
	if (!rows.length) return false;
	const meta = frappe.get_meta(targetDoctype);
	if (!meta || !meta.fields) return false;
	const validFieldnames = new Set(meta.fields.map(f => f.fieldname));
	const validCount = rows.filter(r => validFieldnames.has(r.fieldname)).length;
	return validCount < rows.length / 2;
}

function _bf_sync_columns(frm, { rebuild } = {}) {
	const targetDoctype = _bf_target_doctype(frm);

	const tryPopulate = () => {
		const cols = _bf_build_cols_from_meta(targetDoctype);
		if (!cols.length) return false;

		if (rebuild) {
			frm.clear_table("trip_export_columns");
		}

		const existing = new Set(
			(frm.doc.trip_export_columns || []).map(r => r.fieldname)
		);

		let changed = rebuild;
		cols.forEach(col => {
			if (!existing.has(col.fieldname)) {
				const row = frm.add_child("trip_export_columns");
				row.fieldname = col.fieldname;
				row.label = col.label;
				row.selected = 0;
				changed = true;
			}
		});

		if (changed) frm.refresh_field("trip_export_columns");
		return true;
	};

	if (frappe.get_meta(targetDoctype)) {
		tryPopulate();
	} else {
		frappe.model.with_doctype(targetDoctype, () => tryPopulate());
	}
}

frappe.ui.form.on("Business Format", {
	refresh(frm) {
		_bf_update_section_label(frm);
		if (!frm.doc.trip_export_columns || !frm.doc.trip_export_columns.length) {
			_bf_sync_columns(frm);
		} else {
			const targetDoctype = _bf_target_doctype(frm);
			const tryMismatchCheck = () => {
				if (_bf_columns_mismatch(frm, targetDoctype)) {
					_bf_sync_columns(frm, { rebuild: true });
				}
			};
			if (frappe.get_meta(targetDoctype)) {
				tryMismatchCheck();
			} else {
				frappe.model.with_doctype(targetDoctype, tryMismatchCheck);
			}
		}
		if (!frm.is_new()) {
			frm.set_df_property("business_format", "hidden", 0);
			frm.refresh_field("business_format");
		}
	},
	applies_to(frm) {
		_bf_update_section_label(frm);
		// Switching Trip <-> Amazon changes which doctype's fields are relevant —
		// rebuild the table from scratch instead of leaving stale fieldnames from
		// the other doctype mixed in with the new ones.
		_bf_sync_columns(frm, { rebuild: true });
	},
});
