# Copyright (c) 2026, LogiCore and contributors
# For license information, please see license.txt

from __future__ import annotations

import csv
import datetime
import os
import re

from dateutil import parser as date_parser

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, formatdate, getdate

from logicore.utils.indian_format import format_inr

CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def _normalize_header(value) -> str:
	return " ".join(cstr(value).strip().split()).casefold()


def _normalize_cell(value) -> str:
	"""Render any raw cell value (CSV text, or a native date/number straight
	out of openpyxl/xlrd) as a plain string, so the rest of this module's
	string-based parsing (_parse_amount, _parse_transaction_date) works
	identically regardless of which file format it came from.
	"""
	if value is None:
		return ""
	if isinstance(value, (datetime.datetime, datetime.date)):
		return value.strftime("%d/%m/%Y")
	return cstr(value)


def _read_csv_rows(full_path: str) -> list[list[str]]:
	last_error = None
	for encoding in CSV_ENCODINGS:
		try:
			with open(full_path, "r", encoding=encoding, errors="strict", newline="") as handle:
				return [[_normalize_cell(cell) for cell in row] for row in csv.reader(handle)]
		except UnicodeDecodeError as exc:
			last_error = exc
			continue
	if last_error:
		raise last_error
	return []


def _read_xlsx_rows(full_path: str) -> list[list[str]]:
	import openpyxl

	# read_only=True relies on the file's <dimension> metadata tag to stream
	# rows correctly; real ICICI exports have been observed with a broken/
	# missing dimension tag, which silently degrades read_only parsing to a
	# single blank row instead of raising an error. Full parsing tolerates
	# this and reads every row correctly, at the cost of loading the whole
	# file into memory — acceptable for bank statement file sizes.
	workbook = openpyxl.load_workbook(full_path, data_only=True)
	sheet = workbook.active
	return [[_normalize_cell(cell) for cell in row] for row in sheet.iter_rows(values_only=True)]


def _read_xls_rows(full_path: str) -> list[list[str]]:
	import xlrd

	workbook = xlrd.open_workbook(full_path)
	sheet = workbook.sheet_by_index(0)
	rows = []
	for row_idx in range(sheet.nrows):
		row = []
		for cell in sheet.row(row_idx):
			if cell.ctype == xlrd.XL_CELL_DATE:
				row.append(_normalize_cell(xlrd.xldate_as_datetime(cell.value, workbook.datemode)))
			else:
				row.append(_normalize_cell(cell.value))
		rows.append(row)
	return rows


def _read_statement_rows(file_url: str) -> list[list[str]]:
	if not file_url:
		frappe.throw(_("Statement file is required."))
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	full_path = file_doc.get_full_path()
	extension = os.path.splitext(file_doc.file_name or file_doc.file_url or "")[1].lower()
	if extension == ".csv":
		return _read_csv_rows(full_path)
	if extension == ".xlsx":
		return _read_xlsx_rows(full_path)
	if extension == ".xls":
		return _read_xls_rows(full_path)
	frappe.throw(_("Unsupported file type '{0}' — only .csv, .xlsx, and .xls are supported.").format(extension), title=_("Unsupported File"))


def _parse_amount(value) -> float:
	text = cstr(value).strip().replace(",", "")
	if not text:
		return 0.0
	return flt(text)


def _parse_transaction_date(value):
	text = cstr(value).strip()
	return date_parser.parse(text, dayfirst=True).date()


def _is_asterisk_separator_row(raw_row: list) -> bool:
	"""True for a row of pure '****...' cells — real bank exports use these as
	visual dividers, one right after the header row and (for exports that
	carry a trailing "STATEMENT SUMMARY" footer with running totals, GST
	details, etc.) another right after the last real transaction row, marking
	the end of the transaction table. Used to stop parsing before that footer
	— its own total/summary rows can carry amount-shaped values in the date
	column position and would otherwise be mistaken for a transaction."""
	cells = [cstr(c).strip() for c in raw_row if cstr(c).strip()]
	return bool(cells) and all(set(c) == {"*"} for c in cells)


