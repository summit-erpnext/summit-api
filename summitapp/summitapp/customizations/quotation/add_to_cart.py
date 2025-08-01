import frappe, json
from summitapp.utils import (error_response, success_response, get_company_address, check_guest_user,create_access_token)
from summitapp.api.v2.product import get_recommendation
from summitapp.api.v2.utils import get_price_list
from frappe.utils import flt

def put_cart_products(kwargs):  
	try:
		access_token = None
		email = None
		session_id = None
		auth_header = frappe.request.headers.get('Authorization')
		if not auth_header:
			access_token, email = create_access_token(kwargs)
		elif "token" not in auth_header:
			if not frappe.db.exists("Quotation",{"session_id":auth_header}):
				if frappe.db.exists("Access Token",{"token":auth_header}):
					access_token = frappe.get_value("Access Token",{"token":auth_header},["token"])
					email = frappe.get_value("Access Token",{"token":auth_header},["email"])
				else:
					return error_response("Incorrect Access Token")
			else:
				session_id = auth_header 
				access_token = auth_header
		if session_id:
			quotation_id = frappe.db.exists("Quotation", {"session_id": session_id, "status": "Draft"})
			if not quotation_id:
				return error_response("Invalid session ID or no matching Quotation found")
			quotation = frappe.get_doc("Quotation", quotation_id)
		items = kwargs.get('item_list')
		if isinstance(items,str):
			items = json.loads(items)
		item_list = []
		if not items:
			return error_response('Please Specify item list')

		allow_items_not_in_stock = frappe.db.get_single_value("Web Settings", "allow_items_not_in_stock")
		for row in items:
			kwargs.update({"item_only":1,"item_code":row.get("item_code"), "ptype":"Mandatory"})
			recommendations = get_recommendation(kwargs)
			if recommendations:
				for item in recommendations:
					if not item:
						continue
					item_list.append({"item_code": item, "quantity": row.get("quantity"),"size": row.get("size"),"purity": row.get("purity"),"wastage": row.get("wastage"),"colour": row.get("colour"),"remark": row.get("remark")})
			else:
				item_list.append({"item_code": row.get("item_code"), "quantity": row.get("quantity"),"size": row.get("size"),"purity": row.get("purity"),"wastage": row.get("wastage"),"colour": row.get("colour"),"remark": row.get("remark")})
		in_stock_status = True
		for item in item_list:
			quantity = item.get('quantity') or 1
			if product_bundle:=frappe.db.exists("Product Bundle", {'new_item_code': item.get("item_code")}):
				item_bundle_list = frappe.get_list("Product Bundle Item",{'parent':product_bundle},['item_code','qty'], ignore_permissions=1)
				for i in item_bundle_list:
					if int(get_stock_info(i.item_code, 'stock_qty')) < int(quantity) * flt(i.qty):
						in_stock_status = False
						break
			else:
				if int(get_stock_info(item.get("item_code"), 'stock_qty')) < int(quantity):
					in_stock_status = False
			if (not in_stock_status) and (not allow_items_not_in_stock): return error_response('Stock Not Available!')
		
		fields = {}
		if cust_name:=kwargs.get("cust_name"):
			fields["cust_name"] = cust_name
		if purity:=kwargs.get("purity"):
			fields["purity"] = purity
		if party_name:=kwargs.get("party_name"):
			fields["party_name"] = party_name
		if custom_party_name:=kwargs.get("custom_party_name"):
			fields["custom_party_name"] = custom_party_name	
		added_to_cart = add_item_to_cart(item_list, access_token, kwargs.get("currency"),fields)
		if added_to_cart == "Currency cannot be changed for the same cart.":
			return error_response(added_to_cart)
		elif added_to_cart != "Currency cannot be changed for the same cart.":
			response_data = {
				"access_token": access_token,
				"email":email,
				"data": added_to_cart,
				"notification":"Item has been added to cart"
			}
			return success_response(data = response_data)
	except Exception as e:
		frappe.logger('cart').exception(e)
		return error_response(e)
	
def add_item_to_cart(item_list, access_token, currency, fields={}):
    customer_id = frappe.db.get_value('Customer', {'email': frappe.session.user})
    quotation = create_cart(currency, access_token, customer_id)
    price_list = get_price_list(customer_id)
    
    # Check if currency is already set in the quotation
    if quotation.currency is not None and currency != quotation.currency:
        return 'Currency cannot be changed for the same cart.'
    
    quotation.update(fields)
    quotation.selling_price_list = price_list
    
    for item in item_list:
        if isinstance(item, dict):
            item_code = item.get("item_code")
            quantity = item.get("quantity")
            
            if item_code and quantity:
                quotation_items = [qi for qi in quotation.items if qi.item_code == item_code]
                
                if not quotation_items:
                    item_data = {
                        "doctype": "Quotation Item",
                        "item_code": item_code,
                        "qty": quantity
                    }
                    
                    if "size" in item:
                        item_data["size"] = item["size"]
                    if "wastage" in item:
                        item_data["wastage"] = item["wastage"]
                    if "remark" in item:
                        item_data["remark"] = item["remark"]
                    if "colour" in item:
                        item_data["colour"] = item["colour"]
                    if "purity" in item:
                        item_data["purity"] = item["purity"]
                    
                    quotation.append("items", item_data)
                else:
                    quotation_items[0].qty = quantity
    
    quotation.flags.ignore_mandatory = True
    quotation.flags.ignore_permissions = True
    quotation.payment_schedule = []
    quotation.save(ignore_permissions=True)

    item_codes = ", ".join([row.item_code for row in quotation.items])
    return f'Item {item_codes} Added To Cart'



def create_cart(currency,accees_token, party_name = None):
	or_filter = {
		"session_id": accees_token
	}
	if party_name:
		or_filter["party_name"] = party_name

	if quot:=frappe.db.get_list("Quotation",filters = {'status': 'Draft'}, or_filters = or_filter, fields=['name','currency']):
		quot_doc = frappe.get_doc('Quotation', quot[0].get('name'))
	else:
		quot_doc = frappe.new_doc('Quotation')
		quot_doc.order_type = "Sales"
		quot_doc.party_name = party_name
		quot_doc.session_id = accees_token
		quot_doc.currency = currency
		if check_guest_user(frappe.session.user):
			quot_doc.gst_category = "Unregistered"
		company_addr = get_company_address(quot_doc.company)
		quot_doc.company_address = company_addr.get("company_address")
		quot_doc.company_gstin = company_addr.get("gstin")
	return quot_doc


