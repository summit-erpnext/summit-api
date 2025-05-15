import frappe
from summitapp.api.v2.utils import success_response, error_response

@frappe.whitelisted()
def get_promotional_scheme_items(kwargs):
    scheme = kwargs.get("scheme")
    items = frappe.get_all("Pricing Rule Item Code",filters={"parent":scheme},fields=["item_code"])


@frappe.whitelisted()
def get_promotional_scheme(kwargs):
    promotional_scheme = frappe.get_list("Promotional Scheme",fields=["name"])
    return success_response(promotional_scheme)