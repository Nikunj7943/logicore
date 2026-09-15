"""
utils/telegram_bot.py
Core Telegram bot router and flow state machine.

Mode is decided by the MENU BUTTON, not by guessing:
  "Upload POD"  -> AWAITING_POD_PHOTOS : photos AND pdf accepted -> attach to Trip
  "Create Trip" -> AWAITING_TRIP_PDF   : pdf -> OCR -> draft Trip
Auth: phone-share (Telegram verified number) -> Driver / Employee lookup.

Language: every chat picks English/Hindi on first /start (stored on
Telegram Session.language). All user-facing strings go through
telegram_i18n.t(key, lang, ...).
"""

import json
import frappe
from frappe.utils import now_datetime

from logicore.utils import telegram_api as tg
from logicore.utils.telegram_i18n import t, get_lang


def handle_update(update: dict) -> None:
	if "callback_query" in update:
		_handle_callback(update["callback_query"])
	elif "message" in update:
		_handle_message(update["message"])


def _handle_message(msg: dict) -> None:
	chat_id = str(msg["chat"]["id"])
	from_id = str(msg.get("from", {}).get("id", chat_id))
	text = msg.get("text", "").strip()

	user_map = _get_user_map(from_id)

	# ── Unregistered user → ask for phone (Share Contact) ────────────────
	if not user_map:
		session = _get_or_create_unauth_session(chat_id)
		if not session.language:
			_send_language_selection(chat_id)
			return
		if "contact" in msg:
			_handle_contact(chat_id, msg, session, from_id)
			return
		_request_phone(chat_id, get_lang(session))
		return

	session = _get_or_create_session(chat_id, user_map.name)
	if not session.language:
		_send_language_selection(chat_id)
		return
	lang = get_lang(session)

	if not user_map.is_active:
		tg.send_message(chat_id, t("account_deactivated", lang))
		return

	frappe.db.set_value("Telegram User Map", user_map.name, "last_seen", now_datetime())

	# Commands
	if text.startswith("/"):
		_handle_command(chat_id, text, session, user_map)
		return

	# Reject albums (multiple files sent together) — one warning per group
	if msg.get("media_group_id") and ("photo" in msg or "document" in msg):
		warn_key = f"tg_album_warn:{chat_id}:{msg['media_group_id']}"
		if not frappe.cache().get_value(warn_key):
			frappe.cache().set_value(warn_key, 1, expires_in_sec=120)
			tg.send_message(chat_id, t("album_warning", lang))
		return

	# Photos -> only valid in POD context
	if "photo" in msg:
		if session.state in ("IDLE", "AWAITING_POD_PHOTOS"):
			_handle_photo(chat_id, msg, session, user_map)
		else:
			tg.send_message(chat_id, t("cancel_before_photo", lang))
		return

	# Documents (PDF) -> route by mode
	if "document" in msg:
		if session.state == "AWAITING_TRIP_PDF":
			_handle_trip_pdf(chat_id, msg, session, user_map)
		elif session.state == "AWAITING_POD_PHOTOS":
			_handle_pod_pdf(chat_id, msg, session, user_map)
		else:
			tg.send_message(chat_id, t("choose_first", lang))
			_send_menu(chat_id, user_map, lang)
		return

	# Plain text while collecting POD: treat as a manual Trip No
	if session.state == "AWAITING_POD_PHOTOS":
		if not session.pending_trip and text:
			if frappe.db.exists("Trip", text):
				trip_name = text
				pending_file_ids = json.loads(session.pending_images or "[]")
				_update_session(session, {
					"pending_trip": trip_name,
					"pending_images": "[]",
				})
				if pending_file_ids:
					tg.send_message(chat_id, t("linked_trip_saving", lang, trip=trip_name))
					frappe.enqueue(
						"logicore.utils.telegram_tasks.add_pending_images_async",
						queue="default",
						chat_id=chat_id,
						trip_name=trip_name,
						file_ids=pending_file_ids,
						uploader_user=user_map.frappe_user,
					)
				else:
					tg.send_message(chat_id, t("linked_trip_send_images", lang, trip=trip_name))
			else:
				tg.send_message(chat_id, t("trip_not_found", lang, trip=text))
			return
		tg.send_message(chat_id, t("keep_sending_images", lang))
		return

	_send_menu(chat_id, user_map, lang)


