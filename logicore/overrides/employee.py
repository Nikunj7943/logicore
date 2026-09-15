"""Employee <-> User linkage guards.

The "Employee User Automation" Server Script creates/links a Frappe User from
`company_email` and writes it back with `frappe.db.set_value("Employee", ..., "user_id", ...)`.
`db.set_value` skips validation entirely, so two Employees sharing a company_email
quietly ended up sharing a `user_id` -- and ERPNext's own validate_duplicate_user_id()
then rejected EVERY subsequent save of both records ("User X is already assigned to
Employee Y"), including edits that had nothing to do with email. The records became
unsaveable and the After Save automation never got a chance to repair them, because
it only runs once a save succeeds.

Two guards, both on the way in so the bad state can never form:

  validate()  -> no two Active Employees may claim the same company_email
  on_update() -> changing company_email RENAMES the existing User instead of
                 leaving it behind and creating a second one
"""

import frappe
from frappe import _


def before_validate(doc, method=None):
	# Both run before ERPNext's validate_duplicate_user_id(), which rejects the save
	# outright if `user_id` is still held by another Employee. Renaming from on_update
	# would never be reached: that check fires first and the save dies with the very
	# link the rename was about to resolve.
	if not _rename_user_on_company_email_change(doc):
		_release_stale_duplicate_user_id(doc)


def validate(doc, method=None):
	_validate_unique_company_email(doc)


def sync_user_default_company(doc, method=None):
	"""Keep the linked User's default Company in step with this Employee's.

	Payment/Supplier Payment (and any other doctype with a Link field named
	`company`) no longer hardcode a literal default — Frappe's own new-doc
	logic (frappe.defaults.get_user_default) fills the field from here instead,
	so the value follows whichever branch/company the logged-in user's own
	Employee record says they belong to, not a single company baked into the
	DocType JSON.
	"""
	user_id = (doc.get("user_id") or "").strip()
	company = (doc.get("company") or "").strip()
	if not user_id or not company or user_id in ("Administrator", "Guest"):
		return
	if frappe.defaults.get_user_default("company", user_id) != company:
		frappe.defaults.set_user_default("company", company, user=user_id)


def _will_rename_user(doc, user_id):
	"""True when a company_email change should carry the existing User along.

	Consulted from before_validate as well as on_update so the two never disagree --
	before_validate must not release a link that on_update is about to rename.
	"""
	if not doc.get("custom_application_access"):
		return False
	new_email = (doc.get("company_email") or "").strip()
	if not user_id or not new_email or user_id == new_email:
		return False
	if user_id in ("Administrator", "Guest"):
		return False
	# Nothing to move, or the destination address is already taken by an account of
	# its own -- either way the Server Script's link/create branch is the right path.
	return bool(frappe.db.exists("User", user_id)) and not frappe.db.exists("User", new_email)


def _release_stale_duplicate_user_id(doc):
	"""Drop this Employee's claim on a `user_id` that already belongs to another one.

	Runs in before_validate, ahead of ERPNext's validate_duplicate_user_id(), because
	that check makes an already-duplicated record permanently unsaveable: it rejects
	EVERY save, including the very edit that would resolve the duplicate. Someone
	changing their Company Email to a fresh address gets blocked by a `user_id` the
	edit was about to make obsolete anyway, with no way out from the UI.

	Ownership rule: the Employee whose `company_email` equals the `user_id` owns it,
	because company_email is what the Server Script turns into the login. So a record
	whose company_email points somewhere else is holding a stale link -- released here,
	after which the After Save automation relinks it from its own company_email.

	If both sides genuinely claim it (company_email matches on each), there is no
	rule that can pick a winner -- say so plainly instead of guessing.
	"""
	user_id = (doc.get("user_id") or "").strip()
	if not user_id or user_id in ("Administrator", "Guest"):
		return

	# Hold the link when on_update is about to rename this User onto the new address:
	# releasing it here would leave the rename with nothing to work from, and the
	# Server Script would mint a second account instead of moving the existing one.
	if _will_rename_user(doc, user_id):
		return

	rival = frappe.db.get_value(
		"Employee",
		{"user_id": user_id, "status": "Active", "name": ("!=", doc.name or "")},
		["name", "employee_name", "company_email"],
		as_dict=True,
	)
	if not rival:
		return

	mine = (doc.get("company_email") or "").strip().lower()
	theirs = (rival.company_email or "").strip().lower()
	claim = user_id.lower()

	if mine != claim:
		doc.user_id = None
		return

	if theirs != claim:
		# Their claim is the stale one; leave ours alone and let their next save
		# release it. Saving this record must not silently unlink someone else.
		return

	frappe.throw(
		_("User {0} is linked to both this Employee and {1} ({2}), and both use it as their Company Email. Change the Company Email on one of them first.").format(
			frappe.bold(user_id), frappe.bold(rival.name), rival.employee_name
		),
		title=_("Duplicate User Link"),
	)