_ACCOUNT_LABEL_PATTERN = re.compile(r"a\s*/?\s*c\s*no\.?|account\s*no\.?", re.IGNORECASE)


def _validate_account_number_in_letterhead(rows: list[list[str]], header_index: int, bank_account: str) -> None:
	"""Cross-check the uploaded file's own letterhead (the account-info rows
	above the header row) against Account Head.bank_ac_last_digits, so
	uploading the wrong real bank account's statement is caught immediately
	instead of silently producing an all-Unmatched result. Skipped entirely
	if bank_ac_last_digits isn't set on the Account Head — nothing to check
	against, so the upload proceeds unvalidated (same as before this field
	existed).

	Only considers digits that appear after an "A/C No" / "Account No" label
	within the same letterhead row — not just any long digit run — so
	unrelated numbers on the same row (Cust Id, IFSC, branch code, etc.)
	never get mistaken for the account number, in either the match check or
	the error message shown to the user.
	"""
	last_digits = cstr(frappe.db.get_value("Account Head", bank_account, "bank_ac_last_digits")).strip()
	if not last_digits:
		return

	bank_account_label = frappe.db.get_value("Account Head", bank_account, "name1") or bank_account
	found_numbers = set()
	for row in rows[:header_index]:
		row_text = " ".join(cstr(cell) for cell in row)
		label_match = _ACCOUNT_LABEL_PATTERN.search(row_text)
		if not label_match:
			continue
		# Only the first digit run right after the label — the row can also
		# contain an unrelated later number (e.g. a branch address pincode
		# sharing the row with "A/C No:" in real ICICI exports).
		value_match = re.search(r"\d{4,}", row_text[label_match.end():])
		if not value_match:
			continue
		digit_run = value_match.group()
		if digit_run.endswith(last_digits):
			return
		found_numbers.add(digit_run[-5:])

	if found_numbers:
		frappe.throw(
			_(
				"This file's letterhead shows an account number ending in \"{0}\", but the "
				"selected Bank Account (\"{1}\") is set up for an account ending in \"{2}\". "
				"Please check that you attached the correct statement file for this Bank Account."
			).format(", ".join(sorted(found_numbers)), bank_account_label, last_digits),
			title=_("Bank Account Mismatch"),
		)
	frappe.throw(
		_(
			"Could not find any account number in this file's letterhead to confirm it belongs "
			"to Bank Account \"{0}\" (configured for an account ending in \"{1}\")."
		).format(bank_account_label, last_digits),
		title=_("Bank Account Mismatch"),
	)


