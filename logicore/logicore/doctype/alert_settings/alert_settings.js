// Mirrors CHILD_DETAIL_DOCTYPES in alert_settings.py — these rules read their date/detail
// data from a child table row, not the parent doctype.
const CHILD_DETAIL_DOCTYPES = {
	"Service Logs": "Service  Replacement Item",
	"Tyre Expenses": "Tyre Expense Detail",
};

const WARMED_DOCTYPES = new Set();

// The grid's collapsed/static cell text is rendered via frappe.format(), which for
// Autocomplete/MultiSelect just prints the raw stored value. Warming the doctype's meta
// client-side lets our formatter (below) show the field label instead once it's loaded.
function ensure_doctype_meta_warmed(frm, doctype) {
	if (!doctype) return;
	[doctype, CHILD_DETAIL_DOCTYPES[doctype]].filter(Boolean).forEach((dt) => {
		if (WARMED_DOCTYPES.has(dt)) return;
		WARMED_DOCTYPES.add(dt);
		frappe.model.with_doctype(dt, () => frm.fields_dict.alert_rules.grid.refresh());
	});
}

function resolve_field_label(source_doctype, fieldname) {
	if (!source_doctype || !fieldname) return fieldname;
	const meta = frappe.get_meta(source_doctype);
	let field = meta && meta.fields.find((f) => f.fieldname === fieldname);
	if (field) return field.label || fieldname;

	const child_doctype = CHILD_DETAIL_DOCTYPES[source_doctype];
	if (child_doctype) {
		const child_meta = frappe.get_meta(child_doctype);
		field = child_meta && child_meta.fields.find((f) => f.fieldname === fieldname);
		if (field) return field.label || fieldname;
	}
	return fieldname;
}

// Shared formatter for date_field / detail_fields — detail_fields can hold several
// comma-separated fieldnames, date_field always holds exactly one.
function field_label_formatter(value, df, options, doc) {
	if (!value) return "";
	if (!doc || !doc.source_doctype) return value;
	return value
		.split(",")
		.map((v) => v.trim())
		.filter(Boolean)
		.map((v) => resolve_field_label(doc.source_doctype, v))
		.join(", ");
}

// detail_fields (MultiSelect) is deliberately excluded — its dropdown gets clipped
// inside the inline grid cell (Frappe only repositions it for Link/Autocomplete columns).
// It stays reachable via the row's expanded edit form instead.
const ALERT_RULE_COLUMNS = [
	"enabled", "rule_name", "source_doctype", "date_field",
	"alert_before_days", "upcoming_repeat_frequency", "upcoming_repeat_every_days",
	"overdue_repeat_frequency", "overdue_repeat_every_days", "overdue_window_days",
	"desk_enabled", "email_enabled", "email_recipients", "send_time",
	"show_in_list", "max_rows"
];

function inject_email_history_styles() {
	if (document.getElementById("tms-eh-style")) return;
	const s = document.createElement("style");
	s.id = "tms-eh-style";
	s.textContent = `
.tms-eh-wrap { border:1px solid var(--border-color,#e5e7eb); border-radius:8px; overflow:hidden; margin-top:4px; }
.tms-eh-table { width:100%; border-collapse:collapse; }
.tms-eh-table thead tr { background: var(--subtle-fg, #f3f4f6); }
.tms-eh-table th {
	padding:7px 10px; font-size:11px; font-weight:700; text-align:left;
	color: var(--text-color, #374151);
	border-bottom: 1px solid var(--border-color, #e5e7eb);
}
.tms-eh-table td {
	padding:7px 10px; font-size:12px;
	border-bottom: 1px solid var(--border-color, #f3f4f6);
	color: var(--text-color, #374151);
}
.tms-eh-row-even { background: var(--subtle-accent, #f9fafb); }
.tms-eh-row-odd  { background: var(--card-bg, #fff); }
.tms-eh-muted    { color: var(--text-muted, #6b7280); }
.tms-eh-empty    { padding:12px; color: var(--text-muted, #6b7280); font-size:13px; }
[data-theme="dark"] .tms-eh-row-even { background: rgba(255,255,255,0.04); }
[data-theme="dark"] .tms-eh-row-odd  { background: transparent; }
	`;
	document.head.appendChild(s);
}

