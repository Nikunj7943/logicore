const TRIP_TYPE_META = {
	"Primary": { code: "P", label: "Primary", icon: "🚛" },
	"RCPL Primary": { code: "R", label: "RCPL", icon: "🔄" },
	"Secondary Dedicated": { code: "D", label: "Dedicated", icon: "📦" },
	"Secondary Market": { code: "M", label: "Market", icon: "🏪" },
	"Other": { code: "O", label: "Other", icon: "🔧" },
};

const COMBOS = {
	"Primary": [
		{ name: "Ocean Command", page_bg: "#EEF2FF", card_bg: "#FFFFFF", section_border: "#C7D7FF", field_bg: "#F0F4FF", field_border: "#A5B4FC", primary: "#3B4FE4", accent: "#06B6D4", label_color: "#3730A3", heading_color: "#1E1B4B", radius: "10px" },
		{ name: "Steel Authority", page_bg: "#F0F4F8", card_bg: "#FFFFFF", section_border: "#CBD5E1", field_bg: "#F8FAFC", field_border: "#94A3B8", primary: "#1E3A5F", accent: "#0EA5E9", label_color: "#334155", heading_color: "#0F172A", radius: "8px" },
		{ name: "Midnight Fleet", page_bg: "#0F172A", card_bg: "#1E293B", section_border: "#334155", field_bg: "#1A2540", field_border: "#475569", primary: "#6366F1", accent: "#22D3EE", label_color: "#94A3B8", heading_color: "#E2E8F0", radius: "10px" },
		{ name: "Arctic Blue", page_bg: "#F0F9FF", card_bg: "#FFFFFF", section_border: "#BAE6FD", field_bg: "#F0F9FF", field_border: "#7DD3FC", primary: "#0369A1", accent: "#0EA5E9", label_color: "#075985", heading_color: "#0C4A6E", radius: "12px" },
	],
	"RCPL Primary": [
		{ name: "Forest Route", page_bg: "#F0FDF4", card_bg: "#FFFFFF", section_border: "#BBF7D0", field_bg: "#F0FDF4", field_border: "#86EFAC", primary: "#15803D", accent: "#65A30D", label_color: "#166534", heading_color: "#14532D", radius: "10px" },
		{ name: "Jade Logistics", page_bg: "#ECFDF5", card_bg: "#FFFFFF", section_border: "#A7F3D0", field_bg: "#F0FDF8", field_border: "#6EE7B7", primary: "#047857", accent: "#0D9488", label_color: "#065F46", heading_color: "#022C22", radius: "8px" },
		{ name: "Sage Enterprise", page_bg: "#F7FEE7", card_bg: "#FFFFFF", section_border: "#D9F99D", field_bg: "#F7FEE7", field_border: "#BEF264", primary: "#4D7C0F", accent: "#16A34A", label_color: "#3F6212", heading_color: "#1A2E05", radius: "12px" },
		{ name: "Emerald Night", page_bg: "#052E16", card_bg: "#14532D", section_border: "#166534", field_bg: "#0D3321", field_border: "#15803D", primary: "#22C55E", accent: "#86EFAC", label_color: "#86EFAC", heading_color: "#DCFCE7", radius: "10px" },
	],
	"Secondary Dedicated": [
		{ name: "Amber Cargo", page_bg: "#FFF7ED", card_bg: "#FFFFFF", section_border: "#FED7AA", field_bg: "#FFFBF5", field_border: "#FDBA74", primary: "#EA580C", accent: "#D97706", label_color: "#9A3412", heading_color: "#7C2D12", radius: "12px" },
		{ name: "Sunset Dispatch", page_bg: "#FEF9EE", card_bg: "#FFFFFF", section_border: "#FDE68A", field_bg: "#FFFDF0", field_border: "#FCD34D", primary: "#B45309", accent: "#F59E0B", label_color: "#92400E", heading_color: "#451A03", radius: "10px" },
		{ name: "Copper Line", page_bg: "#FFF8F1", card_bg: "#FFFFFF", section_border: "#FBBF24", field_bg: "#FFFBF5", field_border: "#F59E0B", primary: "#C2410C", accent: "#EA580C", label_color: "#9A3412", heading_color: "#431407", radius: "8px" },
		{ name: "Dark Amber", page_bg: "#1C0A00", card_bg: "#2C1A00", section_border: "#78350F", field_bg: "#1C0F00", field_border: "#92400E", primary: "#F59E0B", accent: "#FCD34D", label_color: "#FCD34D", heading_color: "#FEF3C7", radius: "10px" },
	],

	"Secondary Market": [
		{ name: "Rose Commerce", page_bg: "#FFF1F2", card_bg: "#FFFFFF", section_border: "#FECDD3", field_bg: "#FFF5F7", field_border: "#FDA4AF", primary: "#BE185D", accent: "#EA580C", label_color: "#9D174D", heading_color: "#4C0519", radius: "14px" },
		{ name: "Violet Market", page_bg: "#F5F3FF", card_bg: "#FFFFFF", section_border: "#DDD6FE", field_bg: "#FAF5FF", field_border: "#C4B5FD", primary: "#7C3AED", accent: "#DB2777", label_color: "#5B21B6", heading_color: "#3B0764", radius: "12px" },
		{ name: "Plum Trade", page_bg: "#FDF4FF", card_bg: "#FFFFFF", section_border: "#E9D5FF", field_bg: "#FDF4FF", field_border: "#D8B4FE", primary: "#9333EA", accent: "#C026D3", label_color: "#7E22CE", heading_color: "#3B0764", radius: "10px" },
		{ name: "Magenta Night", page_bg: "#1A0A2E", card_bg: "#2D1B47", section_border: "#4C1D95", field_bg: "#1E0D35", field_border: "#5B21B6", primary: "#C084FC", accent: "#E879F9", label_color: "#D8B4FE", heading_color: "#F3E8FF", radius: "10px" },
	],
	"Other": [
		{ name: "Slate Neutral", page_bg: "#F1F5F9", card_bg: "#FFFFFF", section_border: "#CBD5E1", field_bg: "#F8FAFC", field_border: "#94A3B8", primary: "#475569", accent: "#0284C7", label_color: "#334155", heading_color: "#0F172A", radius: "8px" },
		{ name: "Warm Neutral", page_bg: "#FFFBEB", card_bg: "#FFFFFF", section_border: "#FDE68A", field_bg: "#FFFDF5", field_border: "#FCD34D", primary: "#B45309", accent: "#059669", label_color: "#92400E", heading_color: "#451A03", radius: "10px" },
		{ name: "Teal Operations", page_bg: "#F0FDFA", card_bg: "#FFFFFF", section_border: "#99F6E4", field_bg: "#F0FDFA", field_border: "#5EEAD4", primary: "#0D9488", accent: "#0369A1", label_color: "#0F766E", heading_color: "#042F2E", radius: "10px" },
		{ name: "Carbon Pro", page_bg: "#18181B", card_bg: "#27272A", section_border: "#3F3F46", field_bg: "#1C1C1F", field_border: "#52525B", primary: "#A1A1AA", accent: "#71717A", label_color: "#A1A1AA", heading_color: "#F4F4F5", radius: "6px" },
	],
};

const TMS_STORAGE_KEY = "tms_trip_type_themes";
const DEFAULT_FALLBACK_COMBO = COMBOS["Primary"][0];

const STATUS_COLORS = {
	"Open": "#10B981",
	"Close": "#6366F1",
	"Cancel": "#EF4444",
	"Draft": "#94A3B8",
};

const TRIP_STATUS_STAGES = [
	{ key: "Trip Created", label: "Created", icon: "📋" },
	{ key: "Trip In-Transit", label: "In Transit", icon: "🚛" },
	{ key: "Trip Awaiting Billing", label: "Awaiting Billing", icon: "📄" },
	{ key: "Trip Billed", label: "Billed", icon: "🧾" },
	{ key: "Trip Payment Received", label: "Pmt. Received", icon: "💳" },
	{ key: "Trip Closed", label: "Closed", icon: "✅" },
];

const SECTION_ICONS = {
	"branch": "🏢",
	"route": "🗺️",
	"origin": "📍",
	"destination": "🏁",
	"billing": "💳",
	"vehicle": "🚛",
	"driver": "👤",
	"lr": "📄",
	"loading": "📦",
	"unloading": "📤",
	"detention": "⏱️",
	"additional": "💰",
	"kilometer": "🛣️",
	"vendor freight": "🏭",
	"pod": "📸",
	"approval": "✅",
	"payment": "💵",
	"trip amount": "📊",
	"remarks": "📝",
};

const DATE_DISPLAY_FIELDS = new Set([
	"billing_start_date",
	"billing_end_date",
]);

// ══════════════════════════════════════════════════════════════════
//  FORM EVENTS
// ══════════════════════════════════════════════════════════════════

frappe.ui.form.on("Trip", {

	company(frm) {
		if (!frm.doc.company) return;
		frappe.db.get_value("Company", frm.doc.company, "default_supplier").then((r) => {
			const ds = r && r.message && r.message.default_supplier;
			frm._tms_default_supplier = ds || null;
			if (ds) frm.set_value("vendor", ds);
			apply_vendor_field_lock(frm);
		});
	},

	tcntrip_no(frm) {
		update_tcn_and_format_chip(frm);
	},

	business_format(frm) {
		update_tcn_and_format_chip(frm);
	},

	eway_bill_no(frm) {
		if (!frm.doc.eway_bill_no) return;

		// Ask whether the lookup is switched on before doing anything the user can see.
		// Without this gate the form flashes the "Fetching e-way bill details..." freeze
		// and fires validation alerts even when Eway Bill Settings has it disabled, where
		// this is meant to behave like any other manually typed field. This call is
		// deliberately un-frozen: it is a single indexed read, not the external API.
		frappe.call({
			method: "logicore.logicore.api.is_eway_bill_lookup_enabled",
			args: { company: frm.doc.company || "" },
			callback(r) {
				if (r.message) fetch_eway_bill_details(frm);
			},
		});
	},

	// ── refresh ──────────────────────────────────────────────────────
	refresh(frm) {
		frm.$wrapper.off("click.tms_tabs");
		frm._tms_tab_listener_bound = false;
		frm.$wrapper.addClass("tms-trip-form-active");

		// ── Force Start KM re-fetch when vehicle_no is cleared and the same
		//    value is re-entered — Frappe's own link control skips its change
		//    trigger when the final value equals the previously saved value,
		//    so blanking + re-typing the same vehicle otherwise fetches nothing.
		frm.$wrapper.off("input.tms_vno_clear_track").on(
			"input.tms_vno_clear_track",
			'[data-fieldname="vehicle_no"] input',
			function () {
				if (!this.value) $(this).data("tms_vno_was_cleared", true);
			}
		);
		frm.$wrapper.off("blur.tms_vno_force_fetch").on(
			"blur.tms_vno_force_fetch",
			'[data-fieldname="vehicle_no"] input',
			function () {
				const $el = $(this);
				const was_cleared = $el.data("tms_vno_was_cleared");
				$el.removeData("tms_vno_was_cleared");
				if (was_cleared) fetch_start_km_for_vehicle(frm);
			}
		);

		const combo = get_combo_for_trip(frm.doc.trip_type);
		apply_combo(frm, combo);

		// ── Entry highlight: inject progress bar + update fill dots ──
		tms_inject_progress_bar(frm);
		tms_update_fill_status(frm);
		const _hl_sel = TMS_HL_FIELDS.map(fn =>
			`[data-fieldname="${fn}"] input,[data-fieldname="${fn}"] select`
		).join(",");
		frm.$wrapper.off("change.tms_hl awesomplete-selectcomplete.tms_hl input.tms_hl").on(
			"change.tms_hl awesomplete-selectcomplete.tms_hl input.tms_hl",
			_hl_sel,
			function() {
				// For input events frm.doc is not yet updated — pass live DOM value
				// for the active field so progress bar moves immediately while typing.
				const fn = $(this).closest("[data-fieldname]").attr("data-fieldname");
				tms_update_fill_status(frm, fn, $(this).val());
			}
		);

		// ✅ Render banner immediately with base combo — visibility
		//    function will re-render it once server data arrives
		render_banner(frm, combo);
		_bind_banner_live_listeners(frm);

		setup_so_no_field(frm);
		setup_field_read_only_rules(frm);
		apply_date_sequence_lock(frm);
		fetch_default_supplier_and_lock(frm);
		setup_address_search(frm);
		setup_master_link_filters(frm);
		setup_driver_query(frm);
		setup_vehicle_filter(frm);
		fetch_vendor_tds_and_calc(frm, { apply: false });
		add_custom_buttons(frm);
		_attach_dropdown_fix(frm);

		// ✅ Run section icons + calcs BEFORE visibility async call
		//    so they don't race with the callback
		render_section_icons(frm);
		fetch_vehicle_type_detention_rates(frm);
		setup_vehicle_type_live_clear(frm);
		run_all_calcs_on_load(frm);
		_force_readonly_fields_visible(frm);
		highlight_active_tab(frm);

		// ✅ Call visibility LAST — its callback will update banner/color
		apply_trip_type_visibility(frm);
		setTimeout(() => _fix_other_trip_type_columns(frm), 120);
		

		frm.$wrapper.closest(".page-container").off("page:hide.tms").on("page:hide.tms", function () {
			$("#tms-trip-scoped-vars").remove();
			$("#tms-trip-field-theme").remove();
			$("#tms-color-override").remove();
		});

		frm.$wrapper.closest(".page-container").off("page:show.tms_bf_customer").on("page:show.tms_bf_customer", function () {
			if (frm.is_new() && frm.doc.business_format && !frm.doc.customer) {
				frappe.db.get_value("Business Format", frm.doc.business_format, "default_customer", (r) => {
					if (r && r.default_customer) frm.set_value("customer", r.default_customer);
				});
			}
		});

		if (frm._tms_theme_observer) {
			frm._tms_theme_observer.disconnect();
			frm._tms_theme_observer = null;
		}
		frm._tms_theme_observer = new MutationObserver(() => {
			const combo = get_combo_for_trip(frm.doc.trip_type);
			apply_combo(frm, combo);
			if (frm._tms_resolved_color) {
				apply_trip_color(frm, frm._tms_resolved_color);
			}
		});
		frm._tms_theme_observer.observe(document.documentElement, {
			attributes: true, attributeFilter: ["data-theme-mode"]
		});
		// setup_datetime_no_seconds(frm);
		 _inject_bottom_save_button(frm); 
		
		//  if (frm.doc.trip_type) {
        // frm.set_query("business_format", function () {
        //     return {
        //         filters: {
        //             trip_type: frm.doc.trip_type
        //         }
        //     };
        // });
    //}
		render_vendor_payment_table(frm);
		render_receipt_table(frm);
	},

	// after_save(frm) {
	// 	if (frm.doc.name) {
	// 		frm.doc.so_no = frm.doc.name;
	// 		frm.refresh_field("so_no");
	// 		$(".tms-banner-sono").text(frm.doc.name);
	// 	}
	// 	_force_readonly_fields_visible(frm);
	// 	update_pod_button_label(frm);
	// },
after_save(frm) {
    if (frm.doc.name) {
        frm.doc.so_no = frm.doc.name;
        frm.refresh_field("so_no");
        $(".tms-banner-sono").text(frm.doc.name);
    }
    _force_readonly_fields_visible(frm);
    update_pod_button_label(frm);
    tms_update_fill_status(frm);
    // ── Driver name fix after save/reload ──
	_inject_bottom_save_button(frm);
},

	onload(frm) {
		// Fill default vendor only for NEW trips where vendor is not already set
		const _fill_vendor = () => {
			if (!frm.doc.company || frm.doc.vendor) return;
			frappe.db.get_value("Company", frm.doc.company, "default_supplier").then((r) => {
				const ds = r && r.message && r.message.default_supplier;
				if (ds) frm.set_value("vendor", ds);
			});
		};

		if (!frm.is_new()) {
			return;
		}

		if (!frm.doc.tcntrip_date)
			frm.set_value("tcntrip_date", frappe.datetime.get_today());

		if (!frm.doc.company) {
			const user_company = frappe.defaults.get_user_default("Company");
			if (user_company) {
				frm.set_value("company", user_company).then(_fill_vendor);
			}
		} else {
			_fill_vendor();
		}

		// Focus on trip date after form renders
		setTimeout(() => {
			const fd = frm.fields_dict["tcntrip_date"];
			if (fd && fd.$input) fd.$input.focus();
		}, 600);

		frappe.call({
			method: "frappe.client.get_list",
			args: { doctype: "Trip Type", filters: [["disabled", "=", 0]], fields: ["name"], order_by: "creation asc", limit_page_length: 1 },
			callback(r) { if (r.message && r.message.length) frm.set_value("trip_type", r.message[0].name); },
		});
		frappe.call({
			method: "logicore.logicore.doctype.trip.trip.get_user_branch",
			callback(r) {
				const res = r.message;
				if (!res) return;
				if (res.branch) {
					frm.set_value("branch", res.branch);
					if (res.source === "single_branch")
						frappe.show_alert({ message: "🏢 Branch auto-set (only one branch exists).", indicator: "blue" }, 4);
				} else if (res.debug) {
					frappe.msgprint({ title: "⚠️ Branch Not Auto-Set", message: res.debug.replace(/\\n/g, "<br>"), indicator: "orange" });
				}
			},
		});
	},

	origin_address_1(frm) { on_address_selected(frm, "origin_address_1"); },
	origin_address_2(frm) { on_address_selected(frm, "origin_address_2"); },
	destination_address_1(frm) { on_address_selected(frm, "destination_address_1"); },
	destination_address_2(frm) { on_address_selected(frm, "destination_address_2"); },

	// trip_type(frm) {
	// 	const combo = get_combo_for_trip(frm.doc.trip_type);
	// 	apply_combo(frm, combo);
	// 	setup_field_read_only_rules(frm);
	// 	apply_trip_type_visibility(frm);
	// 	if (frm.doc.trip_type !== "RCPL Primary") {
	// 		if (frm.doc.business_sub_format) frm.set_value("business_sub_format", "");
	// 	} else if (frm.is_new() && !frm.doc.business_sub_format) {
	// 		frappe.call({
	// 			method: "frappe.client.get_list",
	// 			args: { doctype: "Business Subformat", filters: [["disabled", "=", 0]], fields: ["name"], order_by: "creation asc", limit_page_length: 1 },
	// 			callback(r) { if (r.message && r.message.length) frm.set_value("business_sub_format", r.message[0].name); },
	// 		});
	// 	}
	// },

	trip_type(frm) {
    const combo = get_combo_for_trip(frm.doc.trip_type);
    apply_combo(frm, combo);
    setup_field_read_only_rules(frm);
    apply_trip_type_visibility(frm);

    // 🔥 NEW LOGIC
    frm.set_value("business_format", "");
    frm.set_value("customer", "");

    // frm.set_query("business_format", function () {
    //     return {
    //         filters: {
    //             trip_type: frm.doc.trip_type
    //         }
    //     };
    // });

    if (frm.doc.trip_type !== "RCPL Primary") {
        if (frm.doc.business_sub_format) frm.set_value("business_sub_format", "");
    } else if (frm.is_new() && !frm.doc.business_sub_format) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Business Subformat",
                filters: [["disabled", "=", 0]],
                fields: ["name"],
                order_by: "creation asc",
                limit_page_length: 1
            },
            callback(r) {
                if (r.message && r.message.length)
                    frm.set_value("business_sub_format", r.message[0].name);
            },
        });
    }
},
	business_format(frm) {
    if (!frm.doc.business_format) {
        _set_default_customer(frm, null);
        frm.set_value("billing_start_date", "");
        frm.set_value("billing_end_date", "");
        return;
    }
    frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Business Format", name: frm.doc.business_format },
        callback(r) {
            if (r.message) {
                _apply_billing_dates_for_current_month(frm, r.message);
                _set_default_customer(frm, r.message);
            }
        },
    });
},


tcntrip_date(frm) {
    if (frm.doc.business_format) {
        frappe.call({
            method: "frappe.client.get",
            args: { doctype: "Business Format", name: frm.doc.business_format },
            callback(r) {
                if (r.message) {
                    _apply_billing_dates_for_current_month(frm, r.message);
                }
            },
        });
    }
},

driver(frm) {
    if (!frm.doc.driver) {
        frm.set_value("driver_mobile", "");
        return;
    }

    const selected_driver = frm.doc.driver;

    frappe.db.get_value("Driver", selected_driver, ["cell_number"], (r) => {
        if (frm.doc.driver !== selected_driver) return;
        frm.set_value("driver_mobile", (r && r.cell_number) || "");
    });
},

	origin_city(frm) {
		update_route_chip(frm);
		if (frm.doc.origin_city) {
			frappe.call({
				method: "logicore.logicore.doctype.trip.trip.get_city_state",
				args: { city: frm.doc.origin_city },
				callback(r) {
					if (r.message) frm.set_value("origin_state", r.message);
					_force_readonly_fields_visible(frm);
				},
			});
		} else {
			_force_readonly_fields_visible(frm);
		}
		fetch_route_distance(frm);
	},

	destination_city_1(frm) {
		update_route_chip(frm);
		if (frm.doc.destination_city_1) {
			frappe.call({
				method: "logicore.logicore.doctype.trip.trip.get_city_state",
				args: { city: frm.doc.destination_city_1 },
				callback(r) {
					if (r.message) frm.set_value("destination_state", r.message);
					_force_readonly_fields_visible(frm);
				},
			});
		} else {
			_force_readonly_fields_visible(frm);
		}
		fetch_route_distance(frm);
	},

	validate(frm) {
		// Hidden-but-mandatory-field validation now lives globally in
		// tms_field_permission_guard.js (frappe.ui.form.on("*", ...)) -- it runs for
		// every doctype, not just Trip, and covers future TMS-managed doctypes
		// automatically. See that file for the check itself.

		const chrono_errors = validate_chronology(frm);
		const km_error = (flt(frm.doc.start_km) && flt(frm.doc.end_km) && flt(frm.doc.end_km) < flt(frm.doc.start_km))
			? ["End KM cannot be less than Start KM."] : [];
		const all_errors = [...chrono_errors, ...km_error];
		if (all_errors.length) {
			frappe.msgprint({ title: __("Data Validation Error"), message: all_errors.join("<br>"), indicator: "red" });
			frappe.validated = false;
		}
	},

	date_pod_uploaded_on_erp(frm) {
		if (frm.doc.date_pod_uploaded_on_erp && (!frm.doc.arrival_date_time || !frm.doc.release_date_time)) {
			frappe.msgprint({ title: __("Data Validation Error"), message: __("POD cannot be uploaded until Arrival and Release Date/Time at Unloading Site are filled."), indicator: "red" });
			frappe.model.set_value(frm.doctype, frm.docname, "date_pod_uploaded_on_erp", null);
		}
	},

	reach_date_time(frm) { if (!enforce_field_sequence(frm, "reach_date_time")) return; apply_date_sequence_lock(frm); calc_loading_detention(frm, { auto_rate: true }); refresh_calcs(frm); },
	dispatch_date_time(frm) { if (!enforce_field_sequence(frm, "dispatch_date_time")) return; apply_date_sequence_lock(frm); calc_loading_detention(frm, { auto_rate: true }); calc_journey_time(frm); refresh_calcs(frm); },
	loading_detention_rate_per_day(frm) { calc_loading_detention_amount(frm); calc_total_detention(frm); calc_total_additional_charges(frm); refresh_calcs(frm); },
	loading_charge(frm) { calc_loading_unloading_total(frm); calc_total_additional_charges(frm); refresh_calcs(frm); },
	vendor(frm) {
		highlight_active_tab(frm); setup_vehicle_filter(frm);
		fetch_vendor_tds_and_calc(frm);
		apply_vendor_field_lock(frm);
	},
	vehicle_type(frm) {
		calc_loading_detention(frm, { auto_rate: true });
		calc_unloading_detention(frm, { auto_rate: true });
		refresh_calcs(frm);
	},
	vehicle_no(frm) {
		highlight_active_tab(frm);
		fetch_start_km_for_vehicle(frm);
	},
	arrival_date_time(frm) { if (!enforce_field_sequence(frm, "arrival_date_time")) return; apply_date_sequence_lock(frm); calc_unloading_detention(frm, { auto_rate: true }); calc_journey_time(frm); highlight_active_tab(frm); refresh_calcs(frm); },
	release_date_time(frm) { if (!enforce_field_sequence(frm, "release_date_time")) return; apply_date_sequence_lock(frm); calc_unloading_detention(frm, { auto_rate: true }); refresh_calcs(frm); },
	unloading_detention_rate_per_day(frm) { calc_unloading_detention_amount(frm); calc_total_detention(frm); calc_total_additional_charges(frm); refresh_calcs(frm); },
	unloading_charge(frm) { calc_loading_unloading_total(frm); calc_total_additional_charges(frm); refresh_calcs(frm); },
	weighment_charges(frm) { calc_total_additional_charges(frm); refresh_calcs(frm); },
	extra_expenses(frm) { calc_total_additional_charges(frm); refresh_calcs(frm); },
	loading_charge_payment_by(frm) { calc_trip_total_expense(frm); refresh_calcs(frm); },
	unloading_charge_payment_by(frm) { calc_trip_total_expense(frm); refresh_calcs(frm); },
	extra_expense_paid_by(frm) { calc_trip_total_expense(frm); refresh_calcs(frm); },
	distance_loadingunloading_site(frm) { calc_ideal_journey_time(frm); refresh_calcs(frm); },
	start_km(frm) { validate_km(frm); calc_dedicated_km(frm); refresh_calcs(frm); },
	end_km(frm) { validate_km(frm); calc_dedicated_km(frm); refresh_calcs(frm); },
	standard_km(frm) { calc_km_variation(frm); refresh_calcs(frm); },
	vendor_freight(frm) { calc_vendor_freight(frm); apply_vendor_tds(frm); refresh_calcs(frm); },
	vendor_freight_extra(frm) { calc_vendor_freight(frm); apply_vendor_tds(frm); refresh_calcs(frm); },
	vendor_tds_to_be_deducted(frm) { calc_vendor_payment_total(frm); refresh_calcs(frm); },
	customer_freight(frm) { calc_trip_total_amount(frm); calc_trip_total_expense(frm); refresh_calcs(frm); },
	approved_origin_detention(frm) { calc_approved_detention(frm); refresh_calcs(frm); },
	approved_destination_detention(frm) { calc_approved_detention(frm); refresh_calcs(frm); },
	approved_loading_charge(frm) { calc_approved_loading_unloading(frm); refresh_calcs(frm); },
	approved_unloading_charge(frm) { calc_approved_loading_unloading(frm); refresh_calcs(frm); },
	approved_weighment_charge(frm) { calc_total_approved_addl(frm); refresh_calcs(frm); },
	approved_extra_expenses(frm) { calc_total_approved_addl(frm); refresh_calcs(frm); },
	brokerage_amount(frm) { calc_total_approved_addl(frm); refresh_calcs(frm); },
	lr_money(frm) { calc_total_approved_addl(frm); refresh_calcs(frm); },
	tds_deducted_by_customer(frm) { calc_total_approved_addl(frm); refresh_calcs(frm); },

	// date_pod_uploaded_on_erp(frm) {
	// 	frm.set_value("pod_status", frm.doc.date_pod_uploaded_on_erp ? "Uploaded" : "Left");
	// 	update_trip_status_display(frm);
	// 	 update_pod_button_label(frm);
	// },
	date_pod_uploaded_on_erp(frm) {
		if (frm.doc.date_pod_uploaded_on_erp) {
			const pt = (frm.doc.uploaded_pod_originalduplicate || "Original");
			frm.set_value("pod_status", pt === "Duplicate" ? "Duplicate POD Uploaded" : "Original POD Uploaded");
		} else {
			frm.set_value("pod_status", "POD Not Uploaded");
		}
		update_trip_status_display(frm);
		update_pod_button_label(frm);
	},

	utr_no(frm) { update_trip_status_display(frm); highlight_active_tab(frm); },
	payment_advice_no(frm) { update_trip_status_display(frm); highlight_active_tab(frm); },
	bill_nodate(frm) { update_trip_status_display(frm); highlight_active_tab(frm); },

	trip_status(frm) {
		const s = frm.doc.trip_status || "Draft";
		const c = STATUS_COLORS[s] || "#94A3B8";
		$(".tms-bstatus").css({ background: hex_alpha(c, .18), color: c, "border-color": hex_alpha(c, .45) });
		$(".tms-status-dot").css({ background: c, "box-shadow": `0 0 6px ${c}` });
		$(".tms-banner-status-text").text(s);
	},

	tcntrip_no(frm) { },
});


function _apply_billing_dates_for_current_month(frm, bf_record) {
    const raw_start = bf_record.billing_start_date;  // "2026-02-01"
    const raw_end   = bf_record.billing_end_date;    // "2026-02-28" or "2026-02-15"
    if (!raw_start || !raw_end) return;

    const start_day = parseInt(raw_start.split("-")[2], 10);

    const [ey, em, ed] = raw_end.split("-").map(Number);
    const tpl_month_last = new Date(ey, em, 0).getDate();  // last day of template's month
    const end_is_eom     = (ed === tpl_month_last);
    const end_day        = ed;

    // Reference = trip date's month
    const ref          = new Date((frm.doc.tcntrip_date || frappe.datetime.get_today()) + "T00:00:00");
    const yr           = ref.getFullYear();
    const mon          = ref.getMonth();              // 0-indexed
    const trip_last    = new Date(yr, mon + 1, 0).getDate();  // last day of trip's month

    const resolved_end = end_is_eom ? trip_last : Math.min(end_day, trip_last);

    let bs, be;
    if (end_day >= start_day) {
        // Same-month cycle
        bs = new Date(yr, mon, start_day);
        be = new Date(yr, mon, resolved_end);
    } else {
        // Cross-month cycle
        bs = new Date(yr, mon - 1, start_day);
        be = new Date(yr, mon, resolved_end);
    }

    const fmt = d =>
        d.getFullYear() + "-" +
        String(d.getMonth() + 1).padStart(2, "0") + "-" +
        String(d.getDate()).padStart(2, "0");

    frm.set_value("billing_start_date", fmt(bs));
    frm.set_value("billing_end_date",   fmt(be));
}

function fmt_date_display(val) {
	if (!val || typeof val !== "string") return val;
	const parts = val.split("-");
	if (parts.length === 3 && parts[0].length === 4)
		return `${parts[2]}-${parts[1]}-${parts[0]}`;
	return val;
}


// ══════════════════════════════════════════════════════════════════
//  DRIVER DISPLAY — fixed: patch set_input + proper mobile handling
// ══════════════════════════════════════════════════════════════════

function setup_driver_query(frm) {
    frm.set_query("driver", () => ({
        query: "logicore.logicore.doctype.trip.trip.search_driver",
    }));
}

// ══════════════════════════════════════════════════════════════════
//  TRIP TYPE FIELD VISIBILITY
// ══════════════════════════════════════════════════════════════════

function build_trip_layout(frm) {
	const layout = [];
	let currentSection = null, currentColumn = null;
	(frm.meta.fields || []).forEach(field => {
		if (field.fieldtype === "Section Break") {
			currentSection = { section: field.fieldname, columns: [] };
			layout.push(currentSection);
			currentColumn = { col: null, fields: [] };
			currentSection.columns.push(currentColumn);
		} else if (field.fieldtype === "Column Break") {
			if (!currentSection || field.hidden) return;
			currentColumn = { col: field.fieldname, fields: [] };
			currentSection.columns.push(currentColumn);
		} else if (field.fieldtype !== "Tab Break" && currentColumn && !field.hidden) {
			currentColumn.fields.push(field.fieldname);
		}
	});
	return layout;
}

function reflow_trip_layout(frm, hiddenFields) {
	const layout = build_trip_layout(frm);
	layout.map(s => s.section).forEach(s => frm.toggle_display(s, true));
	const allCols = [];
	layout.forEach(s => s.columns.forEach(c => { if (c.col) allCols.push(c.col); }));
	allCols.forEach(c => frm.toggle_display(c, true));
	layout.forEach(s => {
		const sectionVisible = s.columns.some(c => c.fields.some(f => !hiddenFields.has(f)));
		if (!sectionVisible) { frm.toggle_display(s.section, false); return; }
		s.columns.forEach(c => {
			if (!c.col) return;
			if (!c.fields.some(f => !hiddenFields.has(f))) frm.toggle_display(c.col, false);
		});
	});
}


