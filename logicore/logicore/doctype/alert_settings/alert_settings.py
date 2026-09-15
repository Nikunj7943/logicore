# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

from dataclasses import dataclass

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification
from frappe.model import no_value_fields
from frappe.model.document import Document
from frappe.utils import add_days, cint, cstr, fmt_money, get_url_to_form, getdate, nowdate, formatdate, now_datetime

from logicore.utils.email_settings import get_sender_for_doctype


# Rules below read their date/detail data from a child table row, not the parent doctype
# (see _get_service_log_rows / _get_tyre_expense_rows).
CHILD_DETAIL_DOCTYPES = {
	"Service Logs": "Service  Replacement Item",
	"Tyre Expenses": "Tyre Expense Detail",
}

# When a vehicle's document/part is renewed, users create a NEW record rather than
# editing the old one (keeps renewal history intact). These fields identify "same slot"
# records so the alert engine can treat only the one with the latest business date
# (order_field, e.g. issue/installation/purchase date — NOT creation timestamp, since
# entries can be made after the fact) as active, and stop alerting on the superseded
# record — without deleting or flagging it.
GROUP_KEY_FIELDS_CONFIG = {
	"Compliances": {"keys": ("vehicle", "document_type"), "order_field": "issue_date"},
	"Battery Expenses": {"keys": ("vehicle_id", "brand", "battery_regn_no"), "order_field": "purchase_date"},
}


DEFAULT_ALERT_RULES = [
	{
		"enabled": 1,
		"rule_name": "Service Logs - Next Service Date",
		"source_doctype": "Service Logs",
		"date_field": "next_date",
		"alert_before_days": 7,
		"upcoming_repeat_frequency": "Once",
		"overdue_repeat_frequency": "Daily",
		"overdue_window_days": 30,
		"detail_fields": "voucher_no,vehicle_no,service_type,service_replacement,description,last_date,last_km,next_km",
		"show_in_list": 1,
	},
	{
		"enabled": 1,
		"rule_name": "Compliances - Expiry Date",
		"source_doctype": "Compliances",
		"date_field": "expiry_date",
		"alert_before_days": 30,
		"upcoming_repeat_frequency": "Once",
		"overdue_repeat_frequency": "Daily",
		"overdue_window_days": 30,
		"detail_fields": "vehicle,document_type,issue_date,amount",
		"show_in_list": 1,
	},
	{
		"enabled": 1,
		"rule_name": "Battery Expenses - Warranty Expiry",
		"source_doctype": "Battery Expenses",
		"date_field": "warranty_expiry_date",
		"alert_before_days": 30,
		"upcoming_repeat_frequency": "Once",
		"overdue_repeat_frequency": "Daily",
		"overdue_window_days": 30,
		"detail_fields": "vehicle_id,brand,battery_regn_no,installation_date,warranty_status",
		"show_in_list": 1,
	},
	{
		"enabled": 1,
		"rule_name": "Tyre Expenses - Warranty Expiry",
		"source_doctype": "Tyre Expenses",
		"date_field": "warranty_expiry",
		"alert_before_days": 30,
		"upcoming_repeat_frequency": "Once",
		"overdue_repeat_frequency": "Daily",
		"overdue_window_days": 30,
		"detail_fields": "vehicle_id,brand,tyre_type,purchase_date,removal_date",
		"show_in_list": 1,
	},
]

_DEFAULT_DASHBOARD_FIELDS = {
	"Service Logs": ("vehicle_no", "service_type", "voucher_date"),
	"Compliances": ("vehicle", "document_type", "issue_date"),
	"Battery Expenses": ("vehicle_id", "brand", "purchase_date"),
	"Tyre Expenses": ("vehicle_id", "brand", "purchase_date"),
}


class AlertSettings(Document):
	def validate(self):
		seen = {}
		for i, rule in enumerate(self.alert_rules):
			if not rule.source_doctype or not rule.date_field:
				continue
			key = (cstr(rule.source_doctype).strip(), cstr(rule.date_field).strip())
			if key in seen:
				frappe.throw(
					_(
						"Row {0}: Duplicate rule — <b>{1}</b> with date field <b>{2}</b> already exists in Row {3}."
					).format(i + 1, rule.source_doctype, rule.date_field, seen[key] + 1),
					title=_("Duplicate Alert Rule"),
				)
			seen[key] = i


@dataclass(frozen=True)
class _RecipientSplit:
	desk_emails: list[str]
	external_emails: list[str]


def ensure_default_alert_settings():
	"""Create a sensible starter configuration for new or upgraded sites."""
	if not frappe.db.exists("DocType", "Alert Settings"):
		return

	doc = frappe.get_single("Alert Settings")
	changed = False

	if doc.enable_alerts in (None, "", 0):
		doc.enable_alerts = 1
		changed = True

	if doc.enable_email_alerts in (None, "", 0):
		doc.enable_email_alerts = 1
		changed = True

	if _migrate_legacy_notify_users(doc):
		changed = True

	if not _has_notify_users(doc.notify_users):
		doc.set("notify_users", [])
		doc.append("notify_users", {"user": "Administrator"})
		changed = True

	if not doc.alert_rules:
		for rule in DEFAULT_ALERT_RULES:
			doc.append("alert_rules", rule.copy())
		changed = True
	else:
		for rule in doc.alert_rules:
			if rule.source_doctype == "Service Logs":
				if rule.date_field != "next_date":
					rule.date_field = "next_date"
					changed = True
				if not cstr(rule.detail_fields or "").strip():
					rule.detail_fields = "voucher_no,vehicle_no,service_type,service_replacement,description,last_date,last_km,next_km"
					changed = True
			elif rule.source_doctype == "Compliances" and not cstr(rule.detail_fields or "").strip():
				rule.detail_fields = "vehicle,document_type,issue_date,amount"
				changed = True
			elif rule.source_doctype == "Battery Expenses" and not cstr(rule.detail_fields or "").strip():
				rule.detail_fields = "vehicle_id,brand,battery_regn_no,installation_date,warranty_status"
				changed = True
			elif rule.source_doctype == "Tyre Expenses" and not cstr(rule.detail_fields or "").strip():
				rule.detail_fields = "vehicle_id,brand,tyre_type,purchase_date,removal_date"
				changed = True

	if changed:
		doc.save(ignore_permissions=True)


