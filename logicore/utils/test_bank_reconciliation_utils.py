# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

from datetime import date

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.file_manager import save_file

from logicore.utils.bank_reconciliation_utils import (
	compute_opening_closing_balance,
	extract_statement_footer_balances,
	get_eligible_records,
	match_transactions,
	parse_statement_file,
)

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []

# 3 letterhead rows + 1 header row + a "****" divider row (HDFC-style gap) +
# 3 data rows, mirroring real ICICI/HDFC export shapes (comma-grouped/quoted
# amounts, dd/Mon/yyyy dates) without reproducing every real letterhead row.
SAMPLE_STATEMENT_CSV = (
	"Detailed Statement,,,,\n"
	"Name:,SADASHIV LOGISTICS PRIVATE LIMITED,,,\n"
	"A/C No:,084405002881,,,\n"
	"S.N.,Transaction Date,Cheque. No./Ref. No.,Transaction Remarks,Withdrawal Amt (INR),Deposit Amt (INR)\n"
	"****,****,****,****,****,****\n"
	'1,01/Jul/2026,,RTGS-HDFCR52026070177805459-SADASHIV LOGISTICS,,"4,00,000.00"\n'
	'2,01/Jul/2026,,INF/INFT/044964495301/AdvLr15206/AnilKumar1,"16,325.00",\n'
	'3,03/Jul/2026,REF123,MMT/IMPS/618416268165/Advfor2veh/AtharKhan,"1,18,700.00",\n'
)

# Same shape as SAMPLE_STATEMENT_CSV plus a trailing running-Balance column,
# for testing balance_column parsing and opening/closing balance derivation.
# Starting balance (before row 1) is 5,00,000.00; each row's Balance is the
# running total after that row's own Debit/Credit is applied.
SAMPLE_STATEMENT_CSV_WITH_BALANCE = (
	"Detailed Statement,,,,,\n"
	"Name:,SADASHIV LOGISTICS PRIVATE LIMITED,,,,\n"
	"A/C No:,084405002881,,,,\n"
	"S.N.,Transaction Date,Cheque. No./Ref. No.,Transaction Remarks,Withdrawal Amt (INR),Deposit Amt (INR),Balance (INR)\n"
	"****,****,****,****,****,****,****\n"
	'1,01/Jul/2026,,RTGS-HDFCR52026070177805459-SADASHIV LOGISTICS,,"4,00,000.00","9,00,000.00"\n'
	'2,01/Jul/2026,,INF/INFT/044964495301/AdvLr15206/AnilKumar1,"16,325.00",,"8,83,675.00"\n'
	'3,03/Jul/2026,REF123,MMT/IMPS/618416268165/Advfor2veh/AtharKhan,"1,18,700.00",,"7,64,975.00"\n'
)

# Same shape as SAMPLE_STATEMENT_CSV plus a real-ICICI-style "Page Total"
# footer, for testing extract_statement_footer_balances().
SAMPLE_STATEMENT_CSV_WITH_FOOTER = SAMPLE_STATEMENT_CSV + (
	"\n"
	"Page Total,,,,\n"
	'"Opening Bal:","6,93,569.39",,,\n'
	'"Withdrawls:","89,97,536.00",,,\n'
	'"Deposits:","89,00,000.00",,,\n'
	'"Closing Bal:","5,96,033.39",,,\n'
)


