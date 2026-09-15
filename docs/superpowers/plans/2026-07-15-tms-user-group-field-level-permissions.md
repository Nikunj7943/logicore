# TMS User Group — Field-Level Permission (Hidden / Read-Only) Feature Plan

**Status: PLAN ONLY — implementation NOT started. Do not execute until explicitly asked.**

## Context

Abhi TMS User Group sirf **doctype-level** permission manage karta hai (Read/Write/Create/Delete etc. — poore doctype ke liye). Aapne jo maanga hai wo ek level deeper hai: har managed doctype ke andar jo fields already form pe visible hain, unme se **field-by-field** control chahiye — kis field ko kis user group ke liye **Hidden** karna hai, kis field ko **Read Only** karna hai. Ye bilkul Frappe/ERPNext ke standard **Permission Level (permlevel)** field-permission feature jaisa hona chahiye (jo Role Permission Manager se hota hai), bas driven TMS User Group screen se ho, na ki Frappe ke core Role Permission Manager se.

**Feasibility verdict: Haan, ye ban sakta hai** — aur achi baat ye hai ki isko banane ke liye naya "hide/show" reimplementation nahi karna padega. Frappe ke andar already ek real, server-enforced field-level permission mechanism (`permlevel` + `Custom DocPerm`) maujood hai jo:
- Client-side field ko hide/read-only karta hai (form, list view columns, report view sab jagah)
- **Server-side bhi enforce karta hai** — agar koi user browser se bhi field ka value bhejne ki koshish kare jiska usko write-access nahi hai, Frappe save ke time silently us value ko discard/reset kar deta hai (`reset_values_if_no_permlevel_access`)
- Field ka read-access na ho to wo field poore document response se hi remove ho jaata hai (sirf CSS se chhupta nahi) — ye `BaseDocument.apply_fieldlevel_read_permissions()` karta hai

Isliye recommend approach ye hai ki hum **isi native mechanism ko reuse karein**, bas TMS User Group ke UI se drive karein — koi parallel/custom hide-logic banake server-side security duplicate nahi karni.

**Confirm: Existing doctype-level permission system ko koi haath nahi lagega.** Aaj jo `permissions` child table (`TMS User Group Permission`) hai, aur jo uska sync (`_bulk_sync_custom_docperms`, hamesha permlevel 0 pe) hai — wo **bilkul waisa hi rahega, ek line bhi change nahi hogi**. Ye naya field-permission feature ek **alag, parallel layer** hai jo sirf naye permlevel (>0) rows pe kaam karta hai. Purana doctype-level Read/Write/Create/Delete matrix pehle jaisa hi chalta rahega.

Codebase mein already ek similar-shape precedent hai: `Trip Settings` doctype mein per-Trip-Type field visibility (`Trip Field Setting` child table + `get_field_config()` + `frm.set_df_property()` loop) — lekin wo sirf **client-side cosmetic** hai (Trip Type security boundary nahi hai). Field permission ek security feature hai, isliye us halka pattern ko copy nahi karenge — uski jagah real permlevel mechanism use karenge jisme server enforcement bhi hai.

---

## High-Level Design

### ⚠️ REVISED (user feedback ke baad): Ab har field ko apna ALAG/UNIQUE permlevel milega — koi shared bucket nahi

**Pehle wala design** (permlevel `1` = Hidden ka ek hi shared bucket, `2` = Read Only ka ek hi shared bucket, poore doctype ke saare fields ke beech) mein ek real problem thi: agar Group A ne field `customer` ko Hidden kiya aur baad mein Group B ne kisi DUSRE field `vehicle` ko Hidden kiya, to dono fields ek hi permlevel bucket mein aa jaate, aur **Group A ko `vehicle` bhi automatically hidden dikhta** — bawajood iske ki Group A ne kabhi `vehicle` ko touch hi nahi kiya tha. Ye exactly wo "error" hai jo user ne flag kiya.

**Fix: ab har field ko uska APNA, ALAG, UNIQUE permlevel milega** — koi do fields kabhi permlevel share nahi karenge. Isse:
- Ek field ko Hidden/Read-Only karna **sirf usi field ko** affect karega — koi doosra field kabhi accidentally affect nahi hoga.
- Har group independently, poori tarah se, har field ko apni marzi se control kar sakta hai — bina kisi cross-field ya cross-group interference ke.
- **"Error" wala scenario ab structurally hi possible nahi hai.**

### Step 1 — Har field ko unique permlevel assign karna

