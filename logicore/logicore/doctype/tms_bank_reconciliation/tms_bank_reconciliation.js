function open_matched_record_dialog(frm, row) {
	if (!row.matched_source) {
		frappe.msgprint(__("Pick a Matched Source first."));
		return;
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Select Matched Record"),
		size: "large",
		fields: [
			{
				fieldtype: "Data",
				fieldname: "search_txt",
				label: __("Search"),
				placeholder: __("Search by ID or any shown column..."),
			},
			{ fieldtype: "HTML", fieldname: "results_html" },
		],
	});

	function render(data) {
		const columns = data.columns || [];
		const rows = data.rows || [];
		const $wrapper = dialog.fields_dict.results_html.$wrapper;

		if (!columns.length) {
			$wrapper.html(`<p class="text-muted">${__("Pick a Matched Source first.")}</p>`);
			return;
		}

		let html = `<div style="max-height: 50vh; overflow: auto;">
			<table class="table table-bordered table-hover" style="margin-bottom: 0;">
				<thead><tr>${columns.map((c) => `<th>${frappe.utils.escape_html(c.label)}</th>`).join("")}</tr></thead>
				<tbody>`;

		if (!rows.length) {
			html += `<tr><td colspan="${columns.length}" class="text-muted text-center">${__(
				"No matching records found in this reconciliation's date range."
			)}</td></tr>`;
		}

		rows.forEach((r) => {
			html += `<tr class="matched-record-row" data-name="${frappe.utils.escape_html(
				r.name
			)}" style="cursor: pointer;">`;
			columns.forEach((c) => {
				const val = r[c.fieldname];
				html += `<td>${frappe.utils.escape_html(val == null ? "" : String(val))}</td>`;
			});
			html += "</tr>";
		});
		html += "</tbody></table></div>";

		$wrapper.html(html);
		$wrapper.find(".matched-record-row").on("click", function () {
			frappe.model.set_value(row.doctype, row.name, "matched_docname", $(this).attr("data-name"));
			dialog.hide();
		});
	}

	function fetch(txt) {
		frappe.call({
			method: "logicore.utils.bank_reconciliation_utils.get_matched_record_table",
			args: {
				matched_source: row.matched_source,
				bank_reconciliation: frm.doc.name,
				direction: row.direction,
				txt: txt || "",
				current_row_name: row.name,
			},
			callback(r) {
				render(r.message || {});
			},
		});
	}

	dialog.fields_dict.search_txt.$input.on(
		"input",
		frappe.utils.debounce(() => fetch(dialog.get_value("search_txt")), 300)
	);

	dialog.show();
	fetch("");
}

frappe.ui.form.on("TMS Bank Reconciliation Transaction", {
	pick_matched_record(frm, cdt, cdn) {
		open_matched_record_dialog(frm, locals[cdt][cdn]);
	},
});

