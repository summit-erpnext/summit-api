import frappe
from summitapp.utils import error_response, success_response


def get_dealer(kwargs):
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