# Copyright (c) 2023, 8848Digital LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class StoreCreditAssigned(Document):
	def validate(self):
		self.total_amount = self.get("balance_amount",0) + self.get("credit_amount",0)

	def on_submit(self):
		frappe.db.set_value("Customer",self.customer,"balance_amount", self.total_amount)