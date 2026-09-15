from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    # Employee form: rename "Emergency Contact" section to "Next of Kind
    # Details", matching the Driver form's Next of Kind Details naming.
    make_property_setter(
        "Employee", "emergency_contact_details", "label", "Next of Kind Details", "Data"
    )
    # "Relation" (e.g. "brother") -> "Next of Kind"
    make_property_setter("Employee", "relation", "label", "Next of Kind", "Data")
    # "Emergency Contact Name" -> "NOK Name"
    make_property_setter(
        "Employee", "person_to_be_contacted", "label", "NOK Name", "Data"
    )
    # "Emergency Phone" -> "NOK Mobile"
    make_property_setter(
        "Employee", "emergency_phone_number", "label", "NOK Mobile", "Data"
    )
