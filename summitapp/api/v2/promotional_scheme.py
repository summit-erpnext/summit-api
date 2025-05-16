import frappe
from summitapp.api.v2.utils import success_response, error_response
from summitapp.api.v2.product import get_details

@frappe.whitelist(allow_guest=True)
def get_promotional_scheme_items(kwargs):
    try:
        scheme = kwargs.get("scheme")

        if not scheme:
            return error_response("Scheme is required")

        items = frappe.get_all(
            "Pricing Rule Item Code",
            filters={"parent": scheme},
            fields=["item_code"]
        )

        detailed_items = []
        for item in items:
            item_kwargs = {
                "item": item.item_code
            }
            item_detail = get_details(item_kwargs)
            # Ensure it returns data properly and filter errors
            if item_detail and item_detail.get("msg") == "Success":
                detailed_items.append(item_detail.get("data"))

        return success_response(detailed_items)

    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(f"Error fetching items: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_promotional_scheme(kwargs):
    try:
        promotional_schemes = frappe.get_list("Promotional Scheme", fields=["name"])
        return success_response(promotional_schemes)
    except Exception as e:
        return error_response(f"Error fetching schemes: {str(e)}")
