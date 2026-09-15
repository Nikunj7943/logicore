// Staff Payroll Form Controller
// Fixed version with correct module path

// Earning/deduction component lists are no longer hardcoded here — they come
// live from the linked Salary Structure's own earnings/deductions rows
// (Employee Salary Structure / Driver Salary Structure, or whichever
// structure is set on salary_structure). Cached per (salary_type,
// salary_structure) combo on the frm to avoid refetching on every keystroke.
function get_salary_structure_components(frm) {
    const key = (frm.doc.salary_type || "") + "::" + (frm.doc.salary_structure || "");
    frm._sc_cache = frm._sc_cache || {};
    if (frm._sc_cache[key]) {
        return frm._sc_cache[key];
    }
    const promise = new Promise(resolve => {
        frappe.call({
            method: "logicore.logicore.doctype.staff_payroll.staff_payroll.get_salary_structure_component_types",
            args: {
                salary_type: frm.doc.salary_type,
                salary_structure: frm.doc.salary_structure,
            },
            callback: function(r) {
                resolve(r.message || { earnings: [], deductions: [] });
            }
        });
    });
    frm._sc_cache[key] = promise;
    return promise;
}

function is_old_data_import(frm) {
    return frm._is_old_data_import === true;
}

function resolve_old_data_import_state(frm) {
    if (frm._old_import_state_resolved) {
        return Promise.resolve(is_old_data_import(frm));
    }

    if (frm.doc.__islocal) {
        frm._is_old_data_import = false;
        frm._old_import_state_resolved = true;
        return Promise.resolve(false);
    }

    if (!frm._old_import_state_promise) {
        frm._old_import_state_promise = new Promise(resolve => {
            frappe.call({
                method: "logicore.logicore.doctype.staff_payroll.staff_payroll.is_old_data_import_doc",
                args: { name: frm.doc.name },
                callback: function(r) {
                    frm._is_old_data_import = !!r.message;
                    frm._old_import_state_resolved = true;
                    resolve(frm._is_old_data_import);
                },
            });
        });
    }

    return frm._old_import_state_promise;
}