// TMS User Group field-level permission is a HIGHER layer than Trip Settings'
// per-trip-type visibility. Trip Settings' Hidden should only take effect when
// the group has no override (Default) for a field. If the group has explicitly
// set the field to Read Only (real permlevel read:1, write:0 -- distinct from
// Default's read:1, write:1 baseline), the field must stay VISIBLE (read-only),
// ignoring whatever Trip Settings says for the current trip type. A group-level
// Hidden field needs no special-casing here -- permlevel already denies read
// access outright regardless of Trip Settings' own `hidden` flag.
function _tms_group_forces_read_only(frm, fieldname) {
    const df = frm.fields_dict[fieldname] && frm.fields_dict[fieldname].df;
    const permlevel = (df && df.permlevel) || 0;
    if (!permlevel) return false;
    const p = frm.perm && frm.perm[permlevel];
    return !!(p && p.read && !p.write);
}

function apply_trip_type_visibility(frm) {
    const tripType = frm.doc.trip_type;
    if (!tripType) { reflow_trip_layout(frm, new Set()); return; }
    const activeCombo = get_combo_for_trip(tripType);

    // Apply combo immediately
    frm._tms_resolved_color = activeCombo.primary;
    frm._tms_resolved_combo = activeCombo;
    apply_combo(frm, activeCombo);

    frappe.call({
        method: "logicore.logicore.doctype.trip_settings.trip_settings.get_field_config",
        args: { trip_type: tripType },
        callback(r) {
            if (frm.doc.trip_type !== tripType) return;

            const cfg  = r.message || {};
            const rows = cfg.fields || [];
            const hiddenFields = new Set();
            rows.forEach(row => {
                if (!row.is_visible && !_tms_group_forces_read_only(frm, row.fieldname)) {
                    hiddenFields.add(row.fieldname);
                }
            });

            // ✅ Apply field visibility
            reflow_trip_layout(frm, hiddenFields);
            rows.forEach(row => {
                const groupForcesReadOnly = _tms_group_forces_read_only(frm, row.fieldname);
                frm.set_df_property(row.fieldname, "hidden", (row.is_visible || groupForcesReadOnly) ? 0 : 1);
            });

            // ✅ Force Frappe to re-render all changed fields at once
            frm.refresh_fields(rows.map(r => r.fieldname));

            frm._tms_field_config = cfg;

            const tripColor = (cfg.trip_color || "").trim();
        const resolvedCombo = tripColor
            ? Object.assign({}, activeCombo, { primary: tripColor })
            : activeCombo;

        frm._tms_resolved_color = tripColor || activeCombo.primary;
        frm._tms_resolved_combo = resolvedCombo;
        apply_combo(frm, resolvedCombo);

        // ✅ Single setTimeout for all post-render work
        setTimeout(() => {
            render_banner(frm, resolvedCombo);
            if (tripColor) apply_trip_color(frm, tripColor);
            _render_tcntrip_lock_checkbox(frm);
            _force_readonly_fields_visible(frm);
			_inject_bottom_save_button(frm);
			 render_vendor_payment_table(frm);
			_fix_other_trip_type_columns(frm);
        }, 50);
        },
        error() {
            if (frm.doc.trip_type !== tripType) return;
            reflow_trip_layout(frm, new Set());
            frm._tms_resolved_color = activeCombo.primary;
            frm._tms_resolved_combo = activeCombo;
            frm._tms_field_config   = null;
            apply_combo(frm, activeCombo);
            setTimeout(() => {
                render_banner(frm, activeCombo);
                _render_tcntrip_lock_checkbox(frm);
				_inject_bottom_save_button(frm);

            }, 50);
        }
    });
}


const CURRENCY_READONLY_FIELDS = new Set([
	"loading_site_detention_amount", "unloading_site_detention_amount",
	"total_detention_amount", "total_loading_unloading_charge", "total_additional_charges",
	"total_vendor_freight", "amount_to_be_paid_to_vendor",
	"approved_detention_charge", "approved_loadingunloading_charge",
	"total_approved_addl_amount", "difference_claimedapproved", "total_trip_amount",
]);

const SYSTEM_READONLY_FIELDS = [
	"company",
	"origin_state", "destination_state",
	"loading_detention_days", "loading_site_detention_amount",
	"unloading_detention_days", "unloading_site_detention_amount",
	"total_detention_days", "total_detention_amount",
	"total_loading_unloading_charge", "total_additional_charges",
	"total_km", "variation",
	"total_vendor_freight", "amount_to_be_paid_to_vendor",
	"journey_time", "journey_time_400_kmsday",
	"approved_detention_charge", "approved_loadingunloading_charge",
	"total_approved_addl_amount", "difference_claimedapproved",
	"total_trip_amount", "pod_status",
	"billing_start_date", "billing_end_date", "so_no",
];

// Whether the CURRENT logged-in user actually has permlevel READ access to `fieldname`
// on this form. TMS User Group's field-permission feature (Hidden/Read Only) works
// entirely through Frappe's native permlevel + Custom DocPerm mechanism, which does
// NOT touch a field's `hidden` DocField property -- it strips the value and denies
// read at the field's own permlevel instead. So code that unconditionally forces a
// field visible (like the SYSTEM_READONLY_FIELDS handling below) must check this
// first, or it will silently defeat a Hidden field-permission choice for this group.
function _tms_field_readable(frm, fieldname) {
	const df = frm.fields_dict[fieldname] && frm.fields_dict[fieldname].df;
	const permlevel = (df && df.permlevel) || 0;
	if (!permlevel) return true;
	return !!(frm.perm && frm.perm[permlevel] && frm.perm[permlevel].read);
}

function setup_field_read_only_rules(frm) {
	if (!frm.is_new()) {
		frm.set_df_property("trip_type", "read_only", 1);
	}
	frm.set_df_property("so_no", "read_only", 1);
	frm.set_df_property("so_no", "bold", 1);
	if (_tms_field_readable(frm, "so_no")) {
		frm.set_df_property("so_no", "hidden", 0);
	}
	frm.set_df_property("customer_freight", "read_only", 0);
	frm.set_df_property("customer_freight", "hidden", 0);
	SYSTEM_READONLY_FIELDS.forEach(f => { frm.set_df_property(f, "read_only", 1); });
	frm.refresh_fields(SYSTEM_READONLY_FIELDS.concat(["customer_freight"]));
	_force_readonly_fields_visible(frm);
}

function _force_readonly_fields_visible(frm) {
	_do_force(frm);
	setTimeout(() => _do_force(frm), 150);
	setTimeout(() => _do_force(frm), 450);
	setTimeout(() => _do_force(frm), 800);
	setTimeout(() => _do_force(frm), 1400);
	_bind_tab_switch_listener(frm);
}

function refresh_calcs(frm) { setTimeout(() => _do_force(frm), 60); }

function run_all_calcs_on_load(frm) {
	calc_loading_detention(frm); calc_unloading_detention(frm);
	calc_loading_unloading_total(frm); calc_journey_time(frm);
	calc_ideal_journey_time(frm); calc_dedicated_km(frm);
	calc_vendor_freight(frm); calc_approved_detention(frm);
	calc_approved_loading_unloading(frm); calc_total_approved_addl(frm);
	calc_trip_total_expense(frm);
	refresh_calcs(frm);
}

function _bind_tab_switch_listener(frm) {
	if (frm._tms_tab_listener_bound) return;
	frm._tms_tab_listener_bound = true;
	frm.$wrapper.on("click.tms_tabs", ".form-tabs .nav-link", function () {
		setTimeout(() => _do_force(frm), 80);
		setTimeout(() => _do_force(frm), 300);
		setTimeout(() => _do_force(frm), 600);
	});
}

function _fmt_inr(val) {
	const num = parseFloat(val);
	if (isNaN(num)) return "₹ —";
	const abs = Math.abs(num).toLocaleString("en-IN", { maximumFractionDigits: 2 });
	return (num < 0 ? "− ₹\u00A0" : "₹\u00A0") + abs;
}

function _do_force(frm) {
	SYSTEM_READONLY_FIELDS.forEach(f => {
		const fd = frm.fields_dict[f];
		if (!fd || !fd.$wrapper) return;
		if (fd.df && fd.df.hidden) return;
		// TMS User Group field-permission Hidden is a HIGHER-PRIORITY layer than Trip
		// Settings' per-trip-type visibility -- if the current user lacks permlevel
		// read access to this field, it must stay hidden regardless of Trip Settings
		// or anything else below this check.
		if (!_tms_field_readable(frm, f)) {
			fd.$wrapper.addClass("hidden-control").css({ display: "none", visibility: "hidden" });
			return;
		}
		const cfg = frm._tms_field_config;
        if (cfg && Array.isArray(cfg.fields)) {
            const row = cfg.fields.find(r => r.fieldname === f);
            if (row && !row.is_visible) {
                // Actively hide the wrapper so _do_force doesn't fight the setting
                fd.$wrapper.addClass("hidden-control")
                    .css({ display: "none", visibility: "hidden" });
                return;
            }
        }
		const val = frm.doc[f];
		const empty = (val === null || val === undefined || val === "");
		const isCurrency = CURRENCY_READONLY_FIELDS.has(f);
		const isDate = DATE_DISPLAY_FIELDS.has(f);
		fd.$wrapper.addClass("tms-computed-field").removeClass("hidden-control")
			.css({ display: "block", visibility: "visible", opacity: "1" });
		if (!fd.$wrapper.find(".tms-auto-badge").length && f !== "so_no")
			fd.$wrapper.append('<span class="tms-auto-badge">⚙ Auto</span>');
		const label_text = (fd.df && fd.df.label) ? fd.df.label
			: f.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
		let $label = fd.$wrapper.find("label.control-label");
		if (!$label.length) {
			const $lbl = $(`<label class="control-label"></label>`).text(label_text);
			const $val = fd.$wrapper.find(".like-disabled-input, input, select, textarea").first();
			if ($val.length) $val.before($lbl); else fd.$wrapper.prepend($lbl);
			$label = $lbl;
		}
		$label.css({ display: "block", visibility: "visible", opacity: "1" });
		if (!$label.text().trim()) $label.text(label_text);
		fd.$wrapper.closest(".form-column").css({ display: "", visibility: "visible" });
		const $disp = fd.$wrapper.find(".like-disabled-input");
		if ($disp.length) {
			$disp.css({ display: "block", "min-height": "36px", opacity: "1", visibility: "visible" });
			if (empty) {
				$disp.text(f === "so_no" ? "⏳ Auto on Save" : (isCurrency ? "₹ —" : "—"));
			} else if (isCurrency) {
				$disp.text(_fmt_inr(val));
			} else if (isDate) {
				$disp.text(fmt_date_display(String(val)));
			} else {
				$disp.text(String(val));
			}
			if ((parseInt($disp.css("padding-left")) || 0) < 28) $disp.css("padding-left", "32px");
		}
		const $inp = fd.$wrapper.find("input[disabled], input[readonly], .form-control[disabled], select[disabled]");
		if (!$disp.length && $inp.length) {
			if (empty) $inp.attr("placeholder", f === "so_no" ? "⏳ Auto on Save" : (isCurrency ? "₹ —" : "—"));
			$inp.css({ display: "block", "min-height": "36px", opacity: "1", visibility: "visible", "pointer-events": "none" });
		}
	});
	// Sync highlight dots after display values are updated
	tms_update_fill_status(frm);
}

// ══════════════════════════════════════════════════════════════════
//  DROPDOWN FIX
// ══════════════════════════════════════════════════════════════════

function _reposition_awesomplete($input) {
	let $ul = $input.next("ul[role='listbox']");
	if (!$ul.length) $ul = $input.next("ul");
	if (!$ul.length)
		$ul = $input.closest(".frappe-control, .control-input-wrapper, .control-input").find("ul[role='listbox'], ul.awesomplete").first();
	if (!$ul.length || !$ul.is(":visible")) return;
	const rect = $input[0].getBoundingClientRect();
	const ulH = Math.min(300, $ul[0].scrollHeight || 220);
	const openUp = (window.innerHeight - rect.bottom - 6) < ulH && rect.top > ulH;
	$ul.css({
		position: "fixed", zIndex: 99999,
		top: (openUp ? rect.top - ulH - 4 : rect.bottom + 2) + "px",
		left: rect.left + "px", width: rect.width + "px", maxWidth: rect.width + "px",
		maxHeight: "300px", overflowY: "auto", bottom: "auto", right: "auto"
	});
}

function _attach_dropdown_fix(frm) {
	frm.$wrapper.off("input.tms_dd focus.tms_dd awesomplete-open.tms_dd");
	const SEL = ".frappe-control[data-fieldtype='Link'] input, .frappe-control[data-fieldtype='Dynamic Link'] input";
	frm.$wrapper.on("awesomplete-open.tms_dd", SEL, function () {
		_reposition_awesomplete($(this));
		setTimeout(() => _reposition_awesomplete($(this)), 60);
	});
	frm.$wrapper.on("input.tms_dd", SEL, function () {
		const $i = $(this); _reposition_awesomplete($i);
		setTimeout(() => _reposition_awesomplete($i), 80);
	});
	frm.$wrapper.on("focus.tms_dd", SEL, function () {
		const $i = $(this); setTimeout(() => _reposition_awesomplete($i), 60);
	});
	$(window).off("scroll.tms_dd resize.tms_dd").on("scroll.tms_dd resize.tms_dd", () => {
		const $f = frm.$wrapper.find(SEL + ":focus");
		if ($f.length) _reposition_awesomplete($f.first());
	});
}

// ══════════════════════════════════════════════════════════════════
//  VALIDATION
// ══════════════════════════════════════════════════════════════════

const DATE_SEQUENCE = [
	{ field: "reach_date_time",    label: "Reach Loading Point Date/Time" },
	{ field: "dispatch_date_time", label: "Dispatch Loading Point Date/Time" },
	{ field: "arrival_date_time",  label: "Arrival Unloading Point Date/Time" },
	{ field: "release_date_time",  label: "Release Unloading Point Date/Time" },
];

// Freeze each field until its predecessor in the sequence is filled — updates
// live on every relevant field change, not just on form refresh.
// Applies the app's existing "stage-locked" visual treatment (dashed border,
// muted grey, not-allowed cursor — see tms_trip.css .tms-stage-locked) instead
// of Frappe's plain native read-only grey, so conditionally-locked fields read
// as "was editable, now locked" rather than "always system-computed".
function _toggle_stage_lock_class(frm, fieldname, locked) {
	const fd = frm.fields_dict[fieldname];
	if (fd && fd.$wrapper) fd.$wrapper.toggleClass("tms-stage-locked", !!locked);
}

// A field is editable only if its predecessor is filled (forward: can't fill
// out of order) AND its successor is empty (reverse: can't clear a field while
// a later one still depends on it — must clear Release before Arrival, Arrival
// before Dispatch, Dispatch before Reach). So only the current "frontier" field
// — the boundary between filled and unfilled — is ever unlocked.
function apply_date_sequence_lock(frm) {
	const n = DATE_SEQUENCE.length;
	const filled = DATE_SEQUENCE.map(e => !!frm.doc[e.field]);
	const locked_map = {};
	for (let i = 0; i < n; i++) {
		const locked_by_predecessor = i > 0 && !filled[i - 1];
		const locked_by_successor = i < n - 1 && filled[i + 1];
		const locked = locked_by_predecessor || locked_by_successor;
		frm.set_df_property(DATE_SEQUENCE[i].field, "read_only", locked ? 1 : 0);
		locked_map[DATE_SEQUENCE[i].field] = locked;
	}
	const fields = DATE_SEQUENCE.map(e => e.field);
	frm.refresh_fields(fields);
	fields.forEach(f => _toggle_stage_lock_class(frm, f, locked_map[f]));
}

const OWN_FLEET_FIELDS   = ["vehicle_no", "driver", "driver_mobile"];
const MARKET_FLEET_FIELDS = ["vehicle_market", "driver_market", "driver_mobile_market"];

// Own-fleet fields (Vehicle No/Driver/Driver Mobile) are editable only when the
// selected Vendor is the Company's Default Supplier; Market fields (Vehicle/Driver/
// Driver Mobile (Market)) are editable only when a different (market) vendor is
// selected. Until both company's default supplier and trip's vendor are known,
// leave both sets editable rather than guessing.
function apply_vendor_field_lock(frm) {
	const ALL_FIELDS = OWN_FLEET_FIELDS.concat(MARKET_FLEET_FIELDS);
	const locked_map = {};

	if (!frm.doc.vendor || !frm._tms_default_supplier) {
		ALL_FIELDS.forEach(f => { frm.set_df_property(f, "read_only", 0); locked_map[f] = false; });
	} else {
		const is_own_fleet = frm.doc.vendor === frm._tms_default_supplier;
		OWN_FLEET_FIELDS.forEach(f => {
			const locked = !is_own_fleet;
			frm.set_df_property(f, "read_only", locked ? 1 : 0);
			locked_map[f] = locked;
		});
		MARKET_FLEET_FIELDS.forEach(f => {
			const locked = is_own_fleet;
			frm.set_df_property(f, "read_only", locked ? 1 : 0);
			locked_map[f] = locked;
		});
	}
	frm.refresh_fields(ALL_FIELDS);
	ALL_FIELDS.forEach(f => _toggle_stage_lock_class(frm, f, locked_map[f]));
}

function fetch_default_supplier_and_lock(frm) {
	if (!frm.doc.company) {
		frm._tms_default_supplier = null;
		apply_vendor_field_lock(frm);
		return;
	}
	frappe.db.get_value("Company", frm.doc.company, "default_supplier").then((r) => {
		frm._tms_default_supplier = (r && r.message && r.message.default_supplier) || null;
		apply_vendor_field_lock(frm);
	});
}

function validate_chronology(frm) {
	const errors = [];
	for (let i = 1; i < DATE_SEQUENCE.length; i++) {
		const prev = DATE_SEQUENCE[i - 1], cur = DATE_SEQUENCE[i];
		const prev_val = frm.doc[prev.field], cur_val = frm.doc[cur.field];
		if (cur_val && !prev_val) {
			errors.push(`${prev.label} must be entered before ${cur.label}.`);
		} else if (prev_val && cur_val && new Date(cur_val) < new Date(prev_val)) {
			errors.push(`${cur.label} cannot be before ${prev.label}.`);
		}
	}
	if (errors.length) frappe.show_alert({ message: errors.join("<br>"), indicator: "orange" }, 5);
	return errors;
}

// Real-time block: validates the single field just changed and, if invalid,
// reverts only that field so the user sees an immediate error instead of
// discovering the problem at save time.
function enforce_field_sequence(frm, fieldname) {
	const idx = DATE_SEQUENCE.findIndex(e => e.field === fieldname);
	if (idx === -1 || !frm.doc[fieldname]) return true;

	const cur = DATE_SEQUENCE[idx];
	const cur_val = frm.doc[fieldname];

	if (idx > 0) {
		const prev = DATE_SEQUENCE[idx - 1];
		const prev_val = frm.doc[prev.field];
		if (!prev_val) {
			frappe.msgprint({
				title: __("Data Validation Error"),
				message: __("Please enter {0} before entering {1}.", [prev.label, cur.label]),
				indicator: "red",
			});
			frm.set_value(fieldname, "");
			return false;
		}
		if (new Date(cur_val) < new Date(prev_val)) {
			frappe.msgprint({
				title: __("Data Validation Error"),
				message: __("{0} cannot be before {1}.", [cur.label, prev.label]),
				indicator: "red",
			});
			frm.set_value(fieldname, "");
			return false;
		}
	}

	if (idx < DATE_SEQUENCE.length - 1) {
		const next = DATE_SEQUENCE[idx + 1];
		const next_val = frm.doc[next.field];
		if (next_val && new Date(next_val) < new Date(cur_val)) {
			frappe.msgprint({
				title: __("Data Validation Error"),
				message: __("{0} cannot be after {1}. Please update {1} first.", [cur.label, next.label]),
				indicator: "red",
			});
			frm.set_value(fieldname, "");
			return false;
		}
	}

	return true;
}

function validate_km(frm) {
	if (flt(frm.doc.start_km) && flt(frm.doc.end_km) && flt(frm.doc.end_km) < flt(frm.doc.start_km))
		frappe.show_alert({ message: __("End KM cannot be less than Start KM."), indicator: "orange" }, 5);
}

// ══════════════════════════════════════════════════════════════════
//  STAGE DISPLAY
// ══════════════════════════════════════════════════════════════════

function update_trip_status_display(frm) {
	const idx = _get_stage_idx(frm);
	const cur = TRIP_STATUS_STAGES[idx];
	$(".tms-dot").each(function (i) {
		$(this).removeClass("tms-dot-done tms-dot-current tms-dot-pending")
			.addClass(i < idx ? "tms-dot-done" : i === idx ? "tms-dot-current" : "tms-dot-pending");
	});
	$(".tms-bstage").text(cur.icon + " " + cur.label);
}

function update_pod_button_label(frm) {
	const POD_UPLOADED_STATUSES = ["Original POD Uploaded", "Duplicate POD Uploaded"];
	const uploaded = !!(frm.doc.date_pod_uploaded_on_erp)
		|| POD_UPLOADED_STATUSES.includes(frm.doc.pod_status);

	const label = uploaded ? "📷 POD ✅" : "📷 POD ⚠️";

	let $btn = $();
	if (frm.page && frm.page.$actions) {
		$btn = frm.page.$actions.find(".btn").filter(function () {
			return $(this).text().trim().match(/POD/);
		}).first();
	}
	if (!$btn.length) {
		$btn = $(".page-actions .btn, .custom-btn-group .btn, .inner-toolbar .btn").filter(function () {
			return $(this).text().trim().match(/POD/);
		}).first();
	}
	if (!$btn.length) return;

	$btn.text(__(label));
	if (uploaded) {
		$btn.attr("style",
			"background:#ECFDF5!important;border-color:#6EE7B7!important;" +
			"color:#065F46!important;font-weight:700!important;" +
			"box-shadow:0 0 0 2px rgba(34,197,94,0.18)!important;"
		);
	} else {
		$btn.attr("style",
			"background:#FFF7ED!important;border-color:#FCD34D!important;" +
			"color:#92400E!important;font-weight:700!important;" +
			"box-shadow:0 0 0 2px rgba(252,211,77,0.22)!important;"
		);
	}
}

// ══════════════════════════════════════════════════════════════════
//  CALCULATIONS
// ══════════════════════════════════════════════════════════════════

function set_calc(frm, f, v) { frm.doc[f] = v; frm.refresh_field(f); }

function calc_ideal_journey_time(frm) {
	const d = flt(frm.doc.distance_loadingunloading_site);
	if (d) set_calc(frm, "journey_time_400_kmsday", hours_to_readable((d / 400) * 24));
}
function calc_journey_time(frm) {
	const h = hours_between(frm.doc.dispatch_date_time, frm.doc.arrival_date_time);
	if (h > 0) set_calc(frm, "journey_time", hours_to_readable(h));
}
function calc_loading_detention(frm, opts) {
	opts = opts || {};
	const days = (frm.doc.reach_date_time && frm.doc.dispatch_date_time)
		? detention_days_calc(hours_between(frm.doc.reach_date_time, frm.doc.dispatch_date_time))
		: 0;
	set_calc(frm, "loading_detention_days", days);
	if (opts.auto_rate) {
		apply_loading_detention_rate(frm);
	} else {
		calc_loading_detention_amount(frm);
	}
}
function calc_loading_detention_amount(frm) {
	set_calc(frm, "loading_site_detention_amount", flt(cint(frm.doc.loading_detention_days) * flt(frm.doc.loading_detention_rate_per_day)));
	calc_total_detention(frm);
}
function calc_unloading_detention(frm, opts) {
	opts = opts || {};
	const days = (frm.doc.arrival_date_time && frm.doc.release_date_time)
		? detention_days_calc(hours_between(frm.doc.arrival_date_time, frm.doc.release_date_time))
		: 0;
	set_calc(frm, "unloading_detention_days", days);
	if (opts.auto_rate) {
		apply_unloading_detention_rate(frm);
	} else {
		calc_unloading_detention_amount(frm);
	}
}

// ── Auto-fill detention rate/day from Vehicle Type (tiered: up to N days vs beyond) ──
function fetch_vehicle_type_detention_rates(frm, callback) {
	callback = callback || function () {};
	if (!frm.doc.vehicle_type) {
		frm._vehicle_type_rates = null;
		frm._vehicle_type_rates_for = null;
		callback();
		return;
	}
	if (frm._vehicle_type_rates_for === frm.doc.vehicle_type) {
		callback();
		return;
	}
	frappe.db.get_value("Vehicle Type", frm.doc.vehicle_type,
		["upto_day", "detention_per_day_first", "detention_per_day_onwards"]
	).then((r) => {
		frm._vehicle_type_rates = (r && r.message) || null;
		frm._vehicle_type_rates_for = frm.doc.vehicle_type;
		callback();
	});
}
function detention_rate_for_days(days, rates) {
	if (!rates || !days) return 0;
	return days <= cint(rates.upto_day) ? flt(rates.detention_per_day_first) : flt(rates.detention_per_day_onwards);
}
// Always re-confirms the Vehicle Type rates are fresh (fetches if the cache is
// missing/stale) before computing — never silently no-ops on a cold cache.
function apply_loading_detention_rate(frm) {
	fetch_vehicle_type_detention_rates(frm, () => {
		set_calc(frm, "loading_detention_rate_per_day", detention_rate_for_days(cint(frm.doc.loading_detention_days), frm._vehicle_type_rates));
		calc_loading_detention_amount(frm);
	});
}
function apply_unloading_detention_rate(frm) {
	fetch_vehicle_type_detention_rates(frm, () => {
		set_calc(frm, "unloading_detention_rate_per_day", detention_rate_for_days(cint(frm.doc.unloading_detention_days), frm._vehicle_type_rates));
		calc_unloading_detention_amount(frm);
	});
}
// Vehicle Type's Link control only commits to frm.doc on blur (Frappe core
// behaviour), so clearing it via the "x" button or backspace would leave the
// detention rate fields stale until the user clicked away. Zero them the
// instant the input goes empty, ahead of that blur-triggered commit.
function setup_vehicle_type_live_clear(frm) {
	const field = frm.fields_dict.vehicle_type;
	if (!field || !field.$input) return;

	const clear_rates_if_empty = () => {
		if (field.$input.val()) return;
		frm._vehicle_type_rates = null;
		frm._vehicle_type_rates_for = null;
		set_calc(frm, "loading_detention_rate_per_day", 0);
		set_calc(frm, "unloading_detention_rate_per_day", 0);
		calc_loading_detention_amount(frm);
		calc_unloading_detention_amount(frm);
		refresh_calcs(frm);
	};

	field.$input.off("input.tms_vt_clear").on("input.tms_vt_clear", clear_rates_if_empty);
	if (field.$link_clear) {
		field.$link_clear.off("click.tms_vt_clear").on("click.tms_vt_clear", clear_rates_if_empty);
	}
}
function calc_unloading_detention_amount(frm) {
	set_calc(frm, "unloading_site_detention_amount", cint(frm.doc.unloading_detention_days) * flt(frm.doc.unloading_detention_rate_per_day));
	calc_total_detention(frm);
}
function calc_total_detention(frm) {
	set_calc(frm, "total_detention_days", cint(frm.doc.loading_detention_days) + cint(frm.doc.unloading_detention_days));
	set_calc(frm, "total_detention_amount", flt(frm.doc.loading_site_detention_amount) + flt(frm.doc.unloading_site_detention_amount));
	calc_total_additional_charges(frm);
}
function calc_loading_unloading_total(frm) {
	set_calc(frm, "total_loading_unloading_charge", flt(frm.doc.loading_charge) + flt(frm.doc.unloading_charge));
	calc_total_additional_charges(frm);
}
function calc_total_additional_charges(frm) {
	const t = flt(frm.doc.total_detention_amount) + flt(frm.doc.total_loading_unloading_charge) +
		flt(frm.doc.weighment_charges) + flt(frm.doc.extra_expenses);
	set_calc(frm, "total_additional_charges", t);
	set_calc(frm, "difference_claimedapproved", t - flt(frm.doc.total_approved_addl_amount));
	calc_trip_total_expense(frm);
}
function calc_dedicated_km(frm) {
	set_calc(frm, "total_km", flt(frm.doc.end_km) - flt(frm.doc.start_km));
	calc_km_variation(frm);
}
function calc_km_variation(frm) {
	if (flt(frm.doc.standard_km)) set_calc(frm, "variation", flt(frm.doc.total_km) - flt(frm.doc.standard_km));
}
function calc_vendor_freight(frm) {
	set_calc(frm, "total_vendor_freight", flt(frm.doc.vendor_freight) + flt(frm.doc.vendor_freight_extra));
	calc_vendor_payment_total(frm);
	calc_trip_total_expense(frm);
}
function calc_vendor_payment_total(frm) {
	set_calc(frm, "amount_to_be_paid_to_vendor", flt(frm.doc.total_vendor_freight));
}
function apply_vendor_tds(frm) {
	const pct = flt(frm._vendor_tds_pct);
	// TDS is on base Vendor Freight only, not vendor_freight_extra.
	const base = flt(frm.doc.vendor_freight);
	const tds = pct ? flt((base * pct / 100).toFixed(2)) : 0;
	set_calc(frm, "vendor_tds_to_be_deducted", tds);
	calc_vendor_payment_total(frm);
}
function fetch_vendor_tds_and_calc(frm, { apply = true } = {}) {
	if (!frm.doc.vendor) { frm._vendor_tds_pct = 0; return; }
	frappe.call({
		method: "logicore.logicore.doctype.trip.trip.get_vendor_tds",
		args: { vendor: frm.doc.vendor },
		callback(r) {
			frm._vendor_tds_pct = flt(r && r.message);
			console.log("Vendor TDS%:", frm._vendor_tds_pct, "for", frm.doc.vendor);
			// On refresh/load only cache the %, don't touch the stored TDS figure —
			// it must stay exactly as saved until vendor_freight is actually edited.
			if (apply) apply_vendor_tds(frm);
		},
	});
}
function calc_approved_detention(frm) {
	set_calc(frm, "approved_detention_charge", flt(frm.doc.approved_origin_detention) + flt(frm.doc.approved_destination_detention));
	calc_total_approved_addl(frm);
}
function calc_approved_loading_unloading(frm) {
	set_calc(frm, "approved_loadingunloading_charge", flt(frm.doc.approved_loading_charge) + flt(frm.doc.approved_unloading_charge));
	calc_total_approved_addl(frm);
}
function calc_total_approved_addl(frm) {
	let t = flt(frm.doc.approved_detention_charge) + flt(frm.doc.approved_loadingunloading_charge) +
		flt(frm.doc.approved_weighment_charge) + flt(frm.doc.approved_extra_expenses);
	set_calc(frm, "total_approved_addl_amount", t);
	set_calc(frm, "difference_claimedapproved", flt(frm.doc.total_additional_charges) - t);
	calc_trip_total_amount(frm);
	calc_trip_total_expense(frm);
}
function calc_trip_total_amount(frm) {
	// Deductions (brokerage, lr_money, tds) are applied at Receipt level, not here
	if ((frm.doc.trip_type || "").toUpperCase() === "OTHER") {
		amount = flt(frm.doc.customer_freight)
			+ flt(frm.doc.total_approved_addl_amount)
			- flt(frm.doc.brokerage_amount)
			- flt(frm.doc.lr_money)
			- flt(frm.doc.tds_deducted_by_customer);
	} else {
		amount = flt(frm.doc.customer_freight) + flt(frm.doc.total_approved_addl_amount);
	}
	// let amount = flt(frm.doc.customer_freight) + flt(frm.doc.total_approved_addl_amount);
	set_calc(frm, "total_trip_amount", amount);
}
function fetch_route_distance(frm) {
	if (!frm.doc.origin_city || !frm.doc.destination_city_1) return;
	frappe.call({
		method: "logicore.logicore.doctype.trip.trip.get_route_distance",
		args: { origin_city: frm.doc.origin_city, destination_city: frm.doc.destination_city_1 },
		callback(r) { if (r.message) { frm.set_value("distance_loadingunloading_site", r.message); calc_ideal_journey_time(frm); } },
	});
}

function calc_trip_total_expense(frm) {
    const company_paid = ["Company", "Company Driver"];
    const loading = company_paid.includes(frm.doc.loading_charge_payment_by)
        ? flt(frm.doc.loading_charge) : 0;
    const unloading = company_paid.includes(frm.doc.unloading_charge_payment_by)
        ? flt(frm.doc.unloading_charge) : 0;
    const weighment = company_paid.includes(frm.doc.extra_expense_paid_by)
        ? flt(frm.doc.weighment_charges) : 0;
    const extra = company_paid.includes(frm.doc.extra_expense_paid_by)
        ? flt(frm.doc.extra_expenses) : 0;
    const total_expense = flt(frm.doc.total_vendor_freight) +
                          loading + unloading +
                          weighment +
                          extra;
    set_calc(frm, "trip_total_freight", total_expense);
}

