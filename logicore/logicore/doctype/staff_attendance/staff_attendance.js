// // // Copyright (c) 2026, LogiCore and contributors
// // // For license information, please see license.txt

// // const STATUS_CONFIG = [
// // 	{ key: "Present",              label: "PRESENT",              bg: "#d4edda", count_color: "#1e7e34", icon: "✔" },
// // 	{ key: "Absent",               label: "ABSENT",               bg: "#f8d7da", count_color: "#c0392b", icon: "✘" },
// // 	{ key: "On Leave With Pay",    label: "ON LEAVE WITH PAY",    bg: "#d0eaff", count_color: "#2471a3", icon: "📅" },
// // 	{ key: "On Leave Without Pay", label: "ON LEAVE WITHOUT PAY", bg: "#fdebd0", count_color: "#d35400", icon: "📋" },
// // 	{ key: "Sunday/Holiday",       label: "SUNDAY / HOLIDAY",     bg: "#e8e8e8", count_color: "#5d6d7e", icon: "🏖" },
// // ];

// // const ROW_COLORS = {
// // 	"Absent":               { bg: "#ffe0e0", text: "#c0392b" },
// // 	"On Leave With Pay":    { bg: "#d0eaff", text: "#2471a3" },
// // 	"On Leave Without Pay": { bg: "#fdebd0", text: "#d35400" },
// // 	"Sunday/Holiday":       { bg: "#ececec", text: "#7f8c8d" },
// // 	"Present":              { bg: "",        text: ""         },
// // };

// // // ── parent form events ─────────────────────────────────────────────────────────
// // frappe.ui.form.on("Staff Attendance", {
// // 	refresh(frm) {
// // 		if (frm.is_new() && !frm.doc.attendance_no) {
// // 			frm.set_value("date", frappe.datetime.get_today());
// // 		}
// // 		setTimeout(() => {
// // 			render_summary(frm);
// // 			highlight_all_rows(frm);
// // 		}, 300);
// // 	},

// // 	employee_type(frm) {
// // 		if (!frm.doc.employee_type) {
// // 			frm.clear_table("attendance_details");
// // 			frm.refresh_field("attendance_details");
// // 			render_summary(frm);
// // 			return;
// // 		}
// // 		fetch_and_populate(frm);
// // 	},

// // 	date(frm) {
// // 		// re-fetch when date changes so previous-day statuses are recalculated
// // 		if (frm.doc.employee_type) fetch_and_populate(frm);
// // 	},
// // });

// // // ── child table events ─────────────────────────────────────────────────────────
// // frappe.ui.form.on("Staff Attendance Detail", {
// // 	status(frm, cdt, cdn) {
// // 		highlight_row(frm, cdn);
// // 		render_summary(frm);
// // 	},
// // 	form_render(frm, cdt, cdn) {
// // 		highlight_row(frm, cdn);
// // 	},
// // 	attendance_details_remove(frm) {
// // 		render_summary(frm);
// // 	},
// // });

// // // ── summary card strip ─────────────────────────────────────────────────────────
// // function render_summary(frm) {
// // 	let rows  = frm.doc.attendance_details || [];
// // 	let total = rows.length;

// // 	let counts = {};
// // 	STATUS_CONFIG.forEach(s => counts[s.key] = 0);
// // 	rows.forEach(r => { if (counts.hasOwnProperty(r.status)) counts[r.status]++; });

// // 	let cards_html = STATUS_CONFIG.map(s => `
// // 		<div style="
// // 			background:${s.bg};border-radius:10px;padding:14px 18px 12px;
// // 			min-width:110px;flex:1;text-align:center;
// // 			box-shadow:0 1px 4px rgba(0,0,0,.08);position:relative;overflow:hidden;">
// // 			<div style="font-size:2rem;font-weight:700;color:${s.count_color};line-height:1;margin-bottom:6px;">${counts[s.key]}</div>
// // 			<div style="font-size:0.62rem;font-weight:600;color:${s.count_color};letter-spacing:.04em;opacity:.85;">${s.label}</div>
// // 			<div style="position:absolute;right:10px;top:8px;font-size:1.5rem;opacity:.13;">${s.icon}</div>
// // 		</div>`).join("");

// // 	let total_html = `
// // 		<div style="
// // 			background:#f4f5f7;border-radius:10px;padding:14px 18px 12px;
// // 			min-width:80px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.08);">
// // 			<div style="font-size:2rem;font-weight:700;color:#2c3e50;line-height:1;margin-bottom:6px;">${total}</div>
// // 			<div style="font-size:0.62rem;font-weight:600;color:#5d6d7e;letter-spacing:.04em;">TOTAL</div>
// // 		</div>`;