def _handle_command(chat_id: str, text: str, session, user_map) -> None:
	cmd = text.split()[0].lower()
	lang = get_lang(session)

	if cmd == "/start":
		# Always ask for language first on every /start
		_reset_session(session)
		_send_language_selection(chat_id)

	elif cmd in ("/menu", "/help"):
		_reset_session(session)
		_send_menu(chat_id, user_map, lang)

	elif cmd in ("/change_language", "/changelanguage", "/language", "/lang", "/change"):
		_send_language_selection(chat_id, change=True)

	elif cmd == "/done":
		if session.state == "AWAITING_POD_PHOTOS":
			_finalize_pod_collection(chat_id, session)
		else:
			tg.send_message(chat_id, t("nothing_to_finish", lang))

	elif cmd == "/cancel":
		_reset_session(session)
		tg.send_message(chat_id, t("cancelled_returning", lang))
		_send_menu(chat_id, user_map, lang)

	else:
		tg.send_message(chat_id, t("unknown_command", lang))


# ── POD: photos → collection flow ────────────────────────────────────────────

def _handle_photo(chat_id: str, msg: dict, session, user_map) -> None:
	tg.send_typing(chat_id)
	lang = get_lang(session)

	photo = msg["photo"][-1]
	file_id = photo["file_id"]

	# Download immediately
	file_bytes = tg.download_file(file_id)
	if not file_bytes:
		tg.send_message(chat_id, t("download_photo_failed", lang))
		return

	# ── Replace-mode: user tapped "🔄 Img N" and is now sending replacement ──
	replace_ctx = json.loads(session.ocr_draft or "{}") if session.ocr_draft else {}
	if replace_ctx.get("replace_slot"):
		sequence = replace_ctx["replace_slot"]
		collection_name = replace_ctx["collection_name"]
		trip_name = session.pending_trip

		from logicore.utils.pod_collection import replace_image_in_collection
		result = replace_image_in_collection(
			collection_name=collection_name,
			sequence=sequence,
			file_id=file_id,
			file_bytes=file_bytes,
			uploader_user=user_map.frappe_user,
		)
		# Clear replace mode
		_update_session(session, {"ocr_draft": None})

		tg.send_message(chat_id, t("image_replaced", lang, seq=sequence, trip=trip_name),
			reply_markup=_build_collection_keyboard(collection_name, lang))
		return

	# Always scan for a QR — a new QR may switch context to a different trip
	from logicore.utils.doc_ocr import find_trip_from_qr
	qr_trip = find_trip_from_qr(file_bytes)

	switched_trip = False
	if qr_trip and qr_trip != session.pending_trip:
		# New trip detected — switch context to it
		trip_name = qr_trip
		switched_trip = bool(session.pending_trip)
		_update_session(session, {
			"state": "AWAITING_POD_PHOTOS",
			"pending_trip": trip_name,
		})
	else:
		# No QR on this photo — find trips with an active (Collecting) collection
		# in this chat, so the user can pick the correct one
		active_trips = [r.trip for r in frappe.db.get_all(
			"Trip POD Collection",
			filters={"chat_id": chat_id, "status": "Collecting"},
			fields=["trip"],
			order_by="modified desc",
		)]

		if len(active_trips) == 0:
			trip_name = None
		elif len(active_trips) == 1:
			trip_name = active_trips[0]
		else:
			# Multiple trips in progress — ask which one this image belongs to
			_update_session(session, {
				"state": "AWAITING_POD_PHOTOS",
				"ocr_draft": json.dumps({"awaiting_trip_pick": file_id}),
			})
			rows = [[(t_name, f"pod_pick_trip_{t_name}")] for t_name in active_trips]
			tg.send_message(chat_id, t("multiple_trips_prompt", lang),
				reply_markup=tg.inline_keyboard(rows))
			return

	if not trip_name:
		# No QR and no trip context yet — ask user for trip number
		pending = json.loads(session.pending_images or "[]")
		pending.append(file_id)
		_update_session(session, {
			"state": "AWAITING_POD_PHOTOS",
			"pending_images": json.dumps(pending),
		})
		tg.send_message(chat_id, t("photo_saved_no_qr", lang))
		return

	# Add image to collection
	from logicore.utils.pod_collection import add_image_to_collection
	result = add_image_to_collection(
		trip_name=trip_name,
		file_id=file_id,
		file_bytes=file_bytes,
		uploader_user=user_map.frappe_user,
		chat_id=chat_id,
	)

	prefix = t("new_qr_switched_prefix", lang, trip=trip_name) if switched_trip else ""
	tg.send_message(chat_id,
		f"{prefix}" + t("image_saved_progress", lang, count=result["collected"], trip=trip_name),
		reply_markup=_build_collection_keyboard(result["collection_name"], lang))


