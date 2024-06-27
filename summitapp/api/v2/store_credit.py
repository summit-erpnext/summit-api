import frappe
from summitapp.utils import error_response, success_response


# Whitelisted Function
def put(kwargs):
    try:
        email = frappe.session.user
        if email == "Guest":
            return error_response('please login to continue')
        if customer:=frappe.db.exists('Customer', {'email': email}):
            store_credit = float(kwargs.get('store_credit',0))
            if not validate(customer, store_credit):
                return error_response('Store Credit Limit Exceeded')

            sc_added = add_store_credit_to_quotation(store_credit)
            return success_response(data=sc_added)

        else:
            return error_response('Customer Does Not Exists')

    except Exception as e:
        return error_response(e)

# Whitelisted Function
def delete(kwargs):
    try:
        email = frappe.session.user
        if email == "Guest":
            return error_response('please login to continue')
        if frappe.db.exists('Customer', {'email': email}):
            sc_added = add_store_credit_to_quotation(0)
            return success_response(data=sc_added)

        else:
            return error_response('Customer Does Not Exists')
    except Exception as e:
        return error_response(e)

def validate(customer, store_credit):
    sc_info = frappe.db.get_value("Customer", customer, "balance_amount")
    return bool(sc_info >= store_credit)

def add_store_credit_to_quotation(store_credit):
    from webshop.webshop.shopping_cart.cart import _get_cart_quotation 
    quotation = _get_cart_quotation()
    quotation.store_credit_used = store_credit
    quotation.save(ignore_permissions=True)
    return "Store Credit Updated"