def add_alert_settings_bootinfo(bootinfo):
	bootinfo.tms_alert_settings = get_alert_settings_bootinfo()


def clear_alert_settings_cache(*args, **kwargs):
	try:
		frappe.cache.delete_key("bootinfo")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Failed to clear alert settings cache")


def _parse_send_time(value):
	"""Convert Time field value (timedelta or string) to HH:MM string."""
	if not value:
		return ""
	import datetime
	if isinstance(value, datetime.timedelta):
		total_seconds = int(value.total_seconds())
		hours = total_seconds // 3600
		minutes = (total_seconds % 3600) // 60
		return f"{hours:02d}:{minutes:02d}"
	return cstr(value).strip()[:5]


def get_alert_settings_bootinfo():
	"""Return a compact JSON-safe snapshot used by global list JS."""
	if not frappe.db.exists("DocType", "Alert Settings"):
		return {"enabled": 0, "notify_users": [], "rules": []}

	doc = frappe.get_single("Alert Settings")

	return {
		"enabled": cint(doc.enable_alerts),
		"enable_email_alerts": cint(doc.enable_email_alerts),
		"send_time": _parse_send_time(doc.send_time),
		"notify_users": _serialize_notify_users(doc.notify_users),
		"rules": [
			{
				"name": rule.name,
				"enabled": cint(rule.enabled),
				"rule_name": cstr(rule.rule_name or "").strip(),
				"source_doctype": cstr(rule.source_doctype or "").strip(),
				"date_field": cstr(rule.date_field or "").strip(),
				"alert_before_days": cint(rule.alert_before_days or 0),
				"upcoming_repeat_frequency": cstr(rule.upcoming_repeat_frequency or "Once"),
				"upcoming_repeat_every_days": cint(rule.upcoming_repeat_every_days or 0),
				"overdue_repeat_frequency": cstr(rule.overdue_repeat_frequency or "Daily"),
				"overdue_repeat_every_days": cint(rule.overdue_repeat_every_days or 0),
				"overdue_window_days": cint(rule.overdue_window_days or 30),
				"email_enabled": cint(rule.email_enabled if rule.email_enabled is not None else 1),
				"desk_enabled": cint(rule.desk_enabled if rule.desk_enabled is not None else 1),
				"email_recipients": cstr(rule.email_recipients or "").strip(),
				"detail_fields": cstr(rule.detail_fields or "").strip(),
				"show_in_list": cint(rule.show_in_list if rule.show_in_list is not None else 1),
				"max_rows": cint(rule.max_rows or 50),
				"send_time": _parse_send_time(rule.send_time),
			}
			for rule in doc.alert_rules
			if rule.enabled and rule.source_doctype and rule.date_field
		],
	}


def get_alert_rows(limit=50):
	"""Return alert cards for the dashboard and the scheduler preview."""
	limit = max(1, min(cint(limit or 50), 200))
	settings = get_alert_settings_bootinfo()
	rows = []
	today = getdate(nowdate())

	for rule in settings["rules"]:
		if not rule["enabled"] or not rule["source_doctype"] or not rule["date_field"]:
			continue

		rows.extend(_get_rows_for_rule(rule, today=today, max_rows=limit))
		if len(rows) >= limit:
			break

	return rows[:limit]


def run_alert_scheduler():
	"""Runs via 'all' scheduler (tick is ~4 min). Fires alert email within ±4 min of configured
	send_time. An atomic DB claim (see below) ensures only one email per rule per day even
	when more than one scheduler tick lands inside that window."""
	settings = get_alert_settings_bootinfo()
	if not settings["enabled"]:
		return {"sent": 0, "skipped": 0}

	global_send_time = cstr(settings.get("send_time") or "").strip()
	now = now_datetime()

	global_recipients = _split_recipients(settings.get("notify_users"))
	sent = 0
	skipped = 0
	today = getdate(nowdate())

	for rule in settings["rules"]:
		if not rule["enabled"]:
			continue

		# per-rule send_time overrides global; if neither set, skip
		effective_time = cstr(rule.get("send_time") or "").strip() or global_send_time
		if not effective_time:
			skipped += 1
			continue

		# Parse configured HH:MM
		try:
			th, tm = int(effective_time[:2]), int(effective_time[3:5])
		except Exception:
			skipped += 1
			continue

		# Current time in total minutes since midnight
		now_minutes = now.hour * 60 + now.minute
		target_minutes = th * 60 + tm

		# Fire only within ±4 minutes of configured send_time
		if abs(now_minutes - target_minutes) > 4:
			skipped += 1
			continue

		# Dedup: atomically claim "sent today" for this rule row before doing any work.
		# A plain read-then-write (e.g. via cache) can't guarantee exactly-once when
		# the ±4 min send window spans more than one scheduler tick (tick is ~4 min,
		# so two ticks commonly land inside the window) — both ticks would read
		# "not sent yet" and both would send. A conditional UPDATE is a single atomic
		# statement: only the tick whose UPDATE actually matches a row (rowcount == 1)
		# wins the claim; every other tick's UPDATE matches zero rows and is skipped.
		frappe.db.sql(
			"""
			UPDATE `tabAlert Rule`
			SET last_alert_sent_on = %(today)s
			WHERE name = %(name)s
			  AND (last_alert_sent_on IS NULL OR last_alert_sent_on != %(today)s)
			""",
			{"today": today, "name": rule["name"]},
		)
		claimed = frappe.db._cursor.rowcount == 1
		frappe.db.commit()
		if not claimed:
			skipped += 1
			continue

		rows = _get_rows_for_rule(rule, today=today, max_rows=rule["max_rows"] or 50, fetch_for_delivery=True)

		# Collect all rows that should trigger
		triggered = []
		for row in rows:
			should_send, urgency, days_delta = _should_trigger_alert(rule, row["date_value"], today)
			if not should_send:
				skipped += 1
				continue
			triggered.append((row, urgency, days_delta))

		if not triggered:
			continue

		recipients = _split_recipients(rule.get("email_recipients") or "")
		if not recipients.desk_emails and not recipients.external_emails:
			recipients = global_recipients

		# Desk notifications — one per row (Frappe requirement)
		if recipients.desk_emails and rule.get("desk_enabled"):
			for row, urgency, days_delta in triggered:
				docname = row.get("name") or row.get("parent_name", "")
				subject, message = _build_message(rule, row, urgency, days_delta)
				alert_doc = {
					"type": "Alert",
					"subject": subject,
					"email_content": message,
					"document_type": rule["source_doctype"],
					"document_name": docname,
					"link": get_url_to_form(rule["source_doctype"], docname),
					"from_user": frappe.session.user if frappe.session.user != "Guest" else None,
				}
				enqueue_create_notification(recipients.desk_emails, alert_doc)

		# Email — one grouped email per rule with all rows in a table
		all_email_recipients = list(dict.fromkeys(recipients.desk_emails + recipients.external_emails))
		if all_email_recipients and rule.get("email_enabled") and cint(settings.get("enable_email_alerts")):
			subject, message = _build_grouped_message(rule, triggered)
			try:
				frappe.sendmail(
					recipients=all_email_recipients,
					subject=subject,
					message=message,
					sender=get_sender_for_doctype("Alert Settings"),
					now=frappe.in_test,
				)
				sent += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Alert email failed: {rule['rule_name']}")

	return {"sent": sent, "skipped": skipped}


