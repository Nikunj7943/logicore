import json

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

DOCTYPES = [
	"Purchase Invoice",
	"Stock Entry",
	"Payment Entry",
	"Leave Application",
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
]


def _set_core_sort(doctype, sort_field):
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
	print(f"OK core: {doctype} -> sort_field={sort_field}, sort_order=DESC")


def _clear_stale_user_sort_settings():
	rows = frappe.db.sql(
		"""select `user`, `doctype`, `data` from `__UserSettings`
		where `doctype` in %(doctypes)s""",
		{"doctypes": DOCTYPES},
		as_dict=True,
	)
	changed = 0
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
			changed += 1
	print(f"OK cleared stale sort settings on {changed} __UserSettings row(s)")


def execute():
	core_map = {
		"Purchase Invoice": "posting_date",
		"Stock Entry": "posting_date",
		"Payment Entry": "posting_date",
		"Leave Application": "posting_date",
	}
	for doctype, field in core_map.items():
		_set_core_sort(doctype, field)

	custom_doctypes = [d for d in DOCTYPES if d not in core_map]
	for doctype in custom_doctypes:
		frappe.reload_doctype(doctype, force=True)
		print(f"OK reload: {doctype}")

	_clear_stale_user_sort_settings()

	frappe.db.commit()

	print("\n--- verification ---")
	for doctype in DOCTYPES:
		meta = frappe.get_meta(doctype)
		print(f"{doctype}: sort_field={meta.sort_field}, sort_order={meta.sort_order}")