def _build_collection_keyboard(collection_name: str, lang: str = "en"):
	"""Build inline keyboard showing uploaded images + Done button.

	Uploaded images show as '🔄 Img N' (tap to replace).
	Rows: up to 3 buttons per row, then Done row.
	"""
	images = frappe.db.get_all(
		"Trip POD Collection Image",
		filters={"parent": collection_name},
		fields=["sequence"],
		order_by="sequence asc",
	)
	collected_seqs = [r.sequence for r in images]

	if not collected_seqs:
		return None

	img_buttons = [
		(t("btn_img_n", lang, seq=seq), f"prim_{collection_name}_{seq}")
		for seq in sorted(collected_seqs)
	]

	# Split into rows of 3
	rows = [img_buttons[i:i+3] for i in range(0, len(img_buttons), 3)]

	next_seq = max(collected_seqs) + 1
	rows.append([(t("btn_upload_image_n", lang, seq=next_seq), f"pod_collection_next_{collection_name}_{next_seq}")])
	rows.append([(t("btn_complete_pod", lang), f"pod_collection_done_{collection_name}")])
	rows.append([(t("btn_exit", lang), f"pod_collection_exit_{collection_name}")])

	return tg.inline_keyboard(rows)


def _finalize_pod_collection(chat_id: str, session) -> None:
	"""Manual /done — finalize the active collection early."""
	lang = get_lang(session)
	trip_name = session.pending_trip
	if not trip_name:
		tg.send_message(chat_id, t("trip_not_identified", lang))
		return

	collection_name = frappe.db.get_value(
		"Trip POD Collection",
		{"trip": trip_name, "status": "Collecting"},
		"name",
	)
	if not collection_name:
		tg.send_message(chat_id, t("no_active_collection", lang))
		return

	collected = frappe.db.get_value("Trip POD Collection", collection_name, "collected_count") or 0
	if collected == 0:
		tg.send_message(chat_id, t("no_images_yet", lang))
		return

	_reset_session(session)
	frappe.db.set_value("Trip POD Collection", collection_name, "status", "Processing")
	frappe.db.commit()

	tg.send_message(chat_id, t("generating_pod_pdf", lang, count=collected, trip=trip_name))

	frappe.enqueue(
		"logicore.utils.telegram_tasks.finalize_pod_collection_async",
		queue="long",
		collection_name=collection_name,
		chat_id=chat_id,
	)


# ── POD: pdf (in POD mode) ──────────────────────────────────────────────────

def _handle_pod_pdf(chat_id: str, msg: dict, session, user_map) -> None:
	lang = get_lang(session)
	doc = msg["document"]
	if doc.get("mime_type", "") != "application/pdf":
		tg.send_message(chat_id, t("pdf_or_photo_required", lang))
		return

	# If photos are already being collected for this trip, a PDF can't be mixed in.
	# Guide the user instead of silently dropping the PDF.
	if session.pending_trip:
		active = frappe.db.get_value(
			"Trip POD Collection",
			{"trip": session.pending_trip, "status": "Collecting", "chat_id": chat_id},
			["name", "collected_count"],
			as_dict=True,
		)
		if active and (active.collected_count or 0) > 0:
			tg.send_message(chat_id, t(
				"pdf_cannot_mix_photos", lang,
				trip=session.pending_trip, count=active.collected_count,
			), reply_markup=_build_collection_keyboard(active.name, lang))
			return

	# Fresh PDF POD → identify trip via QR in background, then upload
	trip_hint = session.pending_trip
	_reset_session(session)
	tg.send_uploading(chat_id)
	tg.send_message(chat_id, t("processing_pod_pdf", lang))

	frappe.enqueue(
		"logicore.utils.telegram_tasks.process_pod_pdf_async",
		queue="long",
		chat_id=chat_id,
		file_id=doc["file_id"],
		trip_name=trip_hint,
		uploader_user=user_map.frappe_user,
	)


