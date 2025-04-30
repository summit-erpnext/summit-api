import frappe
from summitapp.utils import success_response, error_response

@frappe.whitelist()
def get_website_user(kwargs):
    parent_customer_group = kwargs.get("customer_group")
    
    if not parent_customer_group:
        return error_response("Please provide a customer_group")

    # Get all child customer groups under the specified parent
    child_customer_groups = frappe.get_all(
        "Customer Group",
        filters={"parent_customer_group": parent_customer_group},
        pluck="name"
    )

    if not child_customer_groups:
        return success_response([])  # No customers if group doesn't exist

    # Fetch customers with the given role and in any of the child customer groups
    customers = frappe.get_all(
        "Customer",
        filters={
            "customer_group": ["in", child_customer_groups]
        },
        fields=["name","customer_name","email", "customer_group"]
    )

    return success_response(customers)
