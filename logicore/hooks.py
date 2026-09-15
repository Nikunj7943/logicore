app_name = "logicore"
app_title = "LogiCore"
app_publisher = "LogiCore"
app_description = "Transport and Logistic System"
app_email = "support@logicore.app"
app_license = "mit"

import hashlib, os

def _fv(rel_path):
	"""Return first 8 chars of MD5 hash of a public asset file for cache-busting."""
	abs_path = os.path.join(os.path.dirname(__file__), "public", rel_path)
	try:
		with open(abs_path, "rb") as f:
			return hashlib.md5(f.read()).hexdigest()[:8]
	except Exception:
		return "1"

# 2FA Email Override
import frappe.twofactor
from logicore.overrides.twofactor import send_token_via_email
frappe.twofactor.send_token_via_email = send_token_via_email

# Max File Size boundary tolerance — see overrides/max_file_size.py for why
import frappe.core.api.file
from logicore.overrides.max_file_size import get_max_file_size_with_tolerance
frappe.core.api.file.get_max_file_size = get_max_file_size_with_tolerance

# Fixtures
# --------
fixtures = [
	"Custom Field",
	"Property Setter",
	"Client Script",
	"Server Script",
	{"dt": "Custom DocPerm", "filters": [["parent", "in", ["Data Import"]]]},
	{"dt": "Custom HTML Block", "filters": [["name", "in", ["TMS Filter Bar", "TMS Trip Operations", "TMS Vendor Pending", "TMS Trip Other", "TMS Financial Summary", "TMS Vehicle Finance Activity"]]]},
	{"dt": "Workspace", "filters": [["module", "=", "LogiCore"]]},
	{"dt": "Workspace Sidebar", "filters": [["name", "=", "LogiCore"]]},
	{"dt": "Dashboard", "filters": [["name", "in", ["Trip Dashboard"]]]},
	{"dt": "Dashboard", "prefix": "fleet", "filters": [["name", "in", ["Fleet Dashboard"]]]},
    {
        "doctype": "Website Settings"
    },
	{
		"dt": "Dashboard Chart",
		"filters": [["name", "in", [
			"TMS Trip Volume Monthly",
			"TMS Customer Freight Monthly",
			"TMS Trips by Status",
			"TMS Trips by Trip Type",
			"TMS Trips by Branch",
			"TMS POD Status Distribution",
			"TMS Vendor Freight Monthly",
			"TMS Detention Trend Monthly",
			"TMS Trips by Customer",
			"TMS Trips by Vehicle Type",
			"Fleet Fuel Expenses Monthly",
			"Fleet Fuel KPL Trend",
			"Fleet Repair Expenses Monthly",
			"Fleet Repairs by Category",
			"Fleet Service Cost Monthly",
			"Fleet Compliances by Type",
			"Fleet Tyre Cost Monthly",
			"Fleet Fuel by Vehicle",
			"HR Employee Count by Designation",
			"HR Driver License Status",
			"HR Salary Trend Monthly",
			"HR Leave Applications Monthly",
			"HR Attendance Status Distribution",
			"HR Leave by Type",
			"HR Absent Trend Monthly",
			"HR Leave by Status",
			"HR Expense Claims Monthly",
			"HR Salary by Department",
		]]],
	},
	{
		"dt": "Number Card",
		"filters": [["name", "in", [
			"TMS Open Trips",
			"TMS Trips This Month",
			"TMS Customer Freight MTD",
			"TMS POD Pending",
			"TMS Total KM MTD",
			"TMS Vendor Freight MTD",
			"TMS Detention Amount MTD",
			"TMS Active Vehicles",
			"TMS Trip Revenue MTD",
			"TMS Amazon Trips Active",
			"Fleet Fuel Cost MTD",
			"Fleet Fuel Liters MTD",
			"Fleet Repair Cost MTD",
			"Fleet Repair Count MTD",
			"Fleet Service Cost MTD",
			"Fleet Tyre Cost MTD",
			"Fleet Battery Count MTD",
			"Fleet Compliance Count",
			"Fleet Outstanding Loans",
			"Fleet EMI Total",
			"HR Total Active Employees",
			"HR Active Drivers",
			"HR Active Staff",
			"HR Employees on Leave Today",
			"HR Leave Pending Approval",
			"HR Present MTD",
			"HR Absent MTD",
			"HR Net Pay MTD",
			"HR Expense Claims MTD",
			"HR Approved Claims Amount MTD",
			"HR Driver License Expired",
			"HR Salary Slips MTD",
		]]],
	},
	{
		"dt": "Report",
		"filters": [["name", "in", ["TMS Vendor Payment Summary", "TMS Vendor Payment Detail"]]],
	},
]

