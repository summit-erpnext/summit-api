import frappe
from summitapp.utils import success_response, error_response

def contact_us(kwargs):
    try:
        contact_us = frappe.get_doc("Contact Us")
        result = {
            "sales_email_id":contact_us.sales_email_id,
            "sales_contact_number":contact_us.sales_contact_number,
            "supports_email_id":contact_us.supports_email_id,
            "supports_contact_number":contact_us.supports_contact_number
        }
        return success_response(result)
    except Exception as e:
        frappe.logger("utils").exception(e)
        return error_response(str(e))   