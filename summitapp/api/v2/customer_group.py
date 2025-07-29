import frappe
from summitapp.summitapp.customizations.customer_group.utils import customer_group

# Get Customer Group
@frappe.whitelist()
def get_customer_group(kwargs):
    return customer_group(kwargs)