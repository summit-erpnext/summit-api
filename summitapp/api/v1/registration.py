import frappe
from frappe.exceptions import DuplicateEntryError
from summitapp.utils import success_response, error_response, send_mail

def customer_signup(kwargs):
	try:
		"""
			Creates required documents when a customer registers
			In case of any errors, it will delete the created documents
		"""
		if frappe.db.exists('User', kwargs.get('usr') or kwargs.get('email')):
			return error_response('Customer Already Exists')
		frappe.local.login_manager.login_as('Administrator')
		create_user(kwargs)
		customer_doc = create_customer(kwargs)
		if not kwargs.get('via_google', False):
			create_address(kwargs,customer_doc.name) # for billing
			kwargs['address_type'] = "Shipping"
			create_address(kwargs, customer_doc.name) # for shipping
		frappe.local.login_manager.login_as(kwargs.get('usr') or kwargs.get('email'))
		return success_response(data = customer_doc.name)
	except Exception as e:
		frappe.logger("registration").exception(e) 
		delete_documents(kwargs,customer_doc.name)
		return error_response(e)

def change_password(kwargs):
	try:
		email = frappe.session.user
		if email == "Guest":
			return error_response('Please Login As A Customer')

		if not frappe.db.exists('User',email):
			return error_response('please login to change password')
		user = frappe.get_doc('User',email)
		data = kwargs.get('data')
		if frappe.local.login_manager.check_password(email, data.get('old_password')):
			user.new_password = data.get('new_password')
			user.save(ignore_permissions=True)
			return success_response()
		return error_response("Incorrect Old Password!")
	except Exception as e:
		frappe.logger("registration").exception(e) 
		return error_response(e)


def delete_documents(kwargs,id):
	# Delete existing documents in case of errors
	frappe.local.login_manager.login_as('Administrator')
	frappe.delete_doc("User",kwargs.get('email'),ignore_permissions=True, ignore_missing=1)
	frappe.delete_doc("Customer",id,ignore_permissions=True)
	frappe.delete_doc("Address",{'email':kwargs.get('email')},ignore_permissions=True)
	#ToDo: Delete dynamic link associated with address


def create_address(kwargs,id):
	#Create an Address Document for the Customer
	address_doc = frappe.get_doc({
			'doctype': "Address",
			'gstin': kwargs.get('gst_number'),
			'state': kwargs.get('state'),
			'gst_state': kwargs.get('state'),
			'email_id': kwargs.get('email'),
			'phone': kwargs.get('contact_no') or kwargs.get("contact"),
			'city': kwargs.get('city'),
			'address_type': kwargs.get("address_type","Billing"),
			'address_line1': kwargs.get('address') or kwargs.get("address_1"),
			'address_line2': kwargs.get("address_2"),
			'address_title': id,
			'pincode': kwargs.get('postal_code'),
			'gst_category': 'Registered Regular' if kwargs.get('gst_number') else 'Unregistered',
			'is_primary_address': bool(kwargs.get("address_type", "Billing") == "Billing"),
			'is_shipping_address': bool(kwargs.get("address_type") == "Shipping")
		})
	address_doc.append("links",{
		"link_doctype" :"Customer", 
		"link_name" : id
	})
	address_doc.save(ignore_permissions=True)
	
	return address_doc

def create_user(kwargs):
	#Creates User Document for the Customer
	user_doc = frappe.get_doc({
		"doctype": 'User',
		'email': kwargs.get("usr") or kwargs.get('email'),
		'send_welcome_email': False,
		'new_password': kwargs.get("password") or frappe.generate_hash(),
		'first_name': kwargs.get("name"),
		'language':kwargs.get("language_code"),
		'roles': [{"doctype": "Has Role", "role": "Customer"}],
		"api_key" : frappe.generate_hash(length=15),  
		"api_secret" : frappe.generate_hash(length=15) 
	})
	user_doc.insert(ignore_permissions=True)

def create_customer(kwargs):
	# create customer document
	customer_doc = frappe.get_doc({
		'doctype':"Customer",
		'customer_name': kwargs.get('name'),
		'mobile_no': kwargs.get('contact_no') or kwargs.get("contact") ,
		'mobile_number': kwargs.get('contact_no') or kwargs.get("contact"),
		'email_id': kwargs.get('usr') or kwargs.get('email'),
		'email': kwargs.get('usr') or kwargs.get('email'),
		'type': 'Individual', 
		'customer_group': kwargs.get('customer_group',frappe.db.get_single_value("Webshop Settings","default_customer_group")),
		'territory': 'All Territories'
		})
	customer_doc.insert(ignore_permissions=True)
	return customer_doc

def reset_password(kwargs):
	try:
		email = kwargs.get('email')
		if not frappe.db.exists('User',email):
			return error_response('User With this email Does Not Exists')
		user = frappe.get_doc('User',email)
		user.new_password = kwargs.get('new_password')
		user.save(ignore_permissions=True)
		return success_response(data="Password Changed")
	except Exception as e:
		frappe.logger("registration").exception(e) 
		return error_response(e)

def send_reset_link(kwargs):
	try:
		email = kwargs.get('email')
		if not frappe.db.exists('User',email): return error_response('User With this email Does Not Exists')
		if not kwargs.get('link'): return error_response('Please Send Redirection Link')
		send_mail("Send Reset Link", [email], {'link': kwargs.get('link')})
		return success_response(data="Reset Link Sent")
	except Exception as e:
		frappe.logger("registration").exception(e) 
		return error_response(e)

def create_registration(kwargs):
	doc = frappe.new_doc("Registration Details")
	doc.update({
		"username": kwargs.get("name"),
		"designation": kwargs.get("designation"),
		"company_name": kwargs.get("company_name"),
		"address": kwargs.get("address"),
		"city": kwargs.get("city"),
		"pincode": kwargs.get("postal_code"),
		"state": kwargs.get("state"),
		"gst_no": kwargs.get("gst_number"),
		"email_id": kwargs.get("email"),
		"contact_no": kwargs.get("contact_no"),
		"is_existing": kwargs.get("existing_customer"),
		"buy_parts_for": kwargs.get("buy_parts_for")
	})
	doc.insert(ignore_permissions=True)

	return success_response(data=doc.name)

def add_subscriber(kwargs):
	if not kwargs.get("email"):
		return error_response("Email is mandatory")
	try:
		doc = frappe.get_doc({
			"doctype": "Subscriber",
			"email": kwargs.get("email"),
			"mobile_number": kwargs.get("mobile_no")
		}).insert(ignore_permissions=1)
		return success_response("Subscriber Added")
	except DuplicateEntryError:
		return success_response("Already subscribed")
	except Exception as e:
		return error_response("Something went wrong")