# ── Trip: pdf (in Create-Trip mode) ─────────────────────────────────────────

def _handle_trip_pdf(chat_id: str, msg: dict, session, user_map) -> None:
	lang = get_lang(session)
	if user_map.role not in ("Ops Staff", "Admin"):
		tg.send_message(chat_id, t("ops_staff_only_create", lang))
		return

	doc = msg["document"]
	if doc.get("mime_type", "") != "application/pdf":
		tg.send_message(chat_id, t("pdf_tcn_required", lang))
		return

	tg.send_typing(chat_id)
	tg.send_message(chat_id, t("pdf_received_extracting", lang))

	frappe.enqueue(
		"logicore.utils.telegram_tasks.process_trip_ocr_async",
		queue="default",
		chat_id=chat_id,
		file_id=doc["file_id"],
		ops_user=user_map.frappe_user,
	)


def _handle_callback(cb: dict) -> None:
	chat_id = str(cb["message"]["chat"]["id"])
	from_id = str(cb["from"]["id"])
	msg_id = cb["message"]["message_id"]
	data = cb.get("data", "")

	# ── Language selection works even before the user is registered ─────────
	if data in ("lang_en", "lang_hi", "lang_change_en", "lang_change_hi"):
		_handle_language_selection(chat_id, msg_id, from_id, cb, data)
		return

	user_map = _get_user_map(from_id)
	if not user_map:
		tg.answer_callback(cb["id"], t("not_authorised"))
		return

	session = _get_or_create_session(chat_id, user_map.name)
	lang = get_lang(session)

	if data.startswith("pod_collection_done_"):
		collection_name = data[len("pod_collection_done_"):]
		tg.answer_callback(cb["id"], t("processing_short", lang))
		collected = frappe.db.get_value(
			"Trip POD Collection", collection_name, "collected_count") or 0
		trip_name = frappe.db.get_value(
			"Trip POD Collection", collection_name, "trip") or ""
		tg.edit_message_text(chat_id, msg_id,
			t("generating_pod_pdf", lang, count=collected, trip=trip_name))
		_reset_session(session)
		frappe.db.set_value("Trip POD Collection", collection_name, "status", "Processing")
		frappe.db.commit()
		frappe.enqueue(
			"logicore.utils.telegram_tasks.finalize_pod_collection_async",
			queue="long",
			collection_name=collection_name,
			chat_id=chat_id,
		)

	elif data.startswith("podcol_replace_"):
		collection_name = data[len("podcol_replace_"):]
		trip_name = frappe.db.get_value("Trip POD Collection", collection_name, "trip") or ""
		tg.answer_callback(cb["id"], t("replacing_pod_cb", lang))
		tg.edit_message_text(chat_id, msg_id, t("replacing_pod_progress", lang, trip=trip_name))
		_reset_session(session)
		frappe.db.set_value("Trip POD Collection", collection_name, "status", "Processing")
		frappe.db.commit()
		frappe.enqueue(
			"logicore.utils.telegram_tasks.finalize_pod_collection_async",
			queue="long",
			collection_name=collection_name,
			chat_id=chat_id,
			pod_mode="replace",
		)

	elif data.startswith("podcol_duplicate_"):
		collection_name = data[len("podcol_duplicate_"):]
		trip_name = frappe.db.get_value("Trip POD Collection", collection_name, "trip") or ""
		tg.answer_callback(cb["id"], t("uploading_duplicate_cb", lang))
		tg.edit_message_text(chat_id, msg_id, t("uploading_duplicate_progress", lang, trip=trip_name))
		_reset_session(session)
		frappe.db.set_value("Trip POD Collection", collection_name, "status", "Processing")
		frappe.db.commit()
		frappe.enqueue(
			"logicore.utils.telegram_tasks.finalize_pod_collection_async",
			queue="long",
			collection_name=collection_name,
			chat_id=chat_id,
			pod_mode="duplicate",
		)

	elif data.startswith("pod_collection_resume_"):
		collection_name = data[len("pod_collection_resume_"):]
		trip_name = frappe.db.get_value("Trip POD Collection", collection_name, "trip")
		tg.answer_callback(cb["id"])
		_update_session(session, {
			"state": "AWAITING_POD_PHOTOS",
			"pending_trip": trip_name,
			"pending_images": None,
			"ocr_draft": None,
		})
		tg.edit_message_text(chat_id, msg_id, t("send_next_photos", lang, trip=trip_name))

	elif data.startswith("pod_pick_trip_"):
		trip_name = data[len("pod_pick_trip_"):]
		draft = json.loads(session.ocr_draft or "{}")
		file_id = draft.get("awaiting_trip_pick")
		if not file_id:
			tg.answer_callback(cb["id"], t("session_expired_resend_photo", lang))
			return

		tg.answer_callback(cb["id"], t("processing_short", lang))
		file_bytes = tg.download_file(file_id)
		if not file_bytes:
			tg.edit_message_text(chat_id, msg_id, t("could_not_download_photo_resend", lang))
			return

		_update_session(session, {
			"state": "AWAITING_POD_PHOTOS",
			"pending_trip": trip_name,
			"ocr_draft": None,
		})

		from logicore.utils.pod_collection import add_image_to_collection
		result = add_image_to_collection(
			trip_name=trip_name,
			file_id=file_id,
			file_bytes=file_bytes,
			uploader_user=user_map.frappe_user,
			chat_id=chat_id,
		)
		tg.edit_message_text(chat_id, msg_id,
			t("image_saved_progress", lang, count=result["collected"], trip=trip_name),
			reply_markup=_build_collection_keyboard(result["collection_name"], lang))

	elif data.startswith("pod_collection_next_"):
		# pod_collection_next_{collection_name}_{sequence}
		parts = data[len("pod_collection_next_"):].rsplit("_", 1)
		if len(parts) == 2:
			collection_name, seq_str = parts
			tg.answer_callback(cb["id"], t("send_photo_for_image_cb", lang, seq=seq_str))
			tg.edit_message_text(chat_id, msg_id, t("send_photo_for_image_progress", lang, seq=seq_str))
		else:
			tg.answer_callback(cb["id"])

	elif data.startswith("pod_collection_exit_"):
		tg.answer_callback(cb["id"], t("exited_cb", lang))
		_reset_session(session)
		tg.edit_message_text(chat_id, msg_id, t("exited_upload_progress", lang))
		_send_menu(chat_id, user_map, lang)

	elif data.startswith("prim_"):
		# pod replace image: prim_{collection_name}_{sequence}
		parts = data[len("prim_"):].rsplit("_", 1)
		if len(parts) == 2:
			collection_name, seq_str = parts
			try:
				sequence = int(seq_str)
			except ValueError:
				tg.answer_callback(cb["id"], "Invalid selection")
				return
			tg.answer_callback(cb["id"], t("send_new_photo_for_image_cb", lang, seq=sequence))
			_update_session(session, {
				"state": "AWAITING_POD_PHOTOS",
				"ocr_draft": json.dumps({
					"replace_slot": sequence,
					"collection_name": collection_name,
				}),
			})
			tg.edit_message_text(chat_id, msg_id, t("send_replacement_photo_progress", lang, seq=sequence))
		else:
			tg.answer_callback(cb["id"])

	elif data.startswith("pod_replace_"):
		trip_name = data[len("pod_replace_"):]
		pending = json.loads(session.pending_images or "[]")
		tg.answer_callback(cb["id"], t("replacing_pod_cb", lang))
		tg.edit_message_text(chat_id, msg_id, t("replacing_pod_progress", lang, trip=trip_name))
		_reset_session(session)
		frappe.enqueue(
			"logicore.utils.telegram_tasks.process_pod_async",
			queue="long",
			chat_id=chat_id,
			trip_name=trip_name,
			file_ids=pending,
			uploader_user=user_map.frappe_user,
			pod_mode="replace",
		)

	elif data.startswith("pod_duplicate_"):
		trip_name = data[len("pod_duplicate_"):]
		pending = json.loads(session.pending_images or "[]")
		tg.answer_callback(cb["id"], t("uploading_duplicate_cb", lang))
		tg.edit_message_text(chat_id, msg_id, t("uploading_duplicate_progress", lang, trip=trip_name))
		_reset_session(session)
		frappe.enqueue(
			"logicore.utils.telegram_tasks.process_pod_async",
			queue="long",
			chat_id=chat_id,
			trip_name=trip_name,
			file_ids=pending,
			uploader_user=user_map.frappe_user,
			pod_mode="duplicate",
		)

	elif data.startswith("trip_confirm_"):
		draft_key = data[len("trip_confirm_"):]
		tg.answer_callback(cb["id"], t("creating_trip_cb", lang))
		_confirm_trip_creation(chat_id, msg_id, draft_key, session, user_map)

	elif data == "trip_cancel":
		tg.answer_callback(cb["id"], t("cancelled_cb", lang))
		_reset_session(session)
		tg.edit_message_text(chat_id, msg_id, t("trip_creation_cancelled", lang))

	elif data == "menu_pod":
		tg.answer_callback(cb["id"])
		_update_session(session, {
			"state": "AWAITING_POD_PHOTOS",
			"pending_trip": None,
			"pending_images": None,
			"ocr_draft": None,
		})

		# Resume any in-progress collections from a previous (expired) session
		pending = frappe.db.get_all(
			"Trip POD Collection",
			filters={"chat_id": chat_id, "status": "Collecting"},
			fields=["name", "trip", "collected_count"],
			order_by="modified desc",
		)

		rows = []
		for p in pending:
			rows.append([(
				t("btn_add_photos_resume", lang, trip=p.trip, count=p.collected_count),
				f"pod_collection_resume_{p.name}",
			)])
			rows.append([(
				t("btn_complete_pod_resume", lang, trip=p.trip, count=p.collected_count),
				f"pod_collection_done_{p.name}",
			)])

		text = t("upload_pod_menu_text", lang)
		if pending:
			text += t("finish_existing_trip_suffix", lang)

		tg.edit_message_text(chat_id, msg_id, text,
			reply_markup=tg.inline_keyboard(rows) if rows else None)

	elif data == "menu_trip":
		if user_map.role not in ("Ops Staff", "Admin"):
			tg.answer_callback(cb["id"], t("ops_staff_only_alert", lang), show_alert=True)
			return
		tg.answer_callback(cb["id"])
		_update_session(session, {
			"state": "AWAITING_TRIP_PDF",
			"pending_trip": None,
			"pending_images": None,
			"ocr_draft": None,
		})
		tg.edit_message_text(chat_id, msg_id, t("create_trip_menu_text", lang))

	elif data == "menu_exit":
		tg.answer_callback(cb["id"], t("goodbye_cb", lang))
		_reset_session(session)
		tg.edit_message_text(chat_id, msg_id, t("session_ended", lang))

	else:
		tg.answer_callback(cb["id"])


