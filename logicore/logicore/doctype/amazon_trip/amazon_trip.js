// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// ══════════════════════════════════════════════════════════════════
//  THEME — "Ocean Command"  (mirrors Trip → Primary → Ocean Command)
// ══════════════════════════════════════════════════════════════════

// ── Default combo (used before trip_type is selected) ──────────────
const AT_COMBO_DEFAULT = {
	page_bg:        "#EEF2FF",
	card_bg:        "#FFFFFF",
	section_border: "#C7D7FF",
	field_bg:       "#F0F4FF",
	field_border:   "#A5B4FC",
	primary:        "#3B4FE4",
	accent:         "#06B6D4",
	label_color:    "#3730A3",
	heading_color:  "#1E1B4B",
	radius:         "10px",
};

// ── Per-trip-type combos (mirrors Trip doctype pattern) ─────────────
const AT_TRIP_COMBOS = {
	"SCHEDULED TRIP":       {
		page_bg:        "#F0FDF4",
		card_bg:        "#FFFFFF",
		section_border: "#BBF7D0",
		field_bg:       "#F0FDF8",
		field_border:   "#86EFAC",
		primary:        "#15803D",
		accent:         "#0D9488",
		label_color:    "#166534",
		heading_color:  "#14532D",
		radius:         "10px",
	},
	"SPOT & CONTRACT TRIP": {
		page_bg:        "#FFF7ED",
		card_bg:        "#FFFFFF",
		section_border: "#FED7AA",
		field_bg:       "#FFFBF5",
		field_border:   "#FDBA74",
		primary:        "#EA580C",
		accent:         "#D97706",
		label_color:    "#9A3412",
		heading_color:  "#7C2D12",
		radius:         "10px",
	},
};

function at_get_combo(trip_type) {
	return AT_TRIP_COMBOS[trip_type] || AT_COMBO_DEFAULT;
}

const AT_COMBO = AT_COMBO_DEFAULT;

// ══════════════════════════════════════════════════════════════════
//  STATUS CONFIG
// ══════════════════════════════════════════════════════════════════

const TRIP_STATUS_CONFIG = {
	"Pending":    { bg: "#FEF3C7", color: "#92400E", border: "#FDE68A", icon: "⏳" },
	"In Transit": { bg: "#EFF6FF", color: "#1D4ED8", border: "#BFDBFE", icon: "🚛" },
	"Delivered":  { bg: "#ECFDF5", color: "#065F46", border: "#A7F3D0", icon: "✅" },
	"Cancelled":  { bg: "#FEF2F2", color: "#991B1B", border: "#FECACA", icon: "❌" },
	"Disputed":   { bg: "#FDF4FF", color: "#7E22CE", border: "#E9D5FF", icon: "⚠️" },
	"Billed":     { bg: "#F0F9FF", color: "#0369A1", border: "#BAE6FD", icon: "📄" },
	"Paid":       { bg: "#F0FDF4", color: "#15803D", border: "#BBF7D0", icon: "💰" },
};

// ══════════════════════════════════════════════════════════════════
//  PROGRESS STAGES  (5 linear; Cancelled / Disputed are off-track)
// ══════════════════════════════════════════════════════════════════

const AT_STAGES = [
	{ key: "Pending",    label: "Pending",    icon: "⏳" },
	{ key: "In Transit", label: "In Transit", icon: "🚛" },
	{ key: "Delivered",  label: "Delivered",  icon: "✅" },
	{ key: "Billed",     label: "Billed",     icon: "📄" },
	{ key: "Paid",       label: "Paid",       icon: "💰" },
];

// ══════════════════════════════════════════════════════════════════
//  SECTION ICONS
// ══════════════════════════════════════════════════════════════════

const AT_SECTION_ICONS = {
	"trip and relay info": "🚛",
	"trip details":        "🏷️",
	"vehicle and vendor":  "🚗",
	"customer charges":    "💰",
	"vendor freight":      "🏭",
	"duplication":         "🔁",
	"billing and status":  "📄",
	"amazon payment":      "📊",
};

// ══════════════════════════════════════════════════════════════════
//  COMPUTED FIELDS  (auto-calculated, read-only)
// ══════════════════════════════════════════════════════════════════

const AT_COMPUTED_FIELDS = new Set([
	"trip_cost",
	"total_vendor_freight",
	"computed_total_freight",
	"computed_billed_amount",
	"freight_difference",
]);


// ══════════════════════════════════════════════════════════════════
//  FORM EVENTS
// ══════════════════════════════════════════════════════════════════