def parse_statement_file(
	bank_account: str,
	setting_name: str | None,
	file_url: str,
	from_date,
	to_date,
	setting_doc=None,
) -> list[frappe._dict]:
	"""Parse a bank statement file (.csv/.xlsx/.xls) into transaction rows
	within [from_date, to_date]. Each row carries `direction` ("Debit" or
	"Credit") based on which column had a non-zero amount — Debit rows match
	against Debit-direction TMS Reconciliation Source legs, Credit rows
	against Credit-direction legs (currently just Receipt).
	`setting_doc` lets callers pass an unsaved TMS Bank Reconciliation
	Setting (used by tests that need to assert on a setting that's
	deliberately invalid to save).
	"""
	setting = setting_doc or frappe.get_doc("TMS Bank Reconciliation Setting", setting_name)

	rows = _read_statement_rows(file_url)

	header_index = setting.header_row - 1
	data_index = setting.data_start_row - 1
	if header_index < 0 or header_index >= len(rows):
		frappe.throw(
			_("Header Row ({0}) does not match the uploaded file — it only has {1} rows.").format(
				setting.header_row, len(rows)
			)
		)
	if data_index < header_index or data_index > len(rows):
		frappe.throw(
			_("Data Start Row ({0}) does not match the uploaded file — it only has {1} rows.").format(
				setting.data_start_row, len(rows)
			)
		)

	_validate_account_number_in_letterhead(rows, header_index, bank_account)

	header_row = [cstr(v).strip() for v in rows[header_index]]
	header_map = {_normalize_header(v): idx for idx, v in enumerate(header_row)}

	def _column_index(column_label: str, required: bool) -> int | None:
		if not column_label:
			if required:
				frappe.throw(_("Bank Reconciliation Setting is missing a required column mapping."))
			return None
		idx = header_map.get(_normalize_header(column_label))
		if idx is None:
			frappe.throw(
				_("Column '{0}' was not found in the statement file's header row.").format(column_label)
			)
		return idx

	date_idx = _column_index(setting.transaction_date_column, required=True)
	debit_idx = _column_index(setting.debit_column, required=True)
	credit_idx = _column_index(setting.credit_column, required=True)
	narration_idx = _column_index(setting.get("narration_column"), required=False)
	reference_idx = _column_index(setting.get("reference_column"), required=False)
	balance_idx = _column_index(setting.get("balance_column"), required=False)

	from_date = getdate(from_date)
	to_date = getdate(to_date)

	results = []
	for row_number, raw_row in enumerate(rows[data_index:], start=1):
		if not raw_row or all(cstr(c).strip() == "" for c in raw_row):
			continue
		if _is_asterisk_separator_row(raw_row):
			# End of the transaction table — everything after this is a
			# footer (statement summary/totals, GST/branch details, etc.),
			# never further transactions.
			break
		debit_amount = _parse_amount(raw_row[debit_idx]) if debit_idx < len(raw_row) else 0.0
		credit_amount = _parse_amount(raw_row[credit_idx]) if credit_idx < len(raw_row) else 0.0
		if debit_amount:
			amount, direction = debit_amount, "Debit"
		elif credit_amount:
			amount, direction = credit_amount, "Credit"
		else:
			continue
		raw_date_value = raw_row[date_idx] if date_idx < len(raw_row) else ""
		try:
			transaction_date = _parse_transaction_date(raw_date_value)
		except (ValueError, OverflowError):
			frappe.throw(
				_(
					"Row {0} of the statement file: could not read \"{1}\" as a date (from the "
					"Transaction Date column). This usually means the Transaction Date Column "
					"in this Bank Account's TMS Bank Reconciliation Setting is pointing at the "
					"wrong column — please check its column mapping against the actual file."
				).format(row_number, raw_date_value),
				title=_("Invalid Transaction Date"),
			)
		if transaction_date < from_date or transaction_date > to_date:
			continue
		results.append(frappe._dict(
			row_number=row_number,
			transaction_date=transaction_date,
			amount=amount,
			direction=direction,
			narration=cstr(raw_row[narration_idx]).strip() if narration_idx is not None and narration_idx < len(raw_row) else "",
			reference_no=cstr(raw_row[reference_idx]).strip() if reference_idx is not None and reference_idx < len(raw_row) else "",
			balance=_parse_amount(raw_row[balance_idx]) if balance_idx is not None and balance_idx < len(raw_row) else None,
		))
	return results


_OPENING_BALANCE_LABEL_PATTERN = re.compile(r"^opening\s*bal", re.IGNORECASE)
_CLOSING_BALANCE_LABEL_PATTERN = re.compile(r"^closing\s*bal", re.IGNORECASE)
_AMOUNT_LIKE_PATTERN = re.compile(r"^[₹$]?\s*-?[\d,]*\.?\d+\s*(cr|dr)?$", re.IGNORECASE)


def _looks_like_amount(text: str) -> bool:
	return bool(_AMOUNT_LIKE_PATTERN.match(text.strip()))


def _first_amount_after(row: list, label_idx: int) -> float | None:
	"""Same-row lookup: the first non-empty, amount-shaped cell after the
	label — e.g. a "Opening Bal: 1,23,456.00" layout where the value sits a
	few cells along in the same row. Skips (rather than misreads as 0) a
	non-numeric cell like another column header sharing that row — e.g. a
	"Debits"/"Credits" header cell — so a genuinely absent value here falls
	through to the caller's own row-below fallback instead of being
	mistaken for a found 0.
	"""
	for cell in row[label_idx + 1:]:
		text = cstr(cell).strip()
		if text and _looks_like_amount(text):
			return _parse_amount(text)
	return None


