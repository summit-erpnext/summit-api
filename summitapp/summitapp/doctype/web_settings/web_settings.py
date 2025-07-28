# Copyright (c) 2023, 8848Digital LLP and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from summitapp.summitapp.doctype.web_settings.utils import add_category_from_sub

class WebSettings(Document):
	def validate(self):
		add_category_from_sub(self,"allowed_sub_categories", "allowed_categories")

