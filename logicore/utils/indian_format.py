def format_inr(value):
	"""Format a number as Indian Rupee string: ₹10,00,000.00"""
	try:
		v = float(value or 0)
	except (TypeError, ValueError):
		return "₹0.00"

	# Split into integer and decimal parts
	int_part = int(v)
	dec_part = round(v - int_part, 2)
	dec_str = f"{dec_part:.2f}"[1:]  # ".xx"

	# Indian grouping: last 3 digits, then groups of 2
	s = str(int_part)
	if len(s) > 3:
		last3 = s[-3:]
		rest = s[:-3]
		groups = []
		while len(rest) > 2:
			groups.append(rest[-2:])
			rest = rest[:-2]
		if rest:
			groups.append(rest)
		groups.reverse()
		s = ",".join(groups) + "," + last3
	return f"₹{s}{dec_str}"


def format_inr_short(value):
	"""₹10.50 L or ₹1.25 Cr for large values"""
	try:
		v = float(value or 0)
	except (TypeError, ValueError):
		return "₹0.00"

	if v >= 1e7:
		return f"₹{v / 1e7:.2f} Cr"
	if v >= 1e5:
		return f"₹{v / 1e5:.2f} L"
	return format_inr(v)