class IntegrationTestParseStatementFile(IntegrationTestCase):
	def setUp(self):
		self.bank_account = frappe.get_doc({
			"doctype": "Account Head",
			"name1": "Test Parse Bank Account",
			"group": "BANK",
		}).insert(ignore_permissions=True)
		self.setting = frappe.get_doc({
			"doctype": "TMS Bank Reconciliation Setting",
			"bank_account": self.bank_account.name,
			"header_row": 4,
			"data_start_row": 6,
			"transaction_date_column": "Transaction Date",
			"debit_column": "Withdrawal Amt (INR)",
			"credit_column": "Deposit Amt (INR)",
			"narration_column": "Transaction Remarks",
			"reference_column": "Cheque. No./Ref. No.",
		}).insert(ignore_permissions=True)
		file_doc = save_file(
			"test_statement.csv",
			SAMPLE_STATEMENT_CSV.encode("utf-8"),
			"TMS Bank Reconciliation Setting",
			self.setting.name,
			is_private=1,
		)
		self.file_url = file_doc.file_url

	def tearDown(self):
		frappe.db.delete("TMS Bank Reconciliation Setting", {"bank_account": self.bank_account.name})
		self.bank_account.delete()

	def test_skips_letterhead_and_divider_row_and_parses_both_directions(self):
		rows = parse_statement_file(
			self.bank_account.name, self.setting.name, self.file_url,
			date(2026, 7, 1), date(2026, 7, 31),
		)
		self.assertEqual(len(rows), 3)
		self.assertEqual(rows[0].row_number, 1)
		self.assertEqual(rows[0].transaction_date, date(2026, 7, 1))
		self.assertEqual(rows[0].amount, 400000.0)
		self.assertEqual(rows[0].direction, "Credit")
		self.assertEqual(rows[1].amount, 16325.0)
		self.assertEqual(rows[1].direction, "Debit")
		self.assertEqual(rows[2].amount, 118700.0)
		self.assertEqual(rows[2].direction, "Debit")
		self.assertEqual(rows[2].reference_no, "REF123")

	def test_date_range_filter_excludes_out_of_range_rows(self):
		rows = parse_statement_file(
			self.bank_account.name, self.setting.name, self.file_url,
			date(2026, 7, 2), date(2026, 7, 31),
		)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].amount, 118700.0)

	def test_missing_column_in_header_throws(self):
		bad_setting = frappe.get_doc({
			"doctype": "TMS Bank Reconciliation Setting",
			"bank_account": self.bank_account.name,
			"header_row": 4,
			"data_start_row": 6,
			"transaction_date_column": "Value Date",  # not present in the sample header
			"debit_column": "Withdrawal Amt (INR)",
			"credit_column": "Deposit Amt (INR)",
		})
		with self.assertRaises(frappe.ValidationError):
			parse_statement_file(
				self.bank_account.name, None, self.file_url,
				date(2026, 7, 1), date(2026, 7, 31),
				setting_doc=bad_setting,
			)

	def test_account_number_validation_passes_when_last_digits_match(self):
		frappe.db.set_value("Account Head", self.bank_account.name, "bank_ac_last_digits", "2881")
		rows = parse_statement_file(
			self.bank_account.name, self.setting.name, self.file_url,
			date(2026, 7, 1), date(2026, 7, 31),
		)
		self.assertEqual(len(rows), 3)

	def test_account_number_validation_throws_on_mismatch(self):
		"""The sample file's letterhead has 'A/C No:,084405002881' — setting a
		different last-digits value on the Account Head must be caught, not
		silently produce an all-Unmatched result."""
		frappe.db.set_value("Account Head", self.bank_account.name, "bank_ac_last_digits", "9999")
		with self.assertRaises(frappe.ValidationError):
			parse_statement_file(
				self.bank_account.name, self.setting.name, self.file_url,
				date(2026, 7, 1), date(2026, 7, 31),
			)

	def test_account_number_validation_skipped_when_last_digits_blank(self):
		"""No bank_ac_last_digits set on the Account Head -> nothing to check
		against, so parsing proceeds same as before this field existed."""
		frappe.db.set_value("Account Head", self.bank_account.name, "bank_ac_last_digits", "")
		rows = parse_statement_file(
			self.bank_account.name, self.setting.name, self.file_url,
			date(2026, 7, 1), date(2026, 7, 31),
		)
		self.assertEqual(len(rows), 3)

	def test_balance_column_not_configured_leaves_balance_none(self):
		"""self.setting has no balance_column set — every row's `balance`
		stays None, same as before this field existed."""
		rows = parse_statement_file(
			self.bank_account.name, self.setting.name, self.file_url,
			date(2026, 7, 1), date(2026, 7, 31),
		)
		self.assertTrue(all(row.balance is None for row in rows))

	def test_balance_column_parses_running_balance_per_row(self):
		setting = frappe.get_doc({
			"doctype": "TMS Bank Reconciliation Setting",
			"bank_account": self.bank_account.name,
			"header_row": 4,
			"data_start_row": 6,
			"transaction_date_column": "Transaction Date",
			"debit_column": "Withdrawal Amt (INR)",
			"credit_column": "Deposit Amt (INR)",
			"balance_column": "Balance (INR)",
		})
		file_doc = save_file(
			"test_statement_with_balance.csv",
			SAMPLE_STATEMENT_CSV_WITH_BALANCE.encode("utf-8"),
			"TMS Bank Reconciliation Setting", self.setting.name, is_private=1,
		)
		rows = parse_statement_file(
			self.bank_account.name, None, file_doc.file_url,
			date(2026, 7, 1), date(2026, 7, 31),
			setting_doc=setting,
		)
		self.assertEqual(len(rows), 3)
		self.assertEqual(rows[0].balance, 900000.0)
		self.assertEqual(rows[1].balance, 883675.0)
		self.assertEqual(rows[2].balance, 764975.0)

	def test_extract_statement_footer_balances_reads_page_total(self):
		"""Real ICICI exports carry a 'Page Total' footer with explicit
		'Opening Bal:'/'Closing Bal:' rows — extract those directly rather
		than deriving them, since they reflect the whole statement's true
		balances regardless of header_row/data_start_row."""
		file_doc = save_file(
			"test_statement_with_footer.csv",
			SAMPLE_STATEMENT_CSV_WITH_FOOTER.encode("utf-8"),
			"TMS Bank Reconciliation Setting", self.setting.name, is_private=1,
		)
		opening, closing = extract_statement_footer_balances(file_doc.file_url)
		self.assertEqual(opening, 693569.39)
		self.assertEqual(closing, 596033.39)

	def test_extract_statement_footer_balances_none_when_no_footer(self):
		opening, closing = extract_statement_footer_balances(self.file_url)
		self.assertIsNone(opening)
		self.assertIsNone(closing)

	def test_compute_opening_closing_balance_derives_from_first_and_last_row(self):
		parsed = [
			frappe._dict(row_number=1, transaction_date=date(2026, 7, 1), amount=400000.0, direction="Credit", balance=900000.0),
			frappe._dict(row_number=2, transaction_date=date(2026, 7, 1), amount=16325.0, direction="Debit", balance=883675.0),
			frappe._dict(row_number=3, transaction_date=date(2026, 7, 3), amount=118700.0, direction="Debit", balance=764975.0),
		]
		opening, closing = compute_opening_closing_balance(parsed)
		self.assertEqual(opening, 500000.0)
		self.assertEqual(closing, 764975.0)

	def test_compute_opening_closing_balance_none_when_no_balance_column(self):
		parsed = [
			frappe._dict(row_number=1, transaction_date=date(2026, 7, 1), amount=400000.0, direction="Credit", balance=None),
		]
		opening, closing = compute_opening_closing_balance(parsed)
		self.assertIsNone(opening)
		self.assertIsNone(closing)