def extract_statement_footer_balances(file_url: str) -> tuple[float | None, float | None]:
	"""Scan the raw statement file for the bank's own Opening/Closing balance
	summary and return those amounts directly — authoritative over deriving
	them from individual transaction rows, since it reflects the whole
	statement's true balances regardless of which rows the selected date
	range happens to include. Handles two layouts real exports use:
	  - same-row ("Opening Bal: 1,23,456.00", ICICI-style) — value sits later
	    in the same row as the label.
	  - two-row table ("Opening Balance" / "Closing Bal" as column headers in
	    one row, HDFC-style) — the value sits directly below the label, same
	    column, in the very next row.
	Returns None for either figure the file has no readable value for.
	"""
	rows = _read_statement_rows(file_url)
	opening_balance = closing_balance = None
	for row_idx, row in enumerate(rows):
		for idx, cell in enumerate(row):
			label = cstr(cell).strip()
			if _OPENING_BALANCE_LABEL_PATTERN.match(label):
				opening_balance = _first_amount_after(row, idx)
				if opening_balance is None and row_idx + 1 < len(rows):
					below = rows[row_idx + 1]
					if idx < len(below) and _looks_like_amount(cstr(below[idx]).strip()):
						opening_balance = _parse_amount(below[idx])
			elif _CLOSING_BALANCE_LABEL_PATTERN.match(label):
				closing_balance = _first_amount_after(row, idx)
				if closing_balance is None and row_idx + 1 < len(rows):
					below = rows[row_idx + 1]
					if idx < len(below) and _looks_like_amount(cstr(below[idx]).strip()):
						closing_balance = _parse_amount(below[idx])
	return opening_balance, closing_balance


def compute_opening_closing_balance(parsed_rows: list) -> tuple[float | None, float | None]:
	"""Fallback for extract_statement_footer_balances() — used when the file
	has no explicit 'Opening Bal:'/'Closing Bal:' footer. Derives Opening/
	Closing Balance for the reconciled period from each parsed row's own
	running balance (read from the statement file's Balance Column, if
	configured on the Bank Reconciliation Setting) — Opening is the balance
	just before the first row in the period, Closing is the balance as of the
	last row. Rows are already in file order (chronological for a real bank
	statement), and already scoped to [from_date, to_date] by
	parse_statement_file(). Returns (None, None) if no row carries a balance
	— Balance Column not configured, or the file has no such column.
	"""
	rows_with_balance = [row for row in parsed_rows if row.get("balance") is not None]
	if not rows_with_balance:
		return None, None

	first_row = rows_with_balance[0]
	last_row = rows_with_balance[-1]
	opening_balance = (
		first_row.balance + first_row.amount if first_row.direction == "Debit"
		else first_row.balance - first_row.amount
	)
	return opening_balance, last_row.balance


def _add_leg_candidates(
	target_map: dict, source, bank_account: str, from_date, to_date,
	account_fieldname: str, reconciled_fieldname: str,
) -> None:
	"""Query one leg of a source (its own account/reconciled fieldnames) and
	fold matches into `target_map`, keyed by (date, amount)."""
	filters = {
		account_fieldname: bank_account,
		source.date_fieldname: ["between", [from_date, to_date]],
		reconciled_fieldname: 0,
	}
	if source.requires_submitted:
		filters["docstatus"] = 1

	rows = frappe.db.get_all(
		source.target_doctype,
		filters=filters,
		fields=["name", source.date_fieldname, source.amount_fieldname],
		order_by="creation asc",
	)
	for row in rows:
		key = (getdate(row[source.date_fieldname]), flt(row[source.amount_fieldname]))
		target_map.setdefault(key, []).append((source.name, source.target_doctype, row.name))


