import frappe, json, requests, random
from summitapp.utils import success_response, error_response,send_mail,check_user_exists
from summitapp.api.v2.access_token import get_token_with_mobile
from frappe.utils import now_datetime

def sent_otp(kwargs):
    try:
        username = kwargs.get('usr')
        if not check_user_exists(username):
            return error_response('No account with this Email id')
        else:
            return generate_otp(username)
    except Exception as e:
        return error_response(e)
    

def generate_otp(username, otp=None):
    """
    Generate OTP For a user
    """
    try:
        if not otp:
            otp_length = 6
            otp = "".join([f"{random.randint(0, 9)}" for _ in range(otp_length)])
        if not username:
            frappe.throw(frappe._("NOEMAIL"), exc=LookupError)
        key = f"{username}_otp"
        otp_json = {
            "id": key,
            "otp": otp,
            "timestamp": str(frappe.utils.get_datetime().utcnow()),
        }
        rs = frappe.cache()
        rs.set_value(key, json.dumps(otp_json))
        return success_response( data = send_otp_to_email(username, otp) )
    except Exception as e:
        frappe.logger("otp").exception(e)
        return {"error": e}    
    
def send_otp_to_email(username, otp):
    return send_mail("Send OTP", [username], {'otp': otp})
    

def sent_email_otp(kwargs):
    try:
        username = kwargs.get('email')
        return generate_otp(username)
    except Exception as e:
        return error_response(e)    


def verify(kwargs):
    try:
        email = kwargs.get("email")
        phone = kwargs.get("phone")

        if email:
            key = f"{email}_otp"
        if phone:
            key = f"+{phone}_otp"
        else:
            key = f"{'user_phone_number'}_otp"
        otp = kwargs.get("otp")
        rs = frappe.cache()
        stored_otp = rs.get_value(key)
        if not stored_otp:
            msg = "OTP invalid, Please try again!"
            return error_response(msg)
        otp_json = json.loads(stored_otp)
        if str(otp) == otp_json.get("otp"):
            return success_response(data="OTP Verified")
        msg = "OTP invalid, Please try again!!"
        return error_response(msg)
    except Exception as e:
        frappe.logger("otp").exception(e)
        return {"error": e}



def sent_twilio_sms(user, phone_number, otp):
    """Send SMS via Twilio to a single phone number"""
    twilio_details = frappe.get_doc('Twilio Sms Settings')
    
    account_sid = twilio_details.account_sid
    auth_token = twilio_details.auth_token
    twilio_phone_number = twilio_details.twilio_phone_number
    twilio_api_url = twilio_details.twilio_api_url+f'2010-04-01/Accounts/{account_sid}/Messages.json'
    
    sms_body = (
        f'{user} is trying to login for mobile app please share the otp: {otp}'
    )    
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'To': phone_number,
        'From': twilio_phone_number,
        'Body': sms_body,
    }
    auth = (account_sid, auth_token)
    response = requests.post(twilio_api_url, headers=headers, data=data, auth=auth)
    
    return {
        'status_code': response.status_code,
        'response': response.json() if response.status_code == 201 else response.text,
        'phone': phone_number
    }


def sent_twilio_otp(kwargs):
    twilio_details=frappe.get_doc('Twilio Sms Settings')
    account_sid=twilio_details.account_sid
    auth_token=twilio_details.auth_token
    twilio_phone_number=twilio_details.twilio_phone_number
    twilio_api_url=twilio_details.twilio_api_url+f'2010-04-01/Accounts/{account_sid}/Messages.json'
    phone = kwargs.get("phone")
    phone_number = f"+{phone}"
    otp_length = 6
    otp = "".join([f"{random.randint(0, 9)}" for _ in range(otp_length)])
    key = f"{phone_number}_otp"
    otp_json = {
        "id": key,
        "otp": otp,
        "timestamp": str(frappe.utils.get_datetime().utcnow()),
    }
    rs = frappe.cache()
    rs.set_value(key, json.dumps(otp_json))
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'To': phone_number,
        'From': twilio_phone_number,
        'Body': f'Your Otp is {otp}',
    }
    auth = (account_sid, auth_token)
    response = requests.post(twilio_api_url, headers=headers, data=data, auth=auth)
    if response.status_code == 201:
        # frappe.msgprint(f"SMS sent: {response.json().get('sid')}")
        return success_response("OTP sent on your phone number!")
    else:
        frappe.msgprint(f"Failed to send SMS: {response.status_code}, {response.text}")


def sent_whatsapp_otp(user, summit_mobile_app_settings, phone_number, otp):
    summit_mobile_app_settings = frappe.get_doc(
        "Summit Mobile App Settings", "Summit Mobile App Settings"
    )
    
    # Clean the phone number format
    phone_number = phone_number.replace("+", "").replace("-", "")

    url = f"https://graph.facebook.com/v22.0/{summit_mobile_app_settings.phone_number_id}/messages"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {summit_mobile_app_settings.access_token}",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": summit_mobile_app_settings.template_name,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": user},
                        {"type": "text", "text": otp},
                    ],
                }
            ],
        },
    }
    response = requests.post(url, json=payload, headers=headers)
    
    return {
        'response': response.json(),
        'phone': phone_number
    }


