"""
utils/qr_utils.py
Generate a QR code image (base64-encoded PNG) for embedding in print formats.

Usage in Jinja print format:
  {% set qr_b64 = frappe.call("logicore.utils.qr_utils.trip_qr_base64", trip_name=doc.name) %}
  <img src="data:image/png;base64,{{ qr_b64 }}" width="120" height="120" />

Requires: pip install qrcode[pil] --break-system-packages
"""

import io
import base64
import frappe


def trip_qr_base64(trip_name: str, box_size: int = 6, border: int = 2) -> str:
    """
    Generate a QR code encoding the Trip name.
    Returns base64-encoded PNG string suitable for <img src="data:..."> in Jinja.
    """
    try:
        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(
            version=None,          # auto-size
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(trip_name)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    except ImportError:
        frappe.log_error("qrcode or Pillow not installed", "QR Utils Import Error")
        return ""
    except Exception as e:
        frappe.log_error(str(e), "QR Generation Error")
        return ""


@frappe.whitelist()
def trip_qr_base64_api(trip_name: str) -> str:
    """Whitelisted version callable from Jinja via frappe.call."""
    if not frappe.db.exists("Trip", trip_name):
        frappe.throw(f"Trip {trip_name} not found")
    return trip_qr_base64(trip_name)
