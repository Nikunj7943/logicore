import re

import frappe
from frappe.utils import flt


def get_supplier_tds_pct(supplier):
	"""TDS percentage for a supplier, read from the Supplier field
	`custom_tds_applicable` ("Zero TDS" / "1% TDS" / "2% TDS" / "Vendor Declined").

	Returns 0 for the options that carry no number, for suppliers without the
	field set, and for any lookup failure — callers treat 0 as "no TDS".
	"""
	try:
		value = frappe.db.get_value("Supplier", supplier, "custom_tds_applicable") or ""
		match = re.search(r"(\d+(?:\.\d+)?)", value)
		return flt(match.group(1)) if match else 0
	except Exception:
		return 0