function hours_between(dt1, dt2) { if (!dt1 || !dt2) return 0; try { return Math.abs((new Date(dt2.replace(" ", "T")) - new Date(dt1.replace(" ", "T"))) / 3600000); } catch (_) { return 0; } }
function detention_days_calc(h) { return Math.floor(h / 24); }
function hours_to_readable(hours) { if (!hours) return "0h"; const tm = Math.round(hours * 60); const d = Math.floor(tm / 1440); const h = Math.floor((tm % 1440) / 60); const m = tm % 60; return [d && d + "d", h && h + "h", m && m + "m"].filter(Boolean).join(" ") || "0h"; }

// ══════════════════════════════════════════════════════════════════
//  THEME
// ══════════════════════════════════════════════════════════════════

function get_frappe_theme() {
	return document.documentElement.getAttribute("data-theme-mode") === "dark" ? "dark" : "light";
}

function derive_dark_combo(combo) {
	const [h, s] = hex_to_hsl(combo.primary);
	return Object.assign({}, combo, {
		page_bg: hsl_hex(h, _tc(s * 0.35, 8, 22), 12),
		card_bg: hsl_hex(h, _tc(s * 0.30, 6, 18), 16),
		field_bg: hsl_hex(h, _tc(s * 0.25, 5, 15), 13.5),
		section_border: hex_alpha(combo.primary, 0.20),
		field_border: hex_alpha(combo.primary, 0.32),
		label_color: hsl_hex(h, _tc(s * 0.55, 20, 55), 72),
		heading_color: hsl_hex(h, _tc(s * 0.35, 12, 35), 88),
	});
}

function get_combo_for_trip(trip_type) {
	let b = trip_type || "Other";
	if (!COMBOS[b]) b = "Other";
	let light_combo;
	try { const r = localStorage.getItem(TMS_STORAGE_KEY); if (r) { const s = JSON.parse(r); light_combo = COMBOS[b][s[b] ?? 0] || COMBOS[b][0]; } } catch (_) { }
	light_combo = light_combo || COMBOS[b][0];
	return get_frappe_theme() === "dark" ? derive_dark_combo(light_combo) : light_combo;
}

function apply_combo(frm, combo) {
	if (!combo) combo = DEFAULT_FALLBACK_COMBO;
	const uid = "tms-trip-" + (frm.doc.name || "new").replace(/[^a-zA-Z0-9]/g, "_");
	frm.$wrapper.attr("data-tms-id", uid);
	const sel = `[data-tms-id="${uid}"]`;
	_inject_scoped_style("tms-trip-field-theme", `
@keyframes tms-border-pulse {
  0%,100% { border-color:${combo.field_border}!important; box-shadow:0 0 0 1.5px ${hex_alpha(combo.primary, 0.10)}; }
  50% { border-color:${hex_alpha(combo.primary, 0.70)}!important; box-shadow:0 0 0 2.5px ${hex_alpha(combo.primary, 0.22)}; }
}
${sel} input.form-control:not([disabled]):not([readonly]),
${sel} select.form-control:not([disabled]),
${sel} textarea.form-control:not([disabled]) { background-color:${combo.field_bg}!important;border-color:${combo.field_border}!important;color:${combo.heading_color}!important;border-width:1.5px!important;transition:background-color .2s,border-color .2s,box-shadow .2s;animation:tms-border-pulse 3s ease-in-out infinite; }
${sel} input.form-control:not([disabled]):not([readonly]):hover,
${sel} select.form-control:not([disabled]):hover,
${sel} textarea.form-control:not([disabled]):hover { background-color:${hex_alpha(combo.primary, 0.06)}!important;box-shadow:0 2px 8px ${hex_alpha(combo.primary, 0.10)}!important; }
${sel} input.form-control:not([disabled]):not([readonly]):focus,
${sel} select.form-control:not([disabled]):focus,
${sel} textarea.form-control:not([disabled]):focus { background-color:${hex_alpha(combo.primary, 0.05)}!important;box-shadow:0 0 0 3px ${hex_alpha(combo.primary, 0.18)},0 2px 8px ${hex_alpha(combo.primary, 0.12)}!important;outline:none!important; }
${sel} .frappe-control .control-label,${sel} label.control-label { color:${combo.label_color}!important; }
${sel} .form-section .section-head,${sel} .form-section-heading { color:${combo.heading_color}!important;border-color:${combo.section_border}!important; }
${sel} .like-disabled-input { background-color:${combo.field_bg}!important;border-color:${combo.field_border}!important;color:${combo.label_color}!important; }
`);
	const el = frm.$wrapper[0];
	if (el) {
		el.style.setProperty("--tms-primary", combo.primary);
		el.style.setProperty("--tms-accent", combo.accent);
		el.style.setProperty("--tms-page-bg", combo.page_bg);
		el.style.setProperty("--tms-card-bg", combo.card_bg);
		el.style.setProperty("--tms-section-border", combo.section_border);
		el.style.setProperty("--tms-field-bg", combo.field_bg);
		el.style.setProperty("--tms-field-border", combo.field_border);
		el.style.setProperty("--tms-label-color", combo.label_color);
		el.style.setProperty("--tms-heading-color", combo.heading_color);
		el.style.setProperty("--tms-radius", combo.radius);
		el.style.setProperty("--tms-primary-light", hex_alpha(combo.primary, 0.10));
		el.style.setProperty("--tms-primary-border", hex_alpha(combo.primary, 0.28));
		el.style.setProperty("--tms-field-focus-glow", hex_alpha(combo.primary, 0.12));
		el.style.setProperty("--tms-hl-bg", hex_alpha(combo.primary, 0.13));
		el.style.setProperty("--tms-hl-border", hex_alpha(combo.primary, 0.65));
	}
}

function _inject_scoped_style(id, css) {
	let $el = $(`#${id}`);
	if (!$el.length) { $el = $(`<style id="${id}"></style>`).appendTo("head"); }
	$el.text(css);
}

// Generates highlight CSS for key data-entry fields.
// Called at the END of apply_combo() and apply_trip_color() so it inherits
// the current theme primary/accent and wins the cascade over general field rules
// via higher specificity ([data-fieldname] adds one extra attribute selector).
function _hl_css(sel, primary, accent) {
	const e_fns = [
		"tcntrip_date", "trip_type", "business_format", "tcntrip_no", "vehicle_type",
		"reach_date_time", "dispatch_date_time", "arrival_date_time", "release_date_time",
		"customer_freight", "vendor_freight",
		"loading_charge", "loading_charge_payment_by",
		"unloading_charge", "employee_lr_money", "company_lr_money",
	];
	const c_fns = ["loading_site_detention_amount", "unloading_site_detention_amount"];

	const e_inputs = e_fns.map(fn =>
		`${sel} [data-fieldname="${fn}"] input.form-control:not([disabled]):not([readonly]),` +
		`${sel} [data-fieldname="${fn}"] select.form-control:not([disabled]),` +
		`${sel} [data-fieldname="${fn}"] textarea.form-control:not([disabled])`
	).join(",");

	const c_display = c_fns.map(fn =>
		`${sel} [data-fieldname="${fn}"] .like-disabled-input`
	).join(",");

	const all_labels = [...e_fns, ...c_fns].map(fn =>
		`${sel} [data-fieldname="${fn}"] label.control-label`
	).join(",");

	return `
${e_inputs} { background-color:${hex_alpha(primary, 0.15)}!important;border-left:3.5px solid ${primary}!important;border-color:${hex_alpha(primary, 0.60)}!important; }
${c_display} { background-color:${hex_alpha(accent, 0.12)}!important;border-left:3.5px solid ${accent}!important;border-color:${hex_alpha(accent, 0.50)}!important; }
${all_labels} { color:${primary}!important;font-weight:700!important; }`;
}

// ── Entry Highlight System — D (fill dots) + E (progress bar) ────────────────
// Zero is treated as not filled — default 0 values should stay orange.
function tms_is_filled(val) {
	if (val === null || val === undefined || val === "") return false;
	const n = Number(val);
	if (!isNaN(n)) return n !== 0;
	return true;
}

// ALL highlighted fields — counted in progress bar + tab badges
const TMS_HL_ENTRY_FIELDS = [
	"tcntrip_date", "trip_type", "business_format", "tcntrip_no", "vehicle_type",
	"reach_date_time", "dispatch_date_time", "arrival_date_time", "release_date_time",
	"customer_freight", "vendor_freight",
	"loading_charge", "loading_charge_payment_by",
	"unloading_charge", "employee_lr_money", "company_lr_money",
];
// Auto-calculated read-only — get dots, also counted in bar + badges
const TMS_HL_CALC_FIELDS = [
	"loading_site_detention_amount", "unloading_site_detention_amount",
];
const TMS_HL_FIELDS = [...TMS_HL_ENTRY_FIELDS, ...TMS_HL_CALC_FIELDS];

function tms_inject_progress_bar(frm) {
	if (frm.$wrapper.find(".tms-progress-wrap").length) return;
	const $tabs = frm.$wrapper.find(".form-tabs-list");
	if (!$tabs.length) return;
	$tabs.before(
		`<div class="tms-progress-wrap" id="tms-entry-progress">` +
		`<div class="tms-progress-header">` +
		`<span class="tms-progress-label">Entry Progress</span>` +
		`<span class="tms-progress-fraction">0%</span>` +
		`</div>` +
		`<div class="tms-progress-track"><div class="tms-progress-fill" style="width:0%"></div></div>` +
		`</div>`
	);
}

function tms_update_tab_badges(frm, changedFn, liveVal) {
	// Mirror tms_update_fill_status: use liveVal for the actively-typed field.
	const stats = {};
	TMS_HL_FIELDS.forEach(function(fn) {
		const fd = frm.fields_dict[fn];
		if (!fd || !fd.tab) return;
		const tabId = fd.tab.id;
		if (!stats[tabId]) stats[tabId] = { tab: fd.tab, total: 0, empty: 0 };
		stats[tabId].total++;
		const val = (fn === changedFn && liveVal !== undefined) ? liveVal : frm.doc[fn];
		// Calc fields always count as filled — skip empty count for them
		if (!TMS_HL_CALC_FIELDS.includes(fn) && !tms_is_filled(val)) stats[tabId].empty++;
	});
	Object.values(stats).forEach(function(s) {
		const $btn = s.tab.tab_link.find(".nav-link");
		if (!$btn.length) return;
		let $badge = $btn.find(".tms-tab-badge");
		if (!$badge.length) {
			$badge = $(`<span class="tms-tab-badge"></span>`).appendTo($btn);
		}
		const rem = s.empty;
		$badge.text(rem > 0 ? rem : "").toggleClass("tms-tab-done", rem === 0);
		$badge.css("display", rem > 0 ? "inline-flex" : "none");
	});
}

function tms_update_fill_status(frm, changedFn, liveVal) {
	// changedFn + liveVal: field being typed into right now (frm.doc not yet synced).
	// For all other fields, frm.doc is authoritative.
	// Calc (read-only) fields: dot still reflects actual value, but always count
	// as filled for progress bar — user can't enter them, so zero is valid.
	let filled = 0;
	TMS_HL_FIELDS.forEach(function(fn) {
		const fd = frm.fields_dict[fn];
		if (!fd) return;
		const val = (fn === changedFn && liveVal !== undefined) ? liveVal : frm.doc[fn];
		const isFilled = tms_is_filled(val);
		fd.$wrapper.toggleClass("tms-hl-filled", isFilled);
		if (isFilled || TMS_HL_CALC_FIELDS.includes(fn)) filled++;
	});
	const total = TMS_HL_FIELDS.length;
	const pct = Math.round((filled / total) * 100);
	const $wrap = frm.$wrapper.find(".tms-progress-wrap");
	$wrap.find(".tms-progress-fraction").text(pct + "%");
	$wrap.find(".tms-progress-fill").css("width", pct + "%");
	$wrap.toggleClass("tms-all-done", filled === total);
	tms_update_tab_badges(frm, changedFn, liveVal);
}

function setup_master_link_filters(frm) {
	// The { disabled: 0 } filters below are redundant since the master
	// enable/disable convergence (2026-08-06): every one of these doctypes now
	// carries a `disabled` Check field, and Frappe excludes those from every Link
	// search server-side (frappe/desk/search.py:213-217). Kept commented rather
	// than deleted per project policy. If a disabled record ever shows up in one
	// of these dropdowns again, check the master's fieldname is `disabled` and not
	// `custom_disabled` before restoring these lines.
	// frm.set_query("trip_type", () => ({ filters: { disabled: 0 } }));
	// frm.set_query("business_format", () => ({ filters: { disabled: 0 }, order_by: "name asc" }));
	// frm.set_query("business_sub_format", () => ({ filters: { disabled: 0 }, order_by: "name asc" }));
	// if (frm.fields_dict["vehicle_type"]) frm.set_query("vehicle_type", () => ({ filters: { disabled: 0 } }));
	// order_by is still doing real work, so those two keep a set_query.
	frm.set_query("business_format", () => ({ order_by: "name asc" }));
	frm.set_query("business_sub_format", () => ({ order_by: "name asc" }));
	frm.set_query("trip_coordinator", () => ({
		query: "logicore.logicore.doctype.trip.trip.search_employee",
		filters: {}
	}));
	if (frm.is_new() && frm.doc.business_format && !frm.doc.customer) {
		frappe.db.get_value("Business Format", frm.doc.business_format, "default_customer", (r) => {
			_set_default_customer(frm, r);
		});
	}

}

function setup_so_no_field(frm) {
	// TMS User Group field-permission Hidden overrides this -- never force so_no
	// visible for a user who lacks permlevel read access to it.
	if (_tms_field_readable(frm, "so_no")) {
		frm.set_df_property("so_no", "hidden", 0);
	}
	frm.set_df_property("so_no", "read_only", 1);
	frm.set_df_property("so_no", "label", "Trip ID");
	frm.set_df_property("so_no", "bold", 1);
	//frm.set_df_property("so_no", "description", frm.is_new() ? "⏳ Trip ID is auto-generated when you Save" : "");
	frm.refresh_field("so_no");
}

// ══════════════════════════════════════════════════════════════════
//  BANNER
// ══════════════════════════════════════════════════════════════════

function find_form_container(frm) {
	for (const sel of [".form-page", ".page-form", ".form-layout", ".frappe-card"]) {
		let $el = frm.$wrapper.find(sel).first();
		if (!$el.length) $el = $(sel).first();
		if ($el.length) return $el;
	}
	return frm.$wrapper;
}

function _get_stage_idx(frm) {
	if (frm.doc.trip_status === "Close") return 5;
	// if (frm.doc.utr_no) return 5;
	if (frm.doc.payment_advice_no) return 4;
	if (frm.doc.bill_nodate) return 3;
	if (frm.doc.date_pod_uploaded_on_erp) return 2;
	if (frm.doc.dispatch_date_time) return 1;
	return 0;
}

function render_banner(frm, combo) {
	$(".tms-trip-banner").remove();
	if (!combo) combo = DEFAULT_FALLBACK_COMBO;
	const soNo = frm.doc.tcntrip_no || "";
	const status = frm.doc.trip_status || "Draft";
	const meta = TRIP_TYPE_META[frm.doc.trip_type] || { icon: "🚛" };
	const sColor = STATUS_COLORS[status] || "#94A3B8";
	const route = [frm.doc.origin_city, frm.doc.destination_city_1].filter(Boolean).join(" → ");
	const stageIdx = _get_stage_idx(frm);
	const curStage = TRIP_STATUS_STAGES[stageIdx];
	const dotsHtml = TRIP_STATUS_STAGES.map((_, i) => {
		const cls = i < stageIdx ? "tms-dot-done" : i === stageIdx ? "tms-dot-current" : "tms-dot-pending";
		return `<span class="tms-dot ${cls}"></span>`;
	}).join("");
	const routeHtml = route ? `<span class="tms-bid-route">📍 ${frappe.utils.escape_html(route)}</span>` : "";
	const gradStart = darken(combo.primary, 42);
	const isDark = get_luminance(combo.primary) < 0.35;
	const pillBg = isDark ? "rgba(255,255,255,0.22)" : hex_alpha(darken(combo.primary, 20), 0.85);
	const pillBorder = isDark ? "rgba(255,255,255,0.40)" : hex_alpha(darken(combo.primary, 10), 0.55);
	const typePill = frm.doc.trip_type
		? `<span class="tms-trip-type-pill" style="background:${pillBg};color:#FFFFFF;border-color:${pillBorder};text-shadow:0 1px 3px rgba(0,0,0,0.35);">${frappe.utils.escape_html(frm.doc.trip_type)}</span>`
		: "";
	const businessFormatPill = frm.doc.business_format
		? `<span class="tms-trip-type-pill" style="background:${pillBg};color:#FFFFFF;border-color:${pillBorder};text-shadow:0 1px 3px rgba(0,0,0,0.35);">${frappe.utils.escape_html(frm.doc.business_format)}</span>`
		: "";
	const tcnText = soNo ? `<span style="color:#FFFFFF;font-weight:600;margin:0 6px;text-shadow:0 1px 3px rgba(0,0,0,0.35);">${frappe.utils.escape_html(soNo)}</span>` : "";
	find_form_container(frm).prepend($(`
		<div class="tms-trip-banner" style="background:linear-gradient(135deg,${gradStart} 0%,${combo.primary} 100%);">
			<div class="tms-bid">
				<span class="tms-bid-icon">${meta.icon}</span>
				${typePill}
				${businessFormatPill}
				${tcnText}
				${routeHtml}
			</div>
			<div class="tms-bprogress">
				<div class="tms-dots">${dotsHtml}</div>
				<span class="tms-bstage">${curStage.icon} ${curStage.label}</span>
			</div>
			<div class="tms-bstatus" style="background:${hex_alpha(sColor, .18)};color:${sColor};border-color:${hex_alpha(sColor, .45)};">
				<span class="tms-status-dot" style="background:${sColor};box-shadow:0 0 6px ${sColor};"></span>
				<span class="tms-banner-status-text">${frappe.utils.escape_html(status)}</span>
			</div>
		</div>
	`));
}

function _bind_banner_live_listeners(frm) {
	// TCN/TRIP NO — fire on every keystroke
	frm.$wrapper.off("input.tms_tcn").on(
		"input.tms_tcn",
		'[data-fieldname="tcntrip_no"] input',
		() => {
			const val = frm.$wrapper.find('[data-fieldname="tcntrip_no"] input').val();
			if (frm.doc.tcntrip_no !== val) {
				frm.doc.tcntrip_no = val;
				frm.dirty();
			}
			update_tcn_and_format_chip(frm);
		}
	);

	// BUSINESS FORMAT — fire on awesomplete select (link field dropdown)
	frm.$wrapper.off("awesomplete-selectcomplete.tms_bf change.tms_bf").on(
		"awesomplete-selectcomplete.tms_bf change.tms_bf",
		'[data-fieldname="business_format"] input',
		() => setTimeout(() => {
			const val = frm.$wrapper.find('[data-fieldname="business_format"] input').val();
			if (frm.doc.business_format !== val) {
				frm.doc.business_format = val;
				frm.dirty();
			}
			update_tcn_and_format_chip(frm);
		}, 50)
	);
}

function update_route_chip(frm) {
	const route = [frm.doc.origin_city, frm.doc.destination_city_1].filter(Boolean).join(" → ");
	const $chip = $(".tms-bid-route");
	if (route) {
		if ($chip.length) { $chip.text("📍 " + route).show(); }
		else { $(".tms-bid").append(`<span class="tms-bid-route">📍 ${frappe.utils.escape_html(route)}</span>`); }
	} else { $chip.hide(); }
}

function fetch_eway_bill_details(frm) {
	if (!/^\d{12}$/.test(frm.doc.eway_bill_no)) {
		frappe.show_alert({
			message: __("E-Way Bill No should be a 12-digit number."),
			indicator: "orange",
		});
		return;
	}

	if (!frm.doc.company) {
		frappe.msgprint({
			title: __("E-Way Bill"),
			indicator: "orange",
			message: __("Please select a Company on this Trip before looking up the E-Way Bill."),
		});
		return;
	}

	frappe.call({
		method: "logicore.logicore.api.get_eway_bill_details",
		args: { ewb_no: frm.doc.eway_bill_no, company: frm.doc.company },
		freeze: true,
		freeze_message: __("Fetching e-way bill details..."),
		callback(r) {
			if (!r.message) return;
			const { vehicle_no, eway_bill_date, eway_bill_expiry_date, vehicle_not_found } = r.message;

			if (eway_bill_date) frm.set_value("eway_bill_date", eway_bill_date);
			if (eway_bill_expiry_date) frm.set_value("eway_bill_expiry_date", eway_bill_expiry_date);
			if (vehicle_no) frm.set_value("vehicle_no", vehicle_no);

			if (vehicle_not_found) {
				frappe.msgprint({
					title: __("Vehicle Not Found"),
					indicator: "orange",
					message: __("We found the E-Way Bill, but vehicle number {0} is not in your Vehicle list yet. Please add it, or select the vehicle manually.", [vehicle_not_found]),
				});
			} else if (vehicle_no) {
				frappe.show_alert({ message: __("E-Way Bill details fetched"), indicator: "green" });
			}
		},
	});
}

function update_tcn_and_format_chip(frm) {
	if (!$(".tms-bid").length) return;

	const combo = get_combo_for_trip(frm.doc.trip_type);
	const isDark = get_luminance(combo.primary) < 0.35;
	const pillBg = isDark ? "rgba(255,255,255,0.22)" : hex_alpha(darken(combo.primary, 20), 0.85);
	const pillBorder = isDark ? "rgba(255,255,255,0.40)" : hex_alpha(darken(combo.primary, 10), 0.55);

	const soNo = frm.doc.tcntrip_no || "";
	const $bid = $(".tms-bid");
	const $pills = $bid.find(".tms-trip-type-pill");

	// Update or remove Business Format pill (2nd pill)
	if (frm.doc.business_format) {
		const businessHtml = `<span class="tms-trip-type-pill" style="background:${pillBg};color:#FFFFFF;border-color:${pillBorder};text-shadow:0 1px 3px rgba(0,0,0,0.35);">${frappe.utils.escape_html(frm.doc.business_format)}</span>`;
		if ($pills.length >= 2) {
			$pills.eq(1).replaceWith(businessHtml);
		} else if ($pills.length === 1) {
			$pills.eq(0).after(businessHtml);
		}
	} else {
		if ($pills.length >= 2) {
			$pills.eq(1).remove();
		}
	}

	// Update or remove TCN text - find all spans excluding known classes
	const $allSpans = $bid.find("span");
	let $tcnSpan = null;
	$allSpans.each(function() {
		const $span = $(this);
		if (!$span.hasClass("tms-bid-icon") && !$span.hasClass("tms-trip-type-pill") && !$span.hasClass("tms-bid-route")) {
			$tcnSpan = $span;
		}
	});

	if (soNo) {
		const tcnHtml = `<span style="color:#FFFFFF;font-weight:600;margin:0 6px;text-shadow:0 1px 3px rgba(0,0,0,0.35);">${frappe.utils.escape_html(soNo)}</span>`;
		if ($tcnSpan && $tcnSpan.length) {
			$tcnSpan.replaceWith(tcnHtml);
		} else {
			// Insert before route chip, not at end
			const $route = $bid.find(".tms-bid-route");
			if ($route.length) {
				$route.before(tcnHtml);
			} else {
				$bid.append(tcnHtml);
			}
		}
	} else if ($tcnSpan && $tcnSpan.length) {
		$tcnSpan.remove();
	}
}

function render_section_icons(frm) {
	frm.$wrapper.find(".section-head, .form-section-heading").each(function () {
		const $el = $(this);
		if ($el.find(".tms-sec-icon").length) return;
		const txt = $el.text().trim().toLowerCase();
		for (const [key, icon] of Object.entries(SECTION_ICONS)) {
			if (txt.includes(key)) { $el.prepend(`<span class="tms-sec-icon">${icon}</span>`); break; }
		}
	});
}

// ══════════════════════════════════════════════════════════════════
//  TAB HIGHLIGHT
// ══════════════════════════════════════════════════════════════════

const STAGE_TAB_MAP = {
	"trip_created": "tab_trip_info", "at_loading_site": "tab_loading_unloading",
	"at_unloading_site": "tab_loading_unloading", "pod_uploaded": "tab_pod_approval",
	"bill_raised": "tab_billing_payment", "payment_received": "tab_billing_payment",
};
const TAB_ORDER = ["tab_trip_info", "tab_loading_unloading", "tab_km_vendor", "tab_pod_approval", "tab_billing_payment"];
const STAGE_TAB_COMPLETE_IDX = {
	"trip_created": 0, "at_loading_site": 1, "at_unloading_site": 1,
	"pod_uploaded": 2, "bill_raised": 3, "payment_received": 4,
};

function get_current_stage(frm) {
	if (frm.doc.utr_no) return "payment_received";
	if (frm.doc.payment_advice_no) return "bill_raised";
	if (frm.doc.bill_nodate) return "bill_raised";
	if (frm.doc.date_pod_uploaded_on_erp) return "pod_uploaded";
	if (frm.doc.arrival_date_time) return "at_unloading_site";
	if (frm.doc.dispatch_date_time) return "at_loading_site";
	return "trip_created";
}

function highlight_active_tab(frm) {
	const stage = get_current_stage(frm);
	const active_tab = STAGE_TAB_MAP[stage] || "tab_trip_info";
	const complete_up_to = STAGE_TAB_COMPLETE_IDX[stage] ?? 0;
	frm.$wrapper.find(".tms-stage-dot, .tms-tab-check").remove();
	frm.$wrapper.find(".form-tabs .nav-item").each(function () {
		const $link = $(this).find(".nav-link");
		const fn = $link.attr("data-fieldname") || "";
		const tab_idx = TAB_ORDER.indexOf(fn);
		if (fn === active_tab) $link.append('<span class="tms-stage-dot" title="Action needed here"></span>');
		else if (tab_idx >= 0 && tab_idx < complete_up_to) $link.append('<span class="tms-tab-check" title="Complete">✓</span>');
	});
}

// ══════════════════════════════════════════════════════════════════
//  BUTTONS
// ══════════════════════════════════════════════════════════════════

function _tcntrip_is_locked(frm) {
	return !!frm.doc.trip_no_not_yet_provided;
}
function _tcntrip_set_lock(frm, locked) {
	frm.set_value("trip_no_not_yet_provided", locked ? 1 : 0);
	if (!frm.is_new()) frm.save();
}

function _apply_tcntrip_lock(frm, locked) {
	frm.set_df_property("tcntrip_no", "read_only", locked ? 1 : 0);
	frm.set_df_property("tcntrip_no", "hidden", 0);
	frm.refresh_field("tcntrip_no");

	const fd = frm.fields_dict["tcntrip_no"];
	if (!fd || !fd.$wrapper) return;

	fd.$wrapper.css({ display: "block", visibility: "visible" });

	const $input = fd.$wrapper.find("input.form-control");
	if (locked) {
		$input
			.attr("readonly", "readonly")
			.attr("disabled", "disabled")
			.css({ cursor: "not-allowed", "pointer-events": "none", opacity: "0.72" });
		$input.off("keydown.tcnlock paste.tcnlock")
			.on("keydown.tcnlock paste.tcnlock", function (e) { e.preventDefault(); return false; });
		fd.$wrapper.addClass("tms-tcntrip-locked");
	} else {
		$input
			.removeAttr("readonly")
			.removeAttr("disabled")
			.css({ cursor: "", "pointer-events": "", opacity: "" });
		$input.off("keydown.tcnlock paste.tcnlock");
		fd.$wrapper.removeClass("tms-tcntrip-locked");
	}

	const $cb = $("#tms-tcntrip-lock-cb");
	if ($cb.length) $cb.prop("checked", locked);
	const $pill = $(".tms-tcntrip-lock-pill");
	if ($pill.length) {
		$pill.toggleClass("tms-tcntrip-locked-active", locked);
		$pill.find(".tms-lock-label").text(
			locked ? "Trip No Not Yet Provided 🔒" : "Trip No Not Yet Provided"
		);
	}

	setTimeout(() => {
		const $i2 = fd.$wrapper.find("input.form-control");
		if (locked) {
			$i2.attr("readonly", "readonly").attr("disabled", "disabled")
				.css({ cursor: "not-allowed", "pointer-events": "none", opacity: "0.72" });
		} else {
			$i2.removeAttr("readonly").removeAttr("disabled")
				.css({ cursor: "", "pointer-events": "", opacity: "" });
		}
		fd.$wrapper.css({ display: "block", visibility: "visible" });
	}, 120);
}

function _render_tcntrip_lock_checkbox(frm) {
	$(".tms-tcntrip-lock-wrap").remove();

	const locked = _tcntrip_is_locked(frm);
	const combo = frm._tms_resolved_combo || get_combo_for_trip(frm.doc.trip_type);
	const pri = (combo && combo.primary) ? combo.primary : "#3B4FE4";
	const light = hex_alpha(pri, 0.12);
	const border = hex_alpha(pri, 0.38);
	const activeB = hex_alpha(pri, 0.24);

	const $pill = $(`
		<div class="tms-tcntrip-lock-wrap" title="Check when TCN/Trip No is provided — locks the field">
			<style>
				.tms-tcntrip-lock-wrap { display:inline-flex;align-items:center;margin-right:6px;vertical-align:middle; }
				.tms-tcntrip-lock-pill { display:inline-flex;align-items:center;gap:6px;padding:4px 10px 4px 8px;border-radius:20px;border:1.5px solid ${border};background:${light};cursor:pointer;user-select:none;transition:background .18s,border-color .18s,box-shadow .18s;white-space:nowrap; }
				.tms-tcntrip-lock-pill:hover { background:${activeB};border-color:${pri};box-shadow:0 1px 6px ${hex_alpha(pri, 0.18)}; }
				.tms-tcntrip-lock-pill.tms-tcntrip-locked-active { background:${activeB};border-color:${pri};box-shadow:0 0 0 2px ${hex_alpha(pri, 0.18)}; }
				.tms-tcntrip-lock-cb-inner { position:relative;width:14px;height:14px;border:1.5px solid ${pri};border-radius:3px;background:#fff;flex-shrink:0;transition:background .15s;display:flex;align-items:center;justify-content:center; }
				.tms-tcntrip-lock-pill.tms-tcntrip-locked-active .tms-tcntrip-lock-cb-inner { background:${pri}; }
				.tms-tcntrip-lock-cb-inner::after { content:"";display:none;width:8px;height:5px;border-left:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(-45deg) translateY(-1px); }
				.tms-tcntrip-lock-pill.tms-tcntrip-locked-active .tms-tcntrip-lock-cb-inner::after { display:block; }
				.tms-lock-label { font-size:11.5px;font-weight:600;color:${pri};line-height:1; }
				.tms-tcntrip-locked .like-disabled-input,.tms-tcntrip-locked input.form-control { background:${hex_alpha(pri, 0.06)}!important;border-color:${border}!important;cursor:not-allowed!important; }
				.tms-tcntrip-locked label.control-label::after { content:" 🔒";font-size:10px;opacity:0.7; }
			</style>
			<label class="tms-tcntrip-lock-pill ${locked ? "tms-tcntrip-locked-active" : ""}" for="tms-tcntrip-lock-cb">
				<span class="tms-tcntrip-lock-cb-inner"></span>
				<span class="tms-lock-label">${locked ? "Trip No Not Yet Provided 🔒" : "Trip No Not Yet Provided"}</span>
			</label>
			<input type="checkbox" id="tms-tcntrip-lock-cb" style="display:none;" ${locked ? "checked" : ""} />
		</div>
	`);

	$pill.find(".tms-tcntrip-lock-pill").on("click", function (e) {
		e.preventDefault();
		const nowLocked = !_tcntrip_is_locked(frm);
		_tcntrip_set_lock(frm, nowLocked);
		_apply_tcntrip_lock(frm, nowLocked);
	});

	const $actions = frm.page.$actions || frm.$wrapper.find(".page-actions, .custom-actions").first();
	const $etplBtn = $actions.find(".btn-default, .btn").filter(function () {
		return $(this).text().trim().includes("Email Template");
	}).first();

	if ($etplBtn.length) {
		$etplBtn.before($pill);
	} else {
		$actions.prepend($pill);
	}

	_apply_tcntrip_lock(frm, locked);
}