def sent_otp_message(kwargs):
    user = frappe.db.get_value("User", kwargs.get("user"), "full_name")
    user_phone_number = kwargs.get("phone")
    summit_mobile_app_settings = frappe.get_doc("Summit Mobile App Settings", "Summit Mobile App Settings")
    
    # Check if any OTP method is enabled
    if (
        not summit_mobile_app_settings.send_sms_otp
        and not summit_mobile_app_settings.send_whatsapp_otp
    ):
        frappe.log_error("No OTP delivery method enabled", "OTP Error")
        return error_response("OTP delivery method not configured")

    # Get all recipient numbers from the child table
    recipient_numbers = []
    
    for record in summit_mobile_app_settings.summit_otp_reciever_numbers:
        recipient_numbers.append(record.otp_reciever_mobile_number)

    if not recipient_numbers:
        return error_response("No recipient numbers found")

    # Generate a single OTP for all recipients
    otp_length = 6
    otp = "".join([f"{random.randint(0, 9)}" for _ in range(otp_length)])
    
    # Store OTP for each recipient in cache
    rs = frappe.cache()
    key = f"{'user_phone_number'}_otp"
    otp_json = {
        "id": key,
        "otp": otp,
        "timestamp": str(frappe.utils.get_datetime().utcnow()),
    }
    rs.set_value(key, json.dumps(otp_json))
    
    # Initialize response tracking
    successful_sms = []
    successful_whatsapp = []
    failed_sms = []
    failed_whatsapp = []
    
    # Try sending to all recipients via SMS if enabled
    if summit_mobile_app_settings.send_sms_otp:
        for phone in recipient_numbers:
            try:
                sms_response = sent_twilio_sms(user, phone, otp)
                if sms_response['status_code'] == 201:
                    successful_sms.append(phone)
                else:
                    failed_sms.append(phone)
                    frappe.log_error(
                        f"Failed to send OTP on SMS to {phone}", 
                        sms_response['response']
                    )
            except Exception as e:
                failed_sms.append(phone)
                frappe.log_error(f"Exception sending SMS OTP to {phone}", str(e))

    # Try WhatsApp if it's enabled
    if summit_mobile_app_settings.send_whatsapp_otp:
        for phone in recipient_numbers:
            try:
                whatsapp_response = sent_whatsapp_otp(user, summit_mobile_app_settings, phone, otp)
                if (
                    isinstance(whatsapp_response['response'], dict)
                    and whatsapp_response['response'].get("messages")
                    and whatsapp_response['response']["messages"][0].get("id")
                ):
                    successful_whatsapp.append(phone)
                else:
                    failed_whatsapp.append(phone)
                    frappe.log_error(
                        f"Failed to send OTP on WhatsApp to {phone}", 
                        whatsapp_response['response']
                    )
            except Exception as e:
                failed_whatsapp.append(phone)
                frappe.log_error(f"Exception sending WhatsApp OTP to {phone}", str(e))

    # Prepare response message
    success = bool(successful_sms or successful_whatsapp)
    response_parts = []
    
    if successful_sms:
        response_parts.append(f"OTP sent via SMS")
    if successful_whatsapp:
        response_parts.append(f"OTP sent via WhatsApp")
    
    response_msg = ". ".join(response_parts)
    
    # Return final response
    if success:
        return success_response(response_msg)
    else:
        return error_response("Failed to send OTP to any number")

def sent_pinnacle_sms(kwargs):
    try:
        pinnacle_settings = frappe.get_doc("Pinnacle SMS Settings")
        phone = (kwargs.get("phone"))
        phone_number = f"+{phone}"
        otp_length = 6
        otp = "".join([f"{random.randint(0, 9)}" for _ in range(otp_length)])
        key = f"{phone_number}_otp"
        otp_json = {
            "id": key,
            "otp": otp,
            "timestamp": str(frappe.utils.get_datetime().utcnow()),
        }
        rs = frappe.cache()
        rs.set_value(key, json.dumps(otp_json))
        payload = json.dumps({
        "sender": pinnacle_settings.sender,
        "message": [
            {
            "number": phone_number,
            "text": f"Dear User, your OTP to register with Vortex Infotech is {otp} and is valid for 5 min.",
            "dlttempid": pinnacle_settings.dlttempid
            }
        ],
        "messagetype": pinnacle_settings.messagetype
        })
        headers = {
        'Content-Type': pinnacle_settings.contenttype,
        'apikey': pinnacle_settings.apikey,
       
        }
        response = requests.request("POST", pinnacle_settings.url, headers=headers, data=payload)
        json_response = response.json()
        print("json response",json_response)
        if json_response["code"] == 200 and json_response["status"] == "success":
            return success_response("OTP sent on your phone number!")
    except Exception as e:
        frappe.logger("otp").exception(e)
        return {"error": e}


def login_with_mob_otp(kwargs):
    try:
        mobile = kwargs.get('contact_no') or kwargs.get("contact") or kwargs.get("phone")
        user = get_token_with_mobile(mobile)
        if user.get('msg') == 'success':
            otp = verify(kwargs)
            if otp.get("data") == 'OTP Verified': 
                return user
            else:
                return error_response(otp.get("error"))
        else:
            return error_response('User not found with this mobile number')
    except Exception as e:
        frappe.logger("otp").exception(e)
        return error_response(e) 



def send_whatsapp_otp(kwargs):
    try:
        if isinstance(kwargs, str):
            kwargs = json.loads(kwargs)

        phone_number = get_customer_phone_number(kwargs)
        
        if not phone_number:
            frappe.throw("Phone number not found for the given email ID.")

        phone_number = f"+91{phone_number}"
        otp = generate_otp(phone_number)
  
       
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
