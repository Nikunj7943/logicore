# TMS Trip Operations — Widget Logic Reference

Source of truth: `apps/logicore/logicore/logicore/api.py` → `_trip_operations_card_conditions()` (line 220).
Last updated: 2026-07-31

---

## Common conditions (har widget par lagti hain)

Ye conditions **sabhi tabs ke sabhi widgets** par lagti hain, upar wale Filter Bar se:

| Filter | Condition | Kab lagta hai |
|---|---|---|
| Trip Type | `trip_type = <active tab>` | Hamesha |
| Company | `company = <selected>` | Jab Company select ho |
| Branch | `branch = <selected>` | Jab Branch select ho |
| From Date | `tcntrip_date >= <from_date>` | Jab From Date bhari ho |
| To Date | `tcntrip_date <= <to_date>` | Jab To Date bhari ho |
| Not Cancelled | `trip_status IS NULL OR trip_status != 'Cancel'` | Hamesha (har card me) |

Neeche har widget ki table me sirf **extra** conditions likhi hain — upar wali common conditions unke saath AND hoti hain.

---

## Tab 1 — PRIMARY (10 widgets)

| # | Widget | Logic (plain) | SQL Conditions |
|---|---|---|---|
| 1 | Pending POD | Arrival ho chuki hai lekin POD upload nahi hua | `arrival_date_time IS NOT NULL AND arrival_date_time != ''`<br>`AND (pod_status = 'POD Not Uploaded' OR pod_status IS NULL OR pod_status = '')` |
| 2 | Pending LR No | LR No bhara hi nahi gaya | `(lr_no IS NULL OR lr_no = '')` |
| 3 | Pending Dispatch | LR No hai, Reach ho gaya, lekin Dispatch record nahi hua | `lr_no IS NOT NULL AND lr_no != ''`<br>`AND reach_date_time IS NOT NULL AND reach_date_time != ''`<br>`AND (dispatch_date_time IS NULL OR dispatch_date_time = '')` |
| 4 | Pending Arrival | LR No hai, Dispatch ho gaya, lekin Arrival record nahi hui | `lr_no IS NOT NULL AND lr_no != ''`<br>`AND dispatch_date_time IS NOT NULL AND dispatch_date_time != ''`<br>`AND (arrival_date_time IS NULL OR arrival_date_time = '')` |
| 5 | Pending Customer Freight | LR No bhara hai lekin Customer Freight abhi 0/blank hai | `lr_no IS NOT NULL AND lr_no != ''`<br>`AND (customer_freight IS NULL OR customer_freight = 0)` |
| 6 | Pending Vendor Freight | Total Vendor Freight 0/blank hai | `(total_vendor_freight IS NULL OR total_vendor_freight = 0)` |
| 7 | Trip No To Be Provided | "Trip No Not Yet Provided" checkbox tick hai | `trip_no_not_yet_provided = 1` |
| 8 | Trip To Be Billed | Release ho gaya lekin Bill No aur Bill Date dono blank hain | `release_date_time IS NOT NULL AND release_date_time != ''`<br>`AND (bill_nodate IS NULL OR bill_nodate = '')`<br>`AND (bill_date IS NULL OR bill_date = '')` |
| 9 | Trip Payment Awaited | Release + Bill No + Bill Date sab hain, lekin Date Bill Credited blank hai | `release_date_time IS NOT NULL AND release_date_time != ''`<br>`AND bill_nodate IS NOT NULL AND bill_nodate != ''`<br>`AND bill_date IS NOT NULL AND bill_date != ''`<br>`AND (date_bill_credited IS NULL OR date_bill_credited = '')` |
| 10 | Original POD Awaited | Duplicate POD upload hua hai, Original abhi aana baaki hai | `uploaded_pod_originalduplicate = 'Duplicate'`<br>`AND pod_status = 'Duplicate POD Uploaded'` |

---

## Tab 2 — OTHER (6 widgets)