frappe.ui.form.on('Staff Payroll', {

    setup(frm) {
        frm.set_query("bank_account", () => ({
            filters: { group: frm.doc.payment_mode === "Cash" ? "CASH" : "BANK" }
        }));
    },

    payment_mode(frm) {
        frm.set_value("bank_account", null);
    },

    onload: function(frm) {
        const run_onload_calculations = () => {
            // Only a brand-new document derives its period and attendance
            // automatically. Saving a new payroll renames it, which makes
            // Frappe fire onload a second time — without this guard that reload
            // silently re-ran set_previous_month() and re-fetched attendance,
            // overwriting the saved present/leave days with fresh values. Once
            // saved, the stored numbers ARE the record; the "Fetch Attendance"
            // button is there to refresh them on purpose.
            if (frm.is_new() && frm.doc.payroll_date && !is_old_data_import(frm)) {
                set_previous_month(frm).then(() => {
                    calculate_period(frm);
                    schedule_attendance_fetch(frm);
                });
            }

            if (!is_old_data_import(frm)) {
                update_salary_components(frm);
            }

            configure_salary_detail_grid_columns(frm);
            fetch_and_render_employee_lr_money(frm);
        };

        // Set default dates
        if (!frm.doc.from_date) {
            let today = frappe.datetime.get_today();
            let month_start = frappe.datetime.add_months(today, -1);
            month_start = frappe.datetime.get_first_day(month_start);
            frm.set_value('from_date', month_start);
        }
        
        if (!frm.doc.to_date) {
            let today = frappe.datetime.get_today();
            frm.set_value('to_date', today);
        }
        resolve_old_data_import_state(frm).then(run_onload_calculations);
    },

    payroll_date: function(frm) {
        set_previous_month(frm).then(() => {
            calculate_period(frm);
            schedule_attendance_fetch(frm);
        });
    },
    
    refresh: function(frm) {
        // Add custom buttons
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Fetch Attendance'), function() {
                fetch_attendance_data(frm);
            }, __("Actions"));

            frm.add_custom_button(__('Calculate Payroll'), function() {
                calculate_payroll(frm);
            }, __("Actions"));

            if (frm.doc.approval_status !== "Approved" && frm.doc.docstatus === 0) {
                frm.add_custom_button(__('Approve'), function() {
                    approve_payroll(frm);
                }, __("Actions"));
            }

            frm.add_custom_button(__('Print Salary Slip'), function() {
                const print_url = frappe.urllib.get_full_url(
                    "/printview?doctype=" + encodeURIComponent("Staff Payroll") +
                    "&name=" + encodeURIComponent(frm.doc.name) +
                    "&format=" + encodeURIComponent("Staff payroll 4 june") +
                    "&no_letterhead=1"
                );
                window.open(print_url);
            }, __("Print"));
        }

        // Update status colors
        update_status_color(frm);

        // earnings_table/deductions_table are allow_on_submit so a newly added
        // Salary Structure component can be backfilled into old submitted Staff
        // Payroll records -- only these roles may actually edit them post-submit
        // (server-side enforced in overrides/salary_structure.py).
        if (frm.doc.docstatus === 1) {
            const can_edit_components =
                frappe.session.user === "Administrator" ||
                frappe.user.has_role("System Manager") ||
                frappe.user.has_role("TMS ADMIN");
            ["earnings_table", "deductions_table"].forEach((fieldname) => {
                frm.set_df_property(fieldname, "read_only", can_edit_components ? 0 : 1);
                frm.fields_dict[fieldname].grid.refresh();
            });
        }

        // Frappe reuses one form object across documents of the same doctype,
        // so override tracking has to be reset whenever a different payroll is
        // loaded — otherwise one record's manual edits leak into the next.
        if (frm._override_doc_key !== frm.doc.name) {
            frm._override_doc_key = frm.doc.name;
            frm._manual_component_override = {};
            frm._manual_override_seeded = false;
        }

        resolve_old_data_import_state(frm).then(() => {
            if (!is_old_data_import(frm)) {
                update_salary_components(frm);
            }
            configure_salary_detail_grid_columns(frm);
        });

        // Build base recovery cache for validation (keyed by payment_ref)
        // For saved docs: already_recovered is cumulative (Python set it), derive base = cumulative - recovery_amount
        // For legacy rows (pre-fix): already_recovered < recovery_amount, so base = already_recovered itself
        frm._advance_base_recovered = frm._advance_base_recovered || {};
        (frm.doc.advance_recovery_table || []).forEach(row => {
            if (!row.payment_ref) return;
            if (frm._advance_base_recovered[row.payment_ref] != null) return; // already cached by fetch
            const ar = flt(row.already_recovered);
            const ra = flt(row.recovery_amount);
            // If ar >= ra it's cumulative (post-fix), else it's the raw base (legacy/pre-fix)
            frm._advance_base_recovered[row.payment_ref] = (ar >= ra) ? Math.max(0, ar - ra) : ar;
        });

        // Render advance summary from saved data on page load
        const adv_rows = frm.doc.advance_recovery_table || [];
        if (adv_rows.length) {
            render_advance_summary_from_doc(frm);
        }

        // Auto-fetch driver advances on new doc when driver already set
        if (frm.doc.__islocal && frm.doc.salary_type === "Driver Salary" && frm.doc.driver && !adv_rows.length) {
            fetch_driver_advance(frm);
        }

        // Render fuel incentive and trip expenses sections for driver salary
        if (frm.doc.salary_type === "Driver Salary") {
            fetch_and_render_fuel_incentive(frm);
            fetch_and_render_trip_expenses(frm);
        }
        if (frm.doc.salary_type === "Employee Salary") {
            fetch_and_render_employee_incentive(frm);
            fetch_and_render_employee_lr_money(frm);
        }
    },
    
    salary_type: function(frm) {
        if (frm.doc.salary_type === "Employee Salary") {
            frm.set_value("driver", null);
        } else {
            frm.set_value("employee", null);
            frm.set_value("employee_name", "");
            frm.set_value("ctc", 0);
        }
        // Clear attendance data so previous employee/driver data doesn't carry over
        frm.set_value('present_days', 0);
        frm.set_value('absent_days', 0);
        frm.set_value("leave_with_pay", 0);
        frm.set_value("leave_without_pay", 0);
        frm.set_value("total_attendance_days", 0);
        frm.set_value("worked_days", 0);
        // Clear earning/deduction rows so correct type rows load fresh
        frm.doc.earnings_table = [];
        frm.doc.deductions_table = [];
        frm.doc.advance_recovery_table = [];
        clear_component_overrides(frm);
        // Stale structure from the previous salary_type shouldn't carry over —
        // let it re-resolve (Salary Structure Assignment lookup, or the
        // Employee/Driver Salary Structure default) once employee/driver is picked.
        frm.set_value('salary_structure', "");
        frm.get_field("advance_summary_html").$wrapper.html("");
        const fi_field = frm.get_field("fuel_incentive_html");
        if (fi_field) fi_field.$wrapper.html("");
        const te_field = frm.get_field("trip_expenses_html");
        if (te_field) te_field.$wrapper.html("");
        const lr_field = frm.get_field("employee_lr_money_html");
        if (lr_field) lr_field.$wrapper.html("");
        frm.refresh_fields(["employee", "driver", "earnings_table", "deductions_table", "advance_recovery_table"]);
        update_salary_components(frm);
    },

    driver: function(frm) {
        // Clear all previous data when driver changes
        frm.set_value('present_days', 0);
        frm.set_value('absent_days', 0);
        frm.set_value("leave_with_pay", 0);
        frm.set_value("leave_without_pay", 0);
        frm.set_value("total_attendance_days", 0);
        frm.set_value("worked_days", 0);
        frm.set_value("ctc", 0);
        frm.set_value("employee_name", "");
        frm.doc.earnings_table = [];
        frm.doc.deductions_table = [];
        frm.doc.advance_recovery_table = [];
        clear_component_overrides(frm);
        frm.get_field("advance_summary_html").$wrapper.html("");
        const fi = frm.get_field("fuel_incentive_html");
        if (fi) fi.$wrapper.html("");
        const te = frm.get_field("trip_expenses_html");
        if (te) te.$wrapper.html("");
        frm.refresh_fields(["earnings_table", "deductions_table", "advance_recovery_table"]);
        if (frm.doc.driver && frm.doc.salary_type === "Driver Salary") {
            frappe.call({
                method: "frappe.client.get",
                args: { doctype: "Driver", name: frm.doc.driver },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("employee_name", r.message.full_name || r.message.name || "");
                        frm.set_value("ctc", r.message.custom_ctc || 0);
                        frm.set_value("company", r.message.custom_company || "");
                        frm.set_value("branch", r.message.custom_branch || "");
                        frappe.show_alert({ message: __("✓ Driver details loaded"), indicator: "green" });
                        update_salary_components(frm);
                        schedule_attendance_fetch(frm);
                        fetch_driver_advance(frm);
                        fetch_driver_fuel_incentive(frm);
                        fetch_and_render_fuel_incentive(frm);
                        fetch_and_render_trip_expenses(frm);
                    }
                }
            });
        }
    },

    employee: function(frm) {
        // Clear previous data when employee changes
        frm.set_value('present_days', 0);
        frm.set_value('absent_days', 0);
        frm.set_value("leave_with_pay", 0);
        frm.set_value("leave_without_pay", 0);
        frm.set_value("total_attendance_days", 0);
        frm.set_value("worked_days", 0);
        frm.set_value("ctc", 0);
        frm.set_value("employee_name", "");
        frm.doc.earnings_table = [];
        frm.doc.deductions_table = [];
        frm.doc.advance_recovery_table = [];
        clear_component_overrides(frm);
        frm.get_field("advance_summary_html").$wrapper.html("");
        frm.refresh_fields(["earnings_table", "deductions_table", "advance_recovery_table"]);
        if (frm.doc.employee && frm.doc.salary_type !== "Driver Salary") {
            // Fetch employee details using the correct method path
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Employee',
                    name: frm.doc.employee
                },
                callback: function(r) {
                    if (r.message) {
                        let emp = r.message;
                        frm.set_value('employee_name', emp.employee_name);
                        frm.set_value('ctc', emp.ctc || 0);
                        frm.set_value('department', emp.department);
                        frm.set_value('designation', emp.designation);
                        frm.set_value('branch', emp.branch);
                        frm.set_value('company', emp.company);
                        
                        // Fetch active salary structure assignment
                        frappe.call({
                            method: 'frappe.client.get_list',
                            args: {
                                doctype: 'Salary Structure Assignment',
                                filters: {
                                    employee: frm.doc.employee,
                                    docstatus: 1,
                                    from_date: ['<=', frappe.datetime.get_today()]
                                },
                                fields: ['name', 'salary_structure', 'from_date'],
                                order_by: 'from_date desc',
                                limit_page_length: 1
                            },
                            callback: function(r) {
                                if (r.message && r.message.length > 0) {
                                    frm.set_value('salary_structure', r.message[0].salary_structure);
                                }
                            }
                        });
                        
                        frappe.show_alert({
                            message: __('✓ Employee details loaded'),
                            indicator: 'green'
                        });
                        update_salary_components(frm);
                        schedule_attendance_fetch(frm);
                        fetch_employee_advance(frm);
                        fetch_and_render_employee_incentive(frm);
                        fetch_and_render_employee_lr_money(frm);
                    }
                }
            });
        }
    },
    
    from_date: function(frm) {
        if (frm.doc.from_date && frm.doc.to_date) {
            calculate_period(frm);
            schedule_attendance_fetch(frm);
            fetch_driver_fuel_incentive(frm);
            if (frm.doc.salary_type === "Driver Salary" && frm.doc.driver) {
                fetch_driver_advance(frm);
            } else if (frm.doc.employee) {
                fetch_employee_advance(frm);
            }
            fetch_and_render_fuel_incentive(frm);
            fetch_and_render_trip_expenses(frm);
            fetch_and_render_employee_incentive(frm);
            fetch_and_render_employee_lr_money(frm);
        }
    },

    to_date: function(frm) {
        if (frm.doc.from_date && frm.doc.to_date) {
            calculate_period(frm);
            schedule_attendance_fetch(frm);
            fetch_driver_fuel_incentive(frm);
            if (frm.doc.salary_type === "Driver Salary" && frm.doc.driver) {
                fetch_driver_advance(frm);
            } else if (frm.doc.employee) {
                fetch_employee_advance(frm);
            }
            fetch_and_render_fuel_incentive(frm);
            fetch_and_render_trip_expenses(frm);
            fetch_and_render_employee_incentive(frm);
            fetch_and_render_employee_lr_money(frm);
        }
    },
    
    company: function(frm) {
        schedule_attendance_fetch(frm);
        fetch_and_render_employee_lr_money(frm);
    },
    
    ctc: function(frm) {
        update_salary_components(frm);
    },
    
    present_days: function(frm) {
        update_salary_components(frm);
    },
    
    leave_with_pay: function(frm) {
        update_salary_components(frm);
    },
    
    leave_without_pay: function(frm) {
        update_salary_components(frm);
    },
    
    absent_days: function(frm) {
        update_salary_components(frm);
    },
    
    before_save: function(frm) {
        // update_salary_components() now fetches the component list from the
        // linked Salary Structure asynchronously — return the promise so
        // Frappe's save flow waits for rows to be ensured before saving.
        return update_salary_components(frm).then(() => {
            // Validate before save
            if (frm.doc.salary_type === "Driver Salary" && !frm.doc.driver) {
                frappe.throw(__('Please select a Driver'));
            }
            if (frm.doc.salary_type !== "Driver Salary" && !frm.doc.employee) {
                frappe.throw(__('Please select an Employee'));
            }
            if (!frm.doc.ctc) {
                frappe.throw(__('CTC is required'));
            }
            if (!frm.doc.from_date || !frm.doc.to_date) {
                frappe.throw(__('Please select payroll period'));
            }
        });
    },
    
    after_save: function(frm) {
        frappe.show_alert({
            message: __('✓ Payroll saved successfully'),
            indicator: 'green'
        });
    }
});

