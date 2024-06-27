import frappe
from frappe.utils.password import check_password
from frappe import auth
from summitapp.utils import success_response, error_response

# Manualy generated access token
def get_access_token(kwargs):
    try:
        usr = kwargs.get("usr")
        pwd = kwargs.get("pwd")
        try:
            check_password(usr,pwd)
        except Exception as e:
            return e
        doc = frappe.get_doc("User", {'name':usr})
        api_key = doc.api_key
        api_secret = doc.get_password('api_secret')
        if api_key and api_secret:
            api_token = "token "+api_key+":"+api_secret
            full_name = doc.full_name
            result = {
                "access_token": api_token,
                "full_name":full_name
                }
        return success_response (data=result)
    except Exception as e:
        frappe.logger('token').exception(e)
        return error_response(e)

# Dynamic Generated Access token
def login(kwargs):
    try:
        usr = kwargs.get("usr")
        pwd = kwargs.get("pwd")
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Authentication Error!"
        }

        return

    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)

    frappe.response["message"] = {
        "success_key":1,
        "message":"Authentication success",
        "sid":frappe.session.sid,
        "api_key":user.api_key,
        "api_secret":api_generate,
        "api_token" : "token "+user.api_key+":"+api_generate,
        "username":user.username,
        "email":user.email
    }

def generate_keys(user_id):
    user = frappe.get_doc("User", user_id)
    if not user:
        return "User not found."
    api_key = frappe.generate_hash(length=15)
    api_secret = frappe.generate_hash(length=15)
    user.api_key = api_key
    user.api_secret = api_secret
    user.save(ignore_permissions=True)
    return api_secret


@frappe.whitelist()
def generate_api_keys_for_existing_users():
    users = frappe.get_all("User", filters={"user_type": "System User"},fields=["name"])
    frappe.log_error("users",users)
    for user in users:
        user_doc = frappe.get_doc("User", user.name)
        if not user_doc.get("api_key") and not user_doc.get("api_secret"):
            frappe.db.set_value("User",user.name,{"api_key":frappe.generate_hash(length=15),"api_secret":frappe.generate_hash(length=15)})
@frappe.whitelist()
def generate_keys():
    frappe.enqueue(generate_api_keys_for_existing_users, timeout=1500) 


def auth(kwargs):
    login_manager = frappe.auth.LoginManager()
    login_manager.authenticate(user=kwargs.get('usr'),pwd=kwargs.get('pwd'))
    login_manager.post_login()    
    return get_access_token(kwargs)

def get_token(email):
	doc = frappe.get_doc("User", {'email':email})
	api_key = doc.api_key
	api_secret = doc.get_password('api_secret')
	if api_key and api_secret:
		api_token = "token "+api_key+":"+api_secret
		access_api_token = api_token
			
	return access_api_token 