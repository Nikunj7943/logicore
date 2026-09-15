# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

import frappe
from frappe.core.doctype.access_log.access_log import make_access_log
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def report_to_pdf(html, orientation="Landscape"):
	"""Override for frappe.utils.print_format.report_to_pdf — identical except
	it drops the core function's hard-coded proxy options ("proxy":
	"http://0.0.0.0:0", "bypass-proxy-for": ...), which are meant to disable
	proxying for wkhtmltopdf but instead make it treat 0.0.0.0:0 as a real
	proxy on this environment, failing every PDF export with "network error:
	ConnectionRefusedError". wkhtmltopdf works fine without them here."""
	make_access_log(file_type="PDF", method="PDF", page=html)
	frappe.local.response.filename = "report.pdf"
	frappe.local.response.filecontent = get_pdf(html, {"orientation": orientation, "load-error-handling": "ignore"})
	frappe.local.response.type = "pdf"