@frappe.whitelist()
def get_alert_email_history(limit=50):
	"""Fetch Email Queue entries sent by alert scheduler — filtered by alert rule subject patterns."""
	limit = min(cint(limit or 50), 200)
	try:
		import email.header

		def _decode_subject(raw_subject):
			try:
				decoded = email.header.decode_header(raw_subject)
				parts = []
				for part, charset in decoded:
					if isinstance(part, bytes):
						parts.append(part.decode(charset or "utf-8", errors="replace"))
					else:
						parts.append(part)
				return " ".join(parts).strip()
			except Exception:
				return cstr(raw_subject)

		def _is_alert_email(subject):
			"""Return True if subject matches grouped alert email format: 'Rule Name — N Alert(s)'."""
			s = cstr(subject or "").strip()
			# em-dash (—) may have surrounding spaces after MIME decode; normalize before check
			s_norm = s.replace("—", "—")
			has_emdash = "—" in s_norm
			has_alert = "Alert" in s_norm
			return has_emdash and has_alert

		# Fetch more rows than needed so we can filter client-side after subject extraction
		fetch_limit = min(limit * 6, 500)

		rows = frappe.db.sql(
			"""
			SELECT
				eq.name,
				eq.creation,
				eq.status,
				GROUP_CONCAT(eqr.recipient ORDER BY eqr.idx SEPARATOR ', ') AS recipients
			FROM `tabEmail Queue` eq
			LEFT JOIN `tabEmail Queue Recipient` eqr ON eqr.parent = eq.name
			WHERE eq.name IN (
				SELECT parent FROM `tabEmail Queue Recipient`
			)
			GROUP BY eq.name
			ORDER BY eq.creation DESC
			LIMIT %(limit)s
			""",
			{"limit": fetch_limit},
			as_dict=True,
		)

		result = []
		for row in rows:
			raw = frappe.db.get_value("Email Queue", row["name"], "message") or ""
			subject = ""
			for line in raw.split("\n")[:40]:
				if line.lower().startswith("subject:"):
					subject = _decode_subject(line[8:].strip())
					break

			if not _is_alert_email(subject):
				continue

			result.append({
				"name": row["name"],
				"creation": str(row["creation"]),
				"status": row["status"],
				"recipients": row["recipients"] or "",
				"subject": subject,
			})

			if len(result) >= limit:
				break

		return result
	except Exception:
		frappe.log_error(frappe.get_traceback(), "get_alert_email_history error")
		return []


@frappe.whitelist()
def get_alert_dashboard_rows(limit=50):
	return get_alert_rows(limit=limit)


@frappe.whitelist()
def get_list_alert_status(doctype, names):
	"""Return {name: urgency} map for given docnames — used by list view highlight."""
	import json
	if isinstance(names, str):
		names = json.loads(names)

	settings = get_alert_settings_bootinfo()
	if not settings["enabled"]:
		return {}

	today = getdate(nowdate())
	result = {}

	for rule in settings["rules"]:
		if not rule["enabled"] or rule["source_doctype"] != doctype or not rule["show_in_list"]:
			continue

		rows = _get_rows_for_rule(rule, today=today, max_rows=500)
		for row in rows:
			doc_name = row.get("name") or row.get("parent_name", "")
			if doc_name not in names:
				continue
			_, urgency, _ = _should_include_in_dashboard(rule, row["date_value"], today)
			result[doc_name] = urgency

	return result


