# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import calendar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, get_first_day

from logicore.utils.email_template_utils import render_and_send_email_template
from logicore.tms_list_settings import _get_user_tms_group_candidates


def _effective_emi_day(emi_day, on_date):
	"""Clamp emi_day to the last valid day of on_date's month (handles 29/30/31 in shorter months)."""
	last_day_of_month = calendar.monthrange(on_date.year, on_date.month)[1]
	return min(emi_day, last_day_of_month)


class VehicleFinance(Document):
	def validate(self):
		self._validate_reference_no_unique()

	def after_insert(self):
		"""EMI Draft Payment creation is handled ONLY by the nightly cron
		(create_emi_payments_for_today, runs 23:00 daily) — never immediately on insert.
		This keeps manual entry and Data Import behavior identical: today's EMI (even if
		date_of_emi's day already matches) always waits for tonight's cron run.
		"""
		pass
		# --- previous instant-creation logic (disabled, kept for reference) ---
		# if frappe.flags.in_import:
		# 	return  # bulk/historical Data Import — skip auto EMI payment creation
		# if not self.date_of_emi:
		# 	return
		# today = frappe.utils.today()
		# today_date = getdate(today)
		# emi_day = getdate(self.date_of_emi).day
		# if today_date.day < _effective_emi_day(emi_day, today_date):
		# 	return
		# if getdate(self.start_date or today) > today_date:
		# 	return
		# if self.end_date and getdate(self.end_date) < today_date:
		# 	return
		# month_start = get_first_day(today)
		# existing = frappe.db.exists(
		# 	"Payment",
		# 	{
		# 		"vehicle_finance": self.name,
		# 		"type": "Vehicle Finance EMI",
		# 		"date": [">=", month_start],
		# 		"docstatus": ["!=", 2],
		# 	},
		# )
		# if existing:
		# 	return
		# payment = frappe.get_doc({
		# 	"doctype": "Payment",
		# 	"type": "Vehicle Finance EMI",
		# 	"date": today,
		# 	"vehicle_finance": self.name,
		# 	"vf_vehicle": self.vehicle,
		# 	"vf_financer": self.finance,
		# 	"vf_loan_account": self.loan_account or "",
		# 	"vendor_supplier": self.finance,
		# 	"amount": self.emi_amount,
		# 	"paid_from_account": self.bank_name,
		# 	"mode_of_payment": self.payment_mode or "Bank Transfer",
		# 	"status": "Draft",
		# })
		# payment.insert(ignore_permissions=True)
		# frappe.msgprint(
		# 	f"EMI Draft Payment created: <b>{payment.name}</b>",
		# 	indicator="green",
		# 	alert=True,
		# )

	def _validate_reference_no_unique(self):
		if not self.reference_no:
			return
		duplicate = frappe.db.get_value(
			"Vehicle Finance",
			{"reference_no": self.reference_no, "name": ("!=", self.name or "")},
			"name",
		)
		if duplicate:
			frappe.throw(_("Reference No. {0} already used in {1}.").format(self.reference_no, duplicate))

	def update_emi_summary(self):
		"""Refresh emis_paid and outstanding_loan from submitted Payment records."""
		payments = frappe.db.get_all(
			"Payment",
			filters={
				"vehicle_finance": self.name,
				"type": "Vehicle Finance EMI",
				"docstatus": 1,
			},
			fields=["amount"],
		)
		emis_paid = len(payments)
		amount_paid = sum(flt(p.amount) for p in payments)
		outstanding_loan = max(flt(self.loan_amount or 0) - amount_paid, 0)
		self.db_set("emis_paid", emis_paid)
		self.db_set("outstanding_loan", outstanding_loan)


