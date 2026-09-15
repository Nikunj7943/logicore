import frappe


def sync_email_to_primary_contact(doc, method=None):
	# email_id is a core ERPNext "Read Only" fetch_from field (fed FROM
	# customer_primary_contact.email_id) -- a Property Setter (see install.py)
	# turned it into a normal editable Data field so users can type an email
	# directly on Customer without opening the Contact. That only fixes the
	# input side; without this, the typed value never reaches the Contact
	# record, so the next fetch_from refresh (or anyone opening the Contact
	# directly) would still see the old/blank email. This pushes it there.
	if not doc.customer_primary_contact or not doc.email_id:
		return

	email = doc.email_id.strip()
	if not email:
		return

	contact = frappe.get_doc("Contact", doc.customer_primary_contact)
	existing = next((row for row in contact.email_ids if row.email_id == email), None)
	if existing and existing.is_primary:
		return  # already in sync

	for row in contact.email_ids:
		row.is_primary = 0

	if existing:
		existing.is_primary = 1
	else:
		contact.append("email_ids", {"email_id": email, "is_primary": 1})

	contact.email_id = email
	contact.save(ignore_permissions=True)


def sync_mobile_to_primary_contact(doc, method=None):
	# Same fix as sync_email_to_primary_contact() above, for mobile_no ->
	# customer_primary_contact.mobile_no via the Contact's phone_nos child
	# table (is_primary_mobile_no flag), not email_ids.
	if not doc.customer_primary_contact or not doc.mobile_no:
		return

	mobile = doc.mobile_no.strip()
	if not mobile:
		return

	contact = frappe.get_doc("Contact", doc.customer_primary_contact)
	existing = next((row for row in contact.phone_nos if row.phone == mobile), None)
	if existing and existing.is_primary_mobile_no:
		return  # already in sync

	for row in contact.phone_nos:
		row.is_primary_mobile_no = 0

	if existing:
		existing.is_primary_mobile_no = 1
	else:
		contact.append("phone_nos", {"phone": mobile, "is_primary_mobile_no": 1})

	contact.mobile_no = mobile
	contact.save(ignore_permissions=True)
