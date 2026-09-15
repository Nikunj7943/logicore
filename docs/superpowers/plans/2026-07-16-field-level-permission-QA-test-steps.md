# Field-Level Permission Feature — Professional QA Manual Test Steps

Pehle: `Ctrl+Shift+R` (hard refresh) karke naya JS load karo, phir shuru karo.

Legend: ✅ = expected result jo dikhna chahiye. Agar match na ho to wahi step note karke mujhe batao.

---

## Suite A — Access Control (kaun kya dekh sakta hai)

**A1. TMS Admin se login karo (System Manager ya kisi is_admin=1 group ka user)**
- TMS User Group list kholo
- ✅ Saare groups dikhne chahiye (System Manager/TMS Admin ke liye koi restriction nahi)

**A2. Kisi NON-admin group ke normal user se login karo (jo TMS Admin nahi hai)**
- TMS User Group list kholo
- ✅ Sirf UNKA APNA group dikhna chahiye, list mein aur koi group naam nahi
- Apna group kholo
- ✅ Form khulna chahiye (read access), lekin agar "Update Permission" unke liye check/delegate nahi hai to Save button disabled/permission-denied hona chahiye

**A3. Same non-admin user se, browser URL mein directly kisi DUSRE group ka naam daal ke try karo**
`http://logicore.com:8000/app/tms-user-group/<KISI-AUR-GROUP-KA-NAAM>`
- ✅ "Not permitted" / PermissionError aana chahiye, doc khulna nahi chahiye

---

## Suite B — Generic Field-Level Permission (Hidden / Read Only) — kisi bhi doctype ke liye

**B1. Load speed check**
- TMS Admin se koi bhi group kholo
- ✅ "Permissions Management" matrix turant load ho (1 second se kam, "Loading permissions..." bahut brief flash ho ya bilkul na dikhe)

**B2. Popup khulna**
- Matrix mein kisi bhi doctype ka naam (jaise "Trip", "Payment") ek hyperlink hoga (underline, purple color) — click karo
- ✅ Popup dialog khulega, us doctype ke saare currently-visible fields list honge (label + fieldtype), har field ke saamne ek dropdown/select (Default / Hidden / Read Only)

**B3. Field ko Hidden karna**
- Kisi normal field (jaise "Customer") ko "Hidden" select karo → Save
- ✅ Save successful, dialog band ho jaaye ya confirmation mile
- Us group ke assigned user se login karke us doctype ka koi record kholo
- ✅ Wo field form pe bilkul nahi dikhna chahiye (list view column mein bhi nahi)

**B4. Field ko Read Only karna**
- Kisi doosre field ko "Read Only" select karo → Save
- Us group ke user se record kholo
- ✅ Field dikhega, lekin edit nahi kar sakte (greyed out/disabled input)
- Field ki value change karke Save karne ki koshish karo (agar UI allow kare bhi to)
- ✅ Value change save nahi honi chahiye (server discard kar dega)

**B5. Default pe wapas laana**
- Wahi field ko wapas "Default" select karo → Save
- ✅ Us user ke liye field wapas poori tarah editable ho jaani chahiye (ye critical hai — pehle iska bug tha, ab fix hai)

**B6. Already-read-only field ka special case**
- Popup mein "Trip ID" (so_no) ya koi aisa field dhundo jo already system-read-only hai
- ✅ Uska dropdown pre-selected "Read Only" pe khulna chahiye, "Default" option NAHI hona chahiye (sirf Read Only aur Hidden)
- Usko "Hidden" karo → Save → user se confirm karo gayab hai
- Wapas "Read Only" karo → Save → confirm dobara dikh raha hai (read-only state mein)

**B7. Field independence (cross-field leakage test — bahut important)**
- Ek doctype ke 2 alag fields lo (dono already-read-only ya dono normal)
- Field A ko Hidden karo, Save
- ✅ Field B (jise touch nahi kiya) us user ko bilkul normal dikhna chahiye — Field A ke Hidden hone se Field B affect NAHI hona chahiye
- (Ye confirm karta hai har field ka apna independent permlevel hai, koi shared-bucket wala purana bug nahi)

---

## Suite C — Trip-Specific: Trip-Type-Wise Overlay (sirf Trip doctype ke liye)

**C1. Trip ka popup kholo**
- Matrix mein "Trip" pe click karo
- ✅ Field list ke upar ek extra dropdown dikhna chahiye: "Trip Type" (options: "All Trip Types" + PRIMARY/SECONDARY/OTHER/etc.)