// Sync recovery amount changes to Advances deduction row
frappe.ui.form.on('Payroll Advance Recovery', {
    recovery_amount: function(frm) {
        update_advance_row_balances(frm);
        sync_advance_to_deductions(frm);
        render_advance_summary_from_doc(frm);
        frm.refresh_field("advance_recovery_table");
    },

    // Grid row delete fires this on the CHILD doctype, not on Staff Payroll —
    // without a handler here the Advances deduction keeps the removed row's amount.
    advance_recovery_table_remove: function(frm) {
        update_advance_row_balances(frm);
        sync_advance_to_deductions(frm);
        render_advance_summary_from_doc(frm);
        frm.refresh_field("advance_recovery_table");
    }
});

// Custom field handlers
// earnings_table and deductions_table both use the standard "Salary Detail"
// child doctype, so both tables' events land in this single handler block.
// earnings_table_add / deductions_table_add are field-name-scoped (no clash),
// but "amount" fires for rows from either table, so it branches on parentfield.
frappe.ui.form.on('Salary Detail', {
    amount: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        // Only real grid edits reach this handler — set_child_amount() assigns
        // row.amount directly and never fires it. So a hit on a formula-driven
        // component means the user typed the number themselves.
        if (FORMULA_COMPONENTS[row.parentfield] === row.salary_component) {
            mark_component_overridden(frm, row.salary_component);
        }
        if (row.parentfield === 'deductions_table') {
            if (row?.salary_component === "Advances") {
                sync_deductions_to_advance(frm, flt(row.amount));
            }
            calculate_deductions(frm);
        } else {
            calculate_earnings(frm);
        }
    },

    earnings_table_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.salary_component = 'Basic Salary';
    },

    deductions_table_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.salary_component = 'Professional Tax';
    }
});

// ============== Helper Functions ==============

function fetch_attendance_data(frm, silent) {
    const person = frm.doc.salary_type === "Driver Salary" ? frm.doc.driver : frm.doc.employee;
    if (!person || !frm.doc.from_date || !frm.doc.to_date) {
        if (!silent) {
            frappe.throw(__('Please fill in Employee/Driver and Payroll Period first'));
        }
        return;
    }

    frappe.call({
        method: 'logicore.logicore.doctype.staff_payroll.staff_payroll.fetch_attendance_for_period',
        args: {
            employee: person,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date,
            company: frm.doc.company
        },
        callback: function(r) {
            if (r.message) {
                let present = r.message.present_days || 0;
                let absent = r.message.absent_days || 0;
                let leave_with_pay = r.message.leave_with_pay || 0;
                let leave_without_pay = r.message.leave_without_pay || 0;
                
                frm.set_value('present_days', present);
                frm.set_value('absent_days', absent);
                frm.set_value('leave_with_pay', leave_with_pay);
                frm.set_value('leave_without_pay', leave_without_pay);
                update_salary_components(frm);
                
                if (!silent) {
                    frappe.show_alert({
                        message: __('✓ Attendance fetched<br>Present: {0} | Leave: {1} | Absent: {2}', 
                            [present, leave_with_pay, absent]),
                        indicator: 'green'
                    });
                }
            } else {
                if (!silent) {
                    frappe.show_alert({
                        message: __('⚠️ No attendance records found for this period'),
                        indicator: 'orange'
                    });
                }
            }
        }
    });
}

function schedule_attendance_fetch(frm) {
    const person = frm.doc.salary_type === "Driver Salary" ? frm.doc.driver : frm.doc.employee;
    if (frm.doc.docstatus !== 0 || !person || !frm.doc.from_date || !frm.doc.to_date) {
        return;
    }
    
    clearTimeout(frm._staff_payroll_attendance_timer);
    frm._staff_payroll_attendance_timer = setTimeout(() => {
        fetch_attendance_data(frm, true);
    }, 300);
}