class IntegrationTestMatchTransactions(IntegrationTestCase):
	def setUp(self):
		self.bank_account = frappe.get_doc({
			"doctype": "Account Head",
			"name1": "Test Match Bank Account",
			"group": "BANK",
		}).insert(ignore_permissions=True)
		self.vendor = frappe.db.get_value("Supplier", {"supplier_group": "Vendor"}, "name")
		if not self.vendor:
			self.skipTest("No Supplier with supplier_group=Vendor found on this site — needed to create test Vendor Payments.")
		self.company = frappe.db.get_value("Vendor Payment", {}, "company") or frappe.defaults.get_defaults().get("company")
		self.customer = frappe.db.get_value("Customer", {}, "name")

	def tearDown(self):
		frappe.db.delete("Vendor Payment", {"paid_from_account": self.bank_account.name})
		frappe.db.delete("Receipt", {"paid_from_account": self.bank_account.name})
		frappe.db.delete("Repair Expenses", {"bank_name": self.bank_account.name})
		self.bank_account.delete()

	def _make_vendor_payment(self, posting_date, transfer_amount, is_reconciled=0):
		# A trips row with no `trip` set skips both the Trip-lookup in
		# before_insert's _enrich_manual_trip_rows() and the tds/lr_money
		# lookups in _recalculate_totals() (both guarded by `if row.trip`),
		# so total_transfer_amount ends up exactly equal to payment_amount —
		# no real Trip record needed for these matching-engine tests.
		vp = frappe.get_doc({
			"doctype": "Vendor Payment",
			"company": self.company,
			"payment_date": posting_date,
			"vendor": self.vendor,
			"from_date": posting_date,
			"to_date": posting_date,
			"mode_of_payment": "Bank Transfer",
			"paid_from_account": self.bank_account.name,
			"reference_no": f"TEST-{frappe.generate_hash(length=8)}",
			"ignore_validations": 1,
			"trips": [{"payment_amount": transfer_amount}],
		}).insert(ignore_permissions=True)
		# Vendor Payment.on_submit() -> _update_trip_payment_status() needs a
		# real Trip for every trips row regardless of ignore_validations, but
		# these matching-engine tests only care about docstatus/paid_from_account/
		# payment_date/total_transfer_amount, so set docstatus directly instead
		# of running the full submit flow.
		frappe.db.set_value("Vendor Payment", vp.name, "docstatus", 1)
		if is_reconciled:
			frappe.db.set_value("Vendor Payment", vp.name, "is_reconciled", 1)
		return vp.name

	def _make_repair_expense(self, expense_date, amount):
		# `amount` is read-only — RepairExpenses.before_save() recomputes it
		# as sum(repair_items.amount), so the test amount has to come in via
		# a repair_items row (qty=1, rate=amount), not the field directly.
		doc = frappe.get_doc({
			"doctype": "Repair Expenses",
			"date": expense_date,
			"vehicle_id": frappe.db.get_value("Vehicle", {}, "name"),
			"odometer": 1000,
			"payment_mode": "Bank Transfer",
			"bank_name": self.bank_account.name,
			"repair_items": [{"qty": 1, "rate": amount}],
		}).insert(ignore_permissions=True, ignore_mandatory=True)
		return doc.name

	def test_single_exact_match(self):
		vp_name = self._make_vendor_payment("2026-07-03", 118700.0)
		parsed = [frappe._dict(row_number=1, transaction_date=date(2026, 7, 3), amount=118700.0, direction="Debit", narration="", reference_no="")]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Matched")
		self.assertEqual(results[0].matched_doctype, "Vendor Payment")
		self.assertEqual(results[0].matched_docname, vp_name)

	def test_no_match_is_unmatched(self):
		parsed = [frappe._dict(row_number=1, transaction_date=date(2026, 7, 3), amount=999999.0, direction="Debit", narration="", reference_no="")]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Unmatched")
		self.assertIsNone(results[0].matched_docname)

	def test_two_payments_same_amount_and_date_auto_resolves_to_earlier_one(self):
		"""A single statement row that collides with 2 same-source candidates
		is no longer left Ambiguous — it auto-resolves to the earlier-created
		(FIFO) candidate, per TMS Reconciliation Source priority + creation
		order."""
		vp1 = self._make_vendor_payment("2026-07-03", 50000.0)
		self._make_vendor_payment("2026-07-03", 50000.0)
		parsed = [frappe._dict(row_number=1, transaction_date=date(2026, 7, 3), amount=50000.0, direction="Debit", narration="", reference_no="")]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Matched")
		self.assertEqual(results[0].matched_docname, vp1)

	def test_two_ambiguous_rows_same_key_split_fifo_across_two_candidates(self):
		"""2 statement rows sharing the same (date, amount) key, with exactly 2
		same-source candidates available, each get a distinct candidate —
		row 1 gets the earlier-created payment, row 2 the later one — and
		neither candidate is reused."""
		vp1 = self._make_vendor_payment("2026-07-03", 50000.0)
		vp2 = self._make_vendor_payment("2026-07-03", 50000.0)
		parsed = [
			frappe._dict(row_number=1, transaction_date=date(2026, 7, 3), amount=50000.0, direction="Debit", narration="", reference_no=""),
			frappe._dict(row_number=2, transaction_date=date(2026, 7, 3), amount=50000.0, direction="Debit", narration="", reference_no=""),
		]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Matched")
		self.assertEqual(results[1].status, "Matched")
		self.assertEqual(results[0].matched_docname, vp1)
		self.assertEqual(results[1].matched_docname, vp2)
		self.assertNotEqual(results[0].matched_docname, results[1].matched_docname)

	def test_rows_outnumbering_candidates_leaves_extras_unmatched(self):
		"""3 statement rows sharing a key but only 2 real candidates: the
		first 2 (row order) auto-resolve via priority+FIFO, the 3rd has no
		candidate left to assign — Unmatched, not a false Matched (which
		would reuse one of the first 2 rows' own candidate) and not a
		misleading Ambiguous (no candidate exists for it specifically to
		choose between — the eligible pool is genuinely exhausted)."""
		self._make_vendor_payment("2026-07-03", 50000.0)
		self._make_vendor_payment("2026-07-03", 50000.0)
		parsed = [
			frappe._dict(row_number=1, transaction_date=date(2026, 7, 3), amount=50000.0, direction="Debit", narration="", reference_no=""),
			frappe._dict(row_number=2, transaction_date=date(2026, 7, 3), amount=50000.0, direction="Debit", narration="", reference_no=""),
			frappe._dict(row_number=3, transaction_date=date(2026, 7, 3), amount=50000.0, direction="Debit", narration="", reference_no=""),
		]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Matched")
		self.assertEqual(results[1].status, "Matched")
		self.assertEqual(results[2].status, "Unmatched")
		self.assertIsNone(results[2].matched_docname)

	def test_cross_doctype_same_amount_and_date_resolved_by_source_sequence(self):
		"""A Vendor Payment and a Repair Expenses record sharing the exact
		same (date, amount) against the same bank account both match the same
		statement row — the auto-resolver picks the one from the
		lower-sequence TMS Reconciliation Source (Vendor Payment) over the
		higher-sequence one (Repair Expenses)."""
		vp_name = self._make_vendor_payment("2026-07-05", 30000.0)
		self._make_repair_expense("2026-07-05", 30000.0)
		parsed = [frappe._dict(row_number=1, transaction_date=date(2026, 7, 5), amount=30000.0, direction="Debit", narration="", reference_no="")]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Matched")
		self.assertEqual(results[0].matched_doctype, "Vendor Payment")
		self.assertEqual(results[0].matched_docname, vp_name)

	def test_already_reconciled_payment_is_excluded_from_new_matching(self):
		"""An already-reconciled record is never picked as a fresh Matched
		candidate again (excluded from the eligible pool)."""
		self._make_vendor_payment("2026-07-03", 118700.0, is_reconciled=1)
		parsed = [frappe._dict(row_number=1, transaction_date=date(2026, 7, 3), amount=118700.0, direction="Debit", narration="", reference_no="")]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertNotEqual(results[0].status, "Matched")

	def test_already_reconciled_payment_shows_unmatched(self):
		"""A previously-reconciled payment must be re-matched manually like any
		other row on a fresh upload — it shows 'Unmatched', not a distinct
		status that would let it skip the mandatory match-before-submit rule."""
		self._make_vendor_payment("2026-07-03", 118700.0, is_reconciled=1)
		parsed = [frappe._dict(row_number=1, transaction_date=date(2026, 7, 3), amount=118700.0, direction="Debit", narration="", reference_no="")]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Unmatched")
		self.assertIsNone(results[0].matched_docname)

	def test_credit_row_only_matches_receipt_not_vendor_payment(self):
		"""A Vendor Payment and a Receipt sharing (date, amount) must not
		cross-match: a Credit-direction statement row only checks Receipt
		(money coming in), never Vendor Payment (money going out), even if
		amounts coincide."""
		if not self.customer:
			self.skipTest("No Customer found on this site.")
		self._make_vendor_payment("2026-07-06", 75000.0)
		receipt = frappe.get_doc({
			"doctype": "Receipt",
			"company": self.company,
			"payment_date": "2026-07-06",
			"customer": self.customer,
			"from_date": "2026-07-06",
			"to_date": "2026-07-06",
			"trip_type": frappe.db.get_value("Trip Type", {}, "name"),
			"mode_of_payment": "Bank Transfer",
			"paid_from_account": self.bank_account.name,
			"reference_no": f"TEST-RCT-{frappe.generate_hash(length=8)}",
			"ignore_validations": 1,
			# A trips row with no `trip` set skips the Trip-lookup in
			# _enrich_manual_trip_rows() (guarded by `if row.trip`) and
			# ignore_validations=1 skips _validate_trips(); _recalculate_totals()
			# then sums received_amount straight into total_received_amount.
			"trips": [{"received_amount": 75000.0}],
		}).insert(ignore_permissions=True)
		frappe.db.set_value("Receipt", receipt.name, "docstatus", 1)

		parsed = [frappe._dict(row_number=1, transaction_date=date(2026, 7, 6), amount=75000.0, direction="Credit", narration="", reference_no="")]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Matched")
		self.assertEqual(results[0].matched_doctype, "Receipt")
		self.assertEqual(results[0].matched_docname, receipt.name)
		frappe.db.delete("Receipt", {"name": receipt.name})

	def test_get_eligible_records_keys_by_date_and_amount(self):
		vp_name = self._make_vendor_payment("2026-07-05", 25000.0)
		debit_map, credit_map = get_eligible_records(self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		candidates = debit_map[(date(2026, 7, 5), 25000.0)]
		self.assertIn((frappe.db.get_value("TMS Reconciliation Source", {"target_doctype": "Vendor Payment"}, "name"), "Vendor Payment", vp_name), candidates)

	def test_non_submittable_source_ignores_docstatus(self):
		"""Repair Expenses is not submittable — its docstatus is always 0.
		requires_submitted=0 on its TMS Reconciliation Source row must be
		respected, or it would never be found eligible."""
		repair_name = self._make_repair_expense("2026-07-07", 8000.0)
		parsed = [frappe._dict(row_number=1, transaction_date=date(2026, 7, 7), amount=8000.0, direction="Debit", narration="", reference_no="")]
		results = match_transactions(parsed, self.bank_account.name, date(2026, 7, 1), date(2026, 7, 31))
		self.assertEqual(results[0].status, "Matched")
		self.assertEqual(results[0].matched_doctype, "Repair Expenses")
		self.assertEqual(results[0].matched_docname, repair_name)
