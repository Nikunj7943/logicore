"""
utils/telegram_tasks.py
Background tasks for the Telegram bot — run via frappe.enqueue().
"""

import json
import frappe

from logicore.utils import telegram_api as tg
from logicore.utils.doc_ocr import (
	find_trip_from_qr,
	extract_trip_fields_from_pdf,
)
from logicore.utils.pod_intake import process_pod
from logicore.utils.telegram_i18n import t, get_lang_by_chat


# ─── POD upload (photos) ─────────────────────────────────────────────────────

def process_pod_async(chat_id: str, trip_name: str, file_ids: list[str],
	uploader_user: str, pod_mode: str = "original") -> None:
	"""Background worker: download → compress → attach → notify."""
	tg.send_typing(chat_id)
	lang = get_lang_by_chat(chat_id)

	image_bytes_list = []
	for fid in file_ids:
		data = tg.download_file(fid)
		if data:
			image_bytes_list.append(data)

	if not image_bytes_list:
		tg.send_message(chat_id, t("download_files_failed", lang))
		return

	# Block early if Arrival/Release dates aren't filled
	from logicore.utils.pod_intake import validate_pod_upload_allowed
	if validate_pod_upload_allowed(trip_name):
		_notify_pod_dates_required(chat_id, trip_name, lang)
		return

	result = process_pod(
		trip_name=trip_name,
		image_bytes_list=image_bytes_list,
		uploader_user=uploader_user,
	)

	if result["success"]:
		# Duplicate mode: override pod_status
		if pod_mode == "duplicate":
			frappe.db.set_value("Trip", trip_name, "pod_status", "Duplicate POD Uploaded")
			frappe.db.commit()

		if pod_mode == "replace":
			from logicore.utils.pod_intake import log_pod_replacement
			log_pod_replacement(trip_name, result["file_name"])

		mode_label = {
			"original": t("mode_original", lang),
			"replace": t("mode_original_replaced", lang),
			"duplicate": t("mode_duplicate", lang),
		}.get(pod_mode, "")

		tg.send_message(chat_id, t(
			"pod_upload_success_files", lang,
			trip=trip_name, count=len(image_bytes_list),
			mode=mode_label, filename=result["file_name"],
		))
	else:
		tg.send_message(chat_id, t("pod_upload_failed_retry", lang, error=result["error"]))

	menu_buttons = tg.inline_keyboard([
		[(t("btn_upload_pod", lang), "menu_pod")],
		[(t("btn_exit", lang), "menu_exit")],
	])
	tg.send_message(chat_id, t("what_next", lang), reply_markup=menu_buttons)


# ─── POD upload (single PDF) ─────────────────────────────────────────────────

