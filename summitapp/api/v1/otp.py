import frappe
from summitapp.utils import success_response, error_response, send_mail,check_user_exists
import json
import random

def send_otp(kwargs):
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
    # Params For Send Mail- template_name, recipients(list), context(dict) 
    return send_mail("Send OTP", [username], {'otp': otp})

def verify_otp(kwargs):
    try:
        email = kwargs.get("email")
        key = f"{email}_otp"
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
        return error_response(e)