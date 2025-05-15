import frappe
from summitapp.api.v2.utils import success_response, error_response

@frappe.whitelisted()
def get_promotional_scheme_items(**kwargs):
    try:
        scheme = kwargs.get("scheme")
        if not scheme:
            return error_response("Scheme is required")

        items = frappe.get_all(
            "Pricing Rule Item Code",
            filters={"parent": scheme},
            fields=["item_code"]
        )
        return success_response(items)
    except Exception as e:
        return error_response(f"Error fetching items: {str(e)}")

@frappe.whitelisted()
def get_promotional_scheme():
    try:
        promotional_schemes = frappe.get_list("Promotional Scheme", fields=["name"])
        return success_response(promotional_schemes)
    except Exception as e:
        return error_response(f"Error fetching schemes: {str(e)}")