// function add_custom_buttons(frm) {
// 	frm.add_custom_button(__("📧 Email"), () => show_email_template_dialog(frm));
// 	frm.add_custom_button(__("🗺️ Navigate"),       () => show_navigation_dialog(frm));
// 	frm.add_custom_button(__("📷 POD ⚠️"),  () => show_pod_upload_dialog(frm));  
// 	if (!frm.is_new())
// 		frm.add_custom_button(__("🖨️ Print"), () => frappe.utils.print("Trip", frm.doc.name));

// 	setTimeout(() => {
// 		_render_tcntrip_lock_checkbox(frm);
// 		update_pod_button_label(frm);   
// 	}, 60);
// }
// function add_custom_buttons(frm) {
// 	frm.add_custom_button(__("📧 Email"), () => show_email_template_dialog(frm));
// 	frm.add_custom_button(__("🗺️ Navigate"), () => show_navigation_dialog(frm));

// 	// ── Set correct label immediately based on current doc state ──
// 	const pod_label = frm.doc.date_pod_uploaded_on_erp ? __("📷 POD ✅") : __("📷 POD ⚠️");
// 	frm.add_custom_button(pod_label, () => show_pod_upload_dialog(frm));

// 	if (!frm.is_new())
// 		frm.add_custom_button(__("🖨️ Print"), () => frappe.utils.print("Trip", frm.doc.name, "Trip POD"));

// 	setTimeout(() => {
// 		_render_tcntrip_lock_checkbox(frm);
// 		update_pod_button_label(frm);
// 	}, 60);
// 	setTimeout(() => update_pod_button_label(frm), 350);
// 	setTimeout(() => update_pod_button_label(frm), 900);
// }
function add_custom_buttons(frm) {
	frm.add_custom_button(__("📧 Email"), () => {
		if (frm.is_new() || frm.is_dirty()) {
			frappe.show_alert({ message: __("💾 Please save the trip first."), indicator: "orange" }, 4);
			return;
		}
		show_email_template_dialog(frm);
	});
	frm.add_custom_button(__("🗺️ Navigate"), () => {
		if (frm.is_new() || frm.is_dirty()) {
			frappe.show_alert({ message: __("💾 Please save the trip first."), indicator: "orange" }, 4);
			return;
		}
		show_navigation_dialog(frm);
	});

	const pod_label = frm.doc.date_pod_uploaded_on_erp ? __("📷 POD ✅") : __("📷 POD ⚠️");
	frm.add_custom_button(pod_label, () => show_pod_upload_dialog(frm));

	if (!frm.is_new())
		frm.add_custom_button(__("🖨️ Print"), () => {
			if (frm.is_dirty()) {
				frappe.show_alert({ message: __("💾 Please save the trip first."), indicator: "orange" }, 4);
				return;
			}
			frappe.utils.print("Trip", frm.doc.name, "Trip POD");
		});

	setTimeout(() => {
		_render_tcntrip_lock_checkbox(frm);
		update_pod_button_label(frm);
	}, 60);
	setTimeout(() => update_pod_button_label(frm), 350);
	setTimeout(() => update_pod_button_label(frm), 900);
}

// ══════════════════════════════════════════════════════════════════
//  NAVIGATION DIALOG
// ══════════════════════════════════════════════════════════════════

function show_navigation_dialog(frm) {
	// ── Theme ──────────────────────────────────────────────────
	const combo = frm._tms_resolved_combo || get_combo_for_trip(frm.doc.trip_type);
	const pri = (combo && combo.primary) ? combo.primary : "#3B4FE4";
	const cardBg = (combo && combo.card_bg) ? combo.card_bg : "#FFFFFF";
	const secBdr = (combo && combo.section_border) ? combo.section_border : "#C7D7FF";
	const fldBg = (combo && combo.field_bg) ? combo.field_bg : "#F0F4FF";
	const fldBdr = (combo && combo.field_border) ? combo.field_border : "#A5B4FC";
	const lblClr = (combo && combo.label_color) ? combo.label_color : "#3730A3";
	const hdgClr = (combo && combo.heading_color) ? combo.heading_color : "#1E1B4B";
	const radius = (combo && combo.radius) ? combo.radius : "10px";

	const pa = (a) => hex_alpha(pri, a);
	const priDark = darken(pri, 38);
	const priMid = darken(pri, 18);
	const isDark = get_luminance(pri) < 0.35;
	const hdrTxt = isDark ? "#FFFFFF" : "#0F172A";
	const hdrSub = isDark ? "rgba(255,255,255,0.72)" : "rgba(15,23,42,0.65)";
	const gradHdr = `linear-gradient(135deg, ${priDark} 0%, ${pri} 55%, ${priMid} 100%)`;

	// ── Trip label ─────────────────────────────────────────────
	const tripLbl = [frm.doc.origin_city, frm.doc.destination_city_1]
		.filter(Boolean).join(" → ") || frm.doc.so_no || frm.doc.name || "Trip";

	// ── Google Maps URL helpers (driving, India locale) ────────
	const ENC = encodeURIComponent;
	const LOCALE = "&hl=en&gl=in";
	const gm_place = (addr) => "https://maps.google.com/?q=" + ENC(addr) + "&hl=en&gl=in";
	const gm_route = (from, to) =>
		`https://maps.google.com/maps/dir/${ENC(from)}/${ENC(to)}/?travelmode=driving${LOCALE}`;
	const gm_multi = (pts) =>
		"https://maps.google.com/maps/dir/" + pts.filter(Boolean).map(ENC).join("/") +
		"/?travelmode=driving" + LOCALE;

	// ── CSS ────────────────────────────────────────────────────
	const CSS = `
<style>
#nc-root *, #nc-root *::before, #nc-root *::after { box-sizing:border-box; }
#nc-root {
	font-family:inherit; font-size:13px;
	--pri:${pri}; --card:${cardBg}; --bdr:${secBdr};
	--fbg:${fldBg}; --fbdr:${fldBdr}; --lbl:${lblClr}; --hdg:${hdgClr}; --r:${radius};
}
/* Header */
.nc-hdr {
	background:${gradHdr}; border-radius:10px 10px 0 0;
	padding:10px 14px; display:flex; align-items:center; gap:10px;
	margin:-4px -4px 0; position:relative; overflow:hidden;
}
.nc-hdr::before {
	content:""; position:absolute; inset:0; pointer-events:none;
	background:repeating-linear-gradient(-55deg,transparent 0px,transparent 20px,
		rgba(255,255,255,0.03) 20px,rgba(255,255,255,0.03) 40px);
}
.nc-hdr-icon {
	width:36px; height:36px; flex-shrink:0; font-size:20px;
	background:rgba(255,255,255,0.18); border-radius:9px;
	display:flex; align-items:center; justify-content:center;
	box-shadow:0 2px 8px rgba(0,0,0,0.20);
}
.nc-hdr-body { flex:1; min-width:0; }
.nc-hdr-title { font-size:13px; font-weight:800; color:${hdrTxt}; letter-spacing:-0.2px; }
.nc-hdr-sub   { font-size:10px; color:${hdrSub}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:1px; }
.nc-hdr-badge {
	background:rgba(255,255,255,0.18); border:1.5px solid rgba(255,255,255,0.32);
	color:${hdrTxt}; border-radius:20px; padding:2px 10px;
	font-size:9px; font-weight:700; flex-shrink:0; white-space:nowrap;
}
/* Map */
.nc-map {
	margin:0 -4px; position:relative;
	border-top:1px solid rgba(0,0,0,0.06); border-bottom:1px solid rgba(0,0,0,0.08);
}
#nc-leaflet-map { width:100%; height:230px; }
.nc-map-badge {
	position:absolute; bottom:28px; right:8px;
	background:rgba(0,0,0,0.55); color:#fff; border-radius:5px;
	font-size:9px; padding:2px 7px; pointer-events:none; z-index:999;
}
.nc-map-ph {
	width:100%; height:230px; display:flex; flex-direction:column;
	align-items:center; justify-content:center; gap:8px;
	background:${fldBg}; color:${lblClr}; font-size:11px;
}
/* Summary bar */
.nc-sum-wrap {
	background:var(--fbg); border-top:1px solid var(--bdr); border-bottom:1px solid var(--bdr);
	margin:0 -4px; padding:8px 14px; min-height:42px;
	display:flex; align-items:center;
}
.nc-sum-loading { font-size:11px; color:var(--lbl); display:flex; align-items:center; gap:7px; width:100%; }
.nc-sum-dot {
	display:inline-block; width:8px; height:8px; flex-shrink:0;
	border-radius:50%; background:var(--pri);
	animation:nc-pulse 1.2s ease-in-out infinite;
}
@keyframes nc-pulse { 0%,100%{opacity:.3;transform:scale(.8);} 50%{opacity:1;transform:scale(1.1);} }
.nc-sum { display:flex; width:100%; }
.nc-sum-item {
	flex:1; display:flex; align-items:center; gap:8px;
	padding:2px 10px; border-right:1px solid var(--bdr);
}
.nc-sum-item:first-child { padding-left:0; }
.nc-sum-item:last-child  { border-right:none; }
.nc-sum-ico { font-size:17px; flex-shrink:0; }
.nc-sum-val { font-size:13px; font-weight:800; color:var(--hdg); line-height:1.2; }
.nc-sum-lbl { font-size:8.5px; color:var(--lbl); text-transform:uppercase; letter-spacing:0.5px; margin-top:1px; }
.nc-sum-warn { font-size:10.5px; color:#92400E; }
/* Body */
.nc-body { padding:11px 2px 6px; }
.nc-sec {
	font-size:8.5px; font-weight:800; color:var(--lbl);
	text-transform:uppercase; letter-spacing:0.9px;
	display:flex; align-items:center; gap:6px; margin-bottom:6px;
}
.nc-sec::after { content:""; flex:1; height:1px; background:var(--bdr); border-radius:1px; }
.nc-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:10px; }
.nc-col  { display:flex; flex-direction:column; gap:5px; }
/* Address card */
.nc-addr {
	padding:9px 10px; background:var(--card);
	border:1.5px solid var(--bdr); border-radius:8px;
	transition:border-color .15s, box-shadow .15s;
}
.nc-addr:not(.nc-addr-empty):hover { border-color:var(--pri); box-shadow:0 3px 10px ${pa(.15)}; }
.nc-addr-empty { opacity:.45; }
.nc-arow { display:flex; align-items:flex-start; gap:7px; }
.nc-aicon { font-size:15px; flex-shrink:0; line-height:1.2; }
.nc-atxt  { flex:1; min-width:0; }
.nc-asub  { font-size:8px; font-weight:700; color:var(--lbl); text-transform:uppercase; letter-spacing:0.6px; margin-bottom:2px; }
.nc-atitle {
	font-size:11px; font-weight:600; color:var(--hdg); line-height:1.35;
	overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
}
.nc-atitle-mute { opacity:.45; font-style:italic; }
.nc-abtn-row { display:flex; gap:4px; margin-top:7px; }
.nc-view-btn {
	display:inline-flex; align-items:center; gap:4px; flex:1; justify-content:center;
	padding:4px 8px; background:var(--pri); color:#fff;
	border:none; border-radius:6px; cursor:pointer;
	font-size:10px; font-weight:700; transition:background .14s, transform .1s;
}
.nc-view-btn:hover { background:${priMid}; transform:translateY(-1px); }
.nc-view-btn:active { transform:none; }
.nc-copy-btn {
	width:26px; height:26px; flex-shrink:0;
	background:var(--fbg); border:1.5px solid var(--fbdr); border-radius:6px;
	cursor:pointer; display:flex; align-items:center; justify-content:center;
	color:var(--lbl); transition:all .14s;
}
.nc-copy-btn:hover { background:${pa(.10)}; border-color:var(--pri); color:var(--pri); }
.nc-copy-btn.copied { border-color:#22C55E; color:#16A34A; background:#F0FDF4; }
/* Route CTA */
.nc-cta {
	display:flex; align-items:center; gap:10px;
	padding:11px 14px; background:${gradHdr};
	border-radius:9px; text-decoration:none !important; width:100%;
	border:none; cursor:pointer;
	transition:filter .14s, transform .12s, box-shadow .15s;
	position:relative; overflow:hidden;
}
.nc-cta::before {
	content:""; position:absolute; inset:0; pointer-events:none;
	background:repeating-linear-gradient(-45deg,transparent 0px,transparent 12px,
		rgba(255,255,255,0.04) 12px,rgba(255,255,255,0.04) 24px);
}
.nc-cta:hover { filter:brightness(1.09); transform:translateY(-1px); box-shadow:0 7px 22px ${pa(.28)}; text-decoration:none !important; }
.nc-cta:active { transform:none; }
.nc-cta-icon { font-size:20px; flex-shrink:0; }
.nc-cta-info { flex:1; text-align:left; }
.nc-cta-title { font-size:12px; font-weight:800; color:${hdrTxt}; }
.nc-cta-sub   { font-size:9.5px; color:${hdrSub}; margin-top:1px; }
.nc-cta-arr {
	width:26px; height:26px; flex-shrink:0;
	background:rgba(255,255,255,0.20); border-radius:7px;
	display:flex; align-items:center; justify-content:center;
}
.nc-cta-arr svg { stroke:${isDark ? "rgba(255,255,255,0.85)" : "rgba(0,0,0,0.60)"}; }
.nc-no-route {
	padding:10px 12px; background:#FFFBEB; border:1.5px solid #FDE68A;
	border-radius:8px; font-size:11px; color:#92400E; line-height:1.5;
}
</style>`;

	// ── Dynamic skeleton — only show slots that have an address set ──
	const hasO1 = !!frm.doc.origin_address_1;
	const hasO2 = !!frm.doc.origin_address_2;
	const hasD1 = !!frm.doc.destination_address_1;
	const hasD2 = !!frm.doc.destination_address_2;

	function skel_card(icon, sub) {
		return `
		<div class="nc-addr nc-addr-empty">
			<div class="nc-arow">
				<span class="nc-aicon">${icon}</span>
				<div class="nc-atxt">
					<div class="nc-asub">${sub}</div>
					<div class="nc-atitle nc-atitle-mute">Loading…</div>
				</div>
			</div>
		</div>`;
	}

	const html = CSS + `
<div id="nc-root">
	<div class="nc-hdr">
		<div class="nc-hdr-icon">🚛</div>
		<div class="nc-hdr-body">
			<div class="nc-hdr-title">Truck Navigation</div>
			<div class="nc-hdr-sub">📍 ${frappe.utils.escape_html(tripLbl)}</div>
		</div>
		<span class="nc-hdr-badge">🛣️ Driving</span>
	</div>

	<div class="nc-map">
		<div id="nc-leaflet-map"><div class="nc-map-ph"><span style="font-size:28px;">🗺️</span><span>Loading map…</span></div></div>
		<div class="nc-map-badge">📍 OpenStreetMap</div>
	</div>

	<div id="nc-sum-wrap" class="nc-sum-wrap">
		<div class="nc-sum-loading"><span class="nc-sum-dot"></span> Calculating route…</div>
	</div>

	<div class="nc-body">
		<div class="nc-grid">
			<div class="nc-col">
				<div class="nc-sec">📍 Origin</div>
				${hasO1 ? `<div id="nc-o1">${skel_card("📍", "Addr 1")}</div>` : ""}
				${hasO2 ? `<div id="nc-o2">${skel_card("📍", "Addr 2")}</div>` : ""}
				${!hasO1 && !hasO2 ? `<div class="nc-addr nc-addr-empty"><div class="nc-arow"><span class="nc-aicon">📍</span><div class="nc-atxt"><div class="nc-atitle nc-atitle-mute">No origin set</div></div></div></div>` : ""}
			</div>
			<div class="nc-col">
				<div class="nc-sec">🏁 Destination</div>
				${hasD1 ? `<div id="nc-d1">${skel_card("🏁", "Addr 1")}</div>` : ""}
				${hasD2 ? `<div id="nc-d2">${skel_card("🏁", "Addr 2")}</div>` : ""}
				${!hasD1 && !hasD2 ? `<div class="nc-addr nc-addr-empty"><div class="nc-arow"><span class="nc-aicon">🏁</span><div class="nc-atxt"><div class="nc-atitle nc-atitle-mute">No destination set</div></div></div></div>` : ""}
			</div>
		</div>
		<div id="nc-cta-wrap"></div>
	</div>
</div>`;

	const dialog = new frappe.ui.Dialog({
		title: "",
		fields: [{ fieldname: "nav_html", fieldtype: "HTML", options: html }],
	});
	dialog.$wrapper.find(".modal-footer").hide();
	dialog.$wrapper.find(".modal-dialog").css({ "max-width": "520px", "width": "520px" });
	dialog.show();

	const $root = dialog.$wrapper.find("#nc-root");

	$root.on("click", ".nc-view-btn", function (e) {
		e.preventDefault();
		const addr = $(this).data("addr");
		if (addr) window.open(gm_place(addr), "_blank", "noopener");
	});

	$root.on("click", ".nc-copy-btn", function (e) {
		e.preventDefault();
		const $btn = $(this);
		const addr = $btn.data("addr") || $btn.closest(".nc-addr").data("addr") || "";
		if (!addr) return;
		const flash = () => {
			$btn.addClass("copied");
			frappe.show_alert({ message: "📋 Address copied!", indicator: "green" }, 2);
			setTimeout(() => $btn.removeClass("copied"), 2400);
		};
		if (navigator.clipboard && window.isSecureContext) {
			navigator.clipboard.writeText(addr).then(flash).catch(() => _nav_exec_copy(addr, flash));
		} else {
			_nav_exec_copy(addr, flash);
		}
	});

	// ── Async pipeline: labels → geocode → map + summary ──────
	_nc_load_nav(frm, $root, gm_place, gm_route, gm_multi);
}

// ── Address card HTML builder ──────────────────────────────────────
function _nc_addr_card_html(icon, sub, label) {
	if (!label) return `
	<div class="nc-addr nc-addr-empty">
		<div class="nc-arow">
			<span class="nc-aicon">${icon}</span>
			<div class="nc-atxt"><div class="nc-asub">${sub}</div><div class="nc-atitle nc-atitle-mute">Not set</div></div>
		</div>
	</div>`;
	const safe = frappe.utils.escape_html(label);
	return `
	<div class="nc-addr" data-addr="${safe}">
		<div class="nc-arow">
			<span class="nc-aicon">${icon}</span>
			<div class="nc-atxt">
				<div class="nc-asub">${sub}</div>
				<div class="nc-atitle" title="${safe}">${safe}</div>
			</div>
		</div>
		<div class="nc-abtn-row">
			<button class="nc-view-btn" data-addr="${safe}" title="Open in Google Maps">
				<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
				Maps
			</button>
			<button class="nc-copy-btn" data-addr="${safe}" title="Copy address">
				<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
			</button>
		</div>
	</div>`;
}

async function _nc_load_nav(frm, $root, gm_place, gm_route, gm_multi) {

    // ── 1. Resolve address display labels (server call) ──────────────
    const SLOTS = [
        { id: "nc-o1", fn: "origin_address_1",      cityFn: "origin_city",        icon: "📍", sub: "Origin — Addr 1",      side: "origin" },
        { id: "nc-o2", fn: "origin_address_2",      cityFn: "origin_city_2",      icon: "📍", sub: "Origin — Addr 2",      side: "origin" },
        { id: "nc-d1", fn: "destination_address_1", cityFn: "destination_city_1", icon: "🏁", sub: "Destination — Addr 1", side: "destination" },
        { id: "nc-d2", fn: "destination_address_2", cityFn: "destination_city_2", icon: "🏁", sub: "Destination — Addr 2", side: "destination" },
    ];

    const resolved = await Promise.all(SLOTS.map(sl => new Promise(resolve => {
        const docName = frm.doc[sl.fn];
        if (!docName) { resolve({ ...sl, label: "" }); return; }

        // Use cached description if available
        const fd = frm.fields_dict[sl.fn];
        const desc = (fd && fd.df && fd.df.description) ? fd.df.description.trim() : "";
        if (desc) { resolve({ ...sl, label: desc }); return; }

        frappe.call({
            method: "logicore.logicore.doctype.trip.trip.get_address_display_label",
            args: { address_name: docName },
            callback(r) { resolve({ ...sl, label: (r.message || docName).trim() }); },
            error()     { resolve({ ...sl, label: docName }); },
        });
    })));

    // ── 2. Populate address cards ────────────────────────────────────
    resolved.forEach(r => {
        $root.find("#" + r.id).html(_nc_addr_card_html(r.icon, r.sub, r.label));
    });

    // ── 3. Build Google Maps CTA using resolved labels ───────────────
    const origins = resolved.filter(r => r.side === "origin"      && r.label).map(r => r.label);
    const dests   = resolved.filter(r => r.side === "destination" && r.label).map(r => r.label);
    const allPts  = [...origins, ...dests];

    if (origins.length && dests.length) {
        const routeUrl = allPts.length === 2
            ? gm_route(allPts[0], allPts[1])
            : gm_multi(allPts);
        $root.find("#nc-cta-wrap").html(`
        <a class="nc-cta" href="${routeUrl}" target="_blank" rel="noopener noreferrer">
            <span class="nc-cta-icon">🛣️</span>
            <div class="nc-cta-info">
                <div class="nc-cta-title">Navigate Full Route in Google Maps</div>
                <div class="nc-cta-sub">${allPts.length} stop${allPts.length > 1 ? "s" : ""} · driving · opens Google Maps</div>
            </div>
            <span class="nc-cta-arr">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke-width="2.5">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                    <polyline points="15 3 21 3 21 9"/>
                    <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
            </span>
        </a>`);
    } else {
        $root.find("#nc-cta-wrap").html(`
        <div class="nc-no-route">⚠️ Set at least one origin and one destination address to enable route navigation.</div>`);
    }

    // ── 4. Need at least 2 addresses to show map/summary ────────────
    const filledPts = resolved.filter(r => r.label);
    if (filledPts.length < 2) {
        $root.find("#nc-sum-wrap").html(`<div class="nc-sum-warn">⚠️ Add at least 2 addresses to calculate route.</div>`);
        $root.find("#nc-leaflet-map").html(`<div class="nc-map-ph"><span style="font-size:28px;">🗺️</span><span>No route to display</span></div>`);
        return;
    }

    // ── 5. Geocode using resolved address labels (Nominatim) ─────────
    //       Stagger 1.1s between calls to respect rate limits.
    //       We geocode ALL 4 slots that have a label.
    // Helper: query Nominatim for a single string, return {lat,lon} or null
    async function _nominatim_query(queryStr) {
        try {
            const url = "https://nominatim.openstreetmap.org/search?q="
                      + encodeURIComponent(queryStr.trim() + ", India")
                      + "&format=json&limit=1&accept-language=en";
            const res = await fetch(url);
            if (!res.ok) return null;
            const data = await res.json();
            return (data && data[0]) ? { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon) } : null;
        } catch (_) { return null; }
    }

    let coords = [];
    try {
        const geoResults = await Promise.all(filledPts.map(async (pt, i) => {
            await new Promise(r => setTimeout(r, i * 1100));
            // First try full address label
            let geo = await _nominatim_query(pt.label.replace(/\s+/g, " "));
            // Fallback: try city name if full address geocoding failed
            if (!geo && pt.cityFn && frm.doc[pt.cityFn]) {
                await new Promise(r => setTimeout(r, 600));
                geo = await _nominatim_query(frm.doc[pt.cityFn]);
            }
            if (!geo) return null;
            return {
                lat:    geo.lat,
                lon:    geo.lon,
                addr:   pt.label,
                side:   pt.side,
                slotId: pt.id,
            };
        }));
        coords = geoResults.filter(Boolean);
    } catch (_) { coords = []; }

    const originCount = coords.filter(c => c.side === "origin").length;

    // ── 6. Single OSRM call for both geometry (map polyline) + stats ──
    if (coords.length < 2) {
        $root.find("#nc-sum-wrap").html(`<div class="nc-sum-warn">⚠️ Could not geocode addresses — check address data.</div>`);
        await _nc_render_map($root, coords, originCount, null);
        return;
    }

    let osrmRoute = null;
    try {
        const cStr    = coords.map(c => `${c.lon},${c.lat}`).join(";");
        const osrmRes = await fetch(
            `https://router.project-osrm.org/route/v1/driving/${cStr}?overview=full&geometries=geojson&steps=false`
        );
        const osrmData = await osrmRes.json();
        if (osrmData.code === "Ok" && osrmData.routes && osrmData.routes[0]) {
            osrmRoute = osrmData.routes[0];
        }
    } catch (_) { /* handled below */ }

    // ── 7. Render map using the geometry from the same OSRM response ──
    await _nc_render_map($root, coords, originCount, osrmRoute ? osrmRoute.geometry : null);

    // ── 8. Populate summary bar from the same OSRM response ───────────
    if (osrmRoute) {
        const distKm = Math.round(osrmRoute.distance / 1000);
        const durMin = Math.round(osrmRoute.duration / 60);
        const h      = Math.floor(durMin / 60);
        const m      = durMin % 60;
        const durStr = h > 0 ? `${h}h${m > 0 ? " " + m + "m" : ""}` : `${m}m`;

        const stopLines = coords.map(c => {
            const icon  = c.side === "origin" ? "📍" : "🏁";
            const short = c.addr.length > 42 ? c.addr.slice(0, 40) + "…" : c.addr;
            return `<div style="font-size:9.5px;color:var(--lbl);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${icon} ${frappe.utils.escape_html(short)}</div>`;
        }).join("");

        $root.find("#nc-sum-wrap").html(`
        <div style="width:100%;">
            <div class="nc-sum">
                <div class="nc-sum-item">
                    <span class="nc-sum-ico">🛣️</span>
                    <div>
                        <div class="nc-sum-val">${distKm.toLocaleString("en-IN")} km</div>
                        <div class="nc-sum-lbl">Distance</div>
                    </div>
                </div>
                <div class="nc-sum-item">
                    <span class="nc-sum-ico">⏱️</span>
                    <div>
                        <div class="nc-sum-val">${durStr}</div>
                        <div class="nc-sum-lbl">Est. Drive Time</div>
                    </div>
                </div>
                <div class="nc-sum-item">
                    <span class="nc-sum-ico">📍</span>
                    <div>
                        <div class="nc-sum-val">${coords.length} stop${coords.length > 1 ? "s" : ""}</div>
                        <div class="nc-sum-lbl">Addresses</div>
                    </div>
                </div>
                <div class="nc-sum-item">
                    <span class="nc-sum-ico">🚛</span>
                    <div>
                        <div class="nc-sum-val">Car / Truck</div>
                        <div class="nc-sum-lbl">Mode</div>
                    </div>
                </div>
            </div>
            <div style="padding:4px 14px 2px;border-top:1px solid var(--bdr);margin-top:4px;">${stopLines}</div>
        </div>`);
    } else {
        $root.find("#nc-sum-wrap").html(`<div class="nc-sum-warn">⚠️ Route data unavailable — check network.</div>`);
    }
}


// ── _nc_render_map stays the same — no changes needed ──────────────
// (markers use addr labels for popup text, which now come from addresses)

// ── Leaflet map renderer ───────────────────────────────────────────
// routeGeojson: pre-fetched GeoJSON geometry from the shared OSRM call (or null)
async function _nc_render_map($root, coords, originCount, routeGeojson) {
	const mapDiv = $root.find("#nc-leaflet-map")[0];

	if (!coords.length) {
		mapDiv.innerHTML = `<div class="nc-map-ph"><span style="font-size:28px;">🗺️</span><span>Could not plot addresses</span></div>`;
		return;
	}

	// Load Leaflet from CDN if not yet loaded
	if (!window.L) {
		await new Promise((resolve, reject) => {
			if (!document.getElementById("nc-leaflet-css")) {
				const link = document.createElement("link");
				link.id = "nc-leaflet-css";
				link.rel = "stylesheet";
				link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
				document.head.appendChild(link);
			}
			const script = document.createElement("script");
			script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
			script.onload = resolve;
			script.onerror = reject;
			document.head.appendChild(script);
		});
	}

	const L = window.L;
	mapDiv.innerHTML = "";
	mapDiv.style.height = "230px";

	const center = coords.length === 1
		? [coords[0].lat, coords[0].lon]
		: [coords.reduce((s, c) => s + c.lat, 0) / coords.length,
		coords.reduce((s, c) => s + c.lon, 0) / coords.length];

	const map = L.map(mapDiv, { zoomControl: true, attributionControl: true })
		.setView(center, coords.length === 1 ? 12 : 7);

	L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
		maxZoom: 18,
		attribution: '© <a href="https://www.openstreetmap.org/" target="_blank">OpenStreetMap</a>',
	}).addTo(map);

	// Markers — 📍 for origins, 🏁 for destinations
	coords.forEach((c, i) => {
		const emoji = i < originCount ? "📍" : "🏁";
		const icon = L.divIcon({
			html: `<div style="font-size:22px;line-height:1;filter:drop-shadow(0 1px 3px rgba(0,0,0,0.4));">${emoji}</div>`,
			className: "", iconSize: [26, 26], iconAnchor: [13, 24],
		});
		L.marker([c.lat, c.lon], { icon })
			.addTo(map)
			.bindPopup(`<b style="font-size:12px;">${frappe.utils.escape_html(c.addr)}</b>`);
	});

	// Route polyline — use pre-fetched geometry to stay in sync with summary stats
	if (coords.length >= 2) {
		if (routeGeojson) {
			try {
				const routeLayer = L.geoJSON(routeGeojson, {
					style: { color: "#3B4FE4", weight: 4, opacity: 0.85, lineJoin: "round", lineCap: "round" },
				}).addTo(map);
				map.fitBounds(routeLayer.getBounds(), { padding: [20, 20] });
			} catch (_) {
				map.fitBounds(L.latLngBounds(coords.map(c => [c.lat, c.lon])), { padding: [30, 30] });
			}
		} else {
			map.fitBounds(L.latLngBounds(coords.map(c => [c.lat, c.lon])), { padding: [30, 30] });
		}
	}
}

function _nav_exec_copy(text, cb) {
	const el = document.createElement("textarea");
	el.value = text; el.style.cssText = "position:fixed;opacity:0;pointer-events:none;";
	document.body.appendChild(el); el.select();
	try { document.execCommand("copy"); cb(); } catch (_) { }
	document.body.removeChild(el);
}

// ══════════════════════════════════════════════════════════════════
//  POD UPLOAD
// ══════════════════════════════════════════════════════════════════



// function show_pod_upload_dialog(frm) {
// 	if (frm.is_new()) {
// 		frappe.show_alert({ message: "⚠️ Please save the trip before uploading POD.", indicator: "orange" }, 4);
// 		return;
// 	}

// 	const dialog = new frappe.ui.Dialog({
// 		title: "📷 POD Manager",
// 		size: "small",
// 		fields: [
// 			{
// 				fieldname: "existing_pods", fieldtype: "HTML",
// 				options: `<div id="tms-pod-existing" style="margin-bottom:6px;"></div>`,
// 			},
// 			{ fieldname: "pod_type", fieldtype: "Select", label: "POD Type", options: "Original\nDuplicate", default: "Original", reqd: 1 },
// 			{ fieldname: "pod_date", fieldtype: "Date", label: "Upload Date", default: frappe.datetime.get_today(), reqd: 1 },
// 			{
// 				fieldname: "file_upload_section", fieldtype: "HTML",
// 				options: `
// 				<label for="tms-pod-file-input" id="tms-pod-upload-zone" style="display:block;border:2px dashed #A5B4FC;border-radius:8px;padding:18px 12px;text-align:center;cursor:pointer;background:#F0F4FF;margin:8px 0 2px;transition:background 0.2s,border-color 0.2s;">
// 					<div style="font-size:28px;margin-bottom:4px;">📁</div>
// 					<div style="font-weight:600;color:#3730A3;font-size:13px;">Click or drag to select POD file</div>
// 					<div style="color:#6B7280;font-size:11px;margin-top:2px;">JPEG · PNG · PDF — max 15 MB</div>
// 				</label>
// 				<input type="file" id="tms-pod-file-input" accept=".jpg,.jpeg,.png,.pdf" style="display:none;" />
// 				<div id="tms-pod-file-name" style="font-size:12px;color:#374151;margin-top:4px;display:none;padding:5px 10px;background:#F3F4F6;border-radius:6px;"></div>`,
// 			},
// 		],
// 		primary_action_label: "✅ Upload & Save",
// 		primary_action(vals) {
// 			const fileInput = dialog.$wrapper.find("#tms-pod-file-input")[0];
// 			if (!fileInput || !fileInput.files || !fileInput.files.length) {
// 				frappe.show_alert({ message: "⚠️ Please select a file to upload.", indicator: "orange" }, 4); return;
// 			}
// 			const file = fileInput.files[0];
// 			if (file.size > POD_MAX_BYTES) {
// 				frappe.show_alert({ message: "⚠️ File size exceeds 15 MB limit.", indicator: "red" }, 4); return;
// 			}
// 			dialog.hide();
// 			_upload_pod_file(frm, file, vals.pod_type, vals.pod_date);
// 		},
// 		secondary_action_label: "Close",
// 		secondary_action() {
// 			dialog.hide();
// 		}
// 	});

