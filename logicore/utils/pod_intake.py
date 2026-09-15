"""
utils/pod_intake.py
POD upload pipeline:
  1. Receive list of raw image bytes (from Telegram)
  2. Compress each with Ghostscript  ← reuse existing V2 pattern
  3. Merge all into a single PDF
  4. Attach to the Trip doctype
  5. Update pod_status → "POD Uploaded"

Requires on server: ghostscript (gs), img2pdf  (pip install img2pdf)
"""

import os
import subprocess
import tempfile
import json

import frappe

# Error message shown when a POD upload is attempted before the unloading-site
# Arrival/Release date-times are filled. The exact phrase "Arrival Date/Time" is
# relied upon by the Telegram handlers to show a friendly retry prompt.
POD_DATES_REQUIRED_MSG = (
    "POD cannot be uploaded until Arrival Date/Time and Release "
    "Date/Time at the Unloading Site have been filled in the Trip."
)


def validate_pod_upload_allowed(trip_name: str) -> str | None:
    """Return an error message if POD upload is blocked, else None.

    POD upload requires the unloading-site Arrival and Release date-times to be
    filled on the Trip. Shared by every POD intake path (photos, single PDF,
    and the image-collection flow) so the rule stays consistent.
    """
    arrival, release = frappe.db.get_value(
        "Trip", trip_name, ["arrival_date_time", "release_date_time"]
    )
    if not arrival or not release:
        return POD_DATES_REQUIRED_MSG
    return None


def log_pod_replacement(trip_name: str, new_file_name: str) -> None:
    """Add a Trip timeline comment recording which old POD(s) were replaced.

    The old POD files stay attached to the Trip (for history), this just makes
    the replacement visible in the Activity feed.
    """
    old_files = frappe.db.get_all(
        "File",
        filters={
            "attached_to_doctype": "Trip",
            "attached_to_name": trip_name,
            "file_name": ["like", "POD_%.pdf"],
        },
        fields=["file_name"],
        order_by="creation desc",
    )
    old_names = [f.file_name for f in old_files if f.file_name != new_file_name]
    if not old_names:
        return

    frappe.get_doc("Trip", trip_name).add_comment(
        "Info",
        f"🔄 POD replaced — old POD kept as attachment: <b>{old_names[0]}</b>, "
        f"new POD: <b>{new_file_name}</b>",
    )


# ─── entry point ─────────────────────────────────────────────────────────────

def process_pod(trip_name: str, image_bytes_list: list[bytes],
                uploader_user: str = "Administrator") -> dict:
    """
    Main entry point called by the Telegram bot handler.

    Args:
        trip_name       : e.g. "SLPL-P-052600286"
        image_bytes_list: list of raw JPEG/PNG bytes, 1 per photo
        uploader_user   : frappe user email to credit the file to

    Returns:
        {"success": True, "file_url": "/files/...", "file_name": "..."}
        {"success": False, "error": "..."}
    """
    if not image_bytes_list:
        return {"success": False, "error": "No images received"}

    # Verify Trip exists
    if not frappe.db.exists("Trip", trip_name):
        return {"success": False, "error": f"Trip {trip_name} not found"}

    # POD requires unloading-site Arrival/Release date-times (same rule everywhere)
    block = validate_pod_upload_allowed(trip_name)
    if block:
        return {"success": False, "error": block}

    tmp_dir = tempfile.mkdtemp(prefix="tms_pod_")
    try:
        # ── Step 1: save raw images to tmp ──────────────────────────────────
        input_paths = []
        for idx, img_bytes in enumerate(image_bytes_list):
            ext = _detect_ext(img_bytes)
            path = os.path.join(tmp_dir, f"pod_{idx:03d}.{ext}")
            with open(path, "wb") as f:
                f.write(img_bytes)
            input_paths.append(path)

        # ── Step 2: compress each image ─────────────────────────────────────
        compressed_paths = [_compress_image(p, tmp_dir) for p in input_paths]

        # ── Step 3: merge to single PDF ──────────────────────────────────────
        pdf_filename = f"POD_{trip_name}_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(tmp_dir, pdf_filename)
        _merge_to_pdf(compressed_paths, pdf_path)

        # ── Step 4: attach to Trip in Frappe ────────────────────────────────
        file_url = _attach_file(
            trip_name=trip_name,
            pdf_path=pdf_path,
            pdf_filename=pdf_filename,
            uploader_user=uploader_user,
        )

        # ── Step 5: update Trip pod_status ───────────────────────────────────
        frappe.db.set_value("Trip", trip_name, {
            "pod_status": "Original POD Uploaded",
            "uploaded_pod_originalduplicate": "Original",
        })
        frappe.db.commit()

        return {"success": True, "file_url": file_url, "file_name": pdf_filename}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "POD Intake Error")
        return {"success": False, "error": str(e)}

    finally:
        # cleanup tmp files
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ─── image compression via Ghostscript ──────────────────────────────────────

def _compress_image(input_path: str, tmp_dir: str) -> str:
    """
    Convert image → compressed single-page PDF using Ghostscript.
    Output DPI: 150 (good quality, small file — same as V2 logic).
    """
    out_path = input_path.replace(os.path.splitext(input_path)[1], "_comp.pdf")

    # For images, use img2pdf first to make a lossless PDF, then GS compresses
    raw_pdf = input_path + "_raw.pdf"
    try:
        import img2pdf
        with open(raw_pdf, "wb") as f:
            f.write(img2pdf.convert(input_path))
    except Exception:
        # fallback: use Ghostscript directly on the image
        raw_pdf = input_path

    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/ebook",      # ~150 DPI, balanced quality
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={out_path}",
        raw_pdf,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    if result.returncode != 0:
        frappe.log_error(result.stderr.decode(), "GS Compress Error")
        return input_path  # fallback: use original

    return out_path


# ─── merge PDFs via Ghostscript ──────────────────────────────────────────────

def _merge_to_pdf(pdf_paths: list[str], output_path: str) -> None:
    """Merge list of PDFs into one using Ghostscript."""
    if len(pdf_paths) == 1:
        # Single file — just copy
        import shutil
        shutil.copy2(pdf_paths[0], output_path)
        return

    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/ebook",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
    ] + pdf_paths

    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"GS merge failed: {result.stderr.decode()}")


# ─── attach file to Trip ─────────────────────────────────────────────────────

def _attach_file(trip_name: str, pdf_path: str, pdf_filename: str,
                 uploader_user: str) -> str:
    """Save PDF to Frappe private files and attach to Trip."""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    frappe.set_user(uploader_user)

    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": pdf_filename,
        "attached_to_doctype": "Trip",
        "attached_to_name": trip_name,
        "is_private": 0,
        "content": pdf_bytes,
    })
    file_doc.save(ignore_permissions=True)
    return file_doc.file_url


# ─── utility ────────────────────────────────────────────────────────────────

def _detect_ext(data: bytes) -> str:
    """Detect image extension from magic bytes."""
    if data[:4] == b"\x89PNG":
        return "png"
    if data[:2] in (b"\xff\xd8",):
        return "jpg"
    if data[:4] in (b"%PDF",):
        return "pdf"
    return "jpg"  # default
