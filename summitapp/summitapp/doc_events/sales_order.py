import frappe
import json

@frappe.whitelist()
def make_seller_order_confirmation(doc):
    sales_order = frappe.get_doc("Sales Order", doc)
    for row in sales_order.items:
        seller_order_confirmation = frappe.get_doc({
            'doctype': 'Seller Order Confirmation',
            'sales_order':sales_order.name,
            'item_code': row.item_code,
            'amount': row.amount,
            'quantity': row.qty,
            'item_name': row.item_name,
            'uom': row.uom,
            'seller': row.seller,
            'email' : row.email,
            'status': "Pending",
            })
        seller_order_confirmation.insert()
    sales_order.sales_order_confirmation_created = 1
    sales_order.save()


    
