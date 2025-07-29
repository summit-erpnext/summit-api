import frappe
from summitapp.utils import success_response, error_response

def customer_group(kwargs):
    customer_group = frappe.get_list("Customer Group", filters={"is_group":0}, fields=['name'])
    return success_response(customer_group)




def get_dealer_list(kwargs):
    try:
        state = kwargs.get('state')
        city = kwargs.get('city')
        brand = kwargs.get('brand')
        company_name = kwargs.get('store_name')
        filters = [["Customer", "customer_group", "=", "Dealer"]]
        if brand:
            filters.append(["Brand Multiselect", "name1", "in", [brand]])
        if frappe.session.user != "Guest":
            dealer_list = frappe.db.get_list(
                'Customer',
                filters=filters,
                fields=['name']
            )
        else:
            dealer_list = frappe.db.get_list(
                'Customer',
                filters=filters,
                fields=['name'],
                ignore_permissions=True
            )
        result = []
        for dealer in dealer_list:
            from summitapp.api.v2.profile import get_dealer_profile
            dealer_doc = frappe.get_doc('Customer', dealer['name'])
            result.append(get_dealer_profile(dealer_doc).get('data'))
        if result[0] == None:
            result = result[1:]
        if state:
            if result:
                result = list(filter(lambda d: d['state'] == state, result))
        if city:
            if result:
                result = list(filter(lambda d: d['city'] == city, result))
        if company_name:
            if result:
                result = list(
                    filter(lambda d: d['Trading / Company Name'] == company_name, result))
        return success_response(data=result)
    except Exception as e:
        frappe.logger('utils').exception(e)
        return error_response(e)