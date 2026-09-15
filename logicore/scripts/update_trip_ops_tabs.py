import frappe

HTML = """<div id="tms-ops-root" style="width:100%;display:block;">
  <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;margin-bottom:18px;">
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
  <div id="tms-ops-card-wrap" class="tms-ops-card-wrap">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
      <span style="font-size:15px;font-weight:700;color:var(--heading-color,#1f272e);">Trip Operations</span>
      <span id="tms-last-updated" style="font-size:11px;color:#8d99a6;"></span>
    </div>
    <div class="tms-tt-tabs-wrap">
      <div id="tms-tt-tabs" class="tms-tt-tabs" role="tablist" aria-label="Trip Type">
        <button type="button" class="tms-tt-tab is-active" data-type="primary" role="tab" aria-selected="true">Primary</button>
        <button type="button" class="tms-tt-tab" data-type="other" role="tab" aria-selected="false">Other</button>
        <button type="button" class="tms-tt-tab" data-type="secondary_dedicated" role="tab" aria-selected="false">Secondary Dedicated</button>
        <button type="button" class="tms-tt-tab" data-type="secondary_market" role="tab" aria-selected="false">Secondary Market</button>
        <span class="tms-tt-tabs__highlight"></span>
      </div>
    </div>
    <div id="tms-ops-grid" class="tms-ops-grid" style="width:100%;"></div>
  </div>
</div>"""

