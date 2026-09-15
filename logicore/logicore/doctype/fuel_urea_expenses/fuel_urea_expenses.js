// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Fuel Urea Expenses", {
// 	refresh(frm) {

// 	},
// });
// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Fuel Urea Expenses", {

//     setup(frm) {
//         ["current_odometer", "last_odoometer", "distance",
//          "liters", "kpl", "fixed_kpl",
//          "excessshort_fuel", "excessshort_fuel_rate",
//          "fuel_incentive", "expense_amount"
//         ].forEach(f => frm.set_df_property(f, "precision", "2"));
//     },

//     refresh(frm) {
//         if (frm.is_new() && !frm.doc.date) {
//             frm.set_value("date", frappe.datetime.get_today());
//         }

//         ["distance", "kpl", "excessshort_fuel", "fuel_incentive"]
//             .forEach(f => frm.set_df_property(f, "read_only", 1));

//         _style_excess_short(frm);
//         _apply_section_labels(frm);
//     },

//     // ── Vehicle change: pull last odometer using built-in get_list ──
//     vehicle(frm) {
//         if (!frm.doc.vehicle) {
//             frm.set_value("last_odoometer", 0);
//             _calc_distance(frm);
//             return;
//         }

//         const filters = [
//             ["vehicle",   "=",  frm.doc.vehicle],
//             ["docstatus", "!=", 2]
//         ];

//         if (frm.doc.name && !frm.doc.name.startsWith("new-")) {
//             filters.push(["name", "!=", frm.doc.name]);
//         }

//         frappe.call({
//             method: "frappe.client.get_list",
//             args: {
//                 doctype: "Fuel Urea Expenses",
//                 filters: filters,
//                 fields: ["current_odometer", "date"],
//                 order_by: "date desc, creation desc",
//                 limit: 1
//             },
//             callback(r) {
//                 if (r.message && r.message.length > 0) {
//                     const last_odo = r.message[0].current_odometer || 0;
//                     frm.set_value("last_odoometer", last_odo);
//                     frappe.show_alert({
//                         message: `Last odometer for this vehicle: <b>${last_odo} km</b>`,
//                         indicator: "blue"
//                     }, 4);
//                 } else {
//                     frm.set_value("last_odoometer", 0);
//                     frappe.show_alert({
//                         message: "No previous fuel entry found for this vehicle.",
//                         indicator: "orange"
//                     }, 3);
//                 }
//                 _calc_distance(frm);
//             }
//         });
//     },

//     current_odometer(frm) { _calc_distance(frm); },
//     last_odoometer(frm)   { _calc_distance(frm); },

//     liters(frm)                { _calc_kpl(frm); },
//     fixed_kpl(frm)             { _calc_incentive(frm); },
//     excessshort_fuel_rate(frm) { _calc_incentive(frm); },

//     excessshort_fuel(frm) { _style_excess_short(frm); }
// });


// // ── Helpers ──────────────────────────────────────────────────────────────────

// function _calc_distance(frm) {
//     const cur  = flt(frm.doc.current_odometer);
//     const last = flt(frm.doc.last_odoometer);

//     if (cur > 0 && last > 0 && cur <= last) {
//         frappe.msgprint({
//             title: __("Odometer Warning"),
//             message: __("Current odometer ({0} km) cannot be ≤ last odometer ({1} km).", [cur, last]),
//             indicator: "red"
//         });
//         frm.set_value("distance", 0);
//         frm.set_value("kpl", 0);
//         return;
//     }

//     const dist = (cur > 0 && last >= 0) ? flt(cur - last, 2) : 0;
//     frm.set_value("distance", dist);
//     _calc_kpl(frm);
// }

// function _calc_kpl(frm) {
//     const dist   = flt(frm.doc.distance);
//     const liters = flt(frm.doc.liters);
//     frm.set_value("kpl", liters > 0 ? flt(dist / liters, 2) : 0);
//     _calc_incentive(frm);
// }

// function _calc_incentive(frm) {
//     const dist      = flt(frm.doc.distance);
//     const liters    = flt(frm.doc.liters);
//     const fixed_kpl = flt(frm.doc.fixed_kpl);
//     const rate      = flt(frm.doc.excessshort_fuel_rate);

