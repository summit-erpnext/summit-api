import frappe
from summitapp.utils import success_response, error_response
from summitapp.summitapp.customizations.sales_order.utils import submit_quotation


def place_sales_order(kwargs):
	try:
		frappe.set_user("Administrator")
		party_name = kwargs.get('party_name')
		common_comment = kwargs.get('common_comment')
		payment_date = kwargs.get('payment_date')
		order_id = kwargs.get('order_id')
		billing_address_id = kwargs.get('billing_address_id')
		shipping_address_id = kwargs.get('shipping_address_id')
		transporter = kwargs.get('transporter')
		transport_charges = kwargs.get("transport_charges")
		door_delivery = kwargs.get('door_delivery')
		godown_delivery = kwargs.get('godown_delivery')
		location = kwargs.get('location')
		remarks = kwargs.get('remarks')
		if order_id:	
			quotation = frappe.get_doc('Quotation', order_id)
			quotation.common_comment = common_comment
			quotation.transporter = transporter
			quotation.door_delivery = door_delivery
			quotation.godown_delivery = godown_delivery
			quotation.location = location
			quotation.remarks = remarks
			quotation.transport_charges = transport_charges
			quotation.party_name = party_name
			order = submit_quotation(quotation, billing_address_id, shipping_address_id,payment_date,None)
			return order
	except Exception as e:
		frappe.logger('order').exception(e)



def razorpay_place_order(order_id=None, party_name=None, common_comment=None, payment_date=None,
                billing_address_id=None, shipping_address_id=None, transporter=None,
                transport_charges=None, door_delivery=None, godown_delivery=None,
                location=None, remarks=None,company_gstin=None):
	try:
		frappe.set_user("Administrator")
		if order_id:	
			quotation = frappe.get_doc('Quotation', order_id)
			quotation.common_comment = common_comment
			quotation.transporter = transporter
			quotation.door_delivery = door_delivery
			quotation.godown_delivery = godown_delivery
			quotation.location = location
			quotation.remarks = remarks
			quotation.transport_charges = transport_charges
			quotation.party_name = party_name
			order = submit_quotation(quotation, billing_address_id, shipping_address_id,payment_date,company_gstin)
			return order
	except Exception as e:
		frappe.logger('order').exception(e)
		return error_response(f"Cart Does Not Exists /{e}")