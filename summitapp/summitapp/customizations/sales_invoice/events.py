from summitapp.summitapp.customizations.sales_invoice.utils import on_cancel_commission_sales_invoice, on_submit_unlink_ref_doc_from_payment_entries

def on_cancel(self, method):
	on_cancel_commission_sales_invoice(self)

def on_submit(self, method):
	on_submit_unlink_ref_doc_from_payment_entries(self)
	