def _validate_unique_company_email(doc):
	"""Company Email is what the automation turns into the User's login, so letting
	two Employees hold the same one is what produces the duplicate `user_id` deadlock.
	Blocked here rather than with a unique index on the column: one Employee already
	has a NULL company_email and the field is only ever written through the form/API,
	where this runs.

	Only Active employees conflict -- matching ERPNext's own user_id check, so a
	resigned employee's address can be reissued.
	"""
	email = (doc.get("company_email") or "").strip()
	if not email or doc.get("status") != "Active":
		return

	clash = frappe.db.get_value(
		"Employee",
		{
			"company_email": email,
			"status": "Active",
			"name": ("!=", doc.name or ""),
		},
		["name", "employee_name"],
		as_dict=True,
	)
	if clash:
		frappe.throw(
			_("Company Email {0} is already used by Employee {1} ({2}). Two employees cannot share it — it is the login of the user account created for them.").format(
				frappe.bold(email), frappe.bold(clash.name), clash.employee_name
			),
			title=_("Duplicate Company Email"),
		)


def _rename_user_on_company_email_change(doc):
	"""Follow a company_email change through to the User instead of stranding it.

	The Server Script's "user already exists?" branch only ever links or creates --
	it has no concept of the old address, so changing company_email left the previous
	User untouched and minted a second one. Renaming keeps a single account with its
	roles, permissions and document history intact, which is what changing an
	employee's email is meant to mean.

	Deliberately skipped when a User already exists under the new address (that
	account belongs to someone else, or to this employee already) -- the Server
	Script's own linking branch handles that case.

	When the old User is also linked from other Employees (the duplicate state this
	module exists to clean up), their links are cleared first. A rename rewrites every
	Link pointing at the account, so leaving them attached would silently move those
	employees onto an address that is not theirs; cleared, each one regenerates its own
	User from its own company_email on its next save.
	"""
	old_user = (doc.get("user_id") or "").strip()
	if not _will_rename_user(doc, old_user):
		return False

	new_email = (doc.get("company_email") or "").strip()

	for other in frappe.get_all(
		"Employee", filters={"user_id": old_user, "name": ("!=", doc.name)}, pluck="name"
	):
		frappe.db.set_value("Employee", other, "user_id", None, update_modified=False)

	# frappe.rename_doc (the top-level wrapper) has no ignore_permissions parameter,
	# and renaming a User needs it: whoever edits an Employee is not expected to hold
	# rename rights on User.
	from frappe.model.rename_doc import rename_doc

	rename_doc("User", old_user, new_email, force=True, ignore_permissions=True, show_alert=False)
	# Set on the in-memory doc, not via db_set: this runs before the row is written,
	# so the new value has to travel with the save (and past ERPNext's duplicate check).
	doc.user_id = new_email
	frappe.msgprint(
		_("User account {0} renamed to {1} to match the new Company Email.").format(
			frappe.bold(old_user), frappe.bold(new_email)
		),
		alert=True,
		indicator="green",
	)
	return True