function calculate_period(frm) {
    if (!frm.doc.from_date || !frm.doc.to_date) return;
    if (is_old_data_import(frm)) return;

    let from_date = new Date(frm.doc.from_date);
    let to_date = new Date(frm.doc.to_date);
    let actual_days = Math.floor((to_date - from_date) / (1000 * 60 * 60 * 24)) + 1;
    // Driver salary always uses 30 days regardless of actual month length
    let total_days = frm.doc.salary_type === "Driver Salary" ? 30 : actual_days;

    frm.set_value('total_days', total_days);
    frm.doc.working_days = total_days;
    update_salary_components(frm);
}

function update_salary_components(frm) {
    if (frm.doc.docstatus !== 0 || is_old_data_import(frm)) return Promise.resolve();

    return get_salary_structure_components(frm).then(components => {
        ensure_salary_component_rows(frm, components);

        let ctc = flt(frm.doc.ctc);
        // Driver salary always uses 30 days regardless of actual month length
        let total_days = frm.doc.salary_type === "Driver Salary" ? 30 : flt(frm.doc.total_days);
        let salary_per_day = total_days ? ctc / total_days : 0;
        let present = flt(frm.doc.present_days);
        let lwp = flt(frm.doc.leave_with_pay);
        let lwop = flt(frm.doc.leave_without_pay);
        let absent = flt(frm.doc.absent_days);
        let total_attendance = present + lwp + lwop + absent;
        let worked_days = present + lwp;
        // let basic_salary = salary_per_day * worked_days;  // prorated: salary_per_day × (present + lwp)
        let basic_salary = ctc;  // master salary flows directly into Basic Salary
        // Driver salary always prices a day at ctc/30, so a 31-day calendar
        // month has one more marked attendance day than the pay basis covers —
        // that extra day must not be charged as a leave deduction.
        let extra_days = frm.doc.salary_type === "Driver Salary" ? Math.max(0, total_attendance - total_days) : 0;
        let lop_days = Math.max(0, lwop - extra_days);
        let lop = salary_per_day * lop_days;

        frm.set_value('salary_per_day', salary_per_day);
        frm.set_value('total_attendance_days', total_attendance);
        frm.set_value('worked_days', worked_days);

        seed_component_overrides(frm, {
            'Basic Salary': basic_salary,
            'Leave Deductions': lop,
        });

        // Manually edited components keep the user's amount (see FORMULA_COMPONENTS)
        if (!is_component_overridden(frm, 'Basic Salary')) {
            set_child_amount(frm, 'earnings_table', 'salary_component', 'Basic Salary', basic_salary);
        }
        if (!is_component_overridden(frm, 'Leave Deductions')) {
            set_child_amount(frm, 'deductions_table', 'salary_component', 'Leave Deductions', lop);
        }

        calculate_earnings(frm);
        calculate_deductions(frm);
        frm.refresh_field('earnings_table');
        frm.refresh_field('deductions_table');
        configure_salary_detail_grid_columns(frm);
    });
}

const _MOVED_TO_SECTIONS = ['Fuel Incentive', 'Trip Expenses'];

function ensure_salary_component_rows(frm, components) {
    const earning_types = (components && components.earnings) || [];
    const deduction_types = (components && components.deductions) || [];

    // Remove earning rows that were moved to dedicated sections (also purge from locals)
    const to_remove = (frm.doc.earnings_table || []).filter(
        row => _MOVED_TO_SECTIONS.includes(row.salary_component)
    );
    to_remove.forEach(row => {
        // Remove from Frappe's locals store so the grid does not re-render them
        if (locals["Salary Detail"] && locals["Salary Detail"][row.name]) {
            delete locals["Salary Detail"][row.name];
        }
    });
    frm.doc.earnings_table = (frm.doc.earnings_table || []).filter(
        row => !_MOVED_TO_SECTIONS.includes(row.salary_component)
    );

    earning_types.forEach(earning_type => {
        let row = find_child_row(frm, 'earnings_table', 'salary_component', earning_type);
        if (!row) {
            row = frm.add_child('earnings_table');
            row.salary_component = earning_type;
            row.amount = 0;
        } else if (row.amount == null) {
            row.amount = 0;
        }
    });

    deduction_types.forEach(deduction_type => {
        let row = find_child_row(frm, 'deductions_table', 'salary_component', deduction_type);
        if (!row) {
            row = frm.add_child('deductions_table');
            row.salary_component = deduction_type;
            row.amount = 0;
        } else if (row.amount == null) {
            row.amount = 0;
        }
    });
}

function find_child_row(frm, table_field, type_field, type_value) {
    return (frm.doc[table_field] || []).find(row => row[type_field] === type_value);
}

function set_child_amount(frm, table_field, type_field, type_value, amount) {
    let row = find_child_row(frm, table_field, type_field, type_value);
    if (row) {
        row.amount = amount;
    }
}

// ---------------------------------------------------------------------------
// Manual override tracking
//
// These two components are the only ones update_salary_components() computes
// from a formula. Once the user types their own amount into one of them, the
// formula must stop touching it for the rest of that document — the value they
// saved is the value that stays. Switching employee / driver / salary_type
// wipes the component tables, and that is what brings the formula back.
// ---------------------------------------------------------------------------
const FORMULA_COMPONENTS = {
    earnings_table: 'Basic Salary',
    deductions_table: 'Leave Deductions',
};

function mark_component_overridden(frm, component) {
    frm._manual_component_override = frm._manual_component_override || {};
    frm._manual_component_override[component] = true;
}

function is_component_overridden(frm, component) {
    return !!(frm._manual_component_override || {})[component];
}

function clear_component_overrides(frm) {
    frm._manual_component_override = {};
    frm._manual_override_seeded = true;  // tables are being rebuilt — nothing to re-derive
}

// A saved doc reopened in a fresh form has no memory of past manual edits, so
// derive them: a stored amount that doesn't match the formula IS a manual edit.
function seed_component_overrides(frm, auto_values) {
    if (frm._manual_override_seeded) return;
    frm._manual_override_seeded = true;
    if (frm.is_new()) return;
    Object.keys(FORMULA_COMPONENTS).forEach(table_field => {
        const component = FORMULA_COMPONENTS[table_field];
        const row = find_child_row(frm, table_field, 'salary_component', component);
        if (!row) return;
        if (Math.abs(flt(row.amount) - flt(auto_values[component])) > 0.005) {
            mark_component_overridden(frm, component);
        }
    });
}

function calculate_earnings(frm) {
    let total = 0;
    (frm.doc.earnings_table || []).forEach(row => {
        total += flt(row.amount);
    });
    frm.doc.total_earnings = total;
    frm.refresh_field('total_earnings');
    calculate_net_salary(frm);
}