// 	dialog.show();

// 	// Load existing POD attachments
// 	frappe.call({
// 		method: "frappe.client.get_list",
// 		args: {
// 			doctype: "File",
// 			filters: { attached_to_doctype: frm.doctype, attached_to_name: frm.docname },
// 			fields: ["name", "file_name", "file_url", "creation"],
// 			order_by: "creation desc",
// 			limit: 50,
// 		},
// 		callback(r) {
// 			const files = (r.message || []).filter(f => /\.(jpg|jpeg|png|pdf)$/i.test(f.file_name || ""));
// 			const container = dialog.$wrapper.find("#tms-pod-existing");
// 			if (!files.length) {
// 				container.html(`<div style="font-size:12px;color:#9CA3AF;text-align:center;padding:6px 0 2px;">No POD files uploaded yet.</div>`);
// 				return;
// 			}
// 			const rows = files.map(f => {
// 				const ext = (f.file_name || "").split(".").pop().toUpperCase();
// 				const icon = ext === "PDF" ? "📄" : "🖼️";
// 				const safe = frappe.utils.escape_html(f.file_name || "file");
// 				const url = frappe.utils.escape_html(f.file_url || "");
// 				return `<div style="display:flex;align-items:center;gap:6px;padding:5px 8px;margin-bottom:4px;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;font-size:12px;">
// 					<span style="font-size:16px;">${icon}</span>
// 					<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#374151;" title="${safe}">${safe}</span>
// 					<a href="${url}" target="_blank" style="padding:2px 8px;background:#EEF2FF;color:#4F46E5;border-radius:4px;text-decoration:none;font-size:11px;font-weight:600;white-space:nowrap;">👁 View</a>
// 					<a href="${url}" download="${safe}" style="padding:2px 8px;background:#ECFDF5;color:#059669;border-radius:4px;text-decoration:none;font-size:11px;font-weight:600;white-space:nowrap;">⬇ Download</a>
// 				</div>`;
// 			}).join("");
// 			container.html(`
// 				<div style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Uploaded PODs (${files.length})</div>
// 				${rows}
// 				<hr style="margin:8px 0;border-color:#E5E7EB;">
// 			`);
// 		},
// 	});

// 	// Upload zone interactions — label handles click natively; JS only for drag-drop
// 	dialog.$wrapper.find("#tms-pod-upload-zone").on("dragover", function (e) {
// 		e.preventDefault(); $(this).css({ background: "#E0E7FF", "border-color": "#6366F1" });
// 	}).on("dragleave", function () {
// 		$(this).css({ background: "#F0F4FF", "border-color": "#A5B4FC" });
// 	}).on("drop", function (e) {
// 		e.preventDefault(); $(this).css({ background: "#F0F4FF", "border-color": "#A5B4FC" });
// 		const dt = e.originalEvent.dataTransfer;
// 		if (dt && dt.files && dt.files.length) {
// 			dialog.$wrapper.find("#tms-pod-file-input")[0].files = dt.files;
// 			_show_pod_filename(dialog, dt.files[0].name);
// 		}
// 	});
// 	dialog.$wrapper.find("#tms-pod-file-input").on("change", function () {
// 		if (this.files && this.files.length) _show_pod_filename(dialog, this.files[0].name);
// 	});
// }


// ══════════════════════════════════════════════════════════════════
//  POD MANAGER — Single upload, explicit delete-before-replace flow
// ══════════════════════════════════════════════════════════════════

// System Settings > Max File Size, the same limit Frappe's File doctype enforces
// server-side (frappe.core.api.file.get_max_file_size) — frappe.boot.max_file_size
// is already loaded at desk boot, so this stays in sync with the admin's setting
// without an extra round-trip.
function pod_max_bytes() {
    return frappe.boot.max_file_size || 25 * 1024 * 1024;
}
function pod_max_mb() {
    return Math.round(pod_max_bytes() / (1024 * 1024));
}

// Update frm.doc fields without triggering refresh (avoids re-dirtying the form)
function _pod_sync_frm(frm, fields) {
    Object.assign(frm.doc, fields);
    Object.keys(fields).forEach(k => frm.refresh_field(k));
    frm.doc.__unsaved = 0;
    if (frm.toolbar) frm.toolbar.set_indicator();
    if (frm.footer)  frm.footer.refresh();
}

function show_pod_upload_dialog(frm) {
    if (frm.is_new() || frm.is_dirty()) {
        frappe.msgprint({ title: __("Save Required"), message: __("Please save the trip before managing POD."), indicator: "orange" });
        return;
    }

    const canEditPOD = frappe.model.can_write("Trip") || frappe.model.can_create("Trip");

    const dialog = new frappe.ui.Dialog({
        title: "📷 POD Manager",
        size: "small",
        fields: [{
            fieldname: "pod_section", fieldtype: "HTML",
            options: '<div id="tms-pod-root" style="min-height:80px;padding:2px 0;"></div>',
        }],
        ...(canEditPOD ? {
            primary_action_label: "✅ Upload POD",
            primary_action() { _pod_do_upload(frm, dialog); },
        } : {}),
        secondary_action_label: "Close",
        secondary_action() { dialog.hide(); },
    });

    dialog.show();
    _pod_load_state(frm, dialog, canEditPOD);
}

// Load current POD state and render dialog
function _pod_load_state(frm, dialog, canEditPOD = false) {
    dialog.$wrapper.find("#tms-pod-root").html(
        '<div style="text-align:center;color:#9CA3AF;padding:24px 0;font-size:12px;">⏳ Loading…</div>'
    );
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "File",
            filters: { attached_to_doctype: frm.doctype, attached_to_name: frm.docname },
            fields: ["name", "file_name", "file_url", "file_size", "creation"],
            order_by: "creation desc",
            limit: 10,
        },
        callback(r) {
            const pods = (r.message || []).filter(f => /\.pdf$/i.test(f.file_name || ""));
            // Older PODs are kept as Trip attachments (history) — show only the newest here
            _pod_render(frm, dialog, pods.length ? pods[0] : null, canEditPOD);
        },
        error() {
            dialog.$wrapper.find("#tms-pod-root").html(
                '<div style="color:#DC2626;text-align:center;font-size:12px;padding:16px;">❌ Could not load POD status. Close and retry.</div>'
            );
        },
    });
}

// Render full dialog — existing POD card (if any) + upload form (write users only)
function _pod_render(frm, dialog, pod, canEditPOD = false) {
    const fmt_size = b => !b ? "" : b >= 1000000
        ? (b / 1048576).toFixed(1) + " MB"
        : (b / 1024).toFixed(0) + " KB";

    // Existing POD section (only if a file exists)
    let existingHtml = "";
    if (pod) {
        const safe = frappe.utils.escape_html(pod.file_name || "file");
        const url  = frappe.utils.escape_html(pod.file_url  || "");
        const size = fmt_size(pod.file_size);
        existingHtml = `
        <div style="margin-bottom:10px;">
            <div style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;
                        letter-spacing:.5px;margin-bottom:6px;">Uploaded POD</div>
            <div style="display:flex;align-items:center;gap:6px;padding:8px 10px;
                        background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;font-size:12px;">
                <span style="font-size:18px;">📄</span>
                <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                             color:#374151;" title="${safe}">${safe}</span>
                ${size ? `<span style="font-size:10px;color:#6B7280;background:#F3F4F6;
                    padding:1px 6px;border-radius:4px;white-space:nowrap;">${size}</span>` : ""}
                <a href="${url}" target="_blank"
                   style="padding:2px 8px;background:#EEF2FF;color:#4F46E5;border-radius:4px;
                          text-decoration:none;font-size:11px;font-weight:600;white-space:nowrap;">👁 View</a>
                <a href="${url}" download="${safe}"
                   style="padding:2px 8px;background:#ECFDF5;color:#059669;border-radius:4px;
                          text-decoration:none;font-size:11px;font-weight:600;white-space:nowrap;">⬇ Save</a>
            </div>
            ${canEditPOD ? `
            <button id="tms-pod-delete-btn" class="btn btn-sm"
                style="margin-top:6px;width:100%;background:#FEE2E2;color:#DC2626;
                       border:1px solid #FECACA;font-size:12px;padding:6px;border-radius:6px;">
                🗑 Delete This POD
            </button>
            <div id="tms-pod-delete-progress"
                 style="display:none;text-align:center;color:#6B7280;font-size:12px;margin-top:6px;">
                ⏳ Deleting…
            </div>` : ""}
            <hr style="margin:10px 0;border-color:#E5E7EB;">
        </div>`;
    }

    // Upload form — only for users with write access; zone locked when POD already exists
    const zoneLockedHtml = `
        <div id="tms-pod-upload-zone"
            style="border:2px dashed #D1D5DB;border-radius:8px;padding:18px 12px;
                   text-align:center;cursor:not-allowed;background:#F9FAFB;margin:4px 0;">
            <div style="font-size:28px;margin-bottom:4px;opacity:0.4;">🔒</div>
            <div style="font-weight:600;color:#9CA3AF;font-size:13px;">Delete existing POD to upload a new one</div>
        </div>`;

    const zoneActiveHtml = `
        <div id="tms-pod-upload-zone"
            style="border:2px dashed #A5B4FC;border-radius:8px;padding:18px 12px;
                   text-align:center;cursor:pointer;background:#F0F4FF;margin:4px 0;
                   transition:background 0.2s,border-color 0.2s;">
            <div style="font-size:28px;margin-bottom:4px;">📄</div>
            <div style="font-weight:600;color:#3730A3;font-size:13px;">Click or drag to select POD file</div>
            <div style="color:#6B7280;font-size:11px;margin-top:2px;">PDF only — max ${pod_max_mb()} MB</div>
        </div>`;

    const readOnlyNoPodHtml = `
        <div style="text-align:center;color:#9CA3AF;padding:20px 0;font-size:13px;">
            📭 No POD uploaded yet.
        </div>`;

    dialog.$wrapper.find("#tms-pod-root").html(`
        ${existingHtml}
        ${!pod && canEditPOD ? `<div style="font-size:12px;color:#9CA3AF;text-align:center;padding:0 0 10px;">No POD uploaded yet.</div>` : ""}
        ${!pod && !canEditPOD ? readOnlyNoPodHtml : ""}

        ${canEditPOD ? `
        <div style="margin-bottom:8px;">
            <label style="font-size:12px;font-weight:600;color:${pod ? "#9CA3AF" : "#374151"};display:block;margin-bottom:3px;">
                POD Type <span style="color:#EF4444;">*</span>
            </label>
            <select id="tms-pod-type" class="form-control form-control-sm" style="font-size:13px;" ${pod ? "disabled" : ""}>
                <option value="">-- Select Type --</option>
                <option value="Original">Original</option>
                <option value="Duplicate">Duplicate</option>
            </select>
        </div>

        <div style="margin-bottom:10px;">
            <label style="font-size:12px;font-weight:600;color:${pod ? "#9CA3AF" : "#374151"};display:block;margin-bottom:3px;">
                Upload Date <span style="color:#EF4444;">*</span>
            </label>
            <input type="date" id="tms-pod-date" class="form-control form-control-sm"
                   style="font-size:13px;" value="${frappe.datetime.get_today()}" ${pod ? "disabled" : ""} />
        </div>

        ${pod ? zoneLockedHtml : zoneActiveHtml}
        <input type="file" id="tms-pod-file-input" accept=".pdf,application/pdf" style="display:none;" ${pod ? "disabled" : ""} />
        <div id="tms-pod-file-name"
             style="font-size:12px;color:#374151;margin-top:4px;display:none;
                    padding:5px 10px;background:#F3F4F6;border-radius:6px;"></div>

        <div id="tms-pod-upload-progress" style="display:none;margin-top:8px;">
            <div style="background:#E5E7EB;border-radius:6px;overflow:hidden;height:8px;">
                <div id="tms-pod-progress-bar"
                     style="height:100%;width:0%;background:#6366F1;border-radius:6px;
                            transition:width 0.3s ease;"></div>
            </div>
            <div id="tms-pod-progress-text"
                 style="font-size:11px;color:#6B7280;margin-top:4px;text-align:center;">
                Uploading…
            </div>
        </div>
        ` : ""}
    `);

    // Wire delete button (only present when pod exists and user has write access)
    if (pod && canEditPOD) {
        const safe = frappe.utils.escape_html(pod.file_name || "file");
        dialog.$wrapper.find("#tms-pod-delete-btn").on("click", function () {
            const $btn = $(this);
            frappe.confirm(`Delete <b>${safe}</b> permanently?`, () => {
                $btn.prop("disabled", true);
                dialog.$wrapper.find("#tms-pod-delete-progress").show();
                frappe.call({
                    method: "logicore.logicore.doctype.trip.trip.delete_pod_files",
                    args: { docname: frm.docname },
                    callback() {
                        frappe.show_alert({ message: "✅ POD deleted.", indicator: "green" }, 3);
                        frappe.call({
                            method: "logicore.logicore.doctype.trip.trip.reset_pod_status",
                            args: { docname: frm.docname },
                            callback() {
                                _pod_sync_frm(frm, {
                                    date_pod_uploaded_on_erp:       null,
                                    uploaded_pod_originalduplicate: null,
                                    pod_status:                     "POD Not Uploaded",
                                });
                                update_trip_status_display(frm);
                                highlight_active_tab(frm);
                                update_pod_button_label(frm);
                                _pod_load_state(frm, dialog, canEditPOD);
                            },
                        });
                    },
                    error() {
                        frappe.show_alert({ message: "❌ Could not delete POD.", indicator: "red" }, 4);
                        $btn.prop("disabled", false);
                        dialog.$wrapper.find("#tms-pod-delete-progress").hide();
                    },
                });
            });
        });
    }

    // Upload button: disabled when POD exists (must delete first); hidden for read-only users
    if (canEditPOD) dialog.get_primary_btn().prop("disabled", !!pod);

    if (!pod) {
        // Wire upload zone — click + drag-drop only when no existing POD
        dialog.$wrapper.find("#tms-pod-upload-zone")
            .on("click", () => dialog.$wrapper.find("#tms-pod-file-input")[0].click())
            .on("dragover", e => {
                e.preventDefault();
                $(e.currentTarget).css({ background: "#E0E7FF", "border-color": "#6366F1" });
            })
            .on("dragleave", e => {
                $(e.currentTarget).css({ background: "#F0F4FF", "border-color": "#A5B4FC" });
            })
            .on("drop", e => {
                e.preventDefault();
                $(e.currentTarget).css({ background: "#F0F4FF", "border-color": "#A5B4FC" });
                const f = e.originalEvent?.dataTransfer?.files?.[0];
                if (f) _pod_validate_and_stage(dialog, f);
            });

        dialog.$wrapper.find("#tms-pod-file-input").on("change", function () {
            if (this.files && this.files.length) _pod_validate_and_stage(dialog, this.files[0]);
        });
    }
}

// Validate selected file and stage it on the input element
function _pod_validate_and_stage(dialog, f) {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
        _show_pod_file_error(dialog, f.name);
        dialog.$wrapper.find("#tms-pod-file-input").val("");
        return;
    }
    if (f.size > pod_max_bytes()) {
        _show_pod_size_error(dialog, f.name, f.size);
        dialog.$wrapper.find("#tms-pod-file-input").val("");
        return;
    }
    try {
        const dt = new DataTransfer();
        dt.items.add(f);
        dialog.$wrapper.find("#tms-pod-file-input")[0].files = dt.files;
    } catch (_) {}
    _show_pod_filename(dialog, f.name);
}

// Primary action: validate everything then upload
function _pod_do_upload(frm, dialog) {
    // Re-check trip saved state (might have changed since dialog opened)
    if (frm.is_new()) {
        frappe.msgprint({ title: __("Save Required"), message: __("Please save the trip first."), indicator: "orange" });
        return;
    }

    // POD Type mandatory
    const pod_type = dialog.$wrapper.find("#tms-pod-type").val();
    if (!pod_type) {
        frappe.show_alert({ message: "⚠️ Please select POD Type (Original / Duplicate).", indicator: "orange" }, 4);
        return;
    }

    // Arrival + Release date required — only if those fields are visible per Trip Settings
    const isVisible = fn => frm.fields_dict[fn] && !frm.get_field(fn).df.hidden;
    const needArrival = isVisible("arrival_date_time") && !frm.doc.arrival_date_time;
    const needRelease = isVisible("release_date_time") && !frm.doc.release_date_time;
    if (needArrival || needRelease) {
        frappe.msgprint({
            title: __("POD Upload Not Allowed"),
            message: __(
                "POD cannot be uploaded until <b>Arrival Date/Time</b> and "
                + "<b>Release Date/Time</b> at the Unloading Site have been filled."
            ),
            indicator: "red",
        });
        return;
    }

    const fileInput = dialog.$wrapper.find("#tms-pod-file-input")[0];
    if (!fileInput || !fileInput.files || !fileInput.files.length) {
        frappe.show_alert({ message: "⚠️ Please select a PDF file first.", indicator: "orange" }, 4);
        return;
    }
    const file = fileInput.files[0];
    if (!file.name.toLowerCase().endsWith(".pdf")) {
        frappe.show_alert({ message: "❌ Only PDF files are allowed.", indicator: "red" }, 4);
        return;
    }
    if (file.size > pod_max_bytes()) {
        frappe.show_alert({ message: `❌ File too large. Maximum allowed is ${pod_max_mb()} MB.`, indicator: "red" }, 5);
        return;
    }
    const pod_date = dialog.$wrapper.find("#tms-pod-date").val()  || frappe.datetime.get_today();

    const $btn  = dialog.get_primary_btn();
    const $bar  = dialog.$wrapper.find("#tms-pod-progress-bar");
    const $txt  = dialog.$wrapper.find("#tms-pod-progress-text");
    const $prog = dialog.$wrapper.find("#tms-pod-upload-progress");

    $btn.html("⏳ Processing…").prop("disabled", true);
    $prog.show();

    const setUI = (pct, text) => { $bar.css("width", pct + "%"); $txt.text(text); };

    const finish = (success) => {
        $btn.html("✅ Upload POD").prop("disabled", false);
        $prog.hide(); $bar.css("width", "0%");
        if (success) {
            // Reload state — will show new POD in "existing" view
            setTimeout(() => _pod_load_state(frm, dialog), 600);
        }
        // On failure: keep upload form visible so user can retry
    };

    // Manual POD Manager upload on the Trip form no longer enforces the
    // bulk-import filename-matches-trip-reference rule — any PDF name is
    // accepted here. (Previous validate_pod_file_name call left commented
    // below in case the rule needs to come back.)
    //
    // setUI(5, "Validating file name…");
    // frappe.call({
    //     method: "logicore.logicore.doctype.trip.trip.validate_pod_file_name",
    //     args: { docname: frm.docname, file_name: file.name },
    //     error() { finish(false); },
    //     callback(r) {
    //         if (r.exc) { finish(false); return; }
    //         setUI(10, "Starting…");
    //         _upload_pod_file_v2(frm, file, pod_type, pod_date, dialog, finish, setUI);
    //     },
    // });

    setUI(10, "Starting…");
    _upload_pod_file_v2(frm, file, pod_type, pod_date, dialog, finish, setUI);
}

// ── Client-side PDF compression using PDF.js + jsPDF ──────────────
function _load_script(src) {
    return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${src}"]`)) { resolve(); return; }
        const s = document.createElement("script");
        s.src = src; s.onload = resolve; s.onerror = reject;
        document.head.appendChild(s);
    });
}

async function _compress_pdf_client(file, onProgress) {
    // Load PDF.js (bundled with Frappe)
    if (!window.pdfjsLib) {
        await _load_script("/assets/frappe/js/pdfjs/pdf.min.js");
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = "/assets/frappe/js/pdfjs/pdf.worker.min.js";
    }
    // Load jsPDF
    if (!window.jspdf) {
        await _load_script("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js");
    }

    onProgress(5, "Reading PDF…");
    const buf    = await file.arrayBuffer();
    const srcPdf = await window.pdfjsLib.getDocument({ data: buf }).promise;
    const total  = srcPdf.numPages;
    const { jsPDF } = window.jspdf;

    let outPdf = null;
    for (let i = 1; i <= total; i++) {
        onProgress(Math.round(5 + (i - 1) / total * 88), `Compressing page ${i} of ${total}…`);
        const page = await srcPdf.getPage(i);
        const vp1  = page.getViewport({ scale: 1 });
        const vp   = page.getViewport({ scale: 1.5 }); // ~108 DPI

        const canvas  = document.createElement("canvas");
        canvas.width  = vp.width;
        canvas.height = vp.height;
        await page.render({ canvasContext: canvas.getContext("2d"), viewport: vp }).promise;

        const imgData = canvas.toDataURL("image/jpeg", 0.60); // 50-70% size reduction
        const wMM = vp1.width  * 0.352778; // pt → mm
        const hMM = vp1.height * 0.352778;

        if (!outPdf) outPdf = new jsPDF({ unit: "mm", format: [wMM, hMM], compress: true });
        else outPdf.addPage([wMM, hMM]);
        outPdf.addImage(imgData, "JPEG", 0, 0, wMM, hMM);
    }

    onProgress(95, "Finalizing…");
    const blob = outPdf.output("blob");
    return new File([blob], file.name, { type: "application/pdf" });
}


// ── Reset file input so the same file can be re-selected ──────────
function _reset_pod_file_input(dialog) {
    const $old = dialog.$wrapper.find("#tms-pod-file-input");
    // Replacing the element is the only reliable cross-browser reset
    const $new = $old.clone(false);
    $old.replaceWith($new);
    $new.on("change", function () {
        if (this.files && this.files.length) _show_pod_filename(dialog, this.files[0].name);
    });

    dialog.$wrapper.find("#tms-pod-upload-zone")
        .css({ background: "#F0F4FF", "border-color": "#A5B4FC" })
        .find("div").eq(1).text("Click or drag to select POD file");

    dialog.$wrapper.find("#tms-pod-file-name").hide().text("").css("color", "#374151");
}

function _show_pod_filename(dialog, name) {
    dialog.$wrapper.find("#tms-pod-file-name")
        .text("📎 " + name)
        .css("color", "#065F46")
        .show();
    dialog.$wrapper.find("#tms-pod-upload-zone")
        .css({ background: "#ECFDF5", "border-color": "#22C55E" })
        .find("div").eq(1).text("✅ File ready — click Upload POD");
}

function _show_pod_file_error(dialog, name) {
    const ext = name.split(".").pop().toUpperCase();
    dialog.$wrapper.find("#tms-pod-file-name")
        .text(`❌ "${name}" is not a PDF file. Please select a PDF.`)
        .css("color", "#B91C1C")
        .show();
    dialog.$wrapper.find("#tms-pod-upload-zone")
        .css({ background: "#FEF2F2", "border-color": "#EF4444" })
        .find("div").eq(1).text(`❌ ${ext} format not allowed — PDF only`);
}

function _show_pod_size_error(dialog, name, size) {
    const mb = (size / (1024 * 1024)).toFixed(1);
    const maxMb = pod_max_mb();
    dialog.$wrapper.find("#tms-pod-file-name")
        .text(`❌ File is ${mb} MB. Maximum allowed size is ${maxMb} MB.`)
        .css("color", "#B91C1C")
        .show();
    dialog.$wrapper.find("#tms-pod-upload-zone")
        .css({ background: "#FEF2F2", "border-color": "#EF4444" })
        .find("div").eq(1).text(`❌ File too large (${mb} MB) — max ${maxMb} MB`);
}

// ── Core upload — called after client-side compression ─────────────
function _upload_pod_file_v2(frm, file, pod_type, pod_date, dialog, callback, setUI) {
    setUI = setUI || function(pct, text) {
        dialog.$wrapper.find("#tms-pod-progress-bar").css("width", pct + "%");
        dialog.$wrapper.find("#tms-pod-progress-text").text(text);
    };

    setUI(10, "Deleting old POD…");
    frappe.call({
        method: "logicore.logicore.doctype.trip.trip.delete_pod_files",
        args: { docname: frm.docname },
        callback() {
            setUI(30, "Uploading file…");

            const fd = new FormData();
            const uniqueName = `POD_${frm.docname}_${Date.now()}.pdf`;
            fd.append("file", file, uniqueName);
            fd.append("doctype", frm.doctype);
            fd.append("docname", frm.docname);
            fd.append("folder", "Home/Attachments");
            fd.append("is_private", "0");

            fetch("/api/method/upload_file", {
                method: "POST",
                headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
                body: fd,
            })
            .then(r => r.json())
            .then(data => {
                if (data.exc || !data.message) {
                    frappe.show_alert({ message: "❌ POD upload failed. Please try again.", indicator: "red" }, 5);
                    callback(false);
                    return;
                }

                const file_doc = data.message;
                file_doc.file_name = file.name; // show original name in toast
                setUI(60, "Compressing PDF…");

                // Ghostscript server-side compression (synchronous)
                frappe.call({
                    method: "logicore.logicore.api.compress_pod_pdf",
                    args: { file_doc_name: file_doc.name, original_name: file.name },
                    callback(cr) {
                        const res = cr.message || {};
                        const fmt = b => (b / (1024 * 1024)).toFixed(1) + " MB";
                        const orig = fmt(res.original_size || file.size);
                        const final = fmt(res.final_size || file.size);
                        const size_info = `${orig} → ${final}`;

                        setUI(90, "Saving…");
                        const resolved_type = pod_type || "Original";
                        const resolved_date = pod_date || frappe.datetime.get_today();
                        frappe.call({
                            method: "logicore.logicore.doctype.trip.trip.set_pod_status",
                            args: {
                                docname:  frm.docname,
                                pod_date: resolved_date,
                                pod_type: resolved_type,
                            },
                            callback() {
                                setUI(100, "Done!");
                                frappe.show_alert({
                                    message: `✅ POD uploaded: <b>${file_doc.file_name}</b> (${size_info})`,
                                    indicator: "green"
                                }, 5);
                                const pod_status_val = resolved_type === "Duplicate"
                                    ? "Duplicate POD Uploaded" : "Original POD Uploaded";
                                _pod_sync_frm(frm, {
                                    date_pod_uploaded_on_erp:       resolved_date,
                                    uploaded_pod_originalduplicate: resolved_type,
                                    pod_status:                     pod_status_val,
                                });
                                update_trip_status_display(frm);
                                highlight_active_tab(frm);
                                update_pod_button_label(frm);
                                callback(true);
                            },
                        });
                    }
                });
            })
            .catch(() => {
                frappe.show_alert({ message: "❌ POD upload failed. Please try again.", indicator: "red" }, 5);
                callback(false);
            });
        },
        error() {
            frappe.show_alert({ message: "❌ Could not delete old POD. Please try again.", indicator: "red" }, 5);
            callback(false);
        }
    });
}
function _upload_pod_file(frm, file, pod_type, pod_date) {
	frappe.show_alert({ message: "⏳ Uploading POD…", indicator: "blue" }, 3);
	// Step 1: delete existing POD files
	frappe.call({
		method: "logicore.logicore.doctype.trip.trip.delete_pod_files",
		args: { docname: frm.docname },
		callback() {
			// Step 2: upload directly — no intermediate Frappe dialog, always public
			const fd = new FormData();
			fd.append("file", file, file.name);
			fd.append("doctype", frm.doctype);
			fd.append("docname", frm.docname);
			fd.append("folder", "Home/Attachments");
			fd.append("is_private", "0");

			fetch("/api/method/upload_file", {
				method: "POST",
				headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
				body: fd,
			})
				.then(r => r.json())
				.then(data => {
					if (data.exc || !data.message) {
						frappe.show_alert({ message: "❌ POD upload failed. Please try again.", indicator: "red" }, 5);
						console.error("POD upload error:", data.exc || data);
						return;
					}
					const file_doc = data.message;
					frm.set_value("date_pod_uploaded_on_erp", pod_date || frappe.datetime.get_today());
					frm.set_value("uploaded_pod_originalduplicate", pod_type || "Original");
					// frm.set_value("pod_status", "Uploaded");
					const pod_status_val = (pod_type || "Original") === "Duplicate"
						? "Duplicate POD Uploaded" : "Original POD Uploaded";
					frm.set_value("pod_status", pod_status_val);
					frappe.show_alert({ message: `✅ POD uploaded: <b>${file_doc.file_name}</b>`, indicator: "green" }, 5);
					update_trip_status_display(frm); highlight_active_tab(frm);
					frm.save().then(() => {
						frappe.show_alert({ message: "💾 Trip saved with POD.", indicator: "green" }, 3);
						frm.reload_doc();
					});
				})
				.catch(err => {
					frappe.show_alert({ message: "❌ POD upload failed. Please try again.", indicator: "red" }, 5);
					console.error("POD upload error:", err);
				});
		},
	});
}

// ══════════════════════════════════════════════════════════════════
//  EMAIL TEMPLATE DIALOG  —  Compact Split-pane: Edit | Help | Preview
// ══════════════════════════════════════════════════════════════════

const ETPL_PREVIEW_REQUIRED = [
	{ fieldname: "origin_city", label: "Origin City" },
	{ fieldname: "destination_city_1", label: "Destination City" },
	{ fieldname: "customer", label: "Customer" },
	{ fieldname: "vendor", label: "Vendor" },
];

function show_email_template_dialog(frm) {
	const tripType = frm.doc.trip_type || "";

	const missing = _etpl2_get_missing(frm);
	if (missing.length) {
		frappe.show_alert({
			message: `⚠️ Preview will show blank values for: <b>${missing.join(", ")}</b>. Fill these fields for a meaningful preview.`,
			indicator: "orange",
		}, 7);
	}

	Promise.all([
		new Promise(resolve =>
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Email Template",
					fields: ["name"],
					filters: tripType ? [["custom_trip_type", "=", tripType]] : [],
					limit_page_length: 100,
				},
				callback(r) { resolve(r.message || []); },
			})
		),
		new Promise(resolve =>
			frappe.call({
				method: "logicore.logicore.doctype.trip_settings.trip_settings.get_trip_fields",
				callback(r) { resolve(r.message || []); },
				error() { resolve([]); },
			})
		),
		new Promise(resolve => {
			if (frm._tms_field_config !== undefined) {
				resolve(frm._tms_field_config || null);
			} else if (!tripType) {
				resolve(null);
			} else {
				frappe.call({
					method: "logicore.logicore.doctype.trip_settings.trip_settings.get_field_config",
					args: { trip_type: tripType },
					callback(r) { resolve(r.message || null); },
					error() { resolve(null); },
				});
			}
		}),
	]).then(([templates, trip_tabs, field_config]) => {
		let visibleSet = null;
		if (field_config && Array.isArray(field_config.fields) && field_config.fields.length) {
			visibleSet = new Set(
				field_config.fields.filter(r => r.is_visible).map(r => r.fieldname)
			);
		}
		const canEdit = frappe.model.can_write("Email Template")
			|| frappe.model.can_create("Email Template");
		_build_etpl_dialog(frm, templates, trip_tabs, visibleSet, canEdit);
	});
}

function _etpl_colors(trip_type, override_color) {
	const combo = get_combo_for_trip(trip_type || "Other");
	const pri = (override_color && override_color.trim()) ? override_color.trim()
		: (combo ? combo.primary : "#3B4FE4");
	return {
		pri,
		light: hex_alpha(pri, 0.09),
		mid: hex_alpha(pri, 0.16),
		border: hex_alpha(pri, 0.28),
		dark: darken(pri, 28),
		text: combo ? combo.heading_color : "#1E1B4B",
		label: combo ? combo.label_color : "#3730A3",
		fieldBg: combo ? combo.field_bg : "#F0F4FF",
		fieldBr: override_color ? hex_alpha(pri, 0.50) : (combo ? combo.field_border : "#A5B4FC"),
	};
}

