// frappe.ui.form.on('Vehicle', {
//     refresh: function(frm) {
//         // Set default company only on new entries
//         if (frm.is_new() && !frm.doc.company) {
//             let default_company = frappe.defaults.get_user_default("Company") || 
//                                   frappe.defaults.get_default("company");
//             if (default_company) {
//                 frm.set_value('company', default_company);
//             }
//         }
//     },

//     company: function(frm) {
//         console.log("Company changed to: " + frm.doc.company);
//         set_vendor_from_company(frm);
//     },

//     custom_market: function(frm) {
//         if (frm.doc.custom_market) {
//             console.log("Market checked: Clearing vendor");
//             frm.set_value('custom_vendor', '');
//         } else {
//             console.log("Market unchecked: Fetching vendor");
//             set_vendor_from_company(frm);
//         }
//     }
// });

// function set_vendor_from_company(frm) {
//     // 1. If market is checked, do not auto-fill vendor
//     if (frm.doc.custom_market) return;

//     let company_name = frm.doc.company;
//     if (!company_name) {
//         frm.set_value('custom_vendor', '');
//         return;
//     }

//     // 2. Fetch Supplier
//     // We look for a Supplier whose 'supplier_name' matches the Company link name
//     frappe.call({
//         method: 'frappe.client.get_value',
//         args: {
//             doctype: 'Supplier',
//             filters: {
//                 'supplier_name': company_name,
//                 'supplier_group': 'Vendor' // Matches your Link Filter
//             },
//             fieldname: 'name'
//         },
//         callback: function(r) {
//             if (r.message && r.message.name) {
//                 console.log("Match found: " + r.message.name);
//                 frm.set_value('custom_vendor', r.message.name);
//             } else {
//                 console.log("No exact match found for Supplier Group 'Vendor'");
//                 // Fallback: Try searching for any supplier matching the name 
//                 // regardless of group to see if that's the issue
//                 check_supplier_existence(frm, company_name);
//             }
//         }
//     });
// }

// function check_supplier_existence(frm, company_name) {
//     frappe.db.get_value('Supplier', {'supplier_name': company_name}, 'supplier_group')
//         .then(r => {
//             if (r.message && r.message.supplier_group !== 'Vendor') {
//                 console.warn(`Supplier "${company_name}" exists but is in group "${r.message.supplier_group}", not "Vendor".`);
//             }
//             frm.set_value('custom_vendor', '');
//         });
// }

frappe.ui.form.on('Vehicle', {
    refresh: function(frm) {
        // Set default company only on new entries
        if (frm.is_new() && !frm.doc.company) {
            let default_company = frappe.defaults.get_user_default("Company") || 
                                  frappe.defaults.get_default("company");
            if (default_company) {
                frm.set_value('company', default_company);
            }
        }

        setTimeout(() => {
            frm.set_df_property('last_odometer', 'read_only', 0);
            frm.set_df_property('last_odometer', 'set_only_once', 0);
            frm.toggle_enable('last_odometer', true);
            frm.refresh_field('last_odometer');
        }, 200);

        // Force last_odometer editable — core ERPNext has set_only_once=1 which locks it after first save
        // frm.set_df_property('last_odometer', 'read_only', 0);
        // frm.set_df_property('last_odometer', 'set_only_once', 0);
        // frm.refresh_field('last_odometer');
    },

    company: function(frm) {
        console.log("Company changed to: " + frm.doc.company);
        set_vendor_from_company(frm);
    },

    custom_market: function(frm) {
        if (frm.doc.custom_market) {
            console.log("Market checked: Clearing vendor");
            frm.set_value('custom_vendor', '');
        } else {
            console.log("Market unchecked: Fetching vendor");
            set_vendor_from_company(frm);
        }
    }
});

function set_vendor_from_company(frm) {
    if (frm.doc.custom_market) return;

    let company_name = frm.doc.company;
    if (!company_name) {
        frm.set_value('custom_vendor', '');
        return;
    }

    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Supplier',
            filters: {
                'supplier_name': company_name,
                'supplier_group': 'Vendor'
            },
            fieldname: 'name'
        },
        callback: function(r) {
            if (r.message && r.message.name) {
                console.log("Match found: " + r.message.name);
                frm.set_value('custom_vendor', r.message.name);
            } else {
                console.log("No exact match found for Supplier Group 'Vendor'");
                check_supplier_existence(frm, company_name);
            }
        }
    });
}

function check_supplier_existence(frm, company_name) {
    frappe.db.get_value('Supplier', {'supplier_name': company_name}, 'supplier_group')
        .then(r => {
            if (r.message && r.message.supplier_group !== 'Vendor') {
                console.warn(`Supplier "${company_name}" exists but is in group "${r.message.supplier_group}", not "Vendor".`);
            }
            frm.set_value('custom_vendor', '');
        });
}