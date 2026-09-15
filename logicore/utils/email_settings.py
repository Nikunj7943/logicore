import frappe


def get_sender_for_doctype(reference_doctype):
	"""Look up the Email Account mapped to a doctype in Email Account Settings.

	Reads fresh from the DB on every call, so changing the mapping takes
	effect on the next email without any code change. Returns None (falls
	back to Frappe's default outgoing account) if no mapping exists.
	"""
	email_account = frappe.db.get_value(
		"Email Account Settings", {"reference_doctype": reference_doctype}, "email_account"
	)
	if not email_account:
		return None
	return frappe.db.get_value("Email Account", email_account, "email_id")