function build_period_summary_html(rows, show_matched) {
	const total_count = rows.reduce((s, r) => s + r.count, 0);
	const total_matched = rows.reduce((s, r) => s + (r.matched_count || 0), 0);
	const total_amount = rows.reduce((s, r) => s + r.total_amount, 0);
	const active_sources = rows.filter((r) => r.count > 0).length;

	const style = `
		<style>
			.brc-summary-wrap { width: 100%; }
			.brc-cards-grid {
				display: grid;
				grid-template-columns: repeat(${show_matched ? 4 : 3}, 1fr);
				gap: 12px;
				margin-bottom: 16px;
			}
			@media (max-width: 768px) { .brc-cards-grid { grid-template-columns: repeat(2, 1fr); } }
			@media (max-width: 480px) { .brc-cards-grid { grid-template-columns: 1fr; } }
			.brc-card {
				background: var(--card-bg);
				border: 1px solid var(--border-color);
				border-radius: 8px;
				padding: 14px 16px;
				text-align: center;
			}
			.brc-card-label {
				font-size: 11px;
				color: var(--text-muted);
				text-transform: uppercase;
				letter-spacing: .6px;
				margin-bottom: 6px;
			}
			.brc-card-value { font-size: 20px; font-weight: 700; }
			.brc-table-scroll {
				width: 100%;
				overflow-x: auto;
				border-radius: 8px;
				border: 1px solid var(--border-color);
			}
			.brc-table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 640px; }
			.brc-table thead tr { background: #1a73e8; color: #fff; }
			.brc-table th {
				padding: 10px 14px;
				text-align: left;
				font-weight: 600;
				position: sticky;
				top: 0;
			}
			.brc-table th.brc-num, .brc-table td.brc-num { text-align: right; }
			.brc-table td {
				padding: 9px 14px;
				border-bottom: 1px solid var(--border-color);
				color: var(--text-color);
				white-space: nowrap;
			}
			.brc-table tbody tr:hover { background: var(--control-bg); }
			.brc-table tbody tr.brc-zero-row { color: var(--text-muted); }
			.brc-table tbody tr.brc-zero-row td { color: var(--text-muted); }
			.brc-table tfoot td {
				padding: 10px 14px;
				border-top: 2px solid var(--border-color);
				background: var(--control-bg);
				font-weight: 700;
			}
			.brc-body-scroll { max-height: 360px; overflow-y: auto; }
		</style>
	`;

	const cards = `
		<div class="brc-cards-grid">
			<div class="brc-card" style="border-top: 3px solid var(--blue);">
				<div class="brc-card-label">${__("Sources with Activity")}</div>
				<div class="brc-card-value">${active_sources} / ${rows.length}</div>
			</div>
			<div class="brc-card" style="border-top: 3px solid var(--green);">
				<div class="brc-card-label">${__("Total Transactions")}</div>
				<div class="brc-card-value">${total_count}</div>
			</div>
			${show_matched ? `
				<div class="brc-card" style="border-top: 3px solid var(--blue);">
					<div class="brc-card-label">${__("Matched")}</div>
					<div class="brc-card-value">${total_matched} / ${total_count}</div>
				</div>
			` : ""}
			<div class="brc-card" style="border-top: 3px solid var(--orange);">
				<div class="brc-card-label">${__("Total Amount")}</div>
				<div class="brc-card-value">${format_currency(total_amount)}</div>
			</div>
		</div>
	`;

	const total_matched_amount = rows.reduce((s, r) => s + (r.matched_amount || 0), 0);
	const total_remaining_amount = rows.reduce((s, r) => s + (r.remaining_amount ?? r.total_amount), 0);

	const body = rows
		.map((row) => `
			<tr class="${row.count === 0 ? "brc-zero-row" : ""}">
				<td>${frappe.utils.escape_html(row.label)}</td>
				<td class="brc-num">${row.count}</td>
				${show_matched ? `<td class="brc-num">${row.matched_count || 0}</td>` : ""}
				<td class="brc-num">${format_currency(row.total_amount)}</td>
				${show_matched ? `<td class="brc-num">${format_currency(row.matched_amount || 0)}</td>` : ""}
				${show_matched ? `<td class="brc-num">${format_currency(row.remaining_amount ?? row.total_amount)}</td>` : ""}
			</tr>
		`)
		.join("");

	const table = `
		<div class="brc-table-scroll">
			<div class="brc-body-scroll">
				<table class="brc-table">
					<thead>
						<tr>
							<th>${__("Source")}</th>
							<th class="brc-num">${__("Count")}</th>
							${show_matched ? `<th class="brc-num">${__("Matched")}</th>` : ""}
							<th class="brc-num">${__("Amount")}</th>
							${show_matched ? `<th class="brc-num">${__("Matched Amount")}</th>` : ""}
							${show_matched ? `<th class="brc-num">${__("Remaining Amount")}</th>` : ""}
						</tr>
					</thead>
					<tbody>${body}</tbody>
					<tfoot>
						<tr>
							<td>${__("Total")}</td>
							<td class="brc-num">${total_count}</td>
							${show_matched ? `<td class="brc-num">${total_matched}</td>` : ""}
							<td class="brc-num">${format_currency(total_amount)}</td>
							${show_matched ? `<td class="brc-num">${format_currency(total_matched_amount)}</td>` : ""}
							${show_matched ? `<td class="brc-num">${format_currency(total_remaining_amount)}</td>` : ""}
						</tr>
					</tfoot>
				</table>
			</div>
		</div>
	`;

	return `<div class="brc-summary-wrap">${style}${cards}${table}</div>`;
}

function sync_reconciliation_setting(frm, { silent = false } = {}) {
	if (!frm.doc.bank_account) {
		return Promise.resolve();
	}
	return frappe.db.get_value(
		"TMS Bank Reconciliation Setting",
		{ bank_account: frm.doc.bank_account },
		"name"
	).then(({ message }) => {
		if (message && message.name) {
			// Must return set_value's own promise, not just call it -- callers
			// (validate(frm) below) await this whole chain before letting Save
			// proceed. Without the return, this outer promise resolved the
			// instant set_value was *called*, not once it actually finished
			// writing reconciliation_setting into frm.doc -- so Save could still
			// race ahead and submit the field as blank even though it visibly
			// fills in moments later.
			return frm.set_value("reconciliation_setting", message.name);
		} else if (!silent) {
			return frm.set_value("reconciliation_setting", "").then(() => {
				frappe.msgprint({
					title: __("No Reconciliation Setting Found"),
					message: __(
						"No TMS Bank Reconciliation Setting exists yet for this Bank Account. Create one first."
					),
					indicator: "orange",
				});
			});
		}
	});
}

function refresh_period_summary(frm) {
	const $wrapper = frm.fields_dict.period_summary_html.$wrapper;
	if (!frm.doc.bank_account || !frm.doc.from_date || !frm.doc.to_date) {
		$wrapper.html("");
		return;
	}
	// Only a saved document actually has transactions/a matched_source to
	// count against — an unsaved (new) form has nothing to match yet, so the
	// "Matched" column stays hidden until this doc has a real name.
	const show_matched = !frm.is_new();
	frappe.call({
		method: "logicore.utils.bank_reconciliation_utils.get_period_transaction_summary",
		args: {
			bank_account: frm.doc.bank_account,
			from_date: frm.doc.from_date,
			to_date: frm.doc.to_date,
			bank_reconciliation: show_matched ? frm.doc.name : null,
		},
		callback(r) {
			const rows = r.message || [];
			if (!rows.length) {
				$wrapper.html(`<p class="text-muted">${__("No active TMS Reconciliation Source is configured yet.")}</p>`);
				return;
			}
			$wrapper.html(build_period_summary_html(rows, show_matched));
		},
	});
}

