import frappe
from summitapp.summitapp.doctype.catalog.utils import (get_catalog_list, get_item, create_new_catalog, update_catalog_items, 
                                                       delete_entire_catalog, delete_catalog_items)
 
# Get Catalog List
@frappe.whitelist()
def get(kwargs):
    return get_catalog_list(kwargs)
	

# Get Catalog Item List    
@frappe.whitelist()
def get_items(kwargs):
    return get_item(kwargs)


# Create New Catalog
@frappe.whitelist()
def put(kwargs):
    return create_new_catalog(kwargs)
    
# Update catalog items list    
@frappe.whitelist()
def put_items(kwargs):
    return update_catalog_items(kwargs)
      

# Delete entire catalog
@frappe.whitelist()
def delete(kwargs):
    return delete_entire_catalog(kwargs)


# Delete catalog items
@frappe.whitelist()
def delete_items(kwargs):
    return delete_catalog_items(kwargs)