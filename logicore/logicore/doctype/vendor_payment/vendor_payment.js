frappe.ui.form.on("Vendor Payment", {
	refresh(frm) {
		frm.add_custom_button(__("Print Payment"), function () {
			frappe.utils.print(frm.doctype, frm.docname, "Vendor Payment TMS", frm.doc.language);
		}).addClass("btn-primary");

		style_fetch_btn(frm);
		attach_delete_totals_handler(frm);
		if (typeof render_summary_cards === "function") render_summary_cards(frm);
		watch_trips_grid_for_phantom_rows(frm);

		// Trips only ever come from "Fetch Trips" — a manually added blank row
		// has no valid Trip and just trips mandatory validation on save.
		// Frappe's grid auto-adds a blank row on Tab/Enter in the last cell of
		// the last row unless this is set, which is how empty rows were
		// sneaking in without anyone clicking "Add row". Setting it via
		// set_df_property alone isn't reliably picked up by the already-built
		// grid instance's own add_new_row() check, so it's also set directly
		// on the grid object here.
		frm.set_df_property("trips", "cannot_add_rows", 1);
		const trips_grid = frm.fields_dict?.trips?.grid;
		if (trips_grid) trips_grid.cannot_add_rows = true;

		schedule_force_trips_rebuild(frm);
		start_phantom_row_watchdog(frm);
		block_trips_grid_dblclick(frm);
		attach_lr_lock_notice(frm);
	},

	setup(frm) {
		frm.set_query("paid_from_account", () => ({
			filters: { group: frm.doc.mode_of_payment === "Cash" ? "CASH" : "BANK" }
		}));
	},

	mode_of_payment(frm) {
		frm.set_value("paid_from_account", null);
	},

	validate(frm) {
		// Defensive: a row with no Trip was never real data (Trip only ever
		// comes from Fetch Trips) — drop it instead of blocking save with a
		// bogus mandatory-field error, no matter how it ended up in the table.
		frm.doc.trips = (frm.doc.trips || []).filter((row) => row.trip);
	},

	before_save(frm) {
		// schedule_force_trips_rebuild() wipes grid.grid_rows synchronously
		// and repopulates it 150ms later. Flushing any pending rebuild
		// immediately before save guarantees the grid is never caught
		// mid-wipe when Frappe renders it.
		if (frm.__trips_rebuild_timer) {
			window.clearTimeout(frm.__trips_rebuild_timer);
			frm.__trips_rebuild_timer = null;
			force_trips_grid_rebuild(frm);
		}

		// Frappe's pre-save mandatory check (frappe.ui.form.check_mandatory ->
		// frappe.model.has_value) doesn't read df.reqd fields off the row
		// object in frm.doc.trips — it looks the row up in the global
		// `locals` cache by doctype+name and reads the field from there.
		// After enough fetch/edit/remove/save cycles on this form, a row's
		// `locals` entry can end up missing or stale (observed: a row fully
		// populated in frm.doc.trips with locals[doctype][name] === undefined)
		// even though frm.doc.trips itself is correct, which makes the
		// mandatory check throw a false "Trip is required in row N" and
		// blocks save entirely. Re-registering every current row here right
		// before Frappe's check runs guarantees locals always mirrors
		// frm.doc.trips at the moment it matters.
		(frm.doc.trips || []).forEach((row) => {
			if (!locals[row.doctype]) locals[row.doctype] = {};
			locals[row.doctype][row.name] = row;
		});
	},

	fetch_trips_btn(frm) {
    if (!frm.doc.vendor) {
        frappe.msgprint(__("Please select a Vendor first."));
        return;
    }
    if (!frm.doc.from_date || !frm.doc.to_date) {
        frappe.msgprint(__("Please select From Date and To Date."));
        return;
    }

    frappe.call({
        method: "logicore.logicore.doctype.vendor_payment.vendor_payment.get_unpaid_trips",
        args: {
            vendor: frm.doc.vendor,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date,
            company: frm.doc.company,
        },
        freeze: true,
        freeze_message: __("Fetching trips..."),
        callback(r) {
            if (!r.message || !r.message.length) {
                frappe.msgprint(__("No unpaid trips found for this vendor and date range."));
                return;
            }

            frm.clear_table("trips");

            r.message.forEach((t) => {
                const row = frm.add_child("trips");

                // -- Core identifiers
                row.trip          = t.name;
                row.trip_date     = t.tcntrip_date;
                row.tcntrip_no    = t.tcntrip_no;
                row.lr_no         = t.lr_no;
                row.vehicle_no    = t.vehicle_no || t.vehicle_market;

                // -- Route info
                row.origin_city        = t.origin_city;
                row.destination_city   = t.destination_city_1;

                // -- Financial fields
                row.hire_amount        = flt(t.total_vendor_freight);
                row.tds_amount         = flt(t.vendor_tds_to_be_deducted);
                row.employee_lr_money  = flt(t.employee_lr_money);
                row.employee_lr_locked = t.employee_lr_locked ? 1 : 0;
                row.company_lr_money   = flt(t.company_lr_money);
                row.company_lr_locked  = t.company_lr_locked ? 1 : 0;

                // -- Balance = what's still owed
                row.balance = flt(t.vendor_balance_amount)
                    || flt(t.amount_to_be_paid_to_vendor)
                    || 0;

                // -- Default payment = full balance
                row.payment_amount = row.balance;

                // -- Recalc transfer amount for this row
                recalc_row(row);
			});

            frm.refresh_field("trips");
            schedule_recalc_totals(frm);
            schedule_force_trips_rebuild(frm);
            // Don't wait on the observer/500ms watchdog to catch a ghost row
            // that grid.js leaves behind right after this bulk refresh_field —
            // check immediately so nothing is ever visible even for a moment.
            hide_phantom_trip_rows(frm);

            frappe.show_alert(
                { message: __("{0} trip(s) loaded.", [r.message.length]), indicator: "green" },
                3
            );
        },
    });
},

	trips_remove(frm) {
		schedule_recalc_totals(frm);
		schedule_force_trips_rebuild(frm);
	},

	trips_delete(frm) {
		schedule_recalc_totals(frm);
		schedule_force_trips_rebuild(frm);
	},
});

