import json
import os
import shutil
import subprocess
from pathlib import Path

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from logicore.overrides.login_redirect import TMS_HOME_PAGE
from logicore.role_profile_sync import FRAPPE_SYSTEM_ROLES, ensure_role_profiles_for_existing_roles
from logicore.utils.email_template_utils import ensure_email_template
from logicore.utils.vendor_payment_email import VENDOR_PAYMENT_EMAIL_TEMPLATE_NAME
from logicore.logicore.doctype.alert_settings.alert_settings import ensure_default_alert_settings
from logicore.logicore.doctype.tms_user_group.tms_user_group import (
    BASELINE_ALWAYS_GRANTED_DOCTYPES,
    EXCLUDED_SYSTEM_FIELDNAMES,
    LAYOUT_FIELDTYPES,
    _assign_permlevel_for_field,
    _ensure_baseline_group_permissions,
    _ensure_field_permlevel_baseline_for_role,
    _ensure_protected_role_permissions,
    _get_managed_doctypes,
    ensure_field_permlevel_baseline_all_groups,
    is_permlevel_protected_field,
)


def after_install():
    _ensure_system_dependencies()
    _clear_purchase_invoice_warehouse_default()
    _ensure_tms_user_group()
    ensure_default_alert_settings()
    _cleanup_imported_tms_user_groups()
    _restore_managed_doctype_permissions()
    _sync_baseline_group_permissions_all()
    _ensure_role_profiles()
    _ensure_tms_quick_filter_custom_fields()
    _sync_reconciliation_sources()
    _clear_bootinfo_cache()
    frappe.clear_cache()


def after_migrate():
    _ensure_system_dependencies()
    _clear_purchase_invoice_warehouse_default()
    _reset_trip_list_sort()
    _reset_tms_date_filter_bar_saved_filters()
    _set_tms_sidebar_default_sort()
    _ensure_tms_user_group()
    _backfill_tms_user_group_role_home_page()
    ensure_default_alert_settings()
    _cleanup_imported_tms_user_groups()
    _restore_managed_doctype_permissions()
    _cleanup_zero_only_custom_docperms()
    _sync_doctype_schemas_from_json()
    _apply_renamed_fields()
    _ensure_purchase_invoice_document_status_field()
    _backfill_purchase_invoice_document_status()
    _extend_purchase_invoice_payment_status_options()
    _hide_purchase_invoice_native_status_filter()
    _ensure_stock_issue_expense_setup()
    _backfill_expense_payment_date()
    _backfill_driver_payment_date()
    _backfill_trip_type_applies_to()
    _backfill_business_format_applies_to()
    _seed_compliance_document_types()
    _sync_all_tms_user_group_sidebars()
    _sync_baseline_group_permissions_all()
    _resync_custom_docperms_from_matrix_all()
    _assign_field_permlevels_and_backfill()
    _clear_permlevel_on_sort_fields()
    # Must run BEFORE the baseline backfill: it grants every group a row at every
    # permlevel still assigned, so clearing dead ones first avoids creating rows
    # for fields that no longer exist.
    _cleanup_orphaned_permlevel_artifacts()
    _remove_reconciliation_fields_when_feature_absent()
    ensure_field_permlevel_baseline_all_groups()
    _ensure_role_profiles()
    _backfill_address_display_fields()
    _sync_logicore_workspace()
    _ensure_vendor_pending_scrollbar()
    _warn_missing_generic_export_list_js()
    _ensure_tms_quick_filter_custom_fields()
    _migrate_tms_admin_quick_filters_to_global()
    _remove_company_type_custom_fields()
    _remove_purchase_invoice_duplicate_purchase_date_field()
    _ensure_check_supplier_invoice_uniqueness()
    _backfill_purchase_invoice_payment_status()
    _backfill_receipt_trip_vehicle_no()
    _enable_eway_bill_lookup_on_existing_settings()
    # Master enable/disable. Order matters: the rename frees up the `disabled`
    # fieldname on Vehicle/Branch before _ensure_master_disabled_fields would try
    # to create a fresh one there, and the mirror backfill needs the columns to
    # already exist. See master_status.py.
    _rename_inert_custom_disabled_fields()
    _ensure_master_disabled_fields()
    _backfill_disabled_mirror()
    # Bank reconciliation. Runs after the master enable/disable block above --
    # both are independent, but the reconciliation sources read Account Head /
    # Purchase Invoice metadata that the field steps above may have just changed.
    _ensure_supplier_payment_reconciliation()
    _sync_reconciliation_sources()
    _backfill_missing_account_ledger_entries()
    _backfill_account_ledger_entry_balance_amount()
    _refresh_opening_balance_ledger_ordering()
    _clear_stale_account_ledger_entry_user_settings()
    # _ensure_purchase_invoice_purchase_date()  # removed — reverted to plain posting_date
    # _ensure_stock_entry_payment_date()  # removed — reverted to plain posting_date
    _relabel_purchase_invoice_posting_date()
    _disable_link_preview_popup()
    _rename_border_crossing_payment_type()
    _backfill_cancelled_staff_payroll_status()
    _allow_salary_structure_component_edit_after_submit()
    _make_supplier_email_id_editable()
    _make_customer_email_id_editable()
    _make_supplier_mobile_no_editable()
    _make_customer_mobile_no_editable()
    _ensure_email_template_trip_type_gating()
    _remove_email_template_reference_doctype_overrides()
    # _ensure_vendor_payment_email_template()  # removed — user creates the
    # "Vendor Payment Confirmation" Email Template record manually via
    # Setup > Email > Email Template instead of auto-seeding it on migrate.
    _backfill_employee_user_default_company()
    _clear_sidebar_module_cache()
    _clear_bootinfo_cache()
    frappe.clear_cache()


def _sync_logicore_workspace():
    """Ensure LogiCore workspace content and custom_blocks are always up-to-date after migrate.

    This is needed because Frappe's fixture import skips updating workspace content
    when the record already exists, so we force-sync the content and child table here.
    """
    import json
    from pathlib import Path

    ws_json_path = Path(__file__).parent / "logicore" / "workspace" / "logicore" / "logicore.json"
    if not ws_json_path.exists():
        return

    try:
        ws_data = json.loads(ws_json_path.read_text())
        if not frappe.db.exists("Workspace", "LogiCore"):
            return

        # Update content JSON string
        frappe.db.set_value("Workspace", "LogiCore", "content", ws_data.get("content", "[]"))

        # Sync custom_blocks child table via raw SQL (frappe ORM skips child rows on db_update)
        frappe.db.sql("DELETE FROM `tabWorkspace Custom Block` WHERE parent='LogiCore'")
        now = frappe.utils.now()
        for idx, cb in enumerate(ws_data.get("custom_blocks", []), start=1):
            frappe.db.sql("""
                INSERT INTO `tabWorkspace Custom Block`
                (name, creation, modified, modified_by, owner, docstatus, idx,
                 parent, parenttype, parentfield, custom_block_name, label)
                VALUES (%s, %s, %s, 'Administrator', 'Administrator', 0, %s,
                        'LogiCore', 'Workspace', 'custom_blocks', %s, NULL)
            """, (frappe.generate_hash(length=10), now, now, idx, cb.get("custom_block_name")))

        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to sync LogiCore workspace")


def _ensure_vendor_pending_scrollbar():
    """Give the "Vendor Pending Amount" widget the same scrollable table treatment
    (max-height + sticky header, horizontal + vertical scroll) as the Trip Other
    widget. Idempotent — only touches the block if the old non-scrollable wrapper
    is still present, so re-running on future migrates is a no-op.
    """
    try:
        if not frappe.db.exists("Custom HTML Block", "TMS Vendor Pending"):
            return

        doc = frappe.get_doc("Custom HTML Block", "TMS Vendor Pending")
        if "max-height:480px" in doc.html:
            return

        old_wrapper = (
            '<div style="width:100%;overflow-x:auto;">'
            '<table id="vp-table" style="width:100%;border-collapse:collapse;font-size:13px;">'
        )
        new_wrapper = (
            '<div style="width:100%;overflow:auto;max-height:480px;'
            'border:1px solid var(--border-color);border-radius:8px;">'
            '<table id="vp-table" style="width:100%;border-collapse:collapse;font-size:13px;min-width:820px;">'
        )
        if old_wrapper not in doc.html:
            return

        doc.html = doc.html.replace(old_wrapper, new_wrapper)
        doc.html = doc.html.replace(
            'border-bottom:2px solid var(--border-color);">',
            'border-bottom:2px solid var(--border-color);position:sticky;top:0;'
            'background:var(--subtle-accent,#f4f5f7);z-index:1;">',
        )
        doc.style += (
            "#vp-table thead th:first-child,#vp-table tbody td:first-child"
            "{position:sticky;left:0;background:inherit;z-index:2;}"
            "#vp-table tbody tr:nth-child(even) td:first-child{background:var(--subtle-accent,#f9fafb);}"
            "#vp-table tbody tr:hover td:first-child{background:rgba(0,0,0,.04);}"
        )
        doc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to ensure Vendor Pending scrollbar")


def _warn_missing_generic_export_list_js():
    """Log a warning for any doctype that should have the generic "<DocType> Export"
    button (see utils/export_utils.py + public/js/tms_generic_export.js) but is
    missing its per-doctype `<name>_list.js` wrapper — e.g. a new doctype added
    after this feature was built. The wrapper itself must be created by hand (it
    lives inside that doctype's own folder, same convention as trip_list.js), this
    just surfaces the gap on every migrate so it isn't forgotten silently.
    """
    try:
        from logicore.utils.export_utils import is_export_supported

        doctype_root = Path(frappe.get_app_path("logicore", "logicore", "doctype"))
        missing = []

        for row in frappe.get_all("DocType", fields=["name", "module"]):
            if not row.module:
                continue
            app_name = frappe.db.get_value("Module Def", row.module, "app_name")
            if app_name != "logicore":
                continue
            if not is_export_supported(row.name):
                continue

            scrubbed = frappe.scrub(row.name)
            list_js_path = doctype_root / scrubbed / f"{scrubbed}_list.js"
            if not list_js_path.is_file() or "genericExport" not in list_js_path.read_text():
                missing.append(row.name)

        if missing:
            frappe.logger().warning(
                "[TMS] Generic Export button missing for: "
                + ", ".join(sorted(missing))
                + " — add a <name>_list.js wrapper calling TMS.genericExport.attach(listview)."
            )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to check generic export list.js coverage")


def _clear_bootinfo_cache():
    """Force desk boot payload regeneration after deploy-time permission/UI changes."""
    try:
        frappe.cache.delete_key("bootinfo")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to clear bootinfo cache")


def _rename_inert_custom_disabled_fields():
    """Vehicle/Branch shipped a "Disabled" checkbox that filtered nothing.

    Frappe hides a record from every Link dropdown when its doctype has a Check
    field named exactly `disabled` (frappe/desk/search.py:213-217). Both these
    doctypes got `custom_disabled` instead -- Frappe prepends `custom_` whenever a
    Custom Field is created without an explicit fieldname (custom_field.py:145-156)
    -- so users ticked the box, saw no error, and the vehicle kept appearing in
    every Trip, Repair Expense and Tyre Expense dropdown.

    The presence of `custom_disabled` is what drives this function, NOT the absence
    of `disabled`. That ordering matters on live: fixture import runs before
    after_migrate and creates `Vehicle-disabled` from custom_field.json, so by the
    time this runs both fields exist. Keying off `disabled` being missing would skip
    the whole thing and silently re-enable every vehicle that had been retired
    through the inert checkbox.

    Four states, all handled:
      no custom_disabled                  -> already done, skip
      custom_disabled, no disabled column -> rename_fieldname (column carries data)
      custom_disabled + orphan column     -> adopt the orphan, then copy ticks
      custom_disabled + real disabled CF  -> copy ticks, drop the duplicate field
    """
    from frappe.custom.doctype.custom_field.custom_field import rename_fieldname

    description = (
        "Disabled records stay on existing documents but stop appearing in "
        "dropdowns when creating new ones."
    )

    for doctype in ("Vehicle", "Branch"):
        try:
            old = f"{doctype}-custom_disabled"
            if not frappe.db.exists("Custom Field", old):
                continue

            if not frappe.db.exists("Custom Field", f"{doctype}-disabled"):
                if not frappe.db.has_column(doctype, "disabled"):
                    # Cleanest path: the column itself is renamed, so ticks move with it.
                    rename_fieldname(custom_field=old, fieldname="disabled")
                    ticked = frappe.db.count(doctype, {"disabled": 1})
                    print(
                        f"master enable/disable: {doctype}.custom_disabled -> disabled "
                        f"(renamed, {ticked} ticked)"
                    )
                    continue

                # An orphan `disabled` column is sitting there -- Frappe never drops a
                # column when its Custom Field is deleted, so a long-gone field left one
                # behind. rename_fieldname() refuses to overwrite it
                # (custom_field.py:415), so adopt the orphan instead of renaming onto it.
                frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": doctype,
                    "fieldname": "disabled",
                    "label": "Disabled",
                    "fieldtype": "Check",
                    "default": "0",
                    "description": description,
                    "insert_after": frappe.db.get_value("Custom Field", old, "insert_after"),
                    "in_standard_filter": 1,
                }).insert(ignore_permissions=True)

            # `disabled` exists now -- ours, the fixture's, or pre-existing. Carry the
            # old ticks across with OR semantics: anything retired through either
            # checkbox stays retired.
            if frappe.db.has_column(doctype, "custom_disabled"):
                frappe.db.sql(
                    f"UPDATE `tab{doctype}` SET disabled = 1 WHERE custom_disabled = 1"
                )
            # Removes the duplicate "Disabled" checkbox from the form. The orphaned
            # custom_disabled column stays behind, harmless, same as any other.
            frappe.delete_doc("Custom Field", old, ignore_permissions=True, force=True)

            ticked = frappe.db.count(doctype, {"disabled": 1})
            print(
                f"master enable/disable: {doctype}.custom_disabled -> disabled "
                f"(merged, {ticked} ticked)"
            )
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to rename {doctype}.custom_disabled")


