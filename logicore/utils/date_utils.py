from datetime import date
from frappe.utils import today, getdate


def get_financial_year_start(ref_date=None):
	"""Indian FY: April 1 – March 31"""
	d = getdate(ref_date or today())
	return date(d.year, 4, 1) if d.month >= 4 else date(d.year - 1, 4, 1)


def get_fy_suffix(ref_date=None):
	d = getdate(ref_date or today())
	return d.strftime("%m%y")


def get_fy_key(ref_date=None):
	"""Indian FY as a 4-digit key, e.g. "2627" for FY 2026-27."""
	fy_start = get_financial_year_start(ref_date)
	return f"{str(fy_start.year)[2:]}{str(fy_start.year + 1)[2:]}"
