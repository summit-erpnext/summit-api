# Copyright (c) 2022, 8848Digital LLP and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = get_columns(), get_data()
	return columns, data


def get_columns():
	columns = []
	columns.append({
		"fieldname": "user_name",
		"label" : frappe._("User Name"),
		"fieldtype": "Link",
		"options": "Customer"
	})
	columns.append({
		"fieldname": "store_credit_assigned",
		"label" : frappe._("Store Credit Assigned"),
		"fieldtype": "Data"
	})
	columns.append({
		"fieldname": "store_credit_used",
		"label" : frappe._("Store Credit Used"),
		"fieldtype": "Data"
	})
	columns.append({
		"fieldname": "store_credit_balance",
		"label" : frappe._("Store Credit Balance"),
		"fieldtype": "Data"
	})

	return columns

def get_data():
	user_list = frappe.db.get_list('Store Credit Assigned',{}, ['user as user_name'], group_by = 'user')
	for user in user_list:
		user['store_credit_assigned'] = sum(i.credit_amount for i in amount_list('Store Credit Assigned', user.user_name, 'credit_amount'))
		user['store_credit_used'] = sum(i.debit_amount for i in amount_list('Store Credit Used', user.user_name, 'debit_amount'))
		user['store_credit_balance'] = user['store_credit_assigned'] - user['store_credit_used']
	return user_list
	
def amount_list(table, user, field):
	return frappe.db.get_list(table, {'user': user}, field)