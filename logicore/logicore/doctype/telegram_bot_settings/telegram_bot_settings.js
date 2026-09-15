// Copyright (c) 2026, LogiCore and contributors
// For license information, please see license.txt

frappe.ui.form.on("Telegram Bot Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Sync Webhook Now"), () => {
			frm.save();
		});

		if (frm.doc.webhook_status) {
			const indicator = frm.doc.webhook_status.startsWith("✅") ? "green" : "red";
			frm.dashboard.set_headline_alert(
				`<div class="indicator-pill ${indicator}">${frappe.utils.escape_html(frm.doc.webhook_status)}</div>`
			);
		}

		// Helpful hint: show whether a local ngrok tunnel is detected.
		// On a real server ngrok won't be running and the site URL is used instead —
		// so this is purely informational, no action needed there.
		frappe.call({
			method: "logicore.logicore.doctype.telegram_bot_settings.telegram_bot_settings.get_ngrok_status",
			callback(r) {
				if (r.message && r.message.running) {
					frm.set_intro(__("ngrok tunnel detected: {0} — this will be used as the webhook URL.", [r.message.url]), "green");
				}
			},
		});
	},
});