**C2. Base (All Trip Types) layer test**
- "All Trip Types" selected rakhte hue, ek field Hidden karo → Save
- ✅ Ye Suite B jaisa hi generic layer hai (permlevel-based)

**C3. Trip-Type-specific overlay set karna**
- Dropdown se "PRIMARY" select karo
- ✅ Field list re-load hogi (thoda loading time), fresh/blank state dikhega (Primary ke liye pehle se kuch set nahi)
- Ek ALAG field (jo abhi Hidden nahi hai) ko Primary ke liye "Hidden" karo

**C4. Auto-save on switch verify karna**
- Dropdown se "SECONDARY..." pe switch karo (bina explicitly Save dabaye)
- ✅ Primary wala change automatically save ho jaana chahiye switch hote hi (backend call hoga)
- Secondary ka field-list "Default" (blank) dikhna chahiye

**C5. Per-trip-type isolation verify (end-user se)**
- Us group ke user se login karo
- Ek Trip banao/kholo jiska Trip Type = PRIMARY
- ✅ Jo field Primary ke liye Hidden kiya tha, wo is trip pe gayab hona chahiye
- Ek DUSRA Trip kholo jiska Trip Type = SECONDARY (ya kuch aur)
- ✅ Wahi field yahan NORMAL dikhna chahiye (Primary ka restriction Secondary pe apply nahi hota)

**C6. Trip Settings untouched confirm karna**
- "Trip Settings" doctype (alag doctype, per-trip-type field VISIBILITY ka purana feature) kholo
- ✅ Wahan koi bhi change nahi hona chahiye — wo feature bilkul waisa hi hai jaisa pehle tha

---

## Suite D — Permission Delegation (Update Permission checkbox)

**D1. is_admin group pe section hidden hona chahiye**
- "TMS ADMIN" (ya koi bhi is_admin=1 group) kholo
- ✅ "Permission Delegation" section BILKUL NAHI dikhna chahiye (Is Admin groups ke liye not applicable)

**D2. Normal group pe delegation set karna**
- Ek non-admin group kholo (jaise "TMS DIRECTOR")
- ✅ "Permission Delegation" section dikhna chahiye: "Update Permission" checkbox (unchecked by default) + "Permission Managers" field
- "Update Permission" ko check karo
- ✅ "Permission Managers" multiselect field ab dikhna/enable hona chahiye

**D3. Permission Managers dropdown filter check (important)**
- "Permission Managers" field mein click/type karo
- ✅ Sirf UNHI users ki list aani chahiye jo IS SPECIFIC group ke member hain (Employee mein assign hai) — poori User list nahi
- Ek user select karo → Save

**D4. Delegated user write-access verify**
- Us delegated user se login karo, apna group form kholo
- ✅ Ab wo Save kar sakta hai, matrix ke checkboxes change kar sakta hai, field-permission popup mein bhi changes save kar sakta hai

**D5. Non-delegated user (same group, but not selected) verify**
- Same group ka ek DUSRA user (jo delegate list mein nahi hai) se login karo
- ✅ Wo apna group READ kar sakta hai (dekh sakta hai) lekin Save/edit nahi kar sakta

**D6. Update Permission uncheck karna**
- Wapas TMS Admin se login karo, "Update Permission" ko uncheck karo, Save
- ✅ Ab delegated user bhi sirf read-only ho jaana chahiye (write access wapas le liya)

---

## Suite E — Regression (jo pehle se tha wo abhi bhi kaam kare)

**E1.** Doctype-level Read/Write/Create/Delete checkboxes (top matrix) — koi bhi ek toggle karke Save karo, normal user pe verify karo — pehle jaisa hi kaam karna chahiye.

**E2.** Navigation Visibility (Dashboard/Page toggles, neeche wala section) — kisi ek ko hide/show karke verify karo — unaffected hona chahiye.

**E3.** Kisi EXISTING group (jise aaj tak kisi ne field-permission feature se touch nahi kiya) ke user se login karke, unka Trip form kholo — ✅ Migrate se pehle jitne fields dikhte the, utne hi ab bhi dikhne chahiye (koi field achanak gayab/read-only nahi hona chahiye — backfill sahi se hua hai ye confirm hota hai).

---

## Agar kahin bhi mismatch mile

Mujhe exact bata do:
1. Kaunsa Suite/step number
2. Kya expect kiya tha vs kya actual hua
3. Konsa group/user/doctype/field use kiya

Main turant fix karunga.
