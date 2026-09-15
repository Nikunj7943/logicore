import json
from pathlib import Path

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.model.document import Document
from frappe import _
from logicore.role_profile_sync import (
	FRAPPE_SYSTEM_ROLES,
	_save_unlocking_if_needed,
	enqueue_role_profile_sync,
	ensure_role_profile_for_role,
)
from logicore.overrides.login_redirect import TMS_HOME_PAGE

# Fieldtypes excluded from the field-permission popup's "currently visible fields"
# list: pure layout/UI (never real data fields) and child tables (a Grid isn't
# meaningfully toggled Hidden/Read-Only the same way a single-value field is — it
# always shows as-is, same as today, for every group).
LAYOUT_FIELDTYPES = {
	"Section Break", "Column Break", "Tab Break", "HTML", "Button",
	"Table", "Table MultiSelect",
}

# System fields that are never candidates for group-level field permission — their
# value is managed entirely by Frappe's own document lifecycle (e.g. amended_from is
# auto-set only when a cancelled submittable doc is amended), not business data a
# group's Hidden/Read-Only choice should apply to.
EXCLUDED_SYSTEM_FIELDNAMES = {"amended_from", "naming_series"}


class TMSUserGroup(Document):
	# ── Lifecycle ──────────────────────────────────────────────────────────

	def validate(self):
		if not self.group_name:
			frappe.throw(_("Group Name is mandatory"))
		self.group_name = self.group_name.strip()
		if self.group_name in FRAPPE_SYSTEM_ROLES:
			frappe.throw(
				_("'{0}' is a Frappe system role and cannot be managed as a TMS User Group.").format(
					self.group_name
				)
			)
		self._normalize_permissions()
		self._lock_navigation_visibility_to_db()

	def _lock_navigation_visibility_to_db(self):
		"""CAPA FIX: navigation_visibility_json is written EXCLUSIVELY by the dedicated
		set_navigation_visibility() whitelisted endpoint, called immediately on every toggle
		click. The normal document Save (this validate/save cycle) must never be able to write
		this field, no matter what value the client payload carries — whether it's a stale
		snapshot, a mid-toggle DOM state, or anything else. This makes the field fully
		server-owned: any client-side timing issue in the main form's save flow becomes
		structurally unable to revert a toggle, because this method always discards whatever
		the client sent and re-pulls the current DB value right before the row is written.

		For a brand-new (unsaved) document there is no DB row yet, so the client-supplied
		default is kept as-is.
		"""
		if self.is_new():
			# CAPA FIX (v2): store deny-by-default for EVERY new group, including is_admin.
			# Admin visibility is enforced by the READERS (nav bootinfo context, page/report
			# access sync, form UI) which all ignore hidden labels while is_admin=1. The
			# stored config is never destroyed, so unticking Is Admin later falls back to
			# the stored hidden list (deny-by-default) instead of leaving everything visible.
			# if self.is_admin:
			# 	self.navigation_visibility_json = frappe.as_json({"hidden_labels": []})
			# elif not self.navigation_visibility_json:
			if not self.navigation_visibility_json:
				# CAPA FIX: deny-by-default. Empty hidden_labels meant "everything visible",
				# so a brand-new group silently saw ALL dashboards/pages/reports. A new group
				# must start with every nav item hidden; only toggles the admin explicitly
				# turns ON become visible.
				# self.navigation_visibility_json = frappe.as_json({"hidden_labels": []})
				self.navigation_visibility_json = frappe.as_json(
					{"hidden_labels": _get_all_navigation_labels()}
				)
			return

		# CAPA FIX: use SELECT ... FOR UPDATE, not a plain read. A plain read-then-write here
		# can lose a concurrent set_navigation_visibility() write: if the user toggles and then
		# immediately clicks Save, both requests hit the DB in quick succession. Whichever
		# transaction's WRITE commits last always wins -- so if THIS save's read landed before
		# the toggle's write committed, this save would silently re-persist the pre-toggle value
		# and overwrite the correct one. FOR UPDATE takes a row lock, forcing this transaction to
		# wait for any in-flight set_navigation_visibility() write to commit first, so the value
		# read here is always genuinely the latest one.
		row = frappe.db.sql(
			"SELECT navigation_visibility_json FROM `tabTMS User Group` WHERE name=%s FOR UPDATE",
			self.name,
		)
		self.navigation_visibility_json = (row and row[0][0]) or frappe.as_json({"hidden_labels": []})

		# CAPA FIX (v2, superseded): clearing the json here DESTROYED the group's hidden
		# config permanently — tick + untick Is Admin left everything visible forever.
		# The stored config is now preserved; admin visibility is enforced by the readers
		# (get_tms_navigation_visibility_context, _sync_page_report_access_control, UI),
		# all of which ignore hidden labels while is_admin=1.
		# if self.is_admin:
		# 	self.navigation_visibility_json = frappe.as_json({"hidden_labels": []})

	def _normalize_permissions(self):
		cleaned_rows = []
		for row in self.permissions or []:
			document_type = (row.get("document_type") or "").strip()
			if not document_type:
				continue

			module = (row.get("module") or "").strip()
			if not module:
				module = frappe.db.get_value("DocType", document_type, "module") or ""
				if not module:
					continue
				row.module = module

			row.document_type = document_type
			cleaned_rows.append(row)

		if len(cleaned_rows) != len(self.permissions or []):
			self.set("permissions", cleaned_rows)

	# Superseded by _lock_navigation_visibility_to_db(), which now owns this field exclusively.
	# Kept for reference, not called.
	# def _normalize_navigation_visibility(self):
	# 	"""Keep the navigation visibility JSON valid and stable across saves."""
	# 	config = frappe.parse_json(self.navigation_visibility_json) or {}
	# 	hidden_labels = config.get("hidden_labels") or config.get("hidden") or []
	# 	if isinstance(hidden_labels, str):
	# 		hidden_labels = [hidden_labels]
	#
	# 	cleaned_hidden = []
	# 	seen = set()
	# 	for label in hidden_labels:
	# 		label = (label or "").strip()
	# 		if label and label not in seen:
	# 			cleaned_hidden.append(label)
	# 			seen.add(label)
	#
	# 	self.navigation_visibility_json = frappe.as_json({"hidden_labels": cleaned_hidden})

	def before_save(self):
		self._rename_target = None
		if not self.is_new() and self.group_name != self.name:
			self._rename_target = self.group_name
			self.group_name = self.name

	# CAPA FIX (superseded): moved to on_update. after_insert runs BEFORE on_update's
	# _sync_role(), so the group's Role doesn't exist yet and the Has Role inserts in
	# _sync_page_report_access_control failed with LinkValidationError. on_update's
	# has_value_changed("is_admin") is always True on insert (no doc_before_save), so
	# the sync still runs on every new group — just after the Role has been created.
	# def after_insert(self):
	# 	_sync_page_report_access_control()

	def on_update(self):
		if getattr(self, "_rename_target", None):
			frappe.rename_doc(
				"TMS User Group",
				self.name,
				self._rename_target,
				force=True,
			)
			frappe.clear_cache()
			return

		self._sync_role()
		self._sync_role_profile()
		self._sync_custom_docperms()
		self._sync_baseline_permissions()
		self._sync_field_permission_docperms()
		self._enqueue_role_profile_sync()
		self._invalidate_bootinfo()
		# CAPA FIX: recompute Page/Report `roles` tables when nav visibility just changed —
		# has_value_changed("is_admin") is True both on INSERT (new group starts all-hidden,
		# must be restricted immediately, not only when a toggle is clicked) and when Is Admin
		# is toggled on an existing group (admin sees everything). Placed after _sync_role()
		# so the group's Role exists before Has Role rows referencing it are inserted.
		if self.has_value_changed("is_admin"):
			_sync_page_report_access_control()
		frappe.clear_cache()

	def on_trash(self):
		if self.group_name in FRAPPE_SYSTEM_ROLES:
			frappe.throw(
				_("System role '{0}' cannot be deleted from TMS User Group.").format(self.group_name)
			)
		self._invalidate_bootinfo()
		self._validate_no_assigned_users()
		self._delete_linked_role_profile()
		self._delete_linked_role()

	def after_rename(self, old_name, new_name, merge=False):
		frappe.db.set_value("TMS User Group", new_name, "group_name", new_name, update_modified=False)

		# Sync Role: rename existing or create fresh if it never existed
		if frappe.db.exists("Role", old_name):
			frappe.rename_doc("Role", old_name, new_name, force=True)
		elif not frappe.db.exists("Role", new_name):
			is_active = frappe.db.get_value("TMS User Group", new_name, "is_active")
			frappe.get_doc({
				"doctype": "Role",
				"role_name": new_name,
				"desk_access": 1,
				"disabled": 0 if is_active else 1,
				"home_page": TMS_HOME_PAGE,
			}).insert(ignore_permissions=True)

		# Custom DocPerm rows still reference the old role name after Role rename.
		# Update them so permissions continue to work immediately.
		frappe.db.sql(
			"UPDATE `tabCustom DocPerm` SET role=%s WHERE role=%s",
			(new_name, old_name),
		)
		frappe.clear_cache(doctype="Custom DocPerm")

		# Sync Role Profile: rename by doc name first, then by role_profile field
		if frappe.db.exists("Role Profile", old_name):
			frappe.rename_doc("Role Profile", old_name, new_name, force=True)
			role_profile = frappe.get_doc("Role Profile", new_name)
			role_profile.role_profile = new_name
			for row in role_profile.roles or []:
				if row.role == old_name:
					row.role = new_name
			_save_unlocking_if_needed(role_profile)
		else:
			old_profile_name = frappe.db.get_value("Role Profile", {"role_profile": old_name}, "name")
			if old_profile_name:
				role_profile = frappe.get_doc("Role Profile", old_profile_name)
				role_profile.role_profile = new_name
				for row in role_profile.roles or []:
					if row.role == old_name:
						row.role = new_name
				_save_unlocking_if_needed(role_profile)
		self._invalidate_bootinfo()

	# ── Internal sync helpers ───────────────────────────────────────────────

	def _sync_role(self):
		role_name = self.group_name
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
				"disabled": 0 if self.is_active else 1,
				"home_page": TMS_HOME_PAGE,
			}).insert(ignore_permissions=True)
		else:
			frappe.db.set_value("Role", role_name, {
				"disabled": 0 if self.is_active else 1,
				"home_page": TMS_HOME_PAGE,
			})

		if not self.is_active:
			# frappe.get_roles() reads Has Role rows directly — Role.disabled alone does NOT
			# block access. We must delete the Has Role rows to revoke access immediately.
			# role_profiles child table is kept intact so reactivation can restore access.
			frappe.db.sql(
				"DELETE FROM `tabHas Role` WHERE role=%s AND parenttype='User'",
				role_name,
			)
		else:
			# Reactivation: restore Has Role rows for all users who still have this
			# group's profile assigned (role_profiles child table or deprecated field).
			_restore_has_role_for_profile(role_name)

	def _sync_role_profile(self):
		ensure_role_profile_for_role(self.group_name)

	def _enqueue_role_profile_sync(self):
		try:
			enqueue_role_profile_sync(self.group_name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Failed to enqueue role profile sync for {self.group_name}")

	def _invalidate_bootinfo(self):
		from logicore.tms_list_settings import invalidate_group_bootinfo

		invalidate_group_bootinfo(self.group_name)

	def _sync_custom_docperms(self):
		if self.flags.get("skip_custom_docperm_sync"):
			return

		role = self.group_name
		if frappe.db.get_value("Role", role, "disabled"):
			return

		# is_admin=1 → grant all permissions on all managed doctypes regardless of
		# what is stored in the permissions child table (which is disabled in the UI).
		_bulk_sync_custom_docperms(role, self.permissions, force_all=bool(self.is_admin))
		_ensure_protected_role_permissions()

	def _sync_baseline_permissions(self):
		if self.flags.get("skip_custom_docperm_sync"):
			return
		if frappe.db.get_value("Role", self.group_name, "disabled"):
			return
		_ensure_baseline_group_permissions([self.group_name])
		_ensure_protected_role_permissions(BASELINE_ALWAYS_GRANTED_DOCTYPES)

	def _sync_field_permission_docperms(self):
		"""Push this group's field_permissions (per-field Hidden/Read Only, real
		permlevel-based) into Custom DocPerm. is_admin groups skip only the
		customization step (their popup is disabled) — they still need the baseline
		grant, exactly like the doctype-level matrix's force_all=True.
		"""
		if self.flags.get("skip_custom_docperm_sync"):
			return
		# if self.is_admin:
		#     return
		# ^ used to return HERE, before the baseline backfill below. An is_admin group
		# that missed _backfill_field_permlevel_grants()'s one-time snapshot (created
		# or reactivated after a field got its permlevel) therefore had NO row at any
		# permlevel and could never repair itself — re-saving the group ran none of
		# this. Symptom: TMS-Admin at 0/44 permlevels on Trip, and since Trip's
		# sort_field (tcntrip_date) is permlevel-gated, every list query threw
		# "You do not have permission to access field: Trip.tcntrip_date".
		role = self.group_name
		if frappe.db.get_value("Role", role, "disabled"):
			return
		# A group created/reactivated AFTER a field's permlevel was already assigned (and
		# backfilled for every group active at that time) would otherwise have NO grant
		# at that permlevel at all -- missing row = deny, so it would silently lose
		# access to a field every other group can already see. Backfill this group up to
		# the same default-visible baseline before applying its own customizations.
		_ensure_field_permlevel_baseline_for_role(role)
		if self.is_admin:
			return
		_sync_field_permlevel_custom_docperms(role, self.field_permissions)

	# ── Validation & deletion helpers ──────────────────────────────────────

	def _validate_no_assigned_users(self):
		role_name = self.group_name
		profile_name = frappe.db.get_value("Role Profile", {"role_profile": role_name}, "name")

		# Direct role assignment (Has Role table)
		users_with_role = set(frappe.get_all(
			"Has Role",
			filters={"role": role_name, "parenttype": "User"},
			pluck="parent",
		))

		# Profile assignment — new way (Frappe v15 role_profiles child table)
		users_with_profile = set()
		if profile_name:
			users_with_profile = set(frappe.get_all(
				"User Role Profile",
				filters={"role_profile": profile_name, "parenttype": "User"},
				pluck="parent",
			))
			# Deprecated role_profile_name field (still used in some v15 installs)
			users_with_profile |= set(frappe.get_all(
				"User",
				filters={"role_profile_name": profile_name},
				pluck="name",
			))

		affected = sorted(users_with_role | users_with_profile)
		if affected:
			frappe.throw(
				_(
					"Cannot delete User Group <b>{0}</b>. It is assigned to {1} user(s): {2}.<br>"
					"Please unassign users first."
				).format(role_name, len(affected), ", ".join(affected))
			)

	def _delete_linked_role_profile(self):
		candidates = set()
		p = frappe.db.get_value("Role Profile", {"role_profile": self.group_name}, "name")
		if p:
			candidates.add(p)
		if frappe.db.exists("Role Profile", self.group_name):
			candidates.add(self.group_name)

		for profile_name in candidates:
			# Clear from Frappe v15 role_profiles child table
			frappe.db.sql(
				"DELETE FROM `tabUser Role Profile` WHERE role_profile=%s AND parenttype='User'",
				profile_name,
			)
			# Clear deprecated role_profile_name field
			frappe.db.sql(
				"UPDATE `tabUser` SET role_profile_name=NULL WHERE role_profile_name=%s",
				profile_name,
			)
			frappe.delete_doc("Role Profile", profile_name, ignore_permissions=True, force=True)

	def _delete_linked_role(self):
		role_name = self.group_name
		if not frappe.db.exists("Role", role_name):
			return

		# Remove all Custom DocPerm rows for this role on managed doctypes, plus
		# the always-on baseline doctypes (BASELINE_ALWAYS_GRANTED_DOCTYPES).
		managed = list(_get_managed_doctypes()) + list(BASELINE_ALWAYS_GRANTED_DOCTYPES)
		if managed:
			placeholders = ",".join(["%s"] * len(managed))
			frappe.db.sql(
				f"DELETE FROM `tabCustom DocPerm` WHERE role=%s AND parent IN ({placeholders})",
				[role_name] + managed,
			)

		# Remove Has Role assignments for this role from all users
		frappe.db.sql(
			"DELETE FROM `tabHas Role` WHERE role=%s",
			role_name,
		)

		frappe.delete_doc("Role", role_name, ignore_permissions=True, force=True)

	@frappe.whitelist()
	def sync_sidebar_doctypes(self):
		"""Housekeeping sync against workspace_sidebar.json for this TMS User Group.
		Removes permission rows for doctypes no longer in the sidebar. (Does NOT add
		rows for new doctypes — a missing row is already an explicit deny.)
		"""
		try:
			sidebar_path = Path(frappe.get_app_path("logicore", "workspace_sidebar", "logicore.json"))
			if not sidebar_path.exists():
				return

			with open(sidebar_path) as f:
				sidebar_data = json.load(f)

			sidebar_doctypes = set()

			for item in sidebar_data.get("items", []):
				if item.get("link_type") == "DocType" and item.get("type") == "Link":
					doctype = item.get("link_to")
					if doctype:
						sidebar_doctypes.add(doctype)

			existing_permissions = {row.document_type: row for row in (self.permissions or [])}
			changed = False

			# CAPA FIX (v2): do NOT add rows for missing sidebar doctypes at all. A missing
			# row is already an explicit deny in _bulk_sync_custom_docperms, so the all-zero
			# rows added here (v1 fix) were pure churn: every first open of a group saved
			# the doc, bumped `modified` behind the form's back (false TimestampMismatch on
			# the user's next Save), and the rows were deleted again by any client Save that
			# didn't know about them. This sync now only REMOVES rows for doctypes that are
			# no longer in the sidebar.
			# (v1 original bug: these rows defaulted to near-full access — write/create/
			# delete/print/report/import/export — silently granted on every form open.)
			# for doctype in sidebar_doctypes:
			# 	if doctype not in existing_permissions:
			# 		module = frappe.db.get_value("DocType", doctype, "module") or ""
			# 		self.append("permissions", {
			# 			"module": module,
			# 			"document_type": doctype,
			# 			# "perm_read": 1,
			# 			# "perm_write": 1,
			# 			# "perm_create": 1,
			# 			# "perm_delete": 1,
			# 			# "perm_print": 1,
			# 			# "perm_report": 1,
			# 			# "perm_import": 1,
			# 			# "perm_export": 1,
			# 			# "perm_select": 1,
			# 		})
			# 		changed = True

			# Remove doctypes no longer in sidebar
			rows_to_remove = []
			for doctype, row in existing_permissions.items():
				if doctype not in sidebar_doctypes:
					rows_to_remove.append(row)
					changed = True

			for row in rows_to_remove:
				self.permissions.remove(row)

			if changed:
				# CAPA FIX (preventive): this method is invoked from the client with `doc: frm.doc`,
				# so `self` is built from the browser payload. Its only job is to sync sidebar
				# doctypes into the permissions table — it must never persist a stale/empty
				# navigation_visibility_json and wipe the group's dashboard/page visibility.
				# Re-load the persisted value from DB before saving.
				self.navigation_visibility_json = frappe.db.get_value(
					"TMS User Group", self.name, "navigation_visibility_json"
				)
				self.flags.ignore_permissions = True
				self.flags.skip_custom_docperm_sync = False
				self.save(ignore_permissions=True)
				# CAPA FIX: this server-side save bumps `modified` behind the open form's
				# back. The form still holds the older timestamp, so the user's very next
				# Save (e.g. ticking Is Admin right after opening) raised a false
				# TimestampMismatchError. Return the fresh timestamp so the client can
				# update frm.doc.modified (same pattern as set_navigation_visibility).
				return {"changed": True, "modified": str(self.modified)}

			return {"changed": False}

		except Exception:
			frappe.log_error(frappe.get_traceback(), "Failed to sync sidebar doctypes")
			return {"changed": False}


# ── Module-level helpers ────────────────────────────────────────────────────


def _restore_has_role_for_profile(role_name):
	"""Re-add Has Role rows for users who still have this role's profile assigned.

	Called when a group is reactivated (is_active 0 → 1). Deactivation only removes
	Has Role rows; the role_profiles assignment is kept intact so we can restore here.
	Uses a single bulk INSERT IGNORE instead of a per-user loop.
	"""
	profile_name = frappe.db.get_value("Role Profile", {"role_profile": role_name}, "name")
	if not profile_name:
		return

	# Collect users from both Frappe v16 role_profiles table and deprecated field
	users_new = set(frappe.get_all(
		"User Role Profile",
		filters={"role_profile": profile_name, "parenttype": "User"},
		pluck="parent",
	))
	users_old = set(frappe.get_all(
		"User",
		filters={"role_profile_name": profile_name},
		pluck="name",
	))
	all_users = users_new | users_old
	if not all_users:
		return

	# Exclude users who already have the Has Role row
	existing = set(frappe.get_all(
		"Has Role",
		filters={"role": role_name, "parenttype": "User", "parent": ["in", list(all_users)]},
		pluck="parent",
	))
	to_restore = all_users - existing
	if not to_restore:
		return

	now = frappe.utils.now()
	admin = frappe.session.user or "Administrator"
	col_list = "name, creation, modified, modified_by, owner, parent, parenttype, parentfield, role"
	row_tpl = "(%s, %s, %s, %s, %s, %s, 'User', 'roles', %s)"
	placeholders = ", ".join([row_tpl] * len(to_restore))
	values = []
	for user in to_restore:
		values += [frappe.generate_hash(10), now, now, admin, admin, user, role_name]
	frappe.db.sql(
		f"INSERT IGNORE INTO `tabHas Role` ({col_list}) VALUES {placeholders}",
		values,
	)


def _ensure_protected_role_permissions(doctypes=None):
	"""Ensure admin access remains intact on managed doctypes.

	TMS User Group sync writes Custom DocPerm rows for business roles. Once any
	Custom DocPerm exists on a doctype, Frappe resolves permissions from that
	table first. To keep admin access stable across sites after migrate/sync, we
	explicitly grant full Custom DocPerm access to Administrator and System
	Manager on every managed doctype. For other protected roles, we only mirror
	file-based DocPerm rows when they exist.
	"""
	managed = list(doctypes or _get_managed_doctypes())
	if not managed:
		return

	full_admin_roles = ("Administrator", "System Manager")
	# Do not mirror broad default roles. "All" applies to every user and would
	# bypass TMS User Group grants; "Desk User" applies to most system users.
	mirror_roles = sorted(FRAPPE_SYSTEM_ROLES - {"Administrator", "System Manager", "All", "Guest", "Desk User"})
	protected_roles = sorted(set(full_admin_roles) | set(mirror_roles))
	native_rows = frappe.get_all(
		"DocPerm",
		filters={
			"parent": ["in", managed],
			"permlevel": 0,
			"role": ["in", mirror_roles],
		},
		fields=["parent", "role"] + list(PERM_MAP.keys()),
	)

	native_map = {
		(row.parent, row.role): {col: int(bool(row.get(col))) for col in PERM_MAP}
		for row in native_rows
	}

	existing_map = {
		(row.parent, row.role): row
		for row in frappe.get_all(
			"Custom DocPerm",
			filters={
				"parent": ["in", managed],
				"permlevel": 0,
				"role": ["in", protected_roles],
			},
			fields=["name", "parent", "role"] + list(PERM_MAP.keys()),
		)
	}

	stale_zero_rows = []
	for key, row in existing_map.items():
		native_perm = native_map.get(key) or {}
		if not native_perm or not any(native_perm.values()):
			continue
		if any(int(bool(row.get(col))) for col in PERM_MAP):
			continue
		stale_zero_rows.append(row.name)

	if stale_zero_rows:
		frappe.db.sql(
			f"DELETE FROM `tabCustom DocPerm` WHERE name IN ({','.join(['%s'] * len(stale_zero_rows))})",
			stale_zero_rows,
		)
		existing_map = {
			key: row for key, row in existing_map.items() if row.name not in set(stale_zero_rows)
		}

	now = frappe.utils.now()
	user = frappe.session.user or "Administrator"
	perm_cols = list(PERM_MAP.keys())
	to_insert = []
	to_update = []

	full_admin_set = set(full_admin_roles)
	full_perm_map = {col: 1 for col in perm_cols}

	for doctype in managed:
		for role in full_admin_roles:
			existing_row = existing_map.get((doctype, role))
			if existing_row:
				current_perm_map = {col: int(bool(existing_row.get(col))) for col in perm_cols}
				if current_perm_map != full_perm_map:
					to_update.append((existing_row.name, full_perm_map))
			else:
				to_insert.append((doctype, role, [1] * len(perm_cols)))

	for row in native_rows:
		if row.role in full_admin_set:
			continue
		if existing_map.get((row.parent, row.role)):
			continue
		perm_vals = [int(bool(row.get(col))) for col in perm_cols]
		to_insert.append((row.parent, row.role, perm_vals))

	if to_update:
		set_clause = ", ".join(f"`{col}` = %s" for col in perm_cols)
		update_sql = (
			f"UPDATE `tabCustom DocPerm` SET {set_clause}, modified=%s, modified_by=%s WHERE name=%s"
		)
		for name, perm_map in to_update:
			frappe.db.sql(update_sql, [perm_map[col] for col in perm_cols] + [now, user, name])

	if not to_insert and not to_update:
		return

	col_list = (
		"name, creation, modified, modified_by, owner, docstatus, idx, "
		"parent, role, permlevel, if_owner, "
		+ ", ".join(f"`{c}`" for c in perm_cols)
	)
	if to_insert:
		row_tpl = f"(%s, %s, %s, %s, %s, 0, 0, %s, %s, 0, 0, {', '.join(['%s'] * len(perm_cols))})"
		placeholders = ", ".join([row_tpl] * len(to_insert))
		values = []

		for doctype, role, perm_vals in to_insert:
			values += [frappe.generate_hash(length=10), now, now, user, user, doctype, role] + perm_vals

		frappe.db.sql(
			f"INSERT IGNORE INTO `tabCustom DocPerm` ({col_list}) VALUES {placeholders}",
			values,
		)
	frappe.clear_cache(doctype="Custom DocPerm")


def _ensure_baseline_group_permissions(roles=None):
	"""Grant Custom DocPerm access on BASELINE_ALWAYS_GRANTED_DOCTYPES to every TMS
	User Group role. Unlike the permissions matrix, this set is not exposed in the
	UI and can't be toggled off.

	Full access for all of them, EXCEPT doctypes listed in
	BASELINE_RESTRICTED_FOR_NON_ADMIN (currently just "User"): non-admin (is_admin=0)
	groups get only that doctype's reduced column set there — combined with the
	get_permission_query_conditions_user/has_permission_user hooks (see
	tms_navigation_visibility.py, wired in hooks.py), this means a normal user can see
	and edit only their own User record (e.g. change their own password), never anyone
	else's. is_admin=1 groups keep full access, same as before.

	roles=None syncs every active TMS User Group (used from install.after_migrate so
	existing groups converge on every migrate, without a one-time patch). Passing an
	explicit role list is used from on_update() for a single group.
	"""
	baseline = [dt for dt in BASELINE_ALWAYS_GRANTED_DOCTYPES if frappe.db.exists("DocType", dt)]
	if not baseline:
		return

	if roles is None:
		roles = frappe.get_all("TMS User Group", filters={"is_active": 1}, pluck="group_name")
	roles = [r for r in roles if r and r not in FRAPPE_SYSTEM_ROLES]
	if not roles:
		return

	role_is_admin = {
		r.group_name: bool(r.is_admin)
		for r in frappe.get_all(
			"TMS User Group", filters={"group_name": ["in", roles]}, fields=["group_name", "is_admin"]
		)
	}

	existing_map = {
		(r.parent, r.role): r
		for r in frappe.get_all(
			"Custom DocPerm",
			filters={"role": ["in", roles], "parent": ["in", baseline], "permlevel": 0},
			fields=["name", "parent", "role"] + BASELINE_PERM_COLUMNS,
		)
	}

	now = frappe.utils.now()
	user = frappe.session.user or "Administrator"
	full_perm_map = {col: 1 for col in BASELINE_PERM_COLUMNS}

	def _target_perm_map(doctype, role):
		restricted_cols = BASELINE_RESTRICTED_FOR_NON_ADMIN.get(doctype)
		if restricted_cols is not None and not role_is_admin.get(role):
			return {col: (1 if col in restricted_cols else 0) for col in BASELINE_PERM_COLUMNS}
		return full_perm_map

	to_insert = []
	to_update = []

	for role in roles:
		for doctype in baseline:
			target = _target_perm_map(doctype, role)
			existing_row = existing_map.get((doctype, role))
			if existing_row:
				current = {col: int(bool(existing_row.get(col))) for col in BASELINE_PERM_COLUMNS}
				if current != target:
					to_update.append((existing_row.name, target))
			else:
				to_insert.append((doctype, role, target))

	if to_update:
		for name, target in to_update:
			set_clause = ", ".join(f"`{col}` = %s" for col in BASELINE_PERM_COLUMNS)
			frappe.db.sql(
				f"UPDATE `tabCustom DocPerm` SET {set_clause}, modified=%s, modified_by=%s WHERE name=%s",
				[target[col] for col in BASELINE_PERM_COLUMNS] + [now, user, name],
			)

	if to_insert:
		col_list = (
			"name, creation, modified, modified_by, owner, docstatus, idx, "
			"parent, role, permlevel, if_owner, "
			+ ", ".join(f"`{c}`" for c in BASELINE_PERM_COLUMNS)
		)
		row_tpl = f"(%s, %s, %s, %s, %s, 0, 0, %s, %s, 0, 0, {', '.join(['%s']*len(BASELINE_PERM_COLUMNS))})"
		placeholders = ", ".join([row_tpl] * len(to_insert))
		values = []
		for doctype, role, target in to_insert:
			row_name = frappe.generate_hash(length=10)
			values += [row_name, now, now, user, user, doctype, role]
			values += [target[col] for col in BASELINE_PERM_COLUMNS]
		frappe.db.sql(
			f"INSERT IGNORE INTO `tabCustom DocPerm` ({col_list}) VALUES {placeholders}",
			values,
		)

	if to_insert or to_update:
		frappe.clear_cache(doctype="Custom DocPerm")


# Doctypes where "create" must never be granted via TMS sync, even for is_admin=1
# groups whose force_all otherwise grants every permission. Creating a new Company
# must stay limited to Frappe's real System Manager role / Administrator, never
# opened up to a TMS Admin group. Other permissions (read/write/etc.) on these
# doctypes still follow the normal matrix / force_all rules.
CREATE_LOCKED_DOCTYPES = {"Company"}


def _bulk_sync_custom_docperms(role, permission_rows, force_all=False):
	"""Bulk-sync TMS User Group permissions → Custom DocPerm table.

	force_all=True is used for is_admin=1 groups: all permissions are set to 1
	regardless of what the permissions child table contains.
	"""
	if role in FRAPPE_SYSTEM_ROLES:
		return

	managed_doctypes = list(_get_managed_doctypes())
	if not managed_doctypes:
		return

	granted = {row.document_type: row for row in (permission_rows or [])}

	existing_map = {
		r.parent: r.name
		for r in frappe.db.get_all(
			"Custom DocPerm",
			filters={"role": role, "parent": ["in", managed_doctypes], "permlevel": 0},
			fields=["name", "parent"],
		)
	}

	perm_cols = list(PERM_MAP.keys())
	now = frappe.utils.now()
	user = frappe.session.user or "Administrator"

	to_insert = []
	to_update = []
	deny_to_delete = []

	# Pass 1: identify stale explicit-deny rows to delete (only when not force_all)
	if not force_all:
		for doctype in managed_doctypes:
			if doctype in _NO_EXPLICIT_DENY and granted.get(doctype) is None:
				existing_name = existing_map.get(doctype)
				if existing_name:
					deny_to_delete.append(existing_name)

	if deny_to_delete:
		frappe.db.sql(
			f"DELETE FROM `tabCustom DocPerm` WHERE name IN ({','.join(['%s']*len(deny_to_delete))})",
			deny_to_delete,
		)

	# Pass 2: build insert / update lists
	for doctype in managed_doctypes:
		row = granted.get(doctype)

		if not force_all and doctype in _NO_EXPLICIT_DENY and row is None:
			continue

		if force_all:
			perm_vals = {ff: 1 for ff in PERM_MAP}
		elif row is not None:
			perm_vals = {ff: int(bool(getattr(row, cf, 0))) for ff, cf in PERM_MAP.items()}
		else:
			perm_vals = {ff: 0 for ff in PERM_MAP}

		if doctype in CREATE_LOCKED_DOCTYPES:
			perm_vals["create"] = 0

		existing_name = existing_map.get(doctype)
		if existing_name:
			to_update.append((existing_name, perm_vals))
		else:
			to_insert.append((doctype, perm_vals))

	if to_update:
		set_clause = ", ".join(f"`{col}` = %s" for col in perm_cols)
		update_sql = (
			f"UPDATE `tabCustom DocPerm` SET {set_clause}, modified=%s, modified_by=%s WHERE name=%s"
		)
		for name, pv in to_update:
			frappe.db.sql(update_sql, [pv[col] for col in perm_cols] + [now, user, name])

	if to_insert:
		col_list = (
			"name, creation, modified, modified_by, owner, docstatus, idx, "
			"parent, role, permlevel, if_owner, "
			+ ", ".join(f"`{c}`" for c in perm_cols)
		)
		row_tpl = f"(%s, %s, %s, %s, %s, 0, 0, %s, %s, 0, 0, {', '.join(['%s']*len(perm_cols))})"
		placeholders = ", ".join([row_tpl] * len(to_insert))
		values = []
		for doctype, pv in to_insert:
			row_name = frappe.generate_hash(length=10)
			values += [row_name, now, now, user, user, doctype, role] + [pv[c] for c in perm_cols]
		frappe.db.sql(
			f"INSERT IGNORE INTO `tabCustom DocPerm` ({col_list}) VALUES {placeholders}",
			values,
		)

	frappe.clear_cache(doctype="Custom DocPerm")


# ── Field-level permission (per-field Hidden / Read Only via real permlevel) ────


def _admin_group_roles() -> set:
	"""TMS User Group names with is_admin=1 -- these manage field-level and
	doctype-level permissions for every other role, so they must always have full
	access themselves, never the conservative read_only-field default (write=0)
	applied to ordinary roles. Their own field-permission popup is disabled (see
	_sync_field_permission_docperms), so unlike ordinary roles they have no way to
	override that default via the UI -- the baseline itself must grant them write.
	"""
	return set(frappe.get_all("TMS User Group", filters={"is_admin": 1}, pluck="group_name"))


def is_permlevel_protected_field(doctype, fieldname) -> bool:
	"""True for fields that must never be permlevel-gated.

	A doctype's sort_field goes into ORDER BY on EVERY list query, and Frappe's query
	engine THROWS PermissionError on an unpermitted order-by field rather than
	dropping it (frappe/database/query.py check_filter_field_permission). So gating a
	sort_field doesn't hide one column — it kills the entire list view for any role
	missing a grant at that permlevel. Trip.tcntrip_date is exactly this case.
	"""
	try:
		meta = frappe.get_meta(doctype)
	except Exception:
		return False
	sort_field = (meta.sort_field or "").strip()
	return bool(sort_field) and sort_field == (fieldname or "").strip()


def _assign_permlevel_for_field(doctype, fieldname):
	"""Ensure `fieldname` on `doctype` has its own unique, never-reused permlevel (>0),
	assigning one via Property Setter on first use and backfilling full access for every
	currently-active group + admin roles so the field's visibility never changes for
	anyone until a group explicitly restricts it via the field-permission popup. Returns
	the field's permlevel (existing or newly assigned).
	"""
	existing = frappe.db.get_value(
		"Property Setter",
		{"doc_type": doctype, "field_name": fieldname, "property": "permlevel"},
		"value",
	)
	if existing:
		return frappe.utils.cint(existing)

	max_level = frappe.db.sql(
		"SELECT MAX(CAST(value AS UNSIGNED)) FROM `tabProperty Setter` "
		"WHERE doctype_or_field='DocField' AND property='permlevel'"
	)[0][0]
	new_level = frappe.utils.cint(max_level or 0) + 1

	make_property_setter(doctype, fieldname, "permlevel", new_level, "Int")

	df = frappe.get_meta(doctype).get_field(fieldname)
	_backfill_field_permlevel_grants(doctype, new_level, read_only=bool(df and df.read_only))

	return new_level


def _backfill_field_permlevel_grants(doctype, permlevel, read_only=False):
	"""Grant every currently-active TMS User Group + Administrator + System Manager
	access at `permlevel` for `doctype`, so a field's first-ever permlevel assignment
	never hides it from anyone who could already see it. `read_only=True` grants
	read-only (for fields that were already structurally read_only=1); otherwise full
	read+write. Only a group's own explicit Hidden/Read Only choice in the field
	permission popup (synced via _sync_field_permlevel_custom_docperms) changes this
	afterwards.
	"""
	roles = frappe.get_all("TMS User Group", filters={"is_active": 1}, pluck="group_name")
	roles = [r for r in roles if r not in FRAPPE_SYSTEM_ROLES]
	roles += ["Administrator", "System Manager"]
	if not roles:
		return

	existing_roles = set(frappe.get_all(
		"Custom DocPerm",
		filters={"parent": doctype, "permlevel": permlevel, "role": ["in", roles]},
		pluck="role",
	))
	to_insert = [r for r in roles if r not in existing_roles]
	if not to_insert:
		return

	now = frappe.utils.now()
	user = frappe.session.user or "Administrator"
	admin_roles = _admin_group_roles()
	default_write_val = 0 if read_only else 1
	col_list = (
		"name, creation, modified, modified_by, owner, docstatus, idx, "
		"parent, role, permlevel, if_owner, `read`, `write`"
	)
	row_tpl = "(%s, %s, %s, %s, %s, 0, 0, %s, %s, %s, 0, 1, %s)"
	placeholders = ", ".join([row_tpl] * len(to_insert))
	values = []
	for role in to_insert:
		write_val = 1 if role in admin_roles else default_write_val
		values += [frappe.generate_hash(length=10), now, now, user, user, doctype, role, permlevel, write_val]
	frappe.db.sql(
		f"INSERT IGNORE INTO `tabCustom DocPerm` ({col_list}) VALUES {placeholders}",
		values,
	)
	frappe.clear_cache(doctype="Custom DocPerm")


def _ensure_field_permlevel_baseline_for_role(role):
	"""Backfill full access (or read-only, for structurally-read-only fields) at every
	field-permlevel already assigned SO FAR, for any permlevel this role has no
	explicit Custom DocPerm row at yet.

	_backfill_field_permlevel_grants() only runs once, at the moment a field FIRST
	gets its permlevel, and only covers groups active at that instant. A group
	created (or reactivated) afterwards would otherwise have NO row at all for that
	permlevel — missing row = deny — silently losing access to a field every other
	group can already see. This makes every group converge on the same default-visible
	baseline before its own explicit Hidden/Read Only customizations are applied.

	is_admin groups (_admin_group_roles()) always get write=1 here regardless of the
	field's read_only flag, and any of their existing rows still stuck at write=0 from
	before this carve-out existed are upgraded in place — their field-permission popup
	is disabled (see _sync_field_permission_docperms), so the baseline is the only place
	that can ever grant them write on a structurally read_only field, and they are the
	role that configures everyone else's permissions, so they must never end up
	locked out of a field (e.g. an auto-filled read_only field like TMS Bank
	Reconciliation.reconciliation_setting) that a save legitimately needs to write.
	"""
	assignments = frappe.get_all(
		"Property Setter",
		filters={"doctype_or_field": "DocField", "property": "permlevel"},
		fields=["doc_type", "field_name", "value"],
	)
	if not assignments:
		return

	role_is_admin_group = role in _admin_group_roles()

	if role_is_admin_group:
		frappe.db.sql(
			"UPDATE `tabCustom DocPerm` SET `write`=1 WHERE role=%s AND permlevel>0 AND `write`=0",
			(role,),
		)

	existing = {
		(r.parent, r.permlevel)
		for r in frappe.get_all(
			"Custom DocPerm",
			filters={"role": role, "permlevel": [">", 0]},
			fields=["parent", "permlevel"],
		)
	}

	now = frappe.utils.now()
	user = frappe.session.user or "Administrator"
	to_insert = []
	for row in assignments:
		permlevel = frappe.utils.cint(row.value)
		key = (row.doc_type, permlevel)
		if not permlevel or key in existing:
			continue
		# A Property Setter outlives the DocType it points at (removed/renamed doctype),
		# and get_meta() throws DoesNotExistError on those — without this guard one stale
		# row aborts the whole backfill and every role silently keeps its permlevel gaps.
		try:
			df = frappe.get_meta(row.doc_type).get_field(row.field_name)
		except Exception:
			continue
		write_val = 1 if role_is_admin_group else (0 if (df and df.read_only) else 1)
		to_insert.append((row.doc_type, permlevel, write_val))

	if not to_insert:
		frappe.clear_cache(doctype="Custom DocPerm")
		return

	col_list = (
		"name, creation, modified, modified_by, owner, docstatus, idx, "
		"parent, role, permlevel, if_owner, `read`, `write`"
	)
	row_tpl = "(%s, %s, %s, %s, %s, 0, 0, %s, %s, %s, 0, 1, %s)"
	placeholders = ", ".join([row_tpl] * len(to_insert))
	values = []
	for doctype, permlevel, write_val in to_insert:
		values += [frappe.generate_hash(length=10), now, now, user, user, doctype, role, permlevel, write_val]
	frappe.db.sql(
		f"INSERT IGNORE INTO `tabCustom DocPerm` ({col_list}) VALUES {placeholders}",
		values,
	)
	frappe.clear_cache(doctype="Custom DocPerm")


def ensure_field_permlevel_baseline_all_groups():
	"""Repair every active group's field-permlevel baseline, then re-apply each
	group's own Hidden/Read Only choices on top.

	_backfill_field_permlevel_grants() only ever covers the groups that were active
	at the instant a field FIRST got its permlevel, and _sync_field_permission_docperms()
	only repairs a group when that group is saved. A group created afterwards is left
	with no grant at all until someone happens to re-save it — and before the fix in
	_sync_field_permission_docperms(), an is_admin group was never repaired at all.
	Run from after_migrate so a deploy heals existing sites without anyone touching
	each group by hand.

	Covers inactive groups too. A permlevel row grants nothing on its own — doctype
	access is decided at permlevel 0 by the separate doctype-level matrix, and a row at
	permlevel > 0 only un-hides a field for someone who already has that access. So
	this cannot widen an inactive group's permissions (see the deny-by-default rule),
	but it does mean reactivating a group later can never surprise anyone with fields
	missing just because they were inactive when a permlevel was handed out.
	"""
	groups = frappe.get_all("TMS User Group", fields=["name", "group_name", "is_admin"])
	for group in groups:
		role = group.group_name
		if role in FRAPPE_SYSTEM_ROLES or frappe.db.get_value("Role", role, "disabled"):
			continue
		_ensure_field_permlevel_baseline_for_role(role)
		if group.is_admin:
			continue
		# The baseline grants full access at EVERY permlevel, which would silently undo
		# a group's own Hidden/Read Only choices — re-apply them straight after.
		rows = frappe.get_all(
			"TMS User Group Field Permission",
			filters={"parent": group.name, "parenttype": "TMS User Group"},
			fields=["document_type", "permlevel", "field_state"],
		)
		_sync_field_permlevel_custom_docperms(role, rows)

	for role in ("Administrator", "System Manager"):
		_ensure_field_permlevel_baseline_for_role(role)


def _sync_field_permlevel_custom_docperms(role, field_permission_rows):
	"""Turn a group's field_permissions rows into real Custom DocPerm grants, one row
	per (doctype, field's own unique permlevel). Each field has its own permlevel, so
	this is a straightforward per-field mapping — no bucket-sharing/cross-field effects.

	Every permlevel>0 Custom DocPerm row for a TMS User Group role belongs exclusively
	to this field-permission feature (permlevel 0 is the separate doctype-level matrix;
	nothing else in this app uses permlevel). So ANY such row that is no longer
	referenced by a current field_permissions row (the admin removed it, i.e. set the
	field back to "Default") must be reconciled back to full access here — otherwise a
	field that was once Hidden/Read Only would stay stuck at that stale state forever
	after being reverted to Default in the UI.
	"""
	if role in FRAPPE_SYSTEM_ROLES:
		return

	targets = {
		(r.document_type, r.permlevel): r.field_state
		for r in (field_permission_rows or [])
		if r.permlevel
	}

	existing_map = {
		(r.parent, r.permlevel): r
		for r in frappe.get_all(
			"Custom DocPerm",
			filters={"role": role, "permlevel": [">", 0]},
			fields=["name", "parent", "permlevel", "read", "write"],
		)
	}

	now = frappe.utils.now()
	user = frappe.session.user or "Administrator"
	to_delete = []

	for key in set(existing_map) | set(targets):
		doctype, permlevel = key
		state = targets.get(key)  # None => row removed, i.e. back to Default
		existing_row = existing_map.get(key)
		want_read_write = (1, 0) if state == "Read Only" else (1, 1)  # Hidden handled below

		if state == "Hidden":
			if existing_row:
				to_delete.append(existing_row.name)
			continue

		if existing_row:
			if (existing_row.read, existing_row.write) != want_read_write:
				frappe.db.sql(
					"UPDATE `tabCustom DocPerm` SET `read`=%s, `write`=%s, modified=%s, modified_by=%s WHERE name=%s",
					(*want_read_write, now, user, existing_row.name),
				)
		else:
			frappe.db.sql(
				"INSERT IGNORE INTO `tabCustom DocPerm` "
				"(name, creation, modified, modified_by, owner, docstatus, idx, "
				" parent, role, permlevel, if_owner, `read`, `write`) "
				"VALUES (%s, %s, %s, %s, %s, 0, 0, %s, %s, %s, 0, %s, %s)",
				(frappe.generate_hash(length=10), now, now, user, user, doctype, role, permlevel, *want_read_write),
			)

	if to_delete:
		frappe.db.sql(
			f"DELETE FROM `tabCustom DocPerm` WHERE name IN ({','.join(['%s']*len(to_delete))})",
			to_delete,
		)

	frappe.clear_cache(doctype="Custom DocPerm")


# ── Whitelisted API endpoints ───────────────────────────────────────────────


@frappe.whitelist()
def get_permission_matrix():
	doctype_names = set(_get_managed_doctypes())
	return _group_doctypes_by_workspace_hierarchy(doctype_names, APP_MODULE)


@frappe.whitelist()
def get_baseline_permission_matrix(group_name=None):
	"""Read-only info for the form's "Internal Permission" button: the doctypes and
	columns every TMS User Group role always has access to (BASELINE_ALWAYS_GRANTED_DOCTYPES).
	Informational only — never editable from the UI.

	Most of these give full access identically to every group. A few (see
	BASELINE_RESTRICTED_FOR_NON_ADMIN, e.g. "User") give non-admin groups only a
	reduced column set — group_name (the group currently open in the form) is used
	to reflect the real per-group state instead of always showing everything granted.
	"""
	is_admin = bool(frappe.db.get_value("TMS User Group", group_name, "is_admin")) if group_name else True

	perm_map = {}
	for dt in BASELINE_ALWAYS_GRANTED_DOCTYPES:
		restricted_cols = BASELINE_RESTRICTED_FOR_NON_ADMIN.get(dt)
		if restricted_cols is not None and not is_admin:
			perm_map[dt] = {col: (col in restricted_cols) for col in BASELINE_PERM_COLUMNS}
		else:
			perm_map[dt] = dict.fromkeys(BASELINE_PERM_COLUMNS, True)

	return {
		"doctypes": list(BASELINE_ALWAYS_GRANTED_DOCTYPES),
		"columns": [c.capitalize() for c in BASELINE_PERM_COLUMNS],
		"perm_map": perm_map,
	}


@frappe.whitelist()
def get_navigation_visibility_matrix():
	return _group_navigation_items_by_workspace_hierarchy(APP_MODULE)


@frappe.whitelist()
def get_navigation_visibility_config(group_name):
	"""Return navigation_visibility_json for a TMS User Group (hidden field, not accessible via get_value)."""
	if not group_name:
		return ""
	return frappe.db.get_value("TMS User Group", group_name, "navigation_visibility_json") or ""


@frappe.whitelist()
def set_navigation_visibility(name, hidden_labels):
	"""CAPA FIX: persist a nav-visibility toggle immediately, independent of the full doc
	Save/before_save pipeline. Called directly from the toggle's onchange handler so a toggle
	can never be silently reverted by an unrelated client-side save-cycle race.
	"""
	if not name:
		frappe.throw(_("Group name is required"))
	if not frappe.has_permission("TMS User Group", "write", doc=name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	hidden_labels = frappe.parse_json(hidden_labels) or []
	if isinstance(hidden_labels, str):
		hidden_labels = [hidden_labels]

	# CAPA FIX (v2): is_admin group → toggles are locked; this endpoint is a NO-OP.
	# (v1 forced hidden_labels=[] and WROTE it, which destroyed the stored config —
	# unticking Is Admin later left everything visible.) Return current values so the
	# client callback stays consistent without touching the stored config.
	if frappe.db.get_value("TMS User Group", name, "is_admin"):
		# hidden_labels = []
		return {
			"navigation_visibility_json": frappe.db.get_value(
				"TMS User Group", name, "navigation_visibility_json"
			) or "",
			"modified": frappe.db.get_value("TMS User Group", name, "modified"),
		}

	cleaned = []
	seen = set()
	for label in hidden_labels:
		label = (label or "").strip()
		# CAPA FIX: "Home" (the root Workspace) is never manageable per-group -- always
		# accessible regardless of what the client sends. Defense-in-depth alongside the
		# matrix-builder already excluding it from the toggle UI.
		if label and label != "Home" and label not in seen:
			cleaned.append(label)
			seen.add(label)

	# This field is written via a direct DB bypass (see the CAPA FIX note above), so it
	# never goes through doc.save() and never creates a Version -- unlike every other
	# change on this doctype, a toggle here would otherwise leave NO trace in the
	# Activity timeline. Diff old vs new before overwriting so we can log an explicit
	# audit comment recording exactly which items were shown/hidden.
	old_json = frappe.db.get_value("TMS User Group", name, "navigation_visibility_json") or ""
	try:
		old_hidden = set(frappe.parse_json(old_json).get("hidden_labels") or [])
	except Exception:
		old_hidden = set()
	new_hidden = set(cleaned)
	newly_shown = sorted(old_hidden - new_hidden)
	newly_hidden = sorted(new_hidden - old_hidden)

	value = frappe.as_json({"hidden_labels": cleaned})
	frappe.db.set_value("TMS User Group", name, "navigation_visibility_json", value, update_modified=True)
	frappe.db.commit()

	if newly_shown or newly_hidden:
		parts = []
		if newly_shown:
			parts.append(_("made visible: {0}").format(", ".join(newly_shown)))
		if newly_hidden:
			parts.append(_("hidden: {0}").format(", ".join(newly_hidden)))
		frappe.get_doc("TMS User Group", name).add_comment("Info", "; ".join(parts))

	from logicore.tms_list_settings import invalidate_group_bootinfo

	invalidate_group_bootinfo(name)
	_sync_page_report_access_control()
	# CAPA FIX: commit moved here from inside _sync_page_report_access_control() so that
	# the sync helper stays transaction-neutral — it is now also called from after_insert(),
	# where a forced mid-transaction commit could persist a half-saved document.
	frappe.db.commit()

	# CAPA FIX: this write bumps the doc's `modified` timestamp on the server, but the
	# already-open form still holds the OLDER timestamp from when it was loaded. Frappe's
	# next Save would then see DB.modified > frm.doc.modified and raise a false-positive
	# TimestampMismatchError ("modified after you opened it"). Return the fresh timestamp so
	# the client can update frm.doc.modified and keep the Save button's conflict check valid.
	new_modified = frappe.db.get_value("TMS User Group", name, "modified")
	return {"navigation_visibility_json": value, "modified": new_modified}


def _get_all_navigation_labels():
	"""All manageable nav item labels (dashboards/pages/reports) from the sidebar matrix.

	Used as the deny-by-default hidden list for brand-new groups. "Home" is already
	excluded by the matrix builder, so it always stays visible.
	"""
	labels = []
	seen = set()
	for group in _group_navigation_items_by_workspace_hierarchy(APP_MODULE):
		for item in group.get("items", []):
			label = (item.get("label") or "").strip()
			if label and label not in seen:
				labels.append(label)
				seen.add(label)
	return labels


def _resolve_nav_item_target(item):
	"""Return (target_doctype, target_name) for a Page/Report nav item, or None.

	Dashboard items are NOT handled here -- Dashboard has no native `roles` table, so it is
	blocked separately via an override on get_permitted_charts/get_permitted_cards.
	"""
	link_type = (item.get("link_type") or "").strip()
	if link_type == "Report":
		return ("Report", (item.get("link_to") or "").strip())
	if link_type == "Page":
		return ("Page", (item.get("link_to") or "").strip())
	if link_type == "URL":
		# Sidebar URL items that route to /app/<page-name> are backed by a real Page record
		# (e.g. "Alert Center" -> /app/alert-center -> Page "alert-center").
		url = (item.get("url") or "").strip()
		if "/app/" in url:
			page_name = url.split("/app/", 1)[1].strip("/")
			if page_name and frappe.db.exists("Page", page_name):
				return ("Page", page_name)
	return None


def _sync_page_report_access_control():
	"""CAPA FIX: Page and Report bypass the has_permission hook chain entirely -- both use
	their own is_permitted() method that checks their native `roles` child table (Has Role)
	directly (see Page.is_permitted / Report.is_permitted in frappe core). Hiding an item
	from a TMS User Group's sidebar therefore does NOTHING to actually restrict direct-URL
	access unless that group's Role is also removed from the target Page/Report's `roles`
	table. This function is the single source of truth that keeps those tables in sync with
	every TMS User Group's navigation_visibility_json.

	Rule: if no group hides an item, its `roles` table is cleared (open access, matching
	default Frappe behavior -- an empty roles table means "everyone allowed"). If at least
	one group hides it, the table is set to exactly the roles of groups that still show it,
	plus Administrator/System Manager, so admin access is never accidentally locked out.
	"""
	matrix = _group_navigation_items_by_workspace_hierarchy(APP_MODULE)
	items_by_label = {}
	for group in matrix:
		for item in group.get("items", []):
			label = item.get("label")
			if label:
				items_by_label[label] = item
	if not items_by_label:
		return

	groups = frappe.get_all(
		"TMS User Group",
		filters={"is_active": 1},
		fields=["name", "navigation_visibility_json", "is_admin"],
	)

	all_group_names = [g.name for g in groups]
	hidden_by_label = {label: [] for label in items_by_label}
	for g in groups:
		# CAPA FIX: is_admin group never hides anything — ignore any stale hidden labels
		# in its json so an admin group can never end up excluded from a Page/Report.
		if g.is_admin:
			continue
		config = frappe.parse_json(g.navigation_visibility_json) or {}
		for label in config.get("hidden_labels") or []:
			if label in hidden_by_label:
				hidden_by_label[label].append(g.name)

	protected_roles = {"Administrator", "System Manager"}

	for label, item in items_by_label.items():
		target = _resolve_nav_item_target(item)
		if not target:
			continue
		target_doctype, target_name = target
		if not target_name or not frappe.db.exists(target_doctype, target_name):
			continue

		hiding_groups = set(hidden_by_label.get(label) or [])
		existing_roles = set(frappe.get_all(
			"Has Role",
			filters={"parent": target_name, "parenttype": target_doctype},
			pluck="role",
		))

		if not hiding_groups:
			# Nobody hides this item -- clear restrictions entirely (open access).
			if existing_roles:
				frappe.db.delete("Has Role", {"parent": target_name, "parenttype": target_doctype})
			continue

		allowed_roles = protected_roles | {g for g in all_group_names if g not in hiding_groups}
		to_add = allowed_roles - existing_roles
		to_remove = existing_roles - allowed_roles

		if to_remove:
			frappe.db.delete(
				"Has Role",
				{"parent": target_name, "parenttype": target_doctype, "role": ["in", list(to_remove)]},
			)
		for role in to_add:
			frappe.get_doc({
				"doctype": "Has Role",
				"parent": target_name,
				"parenttype": target_doctype,
				"parentfield": "roles",
				"role": role,
			}).insert(ignore_permissions=True)

	# CAPA FIX: commit removed from here (moved to set_navigation_visibility). This helper
	# is also called from after_insert() now, where committing mid-save is unsafe.
	# frappe.db.commit()


@frappe.whitelist()
def get_role_permissions(group_name):
	"""Return effective permissions for this role across all managed doctypes.

	Custom DocPerm takes precedence over file-based DocPerm, matching Frappe's own resolution.
	"""
	if not group_name:
		return {}

	managed_doctypes = _get_managed_doctypes()
	if not managed_doctypes:
		return {}

	result = {}

	for r in frappe.get_all(
		"DocPerm",
		filters={"role": group_name, "permlevel": 0, "parent": ["in", managed_doctypes]},
		fields=_PERM_FIELDS,
	):
		result[r.parent] = _row_to_perm_dict(r)

	for r in frappe.get_all(
		"Custom DocPerm",
		filters={"role": group_name, "permlevel": 0, "parent": ["in", managed_doctypes]},
		fields=_PERM_FIELDS,
	):
		result[r.parent] = _row_to_perm_dict(r)

	return result


@frappe.whitelist()
def get_form_bundle(group_name=None, include_doc=0):
	"""Combined endpoint for the TMS User Group form's client JS.

	Bundles get_permission_matrix(), get_navigation_visibility_matrix(),
	get_role_permissions(), and get_navigation_visibility_config() into ONE round-trip
	instead of four separate frappe.call()s -- each of those competes for the browser's
	per-origin connection limit alongside sync_sidebar_doctypes(), stretching a group
	switch's wall-clock wait well past any single call's own server time. Optionally
	returns a fresh copy of the group doc itself (include_doc=1), equivalent to
	frappe.client.get, so a document switch never needs a second network wave to
	guarantee frm.doc is current.
	"""
	group_name = (group_name or "").strip()
	result = {
		"matrix": get_permission_matrix(),
		"nav_matrix": get_navigation_visibility_matrix(),
		"role_permissions": {},
		"navigation_visibility_json": "",
		"doc": None,
	}
	if group_name and frappe.db.exists("TMS User Group", group_name):
		result["role_permissions"] = get_role_permissions(group_name)
		result["navigation_visibility_json"] = get_navigation_visibility_config(group_name)
		if frappe.utils.cint(include_doc):
			result["doc"] = frappe.get_doc("TMS User Group", group_name).as_dict()
	return result


def get_effective_field_states(group_name, doctype):
	"""{fieldname: "Hidden"|"Read Only"} for this group's generic (permlevel-based)
	field permissions on `doctype`. Shared by the field-permission popup endpoint below
	and by doctype controllers (e.g. Trip.onload/validate) that need to enforce
	Hidden/Read Only server-side.
	"""
	if not group_name or not frappe.db.exists("TMS User Group", group_name):
		return {}
	group = frappe.get_doc("TMS User Group", group_name)
	return {
		row.fieldname: row.field_state
		for row in (group.field_permissions or [])
		if row.document_type == doctype
	}


# Fields trip.js forces read_only=1 on client-side (SYSTEM_READONLY_FIELDS in
# trip.js) that do NOT already carry read_only=1 in the doctype's own JSON --
# "company" is auto-filled from the user's default Company and locked from
# there, by design, for every user, regardless of TMS User Group. This is
# BADGE-ONLY info (so an admin isn't misled into thinking it's freely editable
# by default) -- unlike a true structural read_only=1 field, it is NOT a Frappe
# permission fact, so it must NOT lock the Read Only toggle or block Default:
# the group's own Hidden/Read Only/Default choice for "company" still needs to
# be fully independent and save-able, same as any other normal field.
TRIP_JS_FORCED_READONLY_FIELDS = {"company"}


@frappe.whitelist()
def get_doctype_field_permission_config(doctype, group_name=None):
	"""Field list (currently visible, non-layout fields) for the field-permission popup,
	plus this group's already-saved Hidden/Read Only state per field.
	"""
	if doctype not in set(_get_managed_doctypes()):
		frappe.throw(_("{0} is not a TMS-managed doctype").format(doctype), frappe.PermissionError)

	meta = frappe.get_meta(doctype)
	forced_readonly = TRIP_JS_FORCED_READONLY_FIELDS if doctype == "Trip" else set()
	fields = []
	for df in meta.fields:
		if df.fieldtype in LAYOUT_FIELDTYPES or df.fieldname in EXCLUDED_SYSTEM_FIELDNAMES or df.hidden:
			continue
		fields.append({
			"fieldname": df.fieldname,
			"label": df.label or df.fieldname,
			"fieldtype": df.fieldtype,
			"is_read_only": bool(df.read_only),
			"is_js_forced_read_only": df.fieldname in forced_readonly,
			# reqd=1 (always mandatory) OR mandatory_depends_on (conditionally mandatory,
			# e.g. Receipt/Payment/Vendor Payment's reference_no -- required only for
			# certain modes of payment, enforced in each controller's validate()) --
			# an admin hiding either kind can break saving for that group.
			"is_mandatory": bool(df.reqd) or bool(df.mandatory_depends_on),
		})

	return {"fields": fields, "saved": get_effective_field_states(group_name, doctype)}


@frappe.whitelist()
def save_field_permissions(group_name, doctype, rows):
	"""Save this group's per-field Hidden/Read Only choices for one doctype. Rows for
	OTHER doctypes on the same group are left untouched. Goes through a normal
	doc.save() (not a bypass-save) so changes land in the version/audit log, since this
	is a security-sensitive permission change.

	Each row carries BOTH raw toggle states (`hidden`, `read_only`) exactly as checked
	in the popup -- no client-side reconciliation between the two. Hidden always wins
	over Read Only when both are checked; this resolution happens here, server-side,
	not in the UI.
	"""
	if not frappe.has_permission("TMS User Group", "write", doc=group_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if doctype not in set(_get_managed_doctypes()):
		frappe.throw(_("{0} is not a TMS-managed doctype").format(doctype), frappe.PermissionError)

	rows = frappe.parse_json(rows) or []
	meta = frappe.get_meta(doctype)
	group = frappe.get_doc("TMS User Group", group_name)
	forced_readonly = TRIP_JS_FORCED_READONLY_FIELDS if doctype == "Trip" else set()

	group.set("field_permissions", [r for r in (group.field_permissions or []) if r.document_type != doctype])

	for row in rows:
		fieldname = (row.get("fieldname") or "").strip()
		if not fieldname:
			continue
		# Hidden always wins over Read Only when both were checked in the popup.
		state = "Hidden" if row.get("hidden") else ("Read Only" if row.get("read_only") else "")
		if state not in ("Hidden", "Read Only"):
			continue

		df = meta.get_field(fieldname)
		if not df or df.fieldtype in LAYOUT_FIELDTYPES or fieldname in EXCLUDED_SYSTEM_FIELDNAMES:
			continue
		if is_permlevel_protected_field(doctype, fieldname):
			# Gating the sort_field breaks the whole list view, not just this column.
			continue
		if state == "Read Only" and (df.read_only or fieldname in forced_readonly):
			# Already read-only for everyone — structurally (df.read_only) or via
			# trip.js's client-side force (forced_readonly) — nothing to customize,
			# and no permlevel assignment either (only assigned when actually restricted).
			continue

		permlevel = _assign_permlevel_for_field(doctype, fieldname)
		group.append("field_permissions", {
			"document_type": doctype,
			"fieldname": fieldname,
			"label": df.label or fieldname,
			"fieldtype": df.fieldtype,
			"permlevel": permlevel,
			"field_state": state,
		})

	group.flags.ignore_permissions = True
	group.save(ignore_permissions=True)
	return {"modified": str(group.modified)}


@frappe.whitelist()
def import_existing_roles():
	frappe.throw(_("Import from Roles is no longer supported. Create TMS User Group records manually."))


# ── Hook functions (called from hooks.py) ──────────────────────────────────


def sync_custom_docperm_to_user_group(doc, method=None):
	"""Hook: Custom DocPerm saved/deleted → mirror into TMS User Group permissions table."""
	if doc.permlevel:
		# Field-level (permlevel > 0) rows are managed exclusively by the field-permission
		# sync (_sync_field_permlevel_custom_docperms) — mirroring them here would corrupt
		# the doctype-level `permissions` table, which only ever tracks permlevel-0 rows.
		return

	role = doc.role
	doctype = doc.parent

	if role in FRAPPE_SYSTEM_ROLES:
		return

	group_name = frappe.db.get_value("TMS User Group", {"group_name": role}, "name")
	if not group_name:
		return

	if doctype not in set(_get_managed_doctypes()):
		return

	group = frappe.get_doc("TMS User Group", group_name)

	existing_row = next((r for r in group.permissions if r.document_type == doctype), None)

	if method == "on_trash":
		if existing_row:
			group.permissions.remove(existing_row)
			group.flags.ignore_permissions = True
			group.flags.skip_custom_docperm_sync = True
			group.save(ignore_permissions=True)
	else:
		perm_vals = {
			child_field: int(bool(doc.get(frappe_field)))
			for frappe_field, child_field in PERM_MAP.items()
		}
		module = frappe.db.get_value("DocType", doctype, "module") or ""

		if existing_row:
			if not existing_row.get("module") and module:
				existing_row.set("module", module)
			for child_field, val in perm_vals.items():
				existing_row.set(child_field, val)
		else:
			if not module:
				return
			group.append("permissions", {"document_type": doctype, "module": module, **perm_vals})

		group.flags.ignore_permissions = True
		group.flags.skip_custom_docperm_sync = True
		group.save(ignore_permissions=True)

	_ensure_protected_role_permissions([doctype])


def sync_role_disabled_to_user_group(doc, method=None):
	"""Hook: Role disabled/enabled → mirror to TMS User Group is_active."""
	if doc.name in FRAPPE_SYSTEM_ROLES:
		return
	group_name = frappe.db.get_value("TMS User Group", {"group_name": doc.name}, "name")
	if not group_name:
		return
	is_active = 0 if doc.disabled else 1
	current = frappe.db.get_value("TMS User Group", group_name, "is_active")
	if current != is_active:
		# db.set_value skips before_validate, so master_status.sync_disabled_mirror
		# never runs on this path — write the mirror here or `disabled` drifts from
		# is_active and the group keeps showing in Employee.custom_role_profile.
		frappe.db.set_value(
			"TMS User Group",
			group_name,
			{"is_active": is_active, "disabled": 0 if is_active else 1},
			update_modified=False,
		)
		from logicore.tms_list_settings import invalidate_group_bootinfo

		invalidate_group_bootinfo(group_name)


# ── Constants ───────────────────────────────────────────────────────────────


APP_MODULE = "LogiCore"

_PERM_FIELDS = [
	"parent", "select", "read", "write", "create", "delete",
	"submit", "cancel", "amend", "print", "email", "report",
	"import", "export",
]

# Maps Frappe Custom DocPerm column → TMS User Group Permission child fieldname
PERM_MAP = {
	"select": "perm_select",
	"read":   "perm_read",
	"write":  "perm_write",
	"create": "perm_create",
	"delete": "perm_delete",
	"submit": "perm_submit",
	"cancel": "perm_cancel",
	"amend":  "perm_amend",
	"print":  "perm_print",
	"email":  "perm_email",
	"report": "perm_report",
	"import": "perm_import",
	"export": "perm_export",
}

# Doctypes that should never receive an explicit-deny Custom DocPerm row.
# If ANY Custom DocPerm exists for a doctype, Frappe ignores ALL file-based DocPerms
# for that doctype across ALL roles — not just the one with the CDP row.
_NO_EXPLICIT_DENY: set = set()

# Doctypes every TMS User Group role gets full access to, always, regardless of
# is_admin and regardless of what the group's own permissions matrix says. Not
# exposed in the permissions matrix UI (these are outside _get_managed_doctypes()) —
# there is nothing for an admin to toggle off.
BASELINE_ALWAYS_GRANTED_DOCTYPES = [
	"TMS User Group",
	"User",
	"File",
	"Salary Structure Assignment",
	"Department",
	"Designation",
	"Leave Type",
	"HR Settings",
	"Page",
	"Data Import",
	"Data Import Log",
	"Error Log",
	"Attendance",
	"Salary Structure",
	"Salary Component",
	"Account",
	"Email Account",
	"Buying Settings",
	"Stock Settings",
	"Contact",
	"Purchase Taxes and Charges Template",
	"Tax Category",
	"GL Entry",
	"Stock Ledger Entry",
	"Bin",
	"Account Ledger",
]

# Custom DocPerm columns granted in full on BASELINE_ALWAYS_GRANTED_DOCTYPES.
# Distinct from PERM_MAP: adds share/mask (not used elsewhere in this file) and
# drops submit/cancel/amend (none of these doctypes are submittable).
BASELINE_PERM_COLUMNS = [
	"select", "read", "write", "create", "delete",
	"print", "email", "report", "import", "export", "share", "mask",
]

# Doctypes in BASELINE_ALWAYS_GRANTED_DOCTYPES that get a REDUCED column set instead
# of full access for non-admin (is_admin=0) groups — is_admin=1 groups still get full
# access as normal. Currently just "User": a normal user can view/edit their own
# profile (change their own password etc.) but not see or touch anyone else's User
# record. The row-level "own record only" restriction is enforced separately by
# get_permission_query_conditions_user/has_permission_user (tms_navigation_visibility.py,
# wired in hooks.py) — this dict only controls which ACTIONS are allowed at all.
BASELINE_RESTRICTED_FOR_NON_ADMIN = {
	"User": {"select", "read", "write"},
	# Non-admin groups get READ only (never write/create/delete) at the role level --
	# and even that read is further narrowed to their OWN group's record only, by
	# get_permission_query_conditions_tms_user_group / has_permission_tms_user_group
	# (tms_navigation_visibility.py, wired in hooks.py). Only TMS Admins (is_admin=1
	# groups) may write, update, or create a TMS User Group.
	"TMS User Group": {"select", "read"},
	# System-written audit trail: rows are created by a document's on_submit and
	# removed by its on_cancel, never by hand — so ordinary groups can look at it
	# and report on it, but not edit it out from under the balances it proves.
	# TMS Admins (is_admin=1) keep full access, same as Administrator would.
	"Account Ledger": {"select", "read", "report", "export", "print", "email", "share"},
}


def _row_to_perm_dict(r):
	return {child: r.get(frappe_f) or 0 for frappe_f, child in PERM_MAP.items()}


# ── Managed DocType resolution ──────────────────────────────────────────────


def _get_managed_doctypes():
	"""Return all DocTypes managed by TMS permissions.

	Result is cached on frappe.local for the lifetime of the current request to avoid
	redundant workspace + DB queries when called multiple times in one save cycle.
	"""
	_cache_attr = "_tms_managed_doctypes_cache"
	cached = getattr(frappe.local, _cache_attr, None)
	if cached is not None:
		return cached

	managed = []
	# "TMS User Group" manages its OWN access via BASELINE_ALWAYS_GRANTED_DOCTYPES +
	# BASELINE_RESTRICTED_FOR_NON_ADMIN (own-record-only read for non-admin groups,
	# full access for is_admin groups) -- see hooks.py's permission_query_conditions/
	# has_permission for "TMS User Group". It must never be matrix-configurable (that
	# would let a normal group grant itself write access to every other group's config).
	seen = {"TMS User Group"}

	for doctype in _get_sidebar_doctypes(APP_MODULE):
		if doctype not in seen:
			managed.append(doctype)
			seen.add(doctype)

	for doctype in frappe.get_all(
		"DocType",
		filters={"module": APP_MODULE, "istable": 0, "issingle": 0},
		pluck="name",
		order_by="name asc",
	):
		if doctype not in seen:
			managed.append(doctype)
			seen.add(doctype)

	setattr(frappe.local, _cache_attr, managed)
	return managed


def _get_sidebar_doctypes(module_name):
	# Collect candidate doctype names first, then resolve existence + istable in ONE
	# batched query instead of two DB round-trips per item (frappe.db.exists +
	# frappe.get_cached_value) -- with ~50+ sidebar doctypes, the old per-item pattern
	# added a full extra second to every single permission-matrix load.
	candidates = []
	seen_candidates = set()
	for item in _iter_workspace_sidebar_items(module_name):
		if item.get("type") != "Link" or item.get("link_type") != "DocType":
			continue
		doctype = item.get("link_to")
		if doctype and doctype not in seen_candidates:
			candidates.append(doctype)
			seen_candidates.add(doctype)

	if not candidates:
		return []

	istable_by_name = {
		row.name: row.istable
		for row in frappe.get_all(
			"DocType",
			filters={"name": ["in", candidates]},
			fields=["name", "istable"],
		)
	}

	doctypes = []
	for doctype in candidates:
		if doctype not in istable_by_name or istable_by_name[doctype]:
			continue
		doctypes.append(doctype)

	return doctypes


def _iter_workspace_sidebar_items(module_name):
	for sidebar_name in _get_sidebar_candidate_names(module_name):
		if frappe.db.exists("Workspace Sidebar", sidebar_name):
			try:
				sidebar = frappe.get_doc("Workspace Sidebar", sidebar_name)
				return [row.as_dict() for row in (sidebar.items or [])]
			except Exception:
				pass

		items = _load_workspace_sidebar_items_from_file(sidebar_name)
		if items:
			return items

	return []


def _get_sidebar_candidate_names(module_name):
	candidates = []

	for ws in frappe.get_all(
		"Workspace",
		filters={"module": module_name},
		fields=["name", "label"],
		order_by="label asc",
	):
		for value in (ws.get("name"), ws.get("label")):
			value = (value or "").strip()
			if value and value not in candidates:
				candidates.append(value)

	module_name = (module_name or "").strip()
	if module_name and module_name not in candidates:
		candidates.append(module_name)

	return candidates


def _load_workspace_sidebar_items_from_file(sidebar_name):
	if not sidebar_name:
		return []

	file_path = (
		Path(frappe.get_app_path("logicore"))
		/ "workspace_sidebar"
		/ f"{frappe.scrub(sidebar_name)}.json"
	)
	if not file_path.is_file():
		return []

	try:
		with file_path.open() as f:
			return json.load(f).get("items") or []
	except Exception:
		return []


# ── Workspace grouping helpers (permission matrix display) ──────────────────


def _group_doctypes_by_workspace_hierarchy(doctype_names, module_name):
	sidebar_groups = _group_doctypes_by_workspace_sidebar(doctype_names, module_name)
	if sidebar_groups:
		return sidebar_groups

	groups = {}
	ordered_sections = []
	ungrouped = set(doctype_names)

	try:
		workspace_names = frappe.get_all(
			"Workspace",
			filters={"module": module_name},
			fields=["name", "label"],
			order_by="label asc",
		)

		for ws_row in workspace_names:
			ws_name = ws_row["name"]
			ws_label = ws_row.get("label") or ws_name
			ws = frappe.get_doc("Workspace", ws_name)

			workspace_doctypes = []
			for link in (ws.links or []):
				if link.type == "DocType" and link.link_to in doctype_names:
					workspace_doctypes.append({
						"doctype": link.link_to,
						"display": link.label or link.link_to,
					})
					ungrouped.discard(link.link_to)

			if workspace_doctypes:
				groups[ws_label] = workspace_doctypes
				ordered_sections.append(ws_label)

	except Exception:
		pass

	if ungrouped:
		catch_all = "Other"
		groups[catch_all] = [{"doctype": dt, "display": dt} for dt in sorted(ungrouped)]
		ordered_sections.append(catch_all)

	return [{"module": s, "items": groups[s]} for s in ordered_sections if groups.get(s)]


def _group_doctypes_by_workspace_sidebar(doctype_names, module_name):
	groups = {}
	ordered_sections = []
	assigned_doctypes = set()
	current_section = None

	for item in _iter_workspace_sidebar_items(module_name):
		item_type = (item.get("type") or "").strip()

		if item_type == "Section Break":
			current_section = (item.get("label") or "").strip() or None
			continue

		if item_type != "Link" or item.get("link_type") != "DocType":
			continue

		doctype = item.get("link_to")
		if not doctype or doctype not in doctype_names or doctype in assigned_doctypes:
			continue

		section = current_section or "Other"
		if section not in groups:
			groups[section] = []
			ordered_sections.append(section)

		groups[section].append({
			"doctype": doctype,
			"display": (item.get("label") or doctype).strip(),
		})
		assigned_doctypes.add(doctype)

	ungrouped = sorted(set(doctype_names) - assigned_doctypes)
	if ungrouped:
		if "Other" not in groups:
			groups["Other"] = []
			ordered_sections.append("Other")
		for dt in ungrouped:
			groups["Other"].append({"doctype": dt, "display": dt})

	return [{"module": s, "items": groups[s]} for s in ordered_sections if groups.get(s)]


def _group_navigation_items_by_workspace_hierarchy(module_name):
	sidebar_groups = _group_navigation_items_by_workspace_sidebar(module_name)
	if sidebar_groups:
		return sidebar_groups
	return []


def _group_navigation_items_by_workspace_sidebar(module_name):
	groups = {}
	ordered_sections = []
	current_section = None

	for item in _iter_workspace_sidebar_items(module_name):
		item_type = (item.get("type") or "").strip()

		if item_type == "Section Break":
			current_section = (item.get("label") or "").strip() or None
			continue

		if item_type != "Link" or item.get("link_type") == "DocType":
			continue

		# CAPA FIX: Home (the root Workspace link) is never manageable per-group -- it is
		# always accessible regardless of any group's toggle, since the workspace itself is
		# the base navigation entry point. Excluding it here removes it from the toggle
		# matrix entirely so admins can't be misled into thinking they can hide it.
		if item.get("link_type") == "Workspace":
			continue

		label = (item.get("label") or item.get("link_to") or item.get("url") or "").strip()
		if not label:
			continue

		section = current_section or "Other"
		if section not in groups:
			groups[section] = []
			ordered_sections.append(section)

		groups[section].append({
			"label": label,
			"display": label,
			"link_type": (item.get("link_type") or "").strip(),
			"link_to": (item.get("link_to") or "").strip(),
			"url": (item.get("url") or "").strip(),
		})

	if not groups:
		return []

	return [{"module": s, "items": groups[s]} for s in ordered_sections if groups.get(s)]
