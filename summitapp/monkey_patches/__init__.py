from frappe.auth import CookieManager
from erpnext.selling.doctype.customer.customer import Customer
from summitapp.summitapp.customizations.customer.utils import _create_primary_contact, _create_primary_address

Customer.create_primary_contact = _create_primary_contact
Customer.create_primary_address = _create_primary_address