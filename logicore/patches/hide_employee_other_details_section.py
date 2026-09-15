from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    # Hides the "Other Details" section (Aadhar Card, Driving License, License
    # Expiry Date) from the Employee form. Fields and their data are kept —
    # "HR Driver License Status" chart and "HR Driver License Expired" number
    # card still read custom_driving_license / custom_license_expiry_date.
    make_property_setter("Employee", "custom_other_details", "hidden", "1", "Check")