def get_eligible_records(bank_account: str, from_date, to_date) -> tuple[dict, dict]:
	"""Submitted (where applicable), not-yet-reconciled records across every
	active TMS Reconciliation Source leg, paid from `bank_account` within
	[from_date, to_date] — split into a Debit-direction map and a
	Credit-direction map, each keyed by (date, amount) -> list of
	(source_name, target_doctype, docname).

	A source with direction="Both" (e.g. a Payment "Bank Transfer" that is
	Debit on the paying account and Credit on the receiving one) contributes
	to BOTH maps — once via its own account_fieldname/reconciled_fieldname
	(the Debit leg), once via its credit_account_fieldname/
	credit_reconciled_fieldname (the Credit leg) — same target_doctype, same
	record, two independent reconciled flags.

	Candidates within each key are ordered by TMS Reconciliation Source.sequence
	(lower first), then by record creation (oldest first) within a source — the
	priority + FIFO order match_transactions() consumes when a key's candidates
	are shared out across every statement row hashing to it.

	This is the single seam a future doctype/leg addition extends — add a
	TMS Reconciliation Source row, nothing here changes.
	"""
	from_date = getdate(from_date)
	to_date = getdate(to_date)
	debit_map: dict = {}
	credit_map: dict = {}

	sources = frappe.get_all(
		"TMS Reconciliation Source",
		filters={"is_active": 1},
		fields=[
			"name", "target_doctype", "direction", "requires_submitted",
			"date_fieldname", "amount_fieldname", "account_fieldname",
			"reconciled_fieldname", "sequence",
			"credit_account_fieldname", "credit_reconciled_fieldname",
		],
		order_by="sequence asc, name asc",
	)
	for source in sources:
		if source.direction in ("Debit", "Both"):
			_add_leg_candidates(
				debit_map, source, bank_account, from_date, to_date,
				source.account_fieldname, source.reconciled_fieldname,
			)
		if source.direction in ("Credit", "Both"):
			account_fieldname = source.credit_account_fieldname if source.direction == "Both" else source.account_fieldname
			reconciled_fieldname = source.credit_reconciled_fieldname if source.direction == "Both" else source.reconciled_fieldname
			_add_leg_candidates(
				credit_map, source, bank_account, from_date, to_date,
				account_fieldname, reconciled_fieldname,
			)

	return debit_map, credit_map


def match_transactions(parsed_rows: list, bank_account: str, from_date, to_date) -> list:
	"""Match each parsed statement row against eligible records (across every
	active TMS Reconciliation Source leg) by exact (transaction_date, amount),
	restricted to the leg(s) whose `direction` matches the row's own
	Debit/Credit direction. Returns parsed_rows with `status`,
	`matched_source`, `matched_doctype`, `matched_docname` added to each dict.

	Every statement row is grouped with every other row sharing its own
	(direction, date, amount) key *before* any matching decision is made —
	including keys with only one row — so a key's candidate list is always
	consumed through the same single FIFO pass (see _resolve_key_group()).
	That is deliberate: a real statement can carry two (or more) genuinely
	separate transactions that happen to share date and amount (e.g. two
	identical-amount UPI payments on the same day) — if only one eligible
	record exists for that key, handing it to whichever row happened to be
	checked first (the old per-row shortcut for a single candidate) would
	silently also hand that *same* record to the second row, reconciling one
	real payment against two different bank lines. Routing every key through
	one grouped pass guarantees a candidate is never handed out twice.
	"""
	debit_map, credit_map = get_eligible_records(bank_account, from_date, to_date)
	results = []
	rows_by_key = {}
	for row in parsed_rows:
		row = frappe._dict(row)
		key = (row.direction, row.transaction_date, flt(row.amount))
		rows_by_key.setdefault(key, []).append(row)
		results.append(row)

	for (direction, transaction_date, amount), rows in rows_by_key.items():
		candidates_map = debit_map if direction == "Debit" else credit_map
		candidates = candidates_map.get((transaction_date, amount), [])
		_resolve_key_group(rows, candidates)

	return results