def _ensure_master_disabled_fields():
    """Give the remaining sidebar Masters a working `disabled` Check field.

    Two shapes. TARGETS is a plain user-facing checkbox. MIRROR_TARGETS is hidden
    and read-only because the doctype already had its own lifecycle field
    (Employee.status, Driver.status) and that field stays in charge --
    master_status.sync_disabled_mirror keeps `disabled` derived from it.

    Also repairs Email Template.enabled, whose default of 0 meant every template
    was born disabled and invisible to Link dropdowns.

    The app-owned masters (Account Head, Repair Category/Sub Category/Item,
    Compliance Document Type, TMS User Group, Import Template) carry the field in
    their own DocType JSON instead, so they are absent here.
    """
    description = (
        "Disabled records stay on existing documents but stop appearing in "
        "dropdowns when creating new ones."
    )
    targets = {
        "Customer Group": "customer_group_name",
        "GST HSN Code": "hsn_code",
        "Item Group": "item_group_name",
        "Supplier Group": "supplier_group_name",
    }
    mirror_targets = {
        "Driver": "status",
        "Employee": "status",
    }

    try:
        for doctype, insert_after in targets.items():
            if frappe.db.exists("Custom Field", f"{doctype}-disabled"):
                continue
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                "fieldname": "disabled",
                "label": "Disabled",
                "fieldtype": "Check",
                "default": "0",
                "description": description,
                "insert_after": insert_after,
                "in_standard_filter": 1,
            }).insert(ignore_permissions=True)
            print(f"master enable/disable: {doctype}.disabled created")

        for doctype, insert_after in mirror_targets.items():
            if frappe.db.exists("Custom Field", f"{doctype}-disabled"):
                continue
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                "fieldname": "disabled",
                "label": "Disabled",
                "fieldtype": "Check",
                "default": "0",
                "description": f"Derived from {frappe.unscrub(insert_after)}. Not edited directly.",
                "insert_after": insert_after,
                "hidden": 1,
                "read_only": 1,
            }).insert(ignore_permissions=True)
            print(f"master enable/disable: {doctype}.disabled mirror created")

        # Fixture import runs after this and would put the old default back, so the
        # fixture file itself carries default "1" -- this only repairs a site whose
        # fixture predates that change.
        name = frappe.db.exists("Custom Field", {"dt": "Email Template", "fieldname": "enabled"})
        if name and frappe.db.get_value("Custom Field", name, "default") != "1":
            frappe.db.set_value("Custom Field", name, "default", "1")
            print("master enable/disable: Email Template.enabled default 0 -> 1")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to ensure master disabled fields")


def _backfill_disabled_mirror():
    """Catch `disabled` up with the source field on masters that derive it.

    The mirror hook only fires on save, so without this an Employee who left two
    years ago still has disabled=0 and keeps appearing in every dropdown.

    update_modified=False on purpose: this is a derived value catching up, not a
    user edit, and it must not disturb timestamps or fire hooks across thousands
    of rows.
    """
    from logicore.master_status import MIRROR_RULES, compute_disabled

    try:
        for doctype, rule in MIRROR_RULES.items():
            if not frappe.db.has_column(doctype, "disabled"):
                continue
            source = rule["source"]
            rows = frappe.get_all(doctype, fields=["name", source, "disabled"])
            changed = 0
            for row in rows:
                expected = compute_disabled(doctype, row.get(source))
                if row.get("disabled") != expected:
                    frappe.db.set_value(
                        doctype, row["name"], "disabled", expected, update_modified=False
                    )
                    changed += 1
            if changed:
                print(f"master enable/disable: {doctype} — {changed} of {len(rows)} mirrored")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill disabled mirror")


def _clear_sidebar_module_cache():
    """Best-effort: clear auto_generate_sidebar_from_module's cache in whichever
    process runs migrate. Does NOT fix already-running web/worker processes on
    live (each worker has its own copy of this cache) — see
    fix_workspace_sidebar_bootinfo() below for the fix that actually holds.
    """
    try:
        from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import (
            auto_generate_sidebar_from_module,
        )

        auto_generate_sidebar_from_module.clear_cache()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to clear sidebar module cache")


def fix_workspace_sidebar_bootinfo(bootinfo):
    """Strip the phantom auto-generated "LogiCore" sidebar entry that
    Frappe's own auto_generate_sidebar_from_module() can inject alongside our
    real fixture-based "LogiCore" sidebar, causing the desk to randomly show
    the generic default sidebar instead of ours on report/dashboard routes.

    Root cause: auto_generate_sidebar_from_module() is decorated with Frappe's
    @site_cache() (frappe/utils/caching.py), which caches its result forever,
    per-process, and is never shared across workers. If even one worker process
    ever computed the duplicate (e.g. before this app's "LogiCore" sidebar
    fixture existed on that site, or from a migrate-timing race on an earlier
    deploy), that single worker keeps serving the duplicate for its entire
    remaining lifetime. Clearing the Redis "bootinfo" cache in after_migrate
    (see _clear_bootinfo_cache) forces boot info to regenerate, but does NOT
    reach this inner per-process cache — so on live (multiple long-lived
    workers), the bug can silently survive any number of future deploys.
    Registered in hooks.py as a boot_session hook so it runs on every single
    boot, in whatever process actually serves that request, making the sidebar
    correct regardless of which worker or how stale its cache is.
    """
    sidebar_items = bootinfo.get("workspace_sidebar_item")
    if sidebar_items and "logicore 2026" in sidebar_items and "logicore" in sidebar_items:
        del sidebar_items["logicore 2026"]


# Every doctype whose list.js wires up TMS.dateFilterBar (public/js/tms_date_filter_bar.js).
# Add a doctype here whenever it gets a new TMS.dateFilterBar.attach() call — see
# _reset_tms_date_filter_bar_saved_filters() below for why this list must stay
# in sync with the JS side.
TMS_DATE_FILTER_BAR_DOCTYPES = [
    "Trip",
    "Amazon Trip",
    "Amazon trip - Import",
    "Vendor Payment",
    "Payment",
    "Receipt",
    "Trip POD Import",
    "Repair Expenses",
    "Fuel Urea Expenses",
    "Battery Expenses",
    "Tyre Expenses",
    "Service Logs",
    "Compliances",
    "Staff Attendance",
    "Staff Payroll",
    "Import Log",
    "Purchase Invoice",
    "Supplier Payment",
    "TMS Bank Reconciliation",
    "Account Ledger",
    "Stock Entry",
    "Leave Application",
]


def _reset_trip_list_sort():
    """Clear saved list filters from __UserSettings so DocType defaults apply for all users.

    Renamed in behavior but not in name (kept to avoid touching every call
    site) — see _reset_tms_date_filter_bar_saved_filters() immediately below,
    which is the same idea generalized to every TMS.dateFilterBar doctype,
    not just Trip/Amazon Trip.
    """
    frappe.db.sql("""
        UPDATE __UserSettings
        SET data = JSON_SET(data, '$.List.filters', JSON_ARRAY())
        WHERE doctype IN ('Trip', 'Amazon Trip')
          AND JSON_VALID(data)
          AND JSON_EXTRACT(data, '$.List.filters') IS NOT NULL
    """)
    frappe.db.commit()


def _reset_tms_date_filter_bar_saved_filters():
    """A doctype's TMS.dateFilterBar bar defaults to "today" and applies that
    filter on every plain sidebar visit — but Frappe also asynchronously
    restores each user's own saved List filters from __UserSettings on list
    load, and that restore can land AFTER the bar's own applied filter,
    silently overwriting it back to whatever (or nothing) was last saved —
    the bar's badge still shows "today" (a plain DOM write) while the grid
    quietly shows unfiltered/stale data underneath.

    Trip and Amazon Trip already got a narrower version of this cleanup
    (_reset_trip_list_sort above); this is the same fix generalized to every
    other doctype wired to TMS.dateFilterBar, so old/stale saved filters
    from before that wiring existed can no longer win the race.

    Idempotent: clearing an already-empty filters array is a no-op.
    """
    frappe.db.sql(
        """
        UPDATE __UserSettings
        SET data = JSON_SET(data, '$.List.filters', JSON_ARRAY())
        WHERE doctype IN %(doctypes)s
          AND JSON_VALID(data)
          AND JSON_EXTRACT(data, '$.List.filters') IS NOT NULL
        """,
        {"doctypes": TMS_DATE_FILTER_BAR_DOCTYPES},
    )
    frappe.db.commit()


TMS_SIDEBAR_SORT_CORE_DOCTYPES = {
    "Purchase Invoice": "posting_date",
    "Stock Entry": "posting_date",
    "Payment Entry": "posting_date",
    "Leave Application": "posting_date",
}

TMS_SIDEBAR_SORT_CUSTOM_DOCTYPES = [
    "Payment",
    "Receipt",
    "Amazon Trip",
    "Amazon trip - Import",
    "Repair Expenses",
    "Fuel Urea Expenses",
    "Battery Expenses",
    "Tyre Expenses",
    "Service Logs",
    "Vehicle Finance",
    "Compliances",
    "Staff Attendance",
    "Staff Payroll",
    "Trip",
    "Trip POD Import",
    "Vendor Payment",
    "Supplier Payment",
    "Account Ledger",
]


def _set_tms_sidebar_default_sort():
    """Keep each doctype's default list sort in sync with TMS_SIDEBAR_SORT_OVERRIDE
    (public/js/hide_sidebar.js) on every migrate, so a fresh site/deploy/Frappe
    Cloud pull doesn't need a manual `bench execute` step.

    - Core doctypes (Purchase Invoice, Stock Entry, ...) can't have their vendor
      JSON edited directly (would be overwritten on app updates), so their
      sort_field/sort_order is set via Property Setter instead.
    - Custom (app-owned) doctypes already declare sort_field/sort_order in their
      own JSON; reload_doc here just guarantees the DB row matches it even if a
      migrate was skipped earlier.
    - Also clears any stale per-user cached sort_by/sort_order in __UserSettings
      for these doctypes, so the new default is visible immediately instead of
      being shadowed by a user's previously saved sort.

    Idempotent: property setters are updated in place if they already exist,
    reload_doc is safe to call repeatedly, and the __UserSettings cleanup is a
    no-op once already cleared.
    """
    try:
        for doctype, sort_field in TMS_SIDEBAR_SORT_CORE_DOCTYPES.items():
            _set_core_doctype_sort(doctype, sort_field)

        for doctype in TMS_SIDEBAR_SORT_CUSTOM_DOCTYPES:
            frappe.reload_doctype(doctype, force=True)

        _clear_stale_sidebar_sort_user_settings()
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to set TMS sidebar default sort")


_SALARY_COMPONENT_TABLES = {
    "Salary Structure": ("earnings", "deductions"),
    "Staff Payroll": ("earnings_table", "deductions_table"),
}


def _allow_salary_structure_component_edit_after_submit():
    """Let earnings/deductions rows be added to a submitted Salary Structure, and to
    the earnings_table/deductions_table of every submitted Staff Payroll generated
    from it -- Staff Payroll generates one record per employee per month, so by the
    time a new component needs adding, cancelling/amending the structure would
    force-cancel every record already submitted against it. Who may actually use
    this hole (only Administrator / System Manager / TMS ADMIN) is enforced in
    overrides/salary_structure.py's before_save hooks, not here; the automatic
    backfill of new components into old Staff Payroll records lives in that same
    module's enqueue_component_backfill / backfill_staff_payroll_components.

    Idempotent: property setters are updated in place if they already exist.
    """
    try:
        for doctype, fieldnames in _SALARY_COMPONENT_TABLES.items():
            for fieldname in fieldnames:
                existing = frappe.db.get_value(
                    "Property Setter",
                    {"doc_type": doctype, "field_name": fieldname, "property": "allow_on_submit"},
                    "name",
                )
                if existing:
                    frappe.db.set_value("Property Setter", existing, "value", "1")
                else:
                    make_property_setter(doctype, fieldname, "allow_on_submit", "1", "Check")
            frappe.clear_cache(doctype=doctype)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to set salary component allow_on_submit")


def _set_core_doctype_sort(doctype, sort_field):
    for prop, value, ptype in (
        ("sort_field", sort_field, "Data"),
        ("sort_order", "DESC", "Select"),
    ):
        existing = frappe.db.get_value(
            "Property Setter",
            {"doc_type": doctype, "property": prop, "doctype_or_field": "DocType"},
            "name",
        )
        if existing:
            frappe.db.set_value("Property Setter", existing, "value", value)
        else:
            make_property_setter(doctype, None, prop, value, ptype, for_doctype=True)
    frappe.clear_cache(doctype=doctype)


def _clear_stale_sidebar_sort_user_settings():
    doctypes = list(TMS_SIDEBAR_SORT_CORE_DOCTYPES) + TMS_SIDEBAR_SORT_CUSTOM_DOCTYPES
    rows = frappe.db.sql(
        """select `user`, `doctype`, `data` from `__UserSettings`
        where `doctype` in %(doctypes)s""",
        {"doctypes": doctypes},
        as_dict=True,
    )
    for row in rows:
        try:
            data = json.loads(row["data"]) if row["data"] else {}
        except ValueError:
            continue
        dirty = False
        list_settings = data.get("List")
        if isinstance(list_settings, dict):
            for key in ("sort_by", "sort_order"):
                if key in list_settings:
                    del list_settings[key]
                    dirty = True
        report_settings = data.get("Report")
        if isinstance(report_settings, dict):
            for key in ("order_by", "sort_by", "sort_order"):
                if key in report_settings:
                    del report_settings[key]
                    dirty = True
        if dirty:
            frappe.db.sql(
                """update `__UserSettings` set `data` = %(data)s
                where `user` = %(user)s and `doctype` = %(doctype)s""",
                {"data": json.dumps(data), "user": row["user"], "doctype": row["doctype"]},
            )


def _ensure_system_dependencies():
    """Install OS packages required by the POD/OCR pipeline if missing.

    - ghostscript    -> `gs`        (PDF compression)
    - poppler-utils  -> `pdftoppm`  (pdf2image: render PDF pages for QR/OCR)
    - tesseract-ocr  -> `tesseract` (pytesseract: TCN Summary Sheet OCR)
    - libzbar0       -> (pyzbar QR decoding shared library)
    """
    _ensure_apt_package("ghostscript", shutil.which, "gs")
    _ensure_apt_package("poppler-utils", shutil.which, "pdftoppm")
    _ensure_apt_package("tesseract-ocr", shutil.which, "tesseract")
    _ensure_apt_package("libzbar0", _has_libzbar)


def _has_libzbar(_binary=None) -> bool:
    import ctypes.util
    return bool(ctypes.util.find_library("zbar"))