function calculate_deductions(frm) {
    let total = 0;
    (frm.doc.deductions_table || []).forEach(row => {
        total += flt(row.amount);
    });
    frm.doc.total_deductions = total;
    frm.refresh_field('total_deductions');
    calculate_net_salary(frm);
}

function calculate_net_salary(frm) {
    let net = flt(frm.doc.total_earnings) - flt(frm.doc.total_deductions);
    frm.doc.net_salary = net;
    frm.refresh_field('net_salary');
}

function calculate_payroll(frm) {
    if (!frm.doc.employee || !frm.doc.ctc) {
        frappe.throw(__('Please fill required fields first'));
        return;
    }
    
    frappe.show_alert({
        message: __('Calculating payroll...'),
        indicator: 'blue'
    });

    update_salary_components(frm).then(() => frm.save());
}

function approve_payroll(frm) {
    frappe.confirm(__('Are you sure you want to approve this payroll?'), function() {
        frappe.call({
            method: 'frappe.client.set_value',
            args: {
                doctype: 'Staff Payroll',
                name: frm.doc.name,
                fieldname: {
                    approval_status: 'Approved',
                    approved_by: frappe.session.user,
                    approved_date: frappe.datetime.now_datetime(),
                    status: 'Approved'
                }
            },
            callback: function(r) {
                if (r.message) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('✓ Payroll approved successfully'),
                        indicator: 'green'
                    });
                }
            }
        });
    });
}

// "Salary Detail" is the standard HR child doctype and carries HR-only grid
// columns (Abbr, Depends on Payment Days, Is Tax Applicable, Accrual
// Component) that don't apply here. Hidden on this form only — doesn't touch
// the Salary Detail doctype itself, so Salary Structure/Salary Slip grids
// elsewhere are unaffected.
const _SALARY_DETAIL_HIDDEN_COLUMNS = [
    'abbr', 'depends_on_payment_days', 'is_tax_applicable',
    'variable_based_on_taxable_salary', 'accrual_component',
];

// Previous approach: CSS `display:none !important` on the extra columns.
// Root cause found: Grid.setup_visible_columns() memoizes its result
// (`if (this.visible_columns.length > 0) return;`) and never recomputes —
// so every docfield.hidden/columns mutation was applied correctly but never
// actually reflected in the rendered widths, no matter what. Worse, a hard
// CSS override would have permanently blocked the "Configure Columns"
// dialog from ever showing a column the user manually re-enabled. Kept the
// CSS version here for reference, not deleted:
// const _SALARY_DETAIL_HIDE_CSS_ID = 'tms-staff-payroll-hide-salary-detail-cols';
// function ensure_salary_detail_hide_css() { ... (see git history) ... }

function configure_salary_detail_grid_columns(frm) {
    ['earnings_table', 'deductions_table'].forEach(fieldname => {
        const grid = frm.fields_dict[fieldname] && frm.fields_dict[fieldname].grid;
        // Docfield mutations are cached per-docname (frappe.meta.docfield_copy),
        // and Frappe reuses the same Grid instance across different Staff
        // Payroll records opened in one session — so the guard must be keyed
        // by docname too, not just "have we ever run this once".
        if (!grid || grid._tms_columns_configured === frm.docname) return;
        grid.set_column_disp(_SALARY_DETAIL_HIDDEN_COLUMNS, false);
        // Roughly 40/40/20 (Component/Amount/checkbox+row-index+settings) —
        // `columns` drives Frappe's own proportional width redistribution.
        grid.update_docfield_property('salary_component', 'columns', 4);
        grid.update_docfield_property('amount', 'columns', 4);
        // reset_grid() clears the visible_columns/grid_rows cache and fully
        // rebuilds head + rows — the only way to make the above mutations
        // actually take effect, per the memoization issue noted above. Only
        // needs to run once per grid instance; afterwards Frappe's own
        // machinery (including the Configure Columns dialog) keeps working
        // normally on top of this corrected baseline.
        grid.reset_grid();
        grid._tms_columns_configured = frm.docname;
    });
}

function update_status_color(frm) {
    let status = frm.doc.status;
    let color = '#999';
    
    switch(status) {
        case 'Draft': color = '#999'; break;
        case 'Pending Approval': color = '#ff9800'; break;
        case 'Approved': color = '#4caf50'; break;
        case 'Processed': color = '#2196f3'; break;
        case 'Cancelled': color = '#f44336'; break;
    }
    
    // Update the status badge
    try {
        $('[data-fieldname="status"]').find('.frappe-control').css('border-left', '4px solid ' + color);
    } catch(e) {
        // Silently fail if element not found
    }
}

function get_advance_cutoff_date(frm) {
    // to_date is the selected payroll period's end — advances given after it
    // haven't happened yet "as of" this period and must not show as
    // outstanding. payroll_date defaults to Today and is unrelated to the
    // selected period, so it can only be a fallback before to_date is set.
    return frm.doc.to_date || frm.doc.payroll_date || frm.doc.from_date || null;
}

function fetch_employee_advance(frm) {
    if (!frm.doc.employee) return;
    frappe.call({
        method: "logicore.logicore.doctype.staff_payroll.staff_payroll.get_employee_advances",
        args: {
            employee: frm.doc.employee,
            exclude_payroll: frm.doc.docstatus === 0 ? frm.doc.name : null,
            until_date: get_advance_cutoff_date(frm),
        },
        callback: function(r) {
            const advances = r.message || [];
            frm.doc.advance_recovery_table = [];
            if (!advances.length) {
                frm.refresh_field("advance_recovery_table");
                sync_advance_to_deductions(frm);
                frm.get_field("advance_summary_html").$wrapper.html("");
                return;
            }
            frm._advance_base_recovered = frm._advance_base_recovered || {};
            advances.forEach(adv => {
                const row = frm.add_child("advance_recovery_table");
                row.payment_ref       = adv.payment_ref;
                row.advance_date      = adv.advance_date;
                row.total_advance     = adv.total_advance;
                // Cache the base (recovered in previously submitted payrolls) for validation
                frm._advance_base_recovered[adv.payment_ref] = flt(adv.already_recovered);
                row.already_recovered = adv.already_recovered;
                row.outstanding       = adv.outstanding;
                row.recovery_amount   = adv.outstanding;
            });
            frm.refresh_field("advance_recovery_table");
            sync_advance_to_deductions(frm);
            render_advance_summary_from_doc(frm);
            frappe.show_alert({
                message: __("{0} advance(s) found. Review recovery amounts.", [advances.length]),
                indicator: "orange"
            });
        }
    });
}