Frappe mein `permlevel` field-level property hai (`DocField.permlevel`, default 0). Assignment `make_property_setter(doctype, fieldname, "permlevel", value, "Int")` se hota hai — yehi tareeka Frappe ka apna "Customize Form" screen use karta hai. Har field ko ek **naya, kabhi-reuse-na-hone-wala** integer milega (koi do fields kabhi same number share nahi karenge, chahe alag-alag doctype mein ho — simplicity ke liye ek hi global counter use karenge, kyunki Custom DocPerm grant `(doctype, role, permlevel)` pe based hai, isliye alag doctype mein number repeat hone se bhi koi conflict nahi hota, lekin global unique rakhna implementation simple banata hai).

**Koi naya `patches/` file nahi banega** — sab kuch `install.py` ke `after_migrate()` mein existing idempotent-helper convention se hoga (jaise already maujood `_restore_managed_doctype_permissions()`, `_sync_baseline_group_permissions_all()`).

Assignment do tareeke se hoga:
1. **Already-read-only fields (upfront, install.py mein):** Jo field doctype meta mein aaj se hi `read_only=1` hai (poori list "Already Read-Only Fields" section mein hai), sabko `_assign_field_permlevels_and_backfill()` function (naya, `install.py` mein) turant apna **alag-alag unique permlevel** de dega — **har field independently controllable hoga, koi shared bucket nahi.**
2. **Normal fields (lazy, jab pehli baar zaroorat pade):** Jo field abhi tak kisi ne customize nahi ki, wo permlevel `0` pe hi rehta hai (bilkul aaj jaisa, koi Custom DocPerm row bhi nahi banti). Jis waqt koi admin PEHLI BAAR us field ko (kisi bhi ek TMS User Group ke liye) Hidden ya Read Only banaata hai, usi waqt `save_field_permissions` whitelisted endpoint us field ko ek **naya unique permlevel** Property Setter se assign karega — aur saath hi turant backfill bhi karega (Step 2).

### Step 2 — Backfill grant (jab bhi koi field pehli baar permlevel 0 se apne unique permlevel pe jaati hai)

Jaise hi kisi field ka permlevel 0 se kisi N pe jaata hai, us field ko **koi bhi role dekh nahi paayega** jab tak us role ko us specific permlevel N pe explicit `Custom DocPerm` row na mile. Isliye jis bhi waqt (chahe upfront install.py mein, ya lazily `save_field_permissions` ke andar) koi field apna permlevel paaye, **usi pass mein**, har currently-active TMS User Group + `Administrator` + `System Manager` ke liye **us field ke us specific permlevel** pe Custom DocPerm row bhi insert hogi (jo group abhi ye field customize nahi kar rahi) — normal fields ke liye `{read:1, write:1}`, already-read-only fields ke liye `{read:1, write:0}`. Matlab "aaj jo visible hai wo migrate/save ke baad bhi visible rahega," jab tak koi admin explicitly us field ko Hidden na kare — aur ye backfill **sirf usi ek field ko** affect karti hai, kisi aur field ko nahi (kyunki permlevel ab unique hai).

### Step 3 — Naya data storage: `TMS User Group Field Permission` child table

Naya child doctype (existing `TMS User Group Permission` jaisa hi pattern):
- `document_type`, `fieldname`, `label`, `fieldtype` (cached display info)
- `permlevel` (read-only, us field ka apna assign hua unique permlevel yaad rakhne ke liye — internal plumbing, user ko UI mein nahi dikhta, lekin sync ke liye zaroori hai)
- `field_state` — **2 mutually-exclusive states**: `1 = Hidden`, `2 = Read Only`. Koi teesra "Default" value store nahi hoga — agar kisi field ke liye row hi nahi hai to matlab wo Default/untouched hai (missing row = default, jaisa `permissions` table ka style hai).

TMS User Group form mein ek naya hidden `field_permissions` Table field (existing `permissions` field jaisa) — ye purane doctype-level `permissions` table se conceptually alag hai (wo permlevel 0 control karta hai, ye har field ke apne unique permlevel pe), isliye dono ka data collide nahi karega.

### Step 4 — UI: Doctype naam → Hyperlink → Popup Dialog

Existing `render_matrix()` (jo permission matrix table banata hai, `tms_user_group.js`) mein har doctype row ka naam ab ek `<a>` hyperlink banega. Click karne pe existing `show_internal_permission_dialog`-jaisa `frappe.ui.Dialog({size: "extra-large", ...})` open hoga (responsive, existing pattern reuse karke — koi naya external UI library nahi, existing vanilla-JS + inline-style approach hi follow hoga):

