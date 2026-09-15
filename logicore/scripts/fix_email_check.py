import frappe

def execute():
    row = frappe.db.get_value("Server Script", "Employee User Automation-TMS Maintenance", "script")
    old = 'if not frappe.db.get_value("Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"):'
    new = 'if not frappe.db.get_value("Email Account", {"enable_outgoing": 1}, "name"):'
    if old in row:
        frappe.db.set_value("Server Script", "Employee User Automation-TMS Maintenance", "script", row.replace(old, new))
        frappe.db.commit()
        print("SUCCESS")
    else:
        print("Already updated or not found")
