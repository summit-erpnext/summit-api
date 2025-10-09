import frappe
from .utils import get_item_field_details as _get_item_field_details


@frappe.whitelist()
def get_item_field_details():    
    return _get_item_field_details()
