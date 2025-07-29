import frappe
from summitapp.summitapp.customizations.brand.utils import get_brand_list, get_list, get_details

@frappe.whitelist(allow_guest=True)
def get(kwargs):
    return get_brand_list(kwargs)


@frappe.whitelist(allow_guest=True)
def get_product_list(kwargs):
    return get_list(kwargs)


@frappe.whitelist(allow_guest=True)
def get_product_details(kwargs):
    return get_details(kwargs)