def _ensure_apt_package(apt_name: str, check_fn, check_arg=None):
    """Install `apt_name` via apt-get unless `check_fn(check_arg)` is already truthy."""
    if check_fn(check_arg):
        return

    env = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}

    # 1. Root / Docker / Frappe Cloud — no sudo needed
    try:
        r = subprocess.run(
            ["apt-get", "install", "-y", apt_name],
            capture_output=True, timeout=60, env=env,
        )
        if r.returncode == 0 and check_fn(check_arg):
            frappe.logger().info(f"{apt_name} installed successfully.")
            return
    except Exception:
        pass

    # 2. NOPASSWD already configured — silent
    try:
        r = subprocess.run(
            ["sudo", "-n", "apt-get", "install", "-y", apt_name],
            capture_output=True, timeout=60, env=env,
        )
        if r.returncode == 0 and check_fn(check_arg):
            frappe.logger().info(f"{apt_name} installed successfully.")
            return
    except Exception:
        pass

    # 3. Interactive — user types password in terminal
    print(f"\n[LogiCore] Installing {apt_name}...")
    try:
        r = subprocess.run(
            ["sudo", "apt-get", "install", "-y", apt_name],
            timeout=120, env=env,
            # No capture_output — stdin/stdout/stderr inherited so password prompt shows
        )
        if r.returncode == 0 and check_fn(check_arg):
            frappe.logger().info(f"{apt_name} installed successfully.")
            return
    except Exception:
        pass

    frappe.logger().warning(
        f"{apt_name} not found and could not be auto-installed. "
        f"Install manually: sudo apt install {apt_name}"
    )


def _ensure_tms_user_group():
    import json
    import os

    doctype_path = os.path.join(
        os.path.dirname(__file__),
        "logicore",
        "doctype",
        "tms_user_group",
        "tms_user_group.json"
    )

    if os.path.exists(doctype_path):
        try:
            with open(doctype_path) as f:
                doc_data = json.load(f)

            if not frappe.db.exists("DocType", "TMS User Group"):
                frappe.get_doc(doc_data).insert(ignore_permissions=True)
                frappe.logger().info("Created TMS User Group DocType")
        except Exception as e:
            frappe.logger().error(f"Failed to ensure TMS User Group: {e}")


def _backfill_tms_user_group_role_home_page():
    """Every TMS User Group's mirrored Role must redirect to the TMS home page.

    _sync_role() on TMSUserGroup already sets this on insert/save, but groups
    that haven't been re-saved since this was added need a one-time backfill.
    """
    for role_name in frappe.get_all("TMS User Group", pluck="name"):
        if frappe.db.exists("Role", role_name):
            if frappe.db.get_value("Role", role_name, "home_page") != TMS_HOME_PAGE:
                frappe.db.set_value("Role", role_name, "home_page", TMS_HOME_PAGE)


def _ensure_role_profiles():
    try:
        ensure_role_profiles_for_existing_roles()
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to ensure role profiles")


def _cleanup_imported_tms_user_groups():
    """Remove old auto-imported TMS User Groups without deleting the original roles.

    Imported groups can be identified because the linked Role existed much earlier
    than the TMS User Group record itself. Custom groups created through TMS
    create the Role during the same save flow, so their timestamps are near-equal.
    """
    try:
        imported = frappe.db.sql(
            """
            SELECT tug.name
            FROM `tabTMS User Group` tug
            INNER JOIN `tabRole` r ON r.name = tug.group_name
            WHERE tug.group_name NOT IN (
                'Administrator', 'All', 'Auditor', 'Blogger', 'Dashboard Manager',
                'Desk User', 'Guest', 'Newsletter Manager', 'Script Manager',
                'System Manager', 'Translator', 'Workspace Manager'
            )
            AND TIMESTAMPDIFF(SECOND, r.creation, tug.creation) > 60
            """,
            as_dict=True,
        )
        if not imported:
            return

        names = [row.name for row in imported]
        managed = list(_get_managed_doctypes())
        group_names = frappe.get_all(
            "TMS User Group",
            filters={"name": ["in", names]},
            pluck="group_name",
        )

        if managed and group_names:
            frappe.db.delete(
                "Custom DocPerm",
                {
                    "parent": ["in", managed],
                    "role": ["in", group_names],
                },
            )

        frappe.db.sql(
            f"DELETE FROM `tabTMS User Group Permission` WHERE parent IN ({','.join(['%s'] * len(names))})",
            names,
        )
        frappe.db.sql(
            f"DELETE FROM `tabTMS User Group` WHERE name IN ({','.join(['%s'] * len(names))})",
            names,
        )
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to cleanup imported TMS User Groups")


def _sync_doctype_schemas_from_json():
	"""Force reload all app doctypes from JSON to sync schema changes on every migrate.

	This ensures fields added to doctype JSON (e.g., repair_expense_item.remark) are
	applied to the database schema. Without this, schema changes in version control
	require manual `bench reload-doc` on the target server.

	Idempotent: frappe.reload_doc() with force=True is safe to call repeatedly.
	"""
	try:
		from pathlib import Path
		doctype_root = Path(frappe.get_app_path("logicore", "logicore", "doctype"))

		if not doctype_root.exists():
			return

		for folder in doctype_root.iterdir():
			if not folder.is_dir():
				continue

			doctype_name = folder.name.replace("_", " ").title().replace(" ", "")
			json_path = folder / f"{folder.name}.json"

			if not json_path.exists():
				continue

			try:
				frappe.reload_doc("logicore", "doctype", folder.name, force=True)
			except Exception as e:
				frappe.logger().warning(f"Failed to sync schema for {folder.name}: {str(e)}")

		frappe.db.commit()
		frappe.logger().info("Synced doctype schemas from JSON files")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Failed to sync doctype schemas from JSON")


# Superseded by RENAMED_FIELDS / _apply_renamed_fields() below — kept per the
# "comment out, never delete" rule. Both did the same job per-doctype; the
# generic version below also runs rename_field() for Supplier Payment now
# (this one only did a raw column copy), so nothing is lost by retiring it.
# def _rename_supplier_payment_posting_date_column():
#     """Supplier Payment's `posting_date` fieldname was renamed to `payment_date`
#     (it was being confused with Purchase Invoice's own posting_date). The schema
#     sync above already added the new `payment_date` column via bench migrate's
#     own ALTER TABLE; this copies over any data still sitting in the orphaned old
#     `posting_date` column and drops it.
#
#     Idempotent: no-op once `posting_date` is gone from the table.
#     """
#     try:
#         if not frappe.db.table_exists("Supplier Payment"):
#             return
#         columns = {c[0] for c in frappe.db.sql("SHOW COLUMNS FROM `tabSupplier Payment`")}
#         if "posting_date" not in columns:
#             return
#         if "payment_date" not in columns:
#             # Schema sync hasn't added the new column yet — retry next migrate.
#             return
#         frappe.db.sql(
#             """
#             UPDATE `tabSupplier Payment`
#             SET payment_date = posting_date
#             WHERE payment_date IS NULL AND posting_date IS NOT NULL
#             """
#         )
#         frappe.db.sql_ddl("ALTER TABLE `tabSupplier Payment` DROP COLUMN posting_date")
#         frappe.db.commit()
#         frappe.logger().info("[TMS] Migrated Supplier Payment.posting_date -> payment_date")
#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Failed to rename Supplier Payment posting_date column")
#
#
# def _rename_vendor_payment_and_receipt_posting_date_columns():
#     """Vendor Payment's and Receipt's `posting_date` fieldname were both renamed
#     to `payment_date` (matching Supplier Payment's earlier rename above). The
#     schema sync above already added the new `payment_date` column via bench
#     migrate's own ALTER TABLE.
#
#     Unlike the Supplier Payment rename above, this uses Frappe's own
#     `rename_field()` (not just a raw column copy) so Property Setters —
#     in_list_view, in_standard_filter (Customize Quick Filters), any
#     `insert_after` pointing at the old fieldname — and saved Report
#     Builder / user list-view settings referencing `posting_date` are migrated
#     to `payment_date` too, instead of silently going stale.
#
#     Idempotent: no-op once `posting_date` is gone from each table.
#     """
#     from frappe.model.utils.rename_field import rename_field
#
#     for doctype in ("Vendor Payment", "Receipt"):
#         try:
#             if not frappe.db.table_exists(doctype):
#                 continue
#             columns = {c[0] for c in frappe.db.sql(f"SHOW COLUMNS FROM `tab{doctype}`")}
#             if "posting_date" not in columns:
#                 continue
#             if "payment_date" not in columns:
#                 # Schema sync hasn't added the new column yet — retry next migrate.
#                 continue
#             rename_field(doctype, "posting_date", "payment_date")
#             frappe.db.sql(
#                 f"""
#                 UPDATE `tab{doctype}`
#                 SET payment_date = posting_date
#                 WHERE payment_date IS NULL AND posting_date IS NOT NULL
#                 """
#             )
#             frappe.db.sql_ddl(f"ALTER TABLE `tab{doctype}` DROP COLUMN posting_date")
#             frappe.db.commit()
#             frappe.logger().info(f"[TMS] Migrated {doctype}.posting_date -> payment_date")
#         except Exception:
#             frappe.log_error(frappe.get_traceback(), f"Failed to rename {doctype} posting_date column")


# Canonical list of every fieldname rename this app has ever needed, as
# (doctype, old_fieldname, new_fieldname). Add a row here for any future
# rename and _apply_renamed_fields() picks it up on the next bench migrate —
# no new patch file needed, and it propagates to every clone/Frappe Cloud
# pull automatically, same convention as RECONCILIATION_SOURCES below.
RENAMED_FIELDS = [
    ("Supplier Payment", "posting_date", "payment_date"),
    ("Vendor Payment", "posting_date", "payment_date"),
    ("Receipt", "posting_date", "payment_date"),
]


def _apply_renamed_fields():
    """Idempotently apply every (doctype, old_fieldname, new_fieldname) in
    RENAMED_FIELDS. The schema sync above (_sync_doctype_schemas_from_json)
    already added each new_fieldname column via bench migrate's own ALTER
    TABLE; this copies over any data still sitting in the orphaned old
    column, migrates Property Setters (in_list_view, in_standard_filter /
    Customize Quick Filters, insert_after, ...) and saved Report Builder /
    user list-view settings via Frappe's own rename_field(), then drops the
    old column.

    Idempotent: no-op per row once its old_fieldname column is gone from
    that table — so re-running on an already-migrated site (or a fresh site
    with old_fieldname never present) is always a safe skip.
    """
    from frappe.model.utils.rename_field import rename_field

    for doctype, old_fieldname, new_fieldname in RENAMED_FIELDS:
        try:
            if not frappe.db.table_exists(doctype):
                continue
            columns = {c[0] for c in frappe.db.sql(f"SHOW COLUMNS FROM `tab{doctype}`")}
            if old_fieldname not in columns:
                continue
            if new_fieldname not in columns:
                # Schema sync hasn't added the new column yet — retry next migrate.
                continue
            rename_field(doctype, old_fieldname, new_fieldname)
            frappe.db.sql(
                f"""
                UPDATE `tab{doctype}`
                SET `{new_fieldname}` = `{old_fieldname}`
                WHERE `{new_fieldname}` IS NULL AND `{old_fieldname}` IS NOT NULL
                """
            )
            frappe.db.sql_ddl(f"ALTER TABLE `tab{doctype}` DROP COLUMN `{old_fieldname}`")
            frappe.db.commit()
            frappe.logger().info(f"[TMS] Migrated {doctype}.{old_fieldname} -> {new_fieldname}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to rename {doctype}.{old_fieldname}")


def _ensure_purchase_invoice_document_status_field():
    """Purchase Invoice's core `status` field mixes docstatus (Draft/Submitted/
    Cancelled) together with payment states (Paid/Unpaid/Overdue) in one Select,
    and is report_hide'd in this app anyway. `custom_document_status` is a plain,
    report-visible column that only ever reflects docstatus — kept separate from
    `custom_payment_status`, which already covers the money-owed side.

    Idempotent: skips if the Custom Field already exists.
    """
    try:
        name = "Purchase Invoice-custom_document_status"
        if frappe.db.exists("Custom Field", name):
            return
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Purchase Invoice",
            "fieldname": "custom_document_status",
            "label": "Document Status",
            "fieldtype": "Select",
            "options": "\nDraft\nSubmitted\nCancelled",
            "insert_after": "custom_payment_status",
            "read_only": 1,
            "no_copy": 1,
            "in_list_view": 1,
            "in_standard_filter": 1,
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to create Purchase Invoice custom_document_status field")


def _backfill_purchase_invoice_document_status():
    """Existing Purchase Invoice rows predate `custom_document_status` and have
    it blank until their next save/submit/cancel — backfill from the real
    docstatus once so the column is populated immediately.

    Idempotent: only fills rows where the field is still blank.
    """
    try:
        if not frappe.db.table_exists("Purchase Invoice") or not frappe.db.has_column(
            "Purchase Invoice", "custom_document_status"
        ):
            return
        frappe.db.sql(
            """
            UPDATE `tabPurchase Invoice`
            SET custom_document_status = CASE docstatus
                WHEN 0 THEN 'Draft'
                WHEN 1 THEN 'Submitted'
                WHEN 2 THEN 'Cancelled'
                ELSE custom_document_status
            END
            WHERE custom_document_status IS NULL OR custom_document_status = ''
            """
        )
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Purchase Invoice custom_document_status")


def _extend_purchase_invoice_payment_status_options():
    """`custom_payment_status` originally only ever held Unpaid/Partially Paid/Paid.
    Native `status` is being hidden from the UI (see
    _hide_purchase_invoice_native_status_filter), so the business states it used
    to carry (Return/Debit Note Issued/Overdue/Internal Transfer — see
    overrides/purchase_invoice.py's _STATUS_PASSTHROUGH) now also land in this
    field; the Select field's option list needs to include them.

    Idempotent: only writes when the options string is missing an entry.
    """
    try:
        name = "Purchase Invoice-custom_payment_status"
        if not frappe.db.exists("Custom Field", name):
            return
        full_options = "Unpaid\nPartially Paid\nPaid\nOverdue\nReturn\nDebit Note Issued\nInternal Transfer"
        current = frappe.db.get_value("Custom Field", name, "options") or ""
        if set(current.split("\n")) >= set(full_options.split("\n")):
            return
        frappe.db.set_value("Custom Field", name, "options", full_options)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to extend Purchase Invoice payment status options")


def _make_supplier_email_id_editable():
    """Core ERPNext's Supplier.email_id is a "Read Only" fetch_from field fed
    one-way from supplier_primary_contact.email_id -- the only way to set it
    used to be opening the linked Contact directly. Turn it into a normal
    editable Data field so it can be typed straight on the Supplier form; the
    typed value is pushed back onto the Contact via doc_events so the two
    never drift apart (see overrides/supplier.py). fetch_from is left in place
    so it still fills email_id automatically when supplier_primary_contact
    itself is (re)selected.

    fetch_if_empty=1 is the load-bearing property setter here, not just
    fieldtype/options: Frappe's own base_input.js has a
    read_only_because_of_fetch_from() check that forces ANY field with a
    non-empty fetch_from back to read-only display -- regardless of the
    field's own fieldtype/read_only value -- for as long as the source link
    (supplier_primary_contact) has a value and fetch_if_empty is falsy. Since
    a Supplier with a Primary Contact already selected is exactly the normal
    case, changing fieldtype alone left the field looking editable in the
    metadata but still rendered read-only on screen. fetch_if_empty=1 is
    Frappe's own documented escape hatch from that check.
    """
    try:
        make_property_setter("Supplier", "email_id", "fieldtype", "Data", "Data")
        make_property_setter("Supplier", "email_id", "options", "Email", "Data")
        make_property_setter("Supplier", "email_id", "fetch_if_empty", "1", "Check")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to make Supplier.email_id editable")