frappe.ui.form.on("Alert Settings", {
	refresh(frm) {
		frm.set_query("source_doctype", "alert_rules", function () {
			return { filters: { issingle: 0, istable: 0, module: "LogiCore" } };
		});

		// Date Field / Card Fields options depend on whichever Source DocType is picked in
		// that row — fetched live from the server so any doctype works, not just hardcoded ones.
		frm.set_query("date_field", "alert_rules", function (doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			return {
				query: "logicore.logicore.doctype.alert_settings.alert_settings.get_date_field_options",
				params: { doctype: row.source_doctype },
			};
		});

		frm.set_query("detail_fields", "alert_rules", function (doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			return {
				query: "logicore.logicore.doctype.alert_settings.alert_settings.get_detail_field_options",
				params: { doctype: row.source_doctype },
			};
		});

		inject_email_history_styles();
		load_email_history(frm);

		// hide_toolbar (this is a Single settings doctype) makes toolbar.refresh()
		// call page.hide_menu() before this handler runs. The shared Help-menu
		// patch (logicore_help_2026) should add the Help item into this same "..."
		// dropdown, but there's a race condition where the item isn't added yet.
		// Manually ensure it exists, then show the menu.
		if (!frm.page._tms_help_menu_shown) {
			frm.page._tms_help_menu_shown = true;
			const enabled_doctypes = (frappe.boot.logicore_help && frappe.boot.logicore_help.enabled_doctypes) || [];
			if (enabled_doctypes.includes(frm.doctype)) {
				// Ensure Help item exists in the menu
				if (!frm.page.menu.find(".dropdown-item:contains('Help')").length) {
					frm.page.add_menu_item(__("Help"), () => {
						window.open("/help?doctype=" + encodeURIComponent(frm.doctype), "_blank");
					});
					// Move it to first position
					const $li = frm.page.menu.find("li:has(.dropdown-item:contains('Help'))").first();
					$li.prependTo($li.parent());
				}
				frm.page.show_menu();
			}
		}

		// Show the field label (not the raw fieldname) in the grid — must be set before
		// user_defined_columns below copies the docfield.
		["date_field", "detail_fields"].forEach((fieldname) => {
			const df = frappe.meta.get_docfield("Alert Rule", fieldname);
			if (df) df.formatter = field_label_formatter;
		});
		// detail_fields is stored as Small Text (MultiSelect isn't a real DB fieldtype and
		// silently drops the column on a fresh install) — force the multiselect pill widget
		// back on client-side only, same as before.
		{
			const df = frappe.meta.get_docfield("Alert Rule", "detail_fields");
			if (df) df.fieldtype = "MultiSelect";
		}
		(frm.doc.alert_rules || []).forEach((row) => ensure_doctype_meta_warmed(frm, row.source_doctype));

		const grid = frm.get_field("alert_rules").grid;

		// Force all defined columns visible regardless of user preferences
		grid.user_defined_columns = ALERT_RULE_COLUMNS.map((fieldname) => {
			const df = frappe.meta.get_docfield("Alert Rule", fieldname);
			return df ? { ...df, in_list_view: 1 } : null;
		}).filter(Boolean);

		grid.setup_columns();
		grid.refresh();
	},
});

