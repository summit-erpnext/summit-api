import frappe

def on_cancel(self, method):
	if self.seller_order_confirmation:
		seller_order = frappe.get_doc("Seller Order Confirmation", self.seller_order_confirmation)
		seller_order.commission_sales_invoice_created = 0
		seller_order.save()

def on_submit(self, method):
	from erpnext.accounts.utils import unlink_ref_doc_from_payment_entries
	if self.is_return:
		doc = frappe.get_doc("Sales Invoice", self.return_against)
		unlink_ref_doc_from_payment_entries(doc)
