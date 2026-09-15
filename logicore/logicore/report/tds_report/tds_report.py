import frappe
from frappe import _

from logicore.utils.tds_utils import get_supplier_tds_pct


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "vendor",
			"label": _("Transporter"),
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 160,
		},
		{
			"fieldname": "vendor_name",
			"label": _("Vendor Name"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "trips",
			"label": _("Trips"),
			"fieldtype": "Int",
			"width": 70,
		},
		{
			"fieldname": "total_vendor_freight",
			"label": _("Sum of Total Vendor Freight"),
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"fieldname": "total_tds",
			"label": _("Sum of Vendor Tds To Be Deducted"),
			"fieldtype": "Currency",
			"width": 190,
		},
		{
			"fieldname": "pan",
			"label": _("PAN"),
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"fieldname": "gstin",
			"label": _("GSTIN"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "tds_rate",
			"label": _("TDS Rate"),
			"fieldtype": "Data",
			"width": 80,
		},
	]


def get_data(filters):
	conditions = ["t.vendor IS NOT NULL", "t.trip_status != 'Cancel'"]
	params = {}

	company = filters.get("company") or frappe.defaults.get_user_default("Company")
	if company:
		conditions.append("t.company = %(company)s")
		params["company"] = company

		default_supplier = frappe.db.get_value("Company", company, "default_supplier")
		if default_supplier:
			conditions.append("t.vendor != %(default_supplier)s")
			params["default_supplier"] = default_supplier

	if filters.get("vendor"):
		conditions.append("t.vendor = %(vendor)s")
		params["vendor"] = filters["vendor"]

	if filters.get("from_date"):
		conditions.append("t.tcntrip_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("t.tcntrip_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	where = " AND ".join(conditions)

	rows = frappe.db.sql(
		"""
		SELECT
			t.vendor,
			s.supplier_name AS vendor_name,
			COUNT(DISTINCT t.name) AS trips,
			SUM(t.vendor_freight) AS total_vendor_freight,
			SUM(t.vendor_tds_to_be_deducted) AS total_tds,
			s.pan,
			s.gstin,
			s.custom_tds_applicable
		FROM `tabTrip` t
		LEFT JOIN `tabSupplier` s ON s.name = t.vendor
		WHERE {where}
		GROUP BY t.vendor
		ORDER BY vendor_name
		""".format(where=where),
		params,
		as_dict=True,
	)

	filtered_rows = []
	for row in rows:
		tds_pct = get_supplier_tds_pct(row["vendor"])
		del row["custom_tds_applicable"]
		if not tds_pct:
			continue
		row["tds_rate"] = f"{tds_pct:g}%"
		filtered_rows.append(row)

	return filtered_rows
