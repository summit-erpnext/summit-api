import frappe
from summitapp.summitapp.doctype.filter_section_setting.utils import (get_listing_page_filters, 
                                                                      get_listing_page_filters_without_category,
                                                                      vehicle_filters)

# Get Filters on listing page
@frappe.whitelist()
def get_filters(kwargs):
    return get_listing_page_filters(kwargs)


# Get filters without category   
@frappe.whitelist()
def get_filters_without_category(kwargs):
    return get_listing_page_filters_without_category(kwargs)
   

# Get Vehicle Filters
@frappe.whitelist(allow_guest=True)
def get_vehicle_filters(kwargs=None):
    return vehicle_filters(kwargs)