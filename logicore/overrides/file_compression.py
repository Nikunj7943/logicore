from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile

import frappe
from frappe import _
from frappe.core.doctype.file.exceptions import MaxFileSizeReachedError
from frappe.core.doctype.file.file import File
from frappe.utils import cstr


TARGET_DOCTYPES = {"Driver", "Employee", "Compliances"}
COMPRESSIBLE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
COMPRESSIBLE_EXTENSIONS = COMPRESSIBLE_IMAGE_EXTENSIONS | {".pdf"}

# Ghostscript downsample passes, tried in order until the file fits under the
# System Settings "Max File Size (MB)" limit. 80 DPI is the readability floor
# for scanned PODs/documents.
PDF_DPI_STEPS = [120, 100, 90, 80]

# Image passes: each scale is tried with each JPEG quality (largest/highest
# first) until the result fits under the limit. PNG has no quality knob, so
# only the scale steps apply to it.
IMAGE_SCALE_STEPS = [1.0, 0.75, 0.5, 0.35]
IMAGE_JPEG_QUALITY_STEPS = [80, 65, 50, 35]


class MasterAttachmentFile(File):
	"""Always compress Driver/Employee/Compliances PDF/JPG/PNG attachments
	towards System Settings "Max File Size (MB)", then let Frappe's own check
	run on the (now smaller) content.

	Both the compression and the size check must happen on the in-memory
	upload bytes inside `before_insert` (via `save_file` -> `check_max_file_size`),
	before the file is ever written to disk — an `after_insert` hook is always
	too late, since by then Frappe has either already rejected an oversized
	upload or already written the uncompressed bytes.
	"""

	def check_max_file_size(self):
		from frappe.core.api.file import get_max_file_size

		content = self._content or b""
		max_file_size = get_max_file_size()

		if cstr(getattr(self, "attached_to_doctype", "")).strip() in TARGET_DOCTYPES:
			ext = os.path.splitext(cstr(getattr(self, "file_name", "")).strip())[1].lower()
			if ext in COMPRESSIBLE_EXTENSIONS:
				compressed = _compress_content_to_target(content, ext, max_file_size)
				if compressed and len(compressed) < len(content):
					content = compressed
					self._content = content
					self.content = content

		file_size = len(content)
		if file_size > max_file_size:
			msg = _("File size exceeded the maximum allowed size of {0} MB").format(max_file_size / 1048576)
			if frappe.has_permission("System Settings", "write"):
				msg += ".<br>" + _("You can increase the limit from System Settings.")
			frappe.throw(msg, exc=MaxFileSizeReachedError)

		return file_size


def _compress_content_to_target(content: bytes, ext: str, max_bytes: int) -> bytes | None:
	try:
		if ext == ".pdf":
			return _compress_pdf_bytes(content, max_bytes)
		if ext in COMPRESSIBLE_IMAGE_EXTENSIONS:
			return _compress_image_bytes(content, ext, max_bytes)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Master attachment compression failed")
	return None


def _compress_pdf_bytes(content: bytes, max_bytes: int) -> bytes | None:
	gs_bin = shutil.which("gs") or "/usr/bin/gs"
	if not os.path.exists(gs_bin):
		frappe.log_error(f"Ghostscript not found at '{gs_bin}'", "Master Attachment Compression")
		return None

	tmp_dir = tempfile.mkdtemp(prefix="tms_master_pdf_")
	try:
		in_path = os.path.join(tmp_dir, "in.pdf")
		with open(in_path, "wb") as f:
			f.write(content)

		best_bytes, best_size = None, len(content)

		for dpi in PDF_DPI_STEPS:
			out_path = os.path.join(tmp_dir, f"p_{dpi}.pdf")
			cmd = [
				gs_bin, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
				"-dNOPAUSE", "-dQUIET", "-dBATCH",
				"-dDownsampleColorImages=true", f"-dColorImageResolution={dpi}",
				"-dDownsampleGrayImages=true", f"-dGrayImageResolution={dpi}",
				"-dDownsampleMonoImages=true", f"-dMonoImageResolution={dpi}",
				"-dAutoFilterColorImages=false", "-dColorImageFilter=/DCTEncode",
				"-dAutoFilterGrayImages=false", "-dGrayImageFilter=/DCTEncode",
				f"-sOutputFile={out_path}", in_path,
			]
			try:
				result = subprocess.run(cmd, capture_output=True, timeout=90)
			except subprocess.TimeoutExpired:
				continue

			if result.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) <= 0:
				continue

			size = os.path.getsize(out_path)
			if size < best_size:
				with open(out_path, "rb") as f:
					best_bytes = f.read()
				best_size = size
			if size <= max_bytes:
				break

		return best_bytes
	finally:
		shutil.rmtree(tmp_dir, ignore_errors=True)


def _compress_image_bytes(content: bytes, ext: str, max_bytes: int) -> bytes | None:
	try:
		from PIL import Image
	except Exception:
		frappe.log_error(
			"Pillow is not available, skipping image compression.",
			"Master Attachment Compression",
		)
		return None

	is_jpeg = ext in {".jpg", ".jpeg"}
	qualities = IMAGE_JPEG_QUALITY_STEPS if is_jpeg else [None]

	with Image.open(io.BytesIO(content)) as img:
		img.load()
		base_img = img.convert("RGB") if is_jpeg and img.mode not in {"RGB", "L"} else img.copy()

	best_bytes, best_size = None, len(content)

	for scale in IMAGE_SCALE_STEPS:
		work_img = base_img
		if scale != 1.0:
			new_size = (max(1, int(base_img.width * scale)), max(1, int(base_img.height * scale)))
			work_img = base_img.resize(new_size, Image.LANCZOS)

		for quality in qualities:
			buf = io.BytesIO()
			if is_jpeg:
				work_img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
			else:
				save_img = work_img
				if save_img.mode not in {"RGBA", "RGB", "P", "L"}:
					save_img = save_img.convert("RGBA")
				save_img.save(buf, format="PNG", optimize=True, compress_level=9)

			data = buf.getvalue()
			size = len(data)
			if size < best_size:
				best_size = size
				best_bytes = data
			if size <= max_bytes:
				break

		if best_size <= max_bytes:
			break

	return best_bytes
