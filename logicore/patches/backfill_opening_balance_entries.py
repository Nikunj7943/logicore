import frappe


def execute():
    """One-time catch-up for existing sites, in two parts:

    1. Create the missing "Opening Balance" Account Ledger row for every
       BANK/CASH Account Head that already has an opening_balance set.
       sync_opening_balance_entry() only runs from Account Head's
       before_save/after_insert hooks (see doctype/account_head/
       account_head.py) — accounts whose opening_balance arrived via a
       direct DB import/restore rather than a real document save never got
       their entry created, so their balance silently excluded it.

    2. Recompute every account's Account Ledger rows as a true running
       (passbook-style) balance plus their ledger_sort_key — balance_amount
       used to just mirror the account's current total onto every row;
       refresh_current_balance() now computes each row's own cumulative
       balance and default-sort position instead. Existing rows still hold
       the old mirrored value/no sort key until this runs once.

    Going forward both stay correct automatically (Account Head's hooks
    create new Opening Balance rows; every submit/save/cancel already calls
    refresh_current_balance()), so this never needs to run again.
    """
    from logicore.utils.account_balance_utils import refresh_current_balance, sync_opening_balance_entry

    accounts_needing_opening_entry = frappe.db.sql(
        """
        SELECT name, opening_balance, opening_balance_date
        FROM `tabAccount Head`
        WHERE `group` IN ('BANK', 'CASH')
          AND opening_balance IS NOT NULL
          AND opening_balance != 0
        """,
        as_dict=True,
    )

    fixed = []
    for account in accounts_needing_opening_entry:
        has_entry = frappe.db.exists(
            "Account Ledger",
            {
                "reference_doctype": "Account Head",
                "reference_name": account.name,
                "remarks": "Opening Balance",
            },
        )
        if has_entry:
            continue
        sync_opening_balance_entry(account.name, account.opening_balance, account.opening_balance_date)
        fixed.append(account.name)

    all_accounts = frappe.db.sql("SELECT DISTINCT account FROM `tabAccount Ledger`", pluck=True)
    for account in all_accounts:
        refresh_current_balance(account)

    frappe.db.commit()
    if fixed:
        frappe.logger().info(f"[TMS] Backfilled Opening Balance entries for: {', '.join(fixed)}")
    frappe.logger().info(f"[TMS] Recomputed running balance for {len(all_accounts)} accounts")