function _build_etpl_dialog(frm, templates, trip_tabs, visibleSet, canEdit = false) {
	const C = _etpl_colors(frm.doc.trip_type, frm._tms_resolved_color || null);
	const ttMeta = TRIP_TYPE_META[frm.doc.trip_type] || { icon: "🚛" };
	const tripType = frm.doc.trip_type || "";

	let autoName = frm.doc.__email_template || "";
	if (!autoName && templates.length) {
		const match = tripType && templates.find(t =>
			t.name.toLowerCase().includes(tripType.toLowerCase())
		);
		autoName = (match || templates[0]).name;
	}

	let totalVisible = 0;
	const helpGroups = (trip_tabs || []).map(tab => {
		const allFields = tab.fields || [];
		const vis = visibleSet ? allFields.filter(f => visibleSet.has(f.fieldname)) : allFields;
		if (!vis.length) return null;
		totalVisible += vis.length;
		return { icon: tab.icon || "📋", label: tab.tab_label || tab.label || "Tab", fields: vis };
	}).filter(Boolean);

	const helpListHtml = helpGroups.map(g => `
		<div class="etpl2-group">
			<div class="etpl2-group-title">${g.icon} ${frappe.utils.escape_html(g.label)}</div>
			${g.fields.map(f => `
			<div class="etpl2-field-row" data-var="{{ doc.${f.fieldname} }}" data-label="${frappe.utils.escape_html
				
				(f.label || f.fieldname)}">
				<span class="etpl2-field-label">${frappe.utils.escape_html(f.label || f.fieldname)}</span>
				<code class="etpl2-field-code">{{ doc.${f.fieldname} }}</code>
				<button class="etpl2-insert-btn" title="Insert at cursor in Body">⊕</button>
			</div>`).join("")}
		</div>`).join("") || `<div class="etpl2-empty">⚙️ No visible fields configured for this trip type.</div>`;

	const scopeNote = visibleSet
		? `${totalVisible} field${totalVisible !== 1 ? "s" : ""} · <b>${frappe.utils.escape_html(tripType || "All")}</b>`
		: `All fields`;

	const optionsHtml = templates.map(t =>
		`<option value="${frappe.utils.escape_html(t.name)}"${t.name === autoName ? " selected" : ""}>${frappe.utils.escape_html(t.name)}</option>`
	).join("");

	const gradHdr = `linear-gradient(135deg, ${darken(C.pri, 36)} 0%, ${C.pri} 100%)`;

	const dialog = new frappe.ui.Dialog({
		title: "",
		fields: [{
			fieldname: "etpl2_ui",
			fieldtype: "HTML",
			options: `
<style>
#etpl2-root *, #etpl2-root *::before, #etpl2-root *::after { box-sizing: border-box; }
#etpl2-root {
	font-family: inherit; font-size: 12px; color: ${C.text};
	--pri: ${C.pri}; --border: ${C.border}; --light: ${C.light}; --mid: ${C.mid};
	--fieldBg: ${C.fieldBg}; --fieldBr: ${C.fieldBr};
}
.etpl2-header {
	background: ${gradHdr}; border-radius: 8px 8px 0 0;
	padding: 8px 12px; display: flex; align-items: center; gap: 8px;
	margin: -4px -4px 0;
}
.etpl2-header-icon {
	width: 28px; height: 28px; background: rgba(255,255,255,0.18);
	border-radius: 6px; display: flex; align-items: center; justify-content: center;
	font-size: 14px; flex-shrink: 0;
}
.etpl2-header-info { flex: 1; min-width: 0; }
.etpl2-header-title { font-size: 12px; font-weight: 700; color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,0.3); }
.etpl2-header-sub   { font-size: 10px; color: rgba(255,255,255,0.72); margin-top: 1px; }
.etpl2-header-new-btn {
	background: rgba(255,255,255,0.18); border: 1.5px solid rgba(255,255,255,0.38);
	color: #fff; border-radius: 5px; padding: 3px 10px; font-size: 10px; font-weight: 600;
	cursor: pointer; white-space: nowrap; transition: background 0.15s;
}
.etpl2-header-new-btn:hover { background: rgba(255,255,255,0.32); }
.etpl2-selector { display: flex; align-items: center; gap: 6px; padding: 7px 0 4px; }
.etpl2-selector label {
	font-size: 9px; font-weight: 700; color: ${C.label};
	text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; flex-shrink: 0;
}
.etpl2-tpl-select {
	flex: 1; height: 28px; padding: 0 8px;
	border: 1.5px solid var(--fieldBr); border-radius: 6px;
	background: var(--fieldBg); color: ${C.text}; font-size: 11px;
	outline: none; cursor: pointer; transition: border-color 0.2s, box-shadow 0.2s;
}
.etpl2-tpl-select:focus { border-color: var(--pri); box-shadow: 0 0 0 2px ${hex_alpha(C.pri, 0.14)}; }
.etpl2-tabs {
	display: flex; gap: 3px; padding: 0 0 8px;
	border-bottom: 1.5px solid var(--border); margin-bottom: 8px;
}
.etpl2-tab {
	padding: 4px 12px; border-radius: 5px; font-size: 11px; font-weight: 600;
	cursor: pointer; border: 1.5px solid transparent; color: ${C.label};
	background: transparent; transition: all 0.15s; white-space: nowrap; display: flex; align-items: center; gap: 5px;
}
.etpl2-tab:hover { background: var(--light); border-color: var(--border); }
.etpl2-tab.etpl2-active {
	background: ${C.pri}; color: #fff; border-color: ${C.dark};
	box-shadow: 0 2px 6px ${hex_alpha(C.pri, 0.28)};
}
.etpl2-tab-badge {
	display: none; background: rgba(255,255,255,0.28); border-radius: 10px;
	padding: 1px 6px; font-size: 9px; font-weight: 700;
}
.etpl2-tab:not(.etpl2-active) .etpl2-tab-badge { background: var(--mid); color: ${C.pri}; }
.etpl2-body { display: flex; gap: 10px; height: 360px; overflow: hidden; }
.etpl2-edit-pane {
	flex: 1 1 54%; display: flex; flex-direction: column; gap: 7px;
	min-width: 0; overflow-y: auto; padding-right: 2px;
}
.etpl2-edit-pane::-webkit-scrollbar { width: 4px; }
.etpl2-edit-pane::-webkit-scrollbar-track { background: transparent; }
.etpl2-edit-pane::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.etpl2-field-block { display: flex; flex-direction: column; gap: 3px; }
.etpl2-lbl {
	font-size: 9px; font-weight: 700; color: ${C.label};
	text-transform: uppercase; letter-spacing: 0.5px;
}
.etpl2-lbl-sub { font-weight: 400; text-transform: none; letter-spacing: 0; font-size: 9px; opacity: 0.65; }
.etpl2-input {
	width: 100%; padding: 5px 8px;
	border: 1.5px solid var(--fieldBr); border-radius: 6px;
	background: var(--fieldBg); color: ${C.text}; font-size: 11.5px;
	font-family: inherit; outline: none; transition: border-color 0.2s, box-shadow 0.2s;
}
.etpl2-input:focus { border-color: var(--pri); box-shadow: 0 0 0 2px ${hex_alpha(C.pri, 0.14)}; }
.etpl2-textarea {
	flex: 1; resize: none; min-height: 200px;
	font-family: 'Consolas', 'Cascadia Code', 'Monaco', monospace;
	font-size: 11px; line-height: 1.65;
}
.etpl2-textarea::placeholder { color: #9CA3AF; font-family: inherit; }
.etpl2-save-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; flex-shrink: 0; padding-bottom: 4px; }
.etpl2-save-btn {
	background: ${C.pri}; color: #fff; border: none; border-radius: 6px;
	padding: 5px 14px; font-size: 11px; font-weight: 700; cursor: pointer;
	transition: background 0.15s, box-shadow 0.15s; display: flex; align-items: center; gap: 5px;
	white-space: nowrap; flex-shrink: 0;
}
.etpl2-save-btn:hover:not(:disabled) { background: ${C.dark}; box-shadow: 0 2px 8px ${hex_alpha(C.pri, 0.32)}; }
.etpl2-save-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.etpl2-saved-badge {
	display: none; font-size: 10px; font-weight: 600; color: #059669;
	background: #ECFDF5; border: 1.5px solid #A7F3D0; border-radius: 5px; padding: 3px 8px;
}
.etpl2-hint { flex: 1; font-size: 9.5px; color: ${C.label}; opacity: 0.8; line-height: 1.5; }
.etpl2-hint code { background: var(--mid); border-radius: 3px; padding: 1px 4px; color: ${C.pri}; font-size: 9px; }
.etpl2-divider { width: 1.5px; background: var(--border); flex-shrink: 0; border-radius: 2px; align-self: stretch; }
.etpl2-help-pane { flex: 0 0 36%; display: flex; flex-direction: column; min-width: 0; }
.etpl2-help-header {
	display: flex; align-items: center; justify-content: space-between;
	gap: 6px; padding-bottom: 4px; flex-shrink: 0;
}
.etpl2-help-title { font-size: 9px; font-weight: 700; color: ${C.label}; text-transform: uppercase; letter-spacing: 0.5px; }
.etpl2-help-scope {
	font-size: 9px; color: ${C.label}; background: var(--mid); border-radius: 10px;
	padding: 1px 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 130px;
}
.etpl2-search {
	width: 100%; padding: 4px 8px; margin-bottom: 5px; flex-shrink: 0;
	border: 1.5px solid var(--fieldBr); border-radius: 5px;
	background: var(--fieldBg); color: ${C.text}; font-size: 10.5px;
	outline: none; transition: border-color 0.2s;
}
.etpl2-search:focus { border-color: var(--pri); }
.etpl2-help-list {
	flex: 1; overflow-y: auto; min-height: 0;
	border: 1.5px solid var(--border); border-radius: 7px; background: #fff;
}
.etpl2-help-list::-webkit-scrollbar { width: 4px; }
.etpl2-help-list::-webkit-scrollbar-track { background: transparent; }
.etpl2-help-list::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.etpl2-group-title {
	position: sticky; top: 0; z-index: 2;
	padding: 4px 8px 3px; font-size: 8.5px; font-weight: 700;
	color: ${C.label}; text-transform: uppercase; letter-spacing: 0.6px;
	background: ${C.light}; border-bottom: 1px solid var(--border);
}
.etpl2-field-row {
	display: flex; align-items: center; gap: 5px;
	padding: 4px 7px; border-bottom: 1px solid #F8FAFC;
	transition: background 0.1s; cursor: pointer;
}
.etpl2-field-row:hover { background: ${hex_alpha(C.pri, 0.06)}; }
.etpl2-field-row:last-child { border-bottom: none; }
.etpl2-field-label { flex: 1; font-size: 10px; color: #374151; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.etpl2-field-code {
	font-size: 8.5px; color: ${C.pri}; background: var(--mid);
	border-radius: 3px; padding: 1px 4px; font-family: monospace;
	white-space: nowrap; max-width: 110px; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0;
}
.etpl2-insert-btn {
	width: 18px; height: 18px; flex-shrink: 0;
	background: none; border: 1.5px solid var(--border); border-radius: 3px;
	color: ${C.pri}; font-size: 13px; line-height: 1; cursor: pointer;
	display: flex; align-items: center; justify-content: center;
	transition: background 0.12s, border-color 0.12s; padding: 0;
}
.etpl2-insert-btn:hover { background: var(--mid); border-color: ${C.pri}; }
.etpl2-empty { padding: 16px 10px; text-align: center; font-size: 10.5px; color: #9CA3AF; }
.etpl2-preview-pane {
	display: none; flex-direction: column; gap: 8px;
	height: 360px; overflow-y: auto;
}
.etpl2-preview-pane::-webkit-scrollbar { width: 4px; }
.etpl2-preview-pane::-webkit-scrollbar-track { background: transparent; }
.etpl2-preview-pane::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.etpl2-preview-card {
	border: 1.5px solid var(--border); border-radius: 8px; overflow: hidden;
	background: #fff; box-shadow: 0 2px 10px ${hex_alpha(C.pri, 0.07)};
}
.etpl2-prev-hdr {
	display: flex; align-items: center; justify-content: space-between;
	padding: 7px 12px; background: var(--light); border-bottom: 1px solid var(--border);
}
.etpl2-prev-hdr-name {
	font-size: 11px; font-weight: 700; color: ${C.text};
	overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 55%;
}
.etpl2-prev-copy-row { display: flex; gap: 4px; }
.etpl2-copy-btn {
	font-size: 10px; padding: 2px 8px; border-radius: 4px; cursor: pointer;
	font-weight: 600; border: 1.5px solid var(--border); background: #fff;
	color: ${C.label}; transition: background 0.15s, border-color 0.15s;
}
.etpl2-copy-btn:hover { background: var(--mid); border-color: ${C.pri}; }
.etpl2-subj-row {
	display: flex; align-items: center; gap: 6px;
	padding: 6px 12px; background: #FAFAFA; border-bottom: 1px solid #F1F5F9;
}
.etpl2-subj-label {
	font-size: 9px; font-weight: 700; color: ${C.label};
	text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; flex-shrink: 0;
}
.etpl2-subj-val {
	flex: 1; font-size: 11.5px; color: ${C.text};
	overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500;
}
.etpl2-body-label {
	padding: 5px 12px 4px; font-size: 9px; font-weight: 700; color: ${C.label};
	text-transform: uppercase; letter-spacing: 0.5px;
	background: var(--light); border-bottom: 1px solid var(--border);
}
.etpl2-body-content {
	padding: 10px 12px; max-height: 260px; overflow-y: auto;
	color: #374151; line-height: 1.7; font-size: 11.5px;
	white-space: pre-wrap; user-select: text;
}
.etpl2-body-content::-webkit-scrollbar { width: 4px; }
.etpl2-body-content::-webkit-scrollbar-track { background: transparent; }
.etpl2-body-content::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.etpl2-prev-footer {
	padding: 5px 12px; background: var(--light); border-top: 1px solid var(--border);
	font-size: 9.5px; color: ${C.label};
}
.etpl2-prev-loading { padding: 36px 16px; text-align: center; }
.etpl2-prev-loading-icon { font-size: 22px; display: inline-block; animation: etpl2-spin 1s linear infinite; }
.etpl2-prev-loading-msg { font-size: 11px; color: ${C.label}; margin-top: 6px; font-weight: 500; }
@keyframes etpl2-spin { to { transform: rotate(360deg); } }
</style>

<div id="etpl2-root">
	<div class="etpl2-header">
		<div class="etpl2-header-icon">${ttMeta.icon}</div>
		<div class="etpl2-header-info">
			<div class="etpl2-header-title">Email Template Editor</div>
			<div class="etpl2-header-sub">${frappe.utils.escape_html(frm.doc.trip_type || "Trip")} · ${frappe.utils.escape_html(frm.doc.so_no || frm.doc.name || "New Trip")}</div>
		</div>
		${canEdit ? `<button class="etpl2-header-new-btn" id="etpl2-new-btn">➕ New Template</button>` : ""}
	</div>
	<div class="etpl2-selector">
		<label>Template</label>
		<select class="etpl2-tpl-select" id="etpl2-select">
			<option value="">— Select Template —</option>
			${optionsHtml}
		</select>
	</div>
	<div class="etpl2-tabs">
		${canEdit ? `<button class="etpl2-tab" data-tab="edit">✏️ Edit &amp; Help</button>` : ""}
		<button class="etpl2-tab etpl2-active" data-tab="preview">
			👁 Preview
			<span class="etpl2-tab-badge" id="etpl2-prev-badge">✓</span>
		</button>
	</div>
	${canEdit ? `<div class="etpl2-body" id="etpl2-edit-panel" style="display:none">
		<div class="etpl2-edit-pane">
			<div class="etpl2-field-block">
				<label class="etpl2-lbl">Subject</label>
				<input id="etpl2-subject" type="text" class="etpl2-input"
					placeholder="e.g. Trip {{ doc.so_no }} dispatched from {{ doc.origin_city }}" />
			</div>
			<div class="etpl2-field-block" style="flex:1;display:flex;flex-direction:column;">
				<label class="etpl2-lbl">
					Body
					<span class="etpl2-lbl-sub">&nbsp;— HTML &amp; Jinja supported. Click ⊕ on any field to insert.</span>
				</label>
				<textarea id="etpl2-body" class="etpl2-input etpl2-textarea"
					placeholder="Dear {{ doc.customer }},&#10;&#10;Your trip {{ doc.so_no }} has been dispatched.&#10;Route: {{ doc.origin_city }} → {{ doc.destination_city_1 }}&#10;Truck: {{ doc.vehicle_no }}&#10;Driver: {{ doc.driver }}"></textarea>
			</div>
			<div class="etpl2-save-row">
				<button class="etpl2-save-btn" id="etpl2-save-btn">💾 Save Template</button>
				<span class="etpl2-saved-badge" id="etpl2-saved-badge">✅ Saved!</span>
				<span class="etpl2-hint">After saving, switch to <b>👁 Preview</b> to see it rendered with trip data.</span>
			</div>
		</div>
		<div class="etpl2-divider"></div>
		<div class="etpl2-help-pane">
			<div class="etpl2-help-header">
				<span class="etpl2-help-title">❓ Field Variables</span>
				<span class="etpl2-help-scope" title="${scopeNote}">${scopeNote}</span>
			</div>
			<input id="etpl2-search" type="text" class="etpl2-search" placeholder="🔍  Search fields…" />
			<div class="etpl2-help-list" id="etpl2-help-list">${helpListHtml}</div>
		</div>
	</div>` : ""}
	<div id="etpl2-preview-panel" class="etpl2-preview-pane" style="display:flex">
		<div id="etpl2-preview-content"></div>
	</div>
</div>`
		}],
	});

	dialog.$wrapper.find(".modal-footer").hide();
	dialog.$wrapper.find(".modal-dialog").css({ "max-width": "720px", "width": "720px" });
	dialog.show();

	const $r = dialog.$wrapper.find("#etpl2-root");

	// Load preview immediately on open
	_etpl2_load_preview(frm, $r);

	$r.on("click", ".etpl2-tab", function () {
		const tab = $(this).data("tab");
		$r.find(".etpl2-tab").removeClass("etpl2-active");
		$(this).addClass("etpl2-active");
		if (tab === "edit") {
			$r.find("#etpl2-edit-panel").css("display", "flex");
			$r.find("#etpl2-preview-panel").css("display", "none");
		} else {
			$r.find("#etpl2-edit-panel").css("display", "none");
			$r.find("#etpl2-preview-panel").css("display", "flex");
			_etpl2_load_preview(frm, $r);
		}
	});

	$r.find("#etpl2-select").on("change", function () {
		const name = $(this).val();
		$r.find("#etpl2-prev-badge").hide();
		if (!name) {
			$r.find("#etpl2-subject").val("");
			$r.find("#etpl2-body").val("");
			$r.data("etpl2_name", "");
			$r.find("#etpl2-preview-content").html(`<div class="etpl2-prev-loading"><div class="etpl2-prev-loading-msg">📭 No template selected.</div></div>`);
			return;
		}
		$r.data("etpl2_name", name);
		_etpl2_load_raw(frm, $r, name);
		// Auto-switch to preview tab and load preview on template select
		$r.find(".etpl2-tab").removeClass("etpl2-active");
		$r.find(".etpl2-tab[data-tab='preview']").addClass("etpl2-active");
		$r.find("#etpl2-edit-panel").css("display", "none");
		$r.find("#etpl2-preview-panel").css("display", "flex");
		_etpl2_load_preview(frm, $r);
	});

	$r.find("#etpl2-new-btn").on("click", () => { dialog.hide(); frappe.new_doc("Email Template", { reference_doctype: "Trip" }); });

	$r.find("#etpl2-search").on("input", function () {
		const q = $(this).val().toLowerCase().trim();
		$r.find(".etpl2-field-row").each(function () {
			const label = ($(this).data("label") || "").toLowerCase();
			const varr = ($(this).data("var") || "").toLowerCase();
			$(this).toggle(!q || label.includes(q) || varr.includes(q));
		});
		$r.find(".etpl2-group").each(function () {
			$(this).toggle($(this).find(".etpl2-field-row:visible").length > 0);
		});
	});

	$r.on("click", ".etpl2-field-row", function (e) {
		const varText = $(this).data("var");
		const $ta = $r.find("#etpl2-body")[0];
		if ($ta) {
			const s = $ta.selectionStart, en = $ta.selectionEnd;
			$ta.value = $ta.value.slice(0, s) + varText + $ta.value.slice(en);
			$ta.selectionStart = $ta.selectionEnd = s + varText.length;
			$ta.focus();
			const $btn = $(this).find(".etpl2-insert-btn");
			const orig = $btn.text();
			$btn.text("✓").css({ color: "#059669", "border-color": "#A7F3D0" });
			setTimeout(() => $btn.text(orig).css({ color: "", "border-color": "" }), 900);
		}
		e.stopPropagation();
	});

	$r.find("#etpl2-save-btn").on("click", function () {
		_etpl2_save(frm, $r);
	});

	if (autoName) {
		$r.find("#etpl2-select").val(autoName);
		_etpl2_load_raw(frm, $r, autoName);
	}
}

function _etpl2_load_raw(frm, $r, name) {
	frappe.call({
		method: "frappe.client.get",
		args: { doctype: "Email Template", name },
		callback(res) {
			const doc = res.message;
			if (!doc) return;
			$r.data("etpl2_name", doc.name);
			$r.find("#etpl2-subject").val(doc.subject || "");
			$r.find("#etpl2-body").val(
				(doc.response || "")
					.replace(/<br\s*\/?>/gi, "\n")
					.replace(/<\/p>/gi, "\n\n")
					.replace(/<[^>]+>/g, "")
					.trim()
			);
			$r.find("#etpl2-saved-badge").hide();
			$r.find("#etpl2-prev-badge").hide();
		},
	});
}

function _etpl2_save(frm, $r) {
	const name = $r.data("etpl2_name") || $r.find("#etpl2-select").val();
	const subject = $r.find("#etpl2-subject").val().trim();
	const body = $r.find("#etpl2-body").val();

	if (!name) {
		frappe.show_alert({ message: "⚠️ Please select a template first.", indicator: "orange" }, 4);
		return;
	}
	if (!subject) {
		frappe.show_alert({ message: "⚠️ Subject cannot be empty.", indicator: "orange" }, 4);
		$r.find("#etpl2-subject").focus();
		return;
	}

	const $btn = $r.find("#etpl2-save-btn");
	$btn.html("⏳ Saving…").prop("disabled", true);

	frappe.call({
		method: "frappe.client.set_value",
		args: {
			doctype: "Email Template",
			name,
			fieldname: { subject, response: body },
		},
		callback(res) {
			$btn.html("💾 Save Template").prop("disabled", false);
			if (res.exc) {
				frappe.show_alert({ message: "❌ Save failed — check permissions.", indicator: "red" }, 4);
				return;
			}
			$r.find("#etpl2-saved-badge").show();
			$r.find("#etpl2-prev-badge").hide();
			setTimeout(() => $r.find("#etpl2-saved-badge").fadeOut(400), 2400);
			frappe.show_alert({ message: `✅ <b>${name}</b> saved successfully!`, indicator: "green" }, 4);
		},
		error() {
			$btn.html("💾 Save Template").prop("disabled", false);
			frappe.show_alert({ message: "❌ Save failed. Check console.", indicator: "red" }, 4);
		},
	});
}

function _etpl2_get_missing(frm) {
	const missing = [];
	for (const f of ETPL_PREVIEW_REQUIRED) {
		if (f.fieldname === "vendor") continue; // customer/vendor checked as a pair below
		if (!frm.doc[f.fieldname]) missing.push(f.label);
	}
	if (!frm.doc.customer && !frm.doc.vendor) missing.push("Customer / Vendor");
	return missing;
}

function _etpl2_missing_fields_banner(frm) {
	const missing = _etpl2_get_missing(frm);
	if (!missing.length) return "";
	return `<div style="background:#FFF7ED;border:1.5px solid #FED7AA;border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:11.5px;color:#92400E;line-height:1.6;">
		<b>⚠️ Missing trip data</b> — these fields are empty, so preview will show blank placeholders:<br>
		<span style="font-weight:600;">${missing.join(" · ")}</span><br>
		<span style="opacity:0.75;">Fill &amp; save the trip first to see a live rendered preview.</span>
	</div>`;
}

function _etpl2_load_preview(frm, $r) {
	const name = $r.data("etpl2_name") || $r.find("#etpl2-select").val();
	const $pc = $r.find("#etpl2-preview-content");
	const missing = _etpl2_get_missing(frm);

	if (!name) {
		$pc.html(`<div class="etpl2-prev-loading"><div class="etpl2-prev-loading-msg">📭 No template selected.</div></div>`);
		return;
	}

	if (missing.length) {
		$pc.html(_etpl2_missing_fields_banner(frm));
		return;
	}

	$pc.html(`<div class="etpl2-prev-loading"><div class="etpl2-prev-loading-icon">⏳</div><div class="etpl2-prev-loading-msg">Rendering preview with trip data…</div></div>`);

	if (frm.is_new()) {
		frappe.call({
			method: "frappe.client.get",
			args: { doctype: "Email Template", name },
			callback(res) {
				const doc = res.message;
				if (!doc) {
					$pc.html(`<div class="etpl2-prev-loading"><div class="etpl2-prev-loading-msg">⚠️ Template not found.</div></div>`);
					return;
				}
				$pc.html("");
				_etpl2_render_card($r, name, doc.subject || "(No subject)", doc.response || "(Empty body)", false, true, frm);
			},
		});
		return;
	}

	frappe.call({
		method: "logicore.logicore.doctype.trip.trip.render_email_template_for_trip",
		args: { template_name: name, trip_name: frm.doc.name },
		callback(r) {
			const rendered = r.message || null;
			if (!rendered) {
				$pc.html(`<div class="etpl2-prev-loading"><div class="etpl2-prev-loading-msg">⚠️ Could not render. Check server logs.</div></div>`);
				return;
			}
			$pc.html("");
			_etpl2_render_card($r, name,
				rendered.subject || "(No subject)",
				rendered.message || "(Empty body)",
				true, false, frm
			);
		},
		error() {
			$pc.html(`<div class="etpl2-prev-loading"><div class="etpl2-prev-loading-msg">⚠️ Could not render. Check server logs.</div></div>`);
		},
	});
}

function _etpl2_render_card($r, name, subject, body, isSavedTrip, isNewTrip, frm) {
	const tip = isNewTrip
		? "⚠️ Unsaved trip — save the trip first to render live Jinja values"
		: isSavedTrip
			? "✨ Live render — Jinja variables filled from current trip"
			: "⚠️ Jinja variables shown as-is — some fields may be empty";

	const bodyText = body
		.replace(/<br\s*\/?>/gi, "\n")
		.replace(/<\/p>/gi, "\n\n")
		.replace(/<[^>]+>/g, "")
		.replace(/&nbsp;/g, " ")
		.replace(/&amp;/g, "&")
		.replace(/&lt;/g, "<")
		.replace(/&gt;/g, ">")
		.replace(/&quot;/g, '"')
		.replace(/&#39;/g, "'");

	$r.find("#etpl2-preview-content").append(`
	<div class="etpl2-preview-card">
		<div class="etpl2-prev-hdr">
			<span class="etpl2-prev-hdr-name" title="${frappe.utils.escape_html(name)}">${frappe.utils.escape_html(name)}</span>
			<div class="etpl2-prev-copy-row">
				<button class="etpl2-copy-btn" id="etpl2-copy-all">📋 Copy</button>
			</div>
		</div>
		<div class="etpl2-subj-row">
			<span class="etpl2-subj-label">Subject</span>
			<span class="etpl2-subj-val">${frappe.utils.escape_html(subject)}</span>
		</div>
		<div class="etpl2-body-label">📝 Message Body</div>
		<div class="etpl2-body-content">${body}</div>
		<div class="etpl2-prev-footer">${frappe.utils.escape_html(tip)}</div>
	</div>`);

	$r.find("#etpl2-prev-badge").show();

	$r.find("#etpl2-copy-all").on("click", function () {
		if (frm) {
			const missing = _etpl2_get_missing(frm);
			if (missing.length) {
				frappe.show_alert({
					message: `⚠️ Cannot copy — fill these fields first: <b>${missing.join(", ")}</b>`,
					indicator: "orange",
				}, 5);
				return;
			}
		}
		_etpl2_copy("Subject: " + subject + "\n\n" + bodyText, $r.find("#etpl2-copy-all"));
	});
}

function _etpl2_copy(text, $btn) {
	const orig = $btn.html();
	const flash = () => {
		$btn.html("✅ Copied!");
		frappe.show_alert({ message: "Copied to clipboard!", indicator: "green" }, 2);
		setTimeout(() => $btn.html(orig), 2000);
	};
	if (navigator.clipboard && window.isSecureContext)
		navigator.clipboard.writeText(text).then(flash).catch(() => _etpl2_exec_copy(text, flash));
	else
		_etpl2_exec_copy(text, flash);
}

function _etpl2_exec_copy(text, cb) {
	const el = document.createElement("textarea");
	el.value = text; el.style.cssText = "position:fixed;opacity:0;";
	document.body.appendChild(el); el.select();
	try { document.execCommand("copy"); cb(); } catch (e) { }
	document.body.removeChild(el);
}

// ══════════════════════════════════════════════════════════════════
//  COLOR UTILS
// ══════════════════════════════════════════════════════════════════

function hex_to_rgb(hex) { const h = hex.trim().replace("#", ""); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
function hex_alpha(hex, a) { try { const [r, g, b] = hex_to_rgb(hex); return `rgba(${r},${g},${b},${a})`; } catch { return hex; } }
function darken(hex, amt) { try { const [r, g, b] = hex_to_rgb(hex); const d = v => Math.max(0, v - amt).toString(16).padStart(2, "0"); return `#${d(r)}${d(g)}${d(b)}`; } catch { return hex; } }
function hex_to_hsl(hex) { try { const [r, g, b] = hex_to_rgb(hex).map(v => v / 255); const mx = Math.max(r, g, b), mn = Math.min(r, g, b); let h = 0, s = 0, l = (mx + mn) / 2; if (mx !== mn) { const d = mx - mn; s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn); switch (mx) { case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break; case g: h = ((b - r) / d + 2) / 6; break; case b: h = ((r - g) / d + 4) / 6; break; } } return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)]; } catch { return [0, 0, 50]; } }
function hsl_hex(h, s, l) { s /= 100; l /= 100; const k = n => (n + h / 30) % 12, a = s * Math.min(l, 1 - l), f = n => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1))); return "#" + [f(0), f(8), f(4)].map(v => Math.round(v * 255).toString(16).padStart(2, "0")).join(""); }
function get_luminance(hex) { try { const [r, g, b] = hex_to_rgb(hex).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; } catch { return 0; } }
function _tc(v, mn, mx) { return Math.max(mn, Math.min(mx, v)); }

// ══════════════════════════════════════════════════════════════════
//  apply_trip_color
// ══════════════════════════════════════════════════════════════════

