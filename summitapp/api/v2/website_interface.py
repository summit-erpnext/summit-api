import frappe
from summitapp.summitapp.doctype.website_interface.utils import get_publish_website_interface

@frappe.whitelist()
def publish_website_interface(kwargs):
    return get_publish_website_interface(kwargs)
