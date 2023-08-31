from frappe.auth import CookieManager
from summitapp.overrides.auth import set_cookie

from erpnext.selling.doctype.customer.customer import Customer
from summitapp.overrides.customer import _create_primary_contact, _create_primary_address

CookieManager.set_cookie = set_cookie

Customer.create_primary_contact = _create_primary_contact
Customer.create_primary_address = _create_primary_address