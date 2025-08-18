import frappe
from summitapp.summitapp.doctype.category.utils import get_breadcrums, mega_menu


# Get Braedcrums
@frappe.whitelist(allow_guest=True)
def breadcrums(kwargs):
	return get_breadcrums(kwargs)


# Get Mega Menu
@frappe.whitelist(allow_guest=True)
def get_mega_menu(kwargs):
	return mega_menu(kwargs)