def _get_rows_for_rule(rule, today, max_rows=50, fetch_for_delivery=False):
	doctype = rule["source_doctype"]
	date_field = rule["date_field"]
	window_days = max(cint(rule.get("alert_before_days") or 0), cint(rule.get("overdue_window_days") or 0), 1)
	upper_date = add_days(today, window_days)
	lower_date = add_days(today, -cint(rule.get("overdue_window_days") or 30))

	if doctype == "Service Logs":
		return _get_service_log_rows(rule, today=today, max_rows=max_rows, fetch_for_delivery=fetch_for_delivery)
	if doctype == "Tyre Expenses":
		return _get_tyre_expense_rows(rule, today=today, max_rows=max_rows, fetch_for_delivery=fetch_for_delivery)

	group_config = GROUP_KEY_FIELDS_CONFIG.get(doctype)

	fields = ["name", date_field]
	for fieldname in _get_detail_fields(rule):
		if fieldname not in fields:
			fields.append(fieldname)
	if group_config:
		for fieldname in (*group_config["keys"], group_config["order_field"]):
			if fieldname not in fields:
				fields.append(fieldname)

	query_filters = [
		[date_field, ">=", lower_date],
		[date_field, "<=", upper_date],
	]

	try:
		rows = frappe.db.get_all(
			doctype,
			fields=fields,
			filters=query_filters,
			order_by=f"{date_field} asc, creation asc",
			limit=max_rows,
		)
	except Exception:
		return []

	if group_config:
		rows = _filter_superseded_rows(doctype, rows, group_config["keys"], group_config["order_field"])

	records = []
	for row in rows:
		date_value = row.get(date_field)
		if not date_value:
			continue
		if fetch_for_delivery:
			should_show, urgency, days_delta = _should_trigger_alert(rule, date_value, today)
		else:
			should_show, urgency, days_delta = _should_include_in_dashboard(rule, date_value, today)

		if not should_show:
			continue

		doc = dict(row)
		doc["doctype"] = doctype
		doc["date_field"] = date_field
		doc["date_value"] = date_value
		doc["urgency"] = urgency
		doc["days_delta"] = days_delta
		doc["title"] = _get_title_for_row(doctype, doc)
		doc["details"] = _build_detail_rows(doctype, doc, rule)
		doc["route"] = f"Form/{doctype}/{row['name']}"
		records.append(doc)

	return records


# The alert engine itself needs these fields regardless of what the user configures in
# Card Fields — dedup key columns (see GROUP_KEY_FIELDS_CONFIG-style matching for child
# doctypes) and the title fallback. Every other column comes purely from the rule's
# configured detail_fields — nothing else is hardcoded, so Alert Settings stays the single
# source of truth for what gets fetched and shown.
_SERVICE_LOG_REQUIRED_FIELDS = ("service_replacement", "vehicle_no", "voucher_no")
_TYRE_EXPENSE_REQUIRED_FIELDS = ("position", "vehicle_id", "tyre_id")


def _resolve_dynamic_columns(rule, required_fields, exclude_fields, parent_doctype, parent_alias, child_doctype, child_alias):
	"""Build 'alias.field AS field' clauses for required_fields + the rule's configured
	detail_fields (Card Fields), resolving each against the child then parent doctype meta.
	exclude_fields are columns already selected under a fixed alias (e.g. name, date_field)."""
	parent_meta = frappe.get_meta(parent_doctype)
	child_meta = frappe.get_meta(child_doctype)
	fieldnames = list(required_fields) + [f for f in _get_detail_fields(rule) if f not in required_fields]
	cols = []
	seen = set(exclude_fields)
	for fieldname in fieldnames:
		if fieldname in seen:
			continue
		seen.add(fieldname)
		if child_meta.get_field(fieldname):
			cols.append(f"{child_alias}.{fieldname} AS {fieldname}")
		elif parent_meta.get_field(fieldname):
			cols.append(f"{parent_alias}.{fieldname} AS {fieldname}")
	return cols


def _get_service_log_rows(rule, today, max_rows=50, fetch_for_delivery=False):
	window_days = max(cint(rule.get("alert_before_days") or 0), cint(rule.get("overdue_window_days") or 0), 1)
	upper_date = add_days(today, window_days)
	lower_date = add_days(today, -cint(rule.get("overdue_window_days") or 30))

	dynamic_cols = _resolve_dynamic_columns(
		rule, _SERVICE_LOG_REQUIRED_FIELDS, {"name", "next_date"},
		"Service Logs", "sl", "Service  Replacement Item", "sri",
	)
	dynamic_select = ("," + ",".join(dynamic_cols)) if dynamic_cols else ""

	rows = frappe.db.sql(
		f"""
		SELECT
			sl.name AS parent_name,
			sri.name AS child_name,
			sri.next_date
			{dynamic_select}
		FROM `tabService Logs` sl
		INNER JOIN `tabService  Replacement Item` sri ON sri.parent = sl.name
		WHERE sri.next_date >= %(lower_date)s
		  AND sri.next_date <= %(upper_date)s
		ORDER BY sri.next_date ASC, sl.creation ASC, sri.idx ASC
		LIMIT %(limit)s
		""",
		{"lower_date": lower_date, "upper_date": upper_date, "limit": max_rows},
		as_dict=True,
	)

	rows = _filter_superseded_service_log_rows(rows)

	records = []
	for row in rows:
		date_value = row.get("next_date")
		if not date_value:
			continue

		if fetch_for_delivery:
			should_show, urgency, days_delta = _should_trigger_alert(rule, date_value, today)
		else:
			should_show, urgency, days_delta = _should_include_in_dashboard(rule, date_value, today)

		if not should_show:
			continue

		doc = dict(row)
		doc["doctype"] = "Service Logs"
		doc["date_field"] = "next_date"
		doc["date_value"] = date_value
		doc["urgency"] = urgency
		doc["days_delta"] = days_delta
		doc["title"] = _get_service_row_title(doc)
		doc["details"] = _build_detail_rows("Service Logs", doc, rule)
		doc["route"] = f"Form/Service Logs/{row['parent_name']}"
		records.append(doc)

	return records