function fetch_driver_fuel_incentive(frm) {
    if (!frm.doc.driver || !frm.doc.from_date || !frm.doc.to_date) return;
    if (frm.doc.salary_type !== "Driver Salary") return;
    frappe.call({
        method: "logicore.logicore.doctype.staff_payroll.staff_payroll.get_driver_fuel_incentive",
        args: {
            driver: frm.doc.driver,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            const incentive = r.message || 0;
            set_child_amount(frm, "earnings_table", "salary_component", "Fuel Incentive", incentive);
            frm.refresh_field("earnings_table");
            calculate_earnings(frm);
            if (incentive > 0) {
                frappe.show_alert({
                    message: __("✓ Fuel Incentive fetched: ₹{0}", [flt(incentive).toLocaleString("en-IN")]),
                    indicator: "green"
                });
            }
        }
    });
}

function fetch_driver_advance(frm) {
    if (!frm.doc.driver) return;
    frappe.call({
        method: "logicore.logicore.doctype.staff_payroll.staff_payroll.get_driver_advances",
        args: {
            driver: frm.doc.driver,
            exclude_payroll: frm.doc.docstatus === 0 ? frm.doc.name : null,
            until_date: get_advance_cutoff_date(frm),
        },
        callback: function(r) {
            const advances = r.message || [];
            frm.doc.advance_recovery_table = [];
            if (!advances.length) {
                frm.refresh_field("advance_recovery_table");
                sync_advance_to_deductions(frm);
                frm.get_field("advance_summary_html").$wrapper.html("");
                return;
            }
            frm._advance_base_recovered = frm._advance_base_recovered || {};
            advances.forEach(adv => {
                const row = frm.add_child("advance_recovery_table");
                row.payment_ref       = adv.payment_ref;
                row.advance_date      = adv.advance_date;
                row.total_advance     = adv.total_advance;
                // Cache the base (recovered in previously submitted payrolls) for validation
                frm._advance_base_recovered[adv.payment_ref] = flt(adv.already_recovered);
                row.already_recovered = adv.already_recovered;
                row.outstanding       = adv.outstanding;
                row.recovery_amount   = adv.outstanding;
            });
            frm.refresh_field("advance_recovery_table");
            sync_advance_to_deductions(frm);
            render_advance_summary_from_doc(frm);
            frappe.show_alert({
                message: __("{0} driver advance(s) found. Review recovery amounts.", [advances.length]),
                indicator: "orange"
            });
        }
    });
}

function sync_advance_to_deductions(frm) {
    const total = (frm.doc.advance_recovery_table || [])
        .reduce((s, r) => s + flt(r.recovery_amount), 0);
    set_child_amount(frm, "deductions_table", "salary_component", "Advances", total);
    frm.refresh_field("deductions_table");
    calculate_deductions(frm);
}

function update_advance_row_balances(frm) {
    (frm.doc.advance_recovery_table || []).forEach(row => {
        const total_advance = flt(row.total_advance);
        // Use cached base (pre-this-payroll recovered); fall back to already_recovered for safety
        const base = (frm._advance_base_recovered && row.payment_ref != null && frm._advance_base_recovered[row.payment_ref] != null)
            ? flt(frm._advance_base_recovered[row.payment_ref])
            : flt(row.already_recovered);
        const entered_recovery = Math.max(0, flt(row.recovery_amount));
        const max_recovery = Math.max(0, total_advance - base);
        const normalized_recovery = Math.min(entered_recovery, max_recovery);

        if (entered_recovery > max_recovery) {
            row.recovery_amount = normalized_recovery;
            frappe.msgprint({
                title: __("Invalid Recovery Amount"),
                indicator: "orange",
                message: __("You can recover only up to ₹{0} for advance {1}.", [
                    flt(max_recovery).toLocaleString("en-IN", { minimumFractionDigits: 2 }),
                    row.payment_ref,
                ]),
            });
        }

        row.recovery_amount = normalized_recovery;
        // outstanding = remaining after this payroll's recovery (for grid display only)
        row.outstanding = Math.max(0, max_recovery - normalized_recovery);
        // already_recovered stays unchanged — Python will update it to cumulative on save
    });
}

function sync_deductions_to_advance(frm, target_total) {
    const advance_rows = frm.doc.advance_recovery_table || [];
    if (!advance_rows.length) {
        set_child_amount(frm, "deductions_table", "salary_component", "Advances", 0);
        frm.refresh_field("deductions_table");
        return;
    }

    let remaining = Math.max(0, flt(target_total));
    let assigned_total = 0;
    advance_rows.forEach(row => {
        const base = (frm._advance_base_recovered && row.payment_ref != null && frm._advance_base_recovered[row.payment_ref] != null)
            ? flt(frm._advance_base_recovered[row.payment_ref])
            : flt(row.already_recovered);
        const max_recovery = Math.max(0, flt(row.total_advance) - base);
        const assigned = Math.min(max_recovery, remaining);
        row.recovery_amount = assigned;
        row.outstanding = Math.max(0, max_recovery - assigned);
        // already_recovered stays unchanged — Python will update it to cumulative on save
        remaining -= assigned;
        assigned_total += assigned;
    });

    set_child_amount(frm, "deductions_table", "salary_component", "Advances", assigned_total);
    render_advance_summary_from_doc(frm);
    frm.refresh_field("advance_recovery_table");
    frm.refresh_field("deductions_table");
}

function get_advance_summary_totals(frm) {
    return (frm.doc.advance_recovery_table || []).reduce((totals, row) => {
        const total_advance = flt(row.total_advance);
        let effective_recovered, effective_outstanding;
        if (frm.doc.__islocal) {
            // New (unsaved) doc: show base only — summary stays fixed until save
            const base = (frm._advance_base_recovered && row.payment_ref && frm._advance_base_recovered[row.payment_ref] != null)
                ? flt(frm._advance_base_recovered[row.payment_ref])
                : flt(row.already_recovered);
            effective_recovered = base;
            effective_outstanding = Math.max(0, total_advance - base);
        } else {
            // Saved doc: Python already set already_recovered to cumulative
            effective_recovered = flt(row.already_recovered);
            effective_outstanding = flt(row.outstanding);
        }
        totals.total_advance += total_advance;
        totals.total_recovered += effective_recovered;
        totals.total_outstanding += effective_outstanding;
        return totals;
    }, {
        total_advance: 0,
        total_recovered: 0,
        total_outstanding: 0,
    });
}

