import frappe
from summitapp.utils import success_response

@frappe.whitelist()
def val_pincode(kwargs):
	pincode = True if frappe.db.exists(
		'Pin Code', kwargs.get('pincode')) else False
	return success_response(data=pincode)