function apply_trip_color(frm, baseHex) {
	const isDark = get_frappe_theme() === "dark";
	const [h, s, l] = hex_to_hsl(baseHex);
	const page_bg = isDark ? hsl_hex(h, _tc(s * .35, 8, 22), 12) : hsl_hex(h, _tc(s * .18, 4, 14), 96.5);
	const card_bg = isDark ? hsl_hex(h, _tc(s * .30, 6, 18), 16) : "#FFFFFF";
	const section_border = isDark ? hex_alpha(baseHex, 0.20) : hsl_hex(h, _tc(s * .42, 8, 38), 87);
	const field_bg = isDark ? hsl_hex(h, _tc(s * .25, 5, 15), 13.5) : hsl_hex(h, _tc(s * .10, 2, 10), 97.5);
	const field_border = isDark ? hex_alpha(baseHex, 0.32) : hsl_hex(h, _tc(s * .52, 12, 48), 80);
	const label_color = isDark ? hsl_hex(h, _tc(s * .55, 20, 55), 72) : hsl_hex(h, _tc(s * .78, 28, 72), _tc(l * .62, 18, 44));
	const heading_color = isDark ? hsl_hex(h, _tc(s * .35, 12, 35), 88) : hsl_hex(h, _tc(s * .90, 38, 85), _tc(l * .32, 8, 22));
	const accent = hsl_hex((h + 28) % 360, _tc(s * .82, 38, 88), _tc(l, 28, 62));
	const uid = frm.$wrapper.attr("data-tms-id") || ("tms-trip-" + (frm.doc.name || "new").replace(/[^a-zA-Z0-9]/g, "_"));
	frm.$wrapper.attr("data-tms-id", uid);
	const el = frm.$wrapper[0];
	if (el) {
		el.style.setProperty("--tms-primary", baseHex);
		el.style.setProperty("--tms-accent", accent);
		el.style.setProperty("--tms-page-bg", page_bg);
		el.style.setProperty("--tms-card-bg", card_bg);
		el.style.setProperty("--tms-section-border", section_border);
		el.style.setProperty("--tms-field-bg", field_bg);
		el.style.setProperty("--tms-field-border", field_border);
		el.style.setProperty("--tms-label-color", label_color);
		el.style.setProperty("--tms-heading-color", heading_color);
		el.style.setProperty("--tms-primary-light", hex_alpha(baseHex, 0.10));
		el.style.setProperty("--tms-primary-border", hex_alpha(baseHex, 0.28));
		el.style.setProperty("--tms-field-focus-glow", hex_alpha(baseHex, isDark ? 0.18 : 0.12));
		el.style.setProperty("--tms-hl-bg", hex_alpha(baseHex, 0.13));
		el.style.setProperty("--tms-hl-border", hex_alpha(baseHex, 0.65));
	}
	const sel = `[data-tms-id="${uid}"]`;
	_inject_scoped_style("tms-trip-field-theme", `
@keyframes tms-border-pulse {
  0%,100% { border-color:${field_border}!important; box-shadow:0 0 0 1.5px ${hex_alpha(baseHex, 0.10)}; }
  50% { border-color:${hex_alpha(baseHex, 0.70)}!important; box-shadow:0 0 0 2.5px ${hex_alpha(baseHex, 0.22)}; }
}
${sel} input.form-control:not([disabled]):not([readonly]),
${sel} select.form-control:not([disabled]),
${sel} textarea.form-control:not([disabled]) { background-color:${field_bg}!important;border-color:${field_border}!important;border-width:1.5px!important;transition:background-color .2s,box-shadow .2s;animation:tms-border-pulse 3s ease-in-out infinite; }
${sel} input.form-control:not([disabled]):not([readonly]):hover,
${sel} select.form-control:not([disabled]):hover,
${sel} textarea.form-control:not([disabled]):hover { background-color:${hex_alpha(baseHex, 0.07)}!important;box-shadow:0 2px 10px ${hex_alpha(baseHex, 0.14)}!important; }
${sel} input.form-control:not([disabled]):not([readonly]):focus,
${sel} select.form-control:not([disabled]):focus,
${sel} textarea.form-control:not([disabled]):focus { background-color:${hex_alpha(baseHex, 0.05)}!important;box-shadow:0 0 0 3px ${hex_alpha(baseHex, 0.20)},0 2px 8px ${hex_alpha(baseHex, 0.14)}!important;outline:none!important; }
${sel} .frappe-control .control-label,${sel} label.control-label { color:${label_color}!important; }
${sel} .form-section .section-head,${sel} .form-section-heading { color:${heading_color}!important;border-color:${section_border}!important; }
${sel} .like-disabled-input { background-color:${field_bg}!important;border-color:${field_border}!important;color:${label_color}!important; }
`);
	$(".tms-trip-banner").css("background", `linear-gradient(135deg,${darken(baseHex, 42)} 0%,${baseHex} 100%)`);
	const isLight = get_luminance(baseHex) > 0.30;
	const txt = isLight ? "#0F172A" : "#FFFFFF";
	const txtSub = isLight ? "rgba(15,23,42,.72)" : "rgba(255,255,255,.88)";
	const txtBg = isLight ? "rgba(15,23,42,.10)" : "rgba(255,255,255,.15)";
	const pillBg = isLight ? hex_alpha(darken(baseHex, 20), 0.85) : "rgba(255,255,255,0.22)";
	const pillBord = isLight ? hex_alpha(darken(baseHex, 10), 0.55) : "rgba(255,255,255,0.40)";
	$(".tms-trip-type-pill").css({ "background": pillBg, "color": "#FFFFFF", "border-color": pillBord, "text-shadow": "0 1px 3px rgba(0,0,0,0.35)" });
	_inject_scoped_style("tms-color-override", `
		.tms-bid-sono  { color:${txt}   !important; }
		.tms-bstage    { color:${txtSub}!important; }
		.tms-bid-route { color:${txtSub}!important; background:${txtBg}!important; }
	`);
}

// ══════════════════════════════════════════════════════════════════
//  ADDRESS SEARCH
// ══════════════════════════════════════════════════════════════════

// function setup_address_search(frm) {
// 	["origin_address_1", "origin_address_2", "destination_address_1", "destination_address_2"].forEach(fn => {
// 		if (!frm.fields_dict[fn]) return;
// 		frm.set_query(fn, () => ({ query: "logicore.logicore.doctype.trip.trip.search_address", filters: {} }));
// 		if (frm.doc[fn]) _show_address_label(frm, fn, frm.doc[fn]);
// 	});
// }
function setup_address_search(frm) {
    ["origin_address_1", "origin_address_2"].forEach(fn => {
        if (!frm.fields_dict[fn]) return;
        frm.set_query(fn, () => ({
            query: "logicore.logicore.doctype.trip.trip.search_address",
            filters: { is_origin: 1 }
        }));
        if (frm.doc[fn]) _show_address_label(frm, fn, frm.doc[fn]);
    });

    ["destination_address_1", "destination_address_2"].forEach(fn => {
        if (!frm.fields_dict[fn]) return;
        frm.set_query(fn, () => ({
            query: "logicore.logicore.doctype.trip.trip.search_address",
            filters: { is_destination: 1 }
        }));
        if (frm.doc[fn]) _show_address_label(frm, fn, frm.doc[fn]);
    });
}
function on_address_selected(frm, fn) {
	const addr = frm.doc[fn];
	if (!addr) { frm.set_df_property(fn, "description", ""); frm.refresh_field(fn); return; }
	_show_address_label(frm, fn, addr);
}
// function _show_address_label(frm, fn, addr_name) {
// 	frappe.call({
// 		method: "logicore.logicore.doctype.trip.trip.postal = (addr.get("custom_postal_",
// 		args: { address_name: addr_name },
// 		callback(r) { if (r.message) { frm.set_df_property(fn, "description", r.message); frm.refresh_field(fn); } },
// 	});
// }

function _show_address_label(frm, fn, addr_name) {
    // Always clear cached description before re-fetching
    frm.set_df_property(fn, "description", "");
    
    frappe.call({
        method: "logicore.logicore.doctype.trip.trip.get_address_display_label",
        args: { address_name: addr_name },
        callback(r) {
            if (r.message) {
                frm.set_df_property(fn, "description", r.message);
                frm.refresh_field(fn);
            }
        },
    });
}
// ══════════════════════════════════════════════════════════════════
//  BOTTOM SAVE BUTTON
// ══════════════════════════════════════════════════════════════════
function _inject_top_save_button(frm) {
    // Avoid duplicate
    if (frm._top_save_added) return;
    frm._top_save_added = true;

    const $btn = $(`
        <button class="btn btn-primary tms-top-save-btn"
            style="margin-right:10px;">
            💾 Save
        </button>
    `);

    $btn.on("click", function () {
        frm.save();
    });

    // Add into page actions (top area)
    if (frm.page && frm.page.$actions) {
        frm.page.$actions.prepend($btn);
    }
}

// ══════════════════════════════════════════════════════════════════
//  BOTTOM SAVE BUTTON  —  sticky bar outside tabs, survives tab switch
// ══════════════════════════════════════════════════════════════════

// function _inject_bottom_save_button(frm) {
//     $("#tms-bottom-save-wrap").remove();

//     const combo   = frm._tms_resolved_combo || get_combo_for_trip(frm.doc.trip_type);
//     const pri     = (combo && combo.primary)     ? combo.primary     : "#3B4FE4";
//     const cardBg  = (combo && combo.card_bg)     ? combo.card_bg     : "#FFFFFF";
//     const lblClr  = (combo && combo.label_color) ? combo.label_color : "#6B7280";
//     const priDark = darken(pri, 22);

//     const soInfo = frm.is_new()
//         ? "⏳ Trip ID auto-generates on first save"
//         : `Trip: <b>${frappe.utils.escape_html(frm.doc.so_no || frm.doc.name)}</b>`;

//     const tripInfo = frm.doc.origin_city && frm.doc.destination_city_1
//         ? `&nbsp;·&nbsp;📍 ${frappe.utils.escape_html(frm.doc.origin_city)} → ${frappe.utils.escape_html(frm.doc.destination_city_1)}`
//         : "";

//     const $bar = $(`
//         <div id="tms-bottom-save-wrap">
//             <style>
//                 #tms-bottom-save-wrap {
//                     position: sticky;
//                     bottom: 0; left: 0; right: 0;
//                     z-index: 990;
//                     display: flex;
//                     align-items: center;
//                     gap: 10px;
//                     padding: 9px 16px 9px 14px;
//                     background: ${cardBg};
//                     border-top: 2px solid ${hex_alpha(pri, 0.22)};
//                     box-shadow: 0 -4px 20px ${hex_alpha(pri, 0.13)};
//                     margin-top: 12px;
//                     border-radius: 0 0 10px 10px;
//                     transition: border-color 0.2s, box-shadow 0.2s;
//                 }
//                 #tms-bottom-save-wrap.tms-has-changes {
//                     border-top-color: ${hex_alpha(pri, 0.55)};
//                     box-shadow: 0 -4px 24px ${hex_alpha(pri, 0.24)};
//                 }
//                 #tms-bottom-save-btn {
//                     display: inline-flex;
//                     align-items: center;
//                     gap: 7px;
//                     padding: 8px 22px;
//                     background: ${pri};
//                     color: #fff;
//                     border: none;
//                     border-radius: 8px;
//                     font-size: 13px;
//                     font-weight: 700;
//                     cursor: pointer;
//                     white-space: nowrap;
//                     flex-shrink: 0;
//                     transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
//                     box-shadow: 0 2px 8px ${hex_alpha(pri, 0.28)};
//                 }
//                 #tms-bottom-save-btn:hover {
//                     background: ${priDark};
//                     box-shadow: 0 4px 16px ${hex_alpha(pri, 0.36)};
//                     transform: translateY(-1px);
//                 }
//                 #tms-bottom-save-btn:active {
//                     transform: none;
//                     box-shadow: 0 1px 4px ${hex_alpha(pri, 0.20)};
//                 }
//                 #tms-bottom-save-btn:disabled {
//                     opacity: 0.62;
//                     cursor: not-allowed;
//                     transform: none;
//                 }
//                 #tms-bottom-save-info {
//                     flex: 1;
//                     font-size: 11.5px;
//                     color: ${lblClr};
//                     line-height: 1.4;
//                     overflow: hidden;
//                     text-overflow: ellipsis;
//                     white-space: nowrap;
//                     transition: color 0.2s;
//                 }
//                 #tms-bottom-save-wrap.tms-has-changes #tms-bottom-save-info {
//                     color: ${pri};
//                     font-weight: 600;
//                 }
//                 #tms-bottom-save-saved {
//                     display: none;
//                     font-size: 11px;
//                     font-weight: 600;
//                     color: #059669;
//                     background: #ECFDF5;
//                     border: 1.5px solid #A7F3D0;
//                     border-radius: 6px;
//                     padding: 4px 10px;
//                     white-space: nowrap;
//                     flex-shrink: 0;
//                 }
//                 #tms-bottom-save-no-changes {
//                     display: none;
//                     font-size: 11px;
//                     font-weight: 600;
//                     color: ${lblClr};
//                     background: ${hex_alpha(pri, 0.07)};
//                     border: 1.5px solid ${hex_alpha(pri, 0.18)};
//                     border-radius: 6px;
//                     padding: 4px 10px;
//                     white-space: nowrap;
//                     flex-shrink: 0;
//                 }
//                 #tms-bottom-discard-btn {
//                     display: inline-flex;
//                     align-items: center;
//                     gap: 7px;
//                     padding: 8px 18px;
//                     background: #EF4444;
//                     color: #fff;
//                     border: none;
//                     border-radius: 8px;
//                     font-size: 13px;
//                     font-weight: 700;
//                     cursor: pointer;
//                     white-space: nowrap;
//                     flex-shrink: 0;
//                     transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
//                     box-shadow: 0 2px 8px rgba(239,68,68,0.28);
//                 }
//                 #tms-bottom-discard-btn:hover {
//                     background: #DC2626;
//                     box-shadow: 0 4px 16px rgba(239,68,68,0.38);
//                     transform: translateY(-1px);
//                 }
//                 #tms-bottom-discard-btn:active {
//                     transform: none;
//                     box-shadow: 0 1px 4px rgba(239,68,68,0.20);
//                 }
//                 #tms-bottom-discard-btn:disabled {
//                     opacity: 0.45;
//                     cursor: not-allowed;
//                     transform: none;
//                 }
//             </style>

//             <button id="tms-bottom-save-btn">💾 Save Trip</button>
//             <button id="tms-bottom-discard-btn">✖ Discard</button>
//             <span id="tms-bottom-save-info">${soInfo}${tripInfo}</span>
//             <span id="tms-bottom-save-saved">✅ Saved!</span>
//             <span id="tms-bottom-save-no-changes">✔ No changes</span>
//         </div>
//     `);

//     // ── Sync info text + bar highlight based on dirty state ────────
//     function _sync_dirty_state() {
//         const dirty = frm.is_dirty();
//         const $wrap = $("#tms-bottom-save-wrap");
//         const $info = $("#tms-bottom-save-info");
//         const $discard = $("#tms-bottom-discard-btn");
//         if (dirty) {
//             $wrap.addClass("tms-has-changes");
//             $info.html(`⌨️ <b>Ctrl+S</b> save &nbsp;·&nbsp; <span style="font-size:10px;opacity:0.75;">Ctrl+D discard</span> · ${soInfo}${tripInfo}`);
//             $discard.prop("disabled", false);
//         } else {
//             $wrap.removeClass("tms-has-changes");
//             $info.html(`${soInfo}${tripInfo}`);
//             $discard.prop("disabled", true);
//         }
//     }

//     // ── Poll dirty state every 600ms ───────────────────────────────
//     if (frm._tms_dirty_timer) clearInterval(frm._tms_dirty_timer);
//     frm._tms_dirty_timer = setInterval(_sync_dirty_state, 600);
//     _sync_dirty_state();


//     // ── Click: always enabled — mimics Frappe top Save button ──────
//     $bar.find("#tms-bottom-save-btn").on("click", function () {
//         if (!frm.is_dirty()) {
//             // Same behaviour as Frappe's own Save button when no changes
//             const $nc = $("#tms-bottom-save-no-changes");
//             $nc.show();
//             setTimeout(() => $nc.fadeOut(400), 1800);
//             return;
//         }
//         const $btn = $(this);
//         $btn.html("⏳ Saving…").prop("disabled", true);
//         frm.save()
//             .then(() => {
//                 $btn.html("💾 Save Trip").prop("disabled", false);
//                 const $badge = $("#tms-bottom-save-saved");
//                 $badge.show();
//                 setTimeout(() => $badge.fadeOut(400), 2200);
//             })
//             .catch(() => {
//                 $btn.html("💾 Save Trip").prop("disabled", false);
//                 _sync_dirty_state();
//             });
//     });

// // ── Discard button: always go back to Trip list ─────────────────
//     $bar.find("#tms-bottom-discard-btn").on("click", function () {
//         if (!frm.is_dirty()) {
//             frappe.set_route("List", "Trip");
//             return;
//         }
//         frappe.confirm(
//             __("Discard all unsaved changes and go back to Trip list?"),
//             () => frappe.set_route("List", "Trip")
//         );
//     });
//     // ── Ctrl+S / Cmd+S ─────────────────────────────────────────────
//     $(document).off("keydown.tms_bottom_save").on("keydown.tms_bottom_save", function (e) {
//         if ((e.ctrlKey || e.metaKey) && e.key === "s" && frm.$wrapper.is(":visible")) {
//             e.preventDefault();
//             if (frm.is_dirty()) {
//                 frm.save();
//             } else {
//                 const $nc = $("#tms-bottom-save-no-changes");
//                 $nc.show();
//                 setTimeout(() => $nc.fadeOut(400), 1800);
//             }
//         }
//     });

//     // ── Ctrl+D — Discard ───────────────────────────────────────────
//     $(document).off("keydown.tms_bottom_discard").on("keydown.tms_bottom_discard", function (e) {
//         if ((e.ctrlKey || e.metaKey) && e.key === "d" && frm.$wrapper.is(":visible")) {
//             e.preventDefault();
//             if (!frm.is_dirty()) {
//                 frappe.set_route("List", "Trip");
//                 return;
//             }
//             frappe.confirm(
//                 __("Discard all unsaved changes and go back to Trip list?"),
//                 () => frappe.set_route("List", "Trip")
//             );
//         }
//     });

//     // ── Clean up timer on page hide ────────────────────────────────
//     frm.$wrapper.closest(".page-container")
//         .off("page:hide.tms_dirty_poll")
//         .on("page:hide.tms_dirty_poll", function () {
//             if (frm._tms_dirty_timer) {
//                 clearInterval(frm._tms_dirty_timer);
//                 frm._tms_dirty_timer = null;
//             }
//             $(document).off("keydown.tms_bottom_discard");
//         });

//     // ── Attach below form tabs ──────────────────────────────────────
//     const $host = frm.$wrapper.find(".form-page").first().length
//         ? frm.$wrapper.find(".form-page").first()
//         : (frm.$wrapper.find(".page-form").first().length
//             ? frm.$wrapper.find(".page-form").first()
//             : frm.$wrapper);

//     $host.append($bar);
// }

function _inject_bottom_save_button(frm) {
    $("#tms-bottom-save-wrap").remove();

    const combo   = frm._tms_resolved_combo || get_combo_for_trip(frm.doc.trip_type);
    const pri     = (combo && combo.primary)     ? combo.primary     : "#3B4FE4";
    const cardBg  = (combo && combo.card_bg)     ? combo.card_bg     : "#FFFFFF";
    const lblClr  = (combo && combo.label_color) ? combo.label_color : "#6B7280";
    const priDark = darken(pri, 22);

    const soInfo = frm.is_new()
        ? "⏳ Trip ID auto-generates on first save"
        : `Trip: <b>${frappe.utils.escape_html(frm.doc.so_no || frm.doc.name)}</b>`;

    const tripInfo = frm.doc.origin_city && frm.doc.destination_city_1
        ? `&nbsp;·&nbsp;📍 ${frappe.utils.escape_html(frm.doc.origin_city)} → ${frappe.utils.escape_html(frm.doc.destination_city_1)}`
        : "";

    const $bar = $(`
        <div id="tms-bottom-save-wrap">
            <style>
                #tms-bottom-save-wrap {
                    position: sticky;
                    bottom: 0; left: 0; right: 0;
                    z-index: 990;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 9px 16px 9px 14px;
                    background: ${cardBg};
                    border-top: 2px solid ${hex_alpha(pri, 0.22)};
                    box-shadow: 0 -4px 20px ${hex_alpha(pri, 0.13)};
                    margin-top: 12px;
                    border-radius: 0 0 10px 10px;
                    transition: border-color 0.2s, box-shadow 0.2s;
                }
                #tms-bottom-save-wrap.tms-has-changes {
                    border-top-color: ${hex_alpha(pri, 0.55)};
                    box-shadow: 0 -4px 24px ${hex_alpha(pri, 0.24)};
                }
                #tms-bottom-left-actions {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                #tms-bottom-right-actions {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-left: auto;
                }
                #tms-bottom-save-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: 7px;
                    padding: 8px 22px;
                    background: ${pri};
                    color: #fff;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 700;
                    cursor: pointer;
                    white-space: nowrap;
                    flex-shrink: 0;
                    transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
                    box-shadow: 0 2px 8px ${hex_alpha(pri, 0.28)};
                }
                #tms-bottom-save-btn:hover {
                    background: ${priDark};
                    box-shadow: 0 4px 16px ${hex_alpha(pri, 0.36)};
                    transform: translateY(-1px);
                }
                #tms-bottom-save-btn:active {
                    transform: none;
                    box-shadow: 0 1px 4px ${hex_alpha(pri, 0.20)};
                }
                #tms-bottom-save-btn:disabled {
                    opacity: 0.62;
                    cursor: not-allowed;
                    transform: none;
                }
                #tms-bottom-payment-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: 7px;
                    padding: 8px 22px;
                    background: ${pri};
                    color: #fff;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 700;
                    cursor: pointer;
                    white-space: nowrap;
                    flex-shrink: 0;
                    transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
                    box-shadow: 0 2px 8px ${hex_alpha(pri, 0.28)};
                }
                #tms-bottom-payment-btn:hover:not(:disabled) {
                    background: ${priDark};
                    box-shadow: 0 4px 16px ${hex_alpha(pri, 0.36)};
                    transform: translateY(-1px);
                }
                #tms-bottom-payment-btn:active:not(:disabled) {
                    transform: none;
                    box-shadow: 0 1px 4px ${hex_alpha(pri, 0.20)};
                }
                #tms-bottom-payment-btn:disabled {
                    opacity: 0.55;
                    cursor: not-allowed;
                    transform: none;
                }
                #tms-bottom-discard-btn {
                    display: inline-flex;
                    align-items: center;
                    gap: 7px;
                    padding: 8px 18px;
                    background: #EF4444;
                    color: #fff;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 700;
                    cursor: pointer;
                    white-space: nowrap;
                    flex-shrink: 0;
                    transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
                    box-shadow: 0 2px 8px rgba(239,68,68,0.28);
                }
                #tms-bottom-discard-btn:hover {
                    background: #DC2626;
                    box-shadow: 0 4px 16px rgba(239,68,68,0.38);
                    transform: translateY(-1px);
                }
                #tms-bottom-discard-btn:active {
                    transform: none;
                    box-shadow: 0 1px 4px rgba(239,68,68,0.20);
                }
                #tms-bottom-discard-btn:disabled {
                    opacity: 0.45;
                    cursor: not-allowed;
                    transform: none;
                }
                #tms-bottom-save-info {
                    flex: 1;
                    font-size: 11.5px;
                    color: ${lblClr};
                    line-height: 1.4;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    transition: color 0.2s;
                }
                #tms-bottom-save-wrap.tms-has-changes #tms-bottom-save-info {
                    color: ${pri};
                    font-weight: 600;
                }
                #tms-bottom-save-saved {
                    display: none;
                    font-size: 11px;
                    font-weight: 600;
                    color: #059669;
                    background: #ECFDF5;
                    border: 1.5px solid #A7F3D0;
                    border-radius: 6px;
                    padding: 4px 10px;
                    white-space: nowrap;
                    flex-shrink: 0;
                }
                #tms-bottom-save-no-changes {
                    display: none;
                    font-size: 11px;
                    font-weight: 600;
                    color: ${lblClr};
                    background: ${hex_alpha(pri, 0.07)};
                    border: 1.5px solid ${hex_alpha(pri, 0.18)};
                    border-radius: 6px;
                    padding: 4px 10px;
                    white-space: nowrap;
                    flex-shrink: 0;
                }
            </style>

            <div id="tms-bottom-left-actions">
                <button id="tms-bottom-save-btn">💾 Save Trip</button>
                <button id="tms-bottom-discard-btn">✖ Discard</button>
                <span id="tms-bottom-save-info">${soInfo}${tripInfo}</span>
                <span id="tms-bottom-save-saved">✅ Saved!</span>
                <span id="tms-bottom-save-no-changes">✔ No changes</span>
            </div>

            <div id="tms-bottom-right-actions">
                <button id="tms-bottom-payment-btn">💵 Add Payment</button>
            </div>
        </div>
    `);

    // ── Sync info text + bar highlight based on dirty state ────────
    function _sync_dirty_state() {
        const dirty = frm.is_dirty();
        const $wrap = $("#tms-bottom-save-wrap");
        const $info = $("#tms-bottom-save-info");
        const $discard = $("#tms-bottom-discard-btn");
        const $payment = $("#tms-bottom-payment-btn");
        if (dirty) {
            $wrap.addClass("tms-has-changes");
            $info.html(`⌨️ <b>Ctrl+S</b> save &nbsp;·&nbsp; <span style="font-size:10px;opacity:0.75;">Ctrl+D discard</span> · ${soInfo}${tripInfo}`);
            $discard.prop("disabled", false);
            $payment.prop("disabled", true);
        } else {
            $wrap.removeClass("tms-has-changes");
            $info.html(`${soInfo}${tripInfo}`);
            $discard.prop("disabled", true);
            $payment.prop("disabled", frm.is_new());
        }
    }

    // ── Poll dirty state every 600ms ───────────────────────────────
    if (frm._tms_dirty_timer) clearInterval(frm._tms_dirty_timer);
    frm._tms_dirty_timer = setInterval(_sync_dirty_state, 600);
    _sync_dirty_state();

    // ── Click: always enabled — mimics Frappe top Save button ──────
    $bar.find("#tms-bottom-save-btn").on("click", function () {
        if (!frm.is_dirty()) {
            // Same behaviour as Frappe's own Save button when no changes
            const $nc = $("#tms-bottom-save-no-changes");
            $nc.show();
            setTimeout(() => $nc.fadeOut(400), 1800);
            return;
        }
        const $btn = $(this);
        $btn.html("⏳ Saving…").prop("disabled", true);
        frm.save()
            .then(() => {
                $btn.html("💾 Save Trip").prop("disabled", false);
                const $badge = $("#tms-bottom-save-saved");
                $badge.show();
                setTimeout(() => $badge.fadeOut(400), 2200);
            })
            .catch(() => {
                $btn.html("💾 Save Trip").prop("disabled", false);
                _sync_dirty_state();
            });
    });

    // ── PAYMENT BUTTON — Add Payment ────────────────────────────────
    $bar.find("#tms-bottom-payment-btn").on("click", function () {
        if (frm.is_new() || frm.is_dirty()) {
            frappe.show_alert({
                message: __("💾 Please save the trip first."),
                indicator: "orange"
            }, 4);
            return;
        }
        const d = new frappe.ui.Dialog({
            title: __("Add Payment"),
            fields: [
                { fieldname: "trip_no", fieldtype: "Link", options: "Trip", label: __("Trip No"), default: frm.doc.name, read_only: 1 },
                { fieldname: "col_break1", fieldtype: "Column Break" },
                { fieldname: "date", fieldtype: "Date", label: __("Date"), reqd: 1, default: frappe.datetime.get_today() },
                { fieldname: "col_break_type", fieldtype: "Column Break" },
                { fieldname: "type", fieldtype: "Select", options: "Loading\nUnloading\nExtra Expense", label: __("Payment Type"), reqd: 1, default: "Loading" },
                { fieldname: "sec_balance", fieldtype: "Section Break", hide_border: 1 },
                { fieldname: "balance_info", fieldtype: "HTML", label: "" },
                { fieldname: "sec_payee", fieldtype: "Section Break" },
                { fieldname: "col_break2", fieldtype: "Column Break" },
                { fieldname: "vendor_supplier", fieldtype: "Link", options: "Supplier", label: __("Vendor/Supplier"), depends_on: "eval:doc.type=='Extra Expense' || doc.type=='Loading' || doc.type=='Unloading'" },
                { fieldname: "col_break3", fieldtype: "Column Break" },
                { fieldname: "amount", fieldtype: "Currency", label: __("Amount"), reqd: 1 },
                { fieldname: "sec_accounting", fieldtype: "Section Break", label: __("Accounting") },
                /* ── OLD accounting fields (kept for reference) — replaced to match Vendor Payment / Payment logic ──
                { fieldname: "mode_of_payment", fieldtype: "Select", options: "Cash\nBank Transfer\nCheque\nUPI\nCredit Card", label: __("Mode of Payment"), reqd: 1, default: "Bank Transfer" },
                { fieldname: "col_break4", fieldtype: "Column Break" },
                { fieldname: "paid_from_account", fieldtype: "Link", options: "Account Head", label: __("Paid From Account (Bank/Cash)"),
                  depends_on: "eval:in_list(['Bank Transfer','Cheque','Cash'], doc.mode_of_payment)",
                  mandatory_depends_on: "eval:in_list(['Bank Transfer','Cheque','Cash'], doc.mode_of_payment)" },
                { fieldname: "upi_id", fieldtype: "Data", label: __("UPI ID"),
                  depends_on: "eval:doc.mode_of_payment === 'UPI'",
                  mandatory_depends_on: "eval:doc.mode_of_payment === 'UPI'" },
                { fieldname: "reference_no", fieldtype: "Data", label: __("Reference No"),
                  depends_on: "eval:in_list(['Bank Transfer','Cheque'], doc.mode_of_payment)",
                  mandatory_depends_on: "eval:in_list(['Bank Transfer','Cheque'], doc.mode_of_payment)" },
                ── end OLD ── */
                // Options + logic aligned with Vendor Payment / Payment doctypes: no "Credit Card";
                // UPI also requires Paid From Account; Reference No shows for UPI too.
                { fieldname: "mode_of_payment", fieldtype: "Select", options: "Cash\nBank Transfer\nCheque\nUPI", label: __("Mode of Payment"), reqd: 1, default: "Bank Transfer" },
                { fieldname: "col_break4", fieldtype: "Column Break" },
                { fieldname: "paid_from_account", fieldtype: "Link", options: "Account Head", label: __("Paid From Account (Bank/Cash)"),
                  depends_on: "eval:in_list(['Bank Transfer','Cheque','Cash','UPI'], doc.mode_of_payment)",
                  mandatory_depends_on: "eval:in_list(['Bank Transfer','Cheque','Cash','UPI'], doc.mode_of_payment)" },
                { fieldname: "upi_id", fieldtype: "Data", label: __("UPI ID"),
                  depends_on: "eval:doc.mode_of_payment === 'UPI'",
                  mandatory_depends_on: "eval:doc.mode_of_payment === 'UPI'" },
                // Reference No: visible for all modes (Cash included); mandatory only for Bank Transfer/Cheque
                // (matches payment.py / vendor_payment.py on_submit validation).
                { fieldname: "reference_no", fieldtype: "Data", label: __("Reference No"),
                  depends_on: "eval:in_list(['Bank Transfer','Cheque','UPI','Cash'], doc.mode_of_payment)",
                  mandatory_depends_on: "eval:in_list(['Bank Transfer','Cheque'], doc.mode_of_payment)" },
                { fieldname: "sec_existing", fieldtype: "Section Break", label: __("Existing Payments for this Trip") },
                { fieldname: "trip_payments_html", fieldtype: "HTML", label: __("Trip Payments") },
            ],
            primary_action_label: __("Save & Submit"),
            primary_action(values) {
                d.disable_primary_action();
                frappe.call({
                    method: "frappe.client.insert",
                    args: {
                        doc: {
                            doctype: "Payment",
                            trip_no: frm.doc.name,
                            type: values.type,
                            date: values.date,
                            vendor_supplier: values.vendor_supplier || "",
                            employee: values.employee || "",
                            amount: values.amount,
                            mode_of_payment: values.mode_of_payment,
                            paid_from_account: values.paid_from_account || "",
                            upi_id: values.upi_id || "",
                            reference_no: values.reference_no || "",
                        }
                    },
                    callback(r) {
                        if (r.exc) { d.enable_primary_action(); return; }
                        frappe.call({
                            method: "frappe.client.submit",
                            args: { doc: r.message },
                            callback(sr) {
                                if (sr.exc) { d.enable_primary_action(); return; }
                                d.hide();
                                frappe.show_alert({ message: __("Payment submitted successfully."), indicator: "green" }, 4);
                                frm.reload_doc();
                            }
                        });
                    }
                });
            }
        });
        d.show();

        // Set Account Head query based on mode_of_payment
        d.fields_dict.paid_from_account.get_query = function() {
            return { filters: { group: "BANK" } };
        };
        // Clear account when mode changes
        d.fields_dict.mode_of_payment.df.onchange = function() {
            d.set_value("paid_from_account", "");
        };

        // Balance info helper
        function refresh_balance_info(payment_type) {
            const $wrap = d.get_field("balance_info").$wrapper;
            if (!payment_type) { $wrap.html(""); return; }
            frappe.call({
                method: "logicore.logicore.doctype.payment.payment.get_trip_payment_balance",
                args: { trip_no: frm.doc.name, payment_type },
                callback(r) {
                    if (!r.message) return;
                    const { limit, already_paid, balance } = r.message;
                    const fmt = v => "₹ " + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2 });
                    const color = balance <= 0 ? "#2e7d32" : already_paid > 0 ? "#e65100" : "#c62828";
                    const bg    = balance <= 0 ? "#e8f5e9" : already_paid > 0 ? "#fff3e0" : "#ffebee";
                    $wrap.html(`
                        <div style="display:flex; align-items:stretch; background:${bg};
                                    border:1px solid ${color}55; border-radius:5px;
                                    font-size:12px; overflow:hidden; width:100%; margin-bottom:8px;">
                            <div style="padding:7px 14px; border-right:1px solid ${color}44; white-space:nowrap; background:${color}11;">
                                <b style="color:${color}; font-size:12px;">${frappe.utils.escape_html(payment_type)}</b>
                            </div>
                            <div style="flex:1; padding:7px 14px; border-right:1px solid ${color}33; white-space:nowrap;">
                                <span style="color:#888;">Trip Amount &nbsp;</span><b style="color:#333;">${fmt(limit)}</b>
                            </div>
                            <div style="flex:1; padding:7px 14px; border-right:1px solid ${color}33; white-space:nowrap;">
                                <span style="color:#888;">Paid &nbsp;</span><b style="color:#333;">${fmt(already_paid)}</b>
                            </div>
                            <div style="flex:1; padding:7px 14px; white-space:nowrap;">
                                <span style="color:#888;">Available &nbsp;</span><b style="color:${color}; font-size:13px;">${fmt(balance)}</b>
                            </div>
                        </div>
                    `);
                }
            });
        }
        d.fields_dict.type.df.onchange = () => refresh_balance_info(d.get_value("type"));
        refresh_balance_info("Loading");

        // Load existing payments for this trip
        frappe.call({
            method: "logicore.logicore.doctype.payment.payment.get_trip_payments",
            args: { trip_no: frm.doc.name },
            callback(r) {
                const rows = r.message || [];
                const wrapper = d.get_field("trip_payments_html").$wrapper;
                if (!rows.length) {
                    wrapper.html('<p style="color:#888;font-size:12px">No payments yet for this trip.</p>');
                    return;
                }
                let total = rows.reduce((s, p) => s + flt(p.amount), 0);
                let html = `<table class="table table-bordered table-condensed" style="font-size:12px;margin-bottom:4px">
                    <thead style="background:#6c5ce7;color:#fff">
                        <tr><th>Reference</th><th>Date</th><th>Vendor / Employee</th><th>Type</th><th style="text-align:right">Amount</th></tr>
                    </thead><tbody>`;
                rows.forEach(p => {
                    html += `<tr>
                        <td><a href="/app/payment/${frappe.utils.escape_html(p.name)}" target="_blank">${frappe.utils.escape_html(p.name)}</a></td>
                        <td>${frappe.datetime.str_to_user(p.date)}</td>
                        <td>${frappe.utils.escape_html(p.party || "—")}</td>
                        <td>${frappe.utils.escape_html(p.type)}</td>
                        <td style="text-align:right">₹ ${flt(p.amount).toLocaleString("en-IN", {minimumFractionDigits:2})}</td>
                    </tr>`;
                });
                html += `</tbody><tfoot><tr style="font-weight:700">
                    <td colspan="4">Total (${rows.length} payment${rows.length > 1 ? "s" : ""})</td>
                    <td style="text-align:right;color:#6c5ce7">₹ ${flt(total).toLocaleString("en-IN", {minimumFractionDigits:2})}</td>
                </tr></tfoot></table>`;
                wrapper.html(html);
            }
        });
    });

    // ── Discard button: always go back to Trip list ─────────────────
    $bar.find("#tms-bottom-discard-btn").on("click", function () {
        if (!frm.is_dirty()) {
            frappe.set_route("List", "Trip");
            return;
        }
        frappe.confirm(
            __("Discard all unsaved changes and go back to Trip list?"),
            () => frappe.set_route("List", "Trip")
        );
    });
    
    // ── Ctrl+S / Cmd+S ─────────────────────────────────────────────
    $(document).off("keydown.tms_bottom_save").on("keydown.tms_bottom_save", function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === "s" && frm.$wrapper.is(":visible")) {
            e.preventDefault();
            if (frm.is_dirty()) {
                frm.save();
            } else {
                const $nc = $("#tms-bottom-save-no-changes");
                $nc.show();
                setTimeout(() => $nc.fadeOut(400), 1800);
            }
        }
    });

    // ── Ctrl+D — Discard ───────────────────────────────────────────
    $(document).off("keydown.tms_bottom_discard").on("keydown.tms_bottom_discard", function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === "d" && frm.$wrapper.is(":visible")) {
            e.preventDefault();
            if (!frm.is_dirty()) {
                frappe.set_route("List", "Trip");
                return;
            }
            frappe.confirm(
                __("Discard all unsaved changes and go back to Trip list?"),
                () => frappe.set_route("List", "Trip")
            );
        }
    });

    // ── Clean up timer on page hide ────────────────────────────────
    frm.$wrapper.closest(".page-container")
        .off("page:hide.tms_dirty_poll")
        .on("page:hide.tms_dirty_poll", function () {
            if (frm._tms_dirty_timer) {
                clearInterval(frm._tms_dirty_timer);
                frm._tms_dirty_timer = null;
            }
            $(document).off("keydown.tms_bottom_discard");
        });

    // ── Attach below form tabs ──────────────────────────────────────
    const $host = frm.$wrapper.find(".form-page").first().length
        ? frm.$wrapper.find(".form-page").first()
        : (frm.$wrapper.find(".page-form").first().length
            ? frm.$wrapper.find(".page-form").first()
            : frm.$wrapper);

    $host.append($bar);
}

