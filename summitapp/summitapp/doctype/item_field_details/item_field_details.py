# Copyright (c) 2025, 8848 Digital LLP and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from .utils import set_label_name_value,set_update_fields

class ItemFieldDetails(Document):
	def before_naming(self):
		set_label_name_value(self)
	def before_validate(self):
		set_update_fields(self)