// // 	frm.fields_dict.attendance_summary.$wrapper
// // 		.find("#att-summary-wrap")
// // 		.html(`<div style="display:flex;flex-wrap:wrap;gap:10px;padding:14px 0 10px;align-items:stretch;">
// // 			${total_html}${cards_html}
// // 		</div>`);
// // }

// // // ── row highlighting ───────────────────────────────────────────────────────────
// // function highlight_row(frm, cdn) {
// // 	let row_doc = locals["Staff Attendance Detail"]?.[cdn];
// // 	if (!row_doc) return;
// // 	let c = ROW_COLORS[row_doc.status] || ROW_COLORS["Present"];
// // 	frm.fields_dict.attendance_details.grid.wrapper
// // 		.find(`.grid-row[data-name="${cdn}"]`)
// // 		.find("td, .row-index, .grid-static-col")
// // 		.css({ "background-color": c.bg, "color": c.text || "" });
// // }

// // function highlight_all_rows(frm) {
// // 	(frm.doc.attendance_details || []).forEach(r => highlight_row(frm, r.name));
// // }

// // // ── fetch & populate ───────────────────────────────────────────────────────────
// // function fetch_and_populate(frm) {
// // 	frappe.call({
// // 		method: "logicore.logicore.doctype.staff_attendance.staff_attendance.get_attendance_employees",
// // 		args: {
// // 			employee_type: frm.doc.employee_type,
// // 			company:       frm.doc.company || "",
// // 			date:          frm.doc.date    || "",
// // 		},
// // 		freeze: true,
// // 		freeze_message: __("Loading attendance..."),
// // 		callback(r) {
// // 			frm.clear_table("attendance_details");

// // 			if (r.message && r.message.length) {
// // 				r.message.forEach(row => {
// // 					let child = frm.add_child("attendance_details");
// // 					child.link_doctype  = row.link_doctype;
// // 					child.employee_link = row.employee_link;
// // 					child.employee_name = row.employee_name;
// // 					child.designation   = row.designation;
// // 					child.status        = row.status;
// // 				});
// // 			}

// // 			frm.refresh_field("attendance_details");
// // 			setTimeout(() => {
// // 				highlight_all_rows(frm);
// // 				render_summary(frm);
// // 			}, 200);
// // 		},
// // 	});
// // }

// // Copyright (c) 2026, LogiCore and contributors
// // For license information, please see license.txt

// const STATUS_CONFIG = [
//     { key: "Present",              label: "PRESENT",              bg: "#d4edda", count_color: "#1e7e34", icon: "✔" },
//     { key: "Absent",               label: "ABSENT",               bg: "#f8d7da", count_color: "#c0392b", icon: "✘" },
//     { key: "On Leave With Pay",    label: "ON LEAVE WITH PAY",    bg: "#d0eaff", count_color: "#2471a3", icon: "📅" },
//     { key: "On Leave Without Pay", label: "ON LEAVE WITHOUT PAY", bg: "#fdebd0", count_color: "#d35400", icon: "📋" },
//     { key: "Sunday/Holiday",       label: "SUNDAY / HOLIDAY",     bg: "#e8e8e8", count_color: "#5d6d7e", icon: "🏖" },
// ];

// const ROW_COLORS = {
//     "Absent":               { bg: "#ffe0e0", text: "#c0392b" },
//     "On Leave With Pay":    { bg: "#d0eaff", text: "#2471a3" },
//     "On Leave Without Pay": { bg: "#fdebd0", text: "#d35400" },
//     "Sunday/Holiday":       { bg: "#ececec", text: "#7f8c8d" },
//     "Present":              { bg: "",        text: ""         },
// };

// // ── parent form events ─────────────────────────────────────────────────────────
// frappe.ui.form.on("Staff Attendance", {
//     refresh(frm) {
//         if (frm.is_new() && !frm.doc.attendance_no) {
//             frm.set_value("date", frappe.datetime.get_today());
//         }
//         if (!frm.is_new()) {
//             frm.set_df_property("date", "read_only", 1);
//             frm.set_df_property("employee_type", "read_only", 1);
//             frm.set_df_property("company", "read_only", 1);
//         }
//         // Proper Frappe API for child-table link query — fires per row, no company block
//         frm.set_query("employee_link", "attendance_details", function(doc, cdt, cdn) {
//             let row = locals[cdt][cdn];
//             if (row.link_doctype === "Employee") {
//                 return { filters: { status: "Active" } };
//             } else if (row.link_doctype === "Driver") {
//                 return { filters: { status: "Active" } };
//             }
//             return {};
//         });
//         setTimeout(() => {
//             render_summary(frm);
//             highlight_all_rows(frm);
//             render_search_bar(frm);
//         }, 300);
//     },

