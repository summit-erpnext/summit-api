import frappe
from summitapp.summitapp.customizations.customer_group.utils import get_dealer_list

@frappe.whitelist()
def get_dealer(kwargs):
    return get_dealer_list(kwargs)