def _confirm_trip_creation(chat_id: str, msg_id: int, draft_key: str,
                           session, user_map) -> None:
	lang = get_lang(session)
	ocr_data = json.loads(session.ocr_draft or "{}")
	if not ocr_data:
		tg.edit_message_text(chat_id, msg_id, t("session_expired_resend_pdf", lang))
		return

	try:
		frappe.set_user(user_map.frappe_user)
		trip = frappe.new_doc("Trip")

		if ocr_data.get("lr_no"):
			trip.trip_type = "Other"
			trip.lr_no = ocr_data["lr_no"]
		else:
			trip.trip_type = "Primary"

		if ocr_data.get("tcntrip_no"):
			trip.tcntrip_no = ocr_data["tcntrip_no"]
		if ocr_data.get("tcntrip_date"):
			trip.tcntrip_date = ocr_data["tcntrip_date"]

		link_map = {
			"customer": "Customer",
			"vehicle_type": "Vehicle Type",
			"vendor": "Supplier",
			"origin_city": "City",
			"destination_city_1": "City",
		}
		for field, doctype in link_map.items():
			val = ocr_data.get(field)
			if val and frappe.db.exists(doctype, val):
				setattr(trip, field, val)

		trip.trip_status = "Open"
		trip.docstatus = 0
		trip.flags.ignore_mandatory = True
		trip.insert(ignore_permissions=True)
		frappe.db.commit()

		_reset_session(session)
		tg.edit_message_text(chat_id, msg_id, t(
			"trip_created_success", lang,
			trip=trip.name, type=trip.trip_type, tcn=ocr_data.get("tcntrip_no", "—"),
		))
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Trip Creation Error")
		tg.edit_message_text(chat_id, msg_id, t("trip_creation_error", lang, error=str(e)))