//     employee_type(frm) {
//         if (!frm.doc.employee_type) {
//             frm.clear_table("attendance_details");
//             frm.refresh_field("attendance_details");
//             render_summary(frm);
//             return;
//         }
//         fetch_and_populate(frm);
//     },

//     date(frm) {
//         if (frm.doc.employee_type) fetch_and_populate(frm);
//     },
// });

// // ── child table events ─────────────────────────────────────────────────────────
// frappe.ui.form.on("Staff Attendance Detail", {
//     status(frm, cdt, cdn) {
//         highlight_row(frm, cdn);
//         render_summary(frm);
//     },
//     form_render(frm, cdt, cdn) {
//         highlight_row(frm, cdn);
//     },
//     attendance_details_remove(frm) {
//         render_summary(frm);
//     },
// });

// // ── summary card strip ─────────────────────────────────────────────────────────
// function render_summary(frm) {
//     let rows  = frm.doc.attendance_details || [];
//     let total = rows.length;

//     let counts = {};
//     STATUS_CONFIG.forEach(s => counts[s.key] = 0);
//     rows.forEach(r => { if (counts.hasOwnProperty(r.status)) counts[r.status]++; });

//     let cards_html = STATUS_CONFIG.map(s => `
//         <div style="
//             background:${s.bg};border-radius:10px;padding:14px 18px 12px;
//             min-width:110px;flex:1;text-align:center;
//             box-shadow:0 1px 4px rgba(0,0,0,.08);position:relative;overflow:hidden;">
//             <div style="font-size:2rem;font-weight:700;color:${s.count_color};line-height:1;margin-bottom:6px;">${counts[s.key]}</div>
//             <div style="font-size:0.62rem;font-weight:600;color:${s.count_color};letter-spacing:.04em;opacity:.85;">${s.label}</div>
//             <div style="position:absolute;right:10px;top:8px;font-size:1.5rem;opacity:.13;">${s.icon}</div>
//         </div>`).join("");

//     let total_html = `
//         <div style="
//             background:#f4f5f7;border-radius:10px;padding:14px 18px 12px;
//             min-width:80px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.08);">
//             <div style="font-size:2rem;font-weight:700;color:#2c3e50;line-height:1;margin-bottom:6px;">${total}</div>
//             <div style="font-size:0.62rem;font-weight:600;color:#5d6d7e;letter-spacing:.04em;">TOTAL</div>
//         </div>`;

//     frm.fields_dict.attendance_summary.$wrapper
//         .find("#att-summary-wrap")
//         .html(`<div style="display:flex;flex-wrap:wrap;gap:10px;padding:14px 0 10px;align-items:stretch;">
//             ${total_html}${cards_html}
//         </div>`);
// }

// // ── row highlighting ───────────────────────────────────────────────────────────
// function highlight_row(frm, cdn) {
//     let row_doc = locals["Staff Attendance Detail"]?.[cdn];
//     if (!row_doc) return;
//     let c = ROW_COLORS[row_doc.status] || ROW_COLORS["Present"];
//     frm.fields_dict.attendance_details.grid.wrapper
//         .find(`.grid-row[data-name="${cdn}"]`)
//         .find("td, .row-index, .grid-static-col")
//         .css({ "background-color": c.bg, "color": c.text || "" });
// }

// function highlight_all_rows(frm) {
//     (frm.doc.attendance_details || []).forEach(r => highlight_row(frm, r.name));
// }

// // ── fetch & populate ───────────────────────────────────────────────────────────
// function fetch_and_populate(frm) {
//     frappe.call({
//         method: "logicore.logicore.doctype.staff_attendance.staff_attendance.get_attendance_employees",
//         args: {
//             employee_type: frm.doc.employee_type,
//             company:       frm.doc.company || "",
//             date:          frm.doc.date    || "",
//         },
//         freeze: true,
//         freeze_message: __("Loading attendance..."),
//         callback(r) {
//             frm.clear_table("attendance_details");