function render_advance_summary_from_doc(frm) {
    const { total_advance, total_recovered, total_outstanding } = get_advance_summary_totals(frm);
    const fmt = v => "₹ " + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2 });
    frm.get_field("advance_summary_html").$wrapper.html(`
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;
            background:var(--border-color);border:1px solid var(--border-color);
            border-radius:6px;overflow:hidden;font-size:12px;margin:8px 0;">
            <div style="background:var(--card-bg);padding:8px 14px;">
                <div style="color:var(--text-muted);font-size:11px;">Total Advance Given</div>
                <div style="font-weight:700;color:var(--blue-500);">${fmt(total_advance)}</div>
            </div>
            <div style="background:var(--card-bg);padding:8px 14px;">
                <div style="color:var(--text-muted);font-size:11px;">Already Recovered</div>
                <div style="font-weight:700;color:var(--green-500);">${fmt(total_recovered)}</div>
            </div>
            <div style="background:var(--card-bg);padding:8px 14px;">
                <div style="color:var(--text-muted);font-size:11px;">Outstanding Balance</div>
                <div style="font-weight:700;color:var(--red-500);font-size:13px;">${fmt(total_outstanding)}</div>
            </div>
        </div>`);
}

function fetch_and_render_fuel_incentive(frm) {
    if (!frm.doc.driver || !frm.doc.from_date || !frm.doc.to_date) {
        render_fuel_incentive_html(frm, []);
        return;
    }
    if (frm.doc.salary_type !== "Driver Salary") return;

    frappe.call({
        method: "logicore.logicore.doctype.staff_payroll.staff_payroll.get_driver_fuel_incentive_details",
        args: {
            driver: frm.doc.driver,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            render_fuel_incentive_html(frm, r.message || []);
        }
    });
}

function render_fuel_incentive_html(frm, rows) {
    const field = frm.get_field("fuel_incentive_html");
    if (!field) return;

    if (!rows.length) {
        field.$wrapper.html(`
            <div style="padding:10px 14px;color:var(--text-muted);font-size:12px;">
                No fuel incentive records found for this period.
            </div>`);
        return;
    }

    const fmt_date = d => d ? frappe.datetime.str_to_user(d) : "";
    const fmt_amt  = v => "₹ " + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2 });

    let total_expense = 0;
    const rows_html = rows.map((r, idx) => {
        total_expense += flt(r.expense_amount);
        return `<tr>
            <td style="padding:6px 10px;">${idx + 1}</td>
            <td style="padding:6px 10px;"><a href="/app/fuel-urea-expenses/${r.name}" target="_blank" style="color:var(--blue-500);text-decoration:none;">${r.name || ""}</a></td>
            <td style="padding:6px 10px;">${fmt_date(r.date)}</td>
            <td style="padding:6px 10px;">${r.vehicle || ""}</td>
            <td style="padding:6px 10px;">${r.payment_reference || ""}</td>
            <td style="padding:6px 10px;text-align:right;">${fmt_amt(r.expense_amount)}</td>
        </tr>`;
    }).join("");

    field.$wrapper.html(`
        <div style="overflow:auto;max-height:360px;margin:4px 0;border:1px solid var(--border-color);">
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead>
                    <tr style="background:var(--subtle-fg);color:var(--text-muted);">
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">S.No.</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">ID</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Date</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Vehicle</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Payment Reference</th>
                        <th style="padding:6px 10px;text-align:right;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Amount Paid to Driver</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows_html}
                </tbody>
                <tfoot>
                    <tr style="border-top:2px solid var(--border-color);background:var(--subtle-fg);">
                        <td colspan="5" style="padding:6px 10px;font-weight:700;position:sticky;bottom:0;background:var(--subtle-fg);">Total</td>
                        <td style="padding:6px 10px;text-align:right;font-weight:700;color:var(--green-500);position:sticky;bottom:0;background:var(--subtle-fg);">${fmt_amt(total_expense)}</td>
                    </tr>
                </tfoot>
            </table>
        </div>`);
}

function fetch_and_render_trip_expenses(frm) {
    if (!frm.doc.driver || !frm.doc.from_date || !frm.doc.to_date) {
        render_trip_expenses_html(frm, []);
        return;
    }
    if (frm.doc.salary_type !== "Driver Salary") return;

    frappe.call({
        method: "logicore.logicore.doctype.staff_payroll.staff_payroll.get_driver_trip_expense_details",
        args: {
            driver: frm.doc.driver,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            render_trip_expenses_html(frm, r.message || []);
        }
    });
}

function render_trip_expenses_html(frm, rows) {
    const field = frm.get_field("trip_expenses_html");
    if (!field) return;

    if (!rows.length) {
        field.$wrapper.html(`
            <div style="padding:10px 14px;color:var(--text-muted);font-size:12px;">
                No trip expense records found for this period.
            </div>`);
        return;
    }

    const fmt_date = d => d ? frappe.datetime.str_to_user(d) : "";
    const fmt_amt  = v => "₹ " + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2 });

    let total_amount = 0;
    const rows_html = rows.map((r, idx) => {
        total_amount += flt(r.amount);
        return `<tr>
            <td style="padding:6px 10px;">${idx + 1}</td>
            <td style="padding:6px 10px;"><a href="/app/payment/${r.name}" target="_blank" style="color:var(--blue-500);text-decoration:none;">${r.name || ""}</a></td>
            <td style="padding:6px 10px;">${fmt_date(r.date)}</td>
            <td style="padding:6px 10px;">${r.payment_reference || ""}</td>
            <td style="padding:6px 10px;text-align:right;">${fmt_amt(r.amount)}</td>
        </tr>`;
    }).join("");

    field.$wrapper.html(`
        <div style="overflow:auto;max-height:360px;margin:4px 0;border:1px solid var(--border-color);">
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead>
                    <tr style="background:var(--subtle-fg);color:var(--text-muted);">
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">S.No.</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">ID</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Date</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Payment Reference</th>
                        <th style="padding:6px 10px;text-align:right;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Amount (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows_html}
                </tbody>
                <tfoot>
                    <tr style="border-top:2px solid var(--border-color);background:var(--subtle-fg);">
                        <td colspan="4" style="padding:6px 10px;font-weight:700;position:sticky;bottom:0;background:var(--subtle-fg);">Total</td>
                        <td style="padding:6px 10px;text-align:right;font-weight:700;color:var(--green-500);position:sticky;bottom:0;background:var(--subtle-fg);">${fmt_amt(total_amount)}</td>
                    </tr>
                </tfoot>
            </table>
        </div>`);
}

function fetch_and_render_employee_incentive(frm) {
    if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date) {
        render_employee_incentive_html(frm, []);
        return;
    }
    if (frm.doc.salary_type !== "Employee Salary") return;

    frappe.call({
        method: "logicore.logicore.doctype.staff_payroll.staff_payroll.get_employee_incentive_details",
        args: {
            employee: frm.doc.employee,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date
        },
        callback: function(r) {
            render_employee_incentive_html(frm, r.message || []);
        }
    });
}

