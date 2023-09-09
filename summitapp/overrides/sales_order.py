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

