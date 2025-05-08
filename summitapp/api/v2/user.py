import requests
import frappe
from summitapp.utils import success_response, error_response

@frappe.whitelist(allow_guest=True)
def get_website_user(kwargs=None):
    if not kwargs:
        kwargs = frappe.form_dict

    parent_customer_group = kwargs.get("customer_group")

    # Get the Authorization header
    auth_token = frappe.local.request.headers.get("Authorization")

    if not parent_customer_group:
        return error_response("Please provide a customer_group")
    if not auth_token:
        return error_response("Authorization token missing in headers")

    # Get child customer groups
    child_customer_groups = frappe.get_all(
        "Customer Group",
        filters={"parent_customer_group": parent_customer_group},
        pluck="name"
    )

    if not child_customer_groups:
        return success_response([])

    # Fetch customers
    customers = frappe.get_all(
        "Customer",
        filters={"customer_group": ["in", child_customer_groups]},
        fields=["name", "customer_name", "email", "customer_group"]
    )

    result = []

    for customer in customers:
        company = get_company(customer["name"])
        credit_data = fetch_credit_balance_from_api(customer["name"], company, auth_token)
        loyalty_data = get_loyalty_collection_factor(customer["name"])
        
        # Merge data
        customer.update(credit_data)
        customer.update(loyalty_data)
        
        result.append(customer)

    return success_response(result)


def fetch_credit_balance_from_api(customer_name, company, auth_token):
    try:
        url = frappe.local.request.host_url.rstrip("/") + "/api/method/frappe.desk.query_report.run"
        payload = {
            "report_name": "Customer Credit Balance",
            "filters": {
                "customer": customer_name,
                "company": company
            }
        }
        headers = {
            'Authorization': auth_token,
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            rows = data.get("message", {}).get("result", [])
            if rows:
                row = rows[0]
                return {
                    "credit_limit": row.get("credit_limit", 0),
                    "outstanding_amount": row.get("outstanding_amount", 0)
                }
    except Exception as e:
        frappe.log_error(f"Error calling credit balance API for {customer_name}: {e}")

    return {"credit_limit": 0, "outstanding_amount": 0}


def get_company(customer_name):
    credit_limit_company = frappe.get_all(
        "Customer Credit Limit",
        filters={"parent": customer_name},
        fields=["company"]
    )
    if credit_limit_company:
        return credit_limit_company[0]["company"]
    return None


def get_loyalty_collection_factor(customer_name):
    # Get loyalty program from Customer
    loyalty_points = frappe.db.get_value("Customer", customer_name, "loyalty_points")
    return {"loyalty_points":loyalty_points}
   

@frappe.whitelist(allow_guest=True)
def get_mechanic(kwargs):
    mechanics = frappe.get_list("Customer",filters={"customer_group":"Mechanic"},fields=["name"])
    return success_response(mechanics)

from frappe import _

@frappe.whitelist(allow_guest=True)
def update_mechanic_in_customer(kwargs):
    email_id = kwargs.get("email_id")
    mechanic = kwargs.get("mechanic")

    if not email_id or not mechanic:
        return {"status": "error", "message": "email_id and mechanic are required."}

    customer = frappe.get_value("Customer", {"email_id": email_id}, "name")
    if not customer:
        return {"status": "error", "message": f"No customer found with email: {email_id}"}

    doc = frappe.get_doc("Customer", customer)
    doc.mechanic = mechanic
    doc.save(ignore_permissions=True)
    return {"status": "success", "message": "Mechanic updated successfully", "customer": doc.name}
