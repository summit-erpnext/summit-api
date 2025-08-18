import frappe
from summitapp.summitapp.customizations.customer.utils import get_user_profile, create_customer_inquiry, get_ageing_report, transporters

# Get user profile
@frappe.whitelist()
def get_profile(kwargs):
	return get_user_profile(kwargs)

# Create customer inquiry
@frappe.whitelist()	
def customer_inquiry(kwargs):
	return create_customer_inquiry(kwargs)

# Get ageingreport
@frappe.whitelist()
def ageing_report(kwargs):
	return get_ageing_report(kwargs)

# Get transporters list
@frappe.whitelist()
def get_transporters(kwargs):
	return transporters(kwargs)