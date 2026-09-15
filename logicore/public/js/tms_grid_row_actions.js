// Frappe's default grid toolbar shows Edit row / Duplicate row / Delete row
// once a row checkbox is checked. This app only wants Add row and Delete row —
// Edit row and Duplicate row are hidden everywhere, for every child-table grid
// across the app.
//
// The Grid class itself (frappe/public/js/frappe/form/grid.js) is a private ES
// module — it is exported but never assigned onto frappe.ui.form, so its
// prototype cannot be reached directly. The only public, global hook is
// frappe.ui.form.ControlTable (the "Table" fieldtype control every grid field
// is built through), which owns the Grid instance as this.grid right after
// construction. So each grid instance gets its own refresh_edit_rows_button /
// refresh_duplicate_rows_button overridden — these are only ever invoked later
// (on checkbox click, or grid.refresh()), by which point the grid's DOM and
// button elements already exist.
(function () {
	if (!frappe.ui || !frappe.ui.form || !frappe.ui.form.ControlTable) return;
	if (frappe.ui.form.ControlTable.prototype._tms_row_actions_trimmed) return;

	const original_make = frappe.ui.form.ControlTable.prototype.make;
	frappe.ui.form.ControlTable.prototype.make = function () {
		original_make.apply(this, arguments);
		if (this.grid) {
			this.grid.refresh_edit_rows_button = function () {
				this.edit_rows_button.addClass("hidden");
			};
			this.grid.refresh_duplicate_rows_button = function () {
				this.duplicate_rows_button.addClass("hidden");
			};
		}
	};

	frappe.ui.form.ControlTable.prototype._tms_row_actions_trimmed = true;
})();