// ══════════════════════════════════════════════════════════════════
//  DEFAULT CUSTOMER — set from Business Format on new/changed BF
// ══════════════════════════════════════════════════════════════════

function _set_default_customer(frm, bf_doc) {
    if (bf_doc && bf_doc.default_customer) {
        frm.set_value("customer", bf_doc.default_customer);
    } else {
        frm.set_value("customer", "");
        // bf_doc truthy = a BF was selected but has no default_customer
        // bf_doc null   = BF was cleared, no warning needed
        if (bf_doc && frm.doc.business_format) {
            frappe.show_alert({
                message: __('No default customer set for Business Format "{0}". Please select a customer manually.', [frm.doc.business_format]),
                indicator: "orange",
            });
        }
    }
}

function fetch_start_km_for_vehicle(frm) {
	if (!frm.doc.vehicle_no) return;
	const requested_vehicle_no = frm.doc.vehicle_no;
	frappe.call({
		method: "logicore.logicore.doctype.trip.trip.get_vehicle_last_trip_end_km",
		args: { vehicle_no: requested_vehicle_no, trip_name: frm.doc.name },
		callback(r) {
			if (frm.doc.vehicle_no !== requested_vehicle_no) return;
			if (r.message) {
				frm.set_value("start_km", r.message);
				frappe.show_alert({ message: __("Start KM set from last trip end KM: {0}", [r.message]), indicator: "blue" }, 4);
			} else {
				frappe.show_alert({ message: __("No previous trip found for vehicle {0}.", [requested_vehicle_no]), indicator: "orange" }, 4);
			}
		}
	});
}

function setup_vehicle_filter(frm) {
    // ── Vehicle No — NO vendor filter, show ALL vehicles ──────────
    frm.set_query("vehicle_no", function () {
        return {};
    });

}

// function render_vendor_payment_table(frm) {
//     const fd = frm.fields_dict.vendor_payment_details_html;
//     if (!fd || !fd.$wrapper) return;

//     // Hide the cramped wrapper — we'll inject standalone below the section
//     fd.$wrapper.html("").closest(".form-column").css("display", "none");

//     // Remove any previously injected table
//     $("#tms-vp-table-standalone").remove();

//     // ── Colors — use the server-resolved color, not the combo default ──
//     const combo  = frm._tms_resolved_combo || get_combo_for_trip(frm.doc.trip_type);
//     const pri    = frm._tms_resolved_color  || (combo && combo.primary)        || "#3B4FE4";
//     const secBdr = (combo && combo.section_border) || hex_alpha(pri, 0.28);
//     const fldBg  = (combo && combo.field_bg)       || hex_alpha(pri, 0.05);
//     const hdgClr = (combo && combo.heading_color)  || "#1E1B4B";
//     const lblClr = (combo && combo.label_color)    || "#3730A3";
//     const radius = (combo && combo.radius)         || "10px";

//     const payments = (frm.doc.__onload && frm.doc.__onload.vendor_payments) || [];

//     const fmt_inr = v => {
//         const n = flt(v);
//         const abs = Math.abs(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
//         return (n < 0 ? "−\u00A0₹" : "₹\u00A0") + abs;
//     };

//     const totalPaid = payments.reduce((s, p) => s + flt(p.payment_amount), 0);

//     const rows_html = payments.length === 0
//         ? `<tr>
//             <td colspan="3" style="text-align:center;padding:20px;color:${lblClr};font-size:12px;opacity:0.6;">
//                 No payments recorded yet
//             </td>
//            </tr>`
//         : payments.map((p, i) => {
//             const date = p.posting_date ? frappe.datetime.str_to_user(p.posting_date) : "—";
//             const ref  = frappe.utils.escape_html(p.reference || "—");
//             return `<tr style="background:${i % 2 === 0 ? "#ffffff" : fldBg};">
//                 <td style="padding:9px 14px;border-bottom:1px solid ${secBdr};font-size:12px;">
//                     <a href="/app/vendor-payment/${ref}"
//                        style="color:${pri};font-weight:600;text-decoration:none;"
//                        onmouseover="this.style.textDecoration='underline'"
//                        onmouseout="this.style.textDecoration='none'">${ref}</a>
//                 </td>
//                 <td style="padding:9px 14px;border-bottom:1px solid ${secBdr};color:${hdgClr};font-size:12px;">
//                     ${frappe.utils.escape_html(date)}
//                 </td>
//                 <td style="padding:9px 14px;border-bottom:1px solid ${secBdr};text-align:right;font-size:12px;font-weight:700;color:${hdgClr};">
//                     ${fmt_inr(flt(p.payment_amount))}
//                 </td>
//             </tr>`;
//         }).join("");
//     const tableHtml = `
//         <div style="padding:0 2px 12px;">
//             <div style="border:1.5px solid ${secBdr};border-radius:${radius};overflow:hidden;">
//                 <table style="width:100%;border-collapse:collapse;">
//                     <thead>
//                         <tr style="background:${pri};">
//                             <th style="padding:9px 14px;text-align:left;font-size:10px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.7px;width:40%;">Reference</th>
//                             <th style="padding:9px 14px;text-align:left;font-size:10px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.7px;width:30%;">Posting Date</th>
//                             <th style="padding:9px 14px;text-align:right;font-size:10px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.7px;width:30%;">Amount</th>
//                         </tr>
//                     </thead>
//                     <tbody>${rows_html}</tbody>
//                     ${payments.length > 0 ? `
//                     <tfoot>
//                         <tr style="background:${fldBg};border-top:1.5px solid ${secBdr};">
//                             <td colspan="2" style="padding:9px 14px;font-size:11px;font-weight:700;color:${lblClr};">
//                                 Total (${payments.length} payment${payments.length !== 1 ? "s" : ""})
//                             </td>
//                             <td style="padding:9px 14px;text-align:right;font-size:13px;font-weight:800;color:${pri};">
//                                 ${fmt_inr(totalPaid)}
//                             </td>
//                         </tr>
//                     </tfoot>` : ""}
//                 </table>
//             </div>
//         </div>`;

//     // Inject as a full-width block directly inside the section body
//     const $section = fd.$wrapper.closest(".form-section").find(".section-body").first();
//     $section.append($(`<div id="tms-vp-table-standalone" style="width:100%;padding:0 15px 4px;">${tableHtml}</div>`));
// }
function render_vendor_payment_table(frm) {
    const fd = frm.fields_dict.vendor_payment_details_html;
    if (!fd || !fd.$wrapper) return;

    // Hide the cramped wrapper — we'll inject standalone below the section
    fd.$wrapper.html("").closest(".form-column").css("display", "none");

    // Remove any previously injected table
    $("#tms-vp-table-standalone").remove();

    // ── Colors — use the server-resolved color, not the combo default ──
    const combo  = frm._tms_resolved_combo || get_combo_for_trip(frm.doc.trip_type);
    const isDark = get_frappe_theme() === "dark";
    const pri    = frm._tms_resolved_color  || (combo && combo.primary)        || "#3B4FE4";
    const secBdr = (combo && combo.section_border) || hex_alpha(pri, 0.28);
    const fldBg  = (combo && combo.field_bg)       || hex_alpha(pri, 0.05);
    const hdgClr = (combo && combo.heading_color)  || "#1E1B4B";
    const lblClr = (combo && combo.label_color)    || "#3730A3";
    const radius = (combo && combo.radius)         || "10px";
    const cardBg  = (combo && combo.card_bg)       || (isDark ? "#1F2937" : "#FFFFFF");
    const rowBgA  = isDark ? cardBg : "#FFFFFF";
    const rowBgB  = isDark ? hex_alpha(pri, 0.12) : fldBg;
    const textClr = isDark ? "#E5E7EB" : hdgClr;
    const mutedClr = isDark ? "#94A3B8" : lblClr;
    const inputBg  = isDark ? "#111827" : "#FFFFFF";
    const inputBorder = isDark ? hex_alpha(pri, 0.35) : secBdr;
    const inputText = isDark ? "#E5E7EB" : hdgClr;
    const inputPlaceholder = isDark ? "#94A3B8" : "#64748B";
    const footerBg = isDark ? hex_alpha("#FFFFFF", 0.04) : fldBg;
    const footerBorder = isDark ? hex_alpha("#FFFFFF", 0.10) : secBdr;
    const accentClr = isDark ? "#34D399" : "#00b894";
    const numCellBg = isDark ? "rgba(255,255,255,0.015)" : "transparent";

    // ── Data: Combine both Vendor Payments & Regular Payments ──
    const raw_vendor_payments = (frm.doc.__onload && frm.doc.__onload.vendor_payments) || [];
    const raw_other_payments = (frm.doc.__onload && frm.doc.__onload.payments) || [];

    const combined_payments = [
        ...raw_vendor_payments.map(p => {
            const generated_id = p.name || p.reference;
            return {
                reference: generated_id,
                date: p.payment_date,
                amount: p.payment_amount,
                payment_amount: p.payment_amount,
                transfer_amount: p.transfer_amount,
                tds_amount: p.tds_amount,
                employee_lr_money: p.employee_lr_money,
                company_lr_money: p.company_lr_money,
                type: "Vendor Payment",
                party: p.vendor || "",
                url: `/app/vendor-payment/${generated_id}`
            };
        }),
        ...raw_other_payments.map(p => {
            const generated_id = p.name;
            return {
                reference: generated_id,
                date: p.payment_date,
                amount: p.amount,
                payment_amount: p.amount,
                transfer_amount: p.amount,
                tds_amount: 0,
                employee_lr_money: 0,
                company_lr_money: 0,
                type: p.payment_type,
                party: p.party || "",
                url: `/app/payment/${generated_id}`
            };
        })
    ];

    combined_payments.sort((a, b) => new Date(a.date) - new Date(b.date));

    const all_payments = combined_payments;

    const fmt_inr = v => {
        const n = flt(v);
        const abs = Math.abs(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        return (n < 0 ? "− ₹" : "₹ ") + abs;
    };

    const all_types = [...new Set(all_payments.map(p => p.type).filter(Boolean))].sort();

    const TH = `padding:9px 12px;font-size:10px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.6px;white-space:nowrap;`;
    const THL = TH + `text-align:left;`;
    const THR = TH + `text-align:right;`;
    const TD  = `padding:8px 12px;border-bottom:1px solid ${secBdr};font-size:12px;color:${textClr};white-space:nowrap;`;
    const TDR = TD + `text-align:right;font-variant-numeric:tabular-nums;font-weight:600;`;
    const TDM = TD + `color:${mutedClr};font-size:11px;`;

    function build_rows(payments) {
        if (payments.length === 0) {
            return `<tr><td colspan="7" style="text-align:center;padding:24px;color:${mutedClr};font-size:12px;">No payments match the filter</td></tr>`;
        }
        return payments.map((p, i) => {
            const date  = p.date ? frappe.datetime.str_to_user(p.date) : "—";
            const ref   = frappe.utils.escape_html(p.reference || "—");
            const type  = frappe.utils.escape_html(p.type || "—");
            const party = frappe.utils.escape_html(p.party || "—");
            const rowBg = i % 2 === 0 ? rowBgA : rowBgB;
            const isVP  = p.type === "Vendor Payment";
            const gross = fmt_inr(isVP ? flt(p.payment_amount) : flt(p.amount));
            const tds   = isVP && flt(p.tds_amount)          ? fmt_inr(flt(p.tds_amount))          : "—";
            const empLr = isVP && flt(p.employee_lr_money)   ? fmt_inr(flt(p.employee_lr_money))   : "—";
            const coLr  = isVP && flt(p.company_lr_money)    ? fmt_inr(flt(p.company_lr_money))    : "—";
            const net   = fmt_inr(isVP ? flt(p.transfer_amount || p.payment_amount) : flt(p.amount));
            const deductClr = `color:#ef4444;`;
            const netClr    = `color:${accentClr};font-weight:700;`;

            return `<tr style="background:${rowBg};">
                <td style="${TD}">
                    <a href="${p.url}" target="_blank" style="color:${pri};font-weight:600;text-decoration:none;"
                       onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">${ref}</a>
                </td>
                <td style="${TDM}">${frappe.utils.escape_html(date)}</td>
                <td style="${TD}">${party}</td>
                <td style="${TDM}">${type}</td>
                <td style="${TDR}">${gross}</td>
                <td style="${TDR}${tds   !== "—" ? deductClr : `color:${mutedClr};font-weight:400;`}">${tds}</td>
                <td style="${TDR}${empLr !== "—" ? deductClr : `color:${mutedClr};font-weight:400;`}">${empLr}</td>
                <td style="${TDR}${coLr  !== "—" ? deductClr : `color:${mutedClr};font-weight:400;`}">${coLr}</td>
                <td style="${TDR}${netClr}">${net}</td>
            </tr>`;
        }).join("");
    }

    function build_footer(payments) {
        if (payments.length === 0) return "";
        const fStyle = `padding:9px 12px;font-size:12px;font-weight:700;background:${footerBg};border-top:2px solid ${footerBorder};`;
        const totGross  = payments.reduce((s,p) => s + flt(p.type === "Vendor Payment" ? p.payment_amount : p.amount), 0);
        const totTds    = payments.reduce((s,p) => s + flt(p.tds_amount), 0);
        const totEmpLr  = payments.reduce((s,p) => s + flt(p.employee_lr_money), 0);
        const totCoLr   = payments.reduce((s,p) => s + flt(p.company_lr_money), 0);
        const totNet    = payments.reduce((s,p) => s + flt(p.type === "Vendor Payment" ? (p.transfer_amount || p.payment_amount) : p.amount), 0);
        return `<tr>
            <td colspan="4" style="${fStyle}color:${mutedClr};">Total (${payments.length} payment${payments.length !== 1 ? "s" : ""})</td>
            <td style="${fStyle}text-align:right;color:${textClr};">${fmt_inr(totGross)}</td>
            <td style="${fStyle}text-align:right;color:#ef4444;">${totTds ? fmt_inr(totTds) : "—"}</td>
            <td style="${fStyle}text-align:right;color:#ef4444;">${totEmpLr ? fmt_inr(totEmpLr) : "—"}</td>
            <td style="${fStyle}text-align:right;color:#ef4444;">${totCoLr ? fmt_inr(totCoLr) : "—"}</td>
            <td style="${fStyle}text-align:right;color:${accentClr};font-size:13px;">${fmt_inr(totNet)}</td>
        </tr>`;
    }

    const type_options = all_types.map(t => `<option value="${frappe.utils.escape_html(t)}">${frappe.utils.escape_html(t)}</option>`).join("");

    const tableHtml = `
        <div style="padding:0 2px 12px;">
            <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                <span style="font-size:11px;font-weight:700;color:${mutedClr};">Filters:</span>
                <select id="tms-pmt-filter-type" style="font-size:11px;padding:4px 8px;border:1px solid ${inputBorder};border-radius:5px;color:${inputText};background:${inputBg};cursor:pointer;">
                    <option value="">All Types</option>
                    ${type_options}
                </select>
                <input id="tms-pmt-filter-party" type="text" placeholder="Vendor / Employee…"
                    style="font-size:11px;padding:4px 8px;border:1px solid ${inputBorder};border-radius:5px;color:${inputText};background:${inputBg};width:150px;" />
                <input id="tms-pmt-filter-from" type="date"
                    style="font-size:11px;padding:4px 8px;border:1px solid ${inputBorder};border-radius:5px;color:${inputText};background:${inputBg};" />
                <span style="font-size:11px;color:${mutedClr};">to</span>
                <input id="tms-pmt-filter-to" type="date"
                    style="font-size:11px;padding:4px 8px;border:1px solid ${inputBorder};border-radius:5px;color:${inputText};background:${inputBg};" />
                <button id="tms-pmt-filter-clear" style="font-size:11px;padding:4px 10px;border:1px solid ${inputBorder};border-radius:5px;background:${inputBg};color:${mutedClr};cursor:pointer;">✕ Clear</button>
            </div>
            <div style="border:1px solid ${secBdr};border-radius:${radius};overflow-x:auto;-webkit-overflow-scrolling:touch;background:${cardBg};">
                <table style="width:100%;min-width:860px;border-collapse:collapse;table-layout:auto;">
                    <thead>
                        <tr style="background:${pri};">
                            <th style="${THL}width:14%;">Reference</th>
                            <th style="${THL}width:10%;">Date</th>
                            <th style="${THL}width:18%;">Vendor / Employee</th>
                            <th style="${THL}width:14%;">Type</th>
                            <th style="${THR}width:11%;">Payment Amt</th>
                            <th style="${THR}width:8%;">TDS</th>
                            <th style="${THR}width:10%;">Emp LR</th>
                            <th style="${THR}width:10%;">Co LR</th>
                            <th style="${THR}width:11%;">Net Transfer</th>
                        </tr>
                    </thead>
                    <tbody id="tms-pmt-tbody">${build_rows(all_payments)}</tbody>
                    <tfoot id="tms-pmt-tfoot">
                        ${build_footer(all_payments)}
                    </tfoot>
                </table>
            </div>
        </div>`;

    const $section = fd.$wrapper.closest(".form-section").find(".section-body").first();
    $section.append($(`<div id="tms-vp-table-standalone" style="width:100%;padding:0 15px 4px;background:transparent;">${tableHtml}</div>`));

    function apply_filters() {
        const type_val  = $("#tms-pmt-filter-type").val();
        const party_val = $("#tms-pmt-filter-party").val().toLowerCase().trim();
        const from_val  = $("#tms-pmt-filter-from").val();
        const to_val    = $("#tms-pmt-filter-to").val();
        const filtered  = all_payments.filter(p => {
            if (type_val  && p.type !== type_val) return false;
            if (party_val && !(p.party || "").toLowerCase().includes(party_val)) return false;
            if (from_val  && p.date && p.date < from_val) return false;
            if (to_val    && p.date && p.date > to_val)   return false;
            return true;
        });
        $("#tms-pmt-tbody").html(build_rows(filtered));
        $("#tms-pmt-tfoot").html(build_footer(filtered));
    }

    $("#tms-pmt-filter-type, #tms-pmt-filter-from, #tms-pmt-filter-to").on("change", apply_filters);
    $("#tms-pmt-filter-party").on("input", apply_filters);
    $("#tms-pmt-filter-clear").on("click", function () {
        $("#tms-pmt-filter-type, #tms-pmt-filter-from, #tms-pmt-filter-to").val("");
        $("#tms-pmt-filter-party").val("");
        apply_filters();
    });

    // Auto-refresh when user switches back from the new tab after editing
    if (!window._tms_vp_visib_bound) {
        window._tms_vp_visib_bound = true;
        document.addEventListener("visibilitychange", function () {
            if (document.visibilityState === "visible" && cur_frm && cur_frm.doctype === "Trip" && !cur_frm.is_dirty()) {
                cur_frm.reload_doc();
            }
        });
    }
}

function render_receipt_table(frm) {
    $("#tms-receipt-table-wrap").remove();

    const receipts = (frm.doc.__onload && frm.doc.__onload.receipts) || [];
    if (!receipts.length) return;

    const combo   = frm._tms_resolved_combo || get_combo_for_trip(frm.doc.trip_type);
    const isDark  = get_frappe_theme() === "dark";
    const pri     = frm._tms_resolved_color || (combo && combo.primary) || "#3B4FE4";
    const secBdr  = (combo && combo.section_border) || hex_alpha(pri, 0.28);
    const fldBg   = (combo && combo.field_bg)       || hex_alpha(pri, 0.05);
    const hdgClr  = (combo && combo.heading_color)  || "#1E1B4B";
    const lblClr  = (combo && combo.label_color)    || "#3730A3";
    const radius  = (combo && combo.radius)         || "10px";
    const cardBg  = (combo && combo.card_bg)        || (isDark ? "#1F2937" : "#FFFFFF");
    const rowBgA  = isDark ? cardBg : "#FFFFFF";
    const rowBgB  = isDark ? hex_alpha(pri, 0.12) : fldBg;
    const textClr = isDark ? "#E5E7EB" : hdgClr;
    const mutedClr = isDark ? "#94A3B8" : lblClr;
    const footerBg = isDark ? hex_alpha("#FFFFFF", 0.04) : fldBg;
    const footerBdr = isDark ? hex_alpha("#FFFFFF", 0.10) : secBdr;
    const accentClr = isDark ? "#34D399" : "#00b894";
    const deductClr = isDark ? "#fca5a5" : "#ef4444";

    const fmt_inr = v => {
        const n = flt(v);
        const abs = Math.abs(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        return (n < 0 ? "− ₹" : "₹ ") + abs;
    };
    const fmt_cell = v => flt(v) ? fmt_inr(v) : "—";

    const TH  = `padding:9px 12px;font-size:10px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.6px;white-space:nowrap;`;
    const THL = TH + `text-align:left;`;
    const THR = TH + `text-align:right;`;
    const TD  = `padding:8px 12px;border-bottom:1px solid ${secBdr};font-size:12px;color:${textClr};white-space:nowrap;`;
    const TDR = TD + `text-align:right;font-variant-numeric:tabular-nums;font-weight:600;`;
    const TDM = TD + `color:${mutedClr};font-size:11px;`;

    // Totals — trip invoice from trip fields (gross), deductions from receipts
    const trip_invoice    = flt(frm.doc.customer_freight) + flt(frm.doc.total_approved_addl_amount);
    const tot_brokerage   = receipts.reduce((s, r) => s + flt(r.brokerage_amount), 0);
    const tot_lr          = receipts.reduce((s, r) => s + flt(r.lr_money), 0);
    const tot_tds         = receipts.reduce((s, r) => s + flt(r.tds_amount), 0);
    const tot_received    = receipts.reduce((s, r) => s + flt(r.received_amount), 0);

    const rows = receipts.map((r, i) => {
        const ref   = frappe.utils.escape_html(r.name || "—");
        const date  = r.payment_date ? frappe.datetime.str_to_user(r.payment_date) : "—";
        const rowBg = i % 2 === 0 ? rowBgA : rowBgB;
        return `<tr style="background:${rowBg};">
            <td style="${TD}">
                <a href="/app/receipt/${r.name}" target="_blank"
                   style="color:${pri};font-weight:600;text-decoration:none;"
                   onmouseover="this.style.textDecoration='underline'"
                   onmouseout="this.style.textDecoration='none'">${ref}</a>
            </td>
            <td style="${TDM}">${frappe.utils.escape_html(date)}</td>
            <td style="${TDR}${flt(r.brokerage_amount) ? `color:${deductClr};` : `color:${mutedClr};font-weight:400;`}">${fmt_cell(r.brokerage_amount)}</td>
            <td style="${TDR}${flt(r.lr_money) ? `color:${deductClr};` : `color:${mutedClr};font-weight:400;`}">${fmt_cell(r.lr_money)}</td>
            <td style="${TDR}${flt(r.tds_amount) ? `color:${deductClr};` : `color:${mutedClr};font-weight:400;`}">${fmt_cell(r.tds_amount)}</td>
            <td style="${TDR}color:${accentClr};font-weight:700;">${fmt_inr(flt(r.received_amount))}</td>
        </tr>`;
    }).join("");

    const tot_deductions  = tot_brokerage + tot_lr + tot_tds;
    const net_receivable  = trip_invoice - tot_deductions;
    const balance         = net_receivable - tot_received;
    const balClr          = balance > 0.01 ? "#ef4444" : accentClr;
    const balLabel        = balance > 0.01 ? "Pending" : balance < -0.01 ? "Overpaid" : "Settled";

    const fS  = `padding:9px 12px;font-size:12px;font-weight:700;background:${footerBg};border-top:2px solid ${footerBdr};`;
    const footer = `<tr>
        <td colspan="2" style="${fS}color:${mutedClr};">Total (${receipts.length} receipt${receipts.length !== 1 ? "s" : ""})</td>
        <td style="${fS}text-align:right;color:${deductClr};">${tot_brokerage ? fmt_inr(tot_brokerage) : "—"}</td>
        <td style="${fS}text-align:right;color:${deductClr};">${tot_lr ? fmt_inr(tot_lr) : "—"}</td>
        <td style="${fS}text-align:right;color:${deductClr};">${tot_tds ? fmt_inr(tot_tds) : "—"}</td>
        <td style="${fS}text-align:right;color:${accentClr};font-size:13px;">${fmt_inr(tot_received)}</td>
    </tr>`;

    const cell = `flex:1 1 120px;min-width:100px;padding:10px 8px;text-align:center;border-bottom:1px solid ${secBdr};`;
    const lbl  = `display:block;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:${mutedClr};margin-bottom:3px;`;
    const val  = `display:block;font-size:14px;font-weight:700;`;
    const summary = `
    <div style="display:flex;flex-wrap:wrap;align-items:stretch;margin-top:8px;border:1px solid ${secBdr};border-radius:${radius};overflow:hidden;background:${cardBg};">
        <div style="${cell}border-right:1px solid ${secBdr};">
            <span style="${lbl}">Trip Total Freight</span>
            <span style="${val}color:${textClr};">${fmt_inr(trip_invoice)}</span>
        </div>
        <div style="${cell}border-right:1px solid ${secBdr};">
            <span style="${lbl}">Total Deductions</span>
            <span style="${val}color:${deductClr};">${fmt_inr(tot_deductions)}</span>
            <span style="font-size:10px;color:${mutedClr};margin-top:2px;display:block;">
                ${tot_brokerage ? `Brk ₹${(tot_brokerage/1).toLocaleString("en-IN")}` : ""}${tot_brokerage && (tot_lr || tot_tds) ? " + " : ""}${tot_lr ? `LR ₹${(tot_lr/1).toLocaleString("en-IN")}` : ""}${tot_lr && tot_tds ? " + " : ""}${tot_tds ? `TDS ₹${(tot_tds/1).toLocaleString("en-IN")}` : ""}
            </span>
        </div>
      	<div style="${cell}border-right:1px solid ${secBdr};">
	      <span style="${lbl}">Net Receivable</span>
        <span style="${val}color:${textClr};">${fmt_inr(net_receivable)}</span>
        </div>
        <div style="${cell}border-right:1px solid ${secBdr};">
            <span style="${lbl}">Received</span>
            <span style="${val}color:${accentClr};">${fmt_inr(tot_received)}</span>
        </div>
        <div style="${cell}background:${balClr}18;border-right:none;">
            <span style="${lbl}">${balLabel}</span>
            <span style="${val}color:${balClr};font-size:15px;">${fmt_inr(balance)}</span>
        </div>
    </div>`;

    const html = `
        <div style="padding:0 2px 12px;">
            <div style="margin-bottom:6px;font-size:11px;font-weight:700;color:${mutedClr};text-transform:uppercase;letter-spacing:0.6px;">Customer Receipts</div>
            <div style="border:1px solid ${secBdr};border-radius:${radius};overflow-x:auto;-webkit-overflow-scrolling:touch;background:${cardBg};">
                <table style="width:100%;min-width:600px;border-collapse:collapse;table-layout:auto;">
                    <thead>
                        <tr style="background:${pri};">
                            <th style="${THL}width:25%;">Reference</th>
                            <th style="${THL}width:14%;">Date</th>
                            <th style="${THR}width:15%;">Brokerage</th>
                            <th style="${THR}width:13%;">Broker LR</th>
                            <th style="${THR}width:11%;">TDS</th>
                            <th style="${THR}width:18%;">Actual Received</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                    <tfoot>${footer}</tfoot>
                </table>
            </div>
            ${summary}
        </div>`;

    const fd = frm.fields_dict.trip_total_amount_billed;
    if (!fd || !fd.$wrapper) return;
    fd.$wrapper.closest(".form-section").after(
        `<div id="tms-receipt-table-wrap" style="width:100%;padding:0 15px 12px;">${html}</div>`
    );
}
function _fix_other_trip_type_columns(frm) {
    if ((frm.doc.trip_type || "").toUpperCase() !== "OTHER") return;

    // Remove col-sm-12 from the two target column breaks
    frm.$wrapper.find('[data-fieldname="column_break_rxiz"]')
        .removeClass("col-sm-12");

    frm.$wrapper.find('[data-fieldname="column_break_iaiz"]')
        .removeClass("col-sm-12");
}
