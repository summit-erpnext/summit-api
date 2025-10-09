# Copyright (c) 2023, 8848Digital LLP and contributors
# For license information, please see license.txt

# import frappe
from frappe.utils.nestedset import NestedSet
from .utils import set_item_fields

class Category(NestedSet):
	def validate(self):
		set_item_fields(self)