- Dialog us doctype ke saare **currently visible fields** list karega (jo aaj form pe dikh rahe hain — `hidden=1` waale aur layout fields jaise Section Break/Column Break/Tab Break skip honge) — label ke saath.
- **Sirf 2 toggle honge per field: `Hidden` aur `Read Only`** — koi teesra "Default" button/pill nahi dikhega. Dono toggle mutually exclusive hain (Hidden ON karne se Read Only auto-OFF, aur vice versa) — dono OFF = default/untouched (aaj jaisa hi).
- **Jo field doctype mein already `read_only=1` hai, uske liye `Read Only` toggle pre-selected (ON) khulega**, aur `Hidden` toggle se OFF karke "editable" nahi bana sakte — us row mein sirf `Hidden` toggle hi actionable hai (Read Only ko manually OFF karne ka option nahi, kyunki field structurally hi kabhi editable nahi ho sakta).
- **Koi "ye field share karega baaki fields ke saath" wala warning ab nahi chahiye** (pehle wale shared-bucket design mein zaroori tha) — kyunki ab har field independent hai, ek field ko Hidden karna kisi aur field ko affect nahi karta.
- "Save" dabane pe naya whitelisted endpoint `save_field_permissions(group_name, doctype, rows)` call hoga jo `field_permissions` child table update karke **normal `doc.save()`** se chalega (audit/version-log trail preserve karne ke liye — bypass-save pattern jo `navigation_visibility_json` use karta hai, is security-sensitive feature ke liye avoid karenge).

### Step 5 — Save hone pe real Custom DocPerm sync

Naya sync function `_sync_field_permlevel_custom_docperms(role, field_permission_rows)` (`_bulk_sync_custom_docperms` jaisa hi shape) — TMS User Group ke `on_update()` mein chalega. **Ab koi bucket-grouping ya "most restrictive wins" rule ki zaroorat nahi** (wo sirf shared-permlevel design mein zaroori thi) — seedha, straightforward per-field logic:
1. Har `field_permissions` row ke liye, us field ka apna unique permlevel resolve karo (row ke `permlevel` column se, ya Property Setter lookup se confirm karo).
2. `field_state = 1` (Hidden) → us field ke apne permlevel pe, us group ke liye Custom DocPerm row **delete** (missing row = deny/hidden, Frappe ka native semantics) — **sirf isi field ko affect karta hai.**
3. `field_state = 2` (Read Only) → us field ke apne permlevel pe `{read:1, write:0}` row upsert — **sirf isi field ko affect karta hai.**
4. Koi row hi nahi (field default/untouched) → kuch nahi karna, backfill grant (Step 2) already current visibility preserve kar rahi hai.

**Existing hook fix zaroori:** `sync_custom_docperm_to_user_group` (jo external Custom DocPerm edits ko wapas `permissions` table mein mirror karta hai) abhi permlevel check nahi karta — isse naye permlevel>0 rows aake purane doctype-level `permissions` table ko corrupt kar sakte hain. Fix: function ke start mein `if doc.permlevel: return` add karna (sirf permlevel-0 external edits hi mirror hongi, jaisa original intent tha).

---

## Already Read-Only Fields Ka Special Handling — Poori List (kis doctype mein kitne)

Actual site data script se query kiya (`frappe.get_meta()` se, har managed doctype ke non-layout, non-hidden fields mein se jo `read_only=1` hain — hand-count nahi, code se exact nikala) — **33 managed doctypes mein already-read-only visible fields hain, poori list neeche hai (koi dash/truncation nahi, sab field names exact hain):**