def _make_customer_email_id_editable():
    """Same fix as _make_supplier_email_id_editable() above, for
    Customer.email_id / customer_primary_contact — see that function's
    docstring for why fetch_if_empty=1 is the load-bearing property setter.
    """
    try:
        make_property_setter("Customer", "email_id", "fieldtype", "Data", "Data")
        make_property_setter("Customer", "email_id", "options", "Email", "Data")
        make_property_setter("Customer", "email_id", "fetch_if_empty", "1", "Check")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to make Customer.email_id editable")


def _make_supplier_mobile_no_editable():
    """Same fix as _make_supplier_email_id_editable() above, for
    Supplier.mobile_no / supplier_primary_contact.mobile_no. `options` is
    left untouched (core leaves it unset for Supplier) — only fieldtype and
    fetch_if_empty need to change to make the field editable.
    """
    try:
        make_property_setter("Supplier", "mobile_no", "fieldtype", "Data", "Data")
        make_property_setter("Supplier", "mobile_no", "fetch_if_empty", "1", "Check")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to make Supplier.mobile_no editable")


def _make_customer_mobile_no_editable():
    """Same fix as _make_customer_email_id_editable() above, for
    Customer.mobile_no / customer_primary_contact.mobile_no.
    """
    try:
        make_property_setter("Customer", "mobile_no", "fieldtype", "Data", "Data")
        make_property_setter("Customer", "mobile_no", "fetch_if_empty", "1", "Check")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to make Customer.mobile_no editable")


def _hide_purchase_invoice_native_status_filter():
    """Native `status` mixes docstatus (Draft/Submitted/Cancelled — now its own
    `custom_document_status` column) with payment/business states (now folded
    into `custom_payment_status`) — remove it from the standard filter row so
    it stops being offered to users as a third, redundant/confusing status
    control. report_hide is already set separately via fixtures/property_setter.json.
    """
    try:
        make_property_setter("Purchase Invoice", "status", "in_standard_filter", "0", "Check")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to hide Purchase Invoice native status filter")


def _ensure_email_template_trip_type_gating():
    """Email Template's "Trip Type" field (custom_trip_type) was reqd=1 for every
    record, but only Trip templates ever have a trip type — Vendor Payment's new
    "Vendor Payment Confirmation" template (see _ensure_vendor_payment_email_template
    below) has none, and failed to insert with MandatoryError before this.

    Gate it on the "Doctype" field (reference_doctype) that Email Template
    already carries but that nothing filtered on before: visible/mandatory only
    when reference_doctype == "Trip". Trip's own dialog filtering (trip.js's
    custom_trip_type query) reads the field value directly and doesn't touch
    depends_on, so it is unaffected by this.

    Also scopes the Trip Type link dropdown to Trip Type.applies_to == "Trip"
    — Trip Type already carries this field (see _backfill_trip_type_applies_to)
    to separate Trip's own types from Amazon's, so an Email Template's trip
    type picker shouldn't offer the Amazon-only ones.

    Idempotent: only writes properties that differ from the target state, and
    only backfills reference_doctype on rows that already have a trip type set
    but no reference_doctype yet (i.e. every pre-existing Trip template).
    """
    try:
        name = "Email Template-custom_trip_type"
        if frappe.db.exists("Custom Field", name):
            target = {
                "depends_on": "eval:doc.reference_doctype=='Trip'",
                "mandatory_depends_on": "eval:doc.reference_doctype=='Trip'",
                "reqd": 0,
                "link_filters": '[["Trip Type","applies_to","=","Trip"]]',
            }
            current = frappe.db.get_value("Custom Field", name, list(target.keys()), as_dict=True)
            if any(current.get(k) != v for k, v in target.items()):
                for k, v in target.items():
                    frappe.db.set_value("Custom Field", name, k, v)
                frappe.clear_cache(doctype="Email Template")

        if frappe.db.table_exists("Email Template"):
            frappe.db.sql("""
                UPDATE `tabEmail Template`
                SET reference_doctype = 'Trip'
                WHERE IFNULL(reference_doctype, '') = ''
                  AND IFNULL(custom_trip_type, '') != ''
            """)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to gate Email Template custom_trip_type on reference_doctype")


def _remove_email_template_reference_doctype_overrides():
    """A Customize Form edit accidentally locked Email Template's "Doctype"
    field (reference_doctype) for every record — default="Trip", read_only=1
    — and separately picked up an unrelated permlevel=251 from the TMS RBAC
    system's field-protection logic, since Email Template is a TMS-managed
    doctype. That made the field permanently stuck on "Trip" everywhere,
    which breaks now that Vendor Payment (and future doctypes) also need
    their own Email Template records.

    The field must stay normal/editable everywhere except the one context
    that already knows which doctype it's for — Trip's "+ New Template"
    button, which now passes reference_doctype="Trip" as a default and gets
    it locked client-side (see public/js/email_template.js) instead of via
    a doctype-wide Property Setter.

    Idempotent: no-op once none of the three stray Property Setters remain.
    """
    try:
        names = [
            "Email Template-reference_doctype-default",
            "Email Template-reference_doctype-read_only",
            "Email Template-reference_doctype-permlevel",
        ]
        removed = False
        for name in names:
            if frappe.db.exists("Property Setter", name):
                frappe.delete_doc("Property Setter", name, ignore_permissions=True, force=True)
                removed = True
        if removed:
            frappe.clear_cache(doctype="Email Template")
            frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to remove Email Template reference_doctype overrides")


