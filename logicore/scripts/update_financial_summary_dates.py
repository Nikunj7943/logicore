import frappe

SCRIPT = "(function() {\n    'use strict';\n    var els = {\n        vf:    root_element.getElementById('tfs-vf'),\n        vp:    root_element.getElementById('tfs-vp'),\n        vpend: root_element.getElementById('tfs-vpend'),\n        inv:   root_element.getElementById('tfs-inv'),\n        cr:    root_element.getElementById('tfs-cr'),\n        co:    root_element.getElementById('tfs-co'),\n    };\n\n    function fmt(v) {\n        var n = parseFloat(v) || 0;\n        return '₹ ' + n.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });\n    }\n\n    function fetchData(company, branch, fromDate, toDate) {\n        frappe.call({\n            method: 'logicore.logicore.api.get_financial_summary',\n            args: { company: company || '', branch: branch || '', from_date: fromDate || '', to_date: toDate || '' },\n            callback: function(r) {\n                if (r && r.message) {\n                    var m = r.message;\n                    els.vf.textContent    = fmt(m.total_vendor_freight);\n                    els.vp.textContent    = fmt(m.total_vendor_paid);\n                    els.vpend.textContent = fmt(m.total_vendor_pending);\n                    els.inv.textContent   = fmt(m.total_invoice);\n                    els.cr.textContent    = fmt(m.total_customer_received);\n                    els.co.textContent    = fmt(m.total_customer_outstanding);\n                }\n            }\n        });\n    }\n\n    window.addEventListener('tms-filter-changed', function(e) {\n        var d = (e && e.detail) || {};\n        fetchData(d.company || '', d.branch || '', d.from_date || '', d.to_date || '');\n    });\n}());"


def run():
	doc = frappe.get_doc("Custom HTML Block", 'TMS Financial Summary')
	doc.script = SCRIPT
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	print('Updated TMS Financial Summary block')