frappe.ui.form.on("Vendor Payment Trip", {
	trip(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.trip) return;
		frappe.db.get_value("Trip", row.trip, ["vehicle_no", "vehicle_market"]).then((r) => {
			const vehicle_no = (r.message && (r.message.vehicle_no || r.message.vehicle_market)) || "";
			frappe.model.set_value(cdt, cdn, "vehicle_no", vehicle_no);
		});
	},
	payment_amount(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		recalc_totals(frm);
	},
	employee_lr_money(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		recalc_totals(frm);
	},
	company_lr_money(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		recalc_totals(frm);
	},
	tds_amount(frm, cdt, cdn) {
		recalc_row(frappe.get_doc(cdt, cdn));
		recalc_totals(frm);
	},
});

function style_fetch_btn(frm) {
	const $field = frm.get_field("fetch_trips_btn").$wrapper;
	const $btn = $field.find("button");
	// Push button down to align vertically with input fields (compensate for label height)
	$field.css({ "margin-top": "21px" });
	$btn.css({
		"background": "linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%)",
		"color": "#fff",
		"font-weight": "700",
		"font-size": "14px",
		"padding": "10px 32px",
		"border": "none",
		"border-radius": "8px",
		"box-shadow": "0 4px 14px rgba(108,92,231,0.4)",
		"cursor": "pointer",
		"letter-spacing": "0.5px",
		"width": "100%",
		"transition": "all 0.2s ease",
	});
	$btn.on("mouseenter", function() {
		$(this).css({ "transform": "translateY(-1px)", "box-shadow": "0 6px 18px rgba(108,92,231,0.5)" });
	}).on("mouseleave", function() {
		$(this).css({ "transform": "translateY(0)", "box-shadow": "0 4px 14px rgba(108,92,231,0.4)" });
	});
}

function recalc_row(row) {
	const pay = flt(row.payment_amount);
	const tds = flt(row.tds_amount);
	const lr = flt(row.employee_lr_money) + flt(row.company_lr_money);
	frappe.model.set_value(row.doctype, row.name, "transfer_amount", pay - tds - lr);
}

function recalc_totals(frm) {
	let total_pay = 0,
		total_lr = 0,
		total_tds = 0,
		total_xfr = 0,
		total_hire = 0;

	const rows = get_trip_rows(frm);

	rows.forEach((r) => {
		total_pay  += flt(r.payment_amount);
		total_lr   += flt(r.employee_lr_money) + flt(r.company_lr_money);
		total_tds  += flt(r.tds_amount);
		total_xfr  += flt(r.transfer_amount);
		total_hire += flt(r.hire_amount);
	});

	frm.set_value("total_payment_amount", total_pay);
	frm.set_value("total_lr_money", total_lr);
	frm.set_value("total_tds_amount", total_tds);
	frm.set_value("total_transfer_amount", total_xfr);
	frm.set_value("total_hire_amount", total_hire);
	frm.set_value("total_outstanding_amount", total_hire - total_pay);
	frm.refresh_fields([
		"total_payment_amount",
		"total_lr_money",
		"total_tds_amount",
		"total_transfer_amount",
		"total_hire_amount",
		"total_outstanding_amount",
	]);
}