**Net Receivable** ka formula (widget 4 & 5 me use hota hai):
`Net Receivable = COALESCE(total_trip_amount,0) - COALESCE(brokerage_amount,0) - COALESCE(lr_money,0)`

| # | Widget | Logic (plain) | SQL Conditions |
|---|---|---|---|
| 1 | Arrival/Dispatch Columns Blank | Chaar milestone datetime me se **koi bhi ek** blank ho | `( (reach_date_time IS NULL OR reach_date_time = '')`<br>`OR (dispatch_date_time IS NULL OR dispatch_date_time = '')`<br>`OR (arrival_date_time IS NULL OR arrival_date_time = '')`<br>`OR (release_date_time IS NULL OR release_date_time = '') )` |
| 2 | Original POD Awaited | Duplicate POD upload hua hai, Original baaki hai | `uploaded_pod_originalduplicate = 'Duplicate'`<br>`AND pod_status = 'Duplicate POD Uploaded'` |
| 3 | Pending POD | Arrival ho chuki hai lekin POD upload nahi hua | `arrival_date_time IS NOT NULL AND arrival_date_time != ''`<br>`AND (pod_status = 'POD Not Uploaded' OR pod_status IS NULL OR pod_status = '')` |
| 4 | Advance Amount Awaited | Net Receivable hai lekin **ek bhi receipt** record nahi hui | `Net Receivable != 0`<br>`AND NOT EXISTS (Customer Receipt Trip row for this trip)` |
| 5 | Balance Amount Awaited | Kuch receipt aayi hai, lekin total received abhi Net Receivable se kam hai | `Net Receivable != 0`<br>`AND EXISTS (Customer Receipt Trip row)`<br>`AND SUM(received_amount) < Net Receivable` |
| 6 | Original POD Not Despatched | POD upload ho chuka hai lekin customer ko bheja nahi gaya | `uploaded_pod_originalduplicate IS NOT NULL AND != ''`<br>`AND pod_status IN ('Original POD Uploaded','Duplicate POD Uploaded')`<br>`AND (date_pod_sent_to_customer IS NULL OR date_pod_sent_to_customer = '')` |

---

## Tab 3 — SECONDARY DEDICATED (3 widgets)

| # | Widget | Logic (plain) | SQL Conditions |
|---|---|---|---|
| 1 | Pending POD | POD upload nahi hua (**yahan Arrival ki shart nahi hai**) | `(pod_status = 'POD Not Uploaded' OR pod_status IS NULL OR pod_status = '')` |
| 2 | Start KM and End KM Not Filled | Start Km aur End Km **dono** blank/0 hain | `(start_km IS NULL OR start_km = 0)`<br>`AND (end_km IS NULL OR end_km = 0)` |
| 3 | Standard KM Not Filled | Standard Km blank hai | `(standard_km IS NULL OR standard_km = '')` |

---

## Tab 4 — SECONDARY MARKET (1 widget)

| # | Widget | Logic (plain) | SQL Conditions |
|---|---|---|---|
| 1 | Pending POD | Arrival ho chuki hai lekin POD upload nahi hua | `arrival_date_time IS NOT NULL AND arrival_date_time != ''`<br>`AND (pod_status = 'POD Not Uploaded' OR pod_status IS NULL OR pod_status = '')` |

---

## Dhyaan dene ki baatein

- **"Pending POD" har tab me same nahi hai** — Primary / Other / Secondary Market me Arrival hona zaroori hai, lekin **Secondary Dedicated** me nahi.
- **Card pe click** karne par Trip list view khulta hai bilkul yahi filters lagake, isliye count aur list hamesha match karte hain.
- Teen cards (**Arrival/Dispatch Columns Blank, Advance Amount Awaited, Balance Amount Awaited**) ka logic OR / sub-query wala hai jo Frappe ke normal list filter me nahi likha ja sakta — inke liye server se exact Trip names mangwa ke list kholi jaati hai.
