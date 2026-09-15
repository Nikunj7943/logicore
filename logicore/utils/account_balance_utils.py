# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

from contextlib import contextmanager

import frappe
from frappe.utils import flt

# Doctypes wired (in hooks.py) to write Account Ledger rows on_submit /
# remove them on_cancel — a one-way state transition, so insert-once is safe.
# Kept here (not derived from TMS Reconciliation Source.requires_submitted)
# because that field controls a different concern — whether the bank
# reconciliation UI requires docstatus=1 to match a row (see
# utils/bank_reconciliation_utils.py) — which Tyre/Battery Expenses
# deliberately keep at 0 so Draft rows stay reconciliation-eligible, even
# though they now also get ledger entries on submit.
LEDGER_ON_SUBMIT_DOCTYPES = [
	"Vendor Payment", "Supplier Payment", "Receipt", "Payment",
	"Fuel Urea Expenses", "Staff Payroll", "Tyre Expenses", "Battery Expenses",
]

# Doctypes that are never submitted (always docstatus=0) — wired (in
# hooks.py) to on_update_upsert_ledger / on_trash instead, since there is no
# on_submit/on_cancel transition to hook. Each has exactly one TMS
# Reconciliation Source row (one leg), so upsert-by-reference is safe: no
# risk of two legs on the same document colliding on the same identity.
LEDGER_ON_SAVE_DOCTYPES = ["Repair Expenses", "Compliances", "Service Logs"]


@contextmanager
def _allow_ledger_entry_write():
	"""Lets this module's own housekeeping writes (inserting a leg for a
	submitted/saved source document, the opening-balance row being created,
	updated or cleared) through Account Ledger's before_insert/on_trash
	guards, which otherwise block every manual create or delete so a row can
	only ever come into or out of existence via its linked transaction being
	submitted/saved/cancelled/deleted — never typed or removed by hand,
	even by an admin role."""
	previous = getattr(frappe.flags, "tms_internal_ledger_write", False)
	frappe.flags.tms_internal_ledger_write = True
	try:
		yield
	finally:
		frappe.flags.tms_internal_ledger_write = previous


def _iter_account_legs(doctype: str, docname: str, sources=None, values=None):
	"""Yield (account, amount, direction, date) for every account this record
	moves money through, derived from the TMS Reconciliation Source rows
	already configured for `doctype` — so this stays in sync with the
	reconciliation engine's own field mapping instead of duplicating it.

	A doctype can have more than one source row (e.g. Fuel Urea Expenses'
	Supplier vs Driver Incentive legs) — each is its own amount out of its own
	account. A direction="Both" row (Payment's "Bank Transfer" type) yields
	two legs: Debit from the paying account, Credit into the receiving one.

	`sources` / `values` let a bulk caller (see backfill_missing_ledger_entries)
	pass in the reconciliation-source rows and this document's field values it
	already fetched once for the whole doctype, instead of this function
	re-querying both per document — the single-document call sites (on_submit,
	on_update, balance refresh) leave both unset and query as before.
	"""
	if sources is None:
		sources = frappe.get_all(
			"TMS Reconciliation Source",
			filters={"target_doctype": doctype, "is_active": 1},
			fields=[
				"direction", "date_fieldname", "amount_fieldname",
				"account_fieldname", "credit_account_fieldname",
			],
		)
	for source in sources:
		fieldnames = {
			source.date_fieldname, source.amount_fieldname,
			source.account_fieldname, source.credit_account_fieldname,
		} - {None, ""}
		if values is not None:
			row_values = values
		else:
			row_values = frappe.db.get_value(doctype, docname, list(fieldnames), as_dict=True)
		if not row_values:
			continue
		amount = flt(row_values.get(source.amount_fieldname))
		if not amount:
			continue
		posting_date = row_values.get(source.date_fieldname)

		if source.direction in ("Debit", "Both"):
			account = row_values.get(source.account_fieldname)
			if account:
				yield account, amount, "Debit", posting_date
		if source.direction in ("Credit", "Both"):
			account_fieldname = source.credit_account_fieldname if source.direction == "Both" else source.account_fieldname
			account = row_values.get(account_fieldname)
			if account:
				yield account, amount, "Credit", posting_date