def _resolve_key_group(rows: list, candidates: list) -> None:
	"""Assign `candidates` to `rows` sharing one (direction, date, amount)
	key, in statement row order (FIFO) — candidates are themselves already
	ordered by TMS Reconciliation Source.sequence then record creation (see
	get_eligible_records()). Each candidate is handed to at most one row, so
	the same real record is never matched to two different statement
	transactions.

	Every row that gets a candidate this way is a deterministic, defensible
	pick (priority + FIFO, not a coin toss) — there is no longer a genuinely
	"which one?" choice left for a human to make, so it's Matched outright.
	A key with more rows than candidates leaves the extras with nothing to
	assign — no eligible record exists for them specifically, only for their
	earlier-row siblings — so they show Unmatched, same as any other row with
	zero candidates: create the missing record (or investigate the narration)
	and re-run Parse & Match, or match manually via Browse.

	Mutates the `row` dicts in place — they are the same objects already
	appended to match_transactions()'s `results` list.
	"""
	rows.sort(key=lambda r: r.row_number)
	for row, candidate in zip(rows, candidates):
		source_name, target_doctype, docname = candidate
		row.status = "Matched"
		row.matched_source = source_name
		row.matched_doctype = target_doctype
		row.matched_docname = docname
	for row in rows[len(candidates):]:
		row.status = "Unmatched"
		row.matched_source = None
		row.matched_doctype = None
		row.matched_docname = None


def _get_eligible_matched_records(
	matched_source: str, bank_reconciliation: str, direction: str = None, txt: str = "", limit: int = 0,
	current_row_name: str = None,
):
	"""Shared lookup behind get_matched_record_table() (table-picker dialog) —
	records the matching engine itself would consider eligible for
	`matched_source`: same TMS Reconciliation Source config, same Bank
	Account, unreconciled, within the parent TMS Bank Reconciliation's own
	[from_date, to_date]. `txt` searches across every column the picker
	actually shows (ID, date, amount, and each display_fieldnames entry) —
	not just the ID — so typing a vendor name or reference number finds the
	row it appears in. `direction` (the statement row's own Debit/Credit)
	picks which leg to query when the source is direction="Both" — ignored
	otherwise. Returns (source_dict, extra_fields, rows) — source/extra_fields
	are None/[] and rows [] if matched_source or bank_reconciliation don't
	resolve.

	A picked record's own `reconciled_fieldname` only gets flipped to 1 at
	submit time (see before_submit()), so between picking it for one row and
	submitting the document it still reads as unreconciled — nothing stopped
	the same record from also showing up (and being pickable) as a candidate
	for a different, still-unmatched row. `current_row_name` (the transaction
	row being browsed for) lets this additionally exclude every docname
	already picked as `matched_docname` on this document's OTHER transaction
	rows, so an in-progress manual match can't be handed out twice.
	"""
	source = frappe.db.get_value(
		"TMS Reconciliation Source", matched_source,
		["target_doctype", "date_fieldname", "amount_fieldname", "account_fieldname",
		 "reconciled_fieldname", "requires_submitted", "display_fieldnames",
		 "direction", "credit_account_fieldname", "credit_reconciled_fieldname"],
		as_dict=True,
	)
	recon = frappe.db.get_value(
		"TMS Bank Reconciliation", bank_reconciliation,
		["bank_account", "from_date", "to_date"], as_dict=True,
	)
	if not source or not recon:
		return None, [], []

	extra_fields = [f.strip() for f in (source.display_fieldnames or "").split(",") if f.strip()]

	use_credit_leg = source.direction == "Both" and direction == "Credit"
	account_fieldname = source.credit_account_fieldname if use_credit_leg else source.account_fieldname
	reconciled_fieldname = source.credit_reconciled_fieldname if use_credit_leg else source.reconciled_fieldname

	query_filters = {
		account_fieldname: recon.bank_account,
		source.date_fieldname: ["between", [recon.from_date, recon.to_date]],
		reconciled_fieldname: 0,
	}
	if source.requires_submitted:
		query_filters["docstatus"] = 1

	already_picked_filters = {
		"parent": bank_reconciliation,
		"parenttype": "TMS Bank Reconciliation",
		"matched_doctype": source.target_doctype,
		"matched_docname": ["is", "set"],
	}
	if current_row_name:
		already_picked_filters["name"] = ["!=", current_row_name]
	already_picked = frappe.db.get_all(
		"TMS Bank Reconciliation Transaction", filters=already_picked_filters, pluck="matched_docname",
	)
	if already_picked:
		query_filters["name"] = ["not in", already_picked]

	or_filters = None
	if txt:
		searchable_fields = ["name", source.date_fieldname, source.amount_fieldname, *extra_fields]
		or_filters = [[field, "like", f"%{txt}%"] for field in searchable_fields]

		# The date column is stored/LIKE-matched as YYYY-MM-DD, but the picker
		# displays (and users type) dd-mm-yyyy — so a typed date only matches
		# via substring today if it happens to overlap that ISO layout (e.g.
		# "2026-07"). Parse it and add an exact match too, so "03-07-2026" or
		# "03/07/2026" finds that date's rows as well.
		if any(sep in txt for sep in ("-", "/")):
			try:
				parsed_date = date_parser.parse(txt, dayfirst=True).date()
			except (ValueError, OverflowError):
				parsed_date = None
			if parsed_date:
				or_filters.append([source.date_fieldname, "=", parsed_date])

	rows = frappe.get_all(
		source.target_doctype,
		filters=query_filters,
		or_filters=or_filters,
		fields=["name", source.date_fieldname, source.amount_fieldname, *extra_fields],
		order_by=f"{source.date_fieldname} asc",
		page_length=cint(limit) or 0,
	)
	return source, extra_fields, rows


