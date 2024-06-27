import frappe
from frappe.model.document import Document
from frappe.utils.password import encrypt,decrypt
class customencryptiontask(Document):
	pass
	
@frappe.whitelist()
def set_encrypted_value(doc):
	try:
		if isinstance(doc, str):
			doc = frappe.parse_json(doc)  
		details = []
		
		if len(doc.get("email", "")) < 50: 
			doc.email = encrypt(doc.email)
			print("docemail",doc.email)
			frappe.db.set_value('custom encryption task', doc.name, 'email', doc.email)

		if len(doc.get("phone_no", "")) < 50: 
			doc.phone_no = encrypt(doc.phone_no)
			print("docphone",doc.phone_no)
			frappe.db.set_value('custom encryption task', doc.name, 'phone_no', doc.phone_no)

		email_return = decrypt(doc.email)
		print("email return",email_return)
		phone_no_return = decrypt(doc.phone_no)
		print("phone return",phone_no_return)
		details.append(email_return)
		details.append(phone_no_return)
		print("details",details)
		return details

	except Exception as e:
		frappe.logger('token').exception(e)