| Doctype | Count | Fields |
|---|---|---|
| Purchase Invoice | 56 | `supplier_name`, `ewaybill`, `tax_id`, `return_against`, `is_boe_applicable`, `amended_from`, `use_transaction_date_exchange_rate`, `price_list_currency`, `total_qty`, `total_net_weight`, `base_total`, `base_net_total`, `claimed_landed_cost_amount`, `total`, `net_total`, `base_taxes_and_charges_added`, `base_taxes_and_charges_deducted`, `base_total_taxes_and_charges`, `taxes_and_charges_added`, `taxes_and_charges_deducted`, `total_taxes_and_charges`, `grand_total`, `in_words`, `rounding_adjustment`, `rounded_total`, `base_grand_total`, `base_in_words`, `base_rounding_adjustment`, `base_rounded_total`, `total_advance`, `outstanding_amount`, `base_discount_amount`, `other_charges_calculation`, `gst_breakup_table`, `pricing_rules`, `base_paid_amount`, `clearance_date`, `base_write_off_amount`, `address_display`, `supplier_gstin`, `gst_category`, `contact_display`, `contact_mobile`, `contact_email`, `dispatch_address_display`, `shipping_address_display`, `billing_address_display`, `company_gstin`, `auto_repeat`, `language`, `transporter_name`, `itc_classification`, `ineligibility_reason`, `reconciliation_status`, `is_internal_supplier`, `inter_company_invoice_reference` |
| Stock Entry | 31 | `subcontracting_order`, `outgoing_stock_entry`, `source_address_display`, `target_address_display`, `total_taxes`, `base_grand_total`, `total_outgoing_value`, `total_incoming_value`, `value_difference`, `total_additional_costs`, `supplier_name`, `bill_from_address_display`, `bill_from_gstin`, `bill_from_gst_category`, `bill_to_address_display`, `bill_to_gstin`, `bill_to_gst_category`, `ship_from_address_display`, `ship_to_address_display`, `transporter_name`, `delivery_note_no`, `sales_invoice_no`, `job_card`, `pick_list`, `asset_repair`, `ewaybill`, `purchase_receipt_no`, `subcontracting_inward_order`, `per_transferred`, `total_amount`, `amended_from` |
| Trip | 30 | `so_no`, `origin_state`, `destination_state`, `billing_start_date`, `billing_end_date`, `journey_time`, `journey_time_400_kmsday`, `total_vendor_freight`, `vendor_tds_to_be_deducted`, `loading_detention_days`, `loading_site_detention_amount`, `unloading_detention_days`, `unloading_site_detention_amount`, `total_detention_days`, `total_detention_amount`, `total_loading_unloading_charge`, `total_additional_charges`, `approved_detention_charge`, `approved_loadingunloading_charge`, `total_approved_addl_amount`, `difference_claimedapproved`, `total_trip_amount`, `trip_total_freight`, `total_km`, `variation`, `pod_status`, `amount_to_be_paid_to_vendor`, `vendor_payment_status`, `total_vendor_paid`, `vendor_balance_amount` |
| Payment Entry | 21 | `book_advance_payments_in_separate_party_account`, `contact_email`, `paid_from_account_currency`, `paid_to_account_currency`, `base_paid_amount`, `base_received_amount`, `total_allocated_amount`, `base_total_allocated_amount`, `difference_amount`, `base_total_taxes_and_charges`, `total_taxes_and_charges`, `company_gstin`, `billing_address_gstin`, `gst_category`, `clearance_date`, `status`, `base_in_words`, `payment_order`, `in_words`, `amended_from`, `auto_repeat` |
| Amazon Trip | 17 | `facility_sequence`, `cpt`, `is_cpt_truck`, `cr_id`, `shipper_accounts`, `estimated_cost`, `tender_status`, `trip_cost`, `total_vendor_freight`, `duplicate_trips`, `duplicate_record_no`, `vr_cancellation_date_time_utc`, `transit_operator_type`, `spot_work`, `computed_total_freight`, `computed_billed_amount`, `freight_difference` |
| Staff Payroll | 14 | `status`, `ctc`, `company`, `branch`, `total_days`, `total_attendance_days`, `salary_per_day`, `leave_with_pay`, `leave_without_pay`, `worked_days`, `total_earnings`, `total_deductions`, `net_salary`, `amended_from` |
| Import Log | 14 | `template_name`, `import_mode`, `status`, `uploaded_file`, `error_file`, `total_rows`, `success_rows`, `failed_rows`, `created_count`, `updated_count`, `skipped_count`, `started_at`, `finished_at`, `imported_by` |
| Payment | 13 | `payment_no`, `company`, `vf_vehicle`, `vf_financer`, `vf_loan_account`, `outstanding_balance`, `trip_tcn_no`, `trip_date`, `trip_type`, `trip_origin`, `trip_destination`, `trip_vehicle_type`, `amended_from` |
| Leave Application | 7 | `employee_name`, `company`, `department`, `total_leave_days`, `leave_balance`, `leave_approver_name`, `amended_from` |
| Vendor Payment | 6 | `company`, `amended_from`, `total_payment_amount`, `total_lr_money`, `total_tds_amount`, `total_transfer_amount` |
| Receipt | 6 | `company`, `amended_from`, `total_invoice_amount`, `total_brokerage_amount`, `total_lr_money`, `total_tds_amount` |
| Customer | 6 | `primary_address`, `loyalty_program_tier`, `lead_name`, `opportunity_name`, `prospect_name`, `customer_pos_id` |
| Item | 6 | `variant_of`, `last_purchase_rate`, `default_bom`, `default_item_manufacturer`, `default_manufacturer_part_no`, `published_in_website` |
| Battery Expenses | 4 | `vehicle_reg_no`, `warranty_expiry_date`, `actual_life_achieved`, `warranty_status` |
| Tyre Expenses | 4 | `total_qty`, `total_cost`, `km_run`, `cost_per_km` |
| Service Logs | 4 | `last_service_date`, `last_service_km`, `total_qty`, `total_amount` |
| Trip POD Collection | 4 | `collected_count`, `chat_id`, `pod_file_url`, `completed_at` |
| Trip POD Import | 3 | `import_no`, `import_date`, `import_by` |
| Amazon trip - Import | 3 | `import_no`, `import_date`, `import_by` |
| Fuel Urea Expenses | 3 | `partial_liters_carried`, `effective_liters`, `amended_from` |
| Address | 3 | `state`, `country`, `city` |
| Repair Expenses | 2 | `total_qty`, `amount` |
| Vehicle Finance | 2 | `emis_paid`, `outstanding_loan` |
| Staff Attendance | 2 | `attendance_no`, `amended_from` |
| Company | 2 | `reporting_currency`, `total_monthly_sales` |
| Employee | 2 | `employee_name`, `prefered_email` |
| Telegram Session | 2 | `last_activity`, `expires_at` |
| Telegram User Map | 2 | `full_name`, `last_seen` |
| Compliances | 1 | `expiry_date` |
| Vehicle | 1 | `amended_from` |
| Supplier | 1 | `primary_address` |
| Email Template | 1 | `reference_doctype` |
| Import Template | 1 | `sample_file` |

