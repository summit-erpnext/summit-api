import frappe
import requests
import json
import random
from frappe.utils import now_datetime
from summitapp.utils import success_response, error_response

@frappe.whitelist()
def send_otp_whatsapp(kwargs):
    try:
        if isinstance(kwargs, str):
            kwargs = json.loads(kwargs)

        phone_number = get_customer_phone_number(kwargs)
        
        print("MOBILE",phone_number)
        if not phone_number:
            frappe.throw("Phone number not found for the given email ID.")

        phone_number = f"+91{phone_number}"
        otp = generate_otp(phone_number)
        print("OTP",otp)
       
        settings = frappe.get_single("WhatsApp Settings")
        if not (settings.enabled and settings.token and settings.phone_id and settings.version and settings.url):
            frappe.throw("WhatsApp is not properly configured. Please check the settings.")

        url = f"{settings.url}{settings.version}/{settings.phone_id}/messages"

        print("URL",settings.token)
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": "hello_world",  
                "language": {
                    "code": "en_US"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": otp
                            }
                        ]
                    }
                ]
            }
        }

        headers = {
            'Authorization': f'Bearer {settings.token}',
            'Content-Type': 'application/json'
        }

        # Make the API request
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Log or handle the response
        if response.status_code == 200:
            return success_response(response.json())
        else:
            frappe.log_error(response.text, "WhatsApp OTP Send Failed")
            return success_response(response.json())
    except Exception as e:
        frappe.logger('OTP').exception(e)
        return error_response(e)    


def get_customer_phone_number(kwargs):
    return frappe.get_value("Customer", filters={"email_id": kwargs.get("email_id")}, fieldname="mobile_no")


def generate_otp(phone_number):
    otp_length = 6
    otp = "".join([str(random.randint(0, 9)) for _ in range(otp_length)])
    key = f"{phone_number}_otp"
    otp_json = {
        "id": key,
        "otp": otp,
        "timestamp": str(now_datetime()),
    }
    frappe.cache().set(key, json.dumps(otp_json))
    return otp