function schedule_recalc_totals(frm) {
	window.setTimeout(() => recalc_totals(frm), 100);
}

// The site's grid.js can leave a stale row behind whose bound `doc` no longer
// matches any row in frm.doc.trips (seen after fetching/removing trip rows) —
// Frappe then renders that row's cells as each column's field *label*
// ("Trip", "Trip Date", ...) instead of a value, looking like a duplicate
// header row. Removing such rows from the DOM/grid state previously caused
// data corruption (an empty row silently ending up in frm.doc.trips), so this
// only *hides* them with CSS — it never touches grid.grid_rows or
// frm.doc.trips, so it cannot affect what actually gets saved. A
// MutationObserver re-checks whenever the grid's rows are redrawn (fetch,
// row add/remove, field edits), since there's no single safe place to hook.
function hide_phantom_trip_rows(frm) {
	const grid = frm.fields_dict?.trips?.grid;
	if (!grid || !grid.wrapper) return;

	const seenNames = new Set();
	grid.wrapper.find(".rows > .grid-row").each(function () {
		const $row = $(this);
		// grid_row.js only sets data-name when the row has a real bound doc —
		// a phantom row has none, so this catches it regardless of which
		// column's label text happens to be showing.
		const rowName = $row.attr("data-name");

		// A row bound to a real doc with a Trip value is never phantom, no
		// matter what its DOM currently shows. Toggling a row between
		// edit-mode inputs and display-mode labels (e.g. on Escape/blur after
		// editing) briefly swaps out its cells, and during that swap the Trip
		// cell can read as empty text even though the row is completely
		// valid — checking frm.doc.trips (the actual data) instead of that
		// transient DOM text stops a real row from being hidden, and
		// visibly flickering away, mid-transition.
		const doc_row = rowName && (frm.doc.trips || []).find((r) => r.name === rowName);
		if (doc_row && doc_row.trip) {
			if (seenNames.has(rowName)) {
				$row.hide();
				return;
			}
			seenNames.add(rowName);
			$row.show();
			return;
		}

		const $tripCell = $row.find('[data-fieldname="trip"]').first();
		const tripCellText = $tripCell.text().trim();
		// A ghost row that got a real (empty) doc shows an actual empty input
		// for Trip instead of static label text — catch that too. Unlike a
		// generic Frappe grid, a row here can never legitimately be created
		// for someone to type a fresh Trip into — cannot_add_rows blocks every
		// UI path that adds a row, and every real row always arrives already
		// carrying a Trip from Fetch Trips. So an empty-Trip row is never a
		// row-in-progress worth protecting from being hidden while focused —
		// it is always illegitimate, focused or not, and must never stay
		// visible just because it happens to have focus.
		const $tripInput = $tripCell.find("input");
		const tripInputEmpty = $tripInput.length > 0 && !$tripInput.val();

		if (!rowName || tripCellText === "Trip" || tripInputEmpty) {
			$row.hide();
			return;
		}
		// Same underlying row occasionally gets rendered as two DOM elements —
		// keep only the first, hide the rest. Purely visual: doesn't touch
		// grid.grid_rows or frm.doc.trips, so it can't affect what saves.
		if (seenNames.has(rowName)) {
			$row.hide();
			return;
		}
		seenNames.add(rowName);
		$row.show();
	});

	// grid.js doesn't always refresh a surviving row's displayed "No." after
	// another row is removed, leaving gaps (1, 2, 4 instead of 1, 2, 3). This
	// only rewrites the on-screen label — row.idx / frm.doc.trips are untouched.
	let visibleIdx = 0;
	grid.wrapper.find(".rows > .grid-row:visible").each(function () {
		visibleIdx += 1;
		$(this).find(".row-index span, .grid-form-row-index").text(visibleIdx);
	});
}

