# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import secrets

import frappe
import requests
from frappe.installer import update_site_config
from frappe.model.document import Document

NGROK_API = "http://127.0.0.1:4040/api/tunnels"
TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
WEBHOOK_PATH = "/api/method/logicore.api.telegram_webhook"


class TelegramBotSettings(Document):
	def validate(self):
		if not self.is_enabled:
			self._disable_bot()
			return

		token = self.get_password("telegram_bot_token", raise_exception=False)
		if not token:
			self.webhook_status = ""
			return

		if not self.telegram_webhook_secret:
			self.telegram_webhook_secret = secrets.token_urlsafe(32)

		update_site_config("telegram_bot_token", token)
		update_site_config("telegram_webhook_secret", self.telegram_webhook_secret)

		me = self._call_telegram(token, "getMe")
		if not me or not me.get("ok"):
			self.webhook_status = f"❌ Invalid bot token: {(me or {}).get('description', 'no response')}"
			return
		self.bot_username = me["result"]["username"]

		base_url, source = self._resolve_base_url()
		if not base_url.startswith("https://"):
			self.webhook_status = (
				f"⚠️ No public HTTPS URL found (detected: {base_url or 'none'} via {source}).\n"
				"Local: start ngrok (e.g. `ngrok http 8001`) and save again.\n"
				"Server: ensure the site is on HTTPS, or set the Override field below."
			)
			return

		webhook_url = base_url.rstrip("/") + WEBHOOK_PATH
		resp = self._call_telegram(
			token,
			"setWebhook",
			{
				"url": webhook_url,
				"secret_token": self.telegram_webhook_secret,
				"allowed_updates": ["message", "callback_query"],
				"drop_pending_updates": False,
			},
		)

		self.webhook_url = webhook_url
		self.last_synced_on = frappe.utils.now_datetime()
		if resp and resp.get("ok"):
			self.webhook_status = f"✅ {resp.get('description', 'Webhook registered')} (via {source})"
		else:
			self.webhook_status = f"❌ {(resp or {}).get('description', 'setWebhook failed')}"

	def _disable_bot(self) -> None:
		"""Remove webhook from Telegram and clear status when bot is disabled."""
		token = frappe.conf.get("telegram_bot_token")
		if token:
			self._call_telegram(token, "deleteWebhook", {"drop_pending_updates": False})
		self.webhook_status = "🔴 Bot disabled — messages are silently dropped"
		self.webhook_url = ""

	def _resolve_base_url(self) -> tuple[str, str]:
		"""Auto-pick the public URL: manual override → ngrok tunnel → this site's URL."""
		if self.base_url_override:
			return self.base_url_override.strip().rstrip("/"), "override"

		ngrok = _detect_ngrok()
		if ngrok:
			return ngrok, "ngrok"

		return (frappe.utils.get_url() or "").rstrip("/"), "site URL"

	@staticmethod
	def _call_telegram(token: str, method: str, payload: dict | None = None) -> dict | None:
		try:
			url = TELEGRAM_API.format(token=token, method=method)
			if payload is None:
				r = requests.get(url, timeout=15)
			else:
				r = requests.post(url, json=payload, timeout=15)
			return r.json()
		except Exception as e:
			frappe.log_error(str(e), "Telegram Bot Settings")
			return None


def _detect_ngrok() -> str | None:
	"""Return the active ngrok HTTPS tunnel URL, or None if ngrok isn't running."""
	try:
		tunnels = requests.get(NGROK_API, timeout=3).json().get("tunnels", [])
	except Exception:
		return None
	for t in tunnels:
		url = t.get("public_url", "")
		if url.startswith("https://"):
			return url
	return None


@frappe.whitelist()
def get_ngrok_status() -> dict:
	"""Used by the form JS to show the live ngrok tunnel URL (or its absence)."""
	url = _detect_ngrok()
	return {"running": bool(url), "url": url}
