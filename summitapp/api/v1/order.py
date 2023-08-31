import contextlib
import frappe
from frappe.utils import flt
from summitapp.utils import error_response, success_response
from summitapp.api.v1.product import get_slide_images, get_product_url, get_detailed_item_list
from summitapp.api.v1.customer_address import get_details as get_address_details
from erpnext.selling.doctype.quotation.quotation import make_sales_order
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from erpnext.e_commerce.shopping_cart.cart import _get_cart_quotation
from summitapp.api.v1.cart import calculate_quot_taxes
from summitapp.api.v1.utils import get_field_names,get_currency,get_currency_symbol,get_logged_user,get_guest_user


@frappe.whitelist()
def get_list(kwargs):
	try:
		order_id = kwargs.get('order_id')
		date_range = kwargs.get('date_range')
		is_cancelled = kwargs.get('is_cancelled')
		email = frappe.session.user
		if email == "Guest":
			return error_response('Please Login As A Customer')
		customer = frappe.get_value("Customer",{'email':email})
		result, order_count = get_listing_details(customer, order_id, date_range, is_cancelled)
		return {'msg': 'success', 'data': result, 'order_count': order_count}
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)

@frappe.whitelist()
def get_summary(kwargs):
	try:
		id = kwargs.get('id')
		quot_doc = frappe.get_doc('Quotation', id)
		symbol = get_currency_symbol(quot_doc.currency)
		data = {'name':'Order Summary', 'id': id, "currency_symbol":symbol,'values': get_summary_details(quot_doc)}
		return success_response(data = data)
	except Exception as e:
		frappe.logger('order').exception(e)
		return error_response(e)    

# Whitelisted Function
@frappe.whitelist()
def get_razorpay_payment_url(kwargs):
	try:
		email = frappe.session.user
		if email == "Guest":
			return error_response('Please Login As A Customer')
		kwargs['full_name'], kwargs['email'] = frappe.db.get_value('User', email, ['full_name','email']) or [None, None]
		# Returns Checkout Url Of Razorpay for payments	
		payment_details = get_payment_details(kwargs)
		doc = frappe.get_doc("Razorpay Settings")
		return doc.get_payment_url(**payment_details)
	except Exception as e:
		frappe.logger('utils').exception(e)
		return error_response(e)

@frappe.whitelist()
def get_order_id(kwargs):
	try:
		email = frappe.session.user
		if email == "Guest":
			return error_response('Please Login As A Customer')

		customer = frappe.get_value("Customer",{'email':email}, 'name')
		order_id = frappe.db.get_value('Sales Order', {'customer': customer}, 'name')
		
		return success_response(data=order_id)
	except Exception as e:
		frappe.logger('utils').exception(e)
		return error_response(e)

def get_payment_details(kwargs):
	return {
		'amount': kwargs.get('amount'),
		'title': f"Payment For {kwargs.get('order_id')}",
		'description': f"Payment For {kwargs.get('order_id')}",
		'payer_name': kwargs.get('full_name'),
		'payer_email': kwargs.get('email'),
		'reference_doctype': kwargs.get('document_type'),
		'reference_docname': kwargs.get('order_id'),
		'order_id': kwargs.get('order_id'),
		'currency': 'INR',
		'redirect_to': f"failed"
	}

def place_order(kwargs):
	try:
		frappe.set_user("Administrator")
		email = frappe.session.user
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
		if not order_id:	
			quotation = _get_cart_quotation()
		else:
			quotation = frappe.get_doc('Quotation', order_id)
		quotation.common_comment = common_comment
		quotation.transporter = transporter
		quotation.door_delivery = door_delivery
		quotation.godown_delivery = godown_delivery
		quotation.location = location
		quotation.remarks = remarks
		quotation.transport_charges = transport_charges
		order = submit_quotation(quotation, billing_address_id, shipping_address_id,payment_date)
		return order
	except Exception as e:
		frappe.logger('order').exception(e)
		return error_response(f"Cart Does Not Exists /{e}")