def _menu_payload(user_map, lang: str = "en"):
	"""Return (text, reply_markup) for the main menu — reused by send and edit."""
	name = user_map.full_name or user_map.telegram_id
	role = user_map.role

	text = t("greeting", lang, name=name)

	rows = [[(t("btn_upload_pod", lang), "menu_pod")]]
	if role in ("Ops Staff", "Admin"):
		rows.append([(t("btn_create_trip", lang), "menu_trip")])
	rows.append([(t("btn_exit", lang), "menu_exit")])

	return text, tg.inline_keyboard(rows)


def _send_menu(chat_id: str, user_map, lang: str = "en") -> None:
	text, kb = _menu_payload(user_map, lang)
	tg.send_message(chat_id, text, reply_markup=kb)


# ── Language selection ────────────────────────────────────────────────────────

def _send_language_selection(chat_id: str, change: bool = False) -> None:
	"""Show the English/Hindi picker.

	change=False → first-time / on /start: after picking, proceed to menu (or phone).
	change=True  → /change_language: after picking, just confirm and stay put — never
	               bounce the user back to the main menu.
	"""
	suffix = "change_" if change else ""
	tg.send_message(chat_id, t("lang_select"),
		reply_markup=tg.inline_keyboard([
			[("English", f"lang_{suffix}en"), ("हिन्दी", f"lang_{suffix}hi")],
		]))


