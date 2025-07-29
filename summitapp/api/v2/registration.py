import frappe
from summitapp.summitapp.customizations.user.utils import signup, change_passwords, reset_passwords, reset_link, registration, subscriber


# Customer Signup
@frappe.whitelist
def customer_signup(kwargs):
	return signup(kwargs)

# Change Password
@frappe.whitelist
def change_password(kwargs):
	return change_passwords(kwargs)

# Reset Password
@frappe.whitelist()
def reset_password(kwargs):
	return reset_passwords(kwargs)

# Send reset password link on email
@frappe.whitelist()
def send_reset_link(kwargs):
	return reset_link(kwargs)


# Registration
@frappe.whitelist()
def create_registration(kwargs):
	return registration(kwargs)


# Add subcriber
@frappe.whitelist()
def add_subscriber(kwargs):
	return subscriber(kwargs)