//     if (fixed_kpl > 0 && dist > 0) {
//         const expected     = flt(dist / fixed_kpl, 2);
//         const excess_short = flt(expected - liters, 2);
//         frm.set_value("excessshort_fuel", excess_short);
//         frm.set_value("fuel_incentive",   flt(excess_short * rate, 2));
//     }

//     _style_excess_short(frm);
// }

// function _style_excess_short(frm) {
//     const val      = flt(frm.doc.excessshort_fuel);
//     const $wrapper = frm.fields_dict["excessshort_fuel"]?.$wrapper;
//     if (!$wrapper) return;

//     const $label = $wrapper.find("label");
//     if (val > 0) {
//         $label.css({ color: "var(--green-600)", fontWeight: "600" });
//         $label.text("Excess Fuel (Saved ✓)");
//     } else if (val < 0) {
//         $label.css({ color: "var(--red-500)", fontWeight: "600" });
//         $label.text("Short Fuel (Over-consumed ✗)");
//     } else {
//         $label.css({ color: "", fontWeight: "" });
//         $label.text("Excess / Short Fuel");
//     }
// }

// function _apply_section_labels(frm) {
//     frm.set_df_property("section_break_inew", "label",       "🛣️  Trip & Fuel Details");
//     frm.set_df_property("section_break_inew", "description", "Odometer readings, fuel consumed and efficiency calculations.");
//     frm.set_df_property("section_break_xiph", "label",       "💳  Payment Details");
//     frm.set_df_property("section_break_xiph", "description", "Supplier, payment mode and bank information.");
// }

// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fuel Urea Expenses", {

    setup(frm) {
        ["current_odometer", "last_odoometer", "distance",
         "liters", "kpl", "fixed_kpl",
         "excessshort_fuel", "excessshort_fuel_rate",
         "fuel_incentive", "expense_amount",
         "fuelurea_amount", "effective_liters", "partial_liters_carried"
        ].forEach(f => frm.set_df_property(f, "precision", "2"));

        frm.set_query("bank_name", () => ({
            filters: { group: frm.doc.payment_mode === "Cash" ? "CASH" : "BANK" }
        }));

        frm.set_query("driver_bank_name", () => ({
            filters: { group: frm.doc.driver_payment_mode === "Cash" ? "CASH" : "BANK" }
        }));

        frm.set_query("urea_item", () => ({
            filters: { item_group: "Fuel and Urea", is_stock_item: 1, disabled: 0 }
        }));
        frm.set_query("warehouse", () => ({
            filters: { is_group: 0 }
        }));
    },

    payment_mode(frm) {
        frm.set_value("bank_name", null);
    },

    entry_type(frm) {
        if (frm.doc.entry_type === "New Purchase" && frm.doc.stock_entry) {
            frappe.msgprint(
                __("Stock has already been issued via {0}. Entry Type cannot be changed.", [frm.doc.stock_entry])
            );
            frm.set_value("entry_type", "In Stock Use");
            return;
        }

        if (frm.doc.entry_type === "In Stock Use") {
            ["supplier", "payment_mode", "bank_name", "reference_no", "upi_id", "payment_date", "fuelurea_amount"]
                .forEach(f => frm.set_value(f, null));
            _set_default_warehouse(frm);
        } else {
            ["urea_item", "warehouse"].forEach(f => frm.set_value(f, null));
        }
    },

    driver_payment_mode(frm) {
        frm.set_value("driver_bank_name", null);
        frm.set_value("driver_upi_id", null);
        frm.set_value("driver_payment_reference", null);
    },

    refresh(frm) {
        if (frm.is_new() && !frm.doc.date) {
            frm.set_value("date", frappe.datetime.get_today());
        }

        ["distance", "kpl", "fixed_kpl", "excessshort_fuel", "fuel_incentive"]
            .forEach(f => frm.set_df_property(f, "read_only", 1));

        // Lock Fuel/Urea field if this is a saved Urea entry
        if (!frm.is_new() && frm.doc.fuelurea === "Urea") {
            frm.set_df_property("fuelurea", "read_only", 1);
            frm.set_df_property("fuelurea", "description", "⚠️ Urea entries cannot be changed. This field is locked.");
        }

        // On existing records, fixed_kpl may have been saved as 0 — re-fetch from vehicle (not for Urea)
        if (!frm.is_new() && frm.doc.vehicle && !flt(frm.doc.fixed_kpl) && frm.doc.fuelurea !== "Urea") {
            _fetch_fixed_kpl_from_vehicle(frm);
        }

        _update_last_odometer_label(frm);
        _apply_field_properties(frm);
        _style_excess_short(frm);
        _apply_section_labels(frm);
        _render_fuel_history(frm);

        if (frm.doc.stock_entry) {
            frm.dashboard.add_indicator(__("Stock Issued: {0}", [frm.doc.stock_entry]), "blue");
            frm.add_custom_button(__("View Stock Entry"), () => {
                frappe.set_route("Form", "Stock Entry", frm.doc.stock_entry);
            });
        }
    },

    on_submit(frm) {
        // Redirect to list only after Submit — not after every Save, so the user
        // can Submit from the same page without an intermediate list bounce.
        setTimeout(() => {
            frappe.set_route("List", "Fuel Urea Expenses");
        }, 500);
    },

    fuelurea(frm) {
        _update_last_odometer_label(frm);
        _handle_fuelurea_change(frm);
    },

    expense_amount(frm) {
        _apply_section_labels(frm);
    },

    fill_type(frm) {
        if (frm.doc.fuelurea === "Urea") return;
        _apply_field_properties(frm);
        frm.set_value("excessshort_fuel", 0);
        frm.set_value("fuel_incentive", 0);
        if (frm.doc.fill_type === "Partial Refill") {
            frm.set_value("partial_liters_carried", 0);
            frm.set_value("effective_liters", 0);
        }
        _fetch_last_odometer_live(frm);
    },

    // ── Vehicle → fetch last odometer + fuel type + fixed KPL ──────────────
    vehicle(frm) {
        _render_fuel_history(frm);

        if (!frm.doc.vehicle) {
            frm.set_value("last_odoometer", 0);
            frm.set_value("fuelurea", "");
            frm.set_value("fixed_kpl", 0);
            _calc_distance(frm);
            return;
        }

        // For Urea: fetch last urea odometer only; fixed KPL always from vehicle master
        if (frm.doc.fuelurea === "Urea") {
            _fetch_last_urea_entry(frm);
            _fetch_fixed_kpl_from_vehicle(frm);
            return;
        }

        // Fetch all needed fields from Vehicle master in one call
        frappe.db.get_value(
            "Vehicle",
            frm.doc.vehicle,
            ["fuel_type", "custom_fixed_kpl"],
            function(d) {
                if (!d) return;

                const fuel_map = {
                    "Diesel":      "Diesel",
                    "Petrol":      "Petrol",
                    "Natural Gas": "Diesel",
                    "Electric":    "Diesel"
                };
                const mapped_fuel = fuel_map[d.fuel_type] || "";
                // Set fuelurea directly on doc (no form event fired) to prevent recursive vehicle trigger
                if (mapped_fuel && mapped_fuel !== frm.doc.fuelurea) {
                    frm.doc.fuelurea = mapped_fuel;
                    frm.refresh_field("fuelurea");
                    _update_last_odometer_label(frm);
                }

                const kpl_val = flt(d.custom_fixed_kpl, 2);
                frm.set_value("fixed_kpl", kpl_val);
                if (kpl_val > 0) {
                    frappe.show_alert({
                        message: `Fixed KPL set to <b>${kpl_val}</b> from vehicle master.`,
                        indicator: "green"
                    }, 4);
                }

                // Top Up -> last Top Up ka odometer | Partial Refill -> immediately previous entry
                // (live query, see get_last_odometer — Vehicle.last_odometer field ke stale hone se bachne ke liye)
                _fetch_last_odometer_live(frm);
            }
        );
    },

    current_odometer(frm) {
        if (frm.doc.fuelurea === "Urea") {
            _calc_distance(frm);  // Urea ka last odometer live-fetch nahi hota, sirf distance recalc chahiye
        } else {
            _fetch_last_odometer_live(frm);  // bounds change hote hain — re-fetch
        }
    },
    last_odoometer(frm) { _calc_distance(frm); },

    liters(frm)                { _update_effective_liters(frm); },
    fixed_kpl(frm)             { _calc_incentive(frm); },
    excessshort_fuel_rate(frm) { _calc_incentive(frm); },

    excessshort_fuel(frm) { _style_excess_short(frm); }
});


