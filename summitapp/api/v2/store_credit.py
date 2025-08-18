import frappe
from summitapp.summitapp.doctype.store_credit_assigned.utils import update_store_credit, delete_store_credit

# Add store credit
@frappe.whitelist()
def put(kwargs):
    return update_store_credit(kwargs)


# Delete Store Credit
@frappe.whitelist()
def delete(kwargs):
    return delete_store_credit(kwargs)