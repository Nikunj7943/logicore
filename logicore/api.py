"""
api.py

Telegram webhook endpoint:
  POST /api/method/logicore.api.telegram_webhook
  Header: X-Telegram-Bot-Api-Secret-Token: <secret>

Webhook registration is handled automatically by the "Telegram Bot Settings"
doctype — enter the bot token there and save.
"""

import json
import frappe


# ─── System dependency check (POD QR / OCR / PDF compression) ────────────────

@frappe.whitelist()
def check_system_dependencies():
    """Report whether the POD/OCR system packages are installed on THIS server.

    Works without terminal/SSH or developer mode — open in a browser while
    logged in to Desk as System Manager:

      https://<your-site>/api/method/logicore.api.check_system_dependencies

    Returns each package, the binary/library it provides, and whether it's found.
    `all_ok` is True only when every dependency is present.
    """
    if "System Manager" not in frappe.get_roles():
        frappe.throw("Not permitted", frappe.PermissionError)

    import shutil
    import ctypes.util

    checks = {
        "ghostscript":   bool(shutil.which("gs")),         # PDF compression
        "poppler-utils": bool(shutil.which("pdftoppm")),   # pdf2image (QR/OCR render)
        "tesseract-ocr": bool(shutil.which("tesseract")),  # pytesseract OCR
        "libzbar0":      bool(ctypes.util.find_library("zbar")),  # pyzbar QR decode
    }

    py_modules = {}
    for mod in ("img2pdf", "pyzbar", "pdf2image", "pytesseract"):
        try:
            __import__(mod)
            py_modules[mod] = True
        except Exception:
            py_modules[mod] = False

    return {
        "all_ok": all(checks.values()) and all(py_modules.values()),
        "apt_packages": checks,
        "python_modules": py_modules,
        "missing_apt": [name for name, ok in checks.items() if not ok],
        "missing_python": [name for name, ok in py_modules.items() if not ok],
    }


# ─── Webhook receiver ────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def telegram_webhook():
    """
    Telegram calls this endpoint for every update.
    Must return HTTP 200 quickly — heavy work is always enqueued.

    Security: validates X-Telegram-Bot-Api-Secret-Token header.
    Set telegram_webhook_secret in site_config.json.
    """
    # ── secret token validation ──────────────────────────────────────────────
    expected_secret = frappe.conf.get("telegram_webhook_secret")
    if expected_secret:
        incoming = frappe.request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if incoming != expected_secret:
            frappe.local.response.http_status_code = 403
            return {"error": "Forbidden"}

    # ── parse body ───────────────────────────────────────────────────────────
    try:
        body = frappe.request.get_data(as_text=True)
        update = json.loads(body)
    except Exception:
        frappe.local.response.http_status_code = 400
        return {"error": "Bad Request"}

    # ── route update ─────────────────────────────────────────────────────────
    try:
        from logicore.utils.telegram_bot import handle_update
        handle_update(update)
    except Exception:
        # Never let an exception cause a non-200 — Telegram would retry indefinitely
        frappe.log_error(frappe.get_traceback(), "Telegram Webhook Handler Error")

    # Telegram requires exactly this response
    frappe.local.response.http_status_code = 200
    return {"ok": True}