// Beyond the cosmetic phantom-row issue, the same stale identity matching in
// grid.js can bind an on-screen row to the WRONG underlying trip after a row
// is removed and the grid re-renders — so editing "row 2" can silently edit
// a different trip's data, which is a real data-integrity risk, not just a
// display glitch. Wiping the grid's own row-tracking forces every row to
// rebind fresh against the current frm.doc.trips, with nothing stale left to
// mismatch against. An earlier version of this caused a blank row to appear
// in frm.doc.trips (removing a DOM row mid-edit could still trigger grid.js's
// own "add new row" side effect) — that trigger is now hard-blocked via
// `grid.cannot_add_rows = true` set in refresh(), so this is safe to run.
function force_trips_grid_rebuild(frm) {
	const grid = frm.fields_dict?.trips?.grid;
	if (!grid || !grid.wrapper) return;

	// Never wipe the grid's DOM/row-tracking while the user currently has a
	// row open for editing. This is the actual root cause of the "ghost row
	// showing field labels" bug: save's server-side zero-payment removal
	// schedules this rebuild for 150ms later; if the user double-clicks the
	// next row to edit it before that fires (very likely when working through
	// several rows back-to-back), the rebuild wipes the very row they just
	// opened out from under them mid-edit, corrupting the grid's row-tracking.
	// Deferring instead of forcing it through — the reschedule keeps retrying
	// every 150ms until the row is closed, so the rebuild still always
	// eventually happens, just never mid-edit.
	if (frappe.ui.form.editable_row && frappe.ui.form.editable_row.grid === grid) {
		schedule_force_trips_rebuild(frm);
		return;
	}

	grid.cannot_add_rows = true;
	grid.wrapper.find(".rows > .grid-row").remove();
	grid.grid_rows = [];
	grid.grid_rows_by_docname = {};
	grid.refresh();
	// grid.refresh() renders every row fresh — check for ghosts immediately
	// instead of waiting for the observer/watchdog to get to it.
	hide_phantom_trip_rows(frm);
}

function schedule_force_trips_rebuild(frm) {
	// Track the timer handle (and clear any earlier pending one) so
	// before_save() can flush it synchronously instead of letting a save
	// race a rebuild that's already in flight.
	if (frm.__trips_rebuild_timer) window.clearTimeout(frm.__trips_rebuild_timer);
	frm.__trips_rebuild_timer = window.setTimeout(() => {
		frm.__trips_rebuild_timer = null;
		force_trips_grid_rebuild(frm);
	}, 150);
}

function watch_trips_grid_for_phantom_rows(frm) {
	const grid = frm.fields_dict?.trips?.grid;
	if (!grid || !grid.wrapper || grid.__phantom_row_observer) return;
	const rowsEl = grid.wrapper.find(".rows").get(0);
	if (!rowsEl) return;

	const observer = new MutationObserver(() => hide_phantom_trip_rows(frm));
	observer.observe(rowsEl, { childList: true });
	grid.__phantom_row_observer = observer;

	// Belt-and-braces recheck on blur too, on top of the observer/watchdog —
	// a ghost row is now hidden immediately even while focused (see
	// hide_phantom_trip_rows), but this catches the case right as focus
	// leaves it, before the next observer/watchdog tick would.
	grid.wrapper.off("focusout.vendor_payment_phantom");
	grid.wrapper.on("focusout.vendor_payment_phantom", ".rows", () => {
		window.setTimeout(() => hide_phantom_trip_rows(frm), 50);
	});
	hide_phantom_trip_rows(frm);
}

// Belt-and-braces: whatever is creating empty ghost rows, this periodically
// re-hides/renumbers via hide_phantom_trip_rows. Display-only — it never
// removes or modifies frm.doc.trips itself, so no filled-in row can ever
// disappear this way. Actual removal of a genuinely empty (no Trip) row only
// ever happens in validate() at save time, same as before. Runs every 500ms
// only while this form is on screen; cleared on navigating away.
function start_phantom_row_watchdog(frm) {
	if (frm.__phantom_watchdog) window.clearInterval(frm.__phantom_watchdog);

	frm.__phantom_watchdog = window.setInterval(() => {
		if (frm.doc.doctype !== "Vendor Payment" || cur_frm !== frm) {
			window.clearInterval(frm.__phantom_watchdog);
			return;
		}
		// Belt-and-braces: if the grid ever swapped in a new .rows element,
		// the observer bound in watch_trips_grid_for_phantom_rows() would be
		// watching a detached node and silently stop firing for good.
		// Re-attach against the live node instead of trusting the
		// __phantom_row_observer guard forever.
		const grid = frm.fields_dict?.trips?.grid;
		const rowsEl = grid?.wrapper?.find(".rows").get(0);
		if (rowsEl && grid.__phantom_row_observer && !rowsEl.isConnected) {
			grid.__phantom_row_observer.disconnect();
			grid.__phantom_row_observer = null;
		}
		if (grid && rowsEl && !grid.__phantom_row_observer) {
			watch_trips_grid_for_phantom_rows(frm);
		}
		hide_phantom_trip_rows(frm);
	}, 500);

	$(window).off("hashchange.vendor_payment_watchdog").on("hashchange.vendor_payment_watchdog", () => {
		if (!frappe.get_route || frappe.get_route()[0] !== "vendor-payment") {
			window.clearInterval(frm.__phantom_watchdog);
		}
	});
}

