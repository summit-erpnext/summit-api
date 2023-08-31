# Copyright (c) 2023, 8848Digital LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProductPageField(Document):
	pass
	# def validate(self):
	# 	self.get_item_fields()

	# def get_item_fields(self):
	# 	meta = frappe.get_meta("Item")
	# 	fields = meta.fields
	# 	item_field =[]
	# 	for field in fields:
	# 		# print(field.fieldname)
	# 	# 	item_field.append(field.fieldname)
	# 	# print("Item Field",item_field)	
	# 		self.append("product_fields",{
	# 		"field":field.fieldname
	# 		})
