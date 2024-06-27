# Copyright (c) 2024, 8848 Digital LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import secrets
from cryptography.fernet import Fernet

class Encryption(Document):
    def validate(self, method=None):
        try:
            # Generate a random encryption key
            encryption_key = generate_random_key()

            # Save the key to the document or wherever it's needed
            self.set('encryption_key', encryption_key)

            encrypt_sensitive_data(self)
        except Exception as e:
            frappe.logger('token').exception(e)

def generate_random_key():
    try:
        return secrets.token_urlsafe(32).encode('utf-8')
    except Exception as e:
        frappe.logger('token').exception(e)

def encrypt_function(data, key):
    try:
        cipher_suite = Fernet(key)
        encrypted_data = cipher_suite.encrypt(data.encode('utf-8'))
        return encrypted_data.decode('utf-8')
    except Exception as e:
        frappe.logger('token').exception(e)

def encrypt_sensitive_data(doc):
    try:
        # Retrieve the actual values from the document
        email = doc.email
        phone = doc.phone

        # Encrypt the data
        encrypted_email = encrypt_function(email, doc.encryption_key)
        encrypted_phone = encrypt_function(phone, doc.encryption_key)

        # Save the encrypted values back to the document
        doc.email = encrypted_email
        doc.phone = encrypted_phone

        # Check if the document already exists in the database
        existing_doc = frappe.get_doc(doc.doctype, doc.name)
        if existing_doc:
            # Update the existing document instead of inserting a new one
            existing_doc.update(doc)
            existing_doc.save()
        else:
            # Save the new document to the database
            doc.insert()
    except Exception as e:
        frappe.logger('token').exception(e)