def _ensure_vendor_payment_email_template():
    """No longer called from after_migrate() — the "Vendor Payment Confirmation"
    Email Template record is now created manually via Setup > Email > Email
    Template instead of auto-seeded here. Left in place (unused) rather than
    deleted; the response_html design below is still useful as a starting
    point if the record needs to be recreated.

    The Vendor Payment submit-confirmation email design used to be a hardcoded
    Python string (logicore.utils.vendor_payment_email._EMAIL_BODY, now
    commented out there). It now lives in this standard Email Template record so
    it can be edited from Setup > Email > Email Template without a code deploy.

    reference_doctype="Vendor Payment" (not "Trip") keeps custom_trip_type
    non-mandatory here — see _ensure_email_template_trip_type_gating above.

    Idempotent (via ensure_email_template): only creates the record if it
    doesn't already exist, so edits made afterwards through the UI are never
    overwritten by a later migrate.
    """
    try:
        ensure_email_template(
            VENDOR_PAYMENT_EMAIL_TEMPLATE_NAME,
            subject="Payment Confirmation — {{ payment_no }}",
            response_html=_VENDOR_PAYMENT_EMAIL_TEMPLATE_HTML,
            reference_doctype="Vendor Payment",
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to ensure Vendor Payment Confirmation email template")


# Jinja port of the design that used to live as _EMAIL_BODY in
# utils/vendor_payment_email.py (now commented out there) — seeded onto the
# "Vendor Payment Confirmation" Email Template record by
# _ensure_vendor_payment_email_template() above. Context keys (vendor_name,
# payment_no, trips, ...) are built in vendor_payment_email.py's _send().
_VENDOR_PAYMENT_EMAIL_TEMPLATE_HTML = """
<div style="background-color:#eef1f6;padding:32px 16px;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;margin:0 auto;background-color:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);">
    <tr>
        <td style="background:linear-gradient(135deg,#0f2942 0%,#1c3f5f 60%,#0d3b66 100%);background-color:#0f2942;padding:32px 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td>
                        <span style="display:inline-block;background-color:rgba(255,255,255,0.12);color:#7ee787;font-size:11px;font-weight:700;letter-spacing:1px;padding:5px 12px;border-radius:20px;text-transform:uppercase;">&#10003; Payment Confirmed</span>
                        <div style="color:#ffffff;font-size:15px;margin-top:16px;opacity:0.85;">Amount Transferred</div>
                        <div style="color:#ffffff;font-size:34px;font-weight:700;margin-top:4px;letter-spacing:0.3px;">{{ total_transfer_amount }}</div>
                    </td>
                    <td style="text-align:right;vertical-align:top;">
                        <div style="color:#ffffff;font-size:13px;opacity:0.75;">Payment No</div>
                        <div style="color:#ffffff;font-size:16px;font-weight:600;margin-top:2px;">{{ payment_no }}</div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <tr>
        <td style="padding:32px 36px 8px 36px;">
            <p style="color:#0f172a;font-size:16px;margin:0 0 6px 0;">To <strong>{{ vendor_name }}</strong>,</p>
            <p style="color:#64748b;font-size:14px;line-height:1.6;margin:0;">We have processed a payment against the trip(s) listed below. Please find the complete breakdown for your records.</p>
        </td>
    </tr>

    <tr>
        <td style="padding:20px 36px 0 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:10px;">
                <tr>
                    <td style="padding:16px 20px;width:25%;border-right:1px solid #eef1f6;">
                        <div style="color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Payment Date</div>
                        <div style="color:#0f172a;font-size:14px;font-weight:600;margin-top:4px;">{{ payment_date }}</div>
                    </td>
                    <td style="padding:16px 20px;width:25%;border-right:1px solid #eef1f6;">
                        <div style="color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Mode of Payment</div>
                        <div style="color:#0f172a;font-size:14px;font-weight:600;margin-top:4px;">{{ mode_of_payment }}</div>
                    </td>
                    <td style="padding:16px 20px;width:50%;">
                        <div style="color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Reference No</div>
                        <div style="color:#0f172a;font-size:14px;font-weight:600;margin-top:4px;">{{ reference_no }}</div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <tr>
        <td style="padding:24px 36px 0 36px;">
            <div style="color:#0f172a;font-size:14px;font-weight:700;margin-bottom:10px;">Trip Breakdown</div>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:12.5px;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
                <thead>
                    <tr style="background-color:#0f2942;">
                        <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Trip No</th>
                        <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">LR No</th>
                        <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Trip Date</th>
                        <th style="padding:10px 12px;text-align:left;color:#ffffff;font-weight:600;">Vehicle No</th>
                        <th style="padding:10px 12px;text-align:right;color:#ffffff;font-weight:600;">Hire Amount</th>
                        <th style="padding:10px 12px;text-align:right;color:#ffffff;font-weight:600;">TDS</th>
                        <th style="padding:10px 12px;text-align:right;color:#ffffff;font-weight:600;">LR Money</th>
                        <th style="padding:10px 12px;text-align:right;color:#ffffff;font-weight:600;">Paid Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in trips %}
                    <tr style="background-color:{{ loop.cycle('#ffffff', '#f8fafc') }};">
                        <td style="padding:10px 12px;font-weight:600;color:#1e293b;">{{ row.trip_no }}</td>
                        <td style="padding:10px 12px;color:#475569;">{{ row.lr_no }}</td>
                        <td style="padding:10px 12px;color:#475569;">{{ row.trip_date }}</td>
                        <td style="padding:10px 12px;color:#475569;">{{ row.vehicle_no }}</td>
                        <td style="padding:10px 12px;text-align:right;color:#475569;">{{ row.hire_amount }}</td>
                        <td style="padding:10px 12px;text-align:right;color:#475569;">{{ row.tds_amount }}</td>
                        <td style="padding:10px 12px;text-align:right;color:#475569;">{{ row.lr_money }}</td>
                        <td style="padding:10px 12px;text-align:right;font-weight:700;color:#0f172a;">{{ row.paid_amount }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </td>
    </tr>

    <tr>
        <td style="padding:24px 36px 0 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;border-radius:10px;">
                <tr>
                    <td style="padding:18px 22px;">
                        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="color:#64748b;font-size:13px;padding:3px 0;">Total Payment Amount</td>
                                <td style="color:#334155;font-size:13px;padding:3px 0;text-align:right;">{{ total_payment_amount }}</td>
                            </tr>
                            <tr>
                                <td style="color:#64748b;font-size:13px;padding:3px 0;">Total TDS Deducted</td>
                                <td style="color:#334155;font-size:13px;padding:3px 0;text-align:right;">{{ total_tds_amount }}</td>
                            </tr>
                            <tr>
                                <td style="color:#64748b;font-size:13px;padding:3px 0;">Total LR Money</td>
                                <td style="color:#334155;font-size:13px;padding:3px 0;text-align:right;">{{ total_lr_money }}</td>
                            </tr>
                            <tr>
                                <td colspan="2" style="border-top:1px solid #e2e8f0;padding-top:10px;margin-top:8px;"></td>
                            </tr>
                            <tr>
                                <td style="color:#0f172a;font-size:15px;font-weight:700;padding-top:6px;">Total Transfer Amount</td>
                                <td style="color:#0d3b66;font-size:19px;font-weight:800;padding-top:6px;text-align:right;">{{ total_transfer_amount }}</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <tr>
        <td style="padding:24px 36px 32px 36px;">
            <p style="color:#94a3b8;font-size:12px;line-height:1.6;margin:0;border-top:1px solid #eef1f6;padding-top:16px;">
                This is a system-generated payment confirmation. Please contact us if you notice any discrepancy in the above details.
            </p>
        </td>
    </tr>

    <tr>
        <td style="background-color:#0f2942;padding:26px 36px;text-align:center;">
            <p style="margin:0 0 12px 0;font-size:11px;color:#93a5bd;letter-spacing:0.5px;text-transform:uppercase;">Sent automatically by</p>
            <a href="https://www.logicore.com/products" target="_blank" style="display:inline-block;background-color:#ffffff;color:#0d3b66;font-weight:800;font-size:14px;letter-spacing:0.2px;text-decoration:none;padding:10px 22px;border-radius:999px;">LogiCore &rarr;</a>
            <p style="margin:14px 0 0 0;font-size:11px;color:#5a7591;">Transforming Logistics with ERP &amp; Automation</p>
        </td>
    </tr>
</table>
</div>
"""


# Doctypes with a "New Purchase / In Stock Use" entry_type field, each backed
# by its own stock Item Group — add new (item_group, doctype) pairs here as
# more expense doctypes (Urea, etc.) gain the same stock-issue pattern instead
# of writing new per-doctype ensure/backfill functions.
STOCK_ISSUE_EXPENSE_DOCTYPES = [
    ("Battery", "Battery Expenses"),
    ("Tyre", "Tyre Expenses"),
    ("Fuel and Urea", "Fuel Urea Expenses"),
]


def _ensure_item_group(item_group_name):
    """Create a top-level stock Item Group once if missing — the "In Stock
    Use" flow's Item/tyre_item Link query filters scope to this group so only
    relevant Items are offered.

    Idempotent: skips if the Item Group already exists.
    """
    try:
        if frappe.db.exists("Item Group", item_group_name):
            return
        parent = "All Item Groups" if frappe.db.exists("Item Group", "All Item Groups") else None
        frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": item_group_name,
            "parent_item_group": parent,
            "is_group": 0,
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Failed to ensure {item_group_name} Item Group")


def _backfill_entry_type(doctype, default="New Purchase"):
    """A doctype gained a required `entry_type` field (New Purchase / In Stock
    Use). Existing records predate it and have it blank, which would force a
    re-save before they could otherwise be opened/saved.

    Idempotent: only fills rows where entry_type is still blank.
    """
    try:
        if not frappe.db.table_exists(doctype) or not frappe.db.has_column(doctype, "entry_type"):
            return
        frappe.db.sql(
            f"""
            UPDATE `tab{doctype}`
            SET entry_type = %(default)s
            WHERE entry_type IS NULL OR entry_type = ''
            """,
            {"default": default},
        )
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Failed to backfill {doctype} entry_type")


def _ensure_stock_issue_expense_setup():
    """Runs _ensure_item_group + _backfill_entry_type for every doctype in
    STOCK_ISSUE_EXPENSE_DOCTYPES — the single place to wire up a new expense
    doctype's stock-issue pattern instead of duplicating install steps.
    """
    for item_group, doctype in STOCK_ISSUE_EXPENSE_DOCTYPES:
        _ensure_item_group(item_group)
        _backfill_entry_type(doctype)


def _backfill_expense_payment_date():
    """Repair Expenses and Fuel Urea Expenses gained a `payment_date` field so
    Bank Reconciliation can match on the actual payment date instead of the
    expense's `date`. Records created before this field existed have it blank,
    which would leave them unmatched — backfill from `date` once.

    Idempotent: only fills rows where payment_date is still NULL.
    """
    try:
        for doctype in ("Repair Expenses", "Fuel Urea Expenses"):
            if not frappe.db.table_exists(doctype) or not frappe.db.has_column(doctype, "payment_date"):
                continue
            frappe.db.sql(
                f"""
                UPDATE `tab{doctype}`
                SET payment_date = date
                WHERE payment_date IS NULL AND date IS NOT NULL
                """
            )
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill expense payment_date")


def _backfill_employee_user_default_company():
    """Payment/Supplier Payment's `company` field no longer carries a hardcoded
    default — it now relies on Frappe's own user-default lookup, which
    overrides/employee.py.sync_user_default_company() keeps in sync going
    forward on every Employee save. Existing Employee/User links predate that
    hook, so run the same sync once for all of them here.

    Idempotent: sync_user_default_company() is a no-op when the value already
    matches.
    """
    try:
        from logicore.overrides.employee import sync_user_default_company

        employees = frappe.get_all(
            "Employee",
            filters={"user_id": ("is", "set"), "company": ("is", "set")},
            fields=["name", "user_id", "company"],
        )
        for employee in employees:
            sync_user_default_company(employee)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Employee user default company")


def _backfill_driver_payment_date():
    """Fuel Urea Expenses gained a separate `driver_payment_date` field so Bank
    Reconciliation can match the driver incentive leg on its own real payment
    date instead of reusing the fuel/supplier `payment_date` (the two are often
    paid on different dates). Records created before this field existed have it
    blank — backfill from `payment_date` once, since that's the date those rows
    were actually reconciled against.

    Idempotent: only fills rows where driver_payment_date is still NULL.
    """
    try:
        if not frappe.db.table_exists("Fuel Urea Expenses") or not frappe.db.has_column(
            "Fuel Urea Expenses", "driver_payment_date"
        ):
            return
        frappe.db.sql(
            """
            UPDATE `tabFuel Urea Expenses`
            SET driver_payment_date = payment_date
            WHERE driver_payment_date IS NULL AND payment_date IS NOT NULL
            """
        )
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Fuel Urea Expenses driver_payment_date")


def _backfill_trip_type_applies_to():
    """Trip Type gained an `applies_to` (Trip/Amazon) Select so the Trip and
    Amazon Trip forms only offer the trip types relevant to each. Existing
    records default to "Trip" (the JSON field default), which is wrong for
    the two types actually used on Amazon Trip — fix those explicitly.

    Idempotent: only touches rows that still have the wrong value.
    """
    try:
        if not frappe.db.exists("DocType", "Trip Type"):
            return
        amazon_types = ["SCHEDULED TRIP", "SPOT & CONTRACT TRIP"]
        for name in amazon_types:
            if frappe.db.exists("Trip Type", name) and frappe.db.get_value("Trip Type", name, "applies_to") != "Amazon":
                frappe.db.set_value("Trip Type", name, "applies_to", "Amazon", update_modified=False)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Trip Type applies_to")


def _backfill_business_format_applies_to():
    """Business Format gained an `applies_to` (Trip/Amazon) Select so the Trip
    and Amazon Trip forms only offer the business formats relevant to each.
    Existing records default to "Trip" (the JSON field default), which is
    wrong for the three Amazon-specific formats — fix those explicitly.

    Idempotent: only touches rows that still have the wrong value.
    """
    try:
        if not frappe.db.exists("DocType", "Business Format"):
            return
        amazon_formats = ["AMAZON", "AMAZON FREIGHT", "AMAZON NOW"]
        for name in amazon_formats:
            if frappe.db.exists("Business Format", name) and frappe.db.get_value("Business Format", name, "applies_to") != "Amazon":
                frappe.db.set_value("Business Format", name, "applies_to", "Amazon", update_modified=False)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Business Format applies_to")


def _restore_managed_doctype_permissions():
    """Reload app-owned managed DocTypes so native DocPerm rows win again.

    Older TMS sync code updated tabDocPerm directly. That should never happen for
    shared/system roles, so on install/migrate we restore app doctype metadata
    from JSON, remove broad default-role Custom DocPerm rows that bypass TMS
    groups, and then ensure protected admin-role Custom DocPerm rows exist only
    as a fallback mirror.
    """
    try:
        doctype_root = Path(frappe.get_app_path("logicore", "logicore", "doctype"))
        managed = _get_managed_doctypes()

        for doctype in managed:
            scrubbed = frappe.scrub(doctype)
            json_path = doctype_root / scrubbed / f"{scrubbed}.json"
            if json_path.is_file():
                frappe.reload_doc(
                    "logicore",
                    "doctype",
                    scrubbed,
                    force=True,
                    reset_permissions=True,
                )

        _remove_broad_default_role_docperms(managed)
        _ensure_protected_role_permissions(managed)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to restore managed doctype permissions")


def _sync_baseline_group_permissions_all():
    """Grant BASELINE_ALWAYS_GRANTED_DOCTYPES full access to every active TMS User
    Group role. Runs on every install/migrate so existing groups (created before
    this feature, or via fixtures) converge automatically -- no one-time patch
    needed. New groups also get this from TMSUserGroup.on_update().
    """
    try:
        _ensure_baseline_group_permissions()
        _ensure_protected_role_permissions(BASELINE_ALWAYS_GRANTED_DOCTYPES)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to sync TMS baseline group permissions")


def _resync_custom_docperms_from_matrix_all():
    """Re-sync every active group's Custom DocPerm from its own permissions matrix.

    Needed for doctypes removed from BASELINE_ALWAYS_GRANTED_DOCTYPES (e.g. UOM,
    already managed via the main matrix under Masters) — the old baseline sync had
    force-granted full access, silently overriding the matrix. That stale
    full-access row won't self-correct just by removing the doctype from the
    list, so this makes existing groups converge automatically on every migrate,
    without a one-time patch.
    """
    try:
        for g in frappe.get_all("TMS User Group", fields=["name", "group_name"]):
            role = g["group_name"]
            if role in FRAPPE_SYSTEM_ROLES:
                continue
            if frappe.db.get_value("Role", role, "disabled"):
                continue
            group = frappe.get_doc("TMS User Group", g["name"])
            group._sync_custom_docperms()
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to resync TMS custom docperms from matrix")


def _assign_field_permlevels_and_backfill():
    """Give every already-`read_only=1` field on a managed doctype its own unique
    permlevel, up front, so it is immediately controllable (Hidden) from the TMS User
    Group field-permission popup.

    Runs on every `bench migrate` (not a one-time patch, per this app's convention) but
    is cheap and fully idempotent: _assign_permlevel_for_field() itself checks for an
    existing Property Setter first and no-ops if the field already has a permlevel, so
    a field is only ever touched once across the site's lifetime.

    "Normal" (not already read-only) fields deliberately do NOT get a permlevel here --
    they only get one lazily, the first time an admin actually restricts them via
    save_field_permissions(), keeping this migrate step small and bounded regardless of
    how many total fields the managed doctypes have.
    """
    try:
        for doctype in _get_managed_doctypes():
            try:
                meta = frappe.get_meta(doctype)
            except Exception:
                continue
            for df in meta.fields:
                if (
                    df.fieldtype in LAYOUT_FIELDTYPES
                    or df.fieldname in EXCLUDED_SYSTEM_FIELDNAMES
                    or df.hidden
                    or not df.read_only
                    or is_permlevel_protected_field(doctype, df.fieldname)
                ):
                    continue
                _assign_permlevel_for_field(doctype, df.fieldname)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to assign field permlevels")


def _clear_permlevel_on_sort_fields():
    """Undo any permlevel already assigned to a doctype's sort_field.

    The sort_field lands in ORDER BY on every list query, and Frappe throws
    PermissionError on an unpermitted order-by field instead of dropping it, so a
    gated sort_field takes down the entire list view for any role missing a grant at
    that permlevel -- it never just hides a column. Trip.tcntrip_date was gated this
    way and broke Trip for a whole user group. Runs every migrate (this app's
    convention over one-time patches) and is a no-op once clean.
    """
    try:
        for doctype in _get_managed_doctypes():
            try:
                meta = frappe.get_meta(doctype)
            except Exception:
                continue
            sort_field = (meta.sort_field or "").strip()
            if not sort_field:
                continue
            ps = frappe.db.get_value(
                "Property Setter",
                {"doc_type": doctype, "field_name": sort_field, "property": "permlevel"},
                ["name", "value"],
                as_dict=True,
            )
            if not ps:
                continue
            permlevel = frappe.utils.cint(ps.value)
            frappe.delete_doc("Property Setter", ps.name, ignore_permissions=True, force=True)
            if permlevel:
                # Each field owns a unique permlevel, so every row at this level
                # belonged to this field alone and is now orphaned.
                frappe.db.delete("Custom DocPerm", {"parent": doctype, "permlevel": permlevel})
                frappe.db.sql(
                    "DELETE FROM `tabTMS User Group Field Permission` "
                    "WHERE document_type=%s AND fieldname=%s",
                    (doctype, sort_field),
                )
        frappe.db.commit()
        frappe.clear_cache()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to clear sort_field permlevels")


def _cleanup_orphaned_permlevel_artifacts():
    """Delete permlevel Property Setters (and their Custom DocPerm rows) whose DocType
    or field no longer exists on this site.

    A Property Setter outlives the schema it points at. Fixtures exported from a site
    where a feature IS installed get imported onto a site where it is NOT -- that is
    how `TMS Bank Reconciliation-*-permlevel` rows reached Sadashiv-Live, whose branch
    has no such doctype. `frappe.get_meta()` then raises DoesNotExistError, and the
    live symptom was a hard "DocType TMS Bank Reconciliation not found" popup on every
    TMS User Group save. _ensure_field_permlevel_baseline_for_role() now guards against
    that, but the guard only stops the crash -- these rows still squat on permlevel
    numbers forever. This removes the cause.

    Scoped to property='permlevel' on purpose: those are the only Property Setters this
    app creates (_assign_permlevel_for_field), so nothing here can touch a Property
    Setter belonging to Frappe, ERPNext or India Compliance. Equally important, it is
    driven entirely by what exists on THIS site -- on the Reconsulation-Tms branch the
    reconciliation doctypes are present, so their rows are correctly left alone.
    """
    try:
        rows = frappe.get_all(
            "Property Setter",
            filters={"doctype_or_field": "DocField", "property": "permlevel"},
            fields=["name", "doc_type", "field_name", "value"],
        )
        for row in rows:
            if not frappe.db.exists("DocType", row.doc_type):
                stale = True
            else:
                try:
                    stale = not frappe.get_meta(row.doc_type).get_field(row.field_name)
                except Exception:
                    stale = True
            if not stale:
                continue

            permlevel = frappe.utils.cint(row.value)
            frappe.delete_doc("Property Setter", row.name, ignore_permissions=True, force=True)
            if permlevel:
                # Every field owns a unique permlevel, so all rows at this level
                # belonged to this one dead field.
                frappe.db.delete("Custom DocPerm", {"parent": row.doc_type, "permlevel": permlevel})
                frappe.db.sql(
                    "DELETE FROM `tabTMS User Group Field Permission` "
                    "WHERE document_type=%s AND fieldname=%s",
                    (row.doc_type, row.field_name),
                )
        frappe.db.commit()
        frappe.clear_cache()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to clean orphaned permlevel artifacts")


# Fields the TMS bank reconciliation feature adds. Named explicitly rather than
# matched on "reconcil" because Purchase Invoice also carries India Compliance's own
# `reconciliation_status` and `itc_claim_period`, and ERPNext has Stock Reconciliation
# and Purchase Reconciliation Tool -- a substring match would delete those too.
TMS_RECONCILIATION_FIELDNAMES = (
    "custom_bank_reconciliation_status",
    "custom_reconciled_amount",
    "is_reconciled",
    "bank_reconciliation",
    "is_reconciled_driver",
    "bank_reconciliation_driver",
)


def _remove_reconciliation_fields_when_feature_absent():
    """Strip TMS bank reconciliation Custom Fields from sites that don't have the feature.

    The feature lives only on the Reconsulation-Tms branch, but `bench export-fixtures`
    run against a site where it IS installed baked its Custom Fields into
    fixtures/custom_field.json, and every deploy of Sadashiv-Live then created them on
    live -- Purchase Invoice showed "Bank Reconciliation Status" and "Reconciled Amount"
    with no code behind them. Removing the fixture entries doesn't undo that: Frappe
    fixtures never delete records they no longer list.

    The presence of the `TMS Bank Reconciliation` doctype is the switch. Where the
    feature is really installed nothing is touched; where it isn't, its leftovers go.

    Only the Custom Field definitions are dropped, not the underlying table columns --
    the fields vanish from every form and list, and any data already written stays
    recoverable if this branch ever merges the feature.
    """
    try:
        if frappe.db.exists("DocType", "TMS Bank Reconciliation"):
            return

        for row in frappe.get_all(
            "Custom Field",
            filters={"fieldname": ["in", TMS_RECONCILIATION_FIELDNAMES]},
            fields=["name", "dt", "fieldname"],
        ):
            frappe.delete_doc("Custom Field", row.name, ignore_permissions=True, force=True)

        # Property Setters on those fields (any property, not just permlevel -- the
        # permlevel ones are already gone via _cleanup_orphaned_permlevel_artifacts,
        # but in_list_view/read_only/label overrides can linger just as orphaned).
        for row in frappe.get_all(
            "Property Setter",
            filters={"field_name": ["in", TMS_RECONCILIATION_FIELDNAMES]},
            fields=["name"],
        ):
            frappe.delete_doc("Property Setter", row.name, ignore_permissions=True, force=True)

        frappe.db.commit()
        frappe.clear_cache()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to remove reconciliation fields")


def _sync_all_tms_user_group_sidebars():
    """Add any new sidebar doctypes to every TMS User Group permission matrix.

    Reads managed doctypes from the DB (Workspace Sidebar is already imported by
    the time after_migrate runs), so new sidebar entries are picked up without
    needing to read fixture files directly.
    """
    try:
        managed = set(_get_managed_doctypes())
        if not managed:
            return

        groups = frappe.get_all("TMS User Group", pluck="name")
        for group_name in groups:
            doc = frappe.get_doc("TMS User Group", group_name)
            existing = {row.document_type for row in (doc.permissions or [])}
            added = False
            for doctype in managed:
                if doctype not in existing:
                    module = frappe.db.get_value("DocType", doctype, "module") or ""
                    doc.append("permissions", {
                        "module": module,
                        "document_type": doctype,
                        "perm_read": 0,
                        "perm_write": 0,
                        "perm_create": 0,
                        "perm_delete": 0,
                        "perm_print": 0,
                        "perm_report": 0,
                        "perm_import": 0,
                        "perm_export": 0,
                        "perm_select": 0,
                    })
                    added = True
            if added:
                doc.save(ignore_permissions=True)

        frappe.db.commit()
        frappe.logger().info(f"Synced sidebar doctypes for {len(groups)} TMS User Groups")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to sync TMS User Group sidebar doctypes")


def _remove_broad_default_role_docperms(managed):
    """Remove Custom DocPerm rows that would apply TMS access to every user."""
    if not managed:
        return

    frappe.db.delete(
        "Custom DocPerm",
        {
            "parent": ["in", list(managed)],
            "role": ["in", ["All", "Guest", "Desk User"]],
        },
    )


def _cleanup_zero_only_custom_docperms():
    """Remove Custom DocPerm rows that block native access without granting any.

    Frappe rule: if ANY Custom DocPerm row exists for a doctype, Frappe ignores ALL
    file-based DocPerm rows for that doctype — across every role including Administrator
    and System Manager. So a single read=0 row blocks everyone.

    This function finds non-TMS-managed doctypes where every Custom DocPerm row has
    read=0 (nobody gets access via Custom DocPerm) and deletes those rows, restoring
    native DocPerm behaviour (System Manager / Administrator regain access).

    ERPNext and HRMS create these zero rows at install time for roles like
    "Employee Self Service" on core Frappe doctypes (Role, DocType, etc.).
    TMS does not manage those doctypes, so deleting the rows is safe.
    """
    try:
        managed = set(_get_managed_doctypes())

        # Doctypes where every Custom DocPerm row has read=0 → nobody has any access
        blocked = frappe.db.sql(
            """
            SELECT parent
            FROM `tabCustom DocPerm`
            WHERE permlevel = 0
            GROUP BY parent
            HAVING MAX(`read`) = 0
            """,
            as_list=True,
        )
        blocked_doctypes = [row[0] for row in blocked if row[0] not in managed]

        if not blocked_doctypes:
            return

        frappe.db.sql(
            f"""
            DELETE FROM `tabCustom DocPerm`
            WHERE parent IN ({','.join(['%s'] * len(blocked_doctypes))})
            AND permlevel = 0
            """,
            blocked_doctypes,
        )
        frappe.clear_cache(doctype="Custom DocPerm")
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to cleanup zero-only Custom DocPerm rows")


def _export_fixtures():
    """Auto-export all app fixtures after migrate so JSON changes sync to database."""
    try:
        from frappe.utils.fixtures import export_fixtures as export_fn

        export_fn(app="logicore")
        frappe.logger().info("Exported fixtures for logicore")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to auto-export fixtures")


def _backfill_address_display_fields():
    """Populate origin/destination address full-text fields for trips where they are empty.

    Idempotent — only processes rows where the address name is set but the
    display text is still blank, so re-running on future migrates is a no-op.
    """
    try:
        # Skip silently if columns don't exist yet (first migrate before schema sync)
        cols = frappe.db.sql("SHOW COLUMNS FROM `tabTrip` LIKE 'origin_address_1_full'")
        if not cols:
            return

        from logicore.logicore.doctype.trip.trip import custom

        trips = frappe.db.sql("""
            SELECT name, origin_address_1, origin_address_2,
                   destination_address_1, destination_address_2
            FROM `tabTrip`
            WHERE (
                (origin_address_1      IS NOT NULL AND origin_address_1      != '' AND (origin_address_1_full      IS NULL OR origin_address_1_full      = ''))
             OR (origin_address_2      IS NOT NULL AND origin_address_2      != '' AND (origin_address_2_full      IS NULL OR origin_address_2_full      = ''))
             OR (destination_address_1 IS NOT NULL AND destination_address_1 != '' AND (destination_address_1_full IS NULL OR destination_address_1_full = ''))
             OR (destination_address_2 IS NOT NULL AND destination_address_2 != '' AND (destination_address_2_full IS NULL OR destination_address_2_full = ''))
            )
        """, as_dict=True)

        if not trips:
            return

        for trip in trips:
            updates = {}
            for addr_field, display_field in [
                ("origin_address_1",      "origin_address_1_full"),
                ("origin_address_2",      "origin_address_2_full"),
                ("destination_address_1", "destination_address_1_full"),
                ("destination_address_2", "destination_address_2_full"),
            ]:
                addr_name = trip.get(addr_field)
                if addr_name:
                    updates[display_field] = custom(addr_name)
            if updates:
                frappe.db.set_value("Trip", trip["name"], updates, update_modified=False)

        frappe.db.commit()
        frappe.logger().info(f"[TMS] Backfilled address display fields for {len(trips)} trips.")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill address display fields")


def _ensure_tms_quick_filter_custom_fields():
    """Global (all-users) storage for the TMS-gated "Customize Quick Filters" override.

    Real (non-child) doctype fields are toggled via a Property Setter on
    in_standard_filter instead (already global by nature) — this Code field only
    holds the child-table field selections. The Check field marks a doctype as
    already processed by _migrate_tms_admin_quick_filters_to_global so that
    one-off migration never re-runs. See tms_quick_filters.py.
    """
    try:
        field_defs = [
            {
                "fieldname": "tms_quick_filter_fields",
                "label": "TMS Quick Filter Fields",
                "fieldtype": "Code",
                "insert_after": "fields",
            },
            {
                "fieldname": "tms_quick_filters_migrated",
                "label": "TMS Quick Filters Migrated",
                "fieldtype": "Check",
                "insert_after": "tms_quick_filter_fields",
            },
        ]
        for field_def in field_defs:
            name = f"List View Settings-{field_def['fieldname']}"
            if frappe.db.exists("Custom Field", name):
                continue
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "List View Settings",
                "hidden": 1,
                "no_copy": 1,
                **field_def,
            }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to create TMS quick filter custom fields")


