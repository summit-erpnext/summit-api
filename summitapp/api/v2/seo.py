import frappe
from summitapp.summitapp.customizations.seo.utils import meta_tags, site_map

# Get Meta Tags
@frappe.whitelist()
def get_meta_tags(kwargs):
    return meta_tags(kwargs)


# Get Site Map
@frappe.whitelist()
def get_site_map(kwargs):
    return site_map(kwargs)