frappe.ui.form.on("Amazon Trip", {

	// ── Lifecycle ──────────────────────────────────────────────────

	onload(frm) {
		if (frm.is_new() && !frm.doc.trip_coordinator) {
			frappe.call({
				method: "logicore.logicore.doctype.amazon_trip.amazon_trip.get_default_trip_coordinator",
				callback(r) {
					if (r.message) frm.set_value("trip_coordinator", r.message);
				},
			});
		}
	},

	refresh(frm) {
		frm.$wrapper.addClass("tms-trip-form-active");
		configure_trip_date_dmy(frm);

		const combo = at_get_combo(frm.doc.trip_type);
		apply_at_combo(frm, combo);
		style_status(frm);
		// add_action_buttons(frm);  // removed — buttons not needed on form
		render_at_banner(frm, combo);
		render_apply_bill_button(frm);

		setTimeout(() => {
			render_at_section_icons(frm);
			_force_at_readonly_visible(frm);
			apply_at_readonly_style(frm);
			freeze_grid_vr_id(frm);
		}, 300);

		// Grid may render late / re-render after save — re-apply a few times.
		[200, 500, 900, 1400].forEach(ms => setTimeout(() => color_vr_status_rows(frm), ms));

		// Keep rows coloured instantly on every grid re-render (incl. inline edits).
		setTimeout(() => watch_vr_status_grid(frm), 300);

		frm.$wrapper.closest(".page-container")
			.off("page:hide.at")
			.on("page:hide.at", () => {
				$("#at-field-theme").remove();
				$("#at-scoped-vars").remove();
				$("#at-readonly-style").remove();
				$("#at-grid-freeze").remove();
				if (frm._at_vr_observer) {
					frm._at_vr_observer.disconnect();
					frm._at_vr_observer = null;
				}
			});
	},

	trip_type(frm) {
		const combo = at_get_combo(frm.doc.trip_type);
		apply_at_combo(frm, combo);
		render_at_banner(frm, combo);
		setTimeout(() => apply_at_readonly_style(frm), 100);
	},

	// ── Vendor auto-fill from Vehicle's Company default supplier ──
	vehicle_id(frm) {
		if (!frm.doc.vehicle_id) {
			frm.set_value("vendor", "");
			return;
		}
		frm.set_value("vehicle_id_market", "");
		frappe.call({
			method: "logicore.logicore.doctype.amazon_trip.amazon_trip.get_default_vendor_for_vehicle",
			args: { vehicle_id: frm.doc.vehicle_id },
			callback(r) {
				frm.set_value("vendor", r.message || "");
			}
		});
		if (frm.doc.trip_type === "SCHEDULED TRIP") {
			fetch_last_trip_end_km(frm, { vehicle_id: frm.doc.vehicle_id });
		}
	},

	// ── Market vehicle: only enforce mutual exclusivity, no Start KM auto-fill ──
	vehicle_id_market(frm) {
		if (!frm.doc.vehicle_id_market) return;
		frm.set_value("vehicle_id", "");
		// Start KM auto-fill is intentionally NOT done for Market vehicles —
		// fetch_last_trip_end_km(frm, { vehicle_id_market: frm.doc.vehicle_id_market });
	},

	start_km(frm) { validate_km(frm); calc_total_km(frm); },
	end_km(frm)   { validate_km(frm); calc_total_km(frm); },

	validate(frm) {
		if (flt(frm.doc.start_km) && flt(frm.doc.end_km) && flt(frm.doc.end_km) < flt(frm.doc.start_km)) {
			frappe.msgprint({ title: __("KM Validation Error"), message: __("End KM cannot be less than Start KM."), indicator: "red" });
			frappe.validated = false;
		}
	},



	after_save(frm) {
		const combo = at_get_combo(frm.doc.trip_type);
		render_at_banner(frm, combo);
		_force_at_readonly_visible(frm);
	},

	// ── Tour ID live uniqueness check ─────────────────────────────

	tour_id_relay(frm) {
		const tour_id = (frm.doc.tour_id_relay || "").trim();
		const $input = frm.fields_dict.tour_id_relay
			&& frm.fields_dict.tour_id_relay.$wrapper
			&& frm.fields_dict.tour_id_relay.$wrapper.find("input.form-control");

		if (!tour_id) {
			if ($input && $input.length) $input.css({ "border-color": "", "background-color": "" });
			return;
		}

		frappe.call({
			method: "logicore.logicore.doctype.amazon_trip.amazon_trip.check_tour_id_unique",
			args: {
				tour_id_relay: tour_id,
				current_name: frm.doc.name || "",
			},
			callback(r) {
				if (!r.message) return;
				if (r.message.exists) {
					if ($input && $input.length) {
						$input.css({ "border-color": "#FF5A5A", "background-color": "#FFF0F0" });
					}
					frappe.show_alert({
						message: `Tour ID <b>${frappe.utils.escape_html(tour_id)}</b> is already used by Amazon Trip <b>${frappe.utils.escape_html(r.message.trip)}</b>. Please use a unique Tour ID.`,
						indicator: "red",
					}, 8);
				} else {
					if ($input && $input.length) {
						$input.css({ "border-color": "", "background-color": "" });
					}
				}
			},
		});
	},

	// ── Trip Cost (instant calc) ──────────────────────────────────

	freight(frm)                    { calc_trip_cost(frm); },
	fuel_surcharge_manual(frm)      { calc_trip_cost(frm); },
	cancellation_charge_manual(frm) { calc_trip_cost(frm); },
	detention_charge_manual(frm)    { calc_trip_cost(frm); },
	ot_cost_manual(frm)             { calc_trip_cost(frm); },
	extra_distance_cost_manual(frm) { calc_trip_cost(frm); },
	toll_parking_charges_manual(frm){ calc_trip_cost(frm); },

	// ── Vendor Freight (instant calc) ─────────────────────────────

	vendor_freight(frm)       { calc_vendor_freight(frm); },
	vendor_freight_extra(frm) { calc_vendor_freight(frm); },

	// ── Trip Status triggers — disabled (user sets manually) ─────────
	// vr_cancellation_date_time_utc(frm) { update_trip_status(frm); },
	// original_sadashiv_bill_no(frm)     { update_trip_status(frm); },
	// start_date(frm)                    { update_trip_status(frm); },
	// end_date(frm)                      { update_trip_status(frm); },

	// Re-style whenever status changes
	trip_status(frm) {
		const s    = frm.doc.trip_status || "Pending";
		const conf = TRIP_STATUS_CONFIG[s] || TRIP_STATUS_CONFIG["Pending"];
		// Live-update banner pill — same pattern as trip.js trip_status handler
		$(".tms-bstatus").css({
			background:     hex_alpha(conf.color, 0.18),
			color:          conf.color,
			"border-color": hex_alpha(conf.color, 0.45),
		});
		$(".tms-status-dot").css({
			background:   conf.color,
			"box-shadow": `0 0 6px ${conf.color}`,
		});
		$(".tms-banner-status-text").text(`${conf.icon} ${s}`);
		style_status(frm);
	},
});

