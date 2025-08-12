import frappe
from summitapp.utils import (error_response, success_response)
from summitapp.summitapp.customizations.user.utils import get_logged_user
from summitapp.api.v2.product import get_stock_info, get_recommendation, get_product_url
from summitapp.api.v2.utils import (get_price_list,get_field_names,get_guest_user,
				    get_currency,get_currency_symbol,get_variant_attributes)
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from frappe.utils import flt, getdate
import json
from summitapp.summitapp.doctype.translation_text.utils import translate_result
from summitapp.summitapp.doctype.category.utils import get_parent_categories

def custom_calculate_taxes_and_totals(self, method):
	try:
		if not self.taxes:
			sales_taxes_and_charges_template = self.taxes_and_charges
			if not sales_taxes_and_charges_template: return "Item Added To Cart"
			from erpnext.controllers.accounts_controller import get_taxes_and_charges
			taxes = get_taxes_and_charges("Sales Taxes and Charges Template",sales_taxes_and_charges_template)
			self.taxes = []
			for i in taxes:
				self.append('taxes', i)
			add_additional_charges(self)
			self.run_method("calculate_taxes_and_totals")
		add_additional_charges(self)
	except Exception as e:
		return 

def add_additional_charges(self):
	charges = frappe.get_doc("Additional Charges Detail")
	if not self.shipping_rule:
		self.shipping_rule = charges.get("shipping_rule")
	self.total_assembly_charges = 0
	for item in self.items:
		self.total_assembly_charges += item.assembly_charges
	if self.total_assembly_charges:
		for tax_row in self.get("taxes", []):
			if tax_row.get("description") == "Assembly Charges":
				tax_row.tax_amount = self.total_assembly_charges
		

def on_payment_authorized(self, *args, **kwargs):
	try:
		if args[1] == 'Authorized':
			from summitapp.summitapp.customizations.sales_order.place_order import razorpay_place_order
			fil_lst = {'order_id': self.name}
			party_name = {"party_name":self.party_name}
			order = razorpay_place_order(fil_lst['order_id'], party_name=party_name['party_name'])
			return f"my-orders/{order}"
		else:
			return 'failed'
	except Exception as e:
		frappe.logger('utils').exception(e)






def delete_cart_products(kwargs):  
	try:
		email = None	
		headers = frappe.request.headers
		if not headers or 'Authorization' not in headers:
			return error_response('Please Specify Authorization Token')
		auth_header = headers.get('Authorization')
		if "token" in auth_header:
			email = get_logged_user()
		else:
			email = get_guest_user(auth_header)
		item_code = kwargs.get('item_code')
		quotation_id = kwargs.get("quotation_id")
		owner = frappe.db.get_value('User', {"email": email})
		if not quotation_id:
			quotation_id = frappe.db.exists("Quotation",{'owner': owner, 'status': 'Draft'})
		if not quotation_id:
			return error_response("Cart not found")
		quot_doc = frappe.get_doc('Quotation', quotation_id)
		
		params = {"item_only":1,"item_code":item_code, "ptype":"Mandatory"}
		item_list = []
		recommendations = get_recommendation(params)
		if recommendations:
			for item in recommendations:
				if not item:
					continue
				item_list.append(item)
		else:
			item_list.append(item_code)

		deleted_from_cart = delete_item_from_cart(item_list, quot_doc)
		return success_response(data = deleted_from_cart)
	except Exception as e:
		frappe.logger('cart').exception(e)
		return error_response('error deleting items to cart')
	

def delete_item_from_cart(item_list, quot_doc):
    item_deleted = False
    for item in item_list:
        quotation_items = quot_doc.get("items")
        if quotation_items and len(quot_doc.get("items", [])) == 1:
            frappe.delete_doc("Quotation", quot_doc.name, ignore_permissions=True)
            return "Item Deleted"
        elif quotation_items:
            frappe.db.delete('Quotation Item', {'parent': quot_doc.name, 'item_code': item})
            quot_doc.reload()
            item_deleted = True
    if item_deleted:
        quot_doc.reload()
        quot_doc.save(ignore_permissions=True)
        return 'Item Deleted'
    return f"Following Items: {', '.join(item_list)} do not exist in cart!"	




def clear_entire_cart(kwargs):
	try:
		quotation_id = kwargs.get('quotation_id')
		if not quotation_id: return error_response('Quotation Not Found')
		frappe.delete_doc("Quotation",quotation_id,ignore_permissions=True, ignore_missing=True)
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)
	


def get_bar_code_image(item_code):
	# pip install python-barcode
	from barcode import Code128
	from barcode.writer import ImageWriter
	image_name = item_code + '_bar_code'  
	barcode_path = frappe.get_site_path()+'/public/files/'
	item_bar_code = Code128(item_code, writer=ImageWriter())	
	item_bar_code.save(barcode_path + image_name)  
	return f'/files/{image_name}.png'


def calculate_quot_taxes(quot_doc):
	sales_taxes_and_charges_template = frappe.db.get_value('Quotation', quot_doc.get("name"), 'taxes_and_charges')
	if not sales_taxes_and_charges_template: return "Item Added To Cart"
	taxes = get_taxes_and_charges("Sales Taxes and Charges Template",sales_taxes_and_charges_template)
	quot = frappe.get_doc('Quotation', quot_doc.get("name"))
	quot.taxes = []
	for i in taxes:
		quot.append('taxes', i)
	if quot:
		quot.save(ignore_permissions=True)  
	else:
		return {'name': quot_doc.get("name")}
	return {'name': quot_doc.get("name")}





def get_request_for_quotation(kwargs):
	quot_id = kwargs.get('quotation_id')
	if not quot_id:
		return error_response("Quotation id is required")
	new_doc = frappe.get_doc("Quotation",quot_id)
	return success_response(data={"quotation_id":new_doc.name,"print_url": get_pdf_link("Quotation",new_doc.name)})


def quotation_history(kwargs):
	if frappe.session.user == "Guest":
		return error_response("Please login first")
	customer = kwargs.get("customer_id")
	if not customer:
		customer = frappe.db.get_value('Customer', {'email': frappe.session.user})
	if not customer:
		return error_response('Please login as a customer')
	send_quotation = kwargs.get("only_requested",1)
	filters = {"party_name": customer, "docstatus":1}
	quotations = frappe.get_list("Quotation",filters=filters,fields=["name","modified","total_qty", "rounded_total","grand_total"])
	if quotations:
		quotations = [
			{
				"name": row.name,
				"enquiry_date": getdate(row.modified),
				"total_qty": row.total_qty,
				"grand_total": row.get("rounded_total") or row.grand_total,
				"print_url": get_pdf_link("Quotation",row.name)
			} for row in quotations
		]
	return success_response(data=quotations)

def get_pdf_link(voucher_type, voucher_no, print_format = None):
	if not print_format:
		print_format = frappe.db.get_value(
			"Property Setter",
			dict(property="default_print_format", doc_type=voucher_type),
			"value",
		)
	if print_format:
		return f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype={voucher_type}&name={voucher_no}&format={print_format}"
	return "#"
