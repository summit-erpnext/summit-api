import frappe
from summitapp.summitapp.customizations.quotation.utils import (get_cart_list, put_cart_products, delete_cart_products,
                                                                clear_entire_cart, get_request_for_quotation, quotation_history)


# Add products to Cart
@frappe.whitelist(allow_guest=True)
def put_products(kwargs):  
	return put_cart_products(kwargs)


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