function load_email_history(frm) {
	frappe.call({
		method: "logicore.logicore.doctype.alert_settings.alert_settings.get_alert_email_history",
		args: { limit: 50 },
		callback(r) {
			const rows = r.message || [];
			const status_color = { "Sent": "#16a34a", "Not Sent": "#ea580c", "Error": "#dc2626", "Sending": "#2563eb" };

			if (!rows.length) {
				$(frm.fields_dict.email_log_html.wrapper).html(
					`<div class="tms-eh-empty">No emails sent yet.</div>`
				);
				return;
			}

			const decode_subject = (s) => {
				// Remove MIME encoded-word =?utf-8?...?= artifacts
				return (s || "—").replace(/=\?utf-8\?[bqBQ]\?[^?]*\?=/gi, "").replace(/\s+/g, " ").trim() || "—";
			};

			const rows_html = rows.map((row, i) => {
				const color = status_color[row.status] || "#6b7280";
				const rowClass = i % 2 === 0 ? "tms-eh-row-even" : "tms-eh-row-odd";
				const dt = row.creation ? row.creation.substring(0, 16) : "";
				const subject = frappe.utils.escape_html(decode_subject(row.subject));
				const recipients = frappe.utils.escape_html((row.recipients || "—").substring(0, 80));

				let action_cell = `<span style="background:${color};color:#fff;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:700">${frappe.utils.escape_html(row.status)}</span>`;

				if (row.status === "Not Sent") {
					action_cell += ` <button
						data-queue="${frappe.utils.escape_html(row.name)}"
						class="tms-send-now-btn"
						style="margin-left:6px;padding:2px 10px;background:#1d4ed8;color:#fff;border:none;border-radius:8px;font-size:11px;font-weight:700;cursor:pointer">
						Send Now
					</button>`;
				} else if (row.status === "Error") {
					action_cell += ` <button
						data-queue="${frappe.utils.escape_html(row.name)}"
						class="tms-show-error-btn"
						style="margin-left:6px;padding:2px 10px;background:#dc2626;color:#fff;border:none;border-radius:8px;font-size:11px;font-weight:700;cursor:pointer">
						Show Error
					</button>`;
				}

				return `<tr class="${rowClass}">
					<td style="white-space:nowrap">${dt}</td>
					<td>${subject}</td>
					<td class="tms-eh-muted">${recipients}</td>
					<td style="white-space:nowrap">${action_cell}</td>
				</tr>`;
			}).join("");

			const th = `<tr>
				<th>Date</th>
				<th>Subject</th>
				<th>Recipients</th>
				<th>Status</th>
			</tr>`;

			const $wrapper = $(frm.fields_dict.email_log_html.wrapper);
			$wrapper.html(`
				<div class="tms-eh-wrap">
					<table class="tms-eh-table">
						<thead>${th}</thead>
						<tbody>${rows_html}</tbody>
					</table>
				</div>
			`);

			// Send Now button handler
			$wrapper.on("click", ".tms-send-now-btn", function () {
				const queue_name = $(this).data("queue");
				const $btn = $(this);
				$btn.prop("disabled", true).text("Sending...");
				frappe.call({
					method: "frappe.email.doctype.email_queue.email_queue.send_now",
					args: { name: queue_name },
					callback(r) {
						frappe.show_alert({ message: __("Email sent successfully."), indicator: "green" });
						load_email_history(frm);
					},
					error() {
						frappe.show_alert({ message: __("Failed to send email."), indicator: "red" });
						$btn.prop("disabled", false).text("Send Now");
					},
				});
			});

			// Show Error button handler
			$wrapper.on("click", ".tms-show-error-btn", function () {
				const queue_name = $(this).data("queue");
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						doctype: "Email Queue",
						filters: { name: queue_name },
						fieldname: "error",
					},
					callback(r) {
						const error_text = (r.message && r.message.error) || __("No error details available.");
						frappe.msgprint({
							title: __("Email Error — " + queue_name),
							message: `<pre style="white-space:pre-wrap;font-size:12px;color:#dc2626">${frappe.utils.escape_html(error_text)}</pre>`,
							indicator: "red",
						});
					},
				});
			});
		}
	});
}

frappe.ui.form.on("Alert Rule", {
	source_doctype(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.source_doctype) return;

		// Duplicate check on source_doctype + date_field combination (checked after date_field is set)


		// date_field and detail_fields are never auto-filled — the user always picks them
		// explicitly from the Date Field / Card Fields dropdowns for the chosen doctype.
		const defaults = {
			"Service Logs": { rule_name: "Service Logs - Next Service Date", alert_before_days: 7 },
			"Compliances": { rule_name: "Compliances - Expiry Date", alert_before_days: 30 },
			"Battery Expenses": { rule_name: "Battery Expenses - Warranty Expiry", alert_before_days: 30 },
			"Tyre Expenses": { rule_name: "Tyre Expenses - Warranty Expiry", alert_before_days: 30 },
		}[row.source_doctype];

		if (defaults) {
			if (!row.rule_name) frappe.model.set_value(cdt, cdn, "rule_name", defaults.rule_name);
			if (!row.alert_before_days) frappe.model.set_value(cdt, cdn, "alert_before_days", defaults.alert_before_days);
		}

		ensure_doctype_meta_warmed(frm, row.source_doctype);
	},

	date_field(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.source_doctype || !row.date_field) return;

		const duplicate = (frm.doc.alert_rules || []).find(
			(r) => r.name !== cdn
				&& r.source_doctype === row.source_doctype
				&& r.date_field === row.date_field
		);
		if (duplicate) {
			frappe.model.set_value(cdt, cdn, "date_field", "");
			frappe.msgprint(__("A rule for {0} with date field {1} already exists.", [row.source_doctype, row.date_field]));
		}
	},
});
