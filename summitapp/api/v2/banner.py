import frappe
from summitapp.summitapp.doctype.home_banner.utils import get_home_banner


# Get Home Banner List
@frappe.whitelist(allow_guest=True)
def get(kwargs):
    return get_home_banner(kwargs)