// ── Helpers ──────────────────────────────────────────────────────────────────

function _handle_fuelurea_change(frm) {
    _apply_field_properties(frm);
    if (frm.doc.fuelurea === "Urea") {
        _fetch_last_urea_entry(frm);
        // fixed_kpl fetch not needed for Urea — field is hidden
    } else {
        // entry_type only applies to Urea — reset so a stale "In Stock Use"
        // doesn't linger hidden on a Diesel/Petrol entry.
        if (frm.doc.entry_type && frm.doc.entry_type !== "New Purchase" && !frm.doc.stock_entry) {
            frm.set_value("entry_type", "New Purchase");
        }
        // User manually switched to Petrol/Diesel — re-fetch from vehicle
        if (frm.doc.vehicle) {
            frm.trigger("vehicle");
        }
    }
}

function _fetch_fixed_kpl_from_vehicle(frm) {
    if (!frm.doc.vehicle) return;
    frappe.db.get_value("Vehicle", frm.doc.vehicle, "custom_fixed_kpl", function(d) {
        if (!d) return;
        const kpl_val = flt(d.custom_fixed_kpl, 2);
        frm.set_value("fixed_kpl", kpl_val);
        if (kpl_val > 0) {
            frappe.show_alert({
                message: `Fixed KPL set to <b>${kpl_val}</b> from vehicle master.`,
                indicator: "green"
            }, 4);
        }
        _calc_incentive(frm);
    });
}

function _fetch_last_urea_entry(frm) {
    if (!frm.doc.vehicle) {
        frm.set_value("last_odoometer", 0);
        return;
    }

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Fuel Urea Expenses",
            filters: [
                ["vehicle", "=", frm.doc.vehicle],
                ["fuelurea", "=", "Urea"],
                ["docstatus", "!=", 2]
            ],
            fields: ["current_odometer", "date"],
            order_by: "date desc, creation desc",
            limit: 1
        },
        callback(r) {
            if (r.message && r.message.length > 0) {
                const last_odo = r.message[0].current_odometer || 0;
                frm.set_value("last_odoometer", last_odo);
                if (last_odo > 0) {
                    frappe.show_alert({
                        message: `Last Urea odometer: <b>${last_odo} km</b>`,
                        indicator: "blue"
                    }, 4);
                }
            } else {
                frm.set_value("last_odoometer", 0);
                frappe.show_alert({
                    message: "No previous Urea entry found for this vehicle.",
                    indicator: "orange"
                }, 3);
            }
            _calc_distance(frm);
        }
    });
}

// _fetch_last_topup_odometer — no longer needed.
// Ab Vehicle.last_odometer hamesha last Top Up ka odometer hai
// (Python _update_vehicle_odometer() Partial Refill pe update nahi karta)
// Isliye vehicle() handler directly Vehicle.last_odometer use karta hai.
// function _fetch_last_topup_odometer(frm) { ... }

// Pre-fill from Stock Settings' Default Warehouse — user can still change it.
function _set_default_warehouse(frm) {
    if (frm.doc.warehouse) return;
    frappe.db.get_single_value("Stock Settings", "default_warehouse").then(warehouse => {
        if (warehouse && !frm.doc.warehouse) {
            frm.set_value("warehouse", warehouse);
        }
    });
}