//             if (r.message && r.message.length) {
//                 // Pre-fill Frappe's link-title cache so Dynamic Link shows "ID: Name"
//                 frappe._link_titles = frappe._link_titles || {};
//                 r.message.forEach(row => {
//                     frappe._link_titles[`${row.link_doctype}::${row.employee_link}`] = row.employee_name;
//                     let child = frm.add_child("attendance_details");
//                     child.link_doctype  = row.link_doctype;
//                     child.employee_link = row.employee_link;
//                     child.employee_name = row.employee_name;
//                     child.designation   = row.designation;
//                     child.status        = row.status;
//                 });
//             }

//             frm.refresh_field("attendance_details");
//             setTimeout(() => {
//                 highlight_all_rows(frm);
//                 render_summary(frm);
//                 render_search_bar(frm);
//             }, 200);
//         },
//     });
// }

// // ── name search bar above child table ──────────────────────────────────────────
// function render_search_bar(frm) {
//     let wrapper = frm.fields_dict.attendance_details.$wrapper;
//     wrapper.find(".att-name-search").remove();

//     let $bar = $(`
//         <div class="att-name-search" style="
//             display:flex;align-items:center;gap:8px;
//             padding:8px 0 6px;margin-bottom:4px;">
//             <span style="font-size:0.8rem;color:#6c757d;white-space:nowrap;">
//                 Search by Name:
//             </span>
//             <input type="text" placeholder="${__('Type name to filter rows...')}"
//                 style="
//                     flex:1;max-width:320px;height:30px;
//                     border:1px solid #d1d8dd;border-radius:5px;
//                     padding:0 10px;font-size:0.85rem;outline:none;
//                     transition:border-color .2s;"/>
//             <button class="att-search-clear btn btn-xs btn-default"
//                 style="display:none;">✕ Clear</button>
//         </div>
//     `);

//     wrapper.prepend($bar);

//     let $input = $bar.find("input");
//     let $clear = $bar.find(".att-search-clear");

//     $input.on("focus", () => $input.css("border-color", "#5e64ff"));
//     $input.on("blur",  () => $input.css("border-color", "#d1d8dd"));

//     $input.on("input", function() {
//         let q = (this.value || "").toLowerCase().trim();
//         $clear.toggle(!!q);
//         let grid = frm.fields_dict.attendance_details.grid;
//         grid.wrapper.find(".grid-row").each(function() {
//             let $row = $(this);
//             let name_cell = $row.find(".col[data-fieldname='employee_name']").text().toLowerCase();
//             let desig_cell = $row.find(".col[data-fieldname='designation']").text().toLowerCase();
//             if (!q || name_cell.includes(q) || desig_cell.includes(q)) {
//                 $row.show();
//             } else {
//                 $row.hide();
//             }
//         });
//     });

//     $clear.on("click", function() {
//         $input.val("").trigger("input").focus();
//     });
// }
// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// const STATUS_CONFIG = [
//     { key: "Present",              label: "PRESENT",              bg: "#d4edda", count_color: "#1e7e34", icon: "✔" },
//     { key: "Absent",               label: "ABSENT",               bg: "#f8d7da", count_color: "#c0392b", icon: "✘" },
//     { key: "On Leave With Pay",    label: "ON LEAVE WITH PAY",    bg: "#d0eaff", count_color: "#2471a3", icon: "📅" },
//     { key: "On Leave Without Pay", label: "ON LEAVE WITHOUT PAY", bg: "#fdebd0", count_color: "#d35400", icon: "📋" },
//     { key: "Sunday/Holiday",       label: "SUNDAY / HOLIDAY",     bg: "#e8e8e8", count_color: "#5d6d7e", icon: "🏖" },
// ];

// const ROW_COLORS = {
//     "Absent":               { bg: "#ffe0e0", text: "#c0392b" },
//     "On Leave With Pay":    { bg: "#d0eaff", text: "#2471a3" },
//     "On Leave Without Pay": { bg: "#fdebd0", text: "#d35400" },
//     "Sunday/Holiday":       { bg: "#ececec", text: "#7f8c8d" },
//     "Present":              { bg: "",        text: ""         },
// };

// // ── parent form events ─────────────────────────────────────────────────────────
// frappe.ui.form.on("Staff Attendance", {
//     refresh(frm) {
//         if (frm.is_new() && !frm.doc.attendance_no) {
//             frm.set_value("date", frappe.datetime.get_today());
//         }
//         if (!frm.is_new()) {
//             frm.set_df_property("date", "read_only", 1);
//             frm.set_df_property("employee_type", "read_only", 1);
//             frm.set_df_property("company", "read_only", 1);
//         }
//         // Proper Frappe API for child-table link query
//         frm.set_query("employee_link", "attendance_details", function(doc, cdt, cdn) {
//             let row = locals[cdt][cdn];
//             if (row.link_doctype === "Employee") {
//                 return { filters: { status: "Active" } };
//             } else if (row.link_doctype === "Driver") {
//                 return { filters: { status: "Active" } };
//             }
//             return {};
//         });
//         setTimeout(() => {
//             render_summary(frm);
//             highlight_all_rows(frm);
//             render_search_bar(frm);
//         }, 300);
//     },