def _get_tyre_expense_rows(rule, today, max_rows=50, fetch_for_delivery=False):
	window_days = max(cint(rule.get("alert_before_days") or 0), cint(rule.get("overdue_window_days") or 0), 1)
	upper_date = add_days(today, window_days)
	lower_date = add_days(today, -cint(rule.get("overdue_window_days") or 30))

	dynamic_cols = _resolve_dynamic_columns(
		rule, _TYRE_EXPENSE_REQUIRED_FIELDS, {"name", "warranty_expiry"},
		"Tyre Expenses", "te", "Tyre Expense Detail", "ted",
	)
	dynamic_select = ("," + ",".join(dynamic_cols)) if dynamic_cols else ""

	rows = frappe.db.sql(
		f"""
		SELECT
			te.name AS parent_name,
			ted.name AS child_name,
			ted.warranty_expiry
			{dynamic_select}
		FROM `tabTyre Expenses` te
		INNER JOIN `tabTyre Expense Detail` ted ON ted.parent = te.name
		WHERE ted.warranty_expiry >= %(lower_date)s
		  AND ted.warranty_expiry <= %(upper_date)s
		ORDER BY ted.warranty_expiry ASC, te.creation ASC, ted.idx ASC
		LIMIT %(limit)s
		""",
		{"lower_date": lower_date, "upper_date": upper_date, "limit": max_rows},
		as_dict=True,
	)

	rows = _filter_superseded_tyre_rows(rows)

	records = []
	for row in rows:
		date_value = row.get("warranty_expiry")
		if not date_value:
			continue

		if fetch_for_delivery:
			should_show, urgency, days_delta = _should_trigger_alert(rule, date_value, today)
		else:
			should_show, urgency, days_delta = _should_include_in_dashboard(rule, date_value, today)

		if not should_show:
			continue

		doc = dict(row)
		doc["doctype"] = "Tyre Expenses"
		doc["date_field"] = "warranty_expiry"
		doc["date_value"] = date_value
		doc["urgency"] = urgency
		doc["days_delta"] = days_delta
		doc["title"] = _get_tyre_row_title(doc)
		doc["details"] = _build_detail_rows("Tyre Expenses", doc, rule)
		doc["route"] = f"Form/Tyre Expenses/{row['parent_name']}"
		records.append(doc)

	return records


def _filter_superseded_rows(doctype, rows, key_fields, order_field):
	"""Drop rows whose (key_fields) group has a newer record (by order_field) elsewhere
	in the doctype — e.g. an old Compliance whose vehicle+document_type was renewed."""
	if not rows:
		return rows

	latest_name_cache = {}
	filtered = []
	for row in rows:
		key_filters = {f: row.get(f) for f in key_fields}
		if not all(key_filters.values()):
			filtered.append(row)
			continue

		cache_key = tuple(sorted(key_filters.items()))
		if cache_key not in latest_name_cache:
			latest_name_cache[cache_key] = frappe.db.get_value(
				doctype, key_filters, "name", order_by=f"{order_field} desc, creation desc"
			)

		latest_name = latest_name_cache[cache_key]
		if latest_name and row.get("name") and latest_name != row["name"]:
			continue  # superseded by a newer record with the same vehicle/document key

		filtered.append(row)
	return filtered


def _filter_superseded_tyre_rows(rows):
	"""Drop tyre rows whose (vehicle_id, position) slot has a newer tyre (by purchase_date)
	fitted since — e.g. an old warranty row for a tyre that has already been replaced."""
	if not rows:
		return rows

	latest_child_cache = {}
	filtered = []
	for row in rows:
		vehicle_id = row.get("vehicle_id")
		position = row.get("position")
		if not vehicle_id or not position:
			filtered.append(row)
			continue

		key = (vehicle_id, position)
		if key not in latest_child_cache:
			latest = frappe.db.sql(
				"""
				SELECT ted.name
				FROM `tabTyre Expense Detail` ted
				INNER JOIN `tabTyre Expenses` te ON te.name = ted.parent
				WHERE te.vehicle_id = %(vehicle_id)s AND ted.position = %(position)s
				ORDER BY te.purchase_date DESC, te.creation DESC, ted.idx DESC
				LIMIT 1
				""",
				{"vehicle_id": vehicle_id, "position": position},
			)
			latest_child_cache[key] = latest[0][0] if latest else None

		latest_child_name = latest_child_cache[key]
		if latest_child_name and row.get("child_name") and latest_child_name != row["child_name"]:
			continue  # superseded by a newer tyre fitted at the same position

		filtered.append(row)
	return filtered


def _filter_superseded_service_log_rows(rows):
	"""Drop service rows whose (vehicle_no, service_replacement) part has a newer service
	voucher (by voucher_date) since — e.g. an old 'next service due' row for a part that
	has already been serviced again."""
	if not rows:
		return rows

	latest_child_cache = {}
	filtered = []
	for row in rows:
		vehicle_no = row.get("vehicle_no")
		service_replacement = row.get("service_replacement")
		if not vehicle_no or not service_replacement:
			filtered.append(row)
			continue

		key = (vehicle_no, service_replacement)
		if key not in latest_child_cache:
			latest = frappe.db.sql(
				"""
				SELECT sri.name
				FROM `tabService  Replacement Item` sri
				INNER JOIN `tabService Logs` sl ON sl.name = sri.parent
				WHERE sl.vehicle_no = %(vehicle_no)s AND sri.service_replacement = %(service_replacement)s
				ORDER BY sl.voucher_date DESC, sl.creation DESC, sri.idx DESC
				LIMIT 1
				""",
				{"vehicle_no": vehicle_no, "service_replacement": service_replacement},
			)
			latest_child_cache[key] = latest[0][0] if latest else None

		latest_child_name = latest_child_cache[key]
		if latest_child_name and row.get("child_name") and latest_child_name != row["child_name"]:
			continue  # superseded by a newer service voucher for the same vehicle/part

		filtered.append(row)
	return filtered


