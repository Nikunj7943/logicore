import frappe


def execute():
	addresses = frappe.db.sql(
		"""
		SELECT name, custom_cityname, custom_postal_code, city
		FROM `tabAddress`
		""",
		as_dict=True,
	)

	for addr in addresses:
		updates = {}

		# custom_cityname -> city (default field)
		if addr.custom_cityname:
			updates["city"] = addr.custom_cityname

		# custom_postal_code -> pincode (default field)
		if addr.custom_postal_code:
			updates["pincode"] = addr.custom_postal_code

		# city -> tabCity lookup -> state + country (default fields)
		city_name = addr.custom_cityname or addr.city
		if city_name:
			city_doc = frappe.db.get_value("City", city_name, ["state", "country"], as_dict=True)
			if city_doc:
				updates["state"] = city_doc.state
				updates["country"] = city_doc.country

		if updates:
			frappe.db.set_value("Address", addr.name, updates)

	# Clear custom fields — default fields use karne hain aage se
	frappe.db.sql("UPDATE `tabAddress` SET custom_cityname = NULL, custom_postal_code = NULL")

	# Remove mandatory from custom fields
	frappe.db.sql("""
		UPDATE `tabCustom Field`
		SET reqd = 0
		WHERE dt = 'Address'
		AND fieldname IN ('custom_cityname', 'custom_postal_code')
	""")

	# Unhide default address fields (city, pincode, state, country)
	frappe.db.sql("""
		UPDATE `tabProperty Setter`
		SET value = '0'
		WHERE doc_type = 'Address'
		AND field_name IN ('city', 'pincode', 'state', 'country')
		AND property = 'hidden'
	""")

	frappe.db.commit()