function _apply_field_properties(frm) {
    const is_urea    = frm.doc.fuelurea  === "Urea";
    const is_partial = frm.doc.fill_type === "Partial Refill";

    // Urea pe fill_type field hide karo — Partial Refill/Top Up sirf Diesel/Petrol ke liye hai
    frm.set_df_property("fill_type", "hidden", is_urea ? 1 : 0);

    // column_break_lzqj/fixed_kpl: sirf Urea pe hide karo — Fixed KPL Partial Refill pe bhi
    // dikhta hai (read-only reference context, koi input risk nahi)
    ["column_break_lzqj", "fixed_kpl"]
        .forEach(f => frm.set_df_property(f, "hidden", is_urea ? 1 : 0));

    // Excess/Short Fuel, Rate, Incentive, Amount Paid: Urea aur Partial Refill dono pe hide —
    // Partial pe Incentive hamesha 0 locked hai (see _calc_incentive), aur Excess/Short
    // uska hi input hai (green/red "Saved"/"Over-consumed" label bhi lagata hai) —
    // isliye inhe dikhana sirf confusion karega
    ["excessshort_fuel", "excessshort_fuel_rate", "fuel_incentive", "expense_amount"]
        .forEach(f => frm.set_df_property(f, "hidden", (is_urea || is_partial) ? 1 : 0));

    // partial_liters_carried aur effective_liters: sirf Top Up pe dikhao (Partial Refill pe nahi)
    ["partial_liters_carried", "effective_liters"]
        .forEach(f => frm.set_df_property(f, "hidden", (is_urea || is_partial) ? 1 : 0));

    if (is_urea) {
        frm.set_df_property("current_odometer", "read_only", 0);
        frm.set_df_property("last_odoometer", "read_only", 0);
        frm.set_df_property("fuelurea", "description", "Urea selected - Odometer fields pulled from last Urea entry.");
        frm.refresh_field("current_odometer");
        frm.refresh_field("last_odoometer");
    } else {
        frm.set_df_property("current_odometer", "read_only", 0);
        frm.set_df_property("last_odoometer", "read_only", 1);
        frm.set_df_property("fuelurea", "description", "Auto-filled from vehicle.");
        frm.set_df_property("fixed_kpl", "description", "Auto-filled from vehicle.");
        frm.refresh_field("current_odometer");
        frm.refresh_field("last_odoometer");
    }
}

function _calc_distance(frm) {
    const cur  = flt(frm.doc.current_odometer);
    const last = flt(frm.doc.last_odoometer);

    if (cur > 0 && last > 0 && cur <= last) {
        frappe.msgprint({
            title: __("Odometer Warning"),
            message: __("Current odometer ({0} km) cannot be ≤ last odometer ({1} km).", [cur, last]),
            indicator: "red"
        });
        frm.set_value("distance", 0);
        frm.set_value("kpl", 0);
        return;
    }

    const dist = (cur > 0 && last >= 0) ? flt(cur - last, 2) : 0;
    frm.set_value("distance", dist);
    _calc_kpl(frm);
}

// ── Last Odometer Live Fetch ────────────────────────────────────────────────
// Top Up -> last Top Up ka odometer | Partial Refill -> immediately previous entry (any type)

function _fetch_last_odometer_live(frm) {
    if (frm.doc.fuelurea === "Urea") return;
    if (!frm.doc.vehicle) {
        frm.set_value("last_odoometer", 0);
        _calc_distance(frm);
        return;
    }

    // Current Odometer abhi khali ho to bhi fetch karo — bina bound ke (latest entry
    // overall) taaki Vehicle/Fill Type badalte hi turant preview mil jaaye.
    // Current Odometer bharne ke baad yehi call bounded (precise) result dega.
    frappe.call({
        method: "logicore.logicore.doctype.fuel_urea_expenses.fuel_urea_expenses.get_last_odometer",
        args: {
            vehicle:          frm.doc.vehicle,
            fill_type:        frm.doc.fill_type,
            current_odometer: frm.doc.current_odometer || 0,
            exclude_name:     frm.doc.name || ""
        },
        callback(r) {
            frm.set_value("last_odoometer", flt(r.message || 0));
            _calc_distance(frm);
            if (frm.doc.fill_type === "Top Up (Full Tank)") {
                _fetch_partial_liters_live(frm);
            }
        }
    });
}

// ── Partial Liters Live Fetch ─────────────────────────────────────────────────