def _should_trigger_alert(rule, date_value, today):
	alert_before_days = max(cint(rule.get("alert_before_days") or 0), 0)
	upcoming_freq = cstr(rule.get("upcoming_repeat_frequency") or "Once")
	upcoming_repeat = cint(rule.get("upcoming_repeat_every_days") or 0)
	overdue_freq = cstr(rule.get("overdue_repeat_frequency") or "Daily")
	overdue_repeat = cint(rule.get("overdue_repeat_every_days") or 0)
	overdue_window_days = max(cint(rule.get("overdue_window_days") or 30), 0)
	days_delta = (getdate(date_value) - today).days

	if days_delta > alert_before_days:
		return False, "upcoming", days_delta

	if days_delta > 0:
		step = alert_before_days - days_delta
		return _repeat_matches(upcoming_freq, step, upcoming_repeat), "upcoming", days_delta

	if days_delta == 0:
		return _repeat_matches(upcoming_freq, alert_before_days, upcoming_repeat), "urgent", days_delta

	overdue_days = abs(days_delta)
	if overdue_days > overdue_window_days:
		return False, "overdue", days_delta

	return _repeat_matches(overdue_freq, overdue_days, overdue_repeat), "overdue", days_delta


def _should_include_in_dashboard(rule, date_value, today):
	alert_before_days = max(cint(rule.get("alert_before_days") or 0), 0)
	overdue_window_days = max(cint(rule.get("overdue_window_days") or 30), 0)
	days_delta = (getdate(date_value) - today).days

	if days_delta > alert_before_days:
		return False, "upcoming", days_delta

	if days_delta >= 0:
		return True, "urgent" if days_delta == 0 else "upcoming", days_delta

	if abs(days_delta) > overdue_window_days:
		return False, "overdue", days_delta

	return True, "overdue", days_delta


def _repeat_matches(frequency, delta_days, custom_days):
	frequency = cstr(frequency or "Once")
	if frequency == "Once":
		return delta_days == 0
	if frequency == "Daily":
		return True
	if frequency == "Alternate Days":
		return delta_days % 2 == 0
	if frequency == "Weekly":
		return delta_days % 7 == 0
	if frequency == "Custom":
		return custom_days > 0 and delta_days % custom_days == 0
	return delta_days == 0


def _dispatch_alert(rule, row, subject, message, recipients, send_email_globally=1):
	sent_count = 0
	docname = row.get("name") or row.get("parent_name", "")
	doctype = rule["source_doctype"]
	link = get_url_to_form(doctype, docname)
	alert_doc = {
		"type": "Alert",
		"subject": subject,
		"email_content": message,
		"document_type": doctype,
		"document_name": docname,
		"link": link,
		"from_user": frappe.session.user if frappe.session.user != "Guest" else None,
	}

	if recipients.desk_emails and rule.get("desk_enabled"):
		enqueue_create_notification(recipients.desk_emails, alert_doc)
		sent_count += len(recipients.desk_emails)

	all_email_recipients = list(dict.fromkeys(recipients.desk_emails + recipients.external_emails))
	if all_email_recipients and rule.get("email_enabled") and send_email_globally:
		frappe.sendmail(
			recipients=all_email_recipients,
			subject=subject,
			message=message,
			now=frappe.in_test,
		)
		sent_count += len(recipients.external_emails)

	return sent_count


def _build_grouped_message(rule, triggered):
	"""Build a single tabular email for all triggered rows of one rule."""
	doctype = rule["source_doctype"]
	rule_name = rule["rule_name"]

	# Determine dominant urgency (worst-case: overdue > urgent > upcoming)
	urgency_order = {"overdue": 0, "urgent": 1, "upcoming": 2}
	dominant = min(triggered, key=lambda x: urgency_order.get(x[1], 9))[1]

	color_map = {
		"overdue": ("#fef2f2", "#fecaca", "#dc2626", "OVERDUE"),
		"urgent":  ("#fff7ed", "#fed7aa", "#ea580c", "URGENT"),
		"upcoming":("#f0fdf4", "#bbf7d0", "#15803d", "UPCOMING"),
	}
	bg_color, border_color, text_color, status_label = color_map[dominant]

	th_style = "padding:8px 10px;text-align:left;background:#f3f4f6;color:#374151;font-size:12px;font-weight:700;border-bottom:2px solid #e5e7eb;white-space:nowrap"

	# Get detail column headers from first row (no duplicates with fixed columns)
	first_row = triggered[0][0]
	detail_keys = [label for label, _ in first_row.get("details", [])]

	th_cells = (
		f"<th style='{th_style}'>#</th>"
		f"<th style='{th_style}'>Due Date</th>"
		f"<th style='{th_style}'>Status</th>"
		+ "".join(f"<th style='{th_style}'>{frappe.utils.escape_html(k)}</th>" for k in detail_keys)
		+ f"<th style='{th_style}'>Action</th>"
	)

	urg_colors = {"overdue": "#dc2626", "urgent": "#ea580c", "upcoming": "#16a34a"}
	urg_labels = {"overdue": "Overdue", "urgent": "Urgent", "upcoming": "Upcoming"}

	tbody_rows = ""
	for idx, (row, urgency, days_delta) in enumerate(triggered, 1):
		docname = row.get("name") or row.get("parent_name", "")
		link = get_url_to_form(doctype, docname)
		date_label = formatdate(row["date_value"]) if row.get("date_value") else ""
		days_text = _format_days_text(days_delta)
		urg_color = urg_colors.get(urgency, "#6b7280")
		urg_label = urg_labels.get(urgency, urgency.title())
		row_bg = "#ffffff" if idx % 2 == 0 else "#f9fafb"
		td_style = "padding:8px 10px;font-size:12px;border-bottom:1px solid #e5e7eb;vertical-align:middle"

		detail_cells = "".join(
			f"<td style='{td_style}'>{frappe.utils.escape_html(val)}</td>"
			for _, val in row.get("details", [])
		)

		tbody_rows += f"""
		<tr style='background:{row_bg}'>
			<td style='{td_style};color:#6b7280'>{idx}</td>
			<td style='{td_style}'>{frappe.utils.escape_html(date_label)}<br>
				<span style='font-size:11px;color:#6b7280'>{frappe.utils.escape_html(days_text)}</span>
			</td>
			<td style='{td_style}'>
				<span style='background:{urg_color};color:#fff;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:700'>{urg_label}</span>
			</td>
			{detail_cells}
			<td style='{td_style}'>
				<a href='{link}' style='display:inline-block;padding:4px 10px;background:#1d4ed8;color:#fff;border-radius:6px;font-size:11px;font-weight:700;text-decoration:none'>Open</a>
			</td>
		</tr>"""

	count = len(triggered)
	subject = f"{rule_name} — {count} Alert{'s' if count > 1 else ''}"

	message = f"""
	<div style="font-family:Inter,Segoe UI,sans-serif;line-height:1.5;color:#111827;max-width:900px">
		<div style="padding:12px 16px;border-radius:8px 8px 0 0;background:#f8fafc;border:1px solid #e2e8f0;border-bottom:none">
			<div style="font-size:16px;font-weight:700">{frappe.utils.escape_html(rule_name)}</div>
			<div style="font-size:12px;color:#64748b;margin-top:2px">{frappe.utils.escape_html(doctype)} &nbsp;·&nbsp; {count} record{'s' if count > 1 else ''}</div>
		</div>
		<div style="border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;overflow-x:auto">
			<table style="width:100%;border-collapse:collapse;min-width:600px">
				<thead><tr>{th_cells}</tr></thead>
				<tbody>{tbody_rows}</tbody>
			</table>
		</div>
	</div>
	"""
	return subject, message


