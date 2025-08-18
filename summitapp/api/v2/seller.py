
import frappe
from summitapp.summitapp.doctype.registration_details.utils import get_seller_registration

#Get Seller Registration
@frappe.whitelist()
def get(kwargs):
    get_seller_registration(kwargs)