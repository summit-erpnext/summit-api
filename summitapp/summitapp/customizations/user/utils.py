import frappe
from frappe.utils.password import check_password
from frappe import auth
from summitapp.utils import success_response, error_response


# Manualy generated access token
def get_api_token(kwargs):
    try:
        usr = kwargs.get("usr")
        pwd = kwargs.get("pwd")
        try:
            check_password(usr, pwd)
        except Exception as e:
            return e
        doc = frappe.get_doc("User", {"name": usr})
        api_key = doc.api_key
        api_secret = doc.get_password("api_secret")
        if api_key and api_secret:
            api_token = "token " + api_key + ":" + api_secret
            full_name = doc.full_name
            user_roles = frappe.get_roles(usr)
            result = {"access_token": api_token, "full_name": full_name, "user_role":user_roles}
        return success_response(data=result)
    except Exception as e:
        frappe.logger("token").exception(e)
        return error_response(e)


def get_token_with_email(email):
    doc = frappe.get_doc("User", {"email": email})
    api_key = doc.api_key
    api_secret = doc.get_password("api_secret")
    if api_key and api_secret:
        api_token = "token " + api_key + ":" + api_secret
        access_api_token = api_token

    return access_api_token


def get_token_with_mobile(mobile):
    try:
        doc = frappe.get_doc("User", {"mobile_no": mobile})
        if doc:
            api_key = doc.api_key
            api_secret = doc.get_password("api_secret")

            if api_key and api_secret:
                api_token = "token " + api_key + ":" + api_secret
                result = {"access_token": api_token, "full_name": doc.full_name}
                return success_response(result)
            else:
                # Handle the case where either api_key or api_secret is not found
                return error_response("API key or API secret not found")
    except Exception as e:
        frappe.logger("token").exception(e)
        return error_response(e)    


    