function configure_trip_date_dmy(frm) {
	const control = frm.fields_dict.trip_date;
	if (!control || control._at_dmy_configured) return;

	control._at_dmy_configured = true;
	control.format_for_input = (value) => value
		? moment(value, "YYYY-MM-DD", true).format("DD-MM-YYYY")
		: "";
	control.parse = (value) => {
		if (!value) return "";
		// Already in storage format
		if (moment(value, "YYYY-MM-DD", true).isValid()) return value;
		// Our custom DD-MM-YYYY numeric format
		const parsed = moment(value, "DD-MM-YYYY", true);
		if (parsed.isValid()) return parsed.format("YYYY-MM-DD");
		// Frappe system date format (e.g. "30-June-2026", "30-Jun-2026")
		try {
			const sys = frappe.datetime.user_to_str(value);
			if (sys && moment(sys, "YYYY-MM-DD", true).isValid()) return sys;
		} catch(e) {}
		// Fallback: month-name variants
		const fallback = moment(value, ["DD-MMMM-YYYY", "D-MMMM-YYYY", "DD-MMM-YYYY", "D-MMM-YYYY"], true);
		return fallback.isValid() ? fallback.format("YYYY-MM-DD") : "";
	};

	if (control.datepicker) {
		control.datepicker.update("dateFormat", "dd-mm-yyyy");
	}
	control.refresh();
}

// ══════════════════════════════════════════════════════════════════
//  COLOR UTILITIES  — identical to trip.js
// ══════════════════════════════════════════════════════════════════

