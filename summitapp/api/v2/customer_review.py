import frappe
from summitapp.utils import success_response,error_response
import datetime
from datetime import datetime
import json
from frappe.model.db_query import DatabaseQuery


@frappe.whitelist()
def create_customer_review(kwargs):
    try:
        if frappe.request.data:
            request_data = json.loads(frappe.request.data)
            if not request_data.get('item_code'): 
                return error_response('Please Specify Item Code')
            if not request_data.get('email'): 
                return error_response('Please Specify email')
            if not request_data.get('name'): 
                return error_response('Please Specify name')

            cr_doc = frappe.new_doc('Customer Reviews')
            cr_doc.name1 = request_data.get('name')
            cr_doc.email = request_data.get('email')
            cr_doc.comment = request_data.get('comment')
            cr_doc.item_code = request_data.get('item_code')
            cr_doc.item_name = request_data.get('item_name')
            cr_doc.rating = request_data.get('rating')
            cr_doc.verified = request_data.get('verified')
            cr_doc.date = datetime.now()
            images = request_data.get("images")
            for i in images:
                image = i.get('image')
                cr_doc.append(
                    "review_image",
                    {
                        "doctype": "Return Replacement Image",
                        "image":image
                    },
                )
            cr_doc.save(ignore_permissions=True)  
            return success_response(data={'docname': cr_doc.name, 'doctype': cr_doc.doctype})
    except Exception as e:
        frappe.logger("cr").exception(e)
        return error_response(str(e))




@frappe.whitelist()
def get_customer_review(kwargs):
    try:
        if not kwargs.get('item_code'): 
            return error_response('Please Specify Item Code')
        filters = {"item_code": kwargs.get("item_code")}
        cr_doc = frappe.get_list("Customer Reviews",
                                 filters=filters,
                                 fields=["name as review_doc", "name1 as name", "email", "comment", "item_code", "item_name", "rating", "date", "verified"])
        
        reviews_with_images = []
        for review in cr_doc:
            images = get_images(review['review_doc'])  # Fetch images for each review
            review['images'] = images  # Append images to the review
            reviews_with_images.append(review)
        response_data = reviews_with_images
        count = get_count("Customer Reviews",filters=filters)
        return {'msg': 'success', 'data': response_data, 'total_count': count}
    
    except Exception as e:
        frappe.logger("cr").exception(e)
        return error_response(str(e))


def get_images(doc):
    try:
        rw_images = frappe.get_all("Return Replacement Image",
                                   filters={"parent": doc},
                                   fields=["image"])
        return rw_images
    except Exception as e:
        frappe.logger("profile").exception(e)
        return error_response(str(e))


def get_count(doctype, **args):
	distinct = "distinct " if args.get("distinct") else ""
	args["fields"] = [f"count({distinct}`tab{doctype}`.name) as total_count"]
	res = DatabaseQuery(doctype).execute(**args)
	data = res[0].get("total_count")
	return data