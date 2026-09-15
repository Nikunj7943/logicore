// "Download POD" button — Trip List View (native button hook) + Trip Report View
// (ReportView.prototype patch, following the same convention already used by
// tms_report_menu_gate.js / tms_list_page_length.js / disable_report_view_inline_edit.js).
//
// Report View builds its visible columns strictly from real DocFields the user has
// selected, and the per-cell format() callback only ever sees data for columns that
// are actually rendered — there is no supported way to fetch an extra field for a
// row without it becoming a visible column. To work around this we read the raw
// server row inside build_row() (which still has every fetched field, regardless of
// which columns are shown) and write the button HTML straight into our own
// synthetic column's cell content — bypassing the column/format machinery entirely.
(function () {
	window.TMS = window.TMS || {};

	const POD_UPLOADED_STATUSES = ["Original POD Uploaded", "Duplicate POD Uploaded"];

	TMS.pod = {
		UPLOADED_STATUSES: POD_UPLOADED_STATUSES,

		download(trip_name) {
			frappe.call({
				method: "logicore.logicore.doctype.trip.trip.get_latest_pod_file",
				args: { docname: trip_name },
				callback(r) {
					if (!r.message || !r.message.file_url) {
						frappe.show_alert(
							{ message: __("⚠️ No POD found for this trip."), indicator: "orange" },
							3
						);
						return;
					}
					const a = document.createElement("a");
					a.href = r.message.file_url;
					a.download = r.message.file_name || "POD.pdf";
					document.body.appendChild(a);
					a.click();
					a.remove();
				},
			});
		},

		render_button_html(doc, opts) {
			if (!doc || !POD_UPLOADED_STATUSES.includes(doc.pod_status)) return "";
			const name = frappe.utils.escape_html(doc.name || "");
			const is_compact = Boolean(opts && opts.compact);
			const compact_class = is_compact ? " tms-pod-download-btn--compact" : "";
			const button = `
				<button type="button" class="tms-pod-download-btn${compact_class}"
					data-trip="${name}" title="${__("Download POD")}">
					<span class="tms-pod-download-icon">⬇</span> ${__("Download")}
				</button>
			`;
			// The Report View grid cell (.dt-cell__content) is a plain block box, not a
			// flex container, so the button otherwise sits low/off-center instead of
			// filling the cell. Wrap it in our own flex box to center it reliably,
			// independent of frappe-datatable's own cell CSS.
			if (!is_compact) return button;
			return `<div style="display:flex;align-items:center;justify-content:center;height:100%;width:100%;">${button}</div>`;
		},

		// List View wraps this inside Frappe's own <button> (settings.button.get_label),
		// so this must be inert markup — no nested <button> — with the click handled by
		// the button's own action() callback instead of our delegated listener.
		render_button_span() {
			return `<span class="tms-pod-download-btn">
				<span class="tms-pod-download-icon">⬇</span> ${__("Download POD")}
			</span>`;
		},
	};

	// One delegated listener for every Report View render (cells are re-created on
	// every scroll/refresh, so per-cell binding would be lost immediately).
	if (!window._tms_pod_download_click_bound) {
		$(document).on("click", ".tms-pod-download-btn", function (e) {
			e.preventDefault();
			e.stopPropagation();
			const trip_name = $(this).attr("data-trip");
			if (trip_name) TMS.pod.download(trip_name);
		});
		window._tms_pod_download_click_bound = true;
	}

	function patch_report_view() {
		const ReportView = frappe.views && frappe.views.ReportView;
		if (!ReportView || ReportView.prototype._tms_pod_column_patched) {
			return Boolean(ReportView);
		}

		const original_set_fields = ReportView.prototype.set_fields;
		ReportView.prototype.set_fields = function () {
			original_set_fields.call(this);
			if (this.doctype === "Trip") {
				this._tms_pod_status_forced = !this.fields.some((f) => f[0] === "pod_status");
				if (this._tms_pod_status_forced) {
					this._add_field("pod_status");
				}
			}
		};

		const original_setup_columns = ReportView.prototype.setup_columns;
		ReportView.prototype.setup_columns = function () {
			// Remember wherever the user last dragged our column to (if anywhere) —
			// rebuilt below, defaulting to "last" only the very first time.
			const desired_index = this._tms_pod_desired_index;

			original_setup_columns.call(this);
			if (this.doctype !== "Trip") return;

			if (this._tms_pod_status_forced) {
				// Only fetched for our own use — strip the auto-built visible column.
				this.columns = this.columns.filter((c) => c.id !== "pod_status");
				delete this.columns_map["pod_status"];
			}

			const pod_column = {
				id: "tms_pod_download",
				field: "name",
				name: "POD",
				content: "POD",
				docfield: {
					parent: "Trip",
					fieldname: "tms_pod_download",
					fieldtype: "Data",
					label: "POD",
					read_only: 1,
				},
				width: 130,
				align: "center",
				editable: false,
				sortable: false,
				resizable: true,
				focusable: false,
				dropdown: false,
			};
			if (desired_index == null || desired_index >= this.columns.length) {
				this.columns.push(pod_column);
			} else {
				this.columns.splice(desired_index, 0, pod_column);
			}
			this.columns_map[pod_column.id] = pod_column;
			this._tms_pod_column_index = this.columns.indexOf(pod_column);
			this._tms_pod_desired_index = this._tms_pod_column_index;
		};

		// switch_column() swaps two entries in this.fields by matching col.field —
		// our synthetic column reuses "name" as a placeholder field (see build_row
		// below), which isn't a real entry in this.fields, so the built-in swap
		// would silently corrupt whatever real column gets dragged next to ours.
		// Handle that case ourselves by reordering this.columns directly instead.
		const original_switch_column = ReportView.prototype.switch_column;
		ReportView.prototype.switch_column = function (col1, col2) {
			if (this.doctype === "Trip" && (col1.id === "tms_pod_download" || col2.id === "tms_pod_download")) {
				const idx1 = this.columns.indexOf(col1);
				const idx2 = this.columns.indexOf(col2);
				if (idx1 !== -1 && idx2 !== -1) {
					const cols = this.columns.slice();
					[cols[idx1], cols[idx2]] = [cols[idx2], cols[idx1]];
					this.columns = cols;
					this._tms_pod_desired_index = this.columns.findIndex((c) => c.id === "tms_pod_download");
					this._tms_pod_column_index = this._tms_pod_desired_index;
					this.refresh();
				}
				return;
			}
			return original_switch_column.call(this, col1, col2);
		};

		const original_build_row = ReportView.prototype.build_row;
		ReportView.prototype.build_row = function (d) {
			const row = original_build_row.call(this, d);
			if (this.doctype === "Trip" && this._tms_pod_column_index != null) {
				row[this._tms_pod_column_index] = {
					name: d.name,
					doctype: "Trip",
					content: TMS.pod.render_button_html(d, { compact: true }),
					editable: false,
				};
			}
			return row;
		};

		ReportView.prototype._tms_pod_column_patched = true;
		return true;
	}

	if (!patch_report_view()) {
		const patch_timer = window.setInterval(() => {
			if (patch_report_view()) {
				window.clearInterval(patch_timer);
			}
		}, 200);
	}
})();