function render_employee_incentive_html(frm, rows) {
    const field = frm.get_field("employee_incentive_html");
    if (!field) return;

    if (!rows.length) {
        field.$wrapper.html(`
            <div style="padding:10px 14px;color:var(--text-muted);font-size:12px;">
                No employee incentive records found for this period.
            </div>`);
        return;
    }

    const fmt_date = d => d ? frappe.datetime.str_to_user(d) : "";
    const fmt_amt  = v => "₹ " + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2 });

    let total_amount = 0;
    const rows_html = rows.map((r, idx) => {
        total_amount += flt(r.amount);
        return `<tr>
            <td style="padding:6px 10px;">${idx + 1}</td>
            <td style="padding:6px 10px;"><a href="/app/payment/${r.name}" target="_blank" style="color:var(--blue-500);text-decoration:none;">${r.name || ""}</a></td>
            <td style="padding:6px 10px;">${fmt_date(r.date)}</td>
            <td style="padding:6px 10px;">${r.payment_reference || ""}</td>
            <td style="padding:6px 10px;text-align:right;">${fmt_amt(r.amount)}</td>
        </tr>`;
    }).join("");

    field.$wrapper.html(`
        <div style="overflow:auto;max-height:360px;margin:4px 0;border:1px solid var(--border-color);">
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead>
                    <tr style="background:var(--subtle-fg);color:var(--text-muted);">
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">S.No.</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">ID</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Date</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Payment Reference</th>
                        <th style="padding:6px 10px;text-align:right;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Amount (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows_html}
                </tbody>
                <tfoot>
                    <tr style="border-top:2px solid var(--border-color);background:var(--subtle-fg);">
                        <td colspan="4" style="padding:6px 10px;font-weight:700;position:sticky;bottom:0;background:var(--subtle-fg);">Total</td>
                        <td style="padding:6px 10px;text-align:right;font-weight:700;color:var(--green-500);position:sticky;bottom:0;background:var(--subtle-fg);">${fmt_amt(total_amount)}</td>
                    </tr>
                </tfoot>
            </table>
        </div>`);
}

function fetch_and_render_employee_lr_money(frm) {
    if (!frm.doc.employee || !frm.doc.from_date || !frm.doc.to_date) {
        render_employee_lr_money_html(frm, []);
        return;
    }
    if (frm.doc.salary_type !== "Employee Salary") return;

    frappe.call({
        method: "logicore.logicore.doctype.staff_payroll.staff_payroll.get_employee_lr_money_details",
        args: {
            employee: frm.doc.employee,
            from_date: frm.doc.from_date,
            to_date: frm.doc.to_date,
            company: frm.doc.company || "",
        },
        callback: function(r) {
            render_employee_lr_money_html(frm, r.message || []);
        }
    });
}

function render_employee_lr_money_html(frm, rows) {
    const field = frm.get_field("employee_lr_money_html");
    if (!field) return;

    if (!rows.length) {
        field.$wrapper.html(`
            <div style="padding:10px 14px;color:var(--text-muted);font-size:12px;">
                No employee LR money records found for this period.
            </div>`);
        const row = find_child_row(frm, "earnings_table", "salary_component", "Employee LR Money");
        if (row) {
            row.amount = 0;
            frm.refresh_field("earnings_table");
            calculate_earnings(frm);
        }
        return;
    }

    const fmt_date = d => d ? frappe.datetime.str_to_user(d) : "";
    const fmt_amt  = v => "₹ " + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2 });

    let total_amount = 0;
    const rows_html = rows.map((r, idx) => {
        total_amount += flt(r.amount);
        const route = [r.origin_city, r.destination_city_1].filter(Boolean).join(" → ");
        const vehicle = r.vehicle_no || r.vehicle_market || "";
        const trip_ref = r.tcntrip_no || r.name || "";
        const vendor_payment_cell = r.vendor_payment
            ? `<a href="/app/vendor-payment/${r.vendor_payment}" target="_blank" style="color:var(--blue-500);text-decoration:none;" title="${r.vendor || ""}">${r.vendor_payment}</a>`
            : `<span style="color:var(--text-muted);">—</span>`;
        return `<tr>
            <td style="padding:6px 10px;">${idx + 1}</td>
            <td style="padding:6px 10px;"><a href="/app/trip/${r.name}" target="_blank" style="color:var(--blue-500);text-decoration:none;">${trip_ref}</a></td>
            <td style="padding:6px 10px;">${fmt_date(r.trip_date)}</td>
            <td style="padding:6px 10px;">${r.lr_no || ""}</td>
            <td style="padding:6px 10px;">${vehicle}</td>
            <td style="padding:6px 10px;">${route}</td>
            <td style="padding:6px 10px;">${vendor_payment_cell}</td>
            <td style="padding:6px 10px;text-align:right;">${fmt_amt(r.amount)}</td>
        </tr>`;
    }).join("");

    field.$wrapper.html(`
        <div style="overflow:auto;max-height:360px;margin:4px 0;border:1px solid var(--border-color);">
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead>
                    <tr style="background:var(--subtle-fg);color:var(--text-muted);">
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">S.No.</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Trip Ref</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Trip Date</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">LR No</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Vehicle</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Route</th>
                        <th style="padding:6px 10px;text-align:left;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">Vendor Payment</th>
                        <th style="padding:6px 10px;text-align:right;font-weight:600;position:sticky;top:0;background:var(--subtle-fg);">LR Money (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows_html}
                </tbody>
                <tfoot>
                    <tr style="border-top:2px solid var(--border-color);background:var(--subtle-fg);">
                        <td colspan="7" style="padding:6px 10px;font-weight:700;position:sticky;bottom:0;background:var(--subtle-fg);">Total Employee LR Money</td>
                        <td style="padding:6px 10px;text-align:right;font-weight:700;color:var(--green-500);position:sticky;bottom:0;background:var(--subtle-fg);">${fmt_amt(total_amount)}</td>
                    </tr>
                </tfoot>
            </table>
        </div>`);

    const row = find_child_row(frm, "earnings_table", "salary_component", "Employee LR Money");
    if (row) {
        row.amount = total_amount;
        frm.refresh_field("earnings_table");
        calculate_earnings(frm);
    }
}

function set_previous_month(frm) {
    if (!frm.doc.payroll_date) return Promise.resolve();

    let selected_date = frappe.datetime.str_to_obj(frm.doc.payroll_date);

    // Get previous month
    let prev_month_date = frappe.datetime.add_months(selected_date, -1);

    let from_date = frappe.datetime.get_first_day(prev_month_date);
    let to_date = frappe.datetime.get_last_day(prev_month_date);

    return Promise.all([
        frm.set_value('from_date', from_date),
        frm.set_value('to_date', to_date)
    ]);
}
