import frappe
from summitapp.utils import make_payment_entry


def validate(self, method):
	try:
		if not self.taxes:
			sales_taxes_and_charges_template = self.taxes_and_charges
			if not sales_taxes_and_charges_template: return "Item Added To Cart"
			from erpnext.controllers.accounts_controller import get_taxes_and_charges
			taxes = get_taxes_and_charges("Sales Taxes and Charges Template",sales_taxes_and_charges_template)
			# quot = frappe.get_doc('Quotation', self.name)
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
	# self.append("taxes", {••••••••••
	# 	"charge_type": "Actual",
	# 	"account_head": charges.get("assembly_account"),
	# 	"tax_amount": self.total_assembly_charges,
	# 	"description": "Assembly Charges"
	# })
	# self.append("taxes", {
	# 	"charge_type": "Actual",
	# 	"account_head": charges.get("payment_gateway_account"),
	# 	"tax_amount": charges.get("gateway_charges"),
	# 	"description": "Payment Gateway Charges"
	# })
	if self.total_assembly_charges:
		for tax_row in self.get("taxes", []):
			if tax_row.get("description") == "Assembly Charges":
				tax_row.tax_amount = self.total_assembly_charges
		

def on_payment_authorized(self, *args, **kwargs):
	try:
		if args[1] == 'Authorized':
			from summitapp.api.v2.order import razorpay_place_order
			fil_lst = {'order_id': self.name}
			party_name = {"party_name":self.party_name}
			razorpay_place_order(fil_lst['order_id'], party_name=party_name['party_name'])
			# if sales_order:
			# 	make_payment_entry(sales_order)
			# frappe.local.response['type'] = 'redirect'
			# frappe.local.response['location'] = "http://localhost:3000/thankyou/SAL-ORD-2022-00525"
			return "thankyou"
		else:
			return 'failed'
	except Exception as e:
		frappe.logger('utils').exception(e)



