// Runs on EVERY doctype form (frappe.ui.form.on("*", ...) is a Frappe-supported
// wildcard registration -- script_manager.js triggers both a doctype's own handlers
// AND "*" handlers for every event, so this runs alongside any doctype-specific
// validate() without needing to be wired into each one individually).
//
// A mandatory field that is Hidden for the current user's TMS User Group (via
// field-level permlevel) can never be filled in by them -- Frappe's own native
// "This field is required" mandatory check would still fire, but it's useless here
// since the field itself isn't visible, leaving the user stuck with no clue why Save
// is failing or what to do about it. Catch this case FIRST, before native validation
// runs, with a clear message naming the field(s) and pointing them at their TMS Admin.
//
// This is doctype-agnostic by construction: a field only trips this check if it has
// a non-zero permlevel AND the current user's role lacks read access at that
// permlevel -- both are only ever true for a field a TMS Admin has actually marked
// Hidden via TMS User Group's field-permission popup. A brand-new doctype added to
// the TMS-managed set later needs no changes here; it's covered automatically the
// moment its fields get permlevel-restricted.
function _tms_field_permission_guard_readable(frm, fieldname) {
	const df = frm.fields_dict[fieldname] && frm.fields_dict[fieldname].df;
	const permlevel = (df && df.permlevel) || 0;
	if (!permlevel) return true;
	return !!(frm.perm && frm.perm[permlevel] && frm.perm[permlevel].read);
}

// A field that is Hidden via TMS User Group has its VALUE stripped from frm.doc
// entirely for this user (that's the whole point -- Hidden must mean the data isn't
// even present client-side, not just CSS-hidden). But a DIFFERENT field's
// `depends_on` expression (e.g. Fuel Urea Expenses' "Bank Account No"/"Reference No",
// both `depends_on: doc.payment_mode in [...]`) evaluates against that now-missing
// value and comes out false, so Frappe's own layout.refresh_dependency() hides those
// OTHER fields too -- a field the TMS Admin never touched disappears as a side effect
// of hiding an unrelated one.
//
// Only the field explicitly marked Hidden should ever disappear. So: for any field
// whose depends_on expression textually references a field this user's group cannot
// read, and which is not itself Hidden, force it back to visible -- we can't
// re-evaluate depends_on honestly (we're not allowed to know the hidden field's real
// value), so treat "the condition depends on a fact this viewer isn't allowed to
// know" as "don't hide it on that basis."
function _tms_reveal_dependents_of_hidden_fields(frm) {
	if (!frm.layout || !frm.layout.fields_list) return;

	const hiddenFieldnames = (frm.meta.fields || [])
		.filter(df => df.fieldname && (df.permlevel || 0) > 0)
		.filter(df => !_tms_field_permission_guard_readable(frm, df.fieldname))
		.map(df => df.fieldname);
	if (!hiddenFieldnames.length) return;

	const escaped = hiddenFieldnames.map(fn => fn.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
	const pattern = new RegExp("\\b(" + escaped.join("|") + ")\\b");
	const hiddenSet = new Set(hiddenFieldnames);

	frm.layout.fields_list.forEach(f => {
		const df = f.df;
		if (!df || !df.fieldname || !df.depends_on || typeof df.depends_on !== "string") return;
		if (hiddenSet.has(df.fieldname)) return; // this field is itself Hidden -- leave it alone
		if (df.hidden_due_to_dependency && pattern.test(df.depends_on)) {
			df.hidden_due_to_dependency = false;
			f.refresh();
		}
	});
}

// layout.refresh_dependency() is Frappe's single central place for depends_on
// evaluation (runs on load, on every relevant field change, on tab switch) --
// wrapping it here (once per form instance) is far more reliable than trying to
// re-run our own check after every possible triggering event.
function _tms_install_dependency_guard(frm) {
	if (!frm.layout || frm.layout._tmsDependencyGuardInstalled) return;
	frm.layout._tmsDependencyGuardInstalled = true;
	const original = frm.layout.refresh_dependency.bind(frm.layout);
	frm.layout.refresh_dependency = function () {
		original();
		_tms_reveal_dependents_of_hidden_fields(frm);
	};
}

frappe.ui.form.on("*", {
	onload(frm) {
		_tms_install_dependency_guard(frm);
	},
	refresh(frm) {
		_tms_install_dependency_guard(frm);
		_tms_reveal_dependents_of_hidden_fields(frm);
	},
	validate(frm) {
		const hiddenMandatoryFields = (frm.meta.fields || [])
			.filter(df => df.fieldname && df.reqd)
			.filter(df => {
				const val = frm.doc[df.fieldname];
				return val === null || val === undefined || val === "";
			})
			.filter(df => !_tms_field_permission_guard_readable(frm, df.fieldname))
			.map(df => df.label || df.fieldname);

		if (hiddenMandatoryFields.length) {
			frappe.msgprint({
				title: __("Cannot Save — Required Field Hidden"),
				indicator: "red",
				message: __(
					"The following required field(s) are hidden for your user group by your TMS Admin, so they cannot be filled in: <b>{0}</b>. Please contact your TMS Admin to get access to these field(s), or ask them to fill this document in for you.",
					[hiddenMandatoryFields.join(", ")]
				),
			});
			frappe.validated = false;
		}
	},
});
