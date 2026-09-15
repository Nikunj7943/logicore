// Overrides Frappe's stock "Customize Quick Filters" (list view "..." menu):
//  1. Allows any value-holding field to be picked (core only allows Select/Link/Data/Int/Check —
//     Date, Datetime, Currency, Float, Text, etc. all get filtered out even though the render
//     path handles them fine).
//  2. Allows child-table fields to be picked too (core never offers these at all).
//  3. Menu item itself is hidden unless frappe.boot.tms_can_use_admin_report_menu (TMS Admin).
//  4. Selections are saved globally (Property Setter for real doctype fields, a custom field
//     on List View Settings for child-table fields) instead of per-user, so every user group
//     sees the same quick filters a TMS Admin configured — see tms_quick_filters.py.
(function () {
	// Any field that can hold a value is a valid quick filter candidate — only layout
	// fields (Section Break, Table, HTML, Button, ...) are excluded. No field is skipped
	// just because of its type (Currency, Float, Text, etc. are all fair game). A small
	// blocklist covers types that are value-types but can't function as a filter input
	// (a password box, a file/signature/map picker). Kept in sync with tms_quick_filters.py.
	const NON_FILTERABLE_FIELDTYPES = ["Password", "Signature", "Attach", "Attach Image", "Geolocation"];
	const is_filterable_fieldtype = (fieldtype) =>
		frappe.model.is_value_type(fieldtype) && !NON_FILTERABLE_FIELDTYPES.includes(fieldtype);
	const PSEUDO_FIELDNAMES = ["assigned_to", "owner", "tags"];
	const CHILD_SEPARATOR = "::";

	function is_tms_quick_filter_admin() {
		return Boolean(frappe.boot && frappe.boot.tms_can_use_admin_report_menu);
	}

	function parse_child_entries(list_view_settings) {
		try {
			return JSON.parse((list_view_settings && list_view_settings.tms_quick_filter_fields) || "[]") || [];
		} catch (e) {
			return [];
		}
	}

	function encode_child_value(entry) {
		return `${entry.doctype}${CHILD_SEPARATOR}${entry.fieldname}`;
	}

	function decode_child_value(value) {
		const idx = value.indexOf(CHILD_SEPARATOR);
		return { doctype: value.slice(0, idx), fieldname: value.slice(idx + CHILD_SEPARATOR.length) };
	}

	function get_child_table_fields(meta) {
		const child_fields = [];
		(meta.fields || [])
			.filter((f) => ["Table", "Table MultiSelect"].includes(f.fieldtype) && f.options)
			.forEach((table_df) => {
				const child_meta = frappe.get_meta(table_df.options);
				if (!child_meta) return;
				(child_meta.fields || [])
					.filter((f) => is_filterable_fieldtype(f.fieldtype))
					.forEach((f) => {
						child_fields.push({
							doctype: table_df.options,
							fieldname: f.fieldname,
							label: `${__(table_df.label)}: ${__(f.label, null, f.parent)}`,
						});
					});
			});
		return child_fields;
	}

	function build_child_standard_filter_df(field_df, child_doctype) {
		let fieldtype = field_df.fieldtype;
		let condition = "=";
		let options = field_df.options;

		if (
			["Text", "Small Text", "Text Editor", "HTML Editor", "Data", "Code", "Phone", "JSON", "Read Only"].includes(
				fieldtype
			)
		) {
			fieldtype = "Data";
			condition = "like";
		} else if (fieldtype === "Select" && options) {
			options = options.split("\n");
			if (options.length && options[0] !== "") options.unshift("");
			options = options.join("\n");
		} else if (fieldtype === "Link" && options && frappe.boot.treeviews.includes(options)) {
			condition = "descendants of (inclusive)";
		}

		return {
			fieldtype,
			label: `${__(field_df.parent)}: ${__(field_df.label, null, field_df.parent)}`,
			options,
			fieldname: field_df.fieldname,
			doctype: child_doctype,
			condition,
			is_filter: 1,
		};
	}

	function add_child_quick_filters(filter_area, list_view) {
		const entries = parse_child_entries(list_view.list_view_settings);
		if (!entries.length) return;

		entries.forEach((entry) => {
			const child_meta = frappe.get_meta(entry.doctype);
			const field_df = child_meta && child_meta.fields.find((f) => f.fieldname === entry.fieldname);
			if (!field_df) return;
			// Standard filter fields are keyed by fieldname only; skip if already used
			// (e.g. by a parent field or another child table with the same fieldname).
			if (list_view.page.fields_dict[field_df.fieldname]) return;

			const df = build_child_standard_filter_df(field_df, entry.doctype);
			df.onchange = () => filter_area.debounced_refresh_list_view();
			list_view.page.add_field(df, filter_area.standard_filters_wrapper);
		});
	}

	function patch_filter_area_instance(filter_area, list_view) {
		if (!filter_area || filter_area._tms_filter_area_patched) return;
		filter_area._tms_filter_area_patched = true;

		const original_make_standard_filters = filter_area.make_standard_filters.bind(filter_area);
		filter_area.make_standard_filters = async function () {
			await original_make_standard_filters();
			add_child_quick_filters(filter_area, list_view);
		};
	}

	function patch_base_list() {
		const BaseList = frappe.views && frappe.views.BaseList;
		// NOTE: this flag name must be unique across patch_base_list/patch_list_view/
		// patch_report_view — ListView.prototype and ReportView.prototype inherit from
		// BaseList.prototype, so a shared flag name would read as "already patched" via
		// the prototype chain and silently skip patching the subclass.
		if (!BaseList || BaseList.prototype._tms_base_list_patched) {
			return Boolean(BaseList);
		}

		const original_setup_filter_area = BaseList.prototype.setup_filter_area;
		BaseList.prototype.setup_filter_area = function (...args) {
			const result = original_setup_filter_area.apply(this, args);
			// FilterArea's constructor calls make_standard_filters() synchronously
			// during its own setup() — before we get a chance to patch the instance
			// method below — so that first (and, in practice, only) invocation always
			// runs unpatched and never adds the child-table fields. Add them directly
			// here instead of relying on the patched method ever firing again.
			add_child_quick_filters(this.filter_area, this);
			// Kept as a defensive fallback in case some code path calls
			// make_standard_filters() again later (e.g. a future core change).
			patch_filter_area_instance(this.filter_area, this);
			return result;
		};

		BaseList.prototype._tms_base_list_patched = true;
		return true;
	}

	function patch_list_view() {
		const ListView = frappe.views && frappe.views.ListView;
		if (!ListView || ListView.prototype._tms_list_view_patched) {
			return Boolean(ListView);
		}

		const original_get_menu_items = ListView.prototype.get_menu_items;
		ListView.prototype.get_menu_items = function (...args) {
			const items = original_get_menu_items.apply(this, args) || [];
			if (is_tms_quick_filter_admin()) return items;
			const label = __("Customize Quick Filters", null, "Customize qucik filters of List View");
			return items.filter((item) => item.label !== label);
		};

		ListView.prototype.get_group_by_dropdown_fields = function () {
			const child_entries = parse_child_entries(this.list_view_settings);
			const child_values = child_entries.map(encode_child_value);
			const pseudo_defaults = frappe.get_user_settings(this.doctype)?.group_by_fields || [];

			const real_fields = this.meta.fields.filter((f) => is_filterable_fieldtype(f.fieldtype));

			const default_fields_dict = [
				{ label: "Assigned To", fieldname: "assigned_to" },
				{ label: "Created By", fieldname: "owner" },
				{ label: "Tags", fieldname: "tags" },
			];

			const options = real_fields
				.map((df) => ({
					label: __(df.label, null, df.parent),
					value: df.fieldname,
					checked: Boolean(df.in_standard_filter),
				}))
				.concat(
					default_fields_dict.map((df) => ({
						label: df.label,
						value: df.fieldname,
						checked: pseudo_defaults.includes(df.fieldname),
					}))
				)
				.concat(
					get_child_table_fields(this.meta).map((cf) => {
						const value = encode_child_value(cf);
						return {
							label: cf.label,
							value,
							checked: child_values.includes(value),
						};
					})
				);

			return [
				{
					label: __(this.doctype),
					fieldname: "group_by_fields",
					fieldtype: "MultiCheck",
					columns: 2,
					options,
				},
			];
		};

		ListView.prototype.make_group_by_fields_modal = function () {
			const me = this;
			let d = new frappe.ui.Dialog({
				title: __("Select Filters"),
				fields: this.get_group_by_dropdown_fields(),
			});

			d.set_primary_action(__("Save"), ({ group_by_fields }) => {
				const selected = group_by_fields || [];
				const child_entries = selected
					.filter((v) => v.includes(CHILD_SEPARATOR))
					.map(decode_child_value);
				const pseudo_selected = selected.filter((v) => PSEUDO_FIELDNAMES.includes(v));
				const parent_fields = selected.filter(
					(v) => !v.includes(CHILD_SEPARATOR) && !PSEUDO_FIELDNAMES.includes(v)
				);

				frappe.call({
					method: "logicore.tms_quick_filters.save_tms_quick_filter_fields_api",
					args: {
						doctype: me.doctype,
						parent_fields,
						child_entries,
					},
					callback: () => {
						// Assigned To / Created By / Tags stay on the older per-user sidebar
						// stats mechanism — unrelated to the global top-of-list quick filters.
						frappe.model.user_settings.save(
							me.doctype,
							"group_by_fields",
							pseudo_selected.length ? pseudo_selected : null
						);
						d.hide();
						frappe.show_alert({ message: __("Saving Changes..."), indicator: "green" });
						setTimeout(() => {
							location.reload();
						}, 1500);
					},
				});
			});

			d.$body.prepend(`
				<div class="filters-search">
					<input type="text"
						placeholder="${__("Search")}"
						data-element="search" class="form-control input-xs">
				</div>
			`);

			frappe.utils.setup_search(d.$body, ".unit-checkbox", ".label-area");
			d.show();
		};

		ListView.prototype._tms_list_view_patched = true;
		return true;
	}

	function patch_report_view() {
		// Report View has its own separate menu-building method (report_menu_items),
		// unrelated to ListView.get_menu_items — it never included "Customize Quick
		// Filters" at all, for anyone. Add it here, admin-only, reusing the same
		// make_group_by_fields_modal inherited from ListView.prototype above.
		const ReportView = frappe.views && frappe.views.ReportView;
		if (!ReportView || ReportView.prototype._tms_report_view_patched) {
			return Boolean(ReportView);
		}

		const original_report_menu_items = ReportView.prototype.report_menu_items;
		ReportView.prototype.report_menu_items = function (...args) {
			const items = original_report_menu_items.apply(this, args) || [];
			if (!is_tms_quick_filter_admin()) return items;

			return items.concat([
				{
					label: __("Customize Quick Filters", null, "Customize qucik filters of List View"),
					action: () => this.make_group_by_fields_modal(),
					standard: true,
				},
			]);
		};

		ReportView.prototype._tms_report_view_patched = true;
		return true;
	}

	function try_patch() {
		const list_view_ok = patch_list_view();
		const base_list_ok = patch_base_list();
		const report_view_ok = patch_report_view();
		return list_view_ok && base_list_ok && report_view_ok;
	}

	if (!try_patch()) {
		const patch_timer = window.setInterval(() => {
			if (try_patch()) {
				window.clearInterval(patch_timer);
			}
		}, 200);
	}
})();
