# Rename Trip Import Template → Import Template and Trip Import Log → Import Log
# Uses direct SQL to work on Frappe Cloud (no file system writes needed).
# Handles both scenarios:
#   A) old exists, new doesn't → simple rename
#   B) old exists, new exists empty (auto-created by model sync) → data migration + cleanup


def _table_exists(table_name):
	import frappe
	result = frappe.db.sql(
		"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = %s",
		(table_name,)
	)
	return result[0][0] > 0


def _table_row_count(table_name):
	import frappe
	try:
		result = frappe.db.sql(f"SELECT COUNT(*) FROM `{table_name}`")
		return result[0][0]
	except Exception:
		return 0


def execute():
	import frappe

	RENAMES = [
		(
			"Trip Import Template", "Import Template",
			"tabTrip Import Template", "tabImport Template",
			"Import Templates",
		),
		(
			"Trip Import Log", "Import Log",
			"tabTrip Import Log", "tabImport Log",
			"Import Logs",
		),
	]

	for old, new, old_tbl, new_tbl, sidebar_label in RENAMES:
		old_exists = frappe.db.exists("DocType", old)
		new_exists = frappe.db.exists("DocType", new)

		if not old_exists:
			# Fresh install or already done
			continue

		if new_exists:
			# Both exist — model sync auto-created new empty table
			# If new table is empty and old has data, do data migration
			old_count = _table_row_count(old_tbl) if _table_exists(old_tbl) else 0
			new_count = _table_row_count(new_tbl) if _table_exists(new_tbl) else 0

			if old_count == 0:
				# Old is also empty or doesn't matter — just clean up old
				frappe.db.sql("DELETE FROM `tabDocType` WHERE `name` = %s", (old,))
				frappe.db.commit()
				continue

			if new_count > 0:
				# Both have data — already migrated
				frappe.db.sql("DELETE FROM `tabDocType` WHERE `name` = %s", (old,))
				frappe.db.commit()
				continue

			# old_count > 0 and new_count == 0 → migrate data
			# Drop the auto-created empty new table, rename old to new
			try:
				frappe.db.sql(f"DROP TABLE IF EXISTS `{new_tbl}`")
			except Exception:
				pass
			try:
				frappe.db.sql(f"RENAME TABLE `{old_tbl}` TO `{new_tbl}`")
			except Exception:
				pass

			# Remove auto-created new DocType entry, update old to new name
			frappe.db.sql("DELETE FROM `tabDocType` WHERE `name` = %s", (new,))
			frappe.db.sql(
				"UPDATE `tabDocType` SET `name` = %s, `modified` = NOW() WHERE `name` = %s",
				(new, old)
			)
		else:
			# Simple case: only old exists — rename table and DocType
			if _table_exists(old_tbl):
				try:
					frappe.db.sql(f"RENAME TABLE `{old_tbl}` TO `{new_tbl}`")
				except Exception:
					pass
			frappe.db.sql(
				"UPDATE `tabDocType` SET `name` = %s, `modified` = NOW() WHERE `name` = %s",
				(new, old)
			)

		# Update DocField options (Link fields pointing to old name)
		frappe.db.sql(
			"UPDATE `tabDocField` SET `options` = %s WHERE `options` = %s",
			(new, old)
		)
		frappe.db.sql(
			"UPDATE `tabCustom Field` SET `options` = %s WHERE `options` = %s",
			(new, old)
		)

		# Update sidebar
		frappe.db.sql(
			"UPDATE `tabWorkspace Sidebar Item` SET `link_to` = %s, `label` = %s WHERE `link_to` = %s",
			(new, sidebar_label, old)
		)

		frappe.db.commit()
		frappe.clear_cache()
