import frappe
from summitapp.summitapp.customizations.item_variant.utils import variants

# Get variants
@frappe.whitelist(allow_guest=True)
def get_variants(kwargs):
    return variants(kwargs)