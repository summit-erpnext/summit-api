import frappe
from summitapp.summitapp.customizations.sales_order.place_order import place_sales_order
from summitapp.summitapp.customizations.sales_order.order_list import get_sales_order_list
from summitapp.summitapp.customizations.sales_order.utils import (get_sales_order_summary, razorpay_payment_url, order_id,
																  recently_bought_items, cancel_sales_order)
from summitapp.summitapp.customizations.sales_order.return_replacment import create_return_replace_item
from summitapp.summitapp.customizations.sales_order.order_details import get_sales_order_details


# Place Order
@frappe.whitelist()
def place_order(kwargs):
	return place_sales_order(kwargs)


# Get Order Listing
@frappe.whitelist()
def get_list(kwargs):
	return get_sales_order_list(kwargs)


# Get Order Summary
@frappe.whitelist()
def get_summary(kwargs):
	return get_sales_order_summary(kwargs)


# Get Order Id
@frappe.whitelist()
def get_order_id(kwargs):
	return order_id(kwargs)


# Get Razorpay Payment URL	
@frappe.whitelist()
def get_razorpay_payment_url(kwargs):
	return razorpay_payment_url(kwargs)
		

# Create Return replacment items	
@frappe.whitelist()
def return_replace_item(kwargs):
	return create_return_replace_item(kwargs)


# Get Sales Order Details
@frappe.whitelist()
def get_order_details(kwargs):
	return get_sales_order_details(kwargs)


# Get Recently bought items
@frappe.whitelist()
def recently_bought(kwargs):
	return recently_bought_items(kwargs)


# Cancle sales order
def cancel_order(kwargs):
	return cancel_sales_order(kwargs)


	