function get_trip_rows(frm) {
	return frm.fields_dict?.trips?.grid?.get_data?.() || frm.doc.trips || [];
}

function attach_delete_totals_handler(frm) {
	const grid = frm.fields_dict?.trips?.grid;
	if (!grid?.wrapper) return;

	grid.wrapper.off("click.vendor_payment_totals");
	grid.wrapper.on("click.vendor_payment_totals", ".grid-remove-rows, .grid-remove-all-rows", () => {
		schedule_recalc_totals(frm);
	});
}

// A single click on a collapsed row cell already opens it for editing
// (grid_row.js's own column click handler) — a second click landing back on
// that same cell a moment later, while the row is mid-transition from
// collapsed to its much taller open-edit layout, hits whatever now happens to
// be under those same screen coordinates instead of the element the user
// actually meant to click, since the layout just shifted under the cursor.
// That misdirected second click is what corrupts the grid into showing field
// *labels* instead of values for a row. Double-clicking to edit is habit, not
// necessity here — a single click already does the job — so the second click
// of any double-click within the trips grid is caught and killed in the
// capturing phase, before grid_row.js's own bubble-phase click handler ever
// sees it, closing off the whole class of trigger regardless of exactly what
// downstream Frappe code the misdirected click was landing on.
function block_trips_grid_dblclick(frm) {
	const grid = frm.fields_dict?.trips?.grid;
	if (!grid || !grid.wrapper || grid.__dblclick_guard_attached) return;
	grid.__dblclick_guard_attached = true;

	const rowsEl = grid.wrapper.find(".rows").get(0);
	if (!rowsEl) return;

	let last_click_at = 0;
	rowsEl.addEventListener(
		"click",
		(e) => {
			const now = Date.now();
			if (now - last_click_at < 500) {
				e.stopPropagation();
				e.preventDefault();
				last_click_at = 0;
				return;
			}
			last_click_at = now;
		},
		true
	);
}

// Once employee_lr_money/company_lr_money is deducted for a trip in an
// earlier submitted payment, the field goes read-only (read_only_depends_on
// employee_lr_locked/company_lr_locked — see vendor_payment_trip.json) so it
// can't be re-deducted. A plain read-only field gives no reason why it's
// locked, so a click on either cell shows which trip already had it
// deducted. This doctype has editable_grid: 1, so Frappe's own grid_row.js
// binds a bubble-phase click handler directly on every `.grid-static-col`
// that synchronously swaps it for an inline input (toggle_editable_row) —
// same root cause block_trips_grid_dblclick documents above. A delegated
// bubble-phase listener on the grid wrapper never sees the click because the
// original cell is already gone from the DOM by the time bubbling would
// reach it, so this binds on the rows container in the CAPTURE phase
// instead, guaranteeing it runs before Frappe's handler touches the DOM.
function attach_lr_lock_notice(frm) {
	const grid = frm.fields_dict?.trips?.grid;
	if (!grid || !grid.wrapper || grid.__lr_lock_notice_attached) return;

	const rowsEl = grid.wrapper.find(".rows").get(0);
	if (!rowsEl) return;
	grid.__lr_lock_notice_attached = true;

	rowsEl.addEventListener(
		"click",
		(e) => {
			const cell = e.target.closest(
				'[data-fieldname="employee_lr_money"], [data-fieldname="company_lr_money"]'
			);
			if (!cell) return;

			const fieldname = cell.getAttribute("data-fieldname");
			const rowName = cell.closest(".grid-row")?.getAttribute("data-name");
			const row = (frm.doc.trips || []).find((r) => r.name === rowName);
			if (!row) return;

			const is_employee = fieldname === "employee_lr_money";
			const locked = is_employee ? row.employee_lr_locked : row.company_lr_locked;
			if (!locked) return;

			const label = is_employee ? __("Employee LR Money") : __("Company LR Money");
			frappe.show_alert({
				message: __("{0} is already deducted for Trip {1} in an earlier payment — it cannot be deducted again.", [label, row.trip]),
				indicator: "orange",
			}, 6);
		},
		true
	);
}
