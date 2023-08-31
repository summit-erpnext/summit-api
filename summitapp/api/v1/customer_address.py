import frappe
from summitapp.utils import success_response,error_response, update_customer

def get(kwargs):
	try:
		user_id = kwargs.get('user_id')
		email = frappe.session.user
		filters = {}
		if add_type := kwargs.get('type'):
			filters = {"address_type": add_type}
		if email == "Guest":
			return error_response('Please login AS A Customer')
			
		if not user_id:
			user_id = frappe.get_value("Customer",{'email':email})
		customer = frappe.db.get_value("Customer",user_id,'name')
		address_result = []
		if address:=kwargs.get('address_id'): 
			address_obj = frappe.db.get_value("Address",address,"*")
			data = get_details(customer, address_obj)
			return success_response(data = data)
		else:
			address_all_doc = frappe.get_all("Dynamic Link",{"link_doctype":"Customer","link_name":user_id},'*')
			for record in address_all_doc:
				filters['name'] = record.parent
				if address:=frappe.db.exists("Address",filters):
					address_obj = frappe.db.get_value("Address",address, "*")
					data = get_details(customer, address_obj) 
					address_result.append(data)
		
			return success_response(data = address_result)
	except Exception as e:
		frappe.logger("erpnext").exception(e)
		return error_response(e)


def put(kwargs):
	try:
		if "random" in frappe.session.user:
			from summitapp.api.v1.signin import signin_as_guest
			return signin_as_guest(kwargs)
		email = kwargs.get("email") if "random" in frappe.session.user else frappe.session.user
		user_id = kwargs.get('user_id')
		if not kwargs.get('user_id'):
			user_id = frappe.get_value("Customer",{'email': email})
		if not user_id:
			user_id = update_customer(data = {
				"customer_name": kwargs.get("name"),
				"email": email,
				"mobile_number": kwargs.get("contact")
			})
			if quot_name:=frappe.db.exists("Quotation",{"status":"Draft","owner": frappe.session.user,"party_name":["is","null"]}):
				frappe.db.set_value("Quotation", quot_name, "party_name", user_id)
		
		address_doc = add_address(kwargs,user_id)
		return success_response(data={"address_id":address_doc.name, "customer_id":user_id})
	except Exception as e:
		frappe.logger("erpnext").exception(e)
		return error_response(e)

def update_quotation(docname):
	doc = frappe.get_doc("Quotation", docname)
	doc.save(ignore_permissions=True)
	return "Quotation Updated"

def get_details(customer, address_obj):
	return {
			"address_id" : address_obj.name,
			"user_id" : customer,
			"name" : address_obj.address_title,
			"address_title":address_obj.get('address_title'),
			"address_1" :address_obj.get('address_line1'),
			"address_2" : address_obj.get('address_line2'),
			"city" : address_obj.get('city'),
			"state" : address_obj.get('state'),
			"email" : address_obj.get('email_id'),
			"contact" : address_obj.get('phone'),
			"country":address_obj.get('country'),
			'gst_number': address_obj.get('gstin'),
			'postal_code': address_obj.get('pincode'),
			"address_type": address_obj.get('address_type'),
			"full_address": get_full_address(address_obj),
			"set_as_default" : bool(address_obj.is_primary_address) if address_obj.get('address_type') =='Billing' else bool(address_obj.is_shipping_address),
			"same_as_shipping_address" : bool(address_obj.is_shipping_address)
		}

def get_full_address(add):
	result = ''
	fields = ["address_title", "address_line1", "address_line2", "city", "state", "country"]
	result = ", ".join(add.get(d) for d in fields if add.get(d))
	result += f"-{add.pincode}"
	return result

def add_address(kwargs,user_id):
	if kwargs.get('address_id'): return update_address(kwargs,kwargs.get('address_id'))
	doc_dict = {
			'doctype': 'Address',
			"address_title":kwargs.get('name'),
			"address_line1" :kwargs.get('address_1'),
			"address_line2" : kwargs.get('address_2'),
			"city" : kwargs.get('city'),
			"state" : kwargs.get('state'),
			"email_id" : kwargs.get('email'),
			"phone" : kwargs.get('contact'),
			"country":kwargs.get('country'),
			"email_id" : kwargs.get('email'),
			'gstin': kwargs.get('gst_number'),
			'pincode': kwargs.get('postal_code'),
			"address_type": kwargs.get('address_type'),
			'gst_category': 'Registered Regular' if kwargs.get('gst_number') else 'Unregistered'
		}
	if kwargs.get('address_type') == 'Billing':
		doc_dict.update({'is_primary_address': kwargs.get('set_as_default',0)})
	else:
		doc_dict.update({'is_shipping_address': kwargs.get('set_as_default',0)})
	doc = frappe.get_doc(doc_dict)
	doc.append("links",{
			"link_doctype" :"Customer", 
			"link_name" : user_id
		})
	doc.insert(ignore_permissions=True)
	return doc

def update_address(kwargs,address_id):
	doc = frappe.get_doc('Address', address_id)
	doc.address_title=kwargs.get('name')
	doc.address_line1 =kwargs.get('address_1')
	doc.address_line2 = kwargs.get('address_2')
	doc.city = kwargs.get('city')
	doc.state = kwargs.get('state')
	doc.email_id = kwargs.get('email')
	doc.pincode = kwargs.get('postal_code')
	doc.phone = kwargs.get('contact')
	doc.country=kwargs.get('country')
	doc.email_id = kwargs.get('email')
	doc.gstin= kwargs.get('gst_number')
	doc.address_type= kwargs.get('address_type')
	if kwargs.get('address_type') == 'Billing':
		doc.is_primary_address= kwargs.get('set_as_default',0)
	else:
		doc.is_shipping_address= kwargs.get('set_as_default',0)
	doc.is_primary_address= kwargs.get('set_as_default',0)
	doc.gst_category = 'Registered Regular' if kwargs.get('gst_number') else 'Unregistered'
	doc.save(ignore_permissions=True)
	return doc