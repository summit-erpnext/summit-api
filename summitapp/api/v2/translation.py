import frappe
from frappe import _
from summitapp.summitapp.doctype.translation_text.utils import languages, translation_text

# Get Languages
@frappe.whitelist()
def get_languages(kwargs):
    return languages(kwargs)


# Get Translation Text
@frappe.whitelist()
def get_translation_text(kwargs):
    return translation_text(kwargs)