from frappe.utils import flt, time_diff_in_hours


def calc_detention_days(free_hours, loading_dt, unloading_dt):
	"""Return detention days beyond free hours."""
	if not (loading_dt and unloading_dt):
		return 0
	hours = time_diff_in_hours(unloading_dt, loading_dt)
	excess_hours = max(0, hours - free_hours)
	return flt(excess_hours / 24, 2)


def calc_journey_time_days(distance_km, kms_per_day):
	"""Return ideal journey time in days at given KM/day rate."""
	if not distance_km or not kms_per_day:
		return 0
	return flt(distance_km / kms_per_day, 2)