def _handle_language_selection(chat_id: str, msg_id: int, from_id: str, cb: dict, data: str) -> None:
	is_change = data.startswith("lang_change_")
	lang = "hi" if data.endswith("_hi") else "en"

	user_map = _get_user_map(from_id)
	if user_map:
		session = _get_or_create_session(chat_id, user_map.name)
	else:
		session = _get_or_create_unauth_session(chat_id)

	_update_session(session, {"language": lang})
	tg.answer_callback(cb["id"])

	# ── /change_language → only switch the language, never re-prompt the menu ──
	if is_change:
		tg.edit_message_text(chat_id, msg_id, t("language_set", lang))
		if not user_map:
			_request_phone(chat_id, lang)
			return
		# If a POD photo collection is in progress, re-show its keyboard in the
		# new language so the user can carry on. Otherwise the confirmation above
		# is enough — leave whatever was on screen untouched.
		if session.state == "AWAITING_POD_PHOTOS" and session.pending_trip:
			collection_name = frappe.db.get_value(
				"Trip POD Collection",
				{"trip": session.pending_trip, "status": "Collecting", "chat_id": chat_id},
				"name",
			)
			kb = _build_collection_keyboard(collection_name, lang) if collection_name else None
			if kb:
				tg.send_message(chat_id, t("language_changed_continue", lang), reply_markup=kb)
		return

	# ── First-time / /start → go straight to the next step, no confirmation ──
	if not user_map:
		_request_phone(chat_id, lang)
		return

	# Replace the picker message with the menu itself (no "language set" notice)
	text, kb = _menu_payload(user_map, lang)
	tg.edit_message_text(chat_id, msg_id, text, reply_markup=kb)


# ── Authentication (phone-share) ──────────────────────────────────────────────

def _request_phone(chat_id: str, lang: str = "en") -> None:
	tg.send_message(chat_id, t("welcome_share_phone", lang),
		reply_markup={
			"keyboard": [[{
				"text": t("btn_share_phone", lang),
				"request_contact": True
			}]],
			"resize_keyboard": True,
			"one_time_keyboard": True
		})


