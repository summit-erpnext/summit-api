import frappe
from summitapp.utils import error_response, success_response
from summitapp.api.v2.utils import get_processed_list
from summitapp.api.v2.product import get_item


def add_to_wishlist(kwargs):
	if frappe.session.user == "Guest":
		return error_response("Please login first.")
	item_code = get_item(kwargs.get('item_code'), kwargs.get('size'), kwargs.get('colour'))
	if not item_code:
		return error_response('Item Does Not Exist')

	if frappe.db.exists("Wishlist Item", {"item_code": item_code, "parent": frappe.session.user}):
		return success_response("Item already exist")

	web_item_data = frappe.db.get_value(
		"Website Item",
		{"item_code": item_code},
		[
			"website_image",
			"website_warehouse",
			"name",
			"web_item_name",
			"item_name",
			"item_group",
			"route",
		],
		as_dict=1,
	)

	wished_item_dict = {
		"item_code": item_code,
		"item_name": web_item_data.get("item_name"),
		"item_group": web_item_data.get("item_group"),
		"website_item": web_item_data.get("name"),
		"web_item_name": web_item_data.get("web_item_name"),
		"image": web_item_data.get("website_image"),
		"warehouse": web_item_data.get("website_warehouse"),
		"route": web_item_data.get("route"),
		"url": kwargs.get("url","/")
	}

	if not frappe.db.exists("Wishlist", frappe.session.user):
		# initialise wishlist
		wishlist = frappe.get_doc({"doctype": "Wishlist"})
		wishlist.user = frappe.session.user
		wishlist.append("items", wished_item_dict)
		wishlist.save(ignore_permissions=True)
	else:
		wishlist = frappe.get_doc("Wishlist", frappe.session.user)
		item = wishlist.append("items", wished_item_dict)
		item.db_insert()

	response = {'msg': 'success',
				'wishlist_count':len(wishlist.items),
				'data': 'Item added successfully'}
	return response

def remove_from_wishlist(kwargs):
	item_code = kwargs.get('item_code')
	if frappe.db.exists("Wishlist Item", {"item_code": item_code, "parent": frappe.session.user}):
		frappe.db.delete("Wishlist Item", {"item_code": item_code, "parent": frappe.session.user})
		frappe.db.commit()  # nosemgrep

		wishlist_items = frappe.db.get_values("Wishlist Item", filters={"parent": frappe.session.user})

		response = {'msg': 'success',
				'wishlist_count':len(wishlist_items),
				'data': 'Item removed successfully'}
		return response

def get_wishlist_items(kwargs):
	try:
		if frappe.session.user == "Guest":
			return error_response("Please Login first.")
		wishlist_items = frappe.db.get_list("Wishlist Item", {"parent": frappe.session.user},pluck='item_code', ignore_permissions=True)
		# return wishlist_items
		if kwargs.get('customer_id'):
			customer_id = kwargs.get('customer_id')
		elif frappe.session.user!="Guest":
			customer_id = frappe.db.get_value("Customer",{"email":frappe.session.user},'name')
		else:
			customer_id = None
		# data = get_list_data({"name":["in",wishlist_items]}, None, [])
		data = frappe.get_list('Item',{"name": ["in", wishlist_items]},"*")
		result = get_processed_list(None,data, customer_id, url_type = "product")
		response = {'msg': 'success',
					'wishlist_count':len(wishlist_items),
					'data': result}
		return response
	except Exception as e:
		frappe.logger("wishlist").exception(e)
		return e