def _migrate_tms_admin_quick_filters_to_global():
    """Carry over quick filters a TMS Admin had already set (per-user, via Frappe's stock
    per-user User Settings) into the new global store, so normal users see continuity
    instead of a reset to blank after this feature ships.

    Idempotent via the tms_quick_filters_migrated marker on List View Settings — once a
    doctype is marked, this never touches it again, even if an admin later clears all
    filters through the new UI.
    """
    try:
        from logicore.tms_list_settings import _get_users_assigned_to_group
        from logicore.tms_quick_filters import (
            is_filterable_fieldtype,
            _set_parent_standard_filters,
        )

        admin_users = []
        seen = set()

        def _add(user):
            if user and user not in seen:
                admin_users.append(user)
                seen.add(user)

        _add("Administrator")
        for user in sorted(frappe.get_all(
            "Has Role", filters={"role": "System Manager", "parenttype": "User"}, pluck="parent"
        )):
            _add(user)
        for group in sorted(frappe.get_all(
            "TMS User Group", filters={"is_admin": 1, "is_active": 1}, pluck="name"
        )):
            for user in sorted(_get_users_assigned_to_group(group)):
                _add(user)

        if not admin_users:
            return

        for user in admin_users:
            rows = frappe.db.sql(
                "SELECT `doctype`, `data` FROM `__UserSettings` WHERE `user`=%s",
                (user,),
                as_dict=True,
            )
            for row in rows:
                doctype = row.doctype
                if doctype == "List View Settings":
                    # __UserSettings can carry a row keyed by this doctype's own
                    # name (e.g. an admin opened its list view) — self-migrating
                    # it means loading/saving a "List View Settings" doc named
                    # "List View Settings", which throws DoesNotExistError.
                    continue
                if not frappe.db.exists("DocType", doctype):
                    continue
                if frappe.db.get_value("List View Settings", doctype, "tms_quick_filters_migrated"):
                    continue

                try:
                    data = json.loads(row.data or "{}")
                except ValueError:
                    continue

                group_by_fields = data.get("group_by_fields") or []
                if group_by_fields:
                    meta = frappe.get_meta(doctype)
                    valid_fields = [
                        f for f in group_by_fields
                        if meta.has_field(f) and is_filterable_fieldtype(meta.get_field(f).fieldtype)
                    ]
                    if valid_fields:
                        _set_parent_standard_filters(doctype, valid_fields)

                if frappe.db.exists("List View Settings", doctype):
                    doc = frappe.get_doc("List View Settings", doctype)
                else:
                    doc = frappe.new_doc("List View Settings")
                    doc.name = doctype
                doc.tms_quick_filters_migrated = 1
                doc.save(ignore_permissions=True)

        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to migrate TMS admin quick filters to global")


def _remove_company_type_custom_fields():
    """Drop the old "Company Type" / Seller / Society custom fields on Company.

    These were added directly through Customize Form (never fixture-tracked) and
    are no longer wanted. Runs on every migrate so any site that still has them
    (e.g. live) converges automatically on deploy — no manual cleanup needed.
    """
    try:
        for cf_name in (
            "Company-custom_seller",
            "Company-custom_society",
            "Company-custom_company_type",
        ):
            if frappe.db.exists("Custom Field", cf_name):
                frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True, force=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to remove Company Type custom fields")


def _remove_purchase_invoice_duplicate_purchase_date_field():
    """Drop the duplicate "Purchase Date" custom field on Purchase Invoice.

    `custom_purchase_date` was added directly through Customize Form and
    duplicated the standard `posting_date` field, which is already relabeled
    "Purchase Date" via a Property Setter. Runs on every migrate so any site
    that still has it converges automatically on deploy.
    """
    try:
        cf_name = "Purchase Invoice-custom_purchase_date"
        if frappe.db.exists("Custom Field", cf_name):
            frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True, force=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to remove duplicate Purchase Invoice date field")


def _clear_purchase_invoice_warehouse_default():
    """Remove the Customize Form default setter from Set Accepted Warehouse.

    New Purchase Invoices get this value from Stock Settings instead. Runs on
    every install/migrate so old Customize Form values cannot override it.
    """
    try:
        property_setter = "Purchase Invoice-set_warehouse-default"
        if frappe.db.exists("Property Setter", property_setter):
            frappe.delete_doc("Property Setter", property_setter, ignore_permissions=True, force=True)
            frappe.clear_cache(doctype="Purchase Invoice")
            frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to clear Purchase Invoice warehouse default")


def _ensure_check_supplier_invoice_uniqueness():
    """Switch on ERPNext's own duplicate-supplier-invoice-number check (Accounts
    Settings.check_supplier_invoice_uniqueness) — Supplier Payment fetches unpaid
    Purchase Invoices by `bill_no`, so two invoices from the same supplier
    sharing a Supplier Invoice No in the same fiscal year would be
    indistinguishable to accounts staff. ERPNext already implements this check
    in PurchaseInvoice.validate_supplier_invoice(); it just ships turned off.

    Idempotent — no-ops once the setting is already 1.
    """
    try:
        if frappe.db.get_single_value("Accounts Settings", "check_supplier_invoice_uniqueness"):
            return
        frappe.db.set_single_value("Accounts Settings", "check_supplier_invoice_uniqueness", 1)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to enable check_supplier_invoice_uniqueness")


def _backfill_purchase_invoice_payment_status():
    """Give every already-submitted Purchase Invoice a starting
    custom_payment_status of "Unpaid" (with custom_total_paid=0 and
    custom_balance_amount=grand_total) so Supplier Payment's fetch filter
    (`custom_payment_status in [Unpaid, Partially Paid]`) finds it. Without
    this, an invoice submitted before Supplier Payment existed has a NULL
    status and never matches the filter.

    Idempotent — only touches rows where custom_payment_status is still NULL,
    so a re-run (or running before the schema is migrated) is a safe no-op.
    """
    try:
        cols = frappe.db.sql("SHOW COLUMNS FROM `tabPurchase Invoice` LIKE 'custom_payment_status'")
        if not cols:
            return

        rows = frappe.db.sql(
            """
            SELECT name, grand_total FROM `tabPurchase Invoice`
            WHERE docstatus = 1 AND (custom_payment_status IS NULL OR custom_payment_status = '')
            """,
            as_dict=True,
        )
        if not rows:
            return

        for row in rows:
            frappe.db.set_value("Purchase Invoice", row.name, {
                "custom_payment_status": "Unpaid",
                "custom_total_paid": 0,
                "custom_balance_amount": row.grand_total,
            }, update_modified=False)

        frappe.db.commit()
        frappe.logger().info(f"[TMS] Backfilled custom_payment_status for {len(rows)} Purchase Invoice(s).")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Purchase Invoice payment status")


