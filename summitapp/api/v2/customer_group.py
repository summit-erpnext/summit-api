import frappe
from summitapp.utils import success_response, error_response

@frappe.whitelist()
def get_customer_group(kwrgs):
    customer_group = frappe.get_list("Customer Group", filters={"is_group":0}, fields=['name'])
    return success_response(customer_group)