//     employee_type(frm) {
//         if (!frm.doc.employee_type) {
//             frm.clear_table("attendance_details");
//             frm.refresh_field("attendance_details");
//             render_summary(frm);
//             // Remove search bar when employee_type is cleared
//            // frm.fields_dict.attendance_details.$wrapper.find(".att-name-search").remove();
//             return;
//         }
//         fetch_and_populate(frm);
//     },

//     date(frm) {
//         if (frm.doc.employee_type) fetch_and_populate(frm);
//     },
// });

// // ── child table events ─────────────────────────────────────────────────────────
// frappe.ui.form.on("Staff Attendance Detail", {
//     status(frm, cdt, cdn) {
//         highlight_row(frm, cdn);
//         render_summary(frm);
//     },
//     form_render(frm, cdt, cdn) {
//         highlight_row(frm, cdn);
//     },
//     attendance_details_remove(frm) {
//         render_summary(frm);
//     },
// });

// // ── summary card strip ─────────────────────────────────────────────────────────
// function render_summary(frm) {
//     let rows  = frm.doc.attendance_details || [];
//     let total = rows.length;

//     let counts = {};
//     STATUS_CONFIG.forEach(s => counts[s.key] = 0);
//     rows.forEach(r => { if (counts.hasOwnProperty(r.status)) counts[r.status]++; });

//     let cards_html = STATUS_CONFIG.map(s => `
//         <div style="
//             background:${s.bg};border-radius:10px;padding:14px 18px 12px;
//             min-width:110px;flex:1;text-align:center;
//             box-shadow:0 1px 4px rgba(0,0,0,.08);position:relative;overflow:hidden;">
//             <div style="font-size:2rem;font-weight:700;color:${s.count_color};line-height:1;margin-bottom:6px;">${counts[s.key]}</div>
//             <div style="font-size:0.62rem;font-weight:600;color:${s.count_color};letter-spacing:.04em;opacity:.85;">${s.label}</div>
//             <div style="position:absolute;right:10px;top:8px;font-size:1.5rem;opacity:.13;">${s.icon}</div>
//         </div>`).join("");

//     let total_html = `
//         <div style="
//             background:#f4f5f7;border-radius:10px;padding:14px 18px 12px;
//             min-width:80px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.08);">
//             <div style="font-size:2rem;font-weight:700;color:#2c3e50;line-height:1;margin-bottom:6px;">${total}</div>
//             <div style="font-size:0.62rem;font-weight:600;color:#5d6d7e;letter-spacing:.04em;">TOTAL</div>
//         </div>`;

//     frm.fields_dict.attendance_summary.$wrapper
//         .find("#att-summary-wrap")
//         .html(`<div style="display:flex;flex-wrap:wrap;gap:10px;padding:14px 0 10px;align-items:stretch;">
//             ${total_html}${cards_html}
//         </div>`);
// }

// // ── row highlighting ───────────────────────────────────────────────────────────
// function highlight_row(frm, cdn) {
//     let row_doc = locals["Staff Attendance Detail"]?.[cdn];
//     if (!row_doc) return;
//     let c = ROW_COLORS[row_doc.status] || ROW_COLORS["Present"];
//     frm.fields_dict.attendance_details.grid.wrapper
//         .find(`.grid-row[data-name="${cdn}"]`)
//         .find("td, .row-index, .grid-static-col")
//         .css({ "background-color": c.bg, "color": c.text || "" });
// }

// function highlight_all_rows(frm) {
//     (frm.doc.attendance_details || []).forEach(r => highlight_row(frm, r.name));
// }

// // ── fetch & populate ───────────────────────────────────────────────────────────
// function fetch_and_populate(frm) {
//     frappe.call({
//         method: "logicore.logicore.doctype.staff_attendance.staff_attendance.get_attendance_employees",
//         args: {
//             employee_type: frm.doc.employee_type,
//             company:       frm.doc.company || "",
//             date:          frm.doc.date    || "",
//         },
//         freeze: true,
//         freeze_message: __("Loading attendance..."),
//         callback(r) {
//             frm.clear_table("attendance_details");