def _backfill_receipt_trip_vehicle_no():
    """Populate vehicle_no on existing Customer Receipt Trip rows from their linked Trip.

    The field was added with fetch_from="trip.vehicle_no", which only populates on
    save / trip-change in the form -- rows already saved before this field existed
    are left NULL. Runs on every migrate (this app's convention over one-time
    patches) and only touches rows still blank, so it is idempotent. A raw column
    update, not gated by docstatus, so it covers Draft and Submitted Receipts alike.
    """
    try:
        cols = frappe.db.sql("SHOW COLUMNS FROM `tabCustomer Receipt Trip` LIKE 'vehicle_no'")
        if not cols:
            return

        frappe.db.sql("""
            UPDATE `tabCustomer Receipt Trip` crt
            INNER JOIN `tabTrip` t ON t.name = crt.trip
            SET crt.vehicle_no = t.vehicle_no
            WHERE (crt.vehicle_no IS NULL OR crt.vehicle_no = '')
              AND t.vehicle_no IS NOT NULL AND t.vehicle_no != ''
        """)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Customer Receipt Trip vehicle_no")


def _enable_eway_bill_lookup_on_existing_settings():
    """Switch on `enabled` for Eway Bill Settings rows that predate the field.

    Frappe applies a field's `default` only to newly created documents, so adding
    the `enabled` Check left every already-saved row at 0 -- silently killing the
    Trip E-Way Bill lookup on sites that had it working. Unlike the other
    backfills here this one is guarded by a marker instead of running every
    migrate, because a 0 means both "never set" and "an admin deliberately turned
    it off", and the latter must never be flipped back on.
    """
    try:
        if not frappe.db.has_column("Eway Bill Settings", "enabled"):
            return
        if frappe.db.get_default("eway_bill_enabled_backfilled"):
            return

        frappe.db.sql("UPDATE `tabEway Bill Settings` SET enabled = 1")
        frappe.db.set_default("eway_bill_enabled_backfilled", "1")
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Eway Bill Settings enabled")


# The exact options the Compliances.document_type Select field used to carry,
# before it became a Link to Compliance Document Type. Existing Compliances rows
# already store these strings as plain text, so master records with these same
# names keep old data valid without any data migration.
COMPLIANCE_DOCUMENT_TYPES = [
    "RC",
    "Insurance",
    "Fitness",
    "State Permit",
    "National Permit",
    "PUC",
    "Government Charges",
    "Road Tax",
    "Vehicle Permit",
]


def _seed_compliance_document_types():
    """Ensure every legacy Compliances.document_type option exists as a
    Compliance Document Type master record.

    Runs on every migrate (this app's convention over one-time patches) so any
    site -- a teammate's pull, or Frappe Cloud/live -- converges automatically on
    deploy. Idempotent: only inserts records that don't already exist.
    """
    try:
        if not frappe.db.exists("DocType", "Compliance Document Type"):
            return
        for name in COMPLIANCE_DOCUMENT_TYPES:
            # Matched on the document_name field, not the docname (name) -- the
            # doctype autonames on "hash", so document_name is just a normal,
            # freely-editable field and is the only reliable natural key here.
            if frappe.db.exists("Compliance Document Type", {"document_name": name}):
                continue
            frappe.get_doc({
                "doctype": "Compliance Document Type",
                "document_name": name,
            }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to seed Compliance Document Type records")


def _ensure_supplier_payment_reconciliation():
    """Wire Supplier Payment into TMS Bank Reconciliation, and give Purchase
    Invoice the two fields that its reconciliation state rolls up into.

    Three idempotent steps: the Purchase Invoice custom fields, the "Supplier
    Payment" TMS Reconciliation Source leg, and a one-time backfill so invoices
    that predate this feature read "Unreconciled" instead of blank.
    """
    try:
        field_defs = [
            {
                "fieldname": "custom_bank_reconciliation_status",
                "label": "Bank Reconciliation Status",
                "fieldtype": "Select",
                "options": "\nUnreconciled\nPartially Reconciled\nReconciled",
                "default": "Unreconciled",
                "insert_after": "custom_payment_status",
            },
            {
                "fieldname": "custom_reconciled_amount",
                "label": "Reconciled Amount (INR)",
                "fieldtype": "Currency",
                "insert_after": "custom_bank_reconciliation_status",
            },
        ]
        for field_def in field_defs:
            name = f"Purchase Invoice-{field_def['fieldname']}"
            if frappe.db.exists("Custom Field", name):
                continue
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Purchase Invoice",
                "read_only": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                **field_def,
            }).insert(ignore_permissions=True)

        # The bank statement shows the post-TDS transfer, so that is what the
        # amount match runs against — mirroring the Vendor Payment leg.
        if not frappe.db.exists("TMS Reconciliation Source", "Supplier Payment"):
            frappe.get_doc({
                "doctype": "TMS Reconciliation Source",
                "label": "Supplier Payment",
                "target_doctype": "Supplier Payment",
                "direction": "Debit",
                "requires_submitted": 1,
                "date_fieldname": "payment_date",
                "amount_fieldname": "total_transfer_amount",
                "account_fieldname": "paid_from_account",
                "reconciled_fieldname": "is_reconciled",
                "reconciliation_link_fieldname": "bank_reconciliation",
            }).insert(ignore_permissions=True)

        cols = frappe.db.sql(
            "SHOW COLUMNS FROM `tabPurchase Invoice` LIKE 'custom_bank_reconciliation_status'"
        )
        if not cols:
            return
        blank = frappe.db.sql(
            """
            SELECT name FROM `tabPurchase Invoice`
            WHERE docstatus = 1
              AND (custom_bank_reconciliation_status IS NULL OR custom_bank_reconciliation_status = '')
            """,
            pluck="name",
        )
        for name in blank:
            frappe.db.set_value("Purchase Invoice", name, {
                "custom_bank_reconciliation_status": "Unreconciled",
                "custom_reconciled_amount": 0,
            }, update_modified=False)

        frappe.db.commit()
        if blank:
            frappe.logger().info(
                f"[TMS] Backfilled bank reconciliation status for {len(blank)} Purchase Invoice(s)."
            )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to set up Supplier Payment reconciliation")