SCRIPT = """(function () {
    'use strict';

    var CARD_DEFS = {
        pending_pod:              { label:'Pending POD',                    css:'tms-card--pending-pod',        icon:'\\uD83D\\uDCC4' },
        pending_lr_no:            { label:'Pending LR No',                  css:'tms-card--pending-lr',         icon:'\\uD83D\\uDCCB' },
        pending_dispatch:         { label:'Pending Dispatch',               css:'tms-card--pending-dispatch',   icon:'\\uD83D\\uDE9A' },
        pending_arrival:          { label:'Pending Arrival',                css:'tms-card--pending-arrival',    icon:'\\uD83C\\uDFE1' },
        pending_customer_freight: { label:'Pending Customer Freight',       css:'tms-card--pending-cf',         icon:'\\uD83D\\uDCB0' },
        pending_vendor_freight:   { label:'Pending Vendor Freight',         css:'tms-card--pending-vf',         icon:'\\uD83D\\uDE9B' },
        trip_no_pending:          { label:'Trip No To Be Provided',         css:'tms-card--trip-no',            icon:'\\uD83D\\uDD22' },
        trip_to_be_billed:        { label:'Trip To Be Billed',              css:'tms-card--trip-billed',        icon:'\\uD83E\\uDDFE' },
        original_pod_awaited:     { label:'Original POD Awaited',          css:'tms-card--pod-awaited',        icon:'\\uD83D\\uDCE5' },
        original_pod_not_despatched: { label:'Original POD Not Despatched', css:'tms-card--pod-not-despatched', icon:'\\uD83D\\uDCE4' },
        start_end_km_not_filled:  { label:'Start KM and End KM Not Filled', css:'tms-card--km-not-filled',      icon:'\\uD83D\\uDCCD' },
        standard_km_not_filled:   { label:'Standard KM Not Filled',         css:'tms-card--std-km-not-filled',  icon:'\\uD83D\\uDCCF' },
        trip_payment_awaited:     { label:'Trip Payment Awaited',          css:'tms-card--payment-awaited',   icon:'\\uD83D\\uDCB8' },
        arrival_dispatch_blank:   { label:'Arrival/Dispatch Columns Blank', css:'tms-card--blank-cols',         icon:'\\u2B1C' },
        advance_amount_awaited:   { label:'Advance Amount Awaited',        css:'tms-card--advance-awaited',    icon:'\\uD83D\\uDCB5' },
        balance_amount_awaited:   { label:'Balance Amount Awaited',        css:'tms-card--balance-awaited',    icon:'\\u2696\\uFE0F' }
    };

    var CARD_SETS = {
        primary: [
            'pending_pod', 'pending_lr_no', 'pending_dispatch', 'pending_arrival',
            'pending_customer_freight', 'pending_vendor_freight', 'trip_no_pending',
            'trip_to_be_billed', 'trip_payment_awaited', 'original_pod_awaited'
        ],
        secondary_market: [
            'pending_pod'
        ],
        secondary_dedicated: [
            'pending_pod', 'start_end_km_not_filled', 'standard_km_not_filled'
        ],
        other: [
            'arrival_dispatch_blank', 'original_pod_awaited', 'pending_pod',
            'advance_amount_awaited', 'balance_amount_awaited', 'original_pod_not_despatched'
        ]
    };

    var TAB_COLS = { primary: 5, other: 6 };

    function applyGridCols() {
        var cols = TAB_COLS[activeTripType];
        if (cols) {
            grid.setAttribute('data-cols', String(cols));
        } else {
            grid.removeAttribute('data-cols');
        }
    }

    function getActiveCards() {
        return (CARD_SETS[activeTripType] || CARD_SETS.primary).map(function (key) {
            var def = CARD_DEFS[key];
            return { key: key, label: def.label, css: def.css, icon: def.icon };
        });
    }

    var TRIP_TYPE_VALUES = {
        primary: 'PRIMARY',
        other: 'OTHER',
        secondary_dedicated: 'SECONDARY DEDICATED',
        secondary_market: 'SECONDARY MARKET'
    };

    // Readable filter chips for cards whose logic is a plain AND of field conditions
    // (mirrors the server-side conditions in api.py's _trip_operations_card_conditions).
    // Keyed per trip_type since the same card key (e.g. pending_pod) can have different
    // logic on different tabs. Cards not listed for a tab (arrival_dispatch_blank,
    // advance_amount_awaited, balance_amount_awaited) need OR-logic / Customer Receipt
    // Trip aggregation that Frappe's list-view filters can't express — those fall back
    // to an exact server-computed record list instead (see get_trip_operations_records).
    var ROUTE_FILTERS = {
        primary: {
            pending_pod:            [['arrival_date_time','is','set'],['pod_status','in',['POD Not Uploaded','']],['trip_status','!=','Cancel']],
            pending_lr_no:          [['lr_no','is','not set'],['trip_status','!=','Cancel']],
            pending_dispatch:       [['lr_no','is','set'],['reach_date_time','is','set'],['dispatch_date_time','is','not set'],['trip_status','!=','Cancel']],
            pending_arrival:        [['lr_no','is','set'],['dispatch_date_time','is','set'],['arrival_date_time','is','not set'],['trip_status','!=','Cancel']],
            pending_customer_freight: [['customer_freight','<=',0],['trip_status','!=','Cancel']],
            pending_vendor_freight: [['total_vendor_freight','<=',0],['trip_status','!=','Cancel']],
            trip_no_pending:        [['trip_no_not_yet_provided','=',1],['trip_status','!=','Cancel']],
            trip_to_be_billed:      [['release_date_time','is','set'],['bill_nodate','is','not set'],['bill_date','is','not set'],['trip_status','!=','Cancel']],
            trip_payment_awaited:   [['release_date_time','is','set'],['bill_nodate','is','set'],['bill_date','is','set'],['date_bill_credited','is','not set'],['trip_status','!=','Cancel']],
            original_pod_awaited:   [['uploaded_pod_originalduplicate','=','Duplicate'],['pod_status','=','Duplicate POD Uploaded'],['trip_status','!=','Cancel']]
        },
        other: {
            original_pod_awaited:   [['uploaded_pod_originalduplicate','=','Duplicate'],['pod_status','=','Duplicate POD Uploaded'],['trip_status','!=','Cancel']],
            pending_pod:            [['arrival_date_time','is','set'],['pod_status','in',['POD Not Uploaded','']],['trip_status','!=','Cancel']],
            original_pod_not_despatched: [['uploaded_pod_originalduplicate','is','set'],['pod_status','in',['Original POD Uploaded','Duplicate POD Uploaded']],['date_pod_sent_to_customer','is','not set'],['trip_status','!=','Cancel']]
        },
        secondary_dedicated: {
            pending_pod:            [['pod_status','in',['POD Not Uploaded','']],['trip_status','!=','Cancel']],
            start_end_km_not_filled: [['start_km','is','not set'],['end_km','is','not set'],['trip_status','!=','Cancel']],
            standard_km_not_filled: [['standard_km','is','not set'],['trip_status','!=','Cancel']]
        },
        secondary_market: {
            pending_pod:            [['arrival_date_time','is','set'],['pod_status','in',['POD Not Uploaded','']],['trip_status','!=','Cancel']]
        }
    };

    var root        = root_element.getElementById('tms-ops-root');
    if (!root) return;

    var grid        = root_element.getElementById('tms-ops-grid');
    var selCompany  = root_element.getElementById('tms-filter-company');
    var selBranch   = root_element.getElementById('tms-filter-branch');
    var inpFrom     = root_element.getElementById('tms-filter-from');
    var inpTo       = root_element.getElementById('tms-filter-to');
    var btnSearch   = root_element.getElementById('tms-btn-search');
    var btnReset    = root_element.getElementById('tms-btn-reset');
    var lblUpdated  = root_element.getElementById('tms-last-updated');

    var tabsWrap      = root_element.getElementById('tms-tt-tabs');
    var tabsHighlight = tabsWrap ? tabsWrap.querySelector('.tms-tt-tabs__highlight') : null;
    var activeTripType = 'primary';
    var lastData = {};

    var TAB_COLORS = {
        primary: '#6366f1',
        other: '#f59e0b',
        secondary_dedicated: '#8b5cf6',
        secondary_market: '#10b981'
    };

    function positionHighlight(el) {
        if (!tabsHighlight || !el) return;
        tabsHighlight.style.left  = el.offsetLeft + 'px';
        tabsHighlight.style.width = el.offsetWidth + 'px';
        tabsHighlight.style.background = TAB_COLORS[el.dataset.type] || '#fff';
    }

    function initTabs() {
        if (!tabsWrap) return;
        var tabs = Array.prototype.slice.call(tabsWrap.querySelectorAll('.tms-tt-tab'));
        tabs.forEach(function (tab) {
            tab.addEventListener('click', function () {
                if (tab.classList.contains('is-active')) return;
                tabs.forEach(function (t) { t.classList.remove('is-active'); t.setAttribute('aria-selected', 'false'); });
                tab.classList.add('is-active');
                tab.setAttribute('aria-selected', 'true');
                activeTripType = tab.dataset.type;
                positionHighlight(tab);
                renderSkeleton();
                fetchCounts();
            });
        });
        var activeTab = tabsWrap.querySelector('.tms-tt-tab.is-active');
        requestAnimationFrame(function () { positionHighlight(activeTab); });
        window.addEventListener('resize', function () {
            positionHighlight(tabsWrap.querySelector('.tms-tt-tab.is-active'));
        });
    }

    function dispatchFilterEvent() {
        window.dispatchEvent(new CustomEvent('tms-filter-changed', {
            detail: {
                from_date: inpFrom.value || '',
                to_date:   inpTo.value   || '',
                company:   selCompany.value || '',
                branch:    selBranch.value  || '',
                trip_type: activeTripType || ''
            }
        }));
    }

    function renderSkeleton() {
        grid.innerHTML = '';
        applyGridCols();
        getActiveCards().forEach(function (c) {
            var el = document.createElement('div');
            el.className = 'tms-ops-card skeleton ' + c.css;
            el.innerHTML = '<span class="tms-card-icon">' + c.icon + '</span><span class="tms-card-number">&nbsp;</span><span class="tms-card-label">&nbsp;</span>';
            grid.appendChild(el);
        });
    }

    function renderCards(data) {
        grid.innerHTML = '';
        applyGridCols();
        getActiveCards().forEach(function (c) {
            var known = data && data[c.key] !== undefined;
            var display = parseInt(data && data[c.key]) || 0;
            var el = document.createElement('div');
            el.className = 'tms-ops-card ' + c.css + (known ? '' : ' tms-ops-card--pending-logic');
            el.setAttribute('role', 'button');
            el.setAttribute('tabindex', '0');
            el.innerHTML =
                '<span class="tms-card-icon">' + c.icon + '</span>' +
                '<span class="tms-card-number">' + display + '</span>' +
                '<span class="tms-card-label">' + frappe.utils.escape_html(c.label) + '</span>';
            el.addEventListener('click', function () {
                if (!known || el.classList.contains('is-loading')) return;

                function baseFilters() {
                    var f = {};
                    var co = selCompany.value, br = selBranch.value;
                    var fd = inpFrom.value,    td = inpTo.value;
                    if (co) f['company'] = co;
                    if (br) f['branch']  = br;
                    if (fd && td) {
                        f['tcntrip_date'] = ['between', [fd, td]];
                    } else if (fd) {
                        f['tcntrip_date'] = ['>=', fd];
                    } else if (td) {
                        f['tcntrip_date'] = ['<=', td];
                    }
                    if (TRIP_TYPE_VALUES[activeTripType]) {
                        f['trip_type'] = TRIP_TYPE_VALUES[activeTripType];
                    }
                    return f;
                }

                var readableFilters = (ROUTE_FILTERS[activeTripType] || {})[c.key];
                if (readableFilters) {
                    // Plain AND-of-fields logic — show the real field filters, same as before.
                    var route_filters = baseFilters();
                    readableFilters.forEach(function (flt) {
                        route_filters[flt[0]] = [flt[1], flt[2]];
                    });
                    frappe.route_options = route_filters;
                    frappe.set_route('List', 'Trip');
                    return;
                }

                // OR-logic / Customer Receipt Trip aggregation — no simple field filter
                // can represent this, so fetch the exact matching Trip names instead.
                el.classList.add('is-loading');
                frappe.call({
                    method: 'logicore.logicore.api.get_trip_operations_records',
                    args: {
                        card_key: c.key,
                        company: selCompany.value || '',
                        branch: selBranch.value || '',
                        from_date: inpFrom.value || '',
                        to_date: inpTo.value || '',
                        trip_type: activeTripType || ''
                    },
                    callback: function (r) {
                        el.classList.remove('is-loading');
                        var names = (r && r.message) || [];
                        var route_filters = baseFilters();
                        route_filters['name'] = ['in', names.length ? names : ['__tms_no_match__']];
                        frappe.route_options = route_filters;
                        frappe.set_route('List', 'Trip');
                    },
                    error: function () {
                        el.classList.remove('is-loading');
                    }
                });
            });
            grid.appendChild(el);
        });
        if (lblUpdated) lblUpdated.textContent = 'Updated ' + new Date().toLocaleTimeString();
    }

    function fetchCounts() {
        root_element.querySelectorAll('.tms-card-number').forEach(function (el) { el.classList.add('refreshing'); });
        btnSearch.disabled = true;
        btnSearch.textContent = 'Searching...';
        dispatchFilterEvent();
        frappe.call({
            method: 'logicore.logicore.api.get_trip_operations_summary',
            args: { company: selCompany.value || '', branch: selBranch.value || '', from_date: inpFrom.value || '', to_date: inpTo.value || '', trip_type: activeTripType || '' },
            callback: function (r) {
                btnSearch.disabled = false;
                btnSearch.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Search';
                lastData = r && r.message ? r.message : {};
                renderCards(lastData);
            },
            error: function () {
                btnSearch.disabled = false;
                btnSearch.textContent = 'Search';
                lastData = {};
                renderCards(lastData);
            }
        });
    }

    function populateFilters() {
        frappe.call({
            method: 'logicore.logicore.api.get_trip_filter_options',
            callback: function (r) {
                if (!r || !r.message) { fetchCounts(); return; }
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
                fetchCounts();
            }
        });
    }

    btnSearch.addEventListener('click', fetchCounts);
    btnReset.addEventListener('click', function () {
        selCompany.value = ''; selBranch.value = ''; inpFrom.value = ''; inpTo.value = '';
        fetchCounts();
    });
    [inpFrom, inpTo].forEach(function (i) { i.addEventListener('keydown', function (e) { if (e.key === 'Enter') fetchCounts(); }); });

    var _now = new Date(), _y = _now.getFullYear(), _m = _now.getMonth();
    function _fmt(d) { return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); }
    inpFrom.value = _fmt(new Date(_y, _m, 1));
    inpTo.value   = _fmt(new Date(_y, _m + 1, 0));

    renderSkeleton();
    initTabs();
    populateFilters();

}());"""