//             if (r.message && r.message.length) {
//                 frappe._link_titles = frappe._link_titles || {};
//                 r.message.forEach(row => {
//                     frappe._link_titles[`${row.link_doctype}::${row.employee_link}`] = row.employee_name;
//                     let child = frm.add_child("attendance_details");
//                     child.link_doctype  = row.link_doctype;
//                     child.employee_link = row.employee_link;
//                     child.employee_name = row.employee_name;
//                     child.designation   = row.designation;
//                     child.status        = row.status;
//                 });
//             }

//             frm.refresh_field("attendance_details");
//             setTimeout(() => {
//                 highlight_all_rows(frm);
//                 render_summary(frm);
//                 render_search_bar(frm);
//             }, 200);
//         },
//     });
// }

// // ── name search bar above child table grid ─────────────────────────────────────
// // Targets the grid body so the bar sits identically for BOTH Employee and Driver.
// // Uses grid.wrapper (same reference Frappe uses internally) which is available
// // regardless of employee_type — so layout is always consistent.
// function render_search_bar(frm) {
//     let grid = frm.fields_dict.attendance_details.grid;
//     if (!grid || !grid.wrapper) return;

//     // Remove any existing search bar to avoid duplicates on re-render
//     grid.wrapper.find(".att-name-search").remove();

//     let $bar = $(`
//         <div class="att-name-search" style="
//             display:flex;align-items:center;gap:8px;
//             padding:8px 10px 6px;margin-bottom:2px;
//             border-bottom:1px solid #e8e8e8;background:#fff;">
//             <span style="font-size:0.8rem;color:#6c757d;white-space:nowrap;">
//                 Search by Name:
//             </span>
//             <input type="text" placeholder="${__('Type name to filter rows...')}"
//                 style="
//                     flex:1;max-width:320px;height:30px;
//                     border:1px solid #d1d8dd;border-radius:5px;
//                     padding:0 10px;font-size:0.85rem;outline:none;
//                     transition:border-color .2s;"/>
//             <button class="att-search-clear btn btn-xs btn-default"
//                 style="display:none;">✕ Clear</button>
//         </div>
//     `);

//     // ── KEY FIX: insert AFTER the column-header row (.grid-heading) ──
//     // This places the bar in the same position for Employee and Driver.
//     let $heading = grid.wrapper.find(".grid-heading");
//     if ($heading.length) {
//         $heading.after($bar);
//     } else {
//         // Fallback: prepend to grid wrapper if heading not found yet
//         grid.wrapper.prepend($bar);
//     }

//     let $input = $bar.find("input");
//     let $clear = $bar.find(".att-search-clear");

//     $input.on("focus", () => $input.css("border-color", "#5e64ff"));
//     $input.on("blur",  () => $input.css("border-color", "#d1d8dd"));

//     $input.on("input", function() {
//         let q = (this.value || "").toLowerCase().trim();
//         $clear.toggle(!!q);
//         grid.wrapper.find(".grid-row").each(function() {
//             let $row = $(this);
//             let name_cell  = $row.find(".col[data-fieldname='employee_name']").text().toLowerCase();
//             let desig_cell = $row.find(".col[data-fieldname='designation']").text().toLowerCase();
//             if (!q || name_cell.includes(q) || desig_cell.includes(q)) {
//                 $row.show();
//             } else {
//                 $row.hide();
//             }
//         });
//     });

//     $clear.on("click", function() {
//         $input.val("").trigger("input").focus();
//     });
// }
// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

const STATUS_CONFIG = [
    { key: "Present",              label: "PRESENT",              bg: "#d4edda", count_color: "#1e7e34", icon: "✔" },
    { key: "Absent",               label: "ABSENT",               bg: "#f8d7da", count_color: "#c0392b", icon: "✘" },
    { key: "On Leave With Pay",    label: "ON LEAVE WITH PAY",    bg: "#d0eaff", count_color: "#2471a3", icon: "📅" },
    { key: "On Leave Without Pay", label: "ON LEAVE WITHOUT PAY", bg: "#fdebd0", count_color: "#d35400", icon: "📋" },
    { key: "Sunday/Holiday",       label: "SUNDAY / HOLIDAY",     bg: "#e8e8e8", count_color: "#5d6d7e", icon: "🏖" },
];

const ROW_COLORS = {
    "Absent":               { bg: "#ffe0e0", text: "#c0392b" },
    "On Leave With Pay":    { bg: "#d0eaff", text: "#2471a3" },
    "On Leave Without Pay": { bg: "#fdebd0", text: "#d35400" },
    "Sunday/Holiday":       { bg: "#ececec", text: "#7f8c8d" },
    "Present":              { bg: "",        text: ""         },
};