@frappe.whitelist()
def get_emi_payment_summary(vehicle_finance):
	"""Return summary stats + payment list for Vehicle Finance EMI history."""
	vf = frappe.db.get_value(
		"Vehicle Finance", vehicle_finance,
		["total_emis", "emi_amount", "loan_amount"], as_dict=True
	)
	payments = frappe.db.get_all(
		"Payment",
		filters={"vehicle_finance": vehicle_finance, "type": "Vehicle Finance EMI"},
		fields=["name", "date", "amount", "status", "reference_no", "docstatus"],
		order_by="date asc",
	)

	total_emis = vf.total_emis or 0
	emis_paid = sum(1 for p in payments if p.docstatus == 1)
	amount_paid = sum(flt(p.amount) for p in payments if p.docstatus == 1)
	emis_balance = max(total_emis - emis_paid, 0)
	amount_pending = max(flt(vf.loan_amount or 0) - amount_paid, 0)

	return {
		"emis_paid": emis_paid,
		"emis_balance": emis_balance,
		"amount_paid": amount_paid,
		"amount_pending": amount_pending,
		"payments": payments,
	}


def create_emi_payments_for_today():
	"""Midnight cron job: create Draft Payment for each active VF whose date_of_emi day has arrived this month."""
	today = frappe.utils.today()
	today_date = getdate(today)
	today_day = today_date.day

	vf_list = frappe.db.get_all(
		"Vehicle Finance",
		filters={
			"start_date": ["<=", today],
			"end_date": [">=", today],
		},
		fields=[
			"name", "finance", "vehicle", "emi_amount", "bank_name",
			"loan_account", "date_of_emi", "payment_mode",
			"total_emis", "emis_paid",
		],
	)

	created = []
	for vf in vf_list:
		if not vf.date_of_emi:
			continue
		if vf.total_emis and vf.emis_paid and vf.emis_paid >= vf.total_emis:
			continue
		emi_day = getdate(vf.date_of_emi).day
		if today_day != _effective_emi_day(emi_day, today_date):
			continue

		# Duplicate check: already a non-cancelled entry this month?
		month_start = get_first_day(today)
		existing = frappe.db.exists(
			"Payment",
			{
				"vehicle_finance": vf.name,
				"type": "Vehicle Finance EMI",
				"date": [">=", month_start],
				"docstatus": ["!=", 2],
			},
		)
		if existing:
			continue

		payment = frappe.get_doc({
			"doctype": "Payment",
			"type": "Vehicle Finance EMI",
			"date": today,
			"vehicle_finance": vf.name,
			"vf_vehicle": vf.vehicle,
			"vf_financer": vf.finance,
			"vf_loan_account": vf.loan_account or "",
			"vendor_supplier": vf.finance,
			"amount": vf.emi_amount,
			"paid_from_account": vf.bank_name,
			"mode_of_payment": vf.payment_mode or "Bank Transfer",
			"status": "Draft",
		})
		payment.insert(ignore_permissions=True)

		created.append({
			"payment": payment.name,
			"vehicle_finance": vf.name,
			"vehicle": vf.vehicle or "—",
			"financer": vf.finance or "—",
			"emi_amount": flt(vf.emi_amount or 0),
		})

	if created:
		_send_emi_creation_email(created, today)


def _send_emi_creation_email(created_list, today):
	"""Send a grouped summary email to users in active admin TMS User Groups."""
	admin_groups = set(
		frappe.db.get_all(
			"TMS User Group",
			filters={"is_admin": 1, "is_active": 1},
			pluck="name",
		)
	)
	recipients = []
	for user in frappe.db.get_all("User", filters={"enabled": 1}, pluck="name"):
		if admin_groups.intersection(_get_user_tms_group_candidates(user)):
			recipients.append(user)
	if not recipients:
		return

	total_amount = sum(r["emi_amount"] for r in created_list)
	render_and_send_email_template(
		template_doctype="Vehicle Finance",
		context={
			"today": today,
			"created_list": created_list,
			"total_amount": total_amount,
			"site_url": frappe.utils.get_url(),
		},
		recipients=recipients,
		sender_doctype="Vehicle Finance",
		reference_doctype="Vehicle Finance",
	)