function _fetch_partial_liters_live(frm) {
    // Only for Top Up (Full Tank) Diesel/Petrol entries
    if (frm.doc.fuelurea === "Urea" || frm.doc.fill_type !== "Top Up (Full Tank)") return;
    if (!frm.doc.vehicle || !flt(frm.doc.current_odometer)) return;

    frappe.call({
        method: "logicore.logicore.doctype.fuel_urea_expenses.fuel_urea_expenses.get_partial_liters",
        args: {
            vehicle:          frm.doc.vehicle,
            last_odoometer:   frm.doc.last_odoometer   || 0,
            current_odometer: frm.doc.current_odometer || 0,
            exclude_name:     frm.doc.name             || ""
        },
        callback(r) {
            const partial = flt(r.message || 0);
            frm.set_value("partial_liters_carried", partial);
            _update_effective_liters(frm);
        }
    });
}

function _update_effective_liters(frm) {
    // Instant update using already-fetched partial_liters_carried
    if (frm.doc.fuelurea === "Urea" || frm.doc.fill_type !== "Top Up (Full Tank)") {
        _calc_kpl(frm);  // Urea pe effective_liters nahi hota — directly liters se KPL calc karo
        return;
    }
    const partial = flt(frm.doc.partial_liters_carried);
    const liters  = flt(frm.doc.liters);
    frm.set_value("effective_liters", flt(partial + liters, 2));
    _calc_kpl(frm);
}

// ── Calculations ──────────────────────────────────────────────────────────────

function _calc_kpl(frm) {
    // Partial Refill bhi apna KPL dikhata hai (apne exclusive odometer segment se) —
    // sirf Excess/Short + Incentive Partial pe locked rehte hain, see _calc_incentive()
    const dist       = flt(frm.doc.distance);
    const eff_liters = flt(frm.doc.effective_liters) || flt(frm.doc.liters);
    frm.set_value("kpl", eff_liters > 0 ? flt(dist / eff_liters, 2) : 0);
    _calc_incentive(frm);
}

function _calc_incentive(frm) {
    if (frm.doc.fill_type === "Partial Refill") {
        frm.set_value("excessshort_fuel", 0);
        frm.set_value("fuel_incentive",   0);
        _style_excess_short(frm);
        return;
    }
    const dist      = flt(frm.doc.distance);
    const liters    = flt(frm.doc.effective_liters) || flt(frm.doc.liters);
    const fixed_kpl = flt(frm.doc.fixed_kpl);
    const rate      = flt(frm.doc.excessshort_fuel_rate);

    if (fixed_kpl > 0 && dist > 0) {
        const expected     = flt(dist / fixed_kpl, 2);
        const excess_short = flt(expected - liters, 2);
        frm.set_value("excessshort_fuel", excess_short);
        frm.set_value("fuel_incentive",   flt(excess_short * rate, 2));
    }

    _style_excess_short(frm);
}

function _style_excess_short(frm) {
    const val      = flt(frm.doc.excessshort_fuel);
    const $wrapper = frm.fields_dict["excessshort_fuel"]?.$wrapper;
    if (!$wrapper) return;

    const $label = $wrapper.find("label");
    if (val > 0) {
        $label.css({ color: "var(--green-600)", fontWeight: "600" });
        $label.text("Excess Fuel (Saved ✓)");
    } else if (val < 0) {
        $label.css({ color: "var(--red-500)", fontWeight: "600" });
        $label.text("Short Fuel (Over-consumed ✗)");
    } else {
        $label.css({ color: "", fontWeight: "" });
        $label.text("Excess / Short Fuel");
    }
}

function _update_last_odometer_label(frm) {
    const label_map = {
        "Petrol": "Petrol Last Odometer",
        "Diesel": "Diesel Last Odometer",
        "Urea":   "Urea Last Odometer"
    };
    const label = label_map[frm.doc.fuelurea] || "Petrol Last Odometer";
    frm.set_df_property("last_odoometer", "label", label);
    frm.refresh_field("last_odoometer");
}

