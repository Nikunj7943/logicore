import frappe


def update_address_fields():
	addresses = frappe.db.sql(
		"""
		SELECT name, city, state, country
		FROM `tabAddress`
		""",
		as_dict=True,
	)

	updated = 0
	skipped = 0

	for addr in addresses:
		updates = {}

		# Use default city field to lookup state & country from tabCity
		if addr.city:
			city_doc = frappe.db.get_value("City", addr.city, ["state", "country"], as_dict=True)
			if city_doc:
				updates["state"] = city_doc.state
				updates["country"] = city_doc.country

		if updates:
			frappe.db.set_value("Address", addr.name, updates)
			print(f"Updated {addr.name}: {updates}")
			updated += 1
		else:
			skipped += 1

	frappe.db.commit()
	print(f"\nDone — Updated: {updated}, Skipped: {skipped}")
