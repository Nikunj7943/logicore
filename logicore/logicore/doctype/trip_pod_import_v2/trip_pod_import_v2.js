// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

const LARGE_BATCH_THRESHOLD = 200;
const DEFAULT_BATCH_SIZE = 10;
const READY_STATUS = "Ready";
const JOB_STATUS_PENDING = "Pending";
const JOB_STATUS_QUEUED = "Queued";
const JOB_STATUS_RUNNING = "Running";
const JOB_STATUS_COMPLETED = "Completed";
const JOB_STATUS_FAILED = "Failed";
const STATUS_POLL_DELAY_MS = 1000;
const STATUS_POLL_ERROR_DELAY_MS = 4000;

frappe.ui.form.on("Trip POD Import V2", {
	refresh(frm) {
		frm.events.ensure_local_session_state(frm);
		frm.events.apply_import_defaults(frm);
		frm.events.configure_actions(frm);
		frm.events.configure_grid(frm);
		frm.events.render_from_doc(frm);
	},

	async trip_type(frm) {
		if (frm.is_new()) {
			frm.events.render_from_doc(frm);
			return;
		}

		await frm.events.ensure_saved(frm);

		if (frm.events.has_local_selection(frm)) {
			await frm.events.request_preview_from_local_files(frm);
			return;
		}

		frm.events.render_from_doc(frm);
	},

	upload_pdfs(frm) {
		frm.events.select_browser_folder(frm);
	},

	importload(frm) {
		frm.events.import_all_batches(frm);
	},

	ensure_local_session_state(frm) {
		if (!(frm.trip_pod_local_files instanceof Map)) {
			frm.trip_pod_local_files = new Map();
		}
		if (typeof frm.trip_pod_selection_summary === "undefined") {
			frm.trip_pod_selection_summary = null;
		}
		if (!frm.trip_pod_runtime_summary) {
			frm.trip_pod_runtime_summary = null;
		}
		if (typeof frm.trip_pod_folder_locked === "undefined") {
			frm.trip_pod_folder_locked = false;
		}
		if (typeof frm.trip_pod_import_in_progress === "undefined") {
			frm.trip_pod_import_in_progress = false;
		}
		if (typeof frm.trip_pod_background_job_started === "undefined") {
			frm.trip_pod_background_job_started = false;
		}
		if (!frm.trip_pod_import_progress) {
			frm.trip_pod_import_progress = null;
		}
		if (typeof frm.trip_pod_status_poll_timer === "undefined") {
			frm.trip_pod_status_poll_timer = null;
		}
		if (typeof frm.trip_pod_status_poll_in_flight === "undefined") {
			frm.trip_pod_status_poll_in_flight = false;
		}
		if (!Array.isArray(frm.trip_pod_selection_rows)) {
			frm.trip_pod_selection_rows = [];
		}
	},

	apply_import_defaults(frm) {
		const updates = {};
		if (!frm.doc.import_date) {
			updates.import_date = frappe.datetime.get_today();
		}
		if (!frm.doc.import_by) {
			updates.import_by = frappe.session.user_fullname || frappe.session.user;
		}
		if (!frm.doc.batch || Number(frm.doc.batch) < 1) {
			updates.batch = DEFAULT_BATCH_SIZE;
		}
		if (typeof frm.doc.source_mode !== "undefined" && frm.doc.source_mode !== "Browser Folder") {
			updates.source_mode = "Browser Folder";
		}
		if (frm.doc.source_folder_path) {
			updates.source_folder_path = "";
		}
		if (Object.keys(updates).length) {
			frm.set_value(updates);
		}
	},

	configure_actions(frm) {
		[
			"source_mode",
			"source_folder_path",
			"status_section",
			"scan_status",
			"import_status",
			"result_report_file",
			"summary_section",
			"total_files_count",
			"ready_files_count",
			"imported_files_count",
			"failed_files_count",
			"unmatched_files_count",
			"duplicate_match_files_count",
			"duplicate_target_files_count",
			"invalid_files_count",
		].forEach((fieldname) => frm.toggle_display(fieldname, false));
		frm.set_df_property("upload_pdfs", "label", __("Select Folder"));
		frm.set_df_property("importload", "label", __("Import"));
		frm.events.apply_post_save_lock(frm);
	},

	set_import_controls_enabled(frm, enabled) {
		frm.events.sync_folder_lock_state(frm);
		frm.events.set_button_enabled(
			frm,
			"upload_pdfs",
			Boolean(enabled && !frm.trip_pod_import_in_progress && !frm.events.is_folder_locked(frm))
		);
		frm.events.set_button_enabled(frm, "importload", Boolean(enabled && frm.events.can_import(frm)));
	},

	set_button_enabled(frm, fieldname, enabled) {
		frm.toggle_enable(fieldname, enabled);
		const field = frm.get_field(fieldname);
		if (!field?.$wrapper) {
			return;
		}

		field.$wrapper
			.find("button, .btn")
			.prop("disabled", !enabled)
			.attr("aria-disabled", enabled ? "false" : "true")
			.toggleClass("disabled", !enabled)
			.css("pointer-events", enabled ? "" : "none");
	},

	apply_post_save_lock(frm) {
		// No field locks — user can change trip_type or batch and re-select folder at any time
	},

	configure_grid(frm) {
		const grid = frm.get_field("pod_files").grid;
		grid.cannot_add_rows = true;
		grid.wrapper.find(".grid-add-row, .grid-add-multiple-rows").hide();
	},

	render_from_doc(frm) {
		frm.events.sync_folder_lock_state(frm);
		const summary = frm.events.get_display_summary(frm);
		const hasFiles = Number(summary.total_files || 0) > 0;
		const showRows = hasFiles && !frm.events.is_large_batch(summary);
		const showPreview = hasFiles || frm.events.has_local_selection(frm) || Boolean(frm.trip_pod_selection_summary);

		frm.toggle_display("pod_files_section", hasFiles);
		frm.toggle_display("pod_files", showRows);
		frm.events.toggle_preview(frm, showPreview);
		frm.events.render_summary(frm, summary, { hasFiles });
		frm.events.set_import_controls_enabled(frm, !frm.trip_pod_import_in_progress);

		if (showRows) {
			frm.refresh_field("pod_files");
			frm.events.configure_grid(frm);
		}

		frm.events.sync_job_polling(frm);
	},

	toggle_preview(frm, showPreview) {
		frm.toggle_display("preview_section", showPreview);
		frm.toggle_display("preview_summary_html", showPreview);
	},

	render_summary(frm, summary, { hasFiles = false } = {}) {
		const wrapper = frm.get_field("preview_summary_html").$wrapper;
		const selectionSummary = frm.trip_pod_selection_summary;
		const lines = [];

		if (!hasFiles && !selectionSummary) {
			wrapper.html(
				`<div class="text-muted small">${frappe.utils.escape_html(frm.events.get_preview_help_text(frm))}</div>`
			);
			return;
		}

		if (hasFiles) {
			const cards = [
				[__("Mapped Files"), Number(summary.total_files || 0)],
				[__("Ready"), Number(summary.importable_files || 0)],
				[__("Imported"), Number(summary.imported_files || 0)],
				[__("Failed"), Number(summary.failed_files || 0)],
			];

			wrapper.html(`
				<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;">
					${cards
						.map(
							([label, value]) => `
								<div style="padding:12px 14px;border:1px solid #dbe4ff;border-radius:12px;background:#f8faff;">
									<div class="text-muted small">${frappe.utils.escape_html(label)}</div>
									<div style="font-weight:700;">${frappe.utils.escape_html(String(value))}</div>
								</div>`
						)
						.join("")}
				</div>
				<div class="trip-pod-preview-lines" style="margin-top:12px;display:flex;flex-direction:column;gap:6px;"></div>
			`);
		} else {
			wrapper.html('<div class="trip-pod-preview-lines" style="display:flex;flex-direction:column;gap:6px;"></div>');
		}

		if (selectionSummary) {
			lines.push(
				`${__("Selected PDFs")}: ${frappe.utils.escape_html(String(selectionSummary.total_files || 0))}`
			);
			if (Number(selectionSummary.unmatched_files || 0)) {
				lines.push(`${__("Ignored No Match")}: ${frappe.utils.escape_html(String(selectionSummary.unmatched_files))}`);
			}
			if (Number(selectionSummary.duplicate_match_files || 0)) {
				lines.push(
					`${__("Ignored Multiple Matches")}: ${frappe.utils.escape_html(String(selectionSummary.duplicate_match_files))}`
				);
			}
			if (Number(selectionSummary.duplicate_target_files || 0)) {
				lines.push(
					`${__("Ignored Duplicate Targets")}: ${frappe.utils.escape_html(String(selectionSummary.duplicate_target_files))}`
				);
			}
			if (Number(selectionSummary.invalid_files || 0)) {
				lines.push(`${__("Ignored Invalid Files")}: ${frappe.utils.escape_html(String(selectionSummary.invalid_files))}`);
			}
			const selFailed = Number(selectionSummary.failed_files || 0);
			if (selFailed) {
				lines.push(`${__("Validation Failed")}: ${frappe.utils.escape_html(String(selFailed))}`);
				const failedRows = (frm.trip_pod_selection_rows || []).slice(0, 5);
				failedRows.forEach((r) => {
					lines.push(`↳ ${frappe.utils.escape_html(r.file_name || "")} — ${frappe.utils.escape_html(r.status_message || "")}`);
				});
				if ((frm.trip_pod_selection_rows || []).length > 5) {
					lines.push(`…${frappe.utils.escape_html(__("and {0} more").replace("{0}", (frm.trip_pod_selection_rows || []).length - 5))}`);
				}
			}
		}

		lines.push(`${__("Batch Size")}: ${frappe.utils.escape_html(String(frm.events.get_batch_size(frm)))}`);

		const stagedFileCount = frm.events.get_staged_file_count(frm);
		if (stagedFileCount) {
			lines.push(`${__("Temporary Staged Files")}: ${frappe.utils.escape_html(String(stagedFileCount))}`);
		}

		if (frm.doc.import_status && frm.doc.import_status !== JOB_STATUS_PENDING) {
			lines.push(
				`${__("Import Status")}: ${frappe.utils.escape_html(String(frm.doc.import_status || JOB_STATUS_PENDING))}`
			);
		}

		if (frm.trip_pod_import_in_progress && frm.trip_pod_import_progress) {
			lines.push(frappe.utils.escape_html(__("Preparing import. Please wait until staging finishes.")));
			lines.push(
				`${__("Staging Batches")}: ${frappe.utils.escape_html(String(frm.trip_pod_import_progress.chunks || 0))}`
			);
			lines.push(
				`${__("Temporarily Staged So Far")}: ${frappe.utils.escape_html(String(frm.trip_pod_import_progress.staged || 0))}`
			);
			lines.push(
				`${__("Failed So Far")}: ${frappe.utils.escape_html(String(frm.trip_pod_import_progress.failed || 0))}`
			);
		}

		if (frm.events.has_running_job(frm)) {
			lines.push(
				frappe.utils.escape_html(
					__("Import is running. Temporary staged files will be removed after processing, and only final successful Trip PDFs will remain.")
				)
			);
		}

		if (
			hasFiles &&
			!frm.events.has_local_selection(frm) &&
			Number(summary.importable_files || 0) > 0 &&
			!frm.events.has_running_job(frm)
		) {
			lines.push(
				frappe.utils.escape_html(
					__("Local folder files are no longer available in this tab. Click Select Folder to re-select and import.")
				)
			);
		}

		if (hasFiles && frm.events.has_local_selection(frm) && !frm.trip_pod_import_in_progress) {
			lines.push(
				frappe.utils.escape_html(
					__("One Import click stages all ready mapped PDFs temporarily in Batch-sized chunks and then completes the Trip import in the same run.")
				)
			);
		}

		if (frm.is_new()) {
			lines.push(
				frappe.utils.escape_html(
					__("Click Select Folder on the new document to prepare preview rows for this import.")
				)
			);
		} else {
			lines.push(
				frappe.utils.escape_html(
					__("Import is the only action available after preview is prepared.")
				)
			);
		}

		wrapper.find(".trip-pod-preview-lines").html(
			lines.map((line) => `<div class="small">${line}</div>`).join("")
		);
	},

	create_folder_input() {
		return $('<input type="file" style="display:none;" multiple accept=".pdf">')
			.attr("webkitdirectory", true)
			.attr("directory", true)
			.appendTo("body");
	},

	async select_browser_folder(frm) {
		if (!frm.doc.trip_type) {
			frappe.msgprint(__("Please select Trip Type before choosing a folder."));
			return;
		}

		await frm.events.ensure_saved(frm);
		const input = frm.events.create_folder_input();
		input.on("change", async () => {
			const selectedFiles = Array.from(input[0].files || []);
			input.remove();
			await frm.events.preview_selected_folder(frm, selectedFiles);
		});
		input.trigger("click");
	},

	async preview_selected_folder(frm, files) {
		const previewFiles = frm.events.prepare_preview_files(files || []);
		if (!previewFiles.length) {
			frappe.msgprint(__("The selected folder does not contain any PDF files."));
			return;
		}

		frm.trip_pod_folder_locked = true;
		frm.trip_pod_local_files = new Map(previewFiles.map((item) => [item.client_row_key, item.file]));
		frm.trip_pod_selection_summary = null;
		frm.events.render_from_doc(frm);

		await frm.events.request_preview(frm, previewFiles);
	},

	async request_preview_from_local_files(frm) {
		const previewFiles = Array.from(frm.trip_pod_local_files.entries())
			.map(([client_row_key, file]) => ({
				client_row_key,
				file_name: file.name,
			}))
			.sort((left, right) =>
				left.file_name.localeCompare(right.file_name, undefined, { sensitivity: "base" }) ||
				left.client_row_key.localeCompare(right.client_row_key)
			);

		if (!previewFiles.length) {
			frm.events.render_from_doc(frm);
			return;
		}

		await frm.events.request_preview(frm, previewFiles);
	},

	async request_preview(frm, previewFiles) {
		return frappe.call({
			method: "logicore.logicore.doctype.trip_pod_import_v2.trip_pod_import_v2.preview_local_folder_trip_pods",
			args: {
				docname: frm.doc.name,
				trip_type: frm.doc.trip_type,
				files: JSON.stringify(
					previewFiles.map((item) => ({
						client_row_key: item.client_row_key,
						file_name: item.file_name,
					}))
				),
			},
			freeze: true,
			freeze_message: __("Preparing folder preview..."),
			callback: (r) => {
				frm.events.apply_status_payload(frm, r.message || {});
			},
		});
	},

	prepare_preview_files(files) {
		const pdfFiles = (files || []).filter((file) => /\.pdf$/i.test(file.name || ""));
		return pdfFiles
			.slice()
			.sort((left, right) => {
				const leftPath = String(left.webkitRelativePath || "");
				const rightPath = String(right.webkitRelativePath || "");
				return (
					String(left.name || "").localeCompare(String(right.name || ""), undefined, {
						sensitivity: "base",
					}) || leftPath.localeCompare(rightPath, undefined, { sensitivity: "base" })
				);
			})
			.map((file, index) => ({
				client_row_key: `row_${index + 1}`,
				file_name: file.name,
				file,
			}));
	},

	async import_all_batches(frm) {
		if (!frm.doc.name) {
			frappe.msgprint(__("Please save the import document before importing."));
			return;
		}
		if (!frm.doc.trip_type) {
			frappe.msgprint(__("Please select Trip Type before importing POD files."));
			return;
		}
		if (!frm.events.has_local_selection(frm)) {
			frappe.msgprint(__("Select Folder again in this tab before importing."));
			return;
		}
		if (frm.trip_pod_import_in_progress) {
			return;
		}

		await frm.events.ensure_saved(frm);
		const initialRows = frm.events.get_batch_candidate_rows(frm);
		if (!initialRows.length) {
			frappe.msgprint(__("No mapped files are ready to import for the current folder selection."));
			return;
		}

		frm.trip_pod_import_in_progress = true;
		frm.trip_pod_import_progress = {
			chunks: 0,
			staged: 0,
			failed: 0,
			total: initialRows.length,
		};
		frm.events.render_from_doc(frm);

		let lastPayload = null;
		try {
			while (true) {
				const batchRows = frm.events
					.get_batch_candidate_rows(frm)
					.slice(0, frm.events.get_batch_size(frm));
				if (!batchRows.length) {
					break;
				}

				const payload = await frm.events.stage_selected_batch(frm, batchRows);
				lastPayload = payload;
				frm.events.apply_status_payload(frm, payload);
				frm.events.remove_processed_files_from_session(frm, batchRows);
				frm.trip_pod_import_progress.chunks += 1;
				frm.trip_pod_import_progress.staged += Number(payload.staged_count || 0);
				frm.trip_pod_import_progress.failed += Number(payload.failed_count || 0);

				if (Number(payload.failed_count || 0)) {
					throw new Error(
						frm.events.build_failure_message(
							payload.failures || [],
							__("Failed to stage one or more PDFs. The Trip import was not started.")
						)
					);
				}

				const processed =
					Number(frm.trip_pod_import_progress.staged || 0) +
					Number(frm.trip_pod_import_progress.failed || 0);
				const total = Math.max(Number(frm.trip_pod_import_progress.total || 0), 1);
				frappe.show_progress(
					__("Staging POD PDFs"),
					processed,
					total,
					__("Chunk {0}: staged {1}, failed {2}, remaining {3}", [
						frm.trip_pod_import_progress.chunks,
						frm.trip_pod_import_progress.staged,
						frm.trip_pod_import_progress.failed,
						Number(payload.summary?.importable_files || 0),
					]),
					true
				);
			}

			frappe.hide_progress();
			const importPayload = await frm.events.import_staged_trip_pods(frm);
			frm.events.apply_status_payload(frm, importPayload);
			frm.trip_pod_import_progress.imported = Number(importPayload.imported_count || 0);
			frm.trip_pod_import_progress.failed = Number(importPayload.failed_count || 0);
			frm.events.show_import_run_result(frm, importPayload);
		} catch (error) {
			frappe.hide_progress();
			frappe.msgprint(error?.message || __("Import failed. Please try again."));
		} finally {
			frm.trip_pod_import_in_progress = false;
			frm.trip_pod_import_progress = null;
			frm.trip_pod_local_files = new Map();
			frm.events.render_from_doc(frm);
		}
	},

	stage_selected_batch(frm, batchRows) {
		return new Promise((resolve, reject) => {
			const xhr = new XMLHttpRequest();
			xhr.open(
				"POST",
				"/api/method/logicore.logicore.doctype.trip_pod_import_v2.trip_pod_import_v2.stage_local_folder_trip_pods",
				true
			);
			xhr.setRequestHeader("Accept", "application/json");
			xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);

			xhr.onreadystatechange = () => {
				if (xhr.readyState !== XMLHttpRequest.DONE) {
					return;
				}

				if (xhr.status !== 200) {
					reject(
						new Error(
							frm.events.extract_xhr_error_message(
								xhr,
								__("Failed to upload one staging batch. Try a smaller Batch size.")
							)
						)
					);
					return;
				}

				try {
					const response = JSON.parse(xhr.responseText);
					resolve(response.message || {});
				} catch (error) {
					reject(error);
				}
			};

			xhr.onerror = () =>
				reject(new Error(__("Staging request failed. Try a smaller Batch size.")));

			const formData = new FormData();
			formData.append("docname", frm.doc.name);
			formData.append("trip_type", frm.doc.trip_type);
			formData.append(
				"batch_rows",
				JSON.stringify(
					batchRows.map((row) => ({
						client_row_key: row.client_row_key,
						file_name: row.file_name,
						matched_trip: row.matched_trip,
						reference_no: row.reference_no,
					}))
				)
			);

			batchRows.forEach((row) => {
				const file = frm.trip_pod_local_files.get(row.client_row_key);
				if (file) {
					formData.append(`file__${row.client_row_key}`, file, row.file_name);
				}
			});

			frappe.dom.freeze(__("Uploading and compressing selected POD batch..."));
			xhr.onloadend = () => frappe.dom.unfreeze();
			xhr.send(formData);
		});
	},

	queue_background_import(frm) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "logicore.logicore.doctype.trip_pod_import_v2.trip_pod_import_v2.queue_import_trip_pods",
				args: {
					docname: frm.doc.name,
					trip_type: frm.doc.trip_type,
				},
				freeze: true,
				freeze_message: __("Queueing background import..."),
				callback: (r) => resolve(r.message || {}),
				error: (r) =>
					reject(
						new Error(
							r?.message ||
								r?.exc ||
								__("Could not queue the background import. Please try again.")
						)
					),
			});
		});
	},

	import_staged_trip_pods(frm) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "logicore.logicore.doctype.trip_pod_import_v2.trip_pod_import_v2.import_staged_trip_pods",
				args: {
					docname: frm.doc.name,
					trip_type: frm.doc.trip_type,
				},
				freeze: true,
				freeze_message: __("Importing staged POD PDFs..."),
				callback: (r) => resolve(r.message || {}),
				error: (r) =>
					reject(
						new Error(
							r?.message ||
								r?.exc ||
								__("Could not complete the Trip import. Please try again.")
						)
					),
			});
		});
	},

	remove_processed_files_from_session(frm, batchRows) {
		batchRows.forEach((row) => {
			frm.trip_pod_local_files.delete(row.client_row_key);
		});
	},

	apply_status_payload(frm, payload) {
		if (payload.summary) {
			frm.trip_pod_runtime_summary = payload.summary;
		}
		if (payload.scan_status) {
			frm.doc.scan_status = payload.scan_status;
		}
		if (payload.import_status) {
			frm.doc.import_status = payload.import_status;
		}
		if (typeof payload.result_report_file !== "undefined") {
			frm.doc.result_report_file = payload.result_report_file || "";
		}
		frm.events.apply_server_doc(frm, payload);
		if (payload.selection_summary) {
			frm.trip_pod_selection_summary = payload.selection_summary;
			frm.trip_pod_selection_rows = payload.selection_failed_rows || [];
		}
		if (payload.doc) {
			frm.trip_pod_runtime_summary = null;
		}
		frm.refresh_fields(["trip_type", "batch"]);
		frm.events.render_from_doc(frm);
	},

	apply_server_doc(frm, payload) {
		if (payload?.doc) {
			frappe.model.sync(payload.doc);
			const syncedDoc = locals[frm.doctype] && locals[frm.doctype][frm.docname];
			if (syncedDoc) {
				frm.doc = syncedDoc;
			}
		}

		frm.events.sync_server_modified(frm, payload);
	},

	show_import_result(payload) {
		frappe.hide_progress();
		const importedCount = Number(payload.imported_count || 0);
		const failedCount = Number(payload.failed_count || 0);
		const remainingReady = Number(payload.summary?.importable_files || 0);

		frappe.msgprint({
			title: __("Trip POD Import Result"),
			indicator: failedCount ? "orange" : "green",
			message: `
				<div><strong>${__("Imported in This Batch")}</strong>: ${importedCount}</div>
				<div><strong>${__("Failed in This Batch")}</strong>: ${failedCount}</div>
				<div><strong>${__("Remaining Ready")}</strong>: ${remainingReady}</div>
			`,
		});
	},

	show_import_run_result(frm, payload) {
		frappe.hide_progress();
		const importedCount = Number(payload?.imported_count || frm.trip_pod_import_progress?.imported || 0);
		const failedCount = Number(payload?.failed_count || frm.trip_pod_import_progress?.failed || 0);
		const remainingReady = Number(payload?.summary?.importable_files || 0);

		frappe.msgprint({
			title: __("Trip POD Import Result"),
			indicator: failedCount ? "orange" : "green",
			message: `
				<div><strong>${__("Imported")}</strong>: ${importedCount}</div>
				<div><strong>${__("Failed")}</strong>: ${failedCount}</div>
				<div><strong>${__("Remaining Ready")}</strong>: ${remainingReady}</div>
			`,
		});
	},

	show_background_job_result(frm, payload) {
		frappe.hide_progress();
		const summary = payload?.summary || frm.events.get_display_summary(frm);
		const importedCount = Number(summary.imported_files || 0);
		const failedCount = Number(summary.failed_files || 0);
		const remainingReady = Number(summary.importable_files || 0);

		frappe.msgprint({
			title: __("Trip POD Import Result"),
			indicator: failedCount ? "orange" : "green",
			message: `
				<div><strong>${__("Imported")}</strong>: ${importedCount}</div>
				<div><strong>${__("Failed")}</strong>: ${failedCount}</div>
				<div><strong>${__("Remaining Ready")}</strong>: ${remainingReady}</div>
			`,
		});
	},

	get_batch_candidate_rows(frm) {
		return (frm.doc.pod_files || []).filter(
			(row) =>
				Number(row.can_import || 0) &&
				String(row.preview_status || "").trim() === READY_STATUS &&
				frm.trip_pod_local_files.has(String(row.client_row_key || "").trim())
		);
	},

	get_batch_size(frm) {
		return Math.max(Number(frm.doc.batch || DEFAULT_BATCH_SIZE), 1);
	},

	get_staged_file_count(frm) {
		return (frm.doc.pod_files || []).filter((row) => String(row.pod_file || "").trim()).length;
	},

	get_display_summary(frm) {
		if (frm.trip_pod_runtime_summary) {
			return frm.trip_pod_runtime_summary;
		}

		return frm.events.summary_from_doc(frm.doc);
	},

	has_local_selection(frm) {
		return frm.trip_pod_local_files instanceof Map && frm.trip_pod_local_files.size > 0;
	},

	has_running_job(frm, payload = null) {
		const scanStatus = String(payload?.scan_status || frm.doc.scan_status || JOB_STATUS_PENDING).trim();
		const importStatus = String(payload?.import_status || frm.doc.import_status || JOB_STATUS_PENDING).trim();
		return [JOB_STATUS_QUEUED, JOB_STATUS_RUNNING].includes(scanStatus) ||
			[JOB_STATUS_QUEUED, JOB_STATUS_RUNNING].includes(importStatus);
	},

	is_folder_locked(frm) {
		return Boolean(frm.trip_pod_folder_locked);
	},

	sync_folder_lock_state(frm) {
		// Only lock while an import is actively running
		frm.trip_pod_folder_locked = Boolean(frm.trip_pod_import_in_progress);
	},

	summary_from_doc(doc) {
		const rows = doc.pod_files || [];
		return {
			total_files: rows.length,
			importable_files: rows.filter((row) => Number(row.can_import || 0)).length,
			imported_files: rows.filter((row) => String(row.preview_status || "").trim() === "Imported").length,
			failed_files: rows.filter((row) => String(row.preview_status || "").trim() === "Failed").length,
		};
	},

	can_import(frm) {
		return Boolean(
			frm.doc.trip_type &&
			frm.doc.name &&
			!frm.trip_pod_import_in_progress &&
			!frm.events.has_running_job(frm) &&
			frm.events.get_batch_candidate_rows(frm).length
		);
	},

	is_large_batch(summary) {
		return Number(summary.total_files || 0) > LARGE_BATCH_THRESHOLD;
	},

	get_preview_help_text(frm) {
		if (!frm.doc.trip_type) {
			return __(
				"Select Trip Type first. Then click Select Folder to preview only the PDFs that map to a Trip."
			);
		}

		if (String(frm.doc.trip_type || "").trim().toLowerCase() === "other") {
			return __("Click Select Folder to preview only the files that map by LR No.");
		}

		return __("Click Select Folder to preview only the files that map by TCN/Trip No.");
	},

	sync_server_modified(frm, payload) {
		if (payload?.doc_modified) {
			frm.doc.modified = payload.doc_modified;
		}
		if (payload?.doc_modified_by) {
			frm.doc.modified_by = payload.doc_modified_by;
		}
	},

	sync_job_polling(frm) {
		if (frm.events.has_running_job(frm)) {
			frm.events.start_status_polling(frm);
			return;
		}

		frm.events.stop_status_polling(frm);
	},

	start_status_polling(frm) {
		if (
			!frm.doc.name ||
			frm.trip_pod_status_poll_in_flight ||
			frm.trip_pod_status_poll_timer ||
			!frm.events.has_running_job(frm)
		) {
			return;
		}

		frm.trip_pod_status_poll_in_flight = true;
		frappe.call({
			method: "logicore.logicore.doctype.trip_pod_import_v2.trip_pod_import_v2.get_import_job_status",
			args: { docname: frm.doc.name },
			freeze: false,
			callback: (r) => {
				const payload = r.message || {};
				frm.events.apply_status_payload(frm, payload);
				if (frm.events.has_running_job(frm, payload)) {
					frm.events.schedule_status_poll(frm, STATUS_POLL_DELAY_MS);
					return;
				}

				frappe.hide_progress();
				if (frm.trip_pod_background_job_started) {
					frm.events.show_background_job_result(frm, payload);
					frm.trip_pod_background_job_started = false;
				}
			},
			error: () => {
				if (frm.events.has_running_job(frm)) {
					frm.events.schedule_status_poll(frm, STATUS_POLL_ERROR_DELAY_MS);
					return;
				}

				frappe.hide_progress();
			},
			always: () => {
				frm.trip_pod_status_poll_in_flight = false;
			},
		});
	},

	schedule_status_poll(frm, delay) {
		frm.events.stop_status_polling(frm);
		frm.trip_pod_status_poll_timer = window.setTimeout(() => {
			frm.trip_pod_status_poll_timer = null;
			frm.events.start_status_polling(frm);
		}, delay);
	},

	stop_status_polling(frm) {
		if (frm.trip_pod_status_poll_timer) {
			window.clearTimeout(frm.trip_pod_status_poll_timer);
			frm.trip_pod_status_poll_timer = null;
		}
	},

	extract_xhr_error_message(xhr, fallbackMessage) {
		try {
			const response = JSON.parse(xhr.responseText || "{}");
			if (response?._server_messages) {
				const serverMessages = JSON.parse(response._server_messages);
				if (serverMessages?.length) {
					const firstMessage = JSON.parse(serverMessages[0]);
					if (firstMessage?.message) {
						return firstMessage.message;
					}
				}
			}
			if (response?.message) {
				return typeof response.message === "string"
					? response.message
					: response.message.message || fallbackMessage;
			}
			if (response?.exception) {
				return response.exception;
			}
		} catch (error) {
			// Ignore parsing failures and fall back to HTTP details.
		}

		return xhr.statusText || fallbackMessage;
	},

	build_failure_message(failures, fallbackMessage) {
		if (!Array.isArray(failures) || !failures.length) {
			return fallbackMessage;
		}

		const firstFailure = failures[0] || {};
		const failureText = [firstFailure.file_name, firstFailure.message].filter(Boolean).join(": ");
		return failureText || fallbackMessage;
	},

	async ensure_saved(frm) {
		if (frm.is_new() || frm.is_dirty()) {
			await frm.save();
		}
	},
});
