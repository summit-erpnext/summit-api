import frappe
from summitapp.summitapp.customizations.quotation.utils import (delete_cart_products,
                                                                clear_entire_cart, get_request_for_quotation, quotation_history)
from summitapp.summitapp.customizations.quotation.get_cart_list import get_cart_list
from summitapp.summitapp.customizations.quotation.add_to_cart import put_cart_products


# Add products to Cart
@frappe.whitelist(allow_guest=True)
def put_products(kwargs):  
	return put_cart_products(kwargs)

# Get Cart List
@frappe.whitelist(allow_guest=True)
def get_list(kwargs):
	return get_cart_list(kwargs)

# Get Cart products
@frappe.whitelist(allow_guest=True)
def delete_products(kwargs):  
	return delete_cart_products(kwargs)
	

# Clear entire Cart
@frappe.whitelist(allow_guest=True)
def clear_cart(kwargs):
	return clear_entire_cart(kwargs)
	

# Get Request for quotation
@frappe.whitelist(allow_guest=True)
def request_for_quotation(kwargs):
	return get_request_for_quotation(kwargs)
	

# Get Quotation History
@frappe.whitelist(allow_guest=True)
def get_quotation_history(kwargs):
	return quotation_history(kwargs)