@frappe.whitelist()
def get_period_transaction_summary(bank_account: str, from_date, to_date, bank_reconciliation: str = None) -> list[dict]:
	"""Pre-upload preview for the TMS Bank Reconciliation form: as soon as Bank
	Account + From Date + To Date are set (before any statement file is even
	attached), shows how many transactions — and their total amount —
	actually happened against this account in that window, broken down by
	each active TMS Reconciliation Source leg (e.g. "Vendor Payment: 25",
	"Receipt: 5"). Purely informational, independent of reconciled status and
	of the statement-file matching flow (Parse & Match) — those are unrelated
	answers to a different question ("what does the bank say happened" vs.
	"what did our own records say happened").

	`bank_reconciliation` (optional) additionally reports, per source leg, how
	many of THIS document's own `transactions` rows matched against it, and
	their amount (`matched_amount`) alongside how much of `total_amount`
	still isn't (`remaining_amount`) — once a statement has actually been
	parsed, that answers a follow-up question the count alone can't: out of
	the N Vendor Payments (₹total) in this period, how many — and how much —
	did the uploaded statement actually confirm?
	"""
	if not bank_account or not from_date or not to_date:
		return []
	from_date = getdate(from_date)
	to_date = getdate(to_date)

	matched_counts = {}
	matched_amounts = {}
	if bank_reconciliation:
		matched_rows = frappe.get_all(
			"TMS Bank Reconciliation Transaction",
			filters={"parent": bank_reconciliation, "status": "Matched"},
			fields=["matched_source", "direction", "amount"],
		)
		for row in matched_rows:
			key = (row.matched_source, row.direction)
			matched_counts[key] = matched_counts.get(key, 0) + 1
			matched_amounts[key] = matched_amounts.get(key, 0.0) + flt(row.amount)

	sources = frappe.get_all(
		"TMS Reconciliation Source",
		filters={"is_active": 1},
		fields=[
			"name", "label", "target_doctype", "direction", "requires_submitted",
			"date_fieldname", "amount_fieldname", "account_fieldname",
			"credit_account_fieldname", "sequence",
		],
		order_by="sequence asc, name asc",
	)

	summary = []
	for source in sources:
		legs = []
		if source.direction in ("Debit", "Both"):
			legs.append((source.account_fieldname, "Debit", " (Debit)" if source.direction == "Both" else ""))
		if source.direction in ("Credit", "Both"):
			account_fieldname = source.credit_account_fieldname if source.direction == "Both" else source.account_fieldname
			legs.append((account_fieldname, "Credit", " (Credit)" if source.direction == "Both" else ""))

		for account_fieldname, leg_direction, suffix in legs:
			filters = {
				account_fieldname: bank_account,
				source.date_fieldname: ["between", [from_date, to_date]],
			}
			if source.requires_submitted:
				filters["docstatus"] = 1
			rows = frappe.db.get_all(source.target_doctype, filters=filters, fields=[source.amount_fieldname])
			total_amount = sum(flt(r[source.amount_fieldname]) for r in rows)
			matched_amount = matched_amounts.get((source.name, leg_direction), 0.0)
			summary.append({
				"label": (source.label or source.name) + suffix,
				"target_doctype": source.target_doctype,
				"count": len(rows),
				"matched_count": matched_counts.get((source.name, leg_direction), 0),
				"total_amount": total_amount,
				"matched_amount": matched_amount,
				"remaining_amount": total_amount - matched_amount,
			})

	return summary


