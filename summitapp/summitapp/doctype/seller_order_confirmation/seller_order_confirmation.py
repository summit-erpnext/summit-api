# Copyright (c) 2022, 8848Digital LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import utils
from frappe.utils import cint
from frappe.model.mapper import get_mapped_doc
class SellerOrderConfirmation(Document):
	pass


def set_sales_invoice_missing_values(target):
	target.run_method("set_missing_values")
	target.run_method("set_po_nos")
	target.run_method("calculate_taxes_and_totals")

@frappe.whitelist()
def make_sales_invoice(doc):
	seller_order = frappe.get_doc("Seller Order Confirmation", doc)
	sales_invoice = frappe.new_doc("Sales Invoice")
	sales_invoice.commission_si_for_seller = 1
	sales_invoice.seller_order_confirmation = seller_order.name
	sales_invoice.sales_order = seller_order.sales_order
	sales_invoice.item_code = seller_order.item_code
	sales_invoice.customer = seller_order.customer
	sales_invoice.item_code = seller_order.item_code
	sales_invoice.qty = seller_order.quantity
	sales_invoice.amount = seller_order.amount
	commission_rate = seller_order.amount*(sales_invoice.commission_percentage / 100)
	item  = frappe.get_doc("Item", "Commission")
	item_tax_template = ""
	for row in item.taxes:
		item_tax_template = row.item_tax_template
	sales_invoice.append("items", {
	"item_code": item.name,
	"item_name":item.item_name,
	"description":item.description,
	"gst_hsn_code":item.gst_hsn_code,
	"qty": 1,
	"uom":item.stock_uom,
	"rate":commission_rate,
	"item_tax_template":item_tax_template,
	"income_account":'Sales - A',
	"cost_center":'Main - A'
	})
	sales_invoice.tax_category = 'In-State'
	set_sales_invoice_missing_values(sales_invoice)
	sales_invoice.save()
	seller_order.commission_sales_invoice_created = 1
	seller_order.save()

# def on_cancel(self, method= None):
#     sales_order = frappe.get_doc("Sales Order", self.sales_order)
#     sales_order.sales_order_confirmation_created = 0
#     sales_order.save()


# @frappe. whitelist()
# def make_sales_invoice(source_name, target_doc=None, ignore_permissions=False):
# 	doclist = get_mapped_doc(
# 		"Seller Order Confirmation",
# 		source_name,
# 		{
# 			"Seller Order Confirmation": {
# 				"doctype": "Sales Invoice",
# 				"field_map": {
# 					"seller_order_confirmation":"name",
# 					"customer":"customer",
# 					"item_code":"item_code",
# 					"qty":"quantity",
# 					"amount":"amount"
# 				},
# 				"field_no_map": ["payment_terms_template"],
# 				#"validation": {"docstatus": ["=", 1]},
# 			},
# # 			"Pick List Item": {
# #                         "doctype": "Sales Invoice Item",
# #                         "field_map":{
# #                                 "name": "pick_list_item",
# #                                 "parent": "pick_list",
# #                                 "sales_order":"sales_order",
# # 				"sales_order_item": "so_detail"
# #                         },
# # #                        "postprocess": update_item

# #                 },
# 			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
# 			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
# 		},
# 		target_doc,
# 		# postprocess,
# 		# ignore_permissions=ignore_permissions,
# 	)

# 	automatically_fetch_payment_terms = cint(
# 		frappe. db. get_single_value("Accounts Settings", "automatically_fetch_payment_terms")
# 	)
# 	if automatically_fetch_payment_terms:
# 		doclist. set_payment_schedule()

# 	doclist. set_onload("ignore_price_list", True)
# 	doclist.commission_si_for_seller = 1
# 	doclist.tax_category = 'In-State'
# 	item  = frappe.get_doc("Item", "Commission")
# 	item_price = frappe.db.get_value("Item Price",{'item_code':item.name},'price_list_rate')
# 	item_tax_template = ""
# 	for row in item.taxes:
# 		item_tax_template = row.item_tax_template
# 	doclist.append("items", {
# 	"item_code": item.name,
# 	"item_name":item.item_name,
# 	"description":item.description,
# 	"gst_hsn_code":item.gst_hsn_code,
# 	"qty": 1,
# 	"uom":item.stock_uom,
# 	"rate":item_price,
# 	"income_account":'Sales - A',
# 	"cost_center":'Main - A',
# 	"item_tax_template": item_tax_template
# 	})
# 	set_sales_invoice_missing_values(doclist)
# 	doclist.save()
# 	return doclist