def get_summary_details(quot_doc):
	charges = get_charges_from_table(quot_doc)
	tax_amt = charges.get("tax", 0)
	summ_list = [get_summary_list_json("Subtotal Excluding Tax", quot_doc.total)]
	summ_list.append(get_summary_list_json("Tax", tax_amt))
	summ_list.append(get_summary_list_json("Shipping Charges", charges.get("shipping", 0)))
	summ_list.append(get_summary_list_json("Assembly Charges", quot_doc.get("total_assembly_charges")))
	summ_list.append(get_summary_list_json("Payment Gateway Charges", charges.get("gateway_charge", 0)))
	summ_list.append(get_summary_list_json("Subtotal Including Tax", quot_doc.total + tax_amt))
	summ_list.append(get_summary_list_json("Coupon Code", quot_doc.coupon_code))
	summ_list.append(get_summary_list_json("Coupon Amount", quot_doc.discount_amount))
	summ_list.append(get_summary_list_json("Store Credit", quot_doc.get("store_credit_used")))
	summ_list.append(get_summary_list_json("Round Off", quot_doc.get("rounding_adjustment",0)))
	summ_list.append(get_summary_list_json("Total", quot_doc.get("rounded_total",quot_doc.grand_total)-flt(quot_doc.get("store_credit_used",0))))
	return summ_list

def get_summary_list_json(name, value):
	return {
		'name': name,
		'value': value
	}

def get_charges_from_table(doc,table=[]):
	charges = {}
	for row in doc.get('taxes',table):
		if row.description == "Payment Gateway Charges":
			charges["gateway_charge"] = row.get("tax_amount",0)
		elif "Shipping" in row.description:
			charges["shipping"] = row.get("tax_amount",0)
		elif "Assembly" in row.description:
			charges["assembly"] = row.get("tax_amount",0)
		elif "CGST" in row.description:
			charges['cgst'] = charges.get("cgst",0) + row.get("tax_amount",0)
		elif "SGST" in row.description:
			charges['sgst'] = charges.get("sgst",0) + row.get("tax_amount",0)
		elif "IGST" in row.description:
			charges['igst'] = charges.get("igst",0) + row.get("tax_amount",0)
		else:
			charges['others'] = charges.get("others",0) + row.get("tax_amount",0)
		charges['total'] = charges.get("total",0) + row.get("tax_amount",0)
	charges['tax'] = charges.get("total",0) - charges.get("gateway_charge",0) - charges.get("shipping",0) - charges.get("assembly",0)
	return charges

def get_listing_details(customer, order_id, date_range, is_cancelled):
    filters = [["Sales Order", "customer", "=", customer]]
    if order_id:
        filters.append(["Sales Order", "name", "=", order_id])
    if is_cancelled:
        filters.append(["Sales Order", "status", "=", "Cancelled"])
    if date_range:
        filters = get_date_range_filter(filters, date_range)
    orders = frappe.get_all("Sales Order", filters=filters, fields="*")
    charges_fields = get_processed_order(orders,customer)
    return charges_fields, len(charges_fields)

def get_processed_order(orders,customer):
    field_names = get_field_names('Order')
    order_data = []
    for order in orders:
        tax_table = frappe.get_all("Sales Taxes and Charges", {'parent': order.name}, "*")
        charges = get_charges_from_table({}, tax_table)
        computed_fields ={
			'tax':lambda: {"tax": charges.get("tax", 0)},
			'shipping':lambda:{"shipping": charges.get("shipping", 0)},
			'gateway_charge': lambda: {"gateway_charges": charges.get("gateway_charge", 0),},
			'subtotal_include_tax': lambda:{"subtotal_include_tax": order.total + charges.get("tax", 0)},
			'subtotal_exclude_tax': lambda:{"subtotal_exclude_tax":order.total},
			'total':lambda:{"total": order.rounded_total - order.store_credit_used},
			'creation': lambda: {"creation": get_creation_date_time(order.name)},
			'order_details': lambda: {"order_details": get_product_details(order.name)},
			'payment_status':lambda:{"payment_status" : order.get("workflow_state")},
			'coupon_code':lambda:{"coupon_code": order.get("coupon_code")},
			'coupon_amount':lambda:{"coupon_amount" : order.get("discount_amount")},
			'currency':lambda:{'currency':get_currency(order.currency)},
			'currency_symbol':lambda:{'currency_symbol':get_currency_symbol(order.currency)},
			'addresses': lambda:{"addresses": get_address(customer, order.customer_address, order.shipping_address_name)},
			'shipping_method': lambda:{'shipping_method':{
				"transporter": order.transporter,
                "transport_charges": order.transport_charges,
                "door_delivery": order.door_delivery,
                "godown_delivery": order.godown_delivery,
                "location": order.location,
                "remarks": order.remarks
			}},
			'outstanding_amount':lambda:{"outstanding_amount": frappe.db.get_value("Return Replacement Request", {"new_order_id": order.name}, "outstanding_amount") or 0}
			}
        charges_fields = {}
        for field_name in field_names:
            if field_name in computed_fields.keys():
                charges_fields.update(computed_fields.get(field_name)())
            else:
                charges_fields.update({field_name: order.get(field_name)})
        order_data.append(charges_fields)    
    return order_data
                
	
