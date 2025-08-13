import frappe
from summitapp.summitapp.customizations.item.product_list import get_product_list
from summitapp.summitapp.customizations.item.product_details import get_product_details
from summitapp.summitapp.customizations.item.variants import get_product_variants, get_variants_listing
from summitapp.summitapp.customizations.item.tagged_product_list import tagged_products
from summitapp.summitapp.customizations.item.check_availability import check_product_availability
from summitapp.summitapp.doctype.category.utils import categories
from summitapp.summitapp.customizations.item.product_search import get_product_search, get_item_search
from summitapp.summitapp.customizations.item.utils import (cyu_categories, get_products_recommendation, top_categories, default_currency,
                                                           get_quick_order, customer_wise_loyalty_points)

# Get Product List
@frappe.whitelist(allow_guest=True)
def get_list(kwargs):
    return get_product_list(kwargs)


# Get Product Detail
@frappe.whitelist(allow_guest=True)
def get_details(kwargs):
    return get_product_details(kwargs)


# Get CYU Categories
@frappe.whitelist(allow_guest=True)
def get_cyu_categories(kwargs):
    return cyu_categories(kwargs)


# Get Variants
@frappe.whitelist(allow_guest=True)
def get_variants(kwargs):
    return get_product_variants(kwargs)


# Get products recommandation
@frappe.whitelist(allow_guest=True)
def get_recommendation(kwargs):
	return get_products_recommendation(kwargs)



# Get Top Categories
@frappe.whitelist(allow_guest=True)
def get_top_categories(kwargs):
	return top_categories(kwargs)



# Get Tagged Product
@frappe.whitelist(allow_guest=True)
def get_tagged_products(kwargs):
    return tagged_products(kwargs)


# Check product availability
@frappe.whitelist(allow_guest=True)
def check_availability(kwargs):
    return check_product_availability(kwargs)


# Get Categories
@frappe.whitelist(allow_guest=True)
def get_categories(kwargs):
    return categories(kwargs)


# Get Default Currency
@frappe.whitelist(allow_guest=True)
def get_default_currency(kwargs):
    return default_currency(kwargs)   


# Get Quick Order
@frappe.whitelist()
def quick_order(kwargs):
    return get_quick_order(kwargs)
    

# Get Variants for listing
@frappe.whitelist()
def get_variants_for_listing(**kwargs):
    return get_variants_listing(**kwargs)


# Get Product Search
@frappe.whitelist(allow_guest=True)
def product_search(kwargs):
    return get_product_search(kwargs)


# Get Item Search
@frappe.whitelist(allow_guest=True)
def item_search(kwargs):
    return get_item_search(kwargs)


# Get customer wise loyalty points
@frappe.whitelist()
def get_customer_wise_loyalty_points(customer_id, currency):
    return customer_wise_loyalty_points(customer_id, currency)