def on_submit_write_ledger(doc, method=None):
	"""doc_events on_submit for every submittable TMS Reconciliation Source
	target doctype — writes one Account Ledger per account leg."""
	for account, amount, direction, posting_date in _iter_account_legs(doc.doctype, doc.name):
		with _allow_ledger_entry_write():
			frappe.get_doc({
				"doctype": "Account Ledger",
				"account": account,
				"posting_date": posting_date or frappe.utils.today(),
				"amount": amount,
				"direction": direction,
				"reference_doctype": doc.doctype,
				"reference_name": doc.name,
			}).insert(ignore_permissions=True)


def on_cancel_delete_ledger(doc, method=None):
	"""Cancelling the source document removes its ledger entries, so the
	account's balance reverts to what it was before — the entries only ever
	exist for live (submitted) documents."""
	frappe.db.delete("Account Ledger", {
		"reference_doctype": doc.doctype,
		"reference_name": doc.name,
	})


def get_account_balance(account: str) -> float:
	"""Current balance = the sum of every Account Ledger booked against
	this account (Credit adds, Debit subtracts) — including its own "Opening
	Balance" entry (see sync_opening_balance_entry()), so the ledger alone
	fully explains the balance; nothing is added on top of it. Always
	computed from the entries — never read from a stored running total — so
	it can be re-derived and verified at any time."""
	if not account:
		return 0.0
	net = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(CASE WHEN direction = 'Credit' THEN amount ELSE -amount END), 0)
		FROM `tabAccount Ledger` WHERE account = %s
		""",
		(account,),
	)[0][0]
	return flt(net)


def sync_opening_balance_entry(account: str, opening_balance, opening_balance_date=None) -> None:
	"""Create/update the one "Opening Balance" Account Ledger for
	`account` so it always matches Account Head.opening_balance — the entry
	that seeds the ledger before any real transaction exists, same as the
	first line of a real bank passbook. Removed (not just zeroed) if
	opening_balance is cleared, so an account with no opening balance has no
	stray zero-amount entry. `opening_balance_date` is the user-entered date
	this balance is effective from (Account Head.opening_balance_date) —
	falls back to today only if left blank."""
	amount = flt(opening_balance)
	existing = frappe.db.get_value(
		"Account Ledger",
		{"reference_doctype": "Account Head", "reference_name": account, "remarks": "Opening Balance"},
		"name",
	)
	if not amount:
		if existing:
			with _allow_ledger_entry_write():
				frappe.delete_doc("Account Ledger", existing, ignore_permissions=True, delete_permanently=True)
		return

	posting_date = opening_balance_date or frappe.utils.today()
	direction = "Credit" if amount >= 0 else "Debit"
	if existing:
		# frappe.db.set_value() deliberately skips Document events (see its own
		# docstring), so it never fires Account Ledger.on_update() — the running
		# balance_amount of every other row for this account would otherwise go
		# stale the moment an existing opening balance is edited. Explicit
		# refresh below covers it instead of relying on that side effect.
		frappe.db.set_value(
			"Account Ledger", existing,
			{"amount": abs(amount), "direction": direction, "posting_date": posting_date},
		)
		refresh_current_balance(account)
	else:
		with _allow_ledger_entry_write():
			frappe.get_doc({
				"doctype": "Account Ledger",
				"account": account,
				"posting_date": posting_date,
				"amount": abs(amount),
				"direction": direction,
				"reference_doctype": "Account Head",
				"reference_name": account,
				"remarks": "Opening Balance",
			}).insert(ignore_permissions=True)


@contextmanager
def _defer_balance_refresh():
	"""Suppress refresh_current_balance()'s work (a full-ledger SUM scan for
	the account plus a bulk UPDATE of every row's balance_amount) while a
	bulk operation (see backfill_missing_ledger_entries) writes many legs for
	the same handful of accounts in a tight loop — each write's on_update
	hook, and any explicit refresh_current_balance() call, would otherwise
	redo that same account-wide scan+update on every single write, taking
	longer the more rows already exist for that account. The final number is
	identical either way — this only skips repeating it mid-loop and instead
	refreshes each touched account once after the loop exits. Live/normal
	single-document saves never enter this context, so their behavior —
	refresh immediately, on the spot — is completely unchanged."""
	previous_flag = getattr(frappe.flags, "tms_defer_balance_refresh", False)
	previous_accounts = getattr(frappe.flags, "tms_deferred_balance_accounts", None)
	frappe.flags.tms_defer_balance_refresh = True
	frappe.flags.tms_deferred_balance_accounts = set()
	try:
		yield frappe.flags.tms_deferred_balance_accounts
	finally:
		frappe.flags.tms_defer_balance_refresh = previous_flag
		frappe.flags.tms_deferred_balance_accounts = previous_accounts


def refresh_current_balance(account: str) -> None:
	"""Recompute Account Head.current_balance and every Account Ledger row's
	balance_amount for this account as a true running balance — the
	cumulative total as of that specific row, like a bank passbook, not a
	flat mirror of the account's current total repeated on every row. Also
	recomputes ledger_sort_key, the single sortable column the default list
	view actually uses (see account_ledger.json — Frappe's Sort By control
	only ever sends one explicit column, so a compound sort_field is not
	enough on its own; ledger_sort_key folds the full precedence into one).

	Chronological order: every row is ordered by its own posting_date first
	— including "Opening Balance", which only wins the same-day tie-break
	(so it seeds the balance for its own date before that date's real
	transactions, without touching the running balance of any row dated
	earlier) — then by creation timestamp as the tie-breaker for same-day
	entries (insertion order — see backfill_missing_ledger_entries' ordering
	choice). A single bulk UPDATE (via window functions) recomputes every
	row for the account in one query — Account Head.current_balance is
	simply the final row's running balance, the same cumulative total
	either way."""
	if not account:
		return
	if getattr(frappe.flags, "tms_defer_balance_refresh", False):
		frappe.flags.tms_deferred_balance_accounts.add(account)
		return

	frappe.db.sql(
		"""
		UPDATE `tabAccount Ledger` al
		JOIN (
			SELECT
				name,
				SUM(CASE WHEN direction = 'Credit' THEN amount ELSE -amount END)
					OVER (
						ORDER BY
							posting_date,
							CASE WHEN remarks = 'Opening Balance' THEN 0 ELSE 1 END,
							creation
						ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
					) AS running_balance,
				TIMESTAMP(posting_date) + INTERVAL (
					ROW_NUMBER() OVER (
						PARTITION BY posting_date
						ORDER BY CASE WHEN remarks = 'Opening Balance' THEN 0 ELSE 1 END, creation
					) - 1
				) SECOND AS sort_key
			FROM `tabAccount Ledger`
			WHERE account = %(account)s
		) calc ON calc.name = al.name
		SET al.balance_amount = calc.running_balance,
		    al.ledger_sort_key = calc.sort_key
		WHERE al.account = %(account)s
		""",
		{"account": account},
	)
	balance = get_account_balance(account)
	frappe.db.set_value("Account Head", account, "current_balance", balance, update_modified=False)


def refresh_balances_for_doc(doc, method=None):
	"""doc_events on_submit/on_cancel companion — refreshes the cached
	current_balance of every account the document touched."""
	for account, _amount, _direction, _posting_date in _iter_account_legs(doc.doctype, doc.name):
		refresh_current_balance(account)


def _upsert_ledger_for_document(doctype: str, docname: str) -> tuple[bool, str | None]:
	"""Keep the one Account Ledger for a LEDGER_ON_SAVE_DOCTYPES document
	(Repair Expenses / Compliances / Service Logs — never submitted, so there
	is no on_submit to insert-once on) in sync with its current bank_name +
	amount on every save: create it the first time, update it in place if the
	account or amount changed on a later edit, or remove it if the document no
	longer has a valid leg (e.g. amount cleared to 0).

	Each of these doctypes has exactly one TMS Reconciliation Source row, so
	`_iter_account_legs` yields at most one leg — safe to upsert keyed only on
	(reference_doctype, reference_name), no account/direction in the identity.

	Returns (created_or_updated, skip_reason) — skip_reason is "negative" if
	the leg was left alone because its amount is negative (see
	backfill_missing_ledger_entries() for why this isn't auto-corrected).
	"""
	legs = list(_iter_account_legs(doctype, docname))
	existing_name = frappe.db.get_value(
		"Account Ledger",
		{"reference_doctype": doctype, "reference_name": docname},
		"name",
	)

	if not legs:
		if existing_name:
			account = frappe.db.get_value("Account Ledger", existing_name, "account")
			with _allow_ledger_entry_write():
				frappe.delete_doc("Account Ledger", existing_name, ignore_permissions=True, delete_permanently=True)
			refresh_current_balance(account)
		return False, None

	account, amount, direction, posting_date = legs[0]
	if amount < 0:
		return False, "negative"

	posting_date = posting_date or frappe.utils.today()
	if existing_name:
		frappe.db.set_value(
			"Account Ledger", existing_name,
			{"account": account, "amount": amount, "direction": direction, "posting_date": posting_date},
		)
	else:
		with _allow_ledger_entry_write():
			frappe.get_doc({
				"doctype": "Account Ledger",
				"account": account,
				"posting_date": posting_date,
				"amount": amount,
				"direction": direction,
				"reference_doctype": doctype,
				"reference_name": docname,
			}).insert(ignore_permissions=True)
	refresh_current_balance(account)
	return True, None


def on_update_upsert_ledger(doc, method=None):
	"""doc_events on_update for LEDGER_ON_SAVE_DOCTYPES — see
	_upsert_ledger_for_document()."""
	_upsert_ledger_for_document(doc.doctype, doc.name)


def backfill_missing_ledger_entries() -> dict:
	"""Create any Account Ledger rows missing for existing documents of
	every LEDGER_ON_SUBMIT_DOCTYPES / LEDGER_ON_SAVE_DOCTYPES doctype —
	covers documents saved/submitted before their ledger hook was wired up in
	hooks.py, so the hook never ran for them (e.g. FUEL-2026-06041, submitted
	2026-07-29, before on_submit_write_ledger was wired up on 2026-08-14).

	Submit-based doctypes only look at already-submitted (docstatus=1) rows
	and only ever insert (never update) a leg, matching what
	on_submit_write_ledger itself does. Save-based doctypes look at every
	non-cancelled row and upsert via _upsert_ledger_for_document(), matching
	on_update_upsert_ledger.

	A leg whose amount is negative (e.g. a Staff Payroll month where
	deductions exceeded earnings) is skipped rather than written — Account
	Ledger Entry requires amount > 0 with Direction carrying the sign, so
	flipping Direction and taking abs() here would be a silent business-logic
	call about which way that money actually moved; instead it's left out and
	returned in "skipped" for manual review.

	Idempotent: a submit-based leg is skipped once its Account Ledger
	already exists (matched on reference_doctype + reference_name + account +
	direction, the same identity on_submit_write_ledger itself writes); a
	save-based document is upserted every time but only writes when something
	actually changed. Re-running is a no-op past the first pass for anything
	already caught up. Returns {"created": int, "skipped": [{"doctype",
	"name", "account", "direction", "amount"}, ...]}.
	"""
	created = 0
	skipped = []
	touched_accounts = set()

	# Deferred for the whole backfill: without this, every single insert/
	# update below still triggers its own immediate refresh_current_balance()
	# (via Account Ledger's on_update hook, or _upsert_ledger_for_document's
	# own explicit call) — an account-wide SUM scan plus a bulk UPDATE of
	# every row for that account, repeated once per write instead of once
	# total. The number it computes is identical either way; deferring just
	# stops paying for it (n_writes_for_that_account) times over. Live saves
	# never enter this context, so a normal single-document save still
	# refreshes immediately, unchanged.
	with _defer_balance_refresh() as deferred_accounts:
		# Bulk-fetched per doctype instead of one query per document — with
		# years of history across 8 doctypes, the old per-document TMS
		# Reconciliation Source lookup + field fetch + existence check made
		# this take upwards of an hour on production. Reads are now
		# O(doctypes) instead of O(documents).
		for doctype in LEDGER_ON_SUBMIT_DOCTYPES:
			if not frappe.db.table_exists(doctype):
				continue

			sources = frappe.get_all(
				"TMS Reconciliation Source",
				filters={"target_doctype": doctype, "is_active": 1},
				fields=[
					"direction", "date_fieldname", "amount_fieldname",
					"account_fieldname", "credit_account_fieldname",
				],
			)
			if not sources:
				continue

			fieldnames = {"name"}
			for source in sources:
				fieldnames |= {
					source.date_fieldname, source.amount_fieldname,
					source.account_fieldname, source.credit_account_fieldname,
				} - {None, ""}

			docs = frappe.get_all(doctype, filters={"docstatus": 1}, fields=list(fieldnames))
			if not docs:
				continue

			existing_keys = {
				(row.reference_name, row.account, row.direction)
				for row in frappe.get_all(
					"Account Ledger",
					filters={"reference_doctype": doctype},
					fields=["reference_name", "account", "direction"],
				)
			}

			for row in docs:
				for account, amount, direction, posting_date in _iter_account_legs(
					doctype, row.name, sources=sources, values=row
				):
					if amount < 0:
						skipped.append({
							"doctype": doctype, "name": row.name,
							"account": account, "direction": direction, "amount": amount,
						})
						continue
					key = (row.name, account, direction)
					if key in existing_keys:
						continue
					with _allow_ledger_entry_write():
						frappe.get_doc({
							"doctype": "Account Ledger",
							"account": account,
							"posting_date": posting_date or frappe.utils.today(),
							"amount": amount,
							"direction": direction,
							"reference_doctype": doctype,
							"reference_name": row.name,
						}).insert(ignore_permissions=True)
					created += 1
					touched_accounts.add(account)
					existing_keys.add(key)

		# Same bulk-read approach as the submit-doctypes loop above, but the
		# actual write still goes through _upsert_ledger_for_document()
		# unchanged — that function is also the on_update_upsert_ledger
		# doc_event for a live save, so its create/update/delete branches
		# stay exactly as they are. Only documents whose already-written leg
		# doesn't match what _iter_account_legs computes get a write at all;
		# a document already correct is skipped entirely (no query, no
		# redundant re-write) instead of unconditionally overwritten on
		# every single migrate like before.
		for doctype in LEDGER_ON_SAVE_DOCTYPES:
			if not frappe.db.table_exists(doctype):
				continue

			sources = frappe.get_all(
				"TMS Reconciliation Source",
				filters={"target_doctype": doctype, "is_active": 1},
				fields=[
					"direction", "date_fieldname", "amount_fieldname",
					"account_fieldname", "credit_account_fieldname",
				],
			)
			if not sources:
				continue

			fieldnames = {"name"}
			for source in sources:
				fieldnames |= {
					source.date_fieldname, source.amount_fieldname,
					source.account_fieldname, source.credit_account_fieldname,
				} - {None, ""}

			docs = frappe.get_all(doctype, filters={"docstatus": ["!=", 2]}, fields=list(fieldnames))
			if not docs:
				continue

			existing_rows = {
				row.reference_name: (row.account, flt(row.amount), row.direction)
				for row in frappe.get_all(
					"Account Ledger",
					filters={"reference_doctype": doctype},
					fields=["reference_name", "account", "amount", "direction"],
				)
			}

			for row in docs:
				legs = list(_iter_account_legs(doctype, row.name, sources=sources, values=row))
				existing = existing_rows.get(row.name)

				if not legs:
					if existing:
						changed, _skip_reason = _upsert_ledger_for_document(doctype, row.name)
						if changed:
							created += 1
					continue

				account, amount, direction, _posting_date = legs[0]
				if amount < 0:
					skipped.append({
						"doctype": doctype, "name": row.name,
						"account": account, "direction": direction, "amount": amount,
					})
					continue

				if existing == (account, flt(amount), direction):
					continue

				changed, _skip_reason = _upsert_ledger_for_document(doctype, row.name)
				if changed:
					created += 1

		touched_accounts |= deferred_accounts

	for account in touched_accounts:
		refresh_current_balance(account)

	return {"created": created, "skipped": skipped}
