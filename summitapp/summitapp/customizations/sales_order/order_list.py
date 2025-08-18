import frappe
from datetime import datetime
from dateutil.relativedelta import relativedelta
from frappe.utils import flt, format_date
from summitapp.utils import error_response
from summitapp.api.v2.utils import get_field_names,get_currency,get_currency_symbol, get_product_url
from summitapp.summitapp.customizations.address.utils import get_details as get_address_details
from summitapp.summitapp.customizations.sales_order.utils import get_charges_from_table

@frappe.whitelist()
def get_sales_order_list(kwargs):
	try:
		email = frappe.session.user
		if email == "Guest":
			return error_response('Please Login As A Customer')
		order_id = kwargs.get('order_id')
		date_range = kwargs.get('date_range')
		status = kwargs.get('status')
		session_id = kwargs.get('session_id')
		limit = int(kwargs.get("limit",0))
		page_no = int((kwargs.get("page_no",0)))
		if "System Manager" not in frappe.get_roles(email):
			customer = frappe.get_value("Customer",{'email':email}, 'name')
		else:
			customer = None
		result, order_count = get_listing_details(customer, order_id, date_range, status, session_id, limit, page_no)
		return {'msg': 'success', 'data': result, 'order_count': order_count}
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)
	


def get_listing_details(customer, order_id, date_range, status, session_id, limit, page_no):
	filters = []
	if customer:
		filters.append(["Sales Order", "customer", "=", customer])
	if order_id:
		filters.append(["Sales Order", "name", "=", order_id])
	else:
		if status == "Cancelled":
			filters.append(["Sales Order", "order_status", "=", "Cancelled"])
		elif status == "Replacement":
			filters.append(["Sales Order", "order_status", "!=", "Cancelled"])
			filters.append(["Sales Order", "is_replacement", "=", "1"])
		elif status == "Completed":
			filters.append(["Sales Order", "order_status", "!=", "Cancelled"])
			filters.append(["Sales Order", "is_replacement", "=", "0"])
		else:
			filters.append(["Sales Order", "order_status", "!=", "Cancelled"])
			filters.append(["Sales Order", "is_replacement", "=", "0"])
	if date_range:
		filters = get_date_range_filter(filters, date_range)
	if session_id:
		filters.append(["Sales Order", "custom_session_id", "=", session_id])
	filters.append(["Sales Order", "order_type", "!=", "Accessory"])
  
	orders = frappe.get_all(
         "Sales Order",
         filters=filters,
         fields="*",
         limit_start=(page_no - 1) * limit,
         limit_page_length=limit,
         order_by="transaction_date desc",
     )
	charges_fields = get_processed_order(orders, customer)
	return charges_fields, len(charges_fields)


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



