import json

import frappe

HTML = """<div id="tms-filter-root" style="width:100%;display:block;">
  <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;">
    <div style="display:flex;flex-direction:column;gap:4px;flex:1 1 160px;min-width:130px;">
      <label style="font-size:11px;font-weight:600;margin-bottom:0;">Company</label>
      <select id="tms-filter-company" class="form-control input-sm" style="height:34px;"><option value="">All Companies</option></select>
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;flex:1 1 160px;min-width:130px;">
      <label style="font-size:11px;font-weight:600;margin-bottom:0;">Branch</label>
      <select id="tms-filter-branch" class="form-control input-sm" style="height:34px;"><option value="">All Branches</option></select>
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;flex:1 1 140px;min-width:120px;">
      <label style="font-size:11px;font-weight:600;margin-bottom:0;">From Date</label>
      <input type="date" id="tms-filter-from" class="form-control input-sm" style="height:34px;" />
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;flex:1 1 140px;min-width:120px;">
      <label style="font-size:11px;font-weight:600;margin-bottom:0;">To Date</label>
      <input type="date" id="tms-filter-to" class="form-control input-sm" style="height:34px;" />
    </div>
    <div style="display:flex;gap:6px;align-items:flex-end;padding-bottom:1px;">
      <button id="tms-btn-search" class="btn btn-primary btn-sm" style="height:34px;padding:0 16px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-right:4px;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>Search
      </button>
      <button id="tms-btn-reset" class="btn btn-default btn-sm" style="height:34px;padding:0 14px;">Reset</button>
    </div>
  </div>
</div>"""

SCRIPT = """(function () {
    'use strict';

    var root = root_element.getElementById('tms-filter-root');
    if (!root) return;

    var selCompany = root_element.getElementById('tms-filter-company');
    var selBranch  = root_element.getElementById('tms-filter-branch');
    var inpFrom    = root_element.getElementById('tms-filter-from');
    var inpTo      = root_element.getElementById('tms-filter-to');
    var btnSearch  = root_element.getElementById('tms-btn-search');
    var btnReset   = root_element.getElementById('tms-btn-reset');

    function _fmt(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }

    function dispatchFilterEvent() {
        window.dispatchEvent(new CustomEvent('tms-filter-changed', {
            detail: {
                from_date: inpFrom.value || '',
                to_date:   inpTo.value   || '',
                company:   selCompany.value || '',
                branch:    selBranch.value  || ''
            }
        }));
    }

    function populateFilters() {
        frappe.call({
            method: 'logicore.logicore.api.get_trip_filter_options',
            callback: function (r) {
                if (r && r.message) {
                    (r.message.companies || []).forEach(function (c) {
                        var o = document.createElement('option');
                        o.value = c.value; o.textContent = c.label;
                        selCompany.appendChild(o);
                    });
                    (r.message.branches || []).forEach(function (b) {
                        var o = document.createElement('option');
                        o.value = b.value; o.textContent = b.label;
                        selBranch.appendChild(o);
                    });
                    var def = frappe.defaults.get_user_default('company') || frappe.defaults.get_default('company') || '';
                    if (def) selCompany.value = def;
                }
                dispatchFilterEvent();
            }
        });
    }

    btnSearch.addEventListener('click', dispatchFilterEvent);
    btnReset.addEventListener('click', function () {
        selCompany.value = ''; selBranch.value = ''; inpFrom.value = ''; inpTo.value = '';
        dispatchFilterEvent();
    });
    [inpFrom, inpTo].forEach(function (i) {
        i.addEventListener('keydown', function (e) { if (e.key === 'Enter') dispatchFilterEvent(); });
    });

    var _now = new Date(), _y = _now.getFullYear(), _m = _now.getMonth();
    inpFrom.value = _fmt(new Date(_y, _m, 1));
    inpTo.value   = _fmt(new Date(_y, _m + 1, 0));

    populateFilters();

}());"""

STYLE = ":host{display:block!important;width:100%!important;box-sizing:border-box!important;}*{box-sizing:border-box;}"


def run():
	if not frappe.db.exists("Custom HTML Block", "TMS Filter Bar"):
		doc = frappe.new_doc("Custom HTML Block")
		doc.name = "TMS Filter Bar"
		doc.private = 0
		doc.html = HTML
		doc.script = SCRIPT
		doc.style = STYLE
		doc.insert(ignore_permissions=True)
		print("Created Custom HTML Block: TMS Filter Bar")
	else:
		doc = frappe.get_doc("Custom HTML Block", "TMS Filter Bar")
		doc.html = HTML
		doc.script = SCRIPT
		doc.style = STYLE
		doc.save(ignore_permissions=True)
		print("Updated Custom HTML Block: TMS Filter Bar")

	ws = frappe.get_doc("Workspace", "LogiCore")
	content = json.loads(ws.content)
	content = [i for i in content if i.get("data", {}).get("custom_block_name") != "TMS Filter Bar"]
	content.insert(
		0,
		{
			"id": "cb_tms_filter_bar",
			"type": "custom_block",
			"data": {"custom_block_name": "TMS Filter Bar", "col": 12},
		},
	)
	ws.content = json.dumps(content)

	if not any(r.custom_block_name == "TMS Filter Bar" for r in ws.custom_blocks):
		ws.append("custom_blocks", {"custom_block_name": "TMS Filter Bar"})

	# Workspace has pre-existing number_card rows pointing at missing HR cards;
	# link validation would block an unrelated content reorder.
	ws.flags.ignore_links = True
	ws.save(ignore_permissions=True)
	print("Reordered LogiCore workspace: TMS Filter Bar is now first")

	frappe.db.commit()
