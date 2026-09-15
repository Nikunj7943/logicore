import frappe
import frappe.core.api.file as file_api

_original_get_max_file_size = file_api.get_max_file_size

# Both the upload dialog (client) and File.check_max_file_size (server) reject
# with a strict "<" comparison, so a file that is exactly at the configured MB
# boundary (e.g. "4.00 MB" as shown by the OS, which rounds the byte count)
# gets rejected even though it should be allowed. A real-world "4.00 MB" file
# measured at 4,200,000 bytes (5,696 bytes over the raw 4 MiB boundary) was
# still being rejected, while a "4.05 MB" file starts around 4,246,733 bytes —
# 32 KB of slack sits comfortably between the two, absorbing the display
# rounding without letting a meaningfully larger file through.
_TOLERANCE_BYTES = 32 * 1024


@frappe.whitelist()
def get_max_file_size_with_tolerance():
	return _original_get_max_file_size() + _TOLERANCE_BYTES