def _resolve_link_titles(meta, extra_fields: list[str], rows: list) -> None:
	"""For every `extra_fields` entry that's a Link field, replace each row's
	raw linked-doc ID with that doctype's own title (e.g. Driver's full_name,
	Employee's employee_name, Supplier's supplier_name) — so the Browse picker
	shows a human-readable name instead of an opaque ID, for any source's
	display_fieldnames, without needing per-source special-casing. No-op for
	Link doctypes whose title_field is just "name" (already human-readable).
	Mutates `rows` in place.
	"""
	for fieldname in extra_fields:
		df = meta.get_field(fieldname)
		if not df or df.fieldtype != "Link" or not df.options:
			continue
		title_field = frappe.get_meta(df.options).get("title_field")
		if not title_field or title_field == "name":
			continue
		ids = {row.get(fieldname) for row in rows if row.get(fieldname)}
		if not ids:
			continue
		titles = frappe.get_all(df.options, filters={"name": ["in", list(ids)]}, fields=["name", title_field])
		title_map = {t.name: t.get(title_field) for t in titles if t.get(title_field)}
		for row in rows:
			value = row.get(fieldname)
			if value in title_map:
				row[fieldname] = title_map[value]


@frappe.whitelist()
def get_matched_record_table(
	matched_source: str, bank_reconciliation: str, direction: str = None, txt: str = "",
	current_row_name: str = None,
):
	"""Structured (column headers + row dicts) version of the same eligible-
	candidates lookup, for the table-picker dialog opened from a transaction
	row's "Browse" button — lets the client render a real HTML table instead
	of a plain dropdown list. `direction` is the transaction row's own Debit/
	Credit — required to pick the right leg when `matched_source` is a
	direction="Both" source (e.g. Payment's "Bank Transfer" type).
	`current_row_name` excludes records already picked by this document's
	other transaction rows (see _get_eligible_matched_records).
	"""
	source, extra_fields, rows = _get_eligible_matched_records(
		matched_source, bank_reconciliation, direction, txt, current_row_name=current_row_name,
	)
	if not source:
		return {"target_doctype": None, "columns": [], "rows": []}

	meta = frappe.get_meta(source.target_doctype)
	_resolve_link_titles(meta, extra_fields, rows)

	columns = [
		{"fieldname": "name", "label": _("ID")},
		{"fieldname": source.date_fieldname, "label": meta.get_label(source.date_fieldname) or _("Date")},
		{"fieldname": source.amount_fieldname, "label": meta.get_label(source.amount_fieldname) or _("Amount")},
	]
	for fieldname in extra_fields:
		columns.append({"fieldname": fieldname, "label": meta.get_label(fieldname) or fieldname})

	table_rows = []
	for row in rows:
		formatted = {"name": row.name}
		formatted[source.date_fieldname] = formatdate(row.get(source.date_fieldname), "dd-mm-yyyy")
		amount = row.get(source.amount_fieldname)
		formatted[source.amount_fieldname] = format_inr(amount) if amount is not None else ""
		for fieldname in extra_fields:
			formatted[fieldname] = cstr(row.get(fieldname))
		table_rows.append(formatted)

	return {"target_doctype": source.target_doctype, "columns": columns, "rows": table_rows}