*(Ye list `install.py` mein banne wale `_assign_field_permlevels_and_backfill()` ke exact scope ko match karti hai — code implementation ke waqt bhi ye query dynamically `frappe.get_meta()` se hi nikaalega, hardcode nahi hoga, isliye doctype/field add-remove hone pe list khud-ba-khud update ho jaayegi.)*

**Note:** Ab in sab fields ko (Purchase Invoice ke 56 ho ya Trip ke 30) **apna alag-alag unique permlevel** milega — koi shared bucket nahi. Matlab agar koi group in mein se KISI EK field ko Hidden karta hai, to **sirf wahi ek field** us group ke liye Hidden hoga — baaki 55/29 fields bilkul unaffected rahenge, poori tarah independent control.

---

## NAYA REQUIREMENT: Trip Doctype Mein Trip-Type-Wise Field Permission (per User Group)

**Trip Settings doctype ko koi haath nahi lagega — confirm.** `Trip Settings` + `Trip Field Setting` (jo aaj Trip Type ke hisaab se field visibility control karte hain, `trip_settings.py` ka `get_field_config()` aur `trip.js` ka `apply_trip_type_visibility()` line ~645) **bilkul waisa hi rahega jaisa aaj hai — na doctype mein change, na permlevel.** Ye ek 100% ALAG, additional requirement hai jo TMS User Group side se aata hai.

**Requirement:** Trip doctype ke fields ka Hidden/Read-Only status ab sirf group-wise nahi, balki **group + trip_type dono ke combination se** decide hona chahiye. Example: "Fleet Manager" group ke liye field X sirf **Primary** trip type mein Hidden ho, lekin **Secondary/RCPL/Amazon/Other** trip type mein wahi field visible rahe — same group, alag trip_type, alag behavior.

### Kyun ye generic permlevel plan (Steps 1-5) se nahi ho sakta

Frappe ka native `permlevel` + `Custom DocPerm` mechanism **sirf ROLE ke basis pe** decide karta hai ki field dikhegi ya nahi — usko document ke andar kisi **dusre field ki VALUE** (jaise `trip_type`) ka koi awareness nahi hota. Permlevel ek field-level property hai (poore doctype ke liye fixed), aur Custom DocPerm grant `(doctype, role, permlevel)` pe based hai — ismein "agar trip_type=Primary tab hi" jaisi conditional logic express karne ka koi native tareeka nahi hai.

**Isliye ye Trip-specific requirement ek ALAG, CUSTOM enforcement layer maangta hai — sirf Trip doctype ke liye, permlevel mechanism ke upar/saath extra layer ke roop mein.** Baaki saare doctypes ke liye jo generic permlevel-based plan hai (upar Steps 1-5), wo bilkul waisa hi rahega — ye naya layer sirf Trip ke liye additive hai.

### Data storage — naya child table

`TMS User Group Trip Type Field Permission` (naya child doctype, Trip-specific):
- `trip_type` (Link → Trip Type)
- `fieldname`
- `field_state` — same 2-state convention: `1 = Hidden`, `2 = Read Only`

TMS User Group form pe naya hidden Table field `trip_type_field_permissions`. Ye Trip Settings ke data se bilkul independent hai — koi collision nahi.

### UI — Trip ke popup mein extra "Trip Type" dimension

Generic field-permission popup (Step 4, upar) sirf ek flat field-list dikhata hai — **Trip doctype ke liye ye popup special hoga**: field-list ke upar Trip Type selector/tabs (Primary / Secondary / RCPL / Amazon / Other) honge. Admin ek Trip Type chunega, us context mein fields ka Hidden/Read Only set karega — same field ka har trip_type ke liye alag-alag state ho sakta hai. Baaki doctypes ka popup pehle jaisa hi (flat list, koi trip-type dimension nahi) rahega.

### User → TMS User Group resolution: EXISTING helper hai, naya nahi banana

