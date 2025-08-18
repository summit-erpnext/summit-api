import frappe, json, requests
from frappe.utils import flt
from erpnext.selling.doctype.quotation.quotation import make_sales_order
import contextlib
from datetime import datetime, timedelta
from summitapp.utils import make_payment_entry
from summitapp.utils import error_response, success_response
from summitapp.api.v2.utils import get_currency_symbol


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



def on_submit_actions(self, method=None):
    if self.store_credit_used:
        balance = frappe.db.get_value("Customer", self.customer, "balance_amount")
        if self.store_credit_used > balance:
            frappe.throw("Not enough store credits")
        doc = frappe.new_doc("Journal Entry")
        doc.voucher_type = "Bank Entry"
        doc.posting_date = frappe.utils.today()
        if not doc.company:
            doc.company = frappe.db.get_single_value("Global Defaults", "default_company")
        discount_acc, receivable_acc = frappe.get_cached_value("Company", doc.company, ["default_discount_account","default_receivable_account"])
        doc.append('accounts',{
            "account": receivable_acc,
            "party_type": "Customer",
            "party": self.customer,
            "credit_in_account_currency": self.store_credit_used,
            "is_advance": "Yes"
        })
        doc.append('accounts',{
            "account": discount_acc,
            "party_type": "Customer",
            "party": self.customer,
            "debit_in_account_currency": self.store_credit_used
        })
        doc.cheque_no = self.name
        doc.cheque_date = self.transaction_date
        doc.remark = f"Store Credit used on Sales Order:{self.name}"
        doc.flags.ignore_permissions = True
        doc.save()
        doc.submit()
        frappe.db.set_value("Customer",self.customer,'balance_amount', balance - self.store_credit_used)
    if self.workflow_state == "Approved":
        frappe.db.set_value("Sales Order",self.name, "order_status","Approved")


def on_payment_authorized(self, *args, **kwargs):
	try:
		if args[1] == 'Authorized':
			make_payment_entry(self.name)
			return "thankyou"
		else:
			return 'failed'
	except Exception as e:
		frappe.logger('utils').exception(e)
          

def on_cancel_set_order_status(self, method=None):
    if self.workflow_state == "Cancelled":
        frappe.db.set_value("Sales Order",self.name,"order_status","Cancelled")


def set_workflow_state_and_order_status(self, method=None):
    send_sales_order_api(self)
    if self.workflow_state == "Order Placed":
        self.order_status = "Pending for Approval"


def on_update_after_submit_set_workflow_state(self, method=None):
    if self.workflow_state == "Billed":
        frappe.db.set_value("Sales Order",self.name,"order_status","Billed")
    elif self.workflow_state == "Delivery":
        frappe.db.set_value("Sales Order",self.name,"order_status","Out For Delivery")
    elif self.workflow_state == "Submitted":
        frappe.db.set_value("Sales Order",self.name,"order_status","Order Delivered")    


def set_autoname(self,method=None):
    if self.is_replacement:
        replacement_sales_order = len(frappe.db.get_all("Sales Order", filters={"parent_sales_order": self.parent_sales_order}, pluck="parent_sales_order"))
        return_replacement_request_sales_order = frappe.db.get_value(
            "Return Replacement Request",
            self.returrn_replacement_request,
            "order_id"
        )
        if replacement_sales_order == 0:
            sales_order_naming = f"{self.parent_sales_order}-Replacement"
            self.name = sales_order_naming
        else:
            sales_order_naming = f"{self.parent_sales_order}-Replacement-{replacement_sales_order}"
            self.name = sales_order_naming



def send_sales_order_api(doc):
    summit_settings = frappe.get_single("Summit Settings")
    url = f"{summit_settings.socket_site_url}/api/sales-order"
    headers = {"Content-Type": "application/json"}
    for item in doc.items:
        payload = {
            "user_name": doc.customer,
            "email_id": frappe.db.get_value("Customer", {"name": doc.customer}, 'email'),
            "phone": frappe.db.get_value("Customer", {"name": doc.customer}, 'mobile_number'),
            "page_type":"Product",
            "page_id": item.item_code,
            "action":"Sales Order",
            "reference_type": item.reference_page,
            "reference_id": item.reference_id
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code != 200:
                frappe.log_error(f"Error in Sales Order API: {response.text}", "Sales Order API Error")
        except Exception as e:
            frappe.log_error(f"Exception: {str(e)}", "Sales Order API Exception")            




def get_sales_order_summary(kwargs):
	try:
		id = kwargs.get('id')
		quot_doc = frappe.get_doc('Quotation', id)
		symbol = get_currency_symbol(quot_doc.currency)
		data = {'name':'Order Summary', 'id': id, "currency_symbol":symbol,'values': get_summary_details(quot_doc)}
		return success_response(data = data)
	except Exception as e:
		frappe.logger('order').exception(e)
		return error_response(e)   
     


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


def razorpay_payment_url(kwargs):
	try:
		email = frappe.session.user
		kwargs['full_name'], kwargs['email'] = frappe.db.get_value('User', email, ['full_name','email']) or [None, None]
		# Returns Checkout Url Of Razorpay for payments	
		payment_details = get_payment_details(kwargs)
		doc = frappe.get_doc("Razorpay Settings")
		return doc.get_payment_url(**payment_details)
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



def order_id(kwargs):
	try:
		email = frappe.session.user
		session_id = kwargs.get('session_id')
		customer = frappe.get_value("Customer",{'email':email}, 'name')
		if customer:
			order_id = frappe.db.get_value('Sales Order', {'customer': customer}, 'name')
		else:
			order_id = frappe.db.get_value('Sales Order', {'custom_session_id': session_id}, 'name')
		return success_response(data=order_id)
	except Exception as e:
		frappe.logger('utils').exception(e)
		return error_response(e)
	


def submit_quotation(quot_doc, billing_address_id, shipping_address_id, payment_date,company_gstin):
    quot_doc.customer_address = billing_address_id
    quot_doc.shipping_address_name = shipping_address_id
    quot_doc.payment_schedule = []
    quot_doc.save()
    quot_doc.submit()
    return create_sales_order(quot_doc, payment_date,company_gstin)    




def create_sales_order(quot_doc, payment_date,company_gstin):
	so_doc = make_sales_order(quot_doc.name)
	if payment_date:
		payment_date = datetime.strptime(payment_date, "%d/%m/%Y").strftime("%Y-%m-%d")
		so_doc.delivery_date = datetime.strptime(payment_date, "%Y-%m-%d")
	else:
		transaction_date = datetime.strptime(so_doc.transaction_date, "%Y-%m-%d")
		so_doc.delivery_date = (transaction_date + timedelta(days=7)).date()
	so_doc.company_gstin = company_gstin
	so_doc.custom_session_id = quot_doc.session_id
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



def recently_bought_items(kwargs):
	try:
		from summitapp.summitapp.customizations.item.utils import get_detailed_item_list
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




def cancel_sales_order(kwargs):
	try:
		sales_order = kwargs.get("order_id")
		if frappe.db.exists("Sales Order", {"name": sales_order, "workflow_state": ["!=", "Cancelled"]}):
			frappe.db.set_value("Sales Order",sales_order,
					   {"workflow_state": "Cancelled",
		 				"order_status":"Cancelled",
						"docstatus":2
						})
			return success_response(data = f"{sales_order} is been Cancelled Successful")
		return error_response(f"{sales_order} doesn't exist")
	except Exception as e:
			frappe.logger("order").exception(e)
			return error_response(e)