function hex_to_rgb(hex) {
	const h = hex.trim().replace("#", "");
	return [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
}

function hex_alpha(hex, a) {
	try   { const [r,g,b] = hex_to_rgb(hex); return `rgba(${r},${g},${b},${a})`; }
	catch { return hex; }
}

function darken(hex, amt) {
	try {
		const [r,g,b] = hex_to_rgb(hex);
		const d = v => Math.max(0, v - amt).toString(16).padStart(2, "0");
		return `#${d(r)}${d(g)}${d(b)}`;
	} catch { return hex; }
}

function get_luminance(hex) {
	try {
		const [r,g,b] = hex_to_rgb(hex).map(v => {
			v /= 255;
			return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
		});
		return 0.2126*r + 0.7152*g + 0.0722*b;
	} catch { return 0; }
}

// ══════════════════════════════════════════════════════════════════
//  THEME — apply_at_combo  (same structure as trip.js apply_combo)
// ══════════════════════════════════════════════════════════════════

function apply_at_combo(frm, combo) {
	if (!combo) combo = AT_COMBO;

	const uid = "at-form-" + (frm.doc.name || "new").replace(/[^a-zA-Z0-9]/g, "_");
	frm.$wrapper.attr("data-at-id", uid);
	const sel = `[data-at-id="${uid}"]`;

	// ── Scoped field-theme CSS ────────────────────────────────────
	const fieldTheme = `

/* ── BASE STATE — size matches Trip UI screenshot (height + padding) */
${sel} input.form-control:not([disabled]):not([readonly]),
${sel} select.form-control:not([disabled]),
${sel} textarea.form-control:not([disabled]) {
	background-color: ${combo.field_bg} !important;
	border-color:     ${combo.field_border} !important;
	color:            ${combo.heading_color} !important;
	height:           36px !important;
	min-height:       36px !important;
	padding:          8px 10px !important;
	font-size:        13px !important;
	line-height:      1.4 !important;
	transition:
		background-color 0.18s ease,
		border-color     0.18s ease,
		box-shadow       0.18s ease !important;
}

/* ── TEXTAREA — allow natural height growth */
${sel} textarea.form-control:not([disabled]) {
	height:     auto !important;
	min-height: 80px !important;
}

/* ── LABELS — uppercase small bold matching Trip */
${sel} .frappe-control .control-label,
${sel} label.control-label {
	color:          ${combo.label_color} !important;
	font-size:      11px !important;
	font-weight:    700 !important;
	letter-spacing: 0.06em !important;
	text-transform: uppercase !important;
	transition:     color 0.15s ease !important;
}

/* ── FOCUS ───────────────────────────────────────────────────── */
${sel} input.form-control:not([disabled]):not([readonly]):focus,
${sel} select.form-control:not([disabled]):focus,
${sel} textarea.form-control:not([disabled]):focus {
	background-color: ${hex_alpha(combo.primary, 0.05)} !important;
	border-color:     ${combo.primary} !important;
	box-shadow:
		0 0 0 3px ${hex_alpha(combo.primary, 0.20)},
		0 0 0 6px ${hex_alpha(combo.primary, 0.07)} !important;
	outline: none !important;
}

/* ── FOCUS label ─────────────────────────────────────────────── */
${sel} .frappe-control:focus-within .control-label,
${sel} .frappe-control:focus-within label.control-label {
	color:       ${combo.primary} !important;
	font-weight: 700 !important;
}

/* ── SECTION HEADS ───────────────────────────────────────────── */
${sel} .form-section .section-head,
${sel} .form-section-heading {
	color:        ${combo.heading_color} !important;
	border-color: ${combo.section_border} !important;
}

/* ── COMPUTED / READ-ONLY ────────────────────────────────────── */
${sel} .like-disabled-input {
	background-color: ${combo.field_bg} !important;
	border-color:     ${combo.field_border} !important;
	color:            ${combo.label_color} !important;
	padding:          8px 10px !important;
	font-size:        13px !important;
	line-height:      1.4 !important;
	min-height:       36px !important;
	height:           36px !important;
	box-sizing:       border-box !important;
}

/* ── KILL hidden ghost input space inside currency wrappers ──── */
${sel} .tms-computed-field .control-input .input-with-feedback,
${sel} .tms-computed-field .control-input input {
	display:    none !important;
	height:     0 !important;
	min-height: 0 !important;
	padding:    0 !important;
	margin:     0 !important;
	border:     none !important;
	overflow:   hidden !important;
}

/* ── CONTROL-INPUT wrapper — no extra padding when computed ──── */
${sel} .tms-computed-field .control-input {
	padding:    0 !important;
	min-height: 0 !important;
}
`;
	_inject_at_style("at-field-theme", fieldTheme);

	// ── CSS custom properties — same set as trip.js ───────────────
	const el = frm.$wrapper[0];
	if (el) {
		el.style.setProperty("--tms-primary",          combo.primary);
		el.style.setProperty("--tms-accent",           combo.accent);
		el.style.setProperty("--tms-page-bg",          combo.page_bg);
		el.style.setProperty("--tms-card-bg",          combo.card_bg);
		el.style.setProperty("--tms-section-border",   combo.section_border);
		el.style.setProperty("--tms-field-bg",         combo.field_bg);
		el.style.setProperty("--tms-field-border",     combo.field_border);
		el.style.setProperty("--tms-label-color",      combo.label_color);
		el.style.setProperty("--tms-heading-color",    combo.heading_color);
		el.style.setProperty("--tms-radius",           combo.radius);
		el.style.setProperty("--tms-primary-light",    hex_alpha(combo.primary, 0.10));
		el.style.setProperty("--tms-primary-border",   hex_alpha(combo.primary, 0.28));
		el.style.setProperty("--tms-field-focus-glow", hex_alpha(combo.primary, 0.12));
	}
}

// ══════════════════════════════════════════════════════════════════
//  READ-ONLY FIELD HIGHLIGHT  — red bg/border for all read_only fields
// ══════════════════════════════════════════════════════════════════

const AT_READONLY_FIELDS = [
	"facility_sequence", "cpt", "is_cpt_truck", "cr_id", "shipper_accounts", "estimated_cost",
	"tender_status", "trip_cost", "total_vendor_freight", "computed_total_freight",
	"computed_billed_amount", "freight_difference", "duplicate_trips", "duplicate_record_no",
	"vr_cancellation_date_time_utc", "transit_operator_type", "spot_work",
];

function apply_at_readonly_style(frm) {
	const uid = frm.$wrapper.attr("data-at-id");
	if (!uid) return;
	const sel = `[data-at-id="${uid}"]`;

	const roSelectors = AT_READONLY_FIELDS.map(f =>
		`${sel} [data-fieldname="${f}"] .like-disabled-input,` +
		`${sel} [data-fieldname="${f}"] input.form-control[readonly],` +
		`${sel} [data-fieldname="${f}"] select.form-control[disabled]`
	).join(",\n");

	const css = `
${roSelectors} {
	background-color: #FFF0F0 !important;
	border-color:     #FFAAAA !important;
	color:            #CC0000 !important;
}
${AT_READONLY_FIELDS.map(f =>
	`${sel} [data-fieldname="${f}"] .control-label,` +
	`${sel} [data-fieldname="${f}"] label.control-label`
).join(",\n")} {
	color: #CC0000 !important;
}
`;
	_inject_at_style("at-readonly-style", css);
}

function _inject_at_style(id, css) {
	let $el = $(`#${id}`);
	if (!$el.length) $el = $(`<style id="${id}"></style>`).appendTo("head");
	$el.text(css);
}

// ══════════════════════════════════════════════════════════════════
//  BANNER — mirrors trip.js render_banner exactly
//  • darken(primary, 42) for gradient start
//  • hex_alpha for status pill bg + border
//  • get_luminance for text contrast logic
// ══════════════════════════════════════════════════════════════════

function _get_at_stage_idx(frm) {
	const s   = frm.doc.trip_status || "Pending";
	const idx = AT_STAGES.findIndex(st => st.key === s);
	return idx >= 0 ? idx : 0;   // Cancelled / Disputed stay at 0
}

function render_at_banner(frm, combo) {
	$(".at-trip-banner").remove();
	if (!combo) combo = AT_COMBO;

	const stageIdx = _get_at_stage_idx(frm);
	const curStage = AT_STAGES[stageIdx];
	const status   = frm.doc.trip_status || "Pending";
	const conf     = TRIP_STATUS_CONFIG[status] || TRIP_STATUS_CONFIG["Pending"];
	const soNo     = frm.is_new() ? "New Amazon Trip" : (frm.doc.name || "");
	const tourR    = frm.doc.tour_id_relay  || "—";
	const tourA    = frm.doc.tour_id_amazon || "—";
	const sColor   = conf.color;

	// darken(primary, 42) — exact same as trip.js render_banner
	const gradStart = darken(combo.primary, 42);

	const dotsHtml = AT_STAGES.map((_, i) => {
		const cls = i < stageIdx ? "tms-dot-done"
			: i === stageIdx    ? "tms-dot-current"
			:                     "tms-dot-pending";
		return `<span class="tms-dot ${cls}"></span>`;
	}).join("");

	const html = `
	<div class="at-trip-banner tms-trip-banner"
		style="background: linear-gradient(135deg, ${gradStart} 0%, ${combo.primary} 100%);">
		<div class="tms-bid">
			<span class="tms-bid-icon">🚛</span>
			<span class="tms-bid-sono tms-banner-sono">${frappe.utils.escape_html(soNo)}</span>
			<span class="tms-bid-route">📡 ${frappe.utils.escape_html(tourR)}</span>
			<span class="tms-bid-route">🛒 ${frappe.utils.escape_html(tourA)}</span>
		</div>
		<div class="tms-bprogress">
			<div class="tms-dots">${dotsHtml}</div>
			<span class="tms-bstage">${curStage.icon} ${curStage.label}</span>
		</div>
		<div class="tms-bstatus"
			style="background:${hex_alpha(sColor, 0.18)};color:${sColor};border-color:${hex_alpha(sColor, 0.45)};">
			<span class="tms-status-dot"
				style="background:${sColor};box-shadow:0 0 6px ${sColor};"></span>
			<span class="tms-banner-status-text">${conf.icon} ${frappe.utils.escape_html(status)}</span>
		</div>
	</div>`;

	const $t = frm.$wrapper.find(".form-page, .form-layout, .frappe-card").first();
	($t.length ? $t : frm.$wrapper).prepend(html);
}

// ══════════════════════════════════════════════════════════════════
//  SECTION ICONS
// ══════════════════════════════════════════════════════════════════

function render_at_section_icons(frm) {
	frm.$wrapper.find(".form-section .section-head, .section-head").each(function () {
		const $h = $(this);
		if ($h.find(".tms-sec-icon").length) return;
		const text = ($h.text() || "").toLowerCase().trim();
		const entry = Object.entries(AT_SECTION_ICONS).find(([k]) => text.includes(k));
		if (entry) $h.prepend(`<span class="tms-sec-icon">${entry[1]}</span>`);
	});
}

// ══════════════════════════════════════════════════════════════════
//  COMPUTED FIELD BADGES  (⚙ Auto + tms-computed-field class)
// ══════════════════════════════════════════════════════════════════

function _force_at_readonly_visible(frm) {
	_do_force_at(frm);
	setTimeout(() => _do_force_at(frm), 150);
	setTimeout(() => _do_force_at(frm), 450);
	setTimeout(() => _do_force_at(frm), 800);
}

function _do_force_at(frm) {
	AT_COMPUTED_FIELDS.forEach(f => {
		const fd = frm.fields_dict[f];
		if (!fd || !fd.$wrapper) return;

		const val   = frm.doc[f];
		const empty = (val === null || val === undefined || val === "");

		fd.$wrapper
			.addClass("tms-computed-field")
			.removeClass("hidden-control")
			.css({ display: "block", visibility: "visible", opacity: "1" });

		if (!fd.$wrapper.find(".tms-auto-badge").length)
			fd.$wrapper.append('<span class="tms-auto-badge">⚙ Auto</span>');

		// Fully collapse hidden native input — display:none so it takes zero space
		fd.$wrapper.find(".control-input .input-with-feedback, .control-input input")
			.css({ display: "none", height: "0", minHeight: "0", padding: "0", margin: "0", border: "none", overflow: "hidden" });

		const $disp = fd.$wrapper.find(".like-disabled-input");
		if ($disp.length) {
			const isFreightDiff = (f === "freight_difference");
			const num           = parseFloat(val) || 0;
			const isNegative    = isFreightDiff && num < 0;

			$disp.css({
				display:            "block",
				height:             "36px",
				minHeight:          "36px",
				padding:            "8px 10px",
				fontSize:           "13px",
				lineHeight:         "1.4",
				boxSizing:          "border-box",
				opacity:            "1",
				color:              isNegative ? "#CC0000" : "",
				"background-color": isNegative ? "#FFF0F0" : "",
				"border-color":     isNegative ? "#FFAAAA" : "",
				"font-weight":      isNegative ? "700"     : "",
			});

			if (empty) {
				$disp.text("₹ —");
			} else if (isFreightDiff) {
				const sign = num < 0 ? "(-) " : "";
				$disp.text(sign + "₹ " + Math.abs(num).toLocaleString("en-IN", { maximumFractionDigits: 2 }));
			} else {
				$disp.text("₹\u00A0" + Math.abs(num).toLocaleString("en-IN", { maximumFractionDigits: 2 }));
			}
		}
	});
}

// ══════════════════════════════════════════════════════════════════
//  TAB INDICATOR DOTS — same as trip.js highlight_active_tab
// ══════════════════════════════════════════════════════════════════

function highlight_at_tab(frm) {
	frm.$wrapper.find(".form-tabs-list .nav-link").each(function () {
		const $tab = $(this);
		if ($tab.find(".tms-stage-dot").length) return;
		$tab.append('<span class="tms-stage-dot" title="Active section"></span>');
	});
}

// ══════════════════════════════════════════════════════════════════
//  CALCULATIONS
// ══════════════════════════════════════════════════════════════════

function calc_trip_cost(frm) {
	const total = flt(frm.doc.freight)
		+ flt(frm.doc.fuel_surcharge_manual)
		+ flt(frm.doc.cancellation_charge_manual)
		+ flt(frm.doc.detention_charge_manual)
		+ flt(frm.doc.ot_cost_manual)
		+ flt(frm.doc.extra_distance_cost_manual)
		+ flt(frm.doc.toll_parking_charges_manual);
	frm.set_value("trip_cost", total);
	// computed_total_freight = trip_cost (live update)
	frm.set_value("computed_total_freight", total);
	frm.set_value("freight_difference", flt(frm.doc.computed_billed_amount) - total);
}

function calc_vendor_freight(frm) {
	const total = flt(frm.doc.vendor_freight) + flt(frm.doc.vendor_freight_extra);
	frm.set_value("total_vendor_freight", total);
}

// ══════════════════════════════════════════════════════════════════
//  SCHEDULED TRIP KM — Start KM auto-fill + Total KM calc
// ══════════════════════════════════════════════════════════════════

function fetch_last_trip_end_km(frm, args) {
	frappe.call({
		method: "logicore.logicore.doctype.amazon_trip.amazon_trip.get_vehicle_last_trip_end_km",
		args: { ...args, trip_name: frm.doc.name },
		callback(r) {
			if (r.message) {
				frm.set_value("start_km", r.message);
				frappe.show_alert({ message: __("Start KM set from last trip end KM: {0}", [r.message]), indicator: "blue" }, 4);
			} else {
				frappe.show_alert({ message: __("No previous Amazon Trip found for this vehicle, so Start KM could not be fetched."), indicator: "orange" }, 6);
			}
		}
	});
}

function validate_km(frm) {
	if (flt(frm.doc.start_km) && flt(frm.doc.end_km) && flt(frm.doc.end_km) < flt(frm.doc.start_km))
		frappe.show_alert({ message: __("End KM cannot be less than Start KM."), indicator: "orange" }, 5);
}

function calc_total_km(frm) {
	frm.set_value("total_km", flt(frm.doc.end_km) - flt(frm.doc.start_km));
}

// ══════════════════════════════════════════════════════════════════
//  TRIP STATUS (client-side mirror of server logic)
// ══════════════════════════════════════════════════════════════════

function update_trip_status(frm) {
	// Never overwrite Cancelled once set
	if (frm.doc.trip_status === "Cancelled" && !!frm.doc.vr_cancellation_date_time_utc) return;

	frappe.call({
		method: "logicore.logicore.doctype.amazon_trip.amazon_trip.get_trip_status_preview",
		args: {
			vr_cancellation_date_time_utc: frm.doc.vr_cancellation_date_time_utc || null,
			original_sadashiv_bill_no:     frm.doc.original_sadashiv_bill_no     || null,
			start_date:                    frm.doc.start_date                    || null,
			end_date:                      frm.doc.end_date                      || null,
			current_status:                frm.doc.trip_status                   || null,
		},
		callback(r) {
			if (r.message && r.message !== frm.doc.trip_status) {
				frm.set_value("trip_status", r.message);
				style_status(frm);
				render_at_banner(frm, AT_COMBO);
			}
		},
	});
}

// ══════════════════════════════════════════════════════════════════
//  STATUS BADGE STYLING — uses hex_alpha like trip.js
// ══════════════════════════════════════════════════════════════════

function style_status(frm) {
	const s    = frm.doc.trip_status || "Pending";
	const conf = TRIP_STATUS_CONFIG[s] || TRIP_STATUS_CONFIG["Pending"];

	setTimeout(() => {
		const $field = frm.$wrapper.find('[data-fieldname="trip_status"]');
		$field.find(".like-disabled-input, .form-control").css({
			"background":     conf.bg,
			"color":          conf.color,
			"border-color":   conf.border,
			"font-weight":    "800",
			"border-radius":  "20px",
			"padding":        "4px 14px",
			"font-size":      "12px",
			"letter-spacing": ".04em",
		});
	}, 80);
}

// ══════════════════════════════════════════════════════════════════
//  ACTION BUTTONS
// ══════════════════════════════════════════════════════════════════

function add_action_buttons(frm) {
	if (!frm.is_new()) {
		frm.add_custom_button(__("✅ APPLY ALL Entries"), () => {
			frappe.confirm(
				"Apply all billing entries for this Amazon Trip record?",
				() => {
					calc_trip_cost(frm);
					calc_vendor_freight(frm);
					frm.save().then(() => {
						frappe.show_alert({ message: "✅ All entries applied and saved.", indicator: "green" }, 4);
					});
				}
			);
		});
	}

	if (frappe.user_roles.includes("System Manager") && !frm.is_new()) {
		frm.add_custom_button(__("🔄 Recalculate All Statuses"), () => {
			frappe.confirm(
				"Re-compute Trip Status for <b>all pending Amazon Trip records</b>? This may take a moment.",
				() => {
					frappe.call({
						method: "logicore.logicore.doctype.amazon_trip.amazon_trip.bulk_update_status",
						freeze: true,
						freeze_message: "Recalculating statuses…",
						callback(r) {
							if (r.message) {
								frappe.show_alert({
									message: `✅ Updated ${r.message.updated} of ${r.message.total} records.`,
									indicator: "green",
								}, 5);
							}
						},
					});
				}
			);
		}, __("Tools"));
	}
}


// ══════════════════════════════════════════════════════════════════
//  APPLY BILL BUTTON — copies Bill No + Bill Date to all grid rows
// ══════════════════════════════════════════════════════════════════

function render_apply_bill_button(frm) {
	const fd = frm.fields_dict.apply_bill_btn_html;
	if (!fd) return;
	fd.$wrapper.html(`
<div style="margin-top:21px;">
	<button class="btn at-apply-bill-btn" style="
		background:linear-gradient(135deg,#3B4FE4 0%,#06B6D4 100%);
		color:#fff;font-weight:700;font-size:13px;border:none;
		border-radius:8px;padding:10px 20px;width:100%;cursor:pointer;
		letter-spacing:0.04em;box-shadow:0 4px 14px rgba(59,79,228,0.35);
		transition:all 0.2s ease;">
		📋 Apply to all VR ID Entries
	</button>
</div>`);
	fd.$wrapper.find(".at-apply-bill-btn")
		.on("click", () => apply_bill_to_grid(frm))
		.on("mouseenter", function () { $(this).css({"transform":"translateY(-2px)","box-shadow":"0 8px 20px rgba(59,79,228,0.45)"}); })
		.on("mouseleave", function () { $(this).css({"transform":"translateY(0)","box-shadow":"0 4px 14px rgba(59,79,228,0.35)"}); });
}

function apply_bill_to_grid(frm) {
	const bill_no   = frm.doc.original_sadashiv_bill_no;
	const bill_date = frm.doc.original_bill_date;

	if (!bill_no && !bill_date) {
		frappe.show_alert({ message: "Please enter Bill No or Bill Date first.", indicator: "orange" }, 4);
		return;
	}

	const rows = frm.doc.amazon_trip_details || [];
	if (!rows.length) {
		frappe.show_alert({ message: "No rows found in Amazon Payment Data grid.", indicator: "orange" }, 4);
		return;
	}

	rows.forEach(row => {
		if (bill_no)   frappe.model.set_value(row.doctype, row.name, "original_sadashiv_bill_no", bill_no);
		if (bill_date) frappe.model.set_value(row.doctype, row.name, "original_bill_date",        bill_date);
	});

	frm.refresh_field("amazon_trip_details");

	frappe.show_alert({
		message: `Bill No & Date applied to ${rows.length} row${rows.length > 1 ? "s" : ""} successfully.`,
		indicator: "green",
	}, 5);
}

// ══════════════════════════════════════════════════════════════════
//  FREEZE VR ID COLUMN in child table grid
// ══════════════════════════════════════════════════════════════════

function freeze_grid_vr_id(frm) {
	const g = `.frappe-control[data-fieldname="amazon_trip_details"]`;

	const apply_freeze = () => {
		const $grid = frm.$wrapper.find('[data-fieldname="amazon_trip_details"]');
		if (!$grid.length) return;

		const chkW = $grid.find('.grid-heading-row .col.row-check').outerWidth() || 28;
		const noW  = $grid.find('.grid-heading-row .col.row-index').outerWidth()  || 50;

		const noLeft = chkW;
		const vrLeft = chkW + noW;

		const HDR_BG = "#f4f5f6";
		const ROW_BG = "#ffffff";
		const HOV_BG = "#f0f4ff";
		const SEL_BG = "#e8eeff";

		const css = `
${g} .grid-heading-row .col.row-check,
${g} .rows .grid-row .col.row-check {
	position:sticky!important;left:0!important;z-index:5!important;
	background-color:${HDR_BG}!important;
}
${g} .grid-heading-row .col.row-index {
	position:sticky!important;left:${noLeft}px!important;z-index:5!important;
	background-color:${HDR_BG}!important;
}
${g} .rows .grid-row .col.row-index {
	position:sticky!important;left:${noLeft}px!important;z-index:4!important;
	background-color:${ROW_BG}!important;
}
${g} .grid-heading-row [data-fieldname="vr_id"] {
	position:sticky!important;left:${vrLeft}px!important;z-index:5!important;
	background-color:${HDR_BG}!important;
	box-shadow:3px 0 6px rgba(0,0,0,0.12)!important;
}
${g} .rows .grid-row .col[data-fieldname="vr_id"] {
	position:sticky!important;left:${vrLeft}px!important;z-index:4!important;
	background-color:${ROW_BG}!important;
	box-shadow:3px 0 6px rgba(0,0,0,0.08)!important;
}
${g} .rows .grid-row:hover .col[data-fieldname="vr_id"] {
	background-color:${HOV_BG}!important;
}
${g} .rows .grid-row.grid-row-open .col[data-fieldname="vr_id"],
${g} .rows .grid-row.selected .col[data-fieldname="vr_id"] {
	background-color:${SEL_BG}!important;
}`;
		_inject_at_style("at-grid-freeze", css);
	};

	apply_freeze();
	setTimeout(apply_freeze, 600);
}

// ══════════════════════════════════════════════════════════════════
//  VR STATUS ROW COLOR — Cancelled=red, Dummy=orange in child grid
// ══════════════════════════════════════════════════════════════════

// One-time stylesheet — survives grid re-renders (scroll, pagination, add/remove row).
function _inject_vr_status_style() {
	if (document.getElementById("at-vr-status-style")) return;
	const css = `
.grid-row.at-vr-cancelled, .grid-row.at-vr-cancelled .data-row {
	background-color: #FFC7CE !important;
}
.grid-row.at-vr-cancelled .data-row .grid-static-col,
.grid-row.at-vr-cancelled .static-area { color: #9C0006 !important; font-weight: 600 !important; }
.grid-row.at-vr-cancelled { box-shadow: inset 4px 0 0 #FF6B6B !important; }

.grid-row.at-vr-dummy, .grid-row.at-vr-dummy .data-row {
	background-color: #FFEB9C !important;
}
.grid-row.at-vr-dummy .data-row .grid-static-col,
.grid-row.at-vr-dummy .static-area { color: #9C5700 !important; font-weight: 600 !important; }
.grid-row.at-vr-dummy { box-shadow: inset 4px 0 0 #FFC000 !important; }
`;
	const el = document.createElement("style");
	el.id = "at-vr-status-style";
	el.textContent = css;
	document.head.appendChild(el);
}

function color_vr_status_rows(frm) {
	const grid_field = frm.fields_dict.amazon_trip_details;
	if (!grid_field || !grid_field.grid) return;

	_inject_vr_status_style();

	const grid_rows = grid_field.grid.grid_rows || [];
	grid_rows.forEach(row_obj => {
		if (!row_obj) return;
		const status   = row_obj.doc && row_obj.doc.vr_status;
		const $wrapper = row_obj.wrapper;
		if (!$wrapper || !$wrapper.length) return;

		$wrapper.removeClass("at-vr-cancelled at-vr-dummy");
		if (status === "Cancelled") $wrapper.addClass("at-vr-cancelled");
		else if (status === "Dummy") $wrapper.addClass("at-vr-dummy");
	});
}

// Watch the grid DOM so a row gets (re-)coloured the instant it re-renders —
// e.g. the moment a VR Status Select is changed, before any save. We observe
// childList/subtree only (not attributes), so toggling classes won't re-trigger.
function watch_vr_status_grid(frm) {
	const grid_field = frm.fields_dict.amazon_trip_details;
	if (!grid_field || !grid_field.grid || !grid_field.grid.wrapper) return;

	const target = grid_field.grid.wrapper.get(0);
	if (!target) return;

	// Re-attach if the grid wrapper was recreated; skip if already watching this node.
	if (frm._at_vr_observer) {
		if (frm._at_vr_observer._target === target) return;
		frm._at_vr_observer.disconnect();
	}

	let scheduled = false;
	const observer = new MutationObserver(() => {
		if (scheduled) return;
		scheduled = true;
		requestAnimationFrame(() => {
			scheduled = false;
			color_vr_status_rows(frm);
		});
	});
	observer._target = target;
	observer.observe(target, { childList: true, subtree: true });
	frm._at_vr_observer = observer;
}

frappe.ui.form.on("Amazon Trip Detail", {
	vr_status(frm, cdt, cdn) {
		// Instant feedback on select — colour right away; the grid observer
		// re-applies if a later re-render drops the class.
		color_vr_status_rows(frm);
	},
	form_render(frm, cdt, cdn) {
		// fires when a grid row expand/collapse re-renders
		setTimeout(() => color_vr_status_rows(frm), 50);
	},
});

// ══════════════════════════════════════════════════════════════════
//  UTILITIES
// ══════════════════════════════════════════════════════════════════

function flt(v) { return parseFloat(v) || 0; }