def _build_message(rule, row, urgency, days_delta):
	doctype = rule["source_doctype"]
	title = row["title"]
	date_label = formatdate(row["date_value"]) if row.get("date_value") else ""
	link = get_url_to_form(doctype, row.get("name") or row.get("parent_name", ""))
	if urgency == "overdue":
		status = _("OVERDUE")
		bg_color = "#fef2f2"
		border_color = "#fecaca"
		text_color = "#dc2626"
	elif urgency == "urgent":
		status = _("URGENT")
		bg_color = "#fff7ed"
		border_color = "#fed7aa"
		text_color = "#ea580c"
	else:
		status = _("UPCOMING")
		bg_color = "#f0fdf4"
		border_color = "#bbf7d0"
		text_color = "#15803d"
	days_text = _format_days_text(days_delta)
	detail_html = "".join(
		f"<tr><td style='padding:4px 8px;color:#6b7280'>{frappe.utils.escape_html(label)}</td>"
		f"<td style='padding:4px 8px;font-weight:600'>{frappe.utils.escape_html(value)}</td></tr>"
		for label, value in row.get("details", [])
	)
	message = f"""
		<div style="font-family:Inter,Segoe UI,sans-serif;line-height:1.5;color:#111827">
			<div style="padding:14px 16px;border-radius:12px;background:{bg_color};border:1px solid {border_color}">
				<div style="font-size:12px;font-weight:800;letter-spacing:.4px;text-transform:uppercase;color:{text_color}">{status}</div>
				<div style="font-size:18px;font-weight:800;margin-top:4px">{frappe.utils.escape_html(title)}</div>
				<div style="font-size:13px;color:#374151;margin-top:2px">{frappe.utils.escape_html(doctype)} · {frappe.utils.escape_html(days_text)}</div>
				<div style="margin-top:8px;font-size:13px"><strong>{frappe.utils.escape_html(rule['rule_name'])}</strong></div>
				<div style="margin-top:8px;font-size:13px">Date: <strong>{frappe.utils.escape_html(date_label)}</strong></div>
				<table style="margin-top:10px;border-collapse:collapse;width:100%">
					{detail_html}
				</table>
				<div style="margin-top:12px">
					<a href="{link}" style="display:inline-block;padding:8px 12px;border-radius:8px;background:#1d4ed8;color:#fff;text-decoration:none;font-weight:700">Open Record</a>
				</div>
			</div>
		</div>
	"""
	subject = f"[{status}] {rule['rule_name']} - {title}"
	return subject, message


def _build_detail_rows(doctype, row, rule):
	details = []
	for fieldname in _get_detail_fields(rule):
		if fieldname == rule["date_field"]:
			continue
		value = row.get(fieldname)
		if value in (None, ""):
			continue
		label, formatted_value = _format_row_field_value(doctype, row, fieldname, value)
		details.append((label, formatted_value))
	return details


def _get_detail_fields(rule):
	fields = []
	raw_value = rule.get("detail_fields") or ""
	if isinstance(raw_value, list):
		for item in raw_value:
			if isinstance(item, dict):
				fieldname = cstr(item.get("fieldname") or item.get("value") or item.get("name") or "").strip()
			else:
				fieldname = cstr(item or "").strip()
			if fieldname:
				fields.append(fieldname)
	else:
		for fieldname in cstr(raw_value or "").split(","):
			fieldname = fieldname.strip()
			if fieldname:
				fields.append(fieldname)
	return fields


def _get_title_for_row(doctype, row):
	if doctype == "Service Logs":
		return _get_service_row_title(row)

	for fieldname in _DEFAULT_DASHBOARD_FIELDS.get(doctype, ()):
		value = row.get(fieldname)
		if value not in (None, ""):
			return _format_value(doctype, fieldname, value)

	if row.get("name"):
		return cstr(row["name"])

	return doctype


def _get_service_row_title(row):
	service_replacement = cstr(row.get("service_replacement") or "").strip()
	if service_replacement:
		return _resolve_link_title("Account Head", service_replacement)
	return cstr(row.get("voucher_no") or row.get("parent_name") or "Service Logs")


def _get_tyre_row_title(row):
	tyre_id = cstr(row.get("tyre_id") or "").strip()
	if tyre_id:
		return tyre_id

	position = cstr(row.get("position") or "").strip()
	if position:
		return position

	return cstr(row.get("parent_name") or "Tyre Expenses")


def _get_field_label(doctype, fieldname):
	meta = frappe.get_meta(doctype)
	field = meta.get_field(fieldname)
	return field.label if field and field.label else fieldname.replace("_", " ").title()