// ── parent form events ─────────────────────────────────────────────────────────
frappe.ui.form.on("Staff Attendance", {
    refresh(frm) {
        if (frm.is_new() && !frm.doc.attendance_no) {
            frm.set_value("date", frappe.datetime.get_today());
        }
        // Saving a draft used to lock these ("!frm.is_new()"), leaving no way to
        // correct a wrong date without cancelling. Only submission locks them
        // now. set_df_property writes to shared docfield meta, so the unlocked
        // state has to be set explicitly too — otherwise opening a submitted
        // record leaves the fields read-only for the next draft in the session.
        const locked = frm.doc.docstatus > 0 ? 1 : 0;
        frm.set_df_property("date", "read_only", locked);
        frm.set_df_property("employee_type", "read_only", locked);
        frm.set_df_property("company", "read_only", locked);
        frm.set_query("employee_link", "attendance_details", function(doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            if (row.link_doctype === "Employee") {
                return { filters: { status: "Active" } };
            } else if (row.link_doctype === "Driver") {
                return { filters: { status: "Active" } };
            }
            return {};
        });
        setTimeout(() => {
            render_summary(frm);
            highlight_all_rows(frm);
            apply_all_work_at_states(frm);
        }, 300);
    },

    employee_type(frm) {
        if (!frm.doc.employee_type) {
            frm.clear_table("attendance_details");
            frm.refresh_field("attendance_details");
            render_summary(frm);
            return;
        }
        fetch_and_populate(frm);
    },

    date(frm) {
        if (!frm.doc.employee_type) return;
        // fetch_and_populate() rebuilds the table from scratch, so every status
        // already marked would be lost. Correcting a wrong date is the main
        // reason to touch this field, so ask before throwing that work away —
        // declining keeps the new date and leaves the existing rows alone.
        if ((frm.doc.attendance_details || []).length) {
            frappe.confirm(
                __("Reload the employee list for this date? Statuses you have already marked will be cleared."),
                () => fetch_and_populate(frm)
            );
            return;
        }
        fetch_and_populate(frm);
    },
});

// ── child table events ─────────────────────────────────────────────────────────
frappe.ui.form.on("Staff Attendance Detail", {
    employee_link(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.employee_link || !row.link_doctype) return;

        if (row.link_doctype === "Employee") {
            frappe.db.get_value("Employee", row.employee_link, ["employee_name", "designation", "branch"], (val) => {
                if (!val) return;
                frappe.model.set_value(cdt, cdn, "employee_name", val.employee_name || "");
                frappe.model.set_value(cdt, cdn, "designation", val.designation || "");
                frappe.model.set_value(cdt, cdn, "branch", val.branch || "");
            });
        } else if (row.link_doctype === "Driver") {
            frappe.db.get_value("Driver", row.employee_link, ["full_name", "custom_branch"], (val) => {
                if (!val) return;
                frappe.model.set_value(cdt, cdn, "employee_name", val.full_name || "");
                frappe.model.set_value(cdt, cdn, "designation", "Driver");
                frappe.model.set_value(cdt, cdn, "branch", val.custom_branch || "");
            });
        }
    },
    status(frm, cdt, cdn) {
        highlight_row(frm, cdn);
        render_summary(frm);
        _toggle_work_at(frm, cdt, cdn);
    },
    form_render(frm, cdt, cdn) {
        highlight_row(frm, cdn);
        _toggle_work_at(frm, cdt, cdn);
    },
    work_at(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row) return;
        if (row.status !== "Present" && row.work_at) {
            frappe.model.set_value(cdt, cdn, "work_at", "");
            frappe.msgprint(__("Work At can only be set when employee is Present."));
        }
    },
    attendance_details_remove(frm) {
        render_summary(frm);
    },
});

// work_at editable only for Present rows — controls expanded form + inline cell
function _toggle_work_at(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!row) return;
    const is_present = row.status === "Present";

    // Default "On Duty" when Present; clear when not Present
    if (is_present && !row.work_at) {
        frappe.model.set_value(cdt, cdn, "work_at", "On Duty");
    } else if (!is_present && row.work_at) {
        frappe.model.set_value(cdt, cdn, "work_at", "");
    }

    // Expanded row form: set field read_only
    const grid_row = frm.fields_dict.attendance_details.grid.get_row(cdn);
    if (grid_row && grid_row.grid_form && grid_row.grid_form.fields_dict.work_at) {
        grid_row.grid_form.set_df_property("work_at", "read_only", is_present ? 0 : 1);
        grid_row.grid_form.refresh_field("work_at");
    }

    // Inline grid cell: block clicks for non-Present rows, no opacity change
    setTimeout(() => {
        frm.fields_dict.attendance_details.grid.wrapper
            .find(`.grid-row[data-name="${cdn}"] .col[data-fieldname="work_at"]`)
            .css("pointer-events", is_present ? "" : "none");
    }, 50);
}

