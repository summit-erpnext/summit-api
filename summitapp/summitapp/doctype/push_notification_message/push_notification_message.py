# Copyright (c) 2023, 8848 Digital LLP and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from summitapp.api.v1.push_notification import send_notification


class PushNotificationMessage(Document):
	# pass
	def after_insert(self):
		send_notification()