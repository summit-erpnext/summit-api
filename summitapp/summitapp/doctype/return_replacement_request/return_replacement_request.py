# Copyright (c) 2022, 8848Digital LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ReturnReplacementRequest(Document):
	pass

@frappe.whitelist()
def get_items_from_sales(doctype, txt, searchfield, start, page_len, filters):
	where_clause = f""" where parent  = '{filters.get("sales_order")}' """ if filters.get("sales_order") else ""
	query = f"""SELECT item_code from `tabSales Order Item` {where_clause}  """
	print(query)
	return frappe.db.sql(query)