# Apps
# ------------------

required_apps = ["erpnext", "hrms", "india_compliance"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "logicore",
# 		"logo": "/assets/logicore/logo.png",
# 		"title": "LogiCore",
# 		"route": "/logicore",
# 		"has_permission": "logicore.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	f"/assets/logicore/css/tms_global.css?v={_fv('css/tms_global.css')}",
	f"/assets/logicore/css/tms_trip.css?v={_fv('css/tms_trip.css')}",
]

app_include_js = [
	f"/assets/logicore/js/tms_utils.js?v={_fv('js/tms_utils.js')}",
	f"/assets/logicore/js/tms_list_settings.js?v={_fv('js/tms_list_settings.js')}",
	# Only the default page length (500) and removing the "20" paging button —
	# no other list view UI/layout changes.
	f"/assets/logicore/js/tms_list_page_length.js?v={_fv('js/tms_list_page_length.js')}",
	f"/assets/logicore/js/tms_alerts.js?v={_fv('js/tms_alerts.js')}",
	f"/assets/logicore/js/hide_sidebar.js?v={_fv('js/hide_sidebar.js')}",
	f"/assets/logicore/js/tms_navigation_visibility.js?v={_fv('js/tms_navigation_visibility.js')}",
	f"/assets/logicore/js/tms_home_breadcrumb.js?v={_fv('js/tms_home_breadcrumb.js')}",
	f"/assets/logicore/js/session_timer.js?v={_fv('js/session_timer.js')}",
	f"/assets/logicore/js/default_public_upload.js?v={_fv('js/default_public_upload.js')}",
	f"/assets/logicore/js/tms_import_dialog.js?v={_fv('js/tms_import_dialog.js')}",
	f"/assets/logicore/js/disable_report_view_inline_edit.js?v={_fv('js/disable_report_view_inline_edit.js')}",
	f"/assets/logicore/js/pin_workspace_sidebar.js?v={_fv('js/pin_workspace_sidebar.js')}",
	f"/assets/logicore/js/tms_field_permission_guard.js?v={_fv('js/tms_field_permission_guard.js')}",
	f"/assets/logicore/js/tms_report_menu_gate.js?v={_fv('js/tms_report_menu_gate.js')}",
	f"/assets/logicore/js/tms_hide_select_report.js?v={_fv('js/tms_hide_select_report.js')}",
	# "Download POD" button — Trip List View (native button hook) + Trip Report View
	# (ReportView.prototype patch, same convention as tms_report_menu_gate.js above).
	f"/assets/logicore/js/tms_pod_download_column.js?v={_fv('js/tms_pod_download_column.js')}",
	# Generic "Export" button for every list/report view except Trip/Amazon Trip
	# (which have their own dedicated export dialogs) and Single/child-table doctypes.
	f"/assets/logicore/js/tms_generic_export.js?v={_fv('js/tms_generic_export.js')}",
	# Overrides india_compliance's AddressQuickEntryForm so the "New Address"
	# dialog's Link Document Type + Link Name fields are always hidden — the
	# auto party-link logic still runs silently in the background.
	f"/assets/logicore/js/address_quick_entry_override.js?v={_fv('js/address_quick_entry_override.js')}",
	# Shared "today by default" quick date-range bar for list views — see the
	# file header for usage. Wired into each opted-in doctype's own <name>_list.js.
	f"/assets/logicore/js/tms_date_filter_bar.js?v={_fv('js/tms_date_filter_bar.js')}",
	# Admin-gated + Date/child-table-aware "Customize Quick Filters" override —
	# see tms_quick_filters.py for the paired whitelisted save API.
	f"/assets/logicore/js/tms_quick_filter_override.js?v={_fv('js/tms_quick_filter_override.js')}",
	# Un-hides the naming field on standard ERPNext/Frappe `field:<x>` autoname
	# doctypes (Vehicle, Company, UOM, Item, etc.) so it can be edited inline —
	# see tms_naming_field_unhide.js. Paired backend rename hook is wired via
	# doc_events -> overrides.standard_doctype_rename below.
	f"/assets/logicore/js/tms_naming_field_unhide.js?v={_fv('js/tms_naming_field_unhide.js')}",
	# Hides "Edit row" and "Duplicate row" from every grid's toolbar app-wide —
	# only "Add row" and "Delete row" stay. See tms_grid_row_actions.js.
	f"/assets/logicore/js/tms_grid_row_actions.js?v={_fv('js/tms_grid_row_actions.js')}",
]


