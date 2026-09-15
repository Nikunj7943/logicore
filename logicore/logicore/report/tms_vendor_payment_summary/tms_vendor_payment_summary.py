import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "name",
			"label": _("Payment Ref"),
			"fieldtype": "Link",
			"options": "Vendor Payment",
			"width": 150,
		},
		{
			"fieldname": "payment_date",
			"label": _("Payment Date"),
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"fieldname": "vendor",
			"label": _("Vendor"),
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 160,
		},
		{
			"fieldname": "vendor_name",
			"label": _("Vendor Name"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "trip_count",
			"label": _("No. of Trips"),
			"fieldtype": "Int",
			"width": 90,
		},
		{
			"fieldname": "total_payment_amount",
			"label": _("Payment Amt"),
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"fieldname": "total_lr_money",
			"label": _("LR Money"),
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"fieldname": "total_tds_amount",
			"label": _("TDS"),
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"fieldname": "total_transfer_amount",
			"label": _("Transfer Amt"),
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"fieldname": "payment_entry",
			"label": _("Payment Entry"),
			"fieldtype": "Link",
			"options": "Payment Entry",
			"width": 150,
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 90,
		},
	]


def get_data(filters):
	conditions = ["tvp.docstatus IN (0, 1)"]
	params = {}

	if filters.get("vendor"):
		conditions.append("tvp.vendor = %(vendor)s")
		params["vendor"] = filters["vendor"]

	if filters.get("from_date"):
		conditions.append("tvp.payment_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("tvp.payment_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	if filters.get("company"):
		conditions.append("tvp.company = %(company)s")
		params["company"] = filters["company"]

	where = " AND ".join(conditions)

	data = frappe.db.sql(
		"""
		SELECT
			tvp.name,
			tvp.payment_date,
			tvp.vendor,
			s.supplier_name AS vendor_name,
			COUNT(tvpt.name) AS trip_count,
			tvp.total_payment_amount,
			tvp.total_lr_money,
			tvp.total_tds_amount,
			tvp.total_transfer_amount,
			tvp.payment_entry,
			CASE tvp.docstatus
				WHEN 0 THEN 'Draft'
				WHEN 1 THEN 'Submitted'
				WHEN 2 THEN 'Cancelled'
			END AS status
		FROM `tabVendor Payment` tvp
		LEFT JOIN `tabVendor Payment Trip` tvpt ON tvpt.parent = tvp.name
		LEFT JOIN `tabSupplier` s ON s.name = tvp.vendor
		WHERE {where}
		GROUP BY tvp.name
		ORDER BY tvp.payment_date DESC, tvp.name
		""".format(where=where),
		params,
		as_dict=True,
	)

	return data


def get_report_filters():
	return [
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
		},
		{
			"fieldname": "vendor",
			"label": _("Vendor"),
			"fieldtype": "Link",
			"options": "Supplier",
		},
		{
			"fieldname": "from_date",
			"label": _("From Date"),
			"fieldtype": "Date",
			"default": frappe.utils.add_months(frappe.utils.today(), -1),
			"reqd": 1,
		},
		{
			"fieldname": "to_date",
			"label": _("To Date"),
			"fieldtype": "Date",
			"default": frappe.utils.today(),
			"reqd": 1,
		},
	]
