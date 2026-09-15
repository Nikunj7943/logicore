"""
utils/telegram_api.py
Thin wrapper around Telegram Bot API — raw requests only.
No aiogram/python-telegram-bot dependency → zero py3.14 compat risk.
"""

import requests
import frappe

# ─── helpers ────────────────────────────────────────────────────────────────

def _is_enabled() -> bool:
    return bool(frappe.db.get_single_value("Telegram Bot Settings", "is_enabled"))


def _token() -> str | None:
    """Return the bot token, or None if the bot is disabled."""
    if not _is_enabled():
        return None
    token = frappe.conf.get("telegram_bot_token")
    if not token:
        frappe.throw("telegram_bot_token not set in site_config.json")
    return token


def _post(method: str, payload: dict) -> dict:
    token = _token()
    if not token:
        return {"ok": False, "skipped": "Telegram bot is disabled"}
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload, timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        frappe.log_error(str(e), "Telegram API Error")
        return {"ok": False, "error": str(e)}


# ─── send messages ──────────────────────────────────────────────────────────

def send_message(chat_id, text: str, parse_mode: str = "HTML",
                 reply_markup: dict = None) -> dict:
    """Send plain or HTML-formatted text message."""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _post("sendMessage", payload)


def send_photo(chat_id, photo_url: str, caption: str = None) -> dict:
    payload = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        payload["caption"] = caption
    return _post("sendPhoto", payload)


def send_document(chat_id, document_url: str, caption: str = None) -> dict:
    payload = {"chat_id": chat_id, "document": document_url}
    if caption:
        payload["caption"] = caption
    return _post("sendDocument", payload)


def send_typing(chat_id) -> dict:
    """Show 'typing...' indicator."""
    return _post("sendChatAction", {"chat_id": chat_id, "action": "typing"})


def send_uploading(chat_id) -> dict:
    """Show 'uploading document...' indicator."""
    return _post("sendChatAction", {"chat_id": chat_id, "action": "upload_document"})


# ─── inline keyboard builder ────────────────────────────────────────────────

def inline_keyboard(buttons: list[list[tuple[str, str]]]) -> dict:
    """
    Build inline_keyboard reply_markup.
    buttons = [[("Label", "callback_data"), ...], ...]  ← rows of buttons
    Example:
        inline_keyboard([
            [("✅ Confirm", "confirm_pod_TRIP001"), ("❌ Cancel", "cancel")],
        ])
    """
    return {
        "inline_keyboard": [
            [{"text": label, "callback_data": data} for label, data in row]
            for row in buttons
        ]
    }


# ─── file download ──────────────────────────────────────────────────────────

def get_file_path(file_id: str) -> str | None:
    """Resolve a Telegram file_id to a download URL."""
    token = _token()
    if not token:
        return None
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/getFile",
        json={"file_id": file_id}, timeout=10,
    )
    if resp.ok:
        data = resp.json()
        if data.get("ok"):
            fp = data["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{token}/{fp}"
    frappe.log_error(f"getFile failed for {file_id}", "Telegram getFile")
    return None


def download_file(file_id: str) -> bytes | None:
    """Download a Telegram file and return raw bytes."""
    url = get_file_path(file_id)
    if not url:
        return None
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        frappe.log_error(str(e), "Telegram Download Error")
        return None


# ─── answer callback queries ────────────────────────────────────────────────

def answer_callback(callback_query_id: str, text: str = None,
                    show_alert: bool = False) -> dict:
    """Dismiss the spinner on inline button press."""
    payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
    if text:
        payload["text"] = text
    return _post("answerCallbackQuery", payload)


# ─── edit message (update confirm card after action) ────────────────────────

def edit_message_text(chat_id, message_id: int, text: str,
                      reply_markup: dict = None) -> dict:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _post("editMessageText", payload)