STYLE = """:host{display:block!important;width:100%!important;box-sizing:border-box!important;}*{box-sizing:border-box;}#tms-ops-card-wrap{position:relative;overflow:hidden;border-radius:16px;padding:20px clamp(14px,3vw,24px) 24px;border:3px solid transparent;background:linear-gradient(var(--card-bg,#fff),var(--card-bg,#fff)) padding-box,linear-gradient(120deg,#6366f1,#22c55e,#f59e0b,#ef4444,#3b82f6) border-box;box-shadow:0 4px 24px rgba(0,0,0,.06);}:host-context([data-theme="dark"]) #tms-ops-card-wrap{background:linear-gradient(rgba(30,32,38,.95),rgba(30,32,38,.95)) padding-box,linear-gradient(120deg,#6366f1,#22c55e,#f59e0b,#ef4444,#3b82f6) border-box;box-shadow:0 4px 24px rgba(0,0,0,.4);}@media(max-width:600px){#tms-ops-card-wrap{border-radius:12px;border-width:2px;padding:16px 14px 18px;}}.tms-ops-grid{display:flex;flex-wrap:wrap;gap:10px;width:100%;box-sizing:border-box;min-height:170px;align-content:flex-start;}.tms-ops-card{box-sizing:border-box;border-radius:10px;padding:14px 14px 12px;color:#3d3d3d;position:relative;overflow:hidden;cursor:pointer;transition:transform .2s ease,box-shadow .2s ease;box-shadow:0 2px 10px rgba(0,0,0,.08);display:block;min-height:80px;user-select:none;flex:1 1 180px;max-width:230px;}.tms-ops-grid[data-cols="5"]>.tms-ops-card{flex:0 0 calc(20% - 8px);max-width:calc(20% - 8px);}.tms-ops-grid[data-cols="6"]>.tms-ops-card{flex:0 0 calc(16.6667% - 8.34px);max-width:calc(16.6667% - 8.34px);}@media(max-width:900px){.tms-ops-grid[data-cols]>.tms-ops-card{flex:0 0 calc(33.333% - 7px);max-width:calc(33.333% - 7px);}}@media(max-width:600px){.tms-ops-grid[data-cols]>.tms-ops-card{flex:0 0 calc(50% - 5px);max-width:calc(50% - 5px);}}.tms-ops-card::before{content:'';position:absolute;top:-20px;right:-20px;width:80px;height:80px;border-radius:50%;background:rgba(0,0,0,.05);pointer-events:none;}.tms-ops-card::after{content:'';position:absolute;bottom:-15px;left:-15px;width:60px;height:60px;border-radius:50%;background:rgba(0,0,0,.03);pointer-events:none;}.tms-ops-card:hover{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.13);color:#3d3d3d;}.tms-ops-card:active{transform:translateY(-1px);}.tms-ops-card--pending-logic{cursor:default;opacity:.72;}.tms-ops-card--pending-logic:hover{transform:none;box-shadow:0 2px 10px rgba(0,0,0,.08);}.tms-ops-card.is-loading{cursor:wait;opacity:.6;}.tms-card-number{font-size:28px;font-weight:800;line-height:1;letter-spacing:-1px;margin-bottom:4px;display:block;text-shadow:none;transition:opacity .25s ease;}.tms-card-number.refreshing{opacity:.35;}.tms-card-label{font-size:10px;font-weight:700;opacity:.75;line-height:1.3;text-transform:uppercase;letter-spacing:.3px;display:block;}.tms-card-icon{position:absolute;top:10px;right:12px;font-size:20px;opacity:.2;line-height:1;pointer-events:none;}.tms-ops-card.skeleton .tms-card-number,.tms-ops-card.skeleton .tms-card-label{background:rgba(0,0,0,.1);border-radius:4px;color:transparent;animation:tms-pulse 1.4s ease-in-out infinite;}.tms-ops-card.skeleton .tms-card-number{width:50px;height:28px;display:inline-block;}.tms-ops-card.skeleton .tms-card-label{width:90%;height:12px;display:block;}@keyframes tms-pulse{0%,100%{opacity:1;}50%{opacity:.4;}}.tms-card--pending-pod{background:linear-gradient(135deg,#ffc8d8 0%,#ffe0ec 100%);}.tms-card--pending-lr{background:linear-gradient(135deg,#b3d9f7 0%,#d6eeff 100%);}.tms-card--pending-dispatch{background:linear-gradient(135deg,#a8dbc5 0%,#c8eed9 100%);}.tms-card--pending-arrival{background:linear-gradient(135deg,#ffd3b6 0%,#ffe8d5 100%);}.tms-card--pending-cf{background:linear-gradient(135deg,#b8e8ca 0%,#d4f5e2 100%);}.tms-card--pending-vf{background:linear-gradient(135deg,#aed6e8 0%,#cce8f5 100%);}.tms-card--trip-no{background:linear-gradient(135deg,#f5dda8 0%,#faecc5 100%);}.tms-card--trip-billed{background:linear-gradient(135deg,#c9b8f5 0%,#e2d6fa 100%);}.tms-card--pod-awaited{background:linear-gradient(135deg,#9fe0d8 0%,#cdf2ec 100%);}.tms-card--pod-not-despatched{background:linear-gradient(135deg,#ffcb9a 0%,#ffe4c4 100%);}.tms-card--km-not-filled{background:linear-gradient(135deg,#fff0a8 0%,#fff8d4 100%);}.tms-card--std-km-not-filled{background:linear-gradient(135deg,#d4f0a8 0%,#eaf8d4 100%);}.tms-card--payment-awaited{background:linear-gradient(135deg,#a8c5f0 0%,#d4e4fa 100%);}.tms-card--blank-cols{background:linear-gradient(135deg,#d9dde3 0%,#eef0f3 100%);}.tms-card--advance-awaited{background:linear-gradient(135deg,#a8ddb5 0%,#d3f0da 100%);}.tms-card--balance-awaited{background:linear-gradient(135deg,#f7b8c4 0%,#fbdae1 100%);}.tms-tt-tabs-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;margin-bottom:16px;scrollbar-width:none;}.tms-tt-tabs-wrap::-webkit-scrollbar{display:none;}.tms-tt-tabs{position:relative;display:inline-flex;gap:2px;padding:4px;background:var(--subtle-accent,#eef1f5);border-radius:12px;min-width:max-content;}.tms-tt-tab{position:relative;z-index:1;border:none;background:transparent;cursor:pointer;padding:8px 18px 8px 15px;font-size:12px;font-weight:700;letter-spacing:.2px;text-transform:uppercase;color:var(--text-muted,#6b7280);border-radius:9px;white-space:nowrap;transition:color .25s ease;display:inline-flex;align-items:center;gap:7px;}.tms-tt-tab::before{content:'';display:inline-block;width:7px;height:7px;border-radius:50%;background:currentColor;opacity:.55;flex:0 0 auto;transition:background-color .25s ease,opacity .25s ease;}.tms-tt-tab[data-type="primary"]::before{background:#6366f1;opacity:1;}.tms-tt-tab[data-type="other"]::before{background:#f59e0b;opacity:1;}.tms-tt-tab[data-type="secondary_dedicated"]::before{background:#8b5cf6;opacity:1;}.tms-tt-tab[data-type="secondary_market"]::before{background:#10b981;opacity:1;}.tms-tt-tab.is-active{color:#fff;}.tms-tt-tab.is-active::before{background:rgba(255,255,255,.9)!important;}.tms-tt-tab:hover:not(.is-active){color:var(--heading-color,#1f272e);}.tms-tt-tab:focus-visible{outline:2px solid #2563eb;outline-offset:2px;}.tms-tt-tabs__highlight{position:absolute;top:4px;bottom:4px;left:4px;width:0;border-radius:9px;background:var(--card-bg,#fff);box-shadow:0 2px 10px rgba(0,0,0,.18);transition:left .28s cubic-bezier(.4,0,.2,1),width .28s cubic-bezier(.4,0,.2,1),background-color .25s ease;z-index:0;}:host-context([data-theme="dark"]) .tms-tt-tabs{background:rgba(255,255,255,.06);}:host-context([data-theme="dark"]) .tms-tt-tab:hover:not(.is-active){color:#fff;}@media(max-width:600px){.tms-tt-tab{padding:7px 12px 7px 10px;font-size:11px;}}"""


def run():
    doc = frappe.get_doc("Custom HTML Block", "TMS Trip Operations")
    doc.html = HTML
    doc.script = SCRIPT
    doc.style = STYLE
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("Updated TMS Trip Operations custom html block with per-tab card sets")