Verify kar liya — is app mein already ek reusable helper maujood hai: **`_get_user_tms_group(user)`** (`apps/logicore/logicore/tms_navigation_visibility.py:52`) — current logged-in user ka TMS User Group return karta hai (Guest/no-user → `None`, System Manager role wale users → `None` yani bypass, warna `_get_user_tms_group_candidates()` — `tms_list_settings.py:49`, Role-Profile based — se pehla matching existing TMS User Group name return karta hai). **Isi function ko import/reuse karenge** (`from logicore.tms_navigation_visibility import _get_user_tms_group`) — naya helper banane ki zaroorat nahi.

### Enforcement — Client-side (existing pattern extend karke, DONO call-sites pe)

`apply_trip_type_visibility(frm)` confirm kiya gaya hai `trip.js:645-710` pe — `trip_settings.get_field_config(trip_type)` (`trip_settings.py:87`) call karta hai, `hiddenFields` Set banata hai (line 663-664) jo `!row.is_visible` waale fields se banta hai, phir `reflow_trip_layout(frm, hiddenFields)` (line 667) aur `frm.set_df_property()` loop (line 668-670) se apply karta hai. **Yahi single merge-point hai** jahan naya group+trip_type wala data (naya whitelisted endpoint `get_trip_type_field_permissions(group_name, trip_type)` se) UNION karke add hoga (Trip Settings ke hidden-set + naya group-wise hidden/read-only-set milke final set banega), line 667/669 se pehle.

**Zaroori: `trip.js` mein `get_field_config` ka EK aur, ALAG call-site bhi hai (~line 3231-3269, ek doosre UI panel ke liye)** — naya merged data sirf pehle wale jagah lagana kaafi nahi hoga, **dono jagah** consistently apply karna hoga, warna form ka ek hissa purana (sirf Trip-Settings-based) behavior dikhayega aur doosra naya. Trip type change hone pe existing handler `trip.js:320` (jo `trip_type(frm)` event pe `apply_trip_type_visibility(frm)` ko line 324 se call karta hai) already trigger hota hai — naya data bhi isi flow mein re-fetch/re-apply hoga.

### Enforcement — Server-side (zaroori, security feature hai, sirf client-side kaafi nahi)

Trip controller (`trip/trip.py`) mein exact hook points confirm ho gaye:
- **`onload()` (lines 160-209):** Abhi sirf `set_onload()` payloads (vendor_payments, payments, receipts) populate karta hai, koi permission-logic nahi. **Yahin field-hiding add hogi** — `_get_user_tms_group(frappe.session.user)` + `self.trip_type` ke against jo fields Hidden hain, unhe `onload()` ke andar hi `self.set(fieldname, None)` (ya equivalent) se strip karna — ye standard Frappe form-load flow (`frappe.desk.form.load.getdoc`) mein doc serialize hone SE PEHLE chalta hai, isliye client ko field value milega hi nahi (permlevel ke `apply_fieldlevel_read_permissions` jaisa hi effect, bas custom logic se).
- **`validate()` (line 269 se shuru):** Already `old_trip_type = frappe.db.get_value(...)` (line 271-272) se trip_type-change detect karta hai — matlab controller already trip_type badalne ka pattern handle karta hai, humein bhi wahi jagah hook milega. **Yahin Read-Only enforcement add hogi** — current user ke group + (naye/purane) trip_type ke against jo fields Read-Only hain, unke values ko DB value se reset karna (agar user ne unhe change karne ki koshish ki), `reset_values_if_no_permlevel_access` jaisa hi custom-logic version.
- **`before_save()` (line 453)** — abhi body nahi padhi, implementation ke waqt zaroor check karenge ki naya code kisi existing logic (detention calc, billing cycle, vendor TDS) ko break na kare.
- **Important caveat:** `api.py:103` `get_trip(trip_name)` (jo `TRIP_FIELDS` list tak filter karta hai) ek ALAG code-path hai — **desk form khud is endpoint se load nahi hota** (standard `frappe.client.get`/doctype loader use hota hai), isliye ye endpoint field-hiding ke liye kaafi nahi — `onload()`/`validate()` hi asli enforcement point hain.

### `Trip.trip_type` field confirm

`trip/trip.json` lines 328-334: Link field (options: "Trip Type"), `reqd:1`, `in_list_view:1` — **koi `read_only`/`set_only_once`/`allow_on_submit` nahi hai**, matlab plain editable field hai aur **existing document pe bhi badal sakta hai** (jaisa `validate()` ka `old_trip_type` lookup already confirm karta hai). Isliye enforcement (client + server dono) trip_type CHANGE hone pe bhi dynamically react karna zaroori hai, sirf initial load pe nahi.

