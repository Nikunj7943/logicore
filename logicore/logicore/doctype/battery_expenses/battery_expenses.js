// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Battery Expenses", {

    setup(frm) {
        frm.set_query("bank_name", () => ({
            filters: { group: frm.doc.payment_mode === "Cash" ? "CASH" : "BANK" }
        }));
        frm.set_query("battery_item", () => ({
            filters: { item_group: "Battery", is_stock_item: 1, disabled: 0 }
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
            ["cost", "vendor", "payment_mode", "bank_name", "reference_no", "upi_id", "payment_date"]
                .forEach(f => frm.set_value(f, null));
            _set_default_warehouse(frm);
        } else {
            ["battery_item", "warehouse"].forEach(f => frm.set_value(f, null));
        }
    },
    //redirect
    on_submit(frm){
    setTimeout(()=>{
        frappe.set_route("List","Battery Expenses");
    },500);
    },

    // ── Refresh ──────────────────────────────────────────────────────────────
    refresh(frm) {
        // Read-only computed fields
        ["warranty_expiry_date", "actual_life_achieved", "warranty_status"]
            .forEach(f => frm.set_df_property(f, "read_only", 1));

        _apply_section_labels(frm);
        _render_status_badge(frm);
        _add_dashboard_indicators(frm);

        if (frm.doc.stock_entry) {
            frm.dashboard.add_indicator(__("Stock Issued: {0}", [frm.doc.stock_entry]), "blue");
            frm.add_custom_button(__("View Stock Entry"), () => {
                frappe.set_route("Form", "Stock Entry", frm.doc.stock_entry);
            });
        }
    },

    // ── Vehicle → fetch reg no ───────────────────────────────────────────────
    vehicle_id(frm) {
        if (!frm.doc.vehicle_id) {
            frm.set_value("vehicle_reg_no", "");
            return;
        }
        frappe.db.get_value(
            "Vehicle",
            frm.doc.vehicle_id,
            ["license_plate"],
            function(d) {
                if (d && d.license_plate) {
                    frm.set_value("vehicle_reg_no", d.license_plate);
                }
            }
        );
    },

    // ── Date & warranty calculations ─────────────────────────────────────────
    purchase_date(frm)    { _calc_warranty_expiry(frm); },
    installation_date(frm){ _calc_actual_life(frm); },
    warranty_months(frm)  { _calc_warranty_expiry(frm); },

    replacement_date(frm) {
        _calc_actual_life(frm);
        _auto_set_condition(frm);
        _update_warranty_status(frm);
    },

    warranty_expiry_date(frm) { _update_warranty_status(frm); },

    battery_condition(frm) { _render_status_badge(frm); }
});



// ── Helpers ──────────────────────────────────────────────────────────────────

function _calc_warranty_expiry(frm) {
    const pd      = frm.doc.purchase_date;
    const months  = cint(frm.doc.warranty_months);

    if (!pd || months <= 0) {
        frm.set_value("warranty_expiry_date", "");
        frm.set_value("warranty_status", "No Warranty");
        return;
    }

    const expiry = frappe.datetime.add_months(pd, months);
    frm.set_value("warranty_expiry_date", expiry);
    _update_warranty_status(frm);
}

function _calc_actual_life(frm) {
    const install  = frm.doc.installation_date;
    const replaced = frm.doc.replacement_date;
    const today    = frappe.datetime.get_today();

    if (!install) {
        frm.set_value("actual_life_achieved", "");
        return;
    }

    // If no replacement date, or replacement is in the future → battery still active
    const is_active = !replaced || frappe.datetime.get_diff(replaced, today) > 0;

    const end_date = is_active ? today : replaced;
    const days     = frappe.datetime.get_diff(end_date, install);
    const months   = Math.floor(days / 30);
    const rem      = days % 30;

    frm.set_value("actual_life_achieved",
        is_active
            ? `${months} month(s) ${rem} day(s) (Active)`
            : `${months} month(s) ${rem} day(s)`
    );
}

