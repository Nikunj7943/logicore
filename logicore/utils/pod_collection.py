"""
utils/pod_collection.py
Trip POD Collection — image intake and PDF finalization.

Flow:
  1. First photo (QR) → get_or_create_collection → add_image_to_collection
  2. Subsequent photos → add_image_to_collection
  3. User taps "Complete POD" → generate_pod_pdf → attach to Trip
"""

import os
import subprocess
import tempfile
import frappe
from frappe.utils import now_datetime


def get_or_create_collection(trip_name: str, chat_id: str = "") -> str:
	"""Return name of the active 'Collecting' record, or create a fresh one."""
	existing = frappe.db.get_value(
		"Trip POD Collection",
		{"trip": trip_name, "status": "Collecting"},
		"name",
	)
	if existing:
		return existing

	doc = frappe.get_doc({
		"doctype": "Trip POD Collection",
		"trip": trip_name,
		"status": "Collecting",
		"collected_count": 0,
		"chat_id": chat_id,
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc.name


def add_image_to_collection(trip_name: str, file_id: str, file_bytes: bytes,
                             uploader_user: str, chat_id: str = "") -> dict:
	"""
	Save image file and append it to the Trip POD Collection.

	Returns:
	  {"collected": int, "collection_name": str}
	"""
	collection_name = get_or_create_collection(trip_name, chat_id)
	collection = frappe.get_doc("Trip POD Collection", collection_name)

	sequence = len(collection.images) + 1

	from datetime import datetime
	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	filename = f"POD_{trip_name}_{sequence:02d}_{ts}.jpg"

	frappe.set_user(uploader_user)
	file_doc = frappe.get_doc({
		"doctype": "File",
		"file_name": filename,
		"attached_to_doctype": "Trip POD Collection",
		"attached_to_name": collection_name,
		"is_private": 0,
		"content": file_bytes,
	})
	file_doc.save(ignore_permissions=True)

	collection.append("images", {
		"sequence": sequence,
		"telegram_file_id": file_id,
		"image_file": file_doc.file_url,
		"uploaded_by": uploader_user,
		"uploaded_at": now_datetime(),
	})
	collection.collected_count = sequence
	collection.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"collected": sequence,
		"collection_name": collection_name,
	}


def generate_pod_pdf(collection_name: str, uploader_user: str = "Administrator",
                     pod_mode: str = "original") -> dict:
	"""
	Merge all images in the collection into one PDF and attach it to the Trip.

	pod_mode: "original" | "replace" (delete old POD first) | "duplicate".

	Returns: {"success": bool, "file_url": str, "file_name": str, "error": str}
	"""
	collection = frappe.get_doc("Trip POD Collection", collection_name)
	trip_name = collection.trip

	if not collection.images:
		_mark_failed(collection_name)
		return {"success": False, "error": "No images in collection"}

	# POD requires unloading-site Arrival/Release date-times (shared rule)
	from logicore.utils.pod_intake import validate_pod_upload_allowed
	block = validate_pod_upload_allowed(trip_name)
	if block:
		frappe.db.set_value("Trip POD Collection", collection_name, "status", "Collecting")
		frappe.db.commit()
		return {"success": False, "error": block}

	tmp_dir = tempfile.mkdtemp(prefix="tms_podcol_")
	try:
		import img2pdf

		# Gather image file paths in sequence order
		image_paths = []
		for row in sorted(collection.images, key=lambda r: r.sequence or 0):
			if not row.image_file:
				continue
			file_doc = frappe.db.get_value("File", {"file_url": row.image_file}, "name")
			if not file_doc:
				continue
			f = frappe.get_doc("File", file_doc)
			full_path = f.get_full_path()
			if os.path.exists(full_path):
				image_paths.append(full_path)

		if not image_paths:
			_mark_failed(collection_name)
			return {"success": False, "error": "Image files not found on disk"}

		pdf_filename = f"POD_{trip_name}_{now_datetime().strftime('%Y%m%d_%H%M%S')}.pdf"
		raw_pdf_path = os.path.join(tmp_dir, f"raw_{pdf_filename}")
		pdf_path = os.path.join(tmp_dir, pdf_filename)

		with open(raw_pdf_path, "wb") as f:
			f.write(img2pdf.convert(image_paths))

		# Compress with Ghostscript (same /ebook settings as old POD pipeline)
		gs_cmd = [
			"gs",
			"-sDEVICE=pdfwrite",
			"-dCompatibilityLevel=1.4",
			"-dPDFSETTINGS=/ebook",
			"-dNOPAUSE",
			"-dQUIET",
			"-dBATCH",
			f"-sOutputFile={pdf_path}",
			raw_pdf_path,
		]
		gs_result = subprocess.run(gs_cmd, capture_output=True, timeout=120)
		if gs_result.returncode != 0:
			frappe.log_error(gs_result.stderr.decode(), "POD Collection GS Compress Error")
			pdf_path = raw_pdf_path  # fallback: use uncompressed PDF

		with open(pdf_path, "rb") as f:
			pdf_bytes = f.read()

		# Attach PDF to Trip
		frappe.set_user(uploader_user)
		pdf_file = frappe.get_doc({
			"doctype": "File",
			"file_name": pdf_filename,
			"attached_to_doctype": "Trip",
			"attached_to_name": trip_name,
			"is_private": 0,
			"content": pdf_bytes,
		})
		pdf_file.save(ignore_permissions=True)

		# Update Trip pod_status according to the chosen mode
		if pod_mode == "duplicate":
			frappe.db.set_value("Trip", trip_name, {
				"pod_status": "Duplicate POD Uploaded",
				"uploaded_pod_originalduplicate": "Duplicate",
			})
		else:
			frappe.db.set_value("Trip", trip_name, {
				"pod_status": "Original POD Uploaded",
				"uploaded_pod_originalduplicate": "Original",
			})

		# Mark collection complete
		frappe.db.set_value("Trip POD Collection", collection_name, {
			"status": "Completed",
			"pod_file_url": pdf_file.file_url,
			"completed_at": now_datetime(),
		})
		frappe.db.commit()

		if pod_mode == "replace":
			from logicore.utils.pod_intake import log_pod_replacement
			log_pod_replacement(trip_name, pdf_filename)

		return {
			"success": True,
			"file_url": pdf_file.file_url,
			"file_name": pdf_filename,
			"count": len(image_paths),
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "POD Collection PDF Error")
		_mark_failed(collection_name)
		return {"success": False, "error": str(e)}

	finally:
		import shutil
		shutil.rmtree(tmp_dir, ignore_errors=True)


def replace_image_in_collection(collection_name: str, sequence: int,
                                 file_id: str, file_bytes: bytes,
                                 uploader_user: str) -> dict:
	"""
	Replace an existing image slot (by sequence number) with new image bytes.
	Returns same dict as add_image_to_collection.
	"""
	collection = frappe.get_doc("Trip POD Collection", collection_name)

	# Find the row to replace
	target_row = None
	for row in collection.images:
		if row.sequence == sequence:
			target_row = row
			break

	from datetime import datetime
	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	trip_name = collection.trip
	filename = f"POD_{trip_name}_{sequence:02d}_{ts}.jpg"

	# Delete old file if exists
	if target_row and target_row.image_file:
		old_file = frappe.db.get_value("File", {"file_url": target_row.image_file}, "name")
		if old_file:
			try:
				frappe.delete_doc("File", old_file, force=True, ignore_permissions=True)
			except Exception:
				pass

	# Save new file
	frappe.set_user(uploader_user)
	file_doc = frappe.get_doc({
		"doctype": "File",
		"file_name": filename,
		"attached_to_doctype": "Trip POD Collection",
		"attached_to_name": collection_name,
		"is_private": 0,
		"content": file_bytes,
	})
	file_doc.save(ignore_permissions=True)

	if target_row:
		target_row.telegram_file_id = file_id
		target_row.image_file = file_doc.file_url
		target_row.uploaded_by = uploader_user
		target_row.uploaded_at = now_datetime()
	else:
		# Slot didn't exist yet — append
		collection.append("images", {
			"sequence": sequence,
			"telegram_file_id": file_id,
			"image_file": file_doc.file_url,
			"uploaded_by": uploader_user,
			"uploaded_at": now_datetime(),
		})
		collection.collected_count = len(collection.images)

	collection.save(ignore_permissions=True)
	frappe.db.commit()

	collected = collection.collected_count or len(collection.images)

	return {
		"collected": collected,
		"collection_name": collection_name,
	}


def _mark_failed(collection_name: str) -> None:
	frappe.db.set_value("Trip POD Collection", collection_name, "status", "Failed")
	frappe.db.commit()
