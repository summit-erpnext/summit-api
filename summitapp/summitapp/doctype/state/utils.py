import frappe
from summitapp.utils import success_response

def states(kwargs):
	state_list = frappe.db.get_list('State', filters = {}, fields =['name', 'country'], ignore_permissions=True)
	return success_response(state_list)



def countries(kwargs):
	country_list = frappe.db.get_list('Country', filters = {}, fields =['name as country_name'], ignore_permissions=True)
	return success_response(data = country_list)