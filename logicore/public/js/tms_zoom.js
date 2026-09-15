(function () {
    const STORAGE_KEY = "tms_zoom_level";
    const MIN = 0.5, MAX = 2.0, STEP = 0.1;

    function applyZoom(level) {
        // Apply to <html> so position:fixed elements are unaffected
        document.documentElement.style.zoom = level;
        localStorage.setItem(STORAGE_KEY, level);
        var label = document.getElementById("tms-zoom-label");
        if (label) label.textContent = Math.round(level * 100) + "%";
        // REVERTED per user request, along with tms_list_page_length.js
        // (which this resize event was feeding). Re-enable together.
        // window.dispatchEvent(new Event("resize"));
    }

    function getZoom() {
        return parseFloat(localStorage.getItem(STORAGE_KEY)) || 1.0;
    }

    function showHint() {
        if (document.getElementById("tms-zoom-hint")) return;

        var hint = document.createElement("div");
        hint.id = "tms-zoom-hint";
        hint.innerHTML =
            '\uD83D\uDD0D <b>Zoom:</b> <kbd>Ctrl +</kbd> In &nbsp;|\u00a0<kbd>Ctrl \u2212</kbd> Out &nbsp;|\u00a0<kbd>Ctrl 0</kbd> Reset' +
            '\u00a0\u00a0<span id="tms-zoom-label" style="font-weight:700;color:#1570ef;">' +
            Math.round(getZoom() * 100) + "%</span>";

        hint.style.cssText = [
            "position:fixed", "bottom:14px", "right:16px", "z-index:99999",
            "background:#f8f9fb", "border:1px solid #d0d5dd", "border-radius:6px",
            "padding:4px 12px", "font-size:11px", "color:#475467",
            "box-shadow:0 2px 8px rgba(0,0,0,0.10)", "white-space:nowrap",
            "pointer-events:none", "line-height:1.8"
        ].join(";");

        hint.querySelectorAll("kbd").forEach(function (k) {
            k.style.cssText = "background:#eaecf0;border:1px solid #c4c9d4;border-radius:3px;padding:0 5px;font-size:10px;font-family:monospace";
        });

        document.body.appendChild(hint);
    }

    applyZoom(getZoom());

    document.addEventListener("keydown", function (e) {
        if (!e.ctrlKey) return;
        var key = e.key;
        if (key === "+" || key === "=") {
            e.preventDefault();
            applyZoom(Math.min(MAX, Math.round((getZoom() + STEP) * 10) / 10));
        } else if (key === "-") {
            e.preventDefault();
            applyZoom(Math.max(MIN, Math.round((getZoom() - STEP) * 10) / 10));
        } else if (key === "0") {
            e.preventDefault();
            applyZoom(1.0);
        }
    });

    // Frappe SPA: re-attach hint after every route change
    $(document).on("page-change", showHint);

    frappe.ready(showHint);
})();