def _format_row_field_value(doctype, row, fieldname, value):
	if doctype == "Service Logs":
		child_doctype = "Service  Replacement Item"
		try:
			meta = frappe.get_meta(child_doctype)
			field = meta.get_field(fieldname)
			if field:
				return field.label if field.label else fieldname.replace("_", " ").title(), _format_value(child_doctype, fieldname, value)
		except Exception:
			pass
	elif doctype == "Tyre Expenses":
		child_doctype = "Tyre Expense Detail"
		try:
			meta = frappe.get_meta(child_doctype)
			field = meta.get_field(fieldname)
			if field:
				return field.label if field.label else fieldname.replace("_", " ").title(), _format_value(child_doctype, fieldname, value)
		except Exception:
			pass

	return _get_field_label(doctype, fieldname), _format_value(doctype, fieldname, value)


def _format_value(doctype, fieldname, value):
	meta = frappe.get_meta(doctype)
	field = meta.get_field(fieldname)
	if not field:
		return cstr(value)

	if field.fieldtype == "Link" and value and field.options:
		return _resolve_link_title(field.options, value)
	if field.fieldtype == "Date" and value:
		return formatdate(value)
	if field.fieldtype == "Currency":
		return fmt_money(value)
	if field.fieldtype in {"Float", "Int"}:
		return cstr(value)
	return cstr(value)


def _resolve_link_title(link_doctype, value):
	value = cstr(value or "").strip()
	if not value:
		return ""

	try:
		meta = frappe.get_meta(link_doctype)
	except Exception:
		return value

	title_field = cstr(meta.title_field or "").strip()
	if title_field and title_field != "name":
		title_value = frappe.db.get_value(link_doctype, value, title_field)
		if title_value not in (None, ""):
			return cstr(title_value)

	return value


def _split_recipients(raw_value):
	items = []
	if isinstance(raw_value, list):
		for item in raw_value:
			if isinstance(item, dict):
				value = cstr(item.get("user") or item.get("email") or item.get("name") or "").strip()
			else:
				value = cstr(item or "").strip()
			if value:
				items.append(value)
	else:
		items = [item.strip() for item in cstr(raw_value or "").split(",") if item.strip()]
	desk_emails = []
	external_emails = []

	for item in items:
		if "@" in item:
			if frappe.db.exists("User", {"email": item, "enabled": 1}):
				desk_emails.append(item)
			else:
				external_emails.append(item)
			continue

		email = frappe.db.get_value("User", item, "email")
		if email:
			desk_emails.append(email)
		else:
			external_emails.append(item)

	return _RecipientSplit(
		desk_emails=list(dict.fromkeys(desk_emails)),
		external_emails=list(dict.fromkeys(external_emails)),
	)


def _has_notify_users(notify_users):
	if isinstance(notify_users, list):
		for item in notify_users:
			if isinstance(item, dict):
				value = cstr(item.get("user") or item.get("email") or "").strip()
			else:
				value = cstr(getattr(item, "user", None) or getattr(item, "email", None) or "").strip()
			if value:
				return True
		return False
	return bool(cstr(notify_users or "").strip())


def _serialize_notify_users(notify_users):
	if isinstance(notify_users, list):
		result = []
		for item in notify_users:
			if isinstance(item, dict):
				value = cstr(item.get("user") or item.get("email") or item.get("name") or "").strip()
			else:
				# Frappe Document object
				value = cstr(getattr(item, "user", None) or getattr(item, "email", None) or getattr(item, "name", None) or "").strip()
			if value:
				result.append(value)
		return result
	return [item.strip() for item in cstr(notify_users or "").split(",") if item.strip()]


def _migrate_legacy_notify_users(doc):
	if isinstance(doc.notify_users, list):
		return False

	raw_value = cstr(doc.notify_users or "").strip()
	if not raw_value:
		return False

	selected_users = []
	for item in [part.strip() for part in raw_value.split(",") if part.strip()]:
		if "@" in item:
			user_name = frappe.db.get_value("User", {"email": item, "enabled": 1}, "name")
			if user_name:
				selected_users.append(user_name)
			continue

		if frappe.db.exists("User", item):
			selected_users.append(item)
			continue

		user_name = frappe.db.get_value("User", {"full_name": item, "enabled": 1}, "name")
		if user_name:
			selected_users.append(user_name)

	if not selected_users:
		return False

	doc.set("notify_users", [])
	for user_name in dict.fromkeys(selected_users):
		doc.append("notify_users", {"user": user_name})
	return True


def _format_days_text(days_delta):
	if days_delta > 0:
		return f"In {days_delta} day{'s' if days_delta != 1 else ''}"
	if days_delta == 0:
		return "Due today"
	overdue_days = abs(days_delta)
	return f"{overdue_days} day{'s' if overdue_days != 1 else ''} overdue"


@frappe.whitelist()
def get_alert_settings():
	return get_alert_settings_bootinfo()


def _doctype_field_options(doctype, only_fieldtypes=None):
	if not doctype or not frappe.db.exists("DocType", doctype):
		return []

	def _collect(meta, suffix=""):
		rows = []
		for df in meta.fields:
			if not df.fieldname:
				continue
			if only_fieldtypes:
				if df.fieldtype not in only_fieldtypes:
					continue
			elif df.fieldtype in no_value_fields:
				continue
			label = df.label or df.fieldname
			rows.append({"label": f"{label}{suffix}", "value": df.fieldname})
		return rows

	options = _collect(frappe.get_meta(doctype))

	child_doctype = CHILD_DETAIL_DOCTYPES.get(doctype)
	if child_doctype:
		options += _collect(frappe.get_meta(child_doctype), suffix=f" ({child_doctype})")

	return options


@frappe.whitelist()
def get_date_field_options(doctype=None, txt=None):
	return _doctype_field_options(doctype, only_fieldtypes={"Date", "Datetime"})


@frappe.whitelist()
def get_detail_field_options(doctype=None, txt=None):
	return _doctype_field_options(doctype)

