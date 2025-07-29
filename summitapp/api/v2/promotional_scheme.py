import frappe
from summitapp.summitapp.customizations.promotional_scheme.utils import promotional_scheme_items, promotional_scheme


# Get promotional scheme items
@frappe.whitelist(allow_guest=True)
def get_promotional_scheme_items(kwargs):
    return promotional_scheme_items(kwargs)
  

# get promotional scheme
@frappe.whitelist(allow_guest=True)
def get_promotional_scheme(kwargs):
    return promotional_scheme(kwargs)