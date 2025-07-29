import frappe
from summitapp.summitapp.doctype.wishlist.utils import add_items_to_wishlist, remove_items_from_wishlist, wishlist_items


# Add items to wishlist
@frappe.whitelist()
def add_to_wishlist(kwargs):
	return add_items_to_wishlist(kwargs)

# Remove Items from Wishlist
@frappe.whitelist()
def remove_from_wishlist(kwargs):
	return remove_items_from_wishlist(kwargs)

# Get wishlist items
@frappe.whitelist()
def get_wishlist_items(kwargs):
	return wishlist_items(kwargs)