def get_product_details(order):
	quot_doc = frappe.get_doc('Sales Order', order)
	return [
		get_item_details(item.item_code, item, quot_doc.transaction_date)
		for item in quot_doc.items
	]

def get_item_details(item_code, item_row, transaction_date):
	item = frappe.get_value('Item', item_code, "*")
	return {
			'name': item.name,
			'item_name': item.item_name,
			'img': get_slide_images(item.name, True),
			'brand': item.get('brand'),
			'brand_img': frappe.get_value('Brand', {'name': item.get('brand')}, 'image'),
			'prod_info': get_item_info(item, item_row),
			"product_url": get_product_url(item),
			"return_date": get_return_date(item.name, transaction_date)
		}

def get_return_date(item, transaction_date):
	return_days = frappe.db.get_value('Item', item, 'return_days')
	if return_days:
		return_date = (transaction_date + relativedelta(days=return_days)).strftime("%d-%m-%Y")
		return return_date

def get_creation_date_time(order):
    quot_doc = frappe.get_doc('Sales Order', order)
    if quot_doc:
        creation = str(quot_doc.creation)
        creation_datetime = datetime.strptime(creation, "%Y-%m-%d %H:%M:%S.%f")
        formatted_date = creation_datetime.strftime("%d-%m-%Y")
        formatted_time = creation_datetime.strftime("%I:%M %p")
        formatted_date_time = (formatted_date + " " + formatted_time)
        return formatted_date_time

def get_item_info(item, item_row):
	from summitapp.api.v1.cart import get_item_details as item_details
	l1 = item_details(item, item_row)
	l1.append({'name':'Quantity', 'value': item_row.qty})
	return l1


def get_address(customer, customer_address, shipping_address):
	if frappe.db.exists('Address', customer_address):
		customer_address_doc = frappe.db.get_value('Address', customer_address, "*")
	else:
		customer_address_doc = None

	if frappe.db.exists('Address', shipping_address):
		shipping_address_doc = frappe.db.get_value('Address', shipping_address, "*")
	else:
		shipping_address_doc = None
	
	res = []
	res.append(get_address_detail_json('Billing Address', customer, customer_address_doc)) if customer_address_doc else '' 
	res.append(get_address_detail_json('Shipping Address', customer, shipping_address_doc)) if shipping_address_doc else '' 
	return res
	
def get_address_detail_json(type, customer, address_doc):
	return {
			'name': type,
			'values' : [get_address_details(customer, address_doc)] if address_doc else []
		}

def submit_quotation(quot_doc, billing_address_id, shipping_address_id, payment_date):
    quot_doc.customer_address = billing_address_id
    quot_doc.shipping_address_name = shipping_address_id
    quot_doc.payment_schedule = []
    quot_doc.save()
    quot_doc.submit()
    return create_sales_order(quot_doc, payment_date)

