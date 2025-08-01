import frappe
from summitapp.summitapp.customizations.sms.utils import send_whatsapp_otp


@frappe.whitelist()
def send_otp_whatsapp(kwargs):
    return send_whatsapp_otp(kwargs)