function _apply_section_labels(frm) {
    frm.set_df_property("section_break_inew", "label",       "🛣️  Trip & Fuel Details");
    frm.set_df_property("section_break_inew", "description", "Odometer readings, fuel consumed and efficiency calculations.");
    frm.set_df_property("section_break_xiph", "label",       "💳  Payment Details");
    frm.set_df_property("section_break_xiph", "description", "Supplier, payment mode and bank information.");

    const is_urea         = frm.doc.fuelurea === "Urea";
    const has_driver_pay  = flt(frm.doc.expense_amount) > 0;
    const hide_driver     = is_urea || !has_driver_pay;
    const driver_section_fields = [
        "section_break_driver_payment", "driver_payment_mode",
        "column_break_driver_payment", "driver_bank_name",
        "driver_upi_id", "driver_payment_reference"
    ];
    driver_section_fields.forEach(f => {
        frm.set_df_property(f, "hidden", hide_driver ? 1 : 0);
    });
    frm.refresh_fields(driver_section_fields);
}

// ── Fuel History panel ─────────────────────────────────────────────────────
// Read-only, client-rendered into the "fuel_history_html" field. Nothing here
// is saved with the document — from/to date pickers are local UI state only.

function _render_fuel_history(frm) {
    const field = frm.fields_dict.fuel_history_html;
    if (!field || !field.$wrapper) return;
    const $wrapper = field.$wrapper;

    if (!frm.doc.vehicle) {
        $wrapper.html(`<div class="tms-fuel-history-empty">${__("Select a vehicle to see fuel history.")}</div>`);
        return;
    }

    const today = frappe.datetime.get_today();
    const default_from = frappe.datetime.add_months(today, -1);
    let current_rows = [];

    $wrapper.html(`
        <div class="tms-fuel-history">
            <div class="tms-fuel-history-filters">
                <div class="tms-fh-field">
                    <label>${__("From Date")}</label>
                    <input type="date" class="form-control input-sm tms-fh-from" value="${default_from}">
                </div>
                <div class="tms-fh-field">
                    <label>${__("To Date")}</label>
                    <input type="date" class="form-control input-sm tms-fh-to" value="${today}">
                </div>
                <button type="button" class="btn btn-xs btn-default tms-fh-show">${__("Show")}</button>
                <button type="button" class="btn btn-xs btn-default tms-fh-download">
                    <i class="fa fa-download" aria-hidden="true"></i> ${__("Download")}
                </button>
            </div>
            <div class="tms-fh-results"></div>
        </div>
    `);

    const $from = $wrapper.find(".tms-fh-from");
    const $to = $wrapper.find(".tms-fh-to");
    const $results = $wrapper.find(".tms-fh-results");

    const fetch_and_render = () => {
        const from_date = $from.val() || default_from;
        const to_date = $to.val() || today;

        if (from_date > to_date) {
            frappe.show_alert({ message: __("From Date cannot be after To Date."), indicator: "orange" }, 3);
            return;
        }

        $results.html(`<div class="text-muted">${__("Loading...")}</div>`);

        frappe.call({
            method: "logicore.logicore.doctype.fuel_urea_expenses.fuel_urea_expenses.get_vehicle_fuel_history",
            args: {
                vehicle: frm.doc.vehicle,
                from_date: from_date,
                to_date: to_date,
                exclude_name: (frm.doc.name && !frm.doc.name.startsWith("new-")) ? frm.doc.name : ""
            },
            callback(r) {
                current_rows = r.message || [];
                _render_fuel_history_rows($results, current_rows);
            }
        });
    };

    $wrapper.find(".tms-fh-show").on("click", fetch_and_render);
    $wrapper.find(".tms-fh-download").on("click", () => {
        _download_fuel_history_csv(current_rows, frm.doc.vehicle, $from.val() || default_from, $to.val() || today);
    });
    fetch_and_render();
}