def get_processed_order(orders, customer):
    field_names = get_field_names('Order')
    order_data = []
    for order in orders:
        tax_table = frappe.get_all("Sales Taxes and Charges", {'parent': order.name}, "*")
        try:
            sales_invoice = frappe.get_doc("Sales Invoice", {'sales_order': order.name}, "*")
            if sales_invoice:
                print_url =get_pdf_link ("Sales Invoice", sales_invoice.name)
            else:
                print_url = ""
        except frappe.DoesNotExistError as e:
            print(f"Sales Invoice not found for order {order.name}: {e}")
            print_url = ""
        charges = get_charges_from_table({}, tax_table)
        computed_fields = {
            'tax': lambda: {"tax": charges.get("tax", 0)},
            'shipping': lambda: {"shipping": charges.get("shipping", 0)},
            'gateway_charge': lambda: {"gateway_charges": charges.get("gateway_charge", 0)},
            'subtotal_include_tax': lambda: {"subtotal_include_tax": order.total + charges.get("tax", 0)},
            'subtotal_exclude_tax': lambda: {"subtotal_exclude_tax": order.total},
            'total': lambda: {"total": order.rounded_total - order.store_credit_used},
            'creation': lambda: {"creation": get_creation_date_time(order.name)},
            'order_details': lambda: {"order_details": get_product_details(order.name)},
            'payment_status': lambda: {"payment_status": order.get("workflow_state")},
            'coupon_code': lambda: {"coupon_code": order.get("coupon_code")},
            'coupon_amount': lambda: {"coupon_amount": order.get("discount_amount")},
            'currency': lambda: {'currency': get_currency(order.currency)},
            'currency_symbol': lambda: {'currency_symbol': get_currency_symbol(order.currency)},
            'addresses': lambda: {"addresses": get_address(customer, order.customer_address, order.shipping_address_name)},
	    	'colour': lambda: {"colour": order.colour},
            'shipping_method': lambda: {'shipping_method': {
                "transporter": order.transporter,
                "transport_charges": order.transport_charges,
                "door_delivery": order.door_delivery,
                "godown_delivery": order.godown_delivery,
                "location": order.location,
                "remarks": order.remarks
            }},
            'outstanding_amount': lambda: {"outstanding_amount": frappe.db.get_value("Return Replacement Request", {"new_order_id": order.name}, "outstanding_amount") or 0},
            'print_url': lambda: {"print_url": print_url},
			'pending_weight': lambda: {"pending_weight": format(calculate_pending_weight(order.name), ".3f")},
			'total_weight': lambda: {"total_weight": format(order.total_weight, ".3f")},
			'transaction_date': lambda: {"transaction_date": format_date(order.transaction_date)},
   			'image': lambda: {"image": frappe.db.get_all("Sales Order Item", {"parent": order.name}, "image", pluck="image")},
			'sales_order_pdf':  lambda: {"sales_order_pdf": get_sales_order_print_url(order.name)},
        }
        charges_fields = {}
        for field_name in field_names:
            if field_name in computed_fields.keys():
                charges_fields.update(computed_fields.get(field_name)())
            else:
                charges_fields.update({field_name: order.get(field_name)})
        order_data.append(charges_fields)
    return order_data    


def get_pdf_link(voucher_type, voucher_no, print_format ="GST Tax Invoice"):
	if print_format:
		return f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype={voucher_type}&name={voucher_no}&format={print_format}&no_letterhead=1&letterhead=No Letterhead&lang=en"
	return "#"		



def get_creation_date_time(order):
    quot_doc = frappe.get_doc('Sales Order', order)
    if quot_doc:
        creation = str(quot_doc.creation)
        creation_datetime = datetime.strptime(creation, "%Y-%m-%d %H:%M:%S.%f")
        formatted_date = creation_datetime.strftime("%d-%m-%Y")
        formatted_time = creation_datetime.strftime("%I:%M %p")
        formatted_date_time = (formatted_date + " " + formatted_time)
        return formatted_date_time
	

	
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
			'img': item.image,
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



def get_item_info(item, item_row):
	from summitapp.api.v2.cart import get_item_details as item_details
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




def calculate_pending_weight(order_name):
    pending_weight = 0
    order_items = frappe.db.get_all(
        "Sales Order Item", {"parent": order_name}, ["name", "total_size_weight"]
    )

    for item in order_items:
        status = frappe.db.get_value(
            "Sales Order Item Status Details", item.name, "manufacturing_status"
        )
        if status != "Completed":
            pending_weight += item.total_size_weight or 0
    return flt(pending_weight, 3)


def get_sales_order_pdf_link(voucher_type, voucher_no, print_format = "Standard"):
	if not print_format:
		print_format = frappe.db.get_value(
			"Property Setter",
			dict(property="default_print_format", doc_type=voucher_type),
			"value",
		)
	if print_format:
		return f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype={voucher_type}&name={voucher_no}&format={print_format}"
	return "#"


def get_sales_order_print_url(sales_order):
	if sales_order:
		return get_sales_order_pdf_link("Sales Order", sales_order)
	else:
		return "#"