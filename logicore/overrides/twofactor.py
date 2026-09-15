import frappe
from frappe import _


def send_token_via_email(user, token, otp_secret, otp_issuer, subject=None, message=None):
    """Custom 2FA email with employee info and styled template."""
    import pyotp

    user_doc = frappe.db.get_value("User", user,
        ["email", "full_name", "name"], as_dict=1)

    if not user_doc or not user_doc.email:
        return False

    hotp = pyotp.HOTP(otp_secret)
    otp = hotp.at(int(token))

    # Employee fetch — user_id, personal_email, company_email se try karo
    employee = (
        frappe.db.get_value("Employee", {"user_id": user}, ["name", "employee_name"], as_dict=1) or
        frappe.db.get_value("Employee", {"personal_email": user}, ["name", "employee_name"], as_dict=1) or
        frappe.db.get_value("Employee", {"company_email": user}, ["name", "employee_name"], as_dict=1)
    )

    employee_id = employee.name if employee else "N/A"
    employee_name = employee.employee_name if employee else user_doc.full_name

    # Email account fetch karo
    email_account = frappe.db.get_value("Email Account",
        {"default_outgoing": 1},
        ["email_id", "email_account_name"], as_dict=1)

    email_account_name = email_account.email_account_name if email_account else otp_issuer
    email_account_id = email_account.email_id if email_account else None

    company_name = frappe.defaults.get_user_default("company", user) or frappe.defaults.get_global_default("company")

    custom_subject = (
        "Verification code: {} for {} ({})".format(otp, email_account_name, company_name)
        if company_name
        else "Verification code: {} for {}".format(otp, email_account_name)
    )

    custom_message = """
    <div style="font-family: Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #2c3e50; padding: 20px; text-align: center;">
            <h2 style="color: #ffffff; margin: 0; font-size: 20px;">Verification Code</h2>
        </div>
        <div style="padding: 30px;">
            <p style="color: #333333; font-size: 16px;">Hello <strong>{employee_name}</strong>,</p>
            <p style="color: #555555; font-size: 14px;">Your login verification code is below. Do not share this with anyone.</p>
            <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 20px; margin: 25px 0; border-radius: 4px;">
                <p style="margin: 5px 0;"><strong>Employee ID:</strong> <span style="color: #007bff;">{employee_id}</span></p>
                <p style="margin: 5px 0;"><strong>Username:</strong> <span style="color: #007bff;">{user}</span></p>
                <p style="margin: 15px 0 5px 0;"><strong>Verification Code:</strong></p>
                <p style="font-family: monospace; font-size: 32px; font-weight: bold; background: #e9ecef; padding: 10px 20px; border-radius: 4px; display: inline-block; letter-spacing: 6px; color: #2c3e50;">{otp}</p>
            </div>
            <p style="color: #dc3545; font-size: 13px; margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px;">
                <strong>Security Note:</strong> This code is valid for a few minutes only. Do not share it with anyone.
            </p>
        </div>
        <div style="background-color: #0f2942; padding: 26px 36px; text-align: center;">
            <p style="margin: 0 0 12px 0; font-size: 11px; color: #93a5bd; letter-spacing: 0.5px; text-transform: uppercase;">Sent automatically by</p>
            <a href="https://www.logicore.com/products" target="_blank" style="display: inline-block; background-color: #ffffff; color: #0d3b66; font-weight: 800; font-size: 14px; letter-spacing: 0.2px; text-decoration: none; padding: 10px 22px; border-radius: 999px;">{email_account_name} &rarr;</a>
            <p style="margin: 14px 0 0 0; font-size: 11px; color: #5a7591;">Transforming Logistics with ERP &amp; Automation</p>
        </div>
    </div>
    """.format(
        employee_name=employee_name,
        employee_id=employee_id,
        user=user,
        otp=otp,
        email_account_name=email_account_name
    )

    frappe.sendmail(
        recipients=user_doc.email,
        sender='"{}" <{}>'.format(email_account_name, email_account_id) if email_account_id else None,
        subject=subject or custom_subject,
        message=message or custom_message,
        delayed=False,
        retry=3,
    )
    return True