function style_parse_match_btn(frm) {
	const field = frm.get_field("parse_and_match_btn");
	if (!field || !field.$wrapper) return;
	const $btn = field.$wrapper.find("button");
	if (!$btn.length) return;
	$btn.css({
		background: "linear-gradient(135deg, #1a73e8 0%, #4f9cf9 100%)",
		color: "#fff",
		"font-weight": "700",
		"font-size": "13px",
		padding: "8px 24px",
		border: "none",
		"border-radius": "8px",
		"box-shadow": "0 4px 14px rgba(26,115,232,0.4)",
		cursor: "pointer",
		"letter-spacing": "0.4px",
		transition: "all 0.2s ease",
	});
	$btn.off("mouseenter.brc_parse_match mouseleave.brc_parse_match");
	$btn.on("mouseenter.brc_parse_match", function () {
		$(this).css({ transform: "translateY(-1px)", "box-shadow": "0 6px 18px rgba(26,115,232,0.5)" });
	}).on("mouseleave.brc_parse_match", function () {
		$(this).css({ transform: "translateY(0)", "box-shadow": "0 4px 14px rgba(26,115,232,0.4)" });
	});
}

frappe.ui.form.on("TMS Bank Reconciliation", {
	refresh(frm) {
		frm.fields_dict.transactions.grid.toggle_checkboxes(false);
		frm.trigger("toggle_submit_button");
		refresh_period_summary(frm);
		style_parse_match_btn(frm);

		// Bank Account arriving via route_options (e.g. "+ New" from a
		// filtered list, or a duplicated doc) doesn't reliably fire the
		// bank_account(frm) field trigger below -- reconciliation_setting is
		// mandatory and read-only, so a doc left in that state can never be
		// saved even though a matching Setting genuinely exists. Silent here
		// (no "not found" popup) since this runs on every refresh, not just
		// on a deliberate field change.
		if (frm.doc.bank_account && !frm.doc.reconciliation_setting) {
			sync_reconciliation_setting(frm, { silent: true });
		}

		// A Debit statement row can only ever be matched to a Debit-direction
		// source (money leaving the account) and vice versa — restrict the
		// Matched Source picker itself so a wrong-direction source (e.g.
		// Compliances, Debit-only) can't even be selected for a Credit row.
		frm.set_query("matched_source", "transactions", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			return {
				filters: {
					is_active: 1,
					direction: ["in", [row.direction, "Both"]],
				},
			};
		});
	},

	validate(frm) {
		// The refresh() auto-fill above is async (a server round-trip) -- if
		// Save is triggered before it resolves, reconciliation_setting is
		// still blank in the outgoing payload even though it visibly fills in
		// moments later, throwing "Value missing" on a doc that looks correct
		// on screen by the time the error shows. Returning this promise makes
		// Frappe's save flow await it, so the field is always resolved (or
		// genuinely absent, if no Setting exists) before the save proceeds.
		if (frm.doc.bank_account && !frm.doc.reconciliation_setting) {
			return sync_reconciliation_setting(frm, { silent: true });
		}
	},

	toggle_submit_button(frm) {
		if (!frm.toolbar || frm.toolbar.current_status !== "Submit") {
			return;
		}
		// refresh() (and therefore this trigger) can fire more than once for a
		// single page load/save — set_intro() on this Frappe version appends a
		// new dismissible banner rather than replacing the existing one, so an
		// unconditional clear right before (re-)setting it keeps it to always
		// exactly one, however many times this runs.
		frm.set_intro();
		const rows = frm.doc.transactions || [];
		const unmatched_count = rows.filter((row) => !row.matched_docname).length;
		if (rows.length === 0 || unmatched_count > 0) {
			frm.page.btn_primary.hide();
			frm.set_intro(
				__("Submit button is hidden — {0} of {1} transaction(s) still need to be matched.", [
					unmatched_count || rows.length,
					rows.length,
				]),
				"orange"
			);
		} else {
			frm.page.btn_primary.show();
		}
	},

	bank_account(frm) {
		refresh_period_summary(frm);
		sync_reconciliation_setting(frm);
	},

	from_date(frm) {
		refresh_period_summary(frm);
	},

	to_date(frm) {
		refresh_period_summary(frm);
	},

	parse_and_match_btn(frm) {
		if (frm.is_new() || frm.is_dirty()) {
			frappe.msgprint(__("Save the document before parsing the statement."));
			return;
		}
		if (!frm.doc.statement_file) {
			frappe.msgprint(__("Attach a statement file first."));
			return;
		}
		frappe.dom.freeze(__("Parsing statement..."));
		frm.call("parse_and_match").then(() => {
			frappe.dom.unfreeze();
			frm.reload_doc();
		}).catch(() => {
			frappe.dom.unfreeze();
		});
	},
});