# Canonical TMS Reconciliation Source rows. Every bench migrate re-applies this
# list so a freshly pulled clone ends up with the same 12 legs — and the same
# field mappings — as the reference site, without needing a patch or fixtures.
# Add/edit a leg here and it propagates on the next migrate everywhere.
RECONCILIATION_SOURCES = [
    {
        "label": "Vendor Payment",
        "target_doctype": "Vendor Payment",
        "direction": "Debit",
        "sequence": 1,
        "is_active": 1,
        "requires_submitted": 1,
        "date_fieldname": "payment_date",
        "amount_fieldname": "total_transfer_amount",
        "account_fieldname": "paid_from_account",
        "display_fieldnames": "vendor,reference_no",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        # Matched on the post-TDS transfer, since that is the figure the bank
        # statement carries. What rolls up onto the Purchase Invoice is the
        # pre-TDS payment_amount — see utils/supplier_payment_reconciliation.py.
        "label": "Supplier Payment",
        "target_doctype": "Supplier Payment",
        "direction": "Debit",
        "sequence": 2,
        "is_active": 1,
        "requires_submitted": 1,
        "date_fieldname": "payment_date",
        "amount_fieldname": "total_transfer_amount",
        "account_fieldname": "paid_from_account",
        "display_fieldnames": "supplier,reference_no",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        "label": "Receipt",
        "target_doctype": "Receipt",
        "direction": "Credit",
        "sequence": 3,
        "is_active": 1,
        "requires_submitted": 1,
        "date_fieldname": "payment_date",
        "amount_fieldname": "total_received_amount",
        "account_fieldname": "paid_from_account",
        "display_fieldnames": "customer,reference_no",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        # direction="Both": a single Payment record is eligible on BOTH legs —
        # Debit via paid_from_account/is_reconciled/bank_reconciliation (the
        # outgoing leg, checked when reconciling the source account) and
        # Credit via the credit_* fields below (the incoming leg for
        # type="Bank Transfer", checked when reconciling the destination
        # account). One row in this list, one Payment record, no separate
        # "second doctype" needed.
        "label": "Payment",
        "target_doctype": "Payment",
        "direction": "Both",
        "sequence": 4,
        "is_active": 1,
        "requires_submitted": 1,
        "date_fieldname": "date",
        "amount_fieldname": "amount",
        "account_fieldname": "paid_from_account",
        "display_fieldnames": "type,reference_no,driver,employee,vendor_supplier",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
        "credit_account_fieldname": "transfer_to_account",
        "credit_reconciled_fieldname": "is_reconciled_in",
        "credit_reconciliation_link_fieldname": "bank_reconciliation_in",
    },
    {
        "label": "Fuel Urea Expenses - Supplier",
        "target_doctype": "Fuel Urea Expenses",
        "direction": "Debit",
        "sequence": 5,
        "is_active": 1,
        "requires_submitted": 1,
        "date_fieldname": "payment_date",
        "amount_fieldname": "fuelurea_amount",
        "account_fieldname": "bank_name",
        "display_fieldnames": "vehicle,supplier",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        "label": "Fuel Urea Expenses - Driver Incentive",
        "target_doctype": "Fuel Urea Expenses",
        "direction": "Debit",
        "sequence": 6,
        "is_active": 1,
        "requires_submitted": 1,
        "date_fieldname": "driver_payment_date",
        "amount_fieldname": "expense_amount",
        "account_fieldname": "driver_bank_name",
        "display_fieldnames": "vehicle,driver_id",
        "reconciled_fieldname": "is_reconciled_driver",
        "reconciliation_link_fieldname": "bank_reconciliation_driver",
    },
    {
        "label": "Repair Expenses",
        "target_doctype": "Repair Expenses",
        "direction": "Debit",
        "sequence": 7,
        "is_active": 1,
        "requires_submitted": 0,
        "date_fieldname": "payment_date",
        "amount_fieldname": "amount",
        "account_fieldname": "bank_name",
        "display_fieldnames": "vehicle_id,vendor",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        "label": "Tyre Expenses",
        "target_doctype": "Tyre Expenses",
        "direction": "Debit",
        "sequence": 8,
        "is_active": 1,
        "requires_submitted": 0,
        "date_fieldname": "purchase_date",
        "amount_fieldname": "total_cost",
        "account_fieldname": "bank_name",
        "display_fieldnames": "vehicle_id,vendor",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        "label": "Battery Expenses",
        "target_doctype": "Battery Expenses",
        "direction": "Debit",
        "sequence": 9,
        "is_active": 1,
        "requires_submitted": 0,
        "date_fieldname": "purchase_date",
        "amount_fieldname": "cost",
        "account_fieldname": "bank_name",
        "display_fieldnames": "vehicle_id,vendor",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        "label": "Compliances",
        "target_doctype": "Compliances",
        "direction": "Debit",
        "sequence": 10,
        "is_active": 1,
        "requires_submitted": 0,
        "date_fieldname": "issue_date",
        "amount_fieldname": "amount",
        "account_fieldname": "bank_name",
        "display_fieldnames": "vehicle,document_type",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        "label": "Service Logs",
        "target_doctype": "Service Logs",
        "direction": "Debit",
        "sequence": 11,
        "is_active": 1,
        "requires_submitted": 0,
        "date_fieldname": "voucher_date",
        "amount_fieldname": "total_amount",
        "account_fieldname": "bank_name",
        "display_fieldnames": "vehicle_no,service_type",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
    {
        "label": "Staff Payroll",
        "target_doctype": "Staff Payroll",
        "direction": "Debit",
        "sequence": 12,
        "is_active": 1,
        "requires_submitted": 1,
        "date_fieldname": "payment_date",
        "amount_fieldname": "net_salary",
        "account_fieldname": "bank_account",
        "display_fieldnames": "salary_type,employee_name",
        "reconciled_fieldname": "is_reconciled",
        "reconciliation_link_fieldname": "bank_reconciliation",
    },
]


def _sync_reconciliation_sources():
    """Create/update TMS Reconciliation Source rows from RECONCILIATION_SOURCES.

    Idempotent: missing rows are inserted, existing rows are corrected field by
    field (autoname is `field:label`, so the label is the primary key). Rows that
    are not in the list are left alone — they may be site-specific legs, and
    deleting them would orphan already-reconciled transactions.

    `sequence` is synced here too, which is what makes the two
    backfill_reconciliation_source_* patches unnecessary (see patches.txt): a row
    created before the field existed sits at the column default 0, and this
    restores the declared order instead of the creation order the patch guessed at.
    """
    try:
        if not frappe.db.table_exists("TMS Reconciliation Source"):
            return

        fields = [
            "target_doctype",
            "direction",
            "is_active",
            "requires_submitted",
            "date_fieldname",
            "amount_fieldname",
            "account_fieldname",
            "reconciled_fieldname",
            "reconciliation_link_fieldname",
            "credit_account_fieldname",
            "credit_reconciled_fieldname",
            "credit_reconciliation_link_fieldname",
            "display_fieldnames",
            "sequence",
        ]
        created = updated = 0

        for source in RECONCILIATION_SOURCES:
            label = source["label"]
            if not frappe.db.exists("TMS Reconciliation Source", label):
                frappe.get_doc({"doctype": "TMS Reconciliation Source", **source}).insert(
                    ignore_permissions=True
                )
                created += 1
                continue

            current = frappe.db.get_value(
                "TMS Reconciliation Source", label, fields, as_dict=True
            )
            changed = {f: source.get(f, "") for f in fields if current.get(f) != source.get(f, "")}
            if changed:
                doc = frappe.get_doc("TMS Reconciliation Source", label)
                doc.update(changed)
                doc.save(ignore_permissions=True)
                updated += 1

        frappe.db.commit()
        if created or updated:
            frappe.logger().info(
                f"[TMS] Reconciliation sources synced: {created} created, {updated} updated."
            )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to sync TMS Reconciliation Sources")


def _backfill_missing_account_ledger_entries():
    """Documents saved/submitted before their ledger hook existed on that
    doctype never got their Account Ledger rows written — e.g.
    FUEL-2026-06041 was submitted 2026-07-29, but the hook (see
    utils/account_balance_utils.py) was only wired up on 2026-08-14, so it
    silently never ran for that document. Runs on every migrate to catch up
    any doctype/document combination left behind this way, across every
    LEDGER_ON_SUBMIT_DOCTYPES doctype (Vendor Payment, Supplier Payment,
    Receipt, Payment, Fuel Urea Expenses, Staff Payroll, Tyre Expenses,
    Battery Expenses) and every LEDGER_ON_SAVE_DOCTYPES doctype (Repair
    Expenses, Compliances, Service Logs) — not just Fuel Urea Expenses.

    Idempotent: backfill_missing_ledger_entries() skips any leg that already
    has an Account Ledger, so re-running is a no-op once caught up.
    Must run after _sync_reconciliation_sources() above, since it reads the
    TMS Reconciliation Source rows to know which doctypes/fields to check.

    Legs with a negative amount (deductions exceeding earnings on a Staff
    Payroll, etc.) are skipped rather than guessed at — see
    backfill_missing_ledger_entries()'s docstring — and logged here so they
    stay visible instead of silently vanishing on every migrate.
    """
    try:
        from logicore.utils.account_balance_utils import backfill_missing_ledger_entries

        result = backfill_missing_ledger_entries()
        frappe.db.commit()
        if result["created"]:
            frappe.logger().info(f"[TMS] Backfilled {result['created']} missing Account Ledger rows")
        if result["skipped"]:
            frappe.logger().warning(
                f"[TMS] Skipped {len(result['skipped'])} negative-amount legs during Account "
                f"Ledger Entry backfill (needs manual review): "
                + ", ".join(f"{s['doctype']} {s['name']} ({s['amount']})" for s in result["skipped"])
            )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill missing Account Ledger rows")


def _backfill_account_ledger_entry_balance_amount():
    """Account Ledger's balance_amount column (mirrors Account
    Head.current_balance onto every row for that account — see
    refresh_current_balance() in utils/account_balance_utils.py) is kept in
    sync going forward by that same function, but rows written before the
    column existed are NULL until refresh_current_balance() runs again for
    their account. Backfill once per account so the "Balance Amount"
    list/report column is populated immediately instead of waiting for the
    next transaction on that account.

    Must run after _backfill_missing_account_ledger_entries() above, so
    every row that should exist for an account is already there before its
    balance is recomputed. Idempotent: only touches accounts that still have
    a NULL row.
    """
    try:
        if not frappe.db.has_column("Account Ledger", "balance_amount"):
            return

        from logicore.utils.account_balance_utils import refresh_current_balance

        accounts = frappe.db.sql(
            """SELECT DISTINCT account FROM `tabAccount Ledger`
            WHERE balance_amount IS NULL""",
            pluck=True,
        )
        for account in accounts:
            refresh_current_balance(account)
        if accounts:
            frappe.db.commit()
            frappe.logger().info(f"[TMS] Backfilled balance_amount for {len(accounts)} accounts")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill Account Ledger balance_amount")


def _refresh_opening_balance_ledger_ordering():
    """refresh_current_balance() (utils/account_balance_utils.py) used to pin
    the "Opening Balance" row to position 0 for the whole account when
    computing running balance_amount — before every other row, regardless of
    its own posting_date — so editing an account's opening balance leaked
    its effect into transactions recorded years before opening_balance_date.
    Fixed to order by posting_date first, with Opening Balance only winning
    the same-day tie-break, so it now seeds the balance from its own date
    forward without touching anything earlier.

    Any account that already had an Opening Balance ledger row before this
    fix has balance_amount values computed under the old (wrong) ordering —
    non-NULL, so _backfill_account_ledger_entry_balance_amount() above
    leaves it alone. Recompute every such account here so any environment
    that pulls this fix gets its existing data corrected on migrate too, not
    just the corrected behavior for future opening balance edits.

    Idempotent: refresh_current_balance() is a pure recompute from the
    ledger rows themselves — re-running it against already-correct data just
    writes the same values back.
    """
    try:
        from logicore.utils.account_balance_utils import refresh_current_balance

        accounts = frappe.db.sql(
            """SELECT DISTINCT account FROM `tabAccount Ledger`
            WHERE remarks = 'Opening Balance'""",
            pluck=True,
        )
        for account in accounts:
            refresh_current_balance(account)
        if accounts:
            frappe.db.commit()
            frappe.logger().info(
                f"[TMS] Recomputed Account Ledger running balance for {len(accounts)} "
                "account(s) with an Opening Balance entry"
            )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to refresh opening balance ledger ordering")


def _clear_stale_account_ledger_entry_user_settings():
    """"Account Ledger Entry" was renamed to "Account Ledger" (2026-08-24).
    frappe.rename_doc() updates saved List/Report settings on OTHER doctypes
    that link to the renamed record, but not a user's own saved column/filter
    layout keyed by the renamed doctype's old name — those __UserSettings
    rows are now permanently orphaned (the "Account Ledger Entry" route no
    longer exists) and would otherwise sit there indefinitely. Deleting them
    is safe: with no override present, the doctype's own in_list_view fields
    (including balance_amount) apply as the default for "Account Ledger"
    going forward.

    Idempotent: a no-op once no rows with the old doctype name remain.
    """
    try:
        frappe.db.delete("__UserSettings", {"doctype": "Account Ledger Entry"})
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to clear stale Account Ledger Entry user settings")


# Reverted per user request — Purchase Invoice/Stock Entry go back to plain
# posting_date (no custom Payment Date field). Custom Field, Property Setters
# and field_order splice were removed directly from the DB; this function is
# kept (commented out, not deleted) in case the feature is wanted again.
# def _ensure_purchase_invoice_purchase_date():
#     """Add Purchase Invoice's "Purchase Date" field, hide posting_date/posting_time
#     in its favour, and splice it into the pinned field_order -- on every migrate.
#
#     posting_date stays wired to GL entries, fiscal year and aging (see
#     sync_posting_date_from_purchase_date() in purchase_invoice.js), so it can't be
#     removed, only hidden. Idempotent: every step checks existence first.
#     """
#     try:
#         if not frappe.db.exists("Custom Field", "Purchase Invoice-custom_purchase_date"):
#             frappe.get_doc(
#                 {
#                     "doctype": "Custom Field",
#                     "dt": "Purchase Invoice",
#                     "fieldname": "custom_purchase_date",
#                     "label": "Payment Date",
#                     "fieldtype": "Date",
#                     "insert_after": "posting_date",
#                     "reqd": 1,
#                     "default": "Today",
#                 }
#             ).insert(ignore_permissions=True)
#         elif frappe.db.get_value("Custom Field", "Purchase Invoice-custom_purchase_date", "label") != "Payment Date":
#             frappe.db.set_value(
#                 "Custom Field", "Purchase Invoice-custom_purchase_date", "label", "Payment Date"
#             )
#
#         if not frappe.db.exists("Property Setter", "Purchase Invoice-posting_date-hidden"):
#             make_property_setter(
#                 {
#                     "doctype": "Purchase Invoice",
#                     "fieldname": "posting_date",
#                     "property": "hidden",
#                     "value": "1",
#                     "property_type": "Check",
#                 }
#             )
#
#         if not frappe.db.exists("Property Setter", "Purchase Invoice-posting_time-hidden"):
#             make_property_setter(
#                 {
#                     "doctype": "Purchase Invoice",
#                     "fieldname": "posting_time",
#                     "property": "hidden",
#                     "value": "1",
#                     "property_type": "Check",
#                 }
#             )
#
#         # Purchase Invoice's layout is pinned by an explicit field_order Property
#         # Setter (set via Customize Form), which ignores each field's own
#         # insert_after -- so custom_purchase_date has to be spliced into that same
#         # list, right after posting_date, or it renders nowhere on the form.
#         field_order_ps = "Purchase Invoice-main-field_order"
#         if frappe.db.exists("Property Setter", field_order_ps):
#             field_order = json.loads(frappe.db.get_value("Property Setter", field_order_ps, "value"))
#             if "posting_date" in field_order and "custom_purchase_date" not in field_order:
#                 field_order.insert(field_order.index("posting_date") + 1, "custom_purchase_date")
#                 frappe.db.set_value("Property Setter", field_order_ps, "value", json.dumps(field_order))
#
#         frappe.clear_cache(doctype="Purchase Invoice")
#         frappe.db.commit()
#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Failed to ensure Purchase Invoice purchase date")


# def _ensure_stock_entry_payment_date():
#     """Add Stock Entry's "Payment Date" field, hide posting_date/posting_time in
#     its favour -- on every migrate.
#
#     posting_date stays wired to the stock ledger and valuation (see
#     sync_posting_date_from_payment_date() in stock_entry.js), so it can't be
#     removed, only hidden. Idempotent: every step checks existence first.
#     """
#     try:
#         if not frappe.db.exists("Custom Field", "Stock Entry-custom_payment_date"):
#             frappe.get_doc(
#                 {
#                     "doctype": "Custom Field",
#                     "dt": "Stock Entry",
#                     "fieldname": "custom_payment_date",
#                     "label": "Payment Date",
#                     "fieldtype": "Date",
#                     "insert_after": "posting_date",
#                     "reqd": 1,
#                     "default": "Today",
#                 }
#             ).insert(ignore_permissions=True)
#
#         if not frappe.db.exists("Property Setter", "Stock Entry-posting_date-hidden"):
#             make_property_setter(
#                 {
#                     "doctype": "Stock Entry",
#                     "fieldname": "posting_date",
#                     "property": "hidden",
#                     "value": "1",
#                     "property_type": "Check",
#                 }
#             )
#
#         if not frappe.db.exists("Property Setter", "Stock Entry-posting_time-hidden"):
#             make_property_setter(
#                 {
#                     "doctype": "Stock Entry",
#                     "fieldname": "posting_time",
#                     "property": "hidden",
#                     "value": "1",
#                     "property_type": "Check",
#                 }
#             )
#
#         frappe.clear_cache(doctype="Stock Entry")
#         frappe.db.commit()
#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Failed to ensure Stock Entry payment date")


def _relabel_purchase_invoice_posting_date():
    """Relabel Purchase Invoice's standard posting_date field to "Purchase Date"
    -- label only, same field/fieldname, no custom field or hidden sibling.
    Idempotent: safe to call on every migrate.
    """
    try:
        ps_name = "Purchase Invoice-posting_date-label"
        if frappe.db.get_value("Property Setter", ps_name, "value") != "Purchase Date":
            if frappe.db.exists("Property Setter", ps_name):
                frappe.delete_doc("Property Setter", ps_name, ignore_permissions=True, force=True)
            make_property_setter("Purchase Invoice", "posting_date", "label", "Purchase Date", "Data")
        frappe.clear_cache(doctype="Purchase Invoice")
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to relabel Purchase Invoice posting_date")


def _disable_link_preview_popup():
    """Turn off "Show Preview Popup" wherever an admin has enabled it via Customize
    Form, on every doctype, every migrate.

    Frappe's Report View renders a Link column as a clickable anchor even when the
    field is blank -- the href points at a document literally named "null". Hovering
    that anchor does nothing UNLESS the linked doctype has "Show Preview Popup" on
    (a Property Setter, since it's set through Customize Form on standard doctypes),
    in which case the hover fires an AJAX lookup for that "null" document and shows
    a "<Doctype> null not found" dialog -- confusing on any list, and on Driver/
    Employee/User columns the cell's *display text* often shows a real-looking name
    (the row's own title) even though the underlying value is empty, so real users
    click it during normal use, not just while hovering. Rather than auditing every
    doctype the popup could ever be turned on for, this blanket-clears it on every
    migrate, on this app's convention of idempotent after_migrate() logic over one-off
    fixes made by hand on a live site (which would drift the next time someone
    touches Customize Form there again).
    """
    try:
        rows = frappe.get_all(
            "Property Setter",
            filters={"property": "show_preview_popup", "value": "1"},
            pluck="name",
        )
        if not rows:
            return
        for name in rows:
            frappe.db.set_value("Property Setter", name, "value", "0")
        frappe.db.commit()
        frappe.clear_cache()
        frappe.logger().info(f"[TMS] Disabled Show Preview Popup on {len(rows)} doctype(s).")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to disable link preview popup")


def _rename_border_crossing_payment_type():
    """Backfill existing Payment rows from the old "Border Crossing" Payment Type
    value to the renamed "Border Crossing/Vehicle Expense/Toll Tax", so historical
    records match the option now in payment.json.
    """
    try:
        frappe.db.set_value(
            "Payment",
            {"type": "Border Crossing"},
            "type",
            "Border Crossing/Vehicle Expense/Toll Tax",
        )
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to rename Border Crossing payment type")


def _backfill_cancelled_staff_payroll_status():
    """Staff Payroll's `status` field only auto-updates on submit (-> Processed).
    Cancelling a submitted payroll never touched it before on_cancel() existed,
    leaving cancelled documents still showing "Processed" in list/report views.
    """
    try:
        frappe.db.set_value(
            "Staff Payroll",
            {"docstatus": 2, "status": ("!=", "Cancelled")},
            "status",
            "Cancelled",
        )
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to backfill cancelled Staff Payroll status")


def _get_fixture_doctypes():
    """Doctype names declared in this app's `fixtures` hook (dict or plain-string entries)."""
    doctypes = set()
    for fixture in frappe.get_hooks("fixtures", app_name="logicore"):
        dt = (fixture.get("doctype") or fixture.get("dt")) if isinstance(fixture, dict) else fixture
        if dt:
            doctypes.add(dt)
    return doctypes


def auto_export_fixtures_on_change(doc, method=None):
    """Auto-export logicore fixtures whenever any fixture-listed doctype changes.

    Without this, saving a Custom HTML Block / Number Card / Dashboard Chart /
    Workspace / Report etc. through the UI (or console) updates the DB only —
    the JSON fixture drifts out of sync until someone remembers to run
    `bench export-fixtures`, and the next `bench migrate` elsewhere then reverts
    the change back to the stale fixture. Workspace Sidebar already has its own
    dedicated hook (export_sidebar_fixtures_on_save) with extra cache-clearing,
    so it's skipped here to avoid a redundant double-export.
    """
    if doc.doctype == "Workspace Sidebar":
        return
    if not frappe.conf.developer_mode:
        return
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_install:
        return
    if doc.doctype not in _get_fixture_doctypes():
        return
    _export_fixtures()


def export_sidebar_fixtures_on_save(doc, method):
	"""Auto-export fixtures whenever Workspace Sidebar is modified (add/remove items)."""
	try:
		_export_fixtures()
		_sync_all_tms_user_group_sidebars()
		frappe.clear_cache()
		# Clear the process-level @site_cache so auto_generate_sidebar_from_module
		# re-evaluates which modules already have a custom sidebar.  Without this,
		# stale cache can inject an auto-generated "LogiCore" sidebar into
		# boot data alongside the real "LogiCore" sidebar, causing sidebar switching.
		try:
			from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import auto_generate_sidebar_from_module
			auto_generate_sidebar_from_module.clear_cache()
		except Exception:
			pass
		frappe.logger().info(f"Exported Workspace Sidebar fixtures for {doc.name}")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Failed to export sidebar fixtures on save")
