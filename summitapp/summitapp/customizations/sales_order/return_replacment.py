import frappe
from summitapp.utils import error_response, success_response

def create_return_replace_item(kwargs):
	try:
		if not kwargs.get('order_id'): return error_response('Please Sepecify Order')
		if not kwargs.get('product_id'): return error_response('Please Specify Product')
		if kwargs.get("product_id") and kwargs.get('order_id'):
			item_code = frappe.db.get_all("Sales Order Item", {"parent": kwargs.get('order_id')},"item_code",pluck="item_code")
			if kwargs.get('product_id') not in item_code:
				return error_response('Product Id Not Present')
		rr_doc = frappe.new_doc('Return Replacement Request')
		rr_doc.type = kwargs.get('type')
		rr_doc.reason = kwargs.get('reason')
		rr_doc.order_id = kwargs.get('order_id')
		rr_doc.product_id = kwargs.get('product_id')
		rr_doc.quantity = kwargs.get('quantity')
		images = kwargs.get("images",[])
		for file in images:
			image = file.get('image')
			rr_doc.append("return_replacement_image",{"image":image})
		rr_doc.save(ignore_permissions=True)
		return success_response(data={'docname':rr_doc.name, 'doctype': rr_doc.doctype})
	except Exception as e:
		return error_response(e)