website_context = {
    "favicon": "/assets/logicore/images/logicore_icon.png"
}

# include js, css files in header of web template
# web_include_css = "/assets/logicore/css/logicore.css"
# web_include_js = "/assets/logicore/js/logicore.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "logicore/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "doctype": "public/js/vehicle.js",
    "Supplier": "public/js/supplier.js",
    "Customer": "public/js/customer.js",
    # Un-hides the Links (Dynamic Link) grid on the full Address form for
    # Administrator / System Manager only — see public/js/address.js.
    "Address": "public/js/address.js",
    # Suppresses the "Create" / "Preview" / "Get Items From" toolbar groups so a
    # saved invoice looks the same as a newly created one. The paired "More Info"
    # / "Connections" tab hiding lives in custom/purchase_invoice.json.
    "Purchase Invoice": "public/js/purchase_invoice.js",
    # Redirects the "View > Stock Ledger" button to TMS Stock Ledger — see
    # public/js/stock_entry.js (the old posting_date sync logic it used to
    # carry is commented out there, not deleted).
    "Stock Entry": "public/js/stock_entry.js",
    # Locks the "Doctype" field read-only whenever a new Email Template opens
    # with reference_doctype already pre-filled (e.g. Trip's "+ New Template"
    # button) — see the file for why.
    "Email Template": "public/js/email_template.js",
    # Restricts "Manage > Delete Transactions" to the literal Administrator
    # account — ERPNext's core company.js only checks the System Manager role,
    # which is broader than intended. See public/js/company.js.
    "Company": "public/js/company.js",
}
doctype_list_js = {
    # Overrides ERPNext's GL-driven "Status" indicator in List/Report View —
    # see the file for why. Also wires TMS.dateFilterBar (defaults to today).
    "Purchase Invoice": "public/js/purchase_invoice_list.js",
    # Adds TMS.dateFilterBar (defaults to today) on top of ERPNext/HRMS's own
    # list settings for these non-app-owned doctypes.
    "Stock Entry": "public/js/stock_entry_list.js",
    "Leave Application": "public/js/leave_application_list.js",
}
doctype_js["Salary Structure"] = "public/js/salary_structure.js"
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "logicore/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

boot_session = [
	"logicore.tms_list_settings.add_tms_list_settings_bootinfo",
	"logicore.tms_navigation_visibility.add_tms_navigation_visibility_bootinfo",
	"logicore.tms_report_menu.add_tms_report_menu_bootinfo",
	"logicore.logicore.doctype.alert_settings.alert_settings.add_alert_settings_bootinfo",
	"logicore.install.fix_workspace_sidebar_bootinfo",
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "logicore.utils.jinja_methods",
# 	"filters": "logicore.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "logicore.install.before_install"
after_install = "logicore.install.after_install"
after_migrate = "logicore.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "logicore.uninstall.before_uninstall"
# after_uninstall = "logicore.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "logicore.utils.before_app_install"
# after_app_install = "logicore.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "logicore.utils.before_app_uninstall"
# after_app_uninstall = "logicore.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "logicore.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"User": "logicore.tms_navigation_visibility.get_permission_query_conditions_user",
	"TMS User Group": "logicore.tms_navigation_visibility.get_permission_query_conditions_tms_user_group",
}

has_permission = {
	"Page":      "logicore.tms_navigation_visibility.has_permission_page",
	"Dashboard": "logicore.tms_navigation_visibility.has_permission_dashboard",
	"Report":    "logicore.tms_navigation_visibility.has_permission_report",
	"User":      "logicore.tms_navigation_visibility.has_permission_user",
	"TMS User Group": "logicore.tms_navigation_visibility.has_permission_tms_user_group",
}

