import frappe
from frappe.contacts.doctype.address.address import Address


class AddressOverride(Address):
    def autoname(self):
        # Fill address_title from custom_address_code before Frappe's mandatory check
        if not self.address_title and self.custom_address_code:
            self.address_title = self.custom_address_code
        super().autoname()


def before_save_fill_city_fields(doc, method=None):
    # Auto-set address_title from custom_address_code if not already set
    if not doc.address_title and doc.custom_address_code:
        doc.address_title = doc.custom_address_code

    # Auto-fill city/state/country from custom_cityname (City doctype link)
    if not doc.custom_cityname:
        return
    city = frappe.db.get_value(
        "City", doc.custom_cityname,
        ["name", "name1", "state", "country"],
        as_dict=True,
    )
    if not city:
        return
    doc.city    = city.name1 or city.name
    if city.state:
        doc.state = city.state
    if city.country:
        # Country is a case-sensitive Link elsewhere (india_compliance's
        # `country != "India"` checks), but City.country can be saved with
        # any casing since Link validation is case-insensitive. Resolve to
        # the Country doctype's exact-cased name so a mis-cased City can
        # never propagate into a new Address.
        doc.country = frappe.db.get_value("Country", city.country) or city.country


def after_insert_set_primary(doc, method=None):
    # Auto-primary rule: a new Address linked to a Customer who has no
    # customer_primary_address yet becomes that Customer's primary,
    # without requiring any checkbox tick. To change primary later, user
    # edits the Customer's customer_primary_address field directly
    # (Frappe core mechanism — ERPNext's Customer.on_update then syncs
    # is_primary_address flags on the related Address records).
    for link in (doc.get("links") or []):
        if link.link_doctype != "Customer" or not link.link_name:
            continue
        if frappe.db.get_value("Customer", link.link_name, "customer_primary_address"):
            continue
        frappe.db.set_value(
            "Customer", link.link_name, "customer_primary_address", doc.name
        )
        if not doc.is_primary_address:
            frappe.db.set_value("Address", doc.name, "is_primary_address", 1)
