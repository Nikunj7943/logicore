# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.file_manager import save_file

from logicore.utils.bank_reconciliation_utils import get_matched_record_table

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = []

SAMPLE_STATEMENT_CSV = (
	"Detailed Statement,,,,,\n"
	"S.N.,Transaction Date,Cheque. No./Ref. No.,Transaction Remarks,Withdrawal Amt (INR),Deposit Amt (INR),Balance (INR)\n"
	'1,03/Jul/2026,,MMT/IMPS/618416268165/Advfor2veh/AtharKhan,"1,18,700.00",,"5,00,000.00"\n'
)


class IntegrationTestTMSBankReconciliation(IntegrationTestCase):
	def setUp(self):
		self.bank_account = frappe.get_doc({
			"doctype": "Account Head",
			"name1": "Test Recon Doc Bank Account",
			"group": "BANK",
		}).insert(ignore_permissions=True)
		self.setting = frappe.get_doc({
			"doctype": "TMS Bank Reconciliation Setting",
			"bank_account": self.bank_account.name,
			"header_row": 2,
			"data_start_row": 3,
			"transaction_date_column": "Transaction Date",
			"debit_column": "Withdrawal Amt (INR)",
			"credit_column": "Deposit Amt (INR)",
			"narration_column": "Transaction Remarks",
			"reference_column": "Cheque. No./Ref. No.",
			"balance_column": "Balance (INR)",
		}).insert(ignore_permissions=True)
		self.vendor = frappe.db.get_value("Supplier", {"supplier_group": "Vendor"}, "name")
		if not self.vendor:
			self.skipTest("No Supplier with supplier_group=Vendor found on this site.")
		self.company = frappe.db.get_value("Vendor Payment", {}, "company") or frappe.defaults.get_defaults().get("company")
		self.vendor_payment = frappe.get_doc({
			"doctype": "Vendor Payment",
			"company": self.company,
			"payment_date": "2026-07-03",
			"vendor": self.vendor,
			"from_date": "2026-07-03",
			"to_date": "2026-07-03",
			"mode_of_payment": "Bank Transfer",
			"paid_from_account": self.bank_account.name,
			"reference_no": f"TEST-{frappe.generate_hash(length=8)}",
			"ignore_validations": 1,
			"trips": [{"payment_amount": 118700.0}],
		}).insert(ignore_permissions=True)
		# Vendor Payment.on_submit() -> _update_trip_payment_status() needs a
		# real Trip for every trips row regardless of ignore_validations; this
		# test only needs a submitted Vendor Payment to match against, so set
		# docstatus directly instead of running the full submit flow.
		frappe.db.set_value("Vendor Payment", self.vendor_payment.name, "docstatus", 1)
		self.vendor_payment.reload()
		file_doc = save_file(
			"test_recon_statement.csv", SAMPLE_STATEMENT_CSV.encode("utf-8"),
			"TMS Bank Reconciliation Setting", self.setting.name, is_private=1,
		)
		self.file_url = file_doc.file_url

	def tearDown(self):
		frappe.db.set_value("Vendor Payment", self.vendor_payment.name, "docstatus", 2)
		frappe.db.delete("Vendor Payment", {"name": self.vendor_payment.name})
		frappe.db.delete("TMS Bank Reconciliation Setting", {"bank_account": self.bank_account.name})
		self.bank_account.delete()

	def _make_reconciliation(self):
		return frappe.get_doc({
			"doctype": "TMS Bank Reconciliation",
			"company": self.company,
			"bank_account": self.bank_account.name,
			"reconciliation_setting": self.setting.name,
			"from_date": "2026-07-01",
			"to_date": "2026-07-31",
			"statement_file": self.file_url,
		}).insert(ignore_permissions=True)

	def test_parse_and_match_populates_transactions(self):
		recon = self._make_reconciliation()
		recon.parse_and_match()
		recon.reload()
		self.assertEqual(recon.total_transactions, 1)
		self.assertEqual(recon.matched_count, 1)
		self.assertEqual(recon.transactions[0].matched_doctype, "Vendor Payment")
		self.assertEqual(recon.transactions[0].matched_docname, self.vendor_payment.name)

	def test_parse_and_match_computes_opening_and_closing_balance(self):
		"""The sample file's single Debit row (₹1,18,700) leaves a running
		Balance of ₹5,00,000 — Closing Balance is that value directly, and
		Opening Balance backs out the Debit to get the balance before it."""
		recon = self._make_reconciliation()
		recon.parse_and_match()
		recon.reload()
		self.assertEqual(recon.opening_balance, 618700.0)
		self.assertEqual(recon.closing_balance, 500000.0)

	def test_get_matched_record_table_excludes_outside_date_range(self):
		recon = frappe.get_doc({
			"doctype": "TMS Bank Reconciliation",
			"company": self.company,
			"bank_account": self.bank_account.name,
			"reconciliation_setting": self.setting.name,
			"from_date": "2026-08-01",
			"to_date": "2026-08-31",
			"statement_file": self.file_url,
		}).insert(ignore_permissions=True)
		data = get_matched_record_table("Vendor Payment", recon.name)
		names = [row["name"] for row in data["rows"]]
		self.assertNotIn(self.vendor_payment.name, names)

	def test_get_matched_record_table_search_matches_vendor_and_reference_no(self):
		"""txt must search every shown column, not just the ID — typing the
		vendor's name or the reference number should both find the row."""
		recon = self._make_reconciliation()

		by_vendor = get_matched_record_table("Vendor Payment", recon.name, txt=self.vendor)
		self.assertIn(self.vendor_payment.name, [row["name"] for row in by_vendor["rows"]])

		by_reference = get_matched_record_table(
			"Vendor Payment", recon.name, txt=self.vendor_payment.reference_no
		)
		self.assertEqual([row["name"] for row in by_reference["rows"]], [self.vendor_payment.name])

	def test_get_matched_record_table_search_matches_displayed_date_format(self):
		"""payment_date is stored as 2026-07-03 but shown/typed as dd-mm-yyyy
		(03-07-2026) — searching in that displayed format must still match,
		not just the raw ISO substring."""
		recon = self._make_reconciliation()
		data = get_matched_record_table("Vendor Payment", recon.name, txt="03-07-2026")
		self.assertIn(self.vendor_payment.name, [row["name"] for row in data["rows"]])

	def test_get_matched_record_table_returns_columns_and_rows(self):
		"""The table-picker dialog's data source: proper column labels (not raw
		fieldnames) plus row dicts keyed by those same fieldnames."""
		recon = self._make_reconciliation()
		data = get_matched_record_table("Vendor Payment", recon.name)
		self.assertEqual(data["target_doctype"], "Vendor Payment")
		fieldnames = [c["fieldname"] for c in data["columns"]]
		self.assertEqual(fieldnames, ["name", "payment_date", "total_transfer_amount", "vendor", "reference_no"])
		self.assertIn("Vendor", [c["label"] for c in data["columns"]])

		row = next(r for r in data["rows"] if r["name"] == self.vendor_payment.name)
		self.assertEqual(row["payment_date"], "03-07-2026")
		self.assertEqual(row["vendor"], self.vendor)

	def test_get_matched_record_table_empty_when_source_missing(self):
		recon = self._make_reconciliation()
		data = get_matched_record_table("", recon.name)
		self.assertEqual(data, {"target_doctype": None, "columns": [], "rows": []})

	def test_submit_flags_vendor_payment_and_cancel_reverses(self):
		recon = self._make_reconciliation()
		recon.parse_and_match()
		recon.reload()
		recon.submit()
		self.assertEqual(frappe.db.get_value("Vendor Payment", self.vendor_payment.name, "is_reconciled"), 1)
		self.assertEqual(frappe.db.get_value("Vendor Payment", self.vendor_payment.name, "bank_reconciliation"), recon.name)

		recon.cancel()
		self.assertEqual(frappe.db.get_value("Vendor Payment", self.vendor_payment.name, "is_reconciled"), 0)
		self.assertFalse(frappe.db.get_value("Vendor Payment", self.vendor_payment.name, "bank_reconciliation"))

	def test_submit_blocked_with_no_transactions(self):
		"""Submitting without ever running Parse & Match (empty transactions
		table) must be blocked too — there is nothing to have matched."""
		recon = self._make_reconciliation()
		with self.assertRaises(frappe.ValidationError):
			recon.submit()

	def test_submit_blocked_while_unmatched_row_unresolved(self):
		"""Every row must be matched before submit — a plain Unmatched row
		with no matched_docname blocks submit."""
		recon = self._make_reconciliation()
		recon.parse_and_match()
		recon.reload()
		recon.transactions[0].status = "Unmatched"
		recon.transactions[0].matched_source = None
		recon.transactions[0].matched_docname = None
		recon.save()
		with self.assertRaises(frappe.ValidationError):
			recon.submit()
