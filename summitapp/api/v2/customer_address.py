import frappe
from summitapp.summitapp.customizations.address.utils import get_customer_address, update_customer_address, create_customer_from_guest

# Get Customer Address
@frappe.whitelist()
def get(kwargs):
	return get_customer_address(kwargs)


# Update Customer Address
@frappe.whitelist()
def put(kwargs):
	return update_customer_address(kwargs)


# Create Customer from Guest User
@frappe.whitelist()
def create_guest_to_customer(kwargs):
	return create_customer_from_guest(kwargs)