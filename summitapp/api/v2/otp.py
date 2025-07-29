import frappe
from summitapp.summitapp.customizations.sms.utils import (sent_otp, verify, sent_twilio_sms, sent_email_otp,
                                                          sent_pinnacle_sms, login_with_mob_otp, sent_otp_message, sent_twilio_otp)

# send otp
@frappe.whitelist()
def send_otp(kwargs):
    return sent_otp(kwargs)


# verify otp
@frappe.whitelist()
def verify_otp(kwargs):
    return verify(kwargs)


# send twillow sms
@frappe.whitelist(allow_guest=True)
def send_twilio_sms(user, phone_number, otp):
    return sent_twilio_sms(user, phone_number, otp)


# send otp on email
@frappe.whitelist()
def send_email_otp(kwargs):
    return sent_email_otp(kwargs)
   

# send pinnacle sms
@frappe.whitelist()
def send_pinnacle_sms(kwargs):
    return sent_pinnacle_sms(kwargs)


# login with mobile otp
@frappe.whitelist()   
def login_with_mobile_otp(kwargs):
    return login_with_mob_otp(kwargs)


# send otp sms
@frappe.whitelist(allow_guest=True)
def send_otp_message(kwargs):
    return sent_otp_message(kwargs)


#
@frappe.whitelist(allow_guest=True)
def send_twilio_otp(kwargs):
    return sent_twilio_otp(kwargs)