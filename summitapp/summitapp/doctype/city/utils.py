import frappe
from summitapp.utils import success_response

def cities(kwargs):
	city_list = frappe.db.get_list('City', filters = {'state': kwargs.get('state')}, fields =['name', 'state', 'country'], ignore_permissions=True)
	return success_response(data=city_list)