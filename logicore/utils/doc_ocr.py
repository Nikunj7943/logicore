"""
utils/doc_ocr.py
QR/barcode decode + PDF OCR extraction for TCN Summary Sheet.
"""

import io
import re
import frappe


def decode_qr_from_bytes(image_bytes: bytes) -> str | None:
	"""Scan image bytes for QR code. Returns decoded string or None.

	Tries multiple scales because Telegram photos are large and the QR is small.
	"""
	try:
		from pyzbar.pyzbar import decode as zbar_decode
		from PIL import Image, ImageFilter

		img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

		# Try at several resolutions — smaller often helps pyzbar find small QRs
		for scale in (1.0, 0.5, 0.25, 2.0):
			w, h = img.size
			candidate = img.resize(
				(int(w * scale), int(h * scale)), Image.LANCZOS
			) if scale != 1.0 else img

			# Sharpen slightly to help with printed QR codes
			candidate = candidate.filter(ImageFilter.SHARPEN)

			results = zbar_decode(candidate)
			for r in results:
				data = r.data.decode("utf-8", errors="ignore").strip()
				if data:
					return data

	except ImportError:
		frappe.log_error("pyzbar/Pillow not installed", "QR Decode Import Error")
	except Exception as e:
		frappe.log_error(str(e), "QR Decode Error")
	return None


def find_trip_from_qr(image_bytes: bytes) -> str | None:
	"""Decode QR and look up matching Trip name in DB."""
	raw = decode_qr_from_bytes(image_bytes)
	if not raw:
		frappe.log_error("QR decoded nothing", "QR Trip Lookup")
		return None

	frappe.log_error(f"QR decoded: {raw!r}", "QR Trip Lookup")

	if frappe.db.exists("Trip", raw):
		return raw

	result = frappe.db.get_value("Trip", {"tcntrip_no": raw}, "name")
	frappe.log_error(f"QR={raw!r} → tcntrip_no match={result!r}", "QR Trip Lookup")
	return result or None


def extract_trip_fields_from_pdf(pdf_bytes: bytes) -> dict:
	"""OCR a TCN Summary Sheet PDF and extract Trip fields."""
	try:
		pages = _pdf_to_images(pdf_bytes)
	except Exception as e:
		frappe.log_error(str(e), "PDF to Image Failed")
		return {}

	all_text = ""
	for img_bytes in pages:
		text = _ocr_image(img_bytes)
		if text:
			all_text += "\n" + text

	if not all_text.strip():
		return {}

	fields = _parse_tcn_text(all_text)
	if fields.get("tcntrip_no") or fields.get("customer"):
		return fields
	return {}


# def _pdf_to_images(pdf_bytes: bytes) -> list[bytes]:
# 	"""Convert PDF pages to JPEG bytes at high DPI for printed text."""
# 	try:
# 		from pdf2image import convert_from_bytes
# 		images = convert_from_bytes(pdf_bytes, dpi=300, fmt="jpeg")
# 		result = []
# 		for img in images:
# 			buf = io.BytesIO()
# 			img.save(buf, format="JPEG")
# 			result.append(buf.getvalue())
# 		return result
# 	except ImportError:
# 		frappe.log_error("pdf2image not installed", "PDF OCR Import Error")
# 		return []

def _pdf_to_images(pdf_bytes: bytes) -> list[bytes]:
	"""Convert only first 2 pages (LR + TCN Summary Sheet)."""
	try:
		from pdf2image import convert_from_bytes
		images = convert_from_bytes(
			pdf_bytes, dpi=300, fmt="jpeg",
			first_page=1, last_page=2,   # ← sirf pehle 2 pages
		)
		result = []
		for img in images:
			buf = io.BytesIO()
			img.save(buf, format="JPEG")
			result.append(buf.getvalue())
		return result
	except ImportError:
		frappe.log_error("pdf2image not installed", "PDF OCR Import Error")
		return []

def _ocr_image(image_bytes: bytes) -> str:
	"""Run plain OCR — best for printed documents."""
	try:
		import pytesseract
		from PIL import Image
		img = Image.open(io.BytesIO(image_bytes))
		return pytesseract.image_to_string(img, lang="eng")
	except ImportError as e:
		frappe.log_error(f"Import error: {str(e)}", "OCR Import Error")
		return ""
	except Exception as e:
		frappe.log_error(str(e), "OCR Error")
		return ""


def _parse_tcn_text(text: str) -> dict:
	"""Parse TCN Summary Sheet OCR text."""
	def find(pattern, flags=re.IGNORECASE):
		m = re.search(pattern, text, flags)
		return m.group(1).strip() if m else ""

	# TCN: "Summary Sheet No: RC90209418"
	tcn_no = find(r"Summary Sheet No\s*[:]?\s*([A-Z]{1,3}\s?[0-9]{6,})")
	if not tcn_no:
		tcn_no = find(r"TCN\s*[:]?\s*([A-Z]{1,3}\s?[0-9]{6,})")
	tcn_no = tcn_no.replace(" ", "")

	# Date: "Date:02.03.2026"
	date_raw = find(r"Date\s*[:]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})")
	trip_date = _normalise_date(date_raw)

	# Truck Type
	vehicle = find(r"Truck Type\s*[:]?\s*([A-Z0-9][A-Z0-9\s]+?)(?:\n|Truck Number|Truck Numbor|$)")

	# Origin
	origin = find(r"(?:Confirmation Location|Loading)\s*[:]?\s*\S*[/]?([A-Za-z]+)")

	# Customer
	customer = find(r"Billed To\s+([A-Z][A-Za-z\s]+?(?:Limited|Ltd|LIMITED))")
	if not customer:
		customer = find(r"(?:For|Consignee)[^A-Z]*([A-Z][A-Za-z\s]+?(?:Limited|Ltd|Retell|Retail))")

	# Vendor: "Operator 'SADASHIV LOGISTICS PRIVATE LIMITED"
	vendor = find(r"(?:Truck Operator|Operator|Transporter Name)\s*[:'\s]*([A-Z][A-Za-z\s]+?(?:LIMITED|Limited|LIM|Ltd))")

	# LR No
	lr_no = find(r"L\.?\s*R\.?\s*No\.?\s*[:]?\s*([0-9]{4,})")

	# Packages
	packages = find(r"(?:Disp\s*Qty|Packages?|Pkgs?)\s*[:\(A-Za-z\)]*\s*([0-9]{2,5})")

	return {
		"tcntrip_no": tcn_no,
		"tcntrip_date": trip_date,
		"vehicle_type": vehicle.strip(),
		"origin_city": origin.strip().title(),
		"destination_city_1": "",
		"customer": customer.strip(),
		"vendor": vendor.strip(),
		"lr_no": lr_no,
		"packages": packages,
	}


def _normalise_date(raw: str) -> str:
	"""Convert date formats to YYYY-MM-DD."""
	if not raw:
		return ""
	from datetime import datetime
	for fmt in ("%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d.%m.%Y"):
		try:
			return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
		except ValueError:
			pass
	return raw


def find_trip_from_pdf_qr(pdf_bytes: bytes) -> str | None:
	"""Render PDF pages and scan for a QR encoding the Trip name."""
	try:
		pages = _pdf_to_images(pdf_bytes)
	except Exception as e:
		frappe.log_error(str(e), "PDF QR: render failed")
		return None
	for img_bytes in pages:
		trip = find_trip_from_qr(img_bytes)
		if trip:
			return trip
	return None