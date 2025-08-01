import frappe
from summitapp.summitapp.customizations.user.utils import website_user, mechanic, mechanic_in_customer

# Get Website User
@frappe.whitelist(allow_guest=True)
def get_website_user(kwargs=None):
    return website_user(kwargs)


# Get Mechanic
@frappe.whitelist(allow_guest=True)
def get_mechanic(kwargs):
    return mechanic(kwargs)


# Update Mechanic in customer
@frappe.whitelist(allow_guest=True)
def update_mechanic_in_customer(kwargs):
    return mechanic_in_customer(kwargs)