def _handle_contact(chat_id: str, msg: dict, session, from_id: str) -> None:
	lang = get_lang(session)
	contact = msg.get("contact", {})

	if str(contact.get("user_id", "")) != from_id:
		tg.send_message(chat_id, t("share_own_number_only", lang),
			reply_markup={"remove_keyboard": True})
		_request_phone(chat_id, lang)
		return

	phone = contact.get("phone_number", "").strip().replace("+", "").replace(" ", "").replace("-", "")
	if phone.startswith("91") and len(phone) == 12:
		phone = phone[2:]
	if len(phone) > 10:
		phone = phone[-10:]

	# Remove the Share Phone keyboard silently
	tg.send_typing(chat_id)

	existing_name = frappe.db.get_value(
		"Telegram User Map", {"telegram_id": from_id}, "name"
	)
	if existing_name:
		existing_doc = frappe.get_doc("Telegram User Map", existing_name)
		if not existing_doc.is_active:
			frappe.db.set_value("Telegram User Map", existing_name, "is_active", 1)
			frappe.db.commit()
		_update_session(session, {
			"state": "IDLE",
			"telegram_user_map": existing_name,
		})
		tg.send_message(chat_id, t("welcome_back", lang, name=existing_doc.full_name))
		_send_menu(chat_id, existing_doc, lang)
		return

	driver = frappe.db.get_value(
		"Driver",
		{"cell_number": phone, "status": "Active"},
		["name", "full_name", "user"],
		as_dict=True
	)
	if driver:
		_register_user(chat_id, from_id, session,
			name=driver.full_name,
			frappe_user=driver.user or "Administrator",
			role="Driver")
		return

	employee = frappe.db.get_value(
		"Employee",
		{"cell_number": phone, "status": "Active"},
		["name", "employee_name", "user_id"],
		as_dict=True
	)
	if employee:
		_register_user(chat_id, from_id, session,
			name=employee.employee_name,
			frappe_user=employee.user_id or "Administrator",
			role="Ops Staff")
		return

	tg.send_message(chat_id, t("access_denied", lang, phone=phone),
		reply_markup={"remove_keyboard": True})


def _register_user(chat_id: str, from_id: str, session,
                   name: str, frappe_user: str, role: str) -> None:
	lang = get_lang(session)
	try:
		user_map = frappe.get_doc({
			"doctype": "Telegram User Map",
			"telegram_id": from_id,
			"frappe_user": frappe_user,
			"role": role,
			"is_active": 1,
		})
		user_map.insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.db.set_value("Telegram User Map", user_map.name, "full_name", name)
		frappe.db.commit()

	except frappe.DuplicateEntryError:
		frappe.db.rollback()
		existing = frappe.db.get_value(
			"Telegram User Map", {"telegram_id": from_id}, "name"
		)
		if not existing:
			tg.send_message(chat_id, t("registration_error", lang))
			return
		user_map = frappe.get_doc("Telegram User Map", existing)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "User Registration Error")
		tg.send_message(chat_id, t("registration_failed", lang))
		return

	_update_session(session, {
		"state": "IDLE",
		"telegram_user_map": user_map.name,
	})

	tg.send_message(chat_id, t("verified_welcome", lang, name=name, role=role),
		reply_markup={"remove_keyboard": True})

	user_map_doc = frappe.get_doc("Telegram User Map", user_map.name)
	_send_menu(chat_id, user_map_doc, lang)


# ── Session helpers ───────────────────────────────────────────────────────────

def _get_user_map(telegram_id: str):
	name = frappe.db.get_value("Telegram User Map",
		{"telegram_id": telegram_id, "is_active": 1}, "name")
	if name:
		return frappe.get_doc("Telegram User Map", name)
	return None


def _get_or_create_unauth_session(chat_id: str):
	if frappe.db.exists("Telegram Session", chat_id):
		return frappe.get_doc("Telegram Session", chat_id)
	session = frappe.get_doc({
		"doctype": "Telegram Session",
		"chat_id": chat_id,
		"state": "IDLE",
		"last_activity": now_datetime(),
	})
	session.insert(ignore_permissions=True)
	frappe.db.commit()
	return session


def _get_or_create_session(chat_id: str, user_map_name: str):
	if frappe.db.exists("Telegram Session", chat_id):
		return frappe.get_doc("Telegram Session", chat_id)
	session = frappe.get_doc({
		"doctype": "Telegram Session",
		"chat_id": chat_id,
		"telegram_user_map": user_map_name,
		"state": "IDLE",
		"last_activity": now_datetime(),
	})
	session.insert(ignore_permissions=True)
	frappe.db.commit()
	return session


def _update_session(session, fields: dict) -> None:
	fields["last_activity"] = now_datetime()
	for k, v in fields.items():
		setattr(session, k, v)
	session.save(ignore_permissions=True)
	frappe.db.commit()


def _reset_session(session) -> None:
	_update_session(session, {
		"state": "IDLE",
		"pending_trip": None,
		"pending_images": None,
		"ocr_draft": None,
	})