### Open items (implementation se pehle confirm karna)
1. Ye feature scope **sirf Trip doctype tak limited hai** (jaisa user ne kaha) — baaki koi bhi doctype trip-type dimension support nahi karega, sirf generic group-wise Hidden/Read-Only (Steps 1-5) hi milega.
2. Ye Trip-Type overlay poori tarah custom/separate enforcement hai (permlevel/Custom DocPerm istemal nahi karta) — har (group, trip_type, field) combination independently store aur enforce hota hai, isliye yahan bhi koi cross-field/cross-group leakage nahi hoti, generic permlevel-based design (jo ab har field ko unique permlevel deta hai) ki tarah hi clean/independent hai.
3. `before_save()` (line 453) ka poora body implementation se pehle padhna hoga taaki naya Read-Only-reset logic sahi jagah (validate vs before_save) mein slot ho, existing detention/billing/TDS calculations se pehle ya baad mein — order matter karta hai.

---

## Single DocType Ka Case (jaise "Alert Settings")

Verify kiya: is app mein 2 Single DocTypes hain — `Alert Settings` (`issingle: 1`) aur `Telegram Bot Settings` (`issingle: 1`). In dono mein se sirf **`Alert Settings` hi TMS User Group ke `_get_managed_doctypes()` mein aata hai** — kyunki wo workspace sidebar (`fixtures/workspace_sidebar.json`) mein link hai, aur `_get_sidebar_doctypes()` function sirf `istable` ko filter karta hai, `issingle` ko nahi (`tms_user_group.py` ka module-doctype fallback loop `issingle=0` filter karta hai, lekin sidebar loop nahi karta). Matlab **`Alert Settings` aaj bhi TMS permission matrix mein doctype-level row ke roop mein already dikh raha hai**, aur naya hyperlink + field-permission popup usko bhi automatically cover karega.

**Good news: koi special-case code nahi chahiye.** Frappe ka `permlevel` + `Custom DocPerm` mechanism Single aur normal (multi-row) doctype dono ke liye bilkul same tareeke se kaam karta hai — permlevel filtering (`apply_fieldlevel_read_permissions`, `reset_values_if_no_permlevel_access`) `Document`/`BaseDocument` object level pe operate karta hai, `istable`/`issingle` se independent. Property Setter bhi doctype+fieldname ke basis pe kaam karta hai, single/multi se farak nahi padta. Isliye:
- `_assign_field_permlevels_and_backfill()` (`install.py`) automatically Alert Settings ke fields ko bhi cover karega (kyunki wo `_get_managed_doctypes()` list mein hai).
- `get_doctype_field_permission_config` aur `save_field_permissions` endpoints bina kisi change ke Alert Settings pe bhi kaam karenge.
- Sirf farak itna hai ki Single doctype ka **list view / report view nahi hota** — is liye "field list-view se bhi gayab ho" wala testing point Alert Settings pe apply nahi hoga, sirf **form view** hi verify karna hoga. Single doctype ka form hamesha `frappe.get_doc(doctype, doctype)` se load hota hai (name == doctype), lekin field-level filtering isse unaffected hai.

Rollout testing checklist (neeche) mein Alert Settings ko explicitly ek test-case ke roop mein add kar diya hai.

---

## Rollout & Testing Plan (bahut zaroori — production risk hai)

Ye sabse zyada blast-radius wala step hai poore plan mein — backfill mein bug hua to migrate chalte hi sab groups ke fields gayab ho sakte hain. Isliye:

1. **Pehle staging/non-production site pe test karo**, production pe nahi.
2. Migrate se **pehle**: kuch representative TMS User Groups (ek `is_admin=1`, ek `is_admin=0`) aur representative doctypes (jaise Trip, jisme fields zyada hain, **aur `Alert Settings` — jo ek Single DocType hai, isko alag se zaroor include karo**) ke liye — as-is visible fields ka snapshot lo (actual desk form khol ke, us group ke user se login karke).
3. `bench migrate` chalao (`_assign_field_permlevels_and_backfill()` `after_migrate()` se chalega).
4. **Migrate ke baad wahi check dobara karo** — koi bhi field kisi bhi group ke liye gayab ya read-only NAHI hona chahiye jab tak koi admin ne explicitly toggle na kiya ho. Ye core regression check hai.
5. `Administrator` aur `System Manager` login verify karo — unaffected hone chahiye.
6. `bench migrate` dobara chalao (idempotency check, kyunki ye har migrate pe chalta hai) — duplicate Property Setter ya duplicate Custom DocPerm rows nahi banne chahiye, aur migrate ka time badhna nahi chahiye.
7. Naya feature functionally test karo: TMS User Group form → doctype naam pe click → field ko Hidden karo → Save → us group ke user se login karke confirm karo field form/list/report — sab jagah se gayab hai. Read Only state test karo (field dikhega but disabled). Ek aisa field bhi test karo jo doctype mein already `read_only=1` hai — confirm karo popup usko pre-selected `Read Only` (ON) state mein dikhaye, sirf `Hidden` hi actionable ho. **Independent-control regression check (naya, zaroori):** ek doctype ke 2+ already-read-only fields ko lo, ek group ke liye sirf EK field ko Hidden karo, Save karo, aur confirm karo doosra field us group ke liye **bilkul unaffected/visible** raha — ye confirm karta hai ki har field ka apna alag permlevel hai aur koi cross-field leakage nahi ho rahi.
8. `sync_custom_docperm_to_user_group` fix verify karo — Frappe ke native Role Permission Manager se ek field-level row edit karke confirm karo ki TMS User Group ka purana `permissions` table corrupt nahi ho raha.
9. TMS User Group delete (`on_trash`) flow verify karo — naye permlevel>0 Custom DocPerm rows bhi cleanup ho rahe hain ya nahi.
10. Trip-type-wise overlay ko alag se test karo: ek group ke liye field X ko Primary trip type mein Hidden karo, Secondary mein Default rakho — confirm karo Primary trip pe field gayab hai, Secondary trip pe dikh raha hai, same group ke liye.
11. Sab pass hone ke baad hi production migrate karo, low-traffic window mein.

