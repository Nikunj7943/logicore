import frappe

TMS_HOME_PAGE = "/app/logicore-tms"


def set_login_redirect():
	# on_login fires before set_user_info, so home_page is not yet set.
	# We patch it in after_request instead (see after_login_redirect below).
	pass


def after_login_redirect(response, request):
	"""after_request hook: override home_page to /app/logicore-tms on every login."""
	try:
		if request.path not in ("/api/method/login", "/login"):
			return

		data = response.get_json(silent=True, force=True)
		if not data or data.get("message") != "Logged In":
			return

		data["home_page"] = TMS_HOME_PAGE
		response.set_data(frappe.as_json(data))
	except Exception:
		pass