def create_sales_order(quot_doc, payment_date):
    so_doc = make_sales_order(quot_doc.name)
    if payment_date:
        payment_date = datetime.strptime(payment_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        so_doc.delivery_date = datetime.strptime(payment_date, "%Y-%m-%d")
    else:
        transaction_date = datetime.strptime(so_doc.transaction_date, "%Y-%m-%d")
        so_doc.delivery_date = (transaction_date + timedelta(days=7)).date()
    so_doc.payment_schedule = []
    so_doc.flags.ignore_permissions = True
    so_doc.save()
    return confirm_order(so_doc)
	

def confirm_order(so_doc):
    with contextlib.suppress(Exception):
        so_doc.flags.ignore_permissions = True
        so_doc.payment_schedule = []
        so_doc.save()
    return so_doc.name

def get_date_range_filter(filters, date_range):
	if date_range == 'past_3_months':
		filters.append(["Sales Order","transaction_date","Timespan","last quarter"])
	if date_range == 'last_30_days':
		filters.append(["Sales Order","transaction_date","Timespan","last month"])
	elif date_range == 'last_6_months':
		filters.append(["Sales Order","transaction_date","Timespan","last 6 months"])
	elif date_range == '2022':
		filters.append(["Sales Order","transaction_date","fiscal year","2022-2023"])
	elif date_range == '2021':
		filters.append(["Sales Order","transaction_date","fiscal year","2021-2022"])
	elif date_range == '2020':
		filters.append(["Sales Order","transaction_date","fiscal year","2020-2021"])
	elif date_range:
		filters.append(["Sales Order","transaction_date","Timespan",date_range.replace("_"," ")])
	return filters


def return_replace_item(kwargs):
	try:
		if not kwargs.get('order_id'): return error_response('Please Sepecify Order')
		if not kwargs.get('product_id'): return error_response('Please Specify Product')
		rr_doc = frappe.new_doc('Return Replacement Request')
		rr_doc.type = kwargs.get('return_replacement')
		rr_doc.reason = kwargs.get('description')
		rr_doc.order_id = kwargs.get('order_id')
		rr_doc.product_id = kwargs.get('product_id')
		images = kwargs.get("images",{})
		for file in images.values():
			rr_doc.append("return_replacement_image",{"image":file})
		rr_doc.save(ignore_permissions=True) # Ignoring Permissions to Save the Document
		return success_response(data={'docname':rr_doc.name, 'doctype': rr_doc.doctype})
	except Exception as e:
		return error_response(e)

def get_order_details(kwargs):
	if not kwargs.get('order_id'):
		return "Invalid Order Id"
	try:
		doc = frappe.get_doc("Sales Order", kwargs.get("order_id"))
		tax = 0
		shipping = 0
		for row in doc.get("taxes", []):
			if "Tax" in row.description:
				tax += row.get("tax_amount",0)
			elif row.description == doc.shipping_rule:
				shipping += row.get("tax_amount",0)
		actionfield = {
			"id": doc.name,
			"affiliation": None,
			"revenue": doc.rounded_total or doc.grand_total,
			"tax": tax,
			"shipping": shipping,
			"coupon": doc.get("coupon_code")
		}
		products = []
		for row in doc.items:
			category = frappe.db.get_value("Item", row.item_code, "category")
			item = {
				"name": row.item_name,
				"id": row.item_code,
				"price": row.rate,
				"brand": row.brand,
				"category": category,
				"variant": None,
				"quantity": row.qty,
				"coupon": doc.get("coupon_code")
			}
			products.append(item)

		res = {"ecommerce": {
			"purchase": {
				"actionField": actionfield,
				"products": products
				}
		}}
		return res
	except Exception as e:
		frappe.logger('utils').exception(e)
		return error_response("Something went wrong")

def recently_bought(kwargs):
	try:
		if frappe.session.user == "Guest":
			return error_response("Please login first")
		customer = kwargs.get("customer_id")
		if not customer:
			customer = frappe.db.get_value("Customer", {"email":frappe.session.user}, "name")
		if not customer:
			return error_response("Customer not found")

		orders = frappe.db.get_values("Sales Order",{"customer":customer},'name', pluck=1)
		items = frappe.db.get_list("Sales Order Item",{'parent':["in",orders]}, pluck="item_code", distinct=1, limit_page_length=8, ignore_permissions=1) or []
		res = []
		res = get_detailed_item_list(items, customer)
		return success_response(data = res)
	except Exception as e:
		frappe.logger("order").exception(e)
		return error_response(e)