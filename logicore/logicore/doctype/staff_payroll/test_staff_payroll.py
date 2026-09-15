# Copyright (c) 2026, LogiCore and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
# Skip auto-generated Company/Fiscal Year test records — this site already
# has real Company/Fiscal Year data, and Frappe's standard test-record
# generator creates an overlapping "_Test Fiscal Year 2025" that conflicts
# with it. Tests use _get_company() to reuse an existing Company instead.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Company", "Fiscal Year"]


class IntegrationTestStaffPayroll(IntegrationTestCase):
	"""
	Integration tests for StaffPayroll.
	Use this class for testing interactions between multiple components.
	"""

	def _get_company(self):
		company = frappe.db.get_value("Company", {}, "name")
		self.assertTrue(company, "No Company found in the test site — required for Staff Payroll tests")
		return company

	def _insert_as_import(self, doc):
		"""Insert a doc the same way Frappe's standard Data Import does —
		with frappe.flags.in_import set — so the import-only auto-fetch in
		staff_payroll.py's before_save() actually runs."""
		frappe.flags.in_import = True
		try:
			doc.insert(ignore_permissions=True)
		finally:
			frappe.flags.in_import = False
		return doc

	def _make_driver(self, company, ctc=300000):
		driver = frappe.get_doc({
			"doctype": "Driver",
			"full_name": "Test Import Driver",
			"custom_ctc": ctc,
			"custom_company": company,
		})
		driver.insert(ignore_permissions=True)
		return driver

	def _make_staff_attendance(self, company, link_doctype, person_name, date, status):
		att = frappe.get_doc({
			"doctype": "Staff Attendance",
			"date": date,
			"company": company,
			"attendance_details": [{
				"link_doctype": link_doctype,
				"employee_link": person_name,
				"status": status,
			}],
		})
		att.insert(ignore_permissions=True)
		return att

	def _make_driver_advance(self, company, driver_name, amount, date):
		payment = frappe.get_doc({
			"doctype": "Payment",
			"date": date,
			"type": "Driver Advance",
			"company": company,
			"mode_of_payment": "Cash",
			"driver": driver_name,
			"amount": amount,
		})
		payment.insert(ignore_permissions=True)
		payment.submit()
		return payment

	def _make_gender(self):
		gender = frappe.db.get_value("Gender", {}, "name")
		if gender:
			return gender
		doc = frappe.get_doc({"doctype": "Gender", "gender": "Test Gender"})
		doc.insert(ignore_permissions=True)
		return doc.name

	def _make_employee(self, company, ctc=300000):
		employee = frappe.get_doc({
			"doctype": "Employee",
			"first_name": "Test Import Employee",
			"company": company,
			"status": "Active",
			"gender": self._make_gender(),
			"date_of_birth": "1990-01-01",
			"date_of_joining": "2015-01-01",
			"ctc": ctc,
		})
		employee.insert(ignore_permissions=True)
		return employee

	def _make_employee_advance(self, company, employee_name, amount, date):
		payment = frappe.get_doc({
			"doctype": "Payment",
			"date": date,
			"type": "Employee Advance",
			"company": company,
			"mode_of_payment": "Cash",
			"employee": employee_name,
			"amount": amount,
		})
		payment.insert(ignore_permissions=True)
		payment.submit()
		return payment

	def test_driver_salary_auto_fetches_attendance_and_advance_on_import(self):
		company = self._get_company()
		driver = self._make_driver(company, ctc=300000)

		from_date = add_days(today(), -2)
		mid_date = add_days(today(), -1)
		to_date = today()
		self._make_staff_attendance(company, "Driver", driver.name, from_date, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, mid_date, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, to_date, "Absent")

		advance = self._make_driver_advance(company, driver.name, 5000, add_days(today(), -10))

		# Simulates what Frappe's standard Data Import produces: only the
		# person + period, no salary_type, no ctc/company, no attendance,
		# no advance rows — everything else must come from auto-fetch.
		payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": from_date,
			"to_date": to_date,
			"payroll_date": to_date,
			"payment_mode": "Bank Transfer",
		})
		self._insert_as_import(payroll)

		self.assertEqual(payroll.salary_type, "Driver Salary")
		self.assertEqual(payroll.company, company)
		self.assertEqual(payroll.ctc, 300000)
		self.assertEqual(payroll.present_days, 2)
		self.assertEqual(payroll.absent_days, 1)
		self.assertEqual(payroll.worked_days, 2)

		self.assertEqual(len(payroll.advance_recovery_table), 1)
		row = payroll.advance_recovery_table[0]
		self.assertEqual(row.payment_ref, advance.name)
		self.assertEqual(row.total_advance, 5000)
		self.assertEqual(row.recovery_amount, 5000)
		# already_recovered/outstanding are projected as "if this recovery_amount
		# is applied" by the pre-existing _update_advance_already_recovered()
		# logic (unchanged by this feature) — so outstanding is already 0 here.
		self.assertEqual(row.already_recovered, 5000)
		self.assertEqual(row.outstanding, 0)

		basic_salary_row = next(r for r in payroll.earnings_table if r.salary_component == "Basic Salary")
		self.assertEqual(basic_salary_row.amount, 20000)  # (300000 / 30 fixed days) * 2 worked days

		advances_row = next(r for r in payroll.deductions_table if r.salary_component == "Advances")
		self.assertEqual(advances_row.amount, 5000)

		self.assertEqual(payroll.net_salary, 15000)

	def test_employee_salary_auto_fetches_attendance_and_advance_on_import(self):
		company = self._get_company()
		employee = self._make_employee(company, ctc=300000)

		from_date = add_days(today(), -2)
		mid_date = add_days(today(), -1)
		to_date = today()
		self._make_staff_attendance(company, "Employee", employee.name, from_date, "Present")
		self._make_staff_attendance(company, "Employee", employee.name, mid_date, "Present")
		self._make_staff_attendance(company, "Employee", employee.name, to_date, "Absent")

		advance = self._make_employee_advance(company, employee.name, 4000, add_days(today(), -10))

		payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"employee": employee.name,
			"from_date": from_date,
			"to_date": to_date,
			"payroll_date": to_date,
			"payment_mode": "Bank Transfer",
		})
		self._insert_as_import(payroll)

		self.assertEqual(payroll.salary_type, "Employee Salary")
		self.assertEqual(payroll.company, company)
		self.assertEqual(payroll.ctc, 300000)
		self.assertEqual(payroll.present_days, 2)
		self.assertEqual(payroll.absent_days, 1)
		self.assertEqual(payroll.worked_days, 2)

		self.assertEqual(len(payroll.advance_recovery_table), 1)
		row = payroll.advance_recovery_table[0]
		self.assertEqual(row.payment_ref, advance.name)
		self.assertEqual(row.recovery_amount, 4000)
		self.assertEqual(row.outstanding, 0)

		basic_salary_row = next(r for r in payroll.earnings_table if r.salary_component == "Basic Salary")
		self.assertEqual(basic_salary_row.amount, 200000)  # (300000 / 3 actual days) * 2 worked days

		advances_row = next(r for r in payroll.deductions_table if r.salary_component == "Advances")
		self.assertEqual(advances_row.amount, 4000)

	def test_employee_salary_fetches_ctc_even_when_employee_name_is_prefilled(self):
		company = self._get_company()
		employee = self._make_employee(company, ctc=300000)

		payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"employee": employee.name,
			"employee_name": "Already Prefilled",
			"from_date": today(),
			"to_date": today(),
			"payroll_date": today(),
			"payment_mode": "Cash",
		})
		self._insert_as_import(payroll)

		self.assertEqual(payroll.employee_name, employee.employee_name)
		self.assertEqual(payroll.ctc, 300000)

	def test_old_data_import_preserves_component_amounts(self):
		company = self._get_company()
		driver = self._make_driver(company, ctc=300000)
		advance = self._make_driver_advance(company, driver.name, 2500, add_days(today(), -10))

		payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": today(),
			"to_date": today(),
			"payroll_date": today(),
			"payment_mode": "Cash",
			"earnings_table": [
				{"salary_component": "Basic Salary", "amount": 12345},
				{"salary_component": "Incentive", "amount": 1500},
			],
			"deductions_table": [
				{"salary_component": "Advances", "amount": 2500},
				{"salary_component": "Leave Deductions", "amount": 800},
			],
			"advance_recovery_table": [
				{
					"payment_ref": advance.name,
					"advance_date": advance.date,
					"total_advance": 2500,
					"already_recovered": 0,
					"outstanding": 2500,
					"recovery_amount": 2500,
				}
			],
		})
		payroll.flags.tms_old_data_import = True
		self._insert_as_import(payroll)

		basic_salary_row = next(r for r in payroll.earnings_table if r.salary_component == "Basic Salary")
		self.assertEqual(basic_salary_row.amount, 12345)
		incentive_row = next(r for r in payroll.earnings_table if r.salary_component == "Incentive")
		self.assertEqual(incentive_row.amount, 1500)
		advances_row = next(r for r in payroll.deductions_table if r.salary_component == "Advances")
		self.assertEqual(advances_row.amount, 2500)
		leave_row = next(r for r in payroll.deductions_table if r.salary_component == "Leave Deductions")
		self.assertEqual(leave_row.amount, 800)
		self.assertEqual(payroll.total_earnings, 13845)
		self.assertEqual(payroll.total_deductions, 3300)
		self.assertEqual(payroll.net_salary, 10545)
		self.assertEqual([row.salary_component for row in payroll.deductions_table], [
			"Advances",
			"Other Deductions",
			"Leave Deductions",
			"Paid Incentive",
		])
		self.assertTrue(
			frappe.db.exists(
				"Comment",
				{
					"reference_doctype": "Staff Payroll",
					"reference_name": payroll.name,
					"comment_type": "Info",
					"content": ["like", "%TMS_OLD_DATA_IMPORT%"],
				},
			)
		)

	def test_import_only_advances_ignore_future_payments(self):
		company = self._get_company()
		employee = self._make_employee(company, ctc=300000)
		driver = self._make_driver(company, ctc=300000)

		cutoff_date = "2022-05-31"
		old_date = "2022-05-10"
		future_date = "2026-07-01"

		old_employee_advance = self._make_employee_advance(company, employee.name, 1200, old_date)
		self._make_employee_advance(company, employee.name, 3400, future_date)
		old_driver_advance = self._make_driver_advance(company, driver.name, 2200, old_date)
		self._make_driver_advance(company, driver.name, 5600, future_date)

		employee_payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"employee": employee.name,
			"from_date": "2022-05-01",
			"to_date": cutoff_date,
			"payroll_date": cutoff_date,
			"payment_mode": "Cash",
		})
		self._insert_as_import(employee_payroll)

		self.assertEqual([row.payment_ref for row in employee_payroll.advance_recovery_table], [old_employee_advance.name])
		self.assertEqual(employee_payroll.advance_recovery_table[0].recovery_amount, 1200)

		driver_payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": "2022-05-01",
			"to_date": cutoff_date,
			"payroll_date": cutoff_date,
			"payment_mode": "Cash",
		})
		self._insert_as_import(driver_payroll)

		self.assertEqual([row.payment_ref for row in driver_payroll.advance_recovery_table], [old_driver_advance.name])
		self.assertEqual(driver_payroll.advance_recovery_table[0].recovery_amount, 2200)

	def test_advance_recovery_carries_forward_across_periods_when_submitted(self):
		company = self._get_company()
		driver = self._make_driver(company, ctc=300000)

		advance = self._make_driver_advance(company, driver.name, 5000, add_days(today(), -40))

		period1_from = add_days(today(), -32)
		period1_mid = add_days(today(), -31)
		period1_to = add_days(today(), -30)
		self._make_staff_attendance(company, "Driver", driver.name, period1_from, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, period1_mid, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, period1_to, "Present")

		payroll_1 = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": period1_from,
			"to_date": period1_to,
			"payroll_date": period1_to,
			"payment_mode": "Bank Transfer",
		})
		self._insert_as_import(payroll_1)
		self.assertEqual(payroll_1.advance_recovery_table[0].recovery_amount, 5000)

		# User reduces recovery to 3000 on the draft before submitting.
		payroll_1.advance_recovery_table[0].recovery_amount = 3000
		payroll_1.save(ignore_permissions=True)
		payroll_1.submit()

		period2_from = add_days(today(), -2)
		period2_mid = add_days(today(), -1)
		period2_to = today()
		self._make_staff_attendance(company, "Driver", driver.name, period2_from, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, period2_mid, "Present")
		self._make_staff_attendance(company, "Driver", driver.name, period2_to, "Present")

		payroll_2 = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": period2_from,
			"to_date": period2_to,
			"payroll_date": period2_to,
			"payment_mode": "Bank Transfer",
		})
		self._insert_as_import(payroll_2)

		self.assertEqual(len(payroll_2.advance_recovery_table), 1)
		row = payroll_2.advance_recovery_table[0]
		self.assertEqual(row.payment_ref, advance.name)
		# The real proof of carry-forward: get_driver_advances() defaulted
		# recovery_amount to the REMAINING outstanding (5000 - 3000 already
		# recovered by payroll_1), not the full original 5000.
		self.assertEqual(row.recovery_amount, 2000)

	def test_manual_creation_does_not_auto_fetch_attendance_or_advance(self):
		"""Same setup as the Driver Salary import test, but inserted WITHOUT
		frappe.flags.in_import — i.e. simulating a normal manual/API save.
		Attendance and advance auto-fetch must NOT happen here; only the
		pre-existing driver-detail fetch (ctc/company/branch/employee_name)
		should still run, exactly as it did before this feature."""
		company = self._get_company()
		driver = self._make_driver(company, ctc=300000)

		from_date = add_days(today(), -2)
		to_date = today()
		self._make_staff_attendance(company, "Driver", driver.name, from_date, "Present")
		self._make_driver_advance(company, driver.name, 5000, add_days(today(), -10))

		payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"salary_type": "Driver Salary",
			"driver": driver.name,
			"from_date": from_date,
			"to_date": to_date,
			"payroll_date": to_date,
			"payment_mode": "Bank Transfer",
		})
		payroll.insert(ignore_permissions=True)

		# Pre-existing behaviour (unrelated to this feature): driver details
		# still auto-fill because before_save always did this.
		self.assertEqual(payroll.company, company)
		self.assertEqual(payroll.ctc, 300000)

		# New behaviour must NOT fire outside of import.
		self.assertEqual(payroll.present_days, 0)
		self.assertEqual(payroll.worked_days, 0)
		self.assertEqual(len(payroll.advance_recovery_table), 0)

	def test_driver_salary_leave_deduction_drops_one_day_in_31_day_month(self):
		"""Driver Salary always prices a day at ctc/30. In a 31-day calendar
		month that pay basis is one day short of the days actually marked in
		Staff Attendance, so the extra day must not be charged as an absence —
		leave deduction should be for (leave_without_pay - 1) days, not the
		full count."""
		company = self._get_company()
		driver = self._make_driver(company, ctc=30000)

		from_date = "2019-05-01"
		to_date = "2019-05-31"  # 31-day month
		present_days = [add_days(from_date, i) for i in range(28)]
		absent_days = [add_days(from_date, i) for i in range(28, 31)]
		for d in present_days:
			self._make_staff_attendance(company, "Driver", driver.name, d, "Present")
		for d in absent_days:
			self._make_staff_attendance(company, "Driver", driver.name, d, "Absent")

		payroll = frappe.get_doc({
			"doctype": "Staff Payroll",
			"driver": driver.name,
			"from_date": from_date,
			"to_date": to_date,
			"payroll_date": to_date,
			"payment_mode": "Bank Transfer",
		})
		self._insert_as_import(payroll)

		self.assertEqual(payroll.present_days, 28)
		self.assertEqual(payroll.leave_without_pay, 3)
		self.assertEqual(payroll.salary_per_day, 1000)  # 30000 / 30 fixed days

		leave_row = next(r for r in payroll.deductions_table if r.salary_component == "Leave Deductions")
		self.assertEqual(leave_row.amount, 2000)  # (3 - 1 extra day) * 1000, not 3 * 1000