---

## Open Decisions (in par input chahiye implementation shuru karne se pehle)

1. **Frappe ka native Role Permission Manager UI kya managed doctypes ke field-permlevel ke liye lock/restrict karna chahiye?** Aaj "Custom DocPerm kabhi direct edit mat karo" rule hai — ye rule ab naye permlevel>0 rows tak bhi extend karna padega, warna koi admin TMS User Group ko bypass karke seedha Frappe ke core UI se field permission badal sakta hai aur drift ho sakta hai. (Recommendation: restrict/hide kar do, lekin ye scope decision hai.)
2. **`is_admin=1` groups ke liye field-permission dialog editable rahe ya read-only/informational?** Existing pattern (doctype-level matrix + nav visibility) mein is_admin groups ke liye controls already disabled hain — same consistency recommend karta hoon.
3. **Print formats/PDF** ka specific coverage — form/list/report to native mechanism se cover ho jaayega, lekin print formats (Trip POD, Salary Slip) apna alag Jinja rendering path use karte hain jo shayad permission-filtered document object use na kare. Isko staging testing mein manually verify karna padega per print format.
4. **Naye fields jo baad mein doctype mein add hon** — unka default kya ho (permlevel 0 = sabko visible, jab tak admin explicitly permission dialog na khole) — ye current recommendation hai, confirm karna hoga.
5. **`before_save()` (trip.py:453) ka poora body** implementation se pehle padhna hoga taaki Read-Only-reset logic sahi jagah slot ho.

---

## Files Jo Touch Honge (implementation ke waqt)

- `apps/logicore/logicore/logicore/doctype/tms_user_group/tms_user_group.py` — naye whitelisted endpoints (`get_doctype_field_permission_config`, `save_field_permissions`), naya sync function, `sync_custom_docperm_to_user_group` fix
- `apps/logicore/logicore/logicore/doctype/tms_user_group/tms_user_group.js` — hyperlink + naya Dialog
- `apps/logicore/logicore/logicore/doctype/tms_user_group/tms_user_group.json` — naya `field_permissions` Table field
- `apps/logicore/logicore/logicore/doctype/tms_user_group_field_permission/` — naya child doctype (folder + json + py)
- `apps/logicore/logicore/install.py` — naya `_assign_field_permlevels_and_backfill()` function, `after_migrate()` ki call-list mein add (**koi naya patches/ file nahi**)

**Trip-type-wise overlay (naya requirement) ke liye extra files:**
- `apps/logicore/logicore/logicore/doctype/tms_user_group_trip_type_field_permission/` — naya child doctype (folder + json + py)
- `apps/logicore/logicore/logicore/doctype/tms_user_group/tms_user_group.json` — naya `trip_type_field_permissions` Table field
- `apps/logicore/logicore/logicore/doctype/tms_user_group/tms_user_group.py` — naya endpoint `get_trip_type_field_permissions(group_name, trip_type)`
- `apps/logicore/logicore/logicore/doctype/tms_user_group/tms_user_group.js` — Trip doctype ke popup mein extra Trip-Type selector/tabs
- `apps/logicore/logicore/logicore/doctype/trip/trip.py` — `onload()` (lines 160-209) mein field-hiding, `validate()` (line 269+) mein Read-Only value-reset
- `apps/logicore/logicore/logicore/doctype/trip/trip.js` — `apply_trip_type_visibility()` (line 645-710) extend, aur doosra `get_field_config` call-site (~line 3231-3269) bhi update
- **`trip_settings.py` / `trip_field_setting` / `trip_settings.js` — koi change NAHI** (explicit confirm kiya gaya hai)

**Implementation abhi nahi ho raha — ye sirf plan hai, execute karna hai jab explicitly kaha jaaye.**
