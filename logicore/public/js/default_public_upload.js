// LogiCore — Default file uploads to Public (is_private = 0)
// Forces make_attachments_public = 1 on every frappe.ui.FileUploader call so
// the per-file "Private" toggle defaults OFF in every upload dialog
// (form Attach fields, sidebar attachments, image fields, etc.).
// User can still tick "Private" manually to override.

(function () {
	frappe.provide("frappe.ui");

	function wrapUploader(Original) {
		if (!Original || Original.__tms_public_patched) return Original;

		function PatchedFileUploader(opts) {
			opts = opts || {};
			// Force public default. Form attach.js sets make_attachments_public from
			// DocType meta (often 0/falsy) — override so user uploads default public.
			opts.make_attachments_public = 1;
			opts.is_private = 0;
			// Keep allow_toggle_private = true (default) so the per-file "Private"
			// checkbox AND the "Set all private" footer button still render.
			// We disable both visually + functionally below.

			const instance = new Original(opts);

			// Mark the dialog so scoped CSS (tms_global.css) can grey-out the
			// Private checkbox and the secondary action button.
			if (instance && instance.dialog && instance.dialog.$wrapper) {
				instance.dialog.$wrapper.addClass("tms-private-disabled");
				// No-op the secondary action so even if a user bypasses CSS,
				// clicking "Set all private" does nothing.
				instance.dialog.secondary_action = function () {};
			}

			return instance;
		}

		PatchedFileUploader.prototype = Original.prototype;
		PatchedFileUploader.__tms_public_patched = true;
		return PatchedFileUploader;
	}

	// Patch whatever is currently assigned (in case bundle already loaded).
	let _stored = wrapUploader(frappe.ui.FileUploader);

	// Trap future assignment too — file_uploader.bundle.js does
	// `frappe.ui.FileUploader = FileUploader` when it loads (lazily via
	// frappe.require). Without this trap our wrapper would be overwritten.
	try {
		Object.defineProperty(frappe.ui, "FileUploader", {
			configurable: true,
			enumerable: true,
			get() {
				return _stored;
			},
			set(val) {
				_stored = wrapUploader(val);
			},
		});
	} catch (e) {
		console.error("[TMS] Failed to install FileUploader patch trap:", e);
	}
})();
