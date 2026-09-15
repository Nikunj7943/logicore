"""
utils/whitebooks_api.py
Thin client for the Whitebooks E-Way Bill GSP API.
Credentials are read per-Company from the "Eway Bill Settings" doctype — never hardcoded.
"""

from __future__ import annotations

from datetime import datetime

import frappe
import requests

AUTHENTICATE_PATH = "/authenticate"
GET_EWAYBILL_PATH = "/ewayapi/getewaybill"

NOT_SET_UP_MESSAGE = "E-Way Bill lookup is not set up for this Company yet. Please contact your administrator."


def is_enabled(company: str) -> bool:
	"""True only when this Company has an Eway Bill Settings record with the lookup switched on."""
	if not company:
		return False
	return bool(frappe.db.get_value("Eway Bill Settings", {"company": company}, "enabled"))


def _settings(company: str):
	# Naming is "hash" (not "field:company") so the Company field stays editable after
	# the record is created — Frappe force-hides an autoname field once a doc is saved.
	# Look the record up by the company field instead of by docname.
	# if not frappe.db.exists("Eway Bill Settings", company):
	# 	frappe.throw(NOT_SET_UP_MESSAGE)
	# return frappe.get_cached_doc("Eway Bill Settings", company)
	name = frappe.db.get_value("Eway Bill Settings", {"company": company}, "name")
	if not name:
		frappe.throw(NOT_SET_UP_MESSAGE)
	return frappe.get_cached_doc("Eway Bill Settings", name)


def _base_url(settings) -> str:
	url = settings.sandbox_url if settings.use_sandbox else settings.production_url
	if not url:
		frappe.throw(NOT_SET_UP_MESSAGE)
	return url.rstrip("/")


def _headers(settings) -> dict:
	client_id = settings.get_password("client_id", raise_exception=False)
	client_secret = settings.get_password("client_secret", raise_exception=False)
	if not (client_id and client_secret and settings.gstin):
		frappe.throw(NOT_SET_UP_MESSAGE)
	return {
		"client_id": client_id,
		"client_secret": client_secret,
		"gstin": settings.gstin,
		"ip_address": settings.ip_address or "",
	}


def _parse_date(value: str | None) -> str | None:
	"""Convert Whitebooks' "DD/MM/YYYY hh:mm:ss AM/PM" strings to an ISO date."""
	if not value:
		return None
	return datetime.strptime(value, "%d/%m/%Y %I:%M:%S %p").date().isoformat()


def _authenticate(settings) -> None:
	"""Whitebooks sessions expire, so re-authenticate before every lookup."""
	password = settings.get_password("password", raise_exception=False)
	if not (settings.username and password):
		frappe.throw(NOT_SET_UP_MESSAGE)

	try:
		response = requests.get(
			_base_url(settings) + AUTHENTICATE_PATH,
			params={"email": settings.email, "password": password, "username": settings.username},
			headers=_headers(settings),
			timeout=30,
		)
		response.raise_for_status()
		payload = response.json()
	except requests.RequestException as e:
		frappe.log_error(str(e), "Whitebooks E-Way Bill Lookup")
		frappe.throw("Couldn't reach the E-Way Bill service right now. Please try again in a few minutes.")

	if payload.get("status_cd") != "1":
		frappe.log_error(payload.get("status_desc") or "no status_desc in response", "Whitebooks E-Way Bill Lookup")
		frappe.throw(NOT_SET_UP_MESSAGE)


def get_e_waybill_details(ewb_no: str, company: str) -> dict:
	"""Fetch e-way bill details from Whitebooks and return the fields Trip cares about."""
	settings = _settings(company)
	email = settings.email
	if not email:
		frappe.throw(NOT_SET_UP_MESSAGE)

	_authenticate(settings)

	try:
		response = requests.get(
			_base_url(settings) + GET_EWAYBILL_PATH,
			params={"email": email, "ewbNo": ewb_no, "irp": "NIC1"},
			headers=_headers(settings),
			timeout=30,
		)
		response.raise_for_status()
		payload = response.json()
	except requests.RequestException as e:
		frappe.log_error(str(e), "Whitebooks E-Way Bill Lookup")
		frappe.throw("Couldn't reach the E-Way Bill service right now. Please try again in a few minutes.")

	if payload.get("status_cd") != "1":
		frappe.log_error(payload.get("status_desc") or "no status_desc in response", "Whitebooks E-Way Bill Lookup")
		frappe.throw("No E-Way Bill found for this number. Please check the number and try again.")

	data = payload.get("data") or {}
	vehicle_updates = data.get("VehiclListDetails") or []
	vehicle_no_raw = vehicle_updates[0].get("vehicleNo") if vehicle_updates else None

	return {
		"vehicle_no_raw": vehicle_no_raw,
		"eway_bill_date": _parse_date(data.get("ewayBillDate")),
		"eway_bill_expiry_date": _parse_date(data.get("validUpto")),
	}