def process_pod_pdf_async(chat_id: str, file_id: str,
	trip_name: str, uploader_user: str) -> None:
	"""Single POD PDF: QR → check pod_status → upload or ask."""
	tg.send_typing(chat_id)
	lang = get_lang_by_chat(chat_id)

	pdf_bytes = tg.download_file(file_id)
	if not pdf_bytes:
		tg.send_message(chat_id, t("download_pdf_failed", lang))
		return

	if not trip_name:
		from logicore.utils.doc_ocr import find_trip_from_pdf_qr
		trip_name = find_trip_from_pdf_qr(pdf_bytes)

	if not trip_name:
		tg.send_message(chat_id, t("qr_not_detected", lang))
		return

	# Block direct PDF upload until Arrival/Release dates are filled
	from logicore.utils.pod_intake import validate_pod_upload_allowed
	if validate_pod_upload_allowed(trip_name):
		_notify_pod_dates_required(chat_id, trip_name, lang)
		return

	# Check if POD already exists → ask Replace/Duplicate
	pod_status = frappe.db.get_value("Trip", trip_name, "pod_status")
	if pod_status and pod_status != "POD Not Uploaded":
		# Store file_id in session for callback to use
		if frappe.db.exists("Telegram Session", chat_id):
			session = frappe.get_doc("Telegram Session", chat_id)
			session.pending_trip = trip_name
			session.pending_images = json.dumps([file_id])
			session.state = "AWAITING_POD_PHOTOS"
			session.save(ignore_permissions=True)
			frappe.db.commit()

		tg.send_message(chat_id, t(
			"pod_already_uploaded", lang, trip=trip_name, status=pod_status,
		), reply_markup=tg.inline_keyboard([[
			(t("btn_replace_original", lang), f"pod_replace_{trip_name}"),
			(t("btn_upload_duplicate", lang), f"pod_duplicate_{trip_name}"),
			(t("btn_cancel_exit", lang), "menu_exit"),
		]]))
		return

	# Fresh upload
	result = process_pod(
		trip_name=trip_name,
		image_bytes_list=[pdf_bytes],
		uploader_user=uploader_user,
	)
	if result.get("success"):
		tg.send_message(chat_id, t(
			"pod_upload_success_simple", lang, trip=trip_name, filename=result["file_name"],
		))
	else:
		tg.send_message(chat_id, t("pod_upload_failed_simple", lang, error=result.get("error")))

	menu_buttons = tg.inline_keyboard([
		[(t("btn_upload_pod", lang), "menu_pod")],
		[(t("btn_exit", lang), "menu_exit")],
	])
	tg.send_message(chat_id, t("what_next", lang), reply_markup=menu_buttons)


# ─── Trip OCR async ──────────────────────────────────────────────────────────

def process_trip_ocr_async(chat_id: str, file_id: str, ops_user: str) -> None:
	"""Background worker: download PDF → OCR → show confirm card."""
	tg.send_typing(chat_id)
	lang = get_lang_by_chat(chat_id)

	pdf_bytes = tg.download_file(file_id)
	if not pdf_bytes:
		tg.send_message(chat_id, t("download_pdf_failed", lang))
		return

	fields = extract_trip_fields_from_pdf(pdf_bytes)

	if not fields:
		tg.send_message(chat_id, t("ocr_extract_failed", lang))
		return

	if frappe.db.exists("Telegram Session", chat_id):
		session = frappe.get_doc("Telegram Session", chat_id)
		session.ocr_draft = json.dumps(fields)
		session.state = "AWAITING_OCR_CONFIRM"
		session.save(ignore_permissions=True)
		frappe.db.commit()

	card = t(
		"ocr_review_card", lang,
		tcn_no=fields.get("tcntrip_no", "—"),
		date=fields.get("tcntrip_date", "—"),
		vehicle=fields.get("vehicle_type", "—"),
		origin=fields.get("origin_city", "—"),
		destination=fields.get("destination_city_1", "—"),
		customer=fields.get("customer", "—"),
		vendor=fields.get("vendor", "—"),
		lr_no=fields.get("lr_no", "—"),
		packages=fields.get("packages", "—"),
	)

	tg.send_message(chat_id, card,
		reply_markup=tg.inline_keyboard([
			[(t("btn_create_draft_trip", lang), "trip_confirm_ocr"),
			 (t("btn_cancel_x", lang), "trip_cancel")],
		]))


# ─── POD Collection finalization ─────────────────────────────────────────────

