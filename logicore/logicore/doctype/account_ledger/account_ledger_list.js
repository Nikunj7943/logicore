frappe.listview_settings["Account Ledger"] = Object.assign(
	frappe.listview_settings["Account Ledger"] || {},
	{
		onload(listview) {
			TMS.genericExport.attach(listview);
			TMS.dateFilterBar.attach(listview, { doctype: "Account Ledger", fieldname: "posting_date", label: "Posting Date" });
			// Rows only ever come from a linked transaction being submitted/saved
			// (account_ledger.py's before_insert blocks any manual create, even for
			// roles that hold create=1 for other reasons) — so the "+ Add Account
			// Ledger" button would just be a dead end. Hide it outright rather than
			// let anyone click into a form that can only ever throw on save.
			listview.page.clear_primary_action();
			// docfield.link_filters (see account_ledger.json's "account" field)
			// only applies inside a document form — the standard filter widget
			// here builds its Link query from scratch (base_list.js) and drops
			// link_filters entirely, so it has no effect on this row. Attaching
			// get_query directly to the rendered filter control is the actual way
			// to restrict it — only BANK/CASH Account Heads ever get ledger entries.
			if (listview.page.fields_dict.account) {
				listview.page.fields_dict.account.get_query = () => {
					return { filters: { group: ["in", ["BANK", "CASH"]] } };
				};
			}
			TMS.enforceDefaultSort(listview, { fieldname: "ledger_sort_key", order: "desc" });
		},
		refresh(listview) {
			TMS.dateFilterBar.refresh(listview, { doctype: "Account Ledger", fieldname: "posting_date" });
			listview.page.clear_primary_action();
			TMS.enforceDefaultSort(listview, { fieldname: "ledger_sort_key", order: "desc" });
		},
	}
);