# Document Events
# ---------------
# Hook on document methods and events

override_doctype_class = {
    "Address": "logicore.overrides.address.AddressOverride",
    # Compresses Driver/Employee/Compliances PDF/JPG/PNG attachments to fit
    # under System Settings "Max File Size (MB)" instead of rejecting them —
    # see overrides/file_compression.py for why this must be a check_max_file_size
    # override rather than an after_insert hook.
    "File": "logicore.overrides.file_compression.MasterAttachmentFile",
}

doc_events = {
    "Address": {
        "before_validate": "logicore.overrides.address.before_save_fill_city_fields",
        "after_insert": "logicore.overrides.address.after_insert_set_primary",
    },
    # email_id/mobile_no are core ERPNext's read-only fetch_from fields (Contact ->
    # Supplier one-way). Property Setters (see install.py) make them editable so
    # users can type them directly here; these push the typed values back onto
    # the linked Contact so they aren't lost/stale next time the Contact itself
    # is opened or the fetch_from re-fires. See overrides/supplier.py.
    "Supplier": {
        "on_update": [
            "logicore.overrides.supplier.sync_email_to_primary_contact",
            "logicore.overrides.supplier.sync_mobile_to_primary_contact",
        ],
    },
    # Same fix, same reason, for Customer.email_id/mobile_no -> customer_primary_contact.
    # See overrides/customer.py.
    "Customer": {
        "on_update": [
            "logicore.overrides.customer.sync_email_to_primary_contact",
            "logicore.overrides.customer.sync_mobile_to_primary_contact",
        ],
    },
    "User": {
        "on_update": "logicore.tms_list_settings.on_user_update_clear_tms_bootinfo",
    },
    "Role": {
        "on_update": "logicore.logicore.doctype.tms_user_group.tms_user_group.sync_role_disabled_to_user_group",
    },
    # The "Employee User Automation" Server Script writes user_id with
    # frappe.db.set_value, which skips validation — see overrides/employee.py for
    # how that produced Employees that could never be saved again.
    "Employee": {
        "before_validate": [
            "logicore.overrides.employee.before_validate",
            "logicore.master_status.sync_disabled_mirror",
        ],
        "validate": "logicore.overrides.employee.validate",
        # Keeps the linked User's default Company (used by Payment/Supplier
        # Payment's company field, which now has no hardcoded default) equal to
        # this Employee's own Company. See overrides/employee.py.
        "on_update": "logicore.overrides.employee.sync_user_default_company",
    },
    # Group B masters: `disabled` is a derived mirror of the lifecycle field that
    # was already there (status / is_active), so Frappe's Link-search filter
    # engages without anyone having to tick a second checkbox. See master_status.py.
    "Driver": {
        "before_validate": "logicore.master_status.sync_disabled_mirror",
    },
    "TMS User Group": {
        "before_validate": "logicore.master_status.sync_disabled_mirror",
    },
    "Import Template": {
        "before_validate": "logicore.master_status.sync_disabled_mirror",
    },
    "Custom DocPerm": {
        "on_update": "logicore.logicore.doctype.tms_user_group.tms_user_group.sync_custom_docperm_to_user_group",
        "on_trash": "logicore.logicore.doctype.tms_user_group.tms_user_group.sync_custom_docperm_to_user_group",
    },
    "Workspace Sidebar": {
        "after_save": "logicore.install.export_sidebar_fixtures_on_save",
    },
    # Staff Payroll generates one record per employee per month from a Salary
    # Structure, so a submitted structure can have hundreds of submitted Staff
    # Payroll records against it by the time a new component needs adding --
    # cancel/amend would force-cancel all of them. So earnings/deductions are made
    # allow_on_submit (see install.py), this hook restricts who may use that hole,
    # and on_update_after_submit backfills the new component into every linked
    # Staff Payroll record (old ones included) at amount=0. See overrides/salary_structure.py.
    "Salary Structure": {
        "before_save": "logicore.overrides.salary_structure.restrict_component_edit_after_submit",
        "on_update_after_submit": "logicore.overrides.salary_structure.enqueue_component_backfill",
    },
    "Alert Settings": {
        "on_update": "logicore.logicore.doctype.alert_settings.alert_settings.clear_alert_settings_cache",
        "on_trash": "logicore.logicore.doctype.alert_settings.alert_settings.clear_alert_settings_cache",
    },
    # Breadcrumb/heading shows the invoice number, not Supplier Name (ERPNext's
    # default title_field) — see overrides/purchase_invoice.py for why this
    # goes through the real `title` field instead of a title_field override.
    "Purchase Invoice": {
        "before_validate": "logicore.overrides.purchase_invoice.set_default_warehouse",
        "validate": [
            "logicore.overrides.purchase_invoice.set_title_to_name",
            "logicore.overrides.purchase_invoice.sync_payment_fields",
            "logicore.overrides.purchase_invoice.sync_document_status",
        ],
        "on_cancel": [
            "logicore.overrides.purchase_invoice.set_document_status_on_cancel",
        ],
    },
    # Standard ERPNext/Frappe `field:<x>` autoname doctypes we did not create —
    # editing the un-hidden naming field (tms_naming_field_unhide.js) and saving
    # now actually renames the record instead of silently reverting. See
    # overrides/standard_doctype_rename.py.
    "Vehicle": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    "Company": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    "UOM": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    "Item Group": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    "Item": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    "GST HSN Code": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    "Supplier Group": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    "Customer Group": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    "Branch": {
        "before_save": "logicore.overrides.standard_doctype_rename.before_save",
        "on_update": "logicore.overrides.standard_doctype_rename.on_update",
    },
    # Account Head.current_balance tracking — see utils/account_balance_utils.py.
    # LEDGER_ON_SUBMIT_DOCTYPES (this block, one on_submit/on_cancel pair per
    # doctype) write one Account Ledger per account leg the moment the
    # document becomes final. Repair Expenses, Compliances, and Service Logs
    # are never submitted in this app (always docstatus=0) — no safe
    # on_submit/on_cancel to hook — so they upsert on every save instead (see
    # the on_update/on_trash block further below, and LEDGER_ON_SAVE_DOCTYPES).
    "Vendor Payment": {
        "on_submit": [
            "logicore.utils.account_balance_utils.on_submit_write_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
        "on_cancel": [
            "logicore.utils.account_balance_utils.on_cancel_delete_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
    },
    "Supplier Payment": {
        "on_submit": [
            "logicore.utils.account_balance_utils.on_submit_write_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
        "on_cancel": [
            "logicore.utils.account_balance_utils.on_cancel_delete_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
    },
    "Receipt": {
        "on_submit": [
            "logicore.utils.account_balance_utils.on_submit_write_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
        "on_cancel": [
            "logicore.utils.account_balance_utils.on_cancel_delete_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
    },
    "Payment": {
        "on_submit": [
            "logicore.utils.account_balance_utils.on_submit_write_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
        "on_cancel": [
            "logicore.utils.account_balance_utils.on_cancel_delete_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
    },
    "Fuel Urea Expenses": {
        "on_submit": [
            "logicore.utils.account_balance_utils.on_submit_write_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
        "on_cancel": [
            "logicore.utils.account_balance_utils.on_cancel_delete_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
    },
    "Staff Payroll": {
        "before_save": "logicore.overrides.salary_structure.restrict_staff_payroll_component_edit_after_submit",
        "on_submit": [
            "logicore.utils.account_balance_utils.on_submit_write_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
        "on_cancel": [
            "logicore.utils.account_balance_utils.on_cancel_delete_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
    },
    "Tyre Expenses": {
        "on_submit": [
            "logicore.utils.account_balance_utils.on_submit_write_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
        "on_cancel": [
            "logicore.utils.account_balance_utils.on_cancel_delete_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
    },
    "Battery Expenses": {
        "on_submit": [
            "logicore.utils.account_balance_utils.on_submit_write_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
        "on_cancel": [
            "logicore.utils.account_balance_utils.on_cancel_delete_ledger",
            "logicore.utils.account_balance_utils.refresh_balances_for_doc",
        ],
    },
    # These three are never submitted (always docstatus=0), so there is no
    # on_submit/on_cancel to hook — on_update upserts the one Account Ledger
    # Entry each document can have on every save, on_trash removes it if the
    # document itself is deleted. See LEDGER_ON_SAVE_DOCTYPES and
    # _upsert_ledger_for_document() in utils/account_balance_utils.py.
    "Repair Expenses": {
        "on_update": ["logicore.utils.account_balance_utils.on_update_upsert_ledger"],
        "on_trash": ["logicore.utils.account_balance_utils.on_cancel_delete_ledger"],
    },
    "Compliances": {
        "on_update": ["logicore.utils.account_balance_utils.on_update_upsert_ledger"],
        "on_trash": ["logicore.utils.account_balance_utils.on_cancel_delete_ledger"],
    },
    "Service Logs": {
        "on_update": ["logicore.utils.account_balance_utils.on_update_upsert_ledger"],
        "on_trash": ["logicore.utils.account_balance_utils.on_cancel_delete_ledger"],
    },
    # CAPA FIX: editing any fixture-listed doctype (Custom HTML Block, Number Card,
    # Dashboard Chart, Workspace, Report, etc.) via the UI/console used to require
    # manually remembering `bench export-fixtures` afterwards, or the change would
    # silently revert on the next migrate elsewhere. "*" runs for every doctype's
    # save/delete; auto_export_fixtures_on_change() filters to fixture doctypes only.
    "*": {
        # Blocks a disabled master from landing on a NEW document via Data Import
        # or the REST API, which bypass the dropdown filter entirely. No-ops for
        # existing documents — see master_status.validate_no_disabled_masters.
        "validate": "logicore.master_status.validate_no_disabled_masters",
        "on_update": "logicore.install.auto_export_fixtures_on_change",
        "on_trash": "logicore.install.auto_export_fixtures_on_change",
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"logicore.logicore.doctype.alert_settings.alert_settings.run_alert_scheduler",
	],
	"cron": {
		"0 23 * * *": [
			"logicore.logicore.doctype.vehicle_finance.vehicle_finance.create_emi_payments_for_today",
		],
	},
}

# Testing
# -------

# before_tests = "logicore.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "logicore.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	# CAPA FIX: Dashboard has no native `roles` table like Page/Report, and its own
	# get_permitted_charts/get_permitted_cards never check Dashboard-level permission
	# (frappe.get_doc without check_permission). Override with wrappers that add the
	# missing check against TMS User Group navigation_visibility_json.
	"frappe.desk.doctype.dashboard.dashboard.get_permitted_charts": "logicore.tms_navigation_visibility.get_permitted_charts",
	"frappe.desk.doctype.dashboard.dashboard.get_permitted_cards": "logicore.tms_navigation_visibility.get_permitted_cards",
	# CAPA FIX: core report_to_pdf() hard-codes a "proxy": "http://0.0.0.0:0"
	# wkhtmltopdf option meant to disable proxying — on this environment
	# wkhtmltopdf instead treats it as a real proxy and fails every PDF export
	# with "network error: ConnectionRefusedError". Override drops that option.
	"frappe.utils.print_format.report_to_pdf": "logicore.overrides.report_to_pdf.report_to_pdf",
	# CAPA FIX: Report View calls get_link_title once per row for every Link
	# column with show_title_field_in_link on, to show a friendly name instead
	# of the raw docname. For a blank field it sends the literal string "null"
	# as docname, and core's frappe.get_lazy_doc() throws DoesNotExistError for
	# it -- surfacing a "<Doctype> null not found" popup to every user who
	# opens the list, no hover or click needed. Override adds the same
	# falsy/nonexistent guard frappe.form.formatters.Link already has for the
	# Form-view equivalent.
	"frappe.desk.search.get_link_title": "logicore.overrides.link_title.get_link_title",
}

# override_whitelisted_methods = {
# 	"frappe.desk.reportview.export_query": "logicore.overrides.trip_export.export_query"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "logicore.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["logicore.utils.before_request"]
# after_request = ["logicore.utils.after_request"]

# Job Events
# ----------
# before_job = ["logicore.utils.before_job"]
# after_job = ["logicore.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

on_login = ["logicore.overrides.login_redirect.set_login_redirect"]

after_request = ["logicore.overrides.login_redirect.after_login_redirect"]

# auth_hooks = [
# 	"logicore.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
