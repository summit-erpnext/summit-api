import frappe
from summitapp.utils import make_payment_entry


def on_submit(self, method=None):
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
			# frappe.local.response['type'] = 'redirect'
			# frappe.local.response['location'] = "http://localhost:3000/thankyou/SAL-ORD-2022-00525"
			return "thankyou"
		else:
			return 'failed'
	except Exception as e:
		frappe.logger('utils').exception(e)

def on_cancel(self, method=None):
    if self.workflow_state == "Cancelled":
        frappe.db.set_value("Sales Order",self.name,"order_status","Cancelled")

def validate(self, method=None):
    print("VALIDATE")
    send_sales_order_api(self)
    if self.workflow_state == "Order Placed":
        self.order_status = "Pending for Approval"

def on_update_after_submit(self, method=None):
    if self.workflow_state == "Billed":
        frappe.db.set_value("Sales Order",self.name,"order_status","Billed")
    elif self.workflow_state == "Delivery":
        frappe.db.set_value("Sales Order",self.name,"order_status","Out For Delivery")
    elif self.workflow_state == "Submitted":
        frappe.db.set_value("Sales Order",self.name,"order_status","Order Delivered")    

def autoname(self,method=None):
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


import frappe
import requests
import json

def send_sales_order_api(doc):
    summit_settings = frappe.get_single("Summit Settings")
    url = f"{summit_settings.socket_site_url}/api/sales-order"
    print("URL",url)
    headers = {"Content-Type": "application/json"}
    print("###")
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
        print("msg order")
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code != 200:
                frappe.log_error(f"Error in Sales Order API: {response.text}", "Sales Order API Error")
        except Exception as e:
            frappe.log_error(f"Exception: {str(e)}", "Sales Order API Exception")