// Apply work_at state to all rows (called after populate / refresh)
function apply_all_work_at_states(frm) {
    (frm.doc.attendance_details || []).forEach(row => {
        _toggle_work_at(frm, "Staff Attendance Detail", row.name);
    });
}

// ── summary card strip ─────────────────────────────────────────────────────────
function render_summary(frm) {
    let rows  = frm.doc.attendance_details || [];
    let total = rows.length;

    let counts = {};
    STATUS_CONFIG.forEach(s => counts[s.key] = 0);
    rows.forEach(r => { if (counts.hasOwnProperty(r.status)) counts[r.status]++; });

    let cards_html = STATUS_CONFIG.map(s => `
        <div style="
            background:${s.bg};border-radius:10px;padding:14px 18px 12px;
            min-width:110px;flex:1;text-align:center;
            box-shadow:0 1px 4px rgba(0,0,0,.08);position:relative;overflow:hidden;">
            <div style="font-size:2rem;font-weight:700;color:${s.count_color};line-height:1;margin-bottom:6px;">${counts[s.key]}</div>
            <div style="font-size:0.62rem;font-weight:600;color:${s.count_color};letter-spacing:.04em;opacity:.85;">${s.label}</div>
            <div style="position:absolute;right:10px;top:8px;font-size:1.5rem;opacity:.13;">${s.icon}</div>
        </div>`).join("");

    let total_html = `
        <div style="
            background:#f4f5f7;border-radius:10px;padding:14px 18px 12px;
            min-width:80px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.08);">
            <div style="font-size:2rem;font-weight:700;color:#2c3e50;line-height:1;margin-bottom:6px;">${total}</div>
            <div style="font-size:0.62rem;font-weight:600;color:#5d6d7e;letter-spacing:.04em;">TOTAL</div>
        </div>`;

    frm.fields_dict.attendance_summary.$wrapper
        .find("#att-summary-wrap")
        .html(`<div style="display:flex;flex-wrap:wrap;gap:10px;padding:14px 0 10px;align-items:stretch;">
            ${total_html}${cards_html}
        </div>`);
}

// ── row highlighting ───────────────────────────────────────────────────────────
function highlight_row(frm, cdn) {
    let row_doc = locals["Staff Attendance Detail"]?.[cdn];
    if (!row_doc) return;
    let c = ROW_COLORS[row_doc.status] || ROW_COLORS["Present"];
    frm.fields_dict.attendance_details.grid.wrapper
        .find(`.grid-row[data-name="${cdn}"]`)
        .find("td, .row-index, .grid-static-col")
        .css({ "background-color": c.bg, "color": c.text || "" });
}

function highlight_all_rows(frm) {
    (frm.doc.attendance_details || []).forEach(r => highlight_row(frm, r.name));
}

// ── fetch & populate ───────────────────────────────────────────────────────────
function fetch_and_populate(frm) {
    frappe.call({
        method: "logicore.logicore.doctype.staff_attendance.staff_attendance.get_attendance_employees",
        args: {
            employee_type: frm.doc.employee_type,
            company:       frm.doc.company || "",
            date:          frm.doc.date    || "",
        },
        freeze: true,
        freeze_message: __("Loading attendance..."),
        callback(r) {
            frm.clear_table("attendance_details");

            if (r.message && r.message.length) {
                frappe._link_titles = frappe._link_titles || {};
                r.message.forEach(row => {
                    frappe._link_titles[`${row.link_doctype}::${row.employee_link}`] = row.employee_name;
                    let child = frm.add_child("attendance_details");
                    child.link_doctype  = row.link_doctype;
                    child.employee_link = row.employee_link;
                    child.employee_name = row.employee_name;
                    child.designation   = row.designation;
                    child.branch        = row.branch || "";
                    child.status        = row.status;
                    child.work_at       = row.work_at || "";
                });
            }

            frm.refresh_field("attendance_details");
            setTimeout(() => {
                highlight_all_rows(frm);
                render_summary(frm);
                apply_all_work_at_states(frm);
            }, 200);
        },
    });
}