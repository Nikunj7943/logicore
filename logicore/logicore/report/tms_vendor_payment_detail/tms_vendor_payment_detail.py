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
			"fieldname": "payment_name",
			"label": _("Payment Ref"),
			"fieldtype": "Link",
			"options": "Vendor Payment",
			"width": 140,
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
			"width": 150,
		},
		{
			"fieldname": "trip",
			"label": _("Trip"),
			"fieldtype": "Link",
			"options": "Trip",
			"width": 130,
		},
		{
			"fieldname": "trip_date",
			"label": _("Trip Date"),
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"fieldname": "tcntrip_no",
			"label": _("TCN/Trip No"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "lr_no",
			"label": _("LR No"),
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"fieldname": "vehicle_no",
			"label": _("Vehicle No"),
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"fieldname": "hire_amount",
			"label": _("Hire Amount"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "balance",
			"label": _("Balance at Pmt"),
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"fieldname": "payment_amount",
			"label": _("Payment Amt"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "lr_money",
			"label": _("LR Money"),
			"fieldtype": "Currency",
			"width": 100,
		},
		{
			"fieldname": "tds_amount",
			"label": _("TDS"),
			"fieldtype": "Currency",
			"width": 90,
		},
		{
			"fieldname": "transfer_amount",
			"label": _("Transfer Amt"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "advance_or_balance",
			"label": _("Adv/Bal"),
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"fieldname": "payment_type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "row_remarks",
			"label": _("Remarks"),
			"fieldtype": "Data",
			"width": 150,
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

	if filters.get("payment_ref"):
		conditions.append("tvp.name = %(payment_ref)s")
		params["payment_ref"] = filters["payment_ref"]

	where = " AND ".join(conditions)

	data = frappe.db.sql(
		"""
		SELECT
			tvp.name            AS payment_name,
			tvp.payment_date,
			tvp.vendor,
			tvpt.trip,
			tvpt.trip_date,
			tvpt.tcntrip_no,
			tvpt.lr_no,
			tvpt.vehicle_no,
			tvpt.hire_amount,
			tvpt.balance,
			tvpt.payment_amount,
			tvpt.lr_money,
			tvpt.tds_amount,
			tvpt.transfer_amount,
			tvpt.advance_or_balance,
			tvpt.payment_type,
			tvpt.row_remarks
		FROM `tabVendor Payment Trip` tvpt
		INNER JOIN `tabVendor Payment` tvp ON tvp.name = tvpt.parent
		WHERE {where}
		ORDER BY tvp.payment_date DESC, tvp.name, tvpt.idx
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
		{
			"fieldname": "payment_ref",
			"label": _("Payment Reference"),
			"fieldtype": "Link",
			"options": "Vendor Payment",
		},
	]