def finalize_pod_collection_async(collection_name: str, chat_id: str,
	pod_mode: str = "original") -> None:
	"""Background: merge collection images → PDF → attach to Trip → notify."""
	lang = get_lang_by_chat(chat_id)
	collection = frappe.get_doc("Trip POD Collection", collection_name)
	trip_name = collection.trip
	uploader_user = frappe.db.get_value(
		"Telegram Session", {"chat_id": chat_id}, "telegram_user_map"
	)
	if uploader_user:
		uploader_user = frappe.db.get_value("Telegram User Map", uploader_user, "frappe_user")
	uploader_user = uploader_user or "Administrator"

	# If a POD already exists and no mode was chosen yet, ask Replace/Duplicate first
	if pod_mode == "original":
		pod_status = frappe.db.get_value("Trip", trip_name, "pod_status")
		if pod_status and pod_status != "POD Not Uploaded":
			frappe.db.set_value("Trip POD Collection", collection_name, "status", "Collecting")
			frappe.db.commit()
			tg.send_message(chat_id, t(
				"pod_already_uploaded", lang, trip=trip_name, status=pod_status,
			), reply_markup=tg.inline_keyboard([[
				(t("btn_replace_original", lang), f"podcol_replace_{collection_name}"),
				(t("btn_upload_duplicate", lang), f"podcol_duplicate_{collection_name}"),
				(t("btn_cancel_exit", lang), "menu_exit"),
			]]))
			return

	from logicore.utils.pod_collection import generate_pod_pdf
	result = generate_pod_pdf(collection_name, uploader_user=uploader_user, pod_mode=pod_mode)

	if result["success"]:
		mode_label = {
			"original": t("mode_original", lang),
			"replace": t("mode_original_replaced", lang),
			"duplicate": t("mode_duplicate", lang),
		}.get(pod_mode, t("mode_original", lang))
		tg.send_message(chat_id, t(
			"pod_upload_success_merged", lang,
			trip=trip_name, count=result["count"], mode=mode_label, filename=result["file_name"],
		))
	elif "Arrival Date/Time" in result["error"]:
		# Restore session so user can retry "Complete POD" after ops fills the dates,
		# without re-uploading any images
		if frappe.db.exists("Telegram Session", chat_id):
			session = frappe.get_doc("Telegram Session", chat_id)
			session.state = "AWAITING_POD_PHOTOS"
			session.pending_trip = trip_name
			session.save(ignore_permissions=True)
			frappe.db.commit()

		from logicore.utils.telegram_bot import _build_collection_keyboard
		tg.send_message(chat_id, t("pod_dates_required_with_images", lang, trip=trip_name),
			reply_markup=_build_collection_keyboard(collection_name, lang))
		return
	else:
		tg.send_message(chat_id, t("pod_generation_failed", lang, error=result["error"]))

	menu_buttons = tg.inline_keyboard([
		[(t("btn_upload_pod", lang), "menu_pod")],
		[(t("btn_exit", lang), "menu_exit")],
	])
	tg.send_message(chat_id, t("what_next", lang), reply_markup=menu_buttons)


def add_pending_images_async(chat_id: str, trip_name: str, file_ids: list[str],
                              uploader_user: str) -> None:
	"""Background: download pending file_ids and add them to the collection."""
	from logicore.utils.pod_collection import add_image_to_collection

	lang = get_lang_by_chat(chat_id)
	last_result = None
	for file_id in file_ids:
		file_bytes = tg.download_file(file_id)
		if not file_bytes:
			continue
		last_result = add_image_to_collection(
			trip_name=trip_name,
			file_id=file_id,
			file_bytes=file_bytes,
			uploader_user=uploader_user,
			chat_id=chat_id,
		)

	if not last_result:
		tg.send_message(chat_id, t("pending_images_failed", lang))
		return

	from logicore.utils.telegram_bot import _build_collection_keyboard
	tg.send_message(chat_id, t(
		"pending_images_saved", lang, count=last_result["collected"], trip=trip_name,
	), reply_markup=_build_collection_keyboard(last_result["collection_name"], lang))


# ─── Helper: POD dates-required notice ───────────────────────────────────────

def _notify_pod_dates_required(chat_id: str, trip_name: str, lang: str = "en") -> None:
	"""Tell the user the POD is blocked until Arrival/Release dates are filled."""
	tg.send_message(chat_id, t("pod_dates_required_blocked", lang, trip=trip_name),
		reply_markup=tg.inline_keyboard([
			[(t("btn_upload_pod", lang), "menu_pod")],
			[(t("btn_exit", lang), "menu_exit")],
		]))