function _render_fuel_history_rows($results, rows) {
    if (!rows.length) {
        $results.html(`<div class="tms-fuel-history-empty">${__("No fuel/urea history found for this vehicle in the selected range.")}</div>`);
        return;
    }

    const fill_type_short = {
        "Top Up (Full Tank)": __("Top Up"),
        "Partial Refill": __("Partial")
    };

    const body_rows = rows.map((row, idx) => {
        const fill = row.fuelurea === "Urea" ? "—" : (fill_type_short[row.fill_type] || row.fill_type || "—");
        const safe_name = frappe.utils.escape_html(row.name);
        return `
            <tr>
                <td>${idx + 1}</td>
                <td>${TMS.formatIndianDate(row.date)}</td>
                <td><a href="#" class="tms-fh-link" data-name="${safe_name}">${safe_name}</a></td>
                <td>${frappe.utils.escape_html(row.fuelurea || "")}</td>
                <td>${frappe.utils.escape_html(fill)}</td>
                <td>${frappe.utils.escape_html(row.driver_name || "")}</td>
                <td>${frappe.utils.escape_html(row.vehicle || "")}</td>
                <td class="tms-fh-num">${flt(row.last_odoometer)}</td>
                <td class="tms-fh-num">${flt(row.current_odometer)}</td>
                <td class="tms-fh-num">${flt(row.distance)}</td>
                <td class="tms-fh-num">${flt(row.kpl, 2)}</td>
                <td class="tms-fh-num">${flt(row.liters, 2)}</td>
                <td class="tms-fh-num">${TMS.formatINR(row.fuelurea_amount || 0)}</td>
            </tr>
        `;
    }).join("");

    $results.html(`
        <div class="tms-fuel-history-scroll">
            <table class="tms-fuel-history-table">
                <thead>
                    <tr>
                        <th>${__("No")}</th>
                        <th>${__("Date")}</th>
                        <th>${__("Entry No")}</th>
                        <th>${__("Type")}</th>
                        <th>${__("Fill Type")}</th>
                        <th>${__("Driver")}</th>
                        <th>${__("Vehicle")}</th>
                        <th class="tms-fh-num">${__("KM-Start")}</th>
                        <th class="tms-fh-num">${__("KM-End")}</th>
                        <th class="tms-fh-num">${__("KM-Total")}</th>
                        <th class="tms-fh-num">${__("KPL")}</th>
                        <th class="tms-fh-num">${__("Qty")}</th>
                        <th class="tms-fh-num">${__("Amount")}</th>
                    </tr>
                </thead>
                <tbody>${body_rows}</tbody>
            </table>
        </div>
    `);

    $results.find(".tms-fh-link").on("click", function (e) {
        e.preventDefault();
        frappe.set_route("Form", "Fuel Urea Expenses", $(this).data("name"));
    });
}

function _csv_cell(value) {
    const str = String(value === undefined || value === null ? "" : value);
    return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
}

function _download_fuel_history_csv(rows, vehicle, from_date, to_date) {
    if (!rows.length) {
        frappe.show_alert({ message: __("No data to download."), indicator: "orange" }, 3);
        return;
    }

    const fill_type_short = {
        "Top Up (Full Tank)": __("Top Up"),
        "Partial Refill": __("Partial")
    };

    const header = [
        __("No"), __("Date"), __("Entry No"), __("Type"), __("Fill Type"), __("Driver"), __("Vehicle"),
        __("KM-Start"), __("KM-End"), __("KM-Total"), __("KPL"), __("Qty"), __("Amount")
    ];

    const lines = [header.map(_csv_cell).join(",")];
    rows.forEach((row, idx) => {
        const fill = row.fuelurea === "Urea" ? "-" : (fill_type_short[row.fill_type] || row.fill_type || "-");
        lines.push([
            idx + 1,
            TMS.formatIndianDate(row.date),
            row.name,
            row.fuelurea || "",
            fill,
            row.driver_name || "",
            row.vehicle || "",
            flt(row.last_odoometer),
            flt(row.current_odometer),
            flt(row.distance),
            flt(row.kpl, 2),
            flt(row.liters, 2),
            flt(row.fuelurea_amount, 2)
        ].map(_csv_cell).join(","));
    });

    const csv_content = "﻿" + lines.join("\r\n");
    const blob = new Blob([csv_content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const $link = $("<a>").attr({
        href: url,
        download: `Fuel_History_${vehicle}_${from_date}_to_${to_date}.csv`
    }).appendTo("body");
    $link[0].click();
    $link.remove();
    URL.revokeObjectURL(url);
}