function _auto_set_condition(frm) {
    const replaced = frm.doc.replacement_date;
    const today    = frappe.datetime.get_today();

    if (!replaced) {
        frm.set_value("battery_condition", "Active");
    } else if (frappe.datetime.get_diff(replaced, today) > 0) {
        // Replacement date is in the future → still active
        frm.set_value("battery_condition", "Active");
        frappe.show_alert({
            message: `Replacement is scheduled for <b>${replaced}</b>. Battery is still Active.`,
            indicator: "blue"
        }, 5);
    } else {
        // Replacement date is today or past → battery replaced
        frm.set_value("battery_condition", "Replaced");
    }
}

function _update_warranty_status(frm) {
    const expiry    = frm.doc.warranty_expiry_date;
    const months    = cint(frm.doc.warranty_months);
    const replaced  = frm.doc.replacement_date;
    const today     = frappe.datetime.get_today();

    // Battery physically replaced (past date) → warranty no longer applicable
    if (replaced && frappe.datetime.get_diff(replaced, today) <= 0) {
        frm.set_value("warranty_status", "No Warranty");
        _render_status_badge(frm);
        return;
    }

    if (!expiry || months <= 0) {
        frm.set_value("warranty_status", "No Warranty");
    } else if (frappe.datetime.get_diff(expiry, today) >= 0) {
        frm.set_value("warranty_status", "Under Warranty");
    } else {
        frm.set_value("warranty_status", "Expired");
    }

    _render_status_badge(frm);
}

function _render_status_badge(frm) {
    const ws = frm.doc.warranty_status;
    const cond = frm.doc.battery_condition;

    // Warranty badge
    const ws_wrapper = frm.fields_dict["warranty_status"]?.$wrapper;
    if (ws_wrapper) {
        const color_map = {
            "Under Warranty": "green",
            "Expired":        "red",
            "No Warranty":    "gray"
        };
        const color = color_map[ws] || "gray";
        const label_el = ws_wrapper.find(".control-label");
        label_el.css({ color: `var(--${color}-600)`, fontWeight: "600" });
    }

    // Condition badge on form header
    if (!frm.is_new()) {
        const color_map = {
            "Active":   "green",
            "Replaced": "blue",
            "Failed":   "red"
        };
        const color = color_map[cond] || "gray";
        frm.page.set_indicator(cond || "Active", color);
    }
}

function _add_dashboard_indicators(frm) {
    if (frm.is_new()) return;

    frm.dashboard.clear_headline();

    const expiry = frm.doc.warranty_expiry_date;
    if (expiry) {
        const today = frappe.datetime.get_today();
        const days_left = frappe.datetime.get_diff(expiry, today);
        if (days_left >= 0) {
            frm.dashboard.add_indicator(
                `Warranty: ${days_left} day(s) left`,
                "green"
            );
        } else {
            frm.dashboard.add_indicator(
                `Warranty expired ${Math.abs(days_left)} day(s) ago`,
                "red"
            );
        }
    }

    if (frm.doc.cost) {
        const formatted = "₹" + flt(frm.doc.cost).toLocaleString("en-IN");
        frm.dashboard.add_indicator(`Cost: ${formatted}`, "blue");
    }

    if (frm.doc.installation_date && !frm.doc.replacement_date) {
        frm.dashboard.add_indicator("Battery in Service", "green");
    } else if (frm.doc.replacement_date) {
        frm.dashboard.add_indicator("Battery Replaced", "orange");
    }
}

function _apply_section_labels(frm) {
    frm.set_df_property("section_identification", "description",
        "Link the vehicle, enter battery brand and registration number.");
    frm.set_df_property("section_dates", "description",
        "Purchase/Installation dates and warranty period. Expiry is auto-calculated.");
    frm.set_df_property("section_cost", "description",
        "Battery cost (₹), vendor details and replacement date if applicable.");
    frm.set_df_property("section_status", "description",
        "Auto-calculated warranty and battery condition status.");
}

// Pre-fill from Stock Settings' Default Warehouse — user can still change it.
function _set_default_warehouse(frm) {
    if (frm.doc.warehouse) return;
    frappe.db.get_single_value("Stock Settings", "default_warehouse").then(warehouse => {
        if (warehouse && !frm.doc.warehouse) {
            frm.set_value("warehouse", warehouse);
        }
    });
}
