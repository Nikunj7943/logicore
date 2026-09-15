# v2: Robust rename using direct SQL — works on Frappe Cloud (no file system writes).
# Handles both: simple rename OR data migration when model sync already created new empty table.


def _table_exists(table_name):
	import frappe
	result = frappe.db.sql(
		"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s",
		(table_name,)
	)
	return bool(result[0][0])


def _row_count(table_name):
	import frappe
	try:
		return frappe.db.sql(f"SELECT COUNT(*) FROM `{table_name}`")[0][0]
	except Exception:
		return 0


def execute():
	import frappe

	RENAMES = [
		("Trip Import Template", "Import Template",
		 "tabTrip Import Template", "tabImport Template", "Import Templates"),
		("Trip Import Log", "Import Log",
		 "tabTrip Import Log", "tabImport Log", "Import Logs"),
	]

	for old, new, old_tbl, new_tbl, sidebar_label in RENAMES:
		old_in_db = frappe.db.exists("DocType", old)
		new_in_db = frappe.db.exists("DocType", new)

		if not old_in_db and not new_in_db:
			continue  # fresh install — model sync will create correctly

		if not old_in_db and new_in_db:
			# Already renamed correctly
			_fix_sidebar(new, sidebar_label)
			frappe.db.commit()
			continue

		# old exists in DB — need to rename
		if new_in_db:
			# Both exist: model sync auto-created new (empty) table
			# Migrate: drop empty new table, rename old to new
			old_count = _row_count(old_tbl) if _table_exists(old_tbl) else 0
			new_count = _row_count(new_tbl) if _table_exists(new_tbl) else 0

			if old_count > 0 and new_count == 0:
				frappe.db.sql(f"DROP TABLE IF EXISTS `{new_tbl}`")
				if _table_exists(old_tbl):
					frappe.db.sql(f"RENAME TABLE `{old_tbl}` TO `{new_tbl}`")
				frappe.db.sql("DELETE FROM `tabDocType` WHERE `name` = %s", (new,))
				frappe.db.sql(
					"UPDATE `tabDocType` SET `name` = %s, `modified` = NOW() WHERE `name` = %s",
					(new, old)
				)
			elif new_count > 0:
				# New already has data — just clean up old DocType entry
				frappe.db.sql("DELETE FROM `tabDocType` WHERE `name` = %s", (old,))
		else:
			# Simple: only old exists
			if _table_exists(old_tbl):
				frappe.db.sql(f"RENAME TABLE `{old_tbl}` TO `{new_tbl}`")
			frappe.db.sql(
				"UPDATE `tabDocType` SET `name` = %s, `modified` = NOW() WHERE `name` = %s",
				(new, old)
			)

		# Update Link field references
		for tbl in ("tabDocField", "tabCustom Field"):
			frappe.db.sql(f"UPDATE `{tbl}` SET `options` = %s WHERE `options` = %s", (new, old))

		_fix_sidebar(new, sidebar_label)
		frappe.db.commit()
		frappe.clear_cache()


def _fix_sidebar(new, label):
	import frappe
	frappe.db.sql(
		"UPDATE `tabWorkspace Sidebar Item` SET `link_to` = %s, `label` = %s WHERE `link_to` IN (%s, %s)",
		(new, label, new, new.replace("Import", "Trip Import"))
	)
