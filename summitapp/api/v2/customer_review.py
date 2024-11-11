import frappe
from summitapp.utils import success_response,error_response
import datetime
from datetime import datetime
import json
from frappe.model.db_query import DatabaseQuery
import json
from better_profanity import profanity

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


def create_customer_review_and_send_mail(kwargs):
    try:
        user = frappe.session.user
        comment = kwargs.get("comment")
        if not user:
            return error_response(data="User does not exist")
        customer = frappe.get_doc("Customer", {"account_manager": user}).name
        if not customer:
            return error_response(data="Customer does not exist")
        if not comment:
            return error_response(data="Add Your Comment")
        item_name = kwargs.get("item_code")
        existing_review = frappe.db.exists(
            "Customer Reviews", 
            {"email": user, "item_code": item_name}
        )
        if existing_review:
            print(customer)
            customer_review_send_email(
                customer, 
                user, 
                message="You cannot add another review for this product as it already exists."
            )
            return success_response(data="Duplicate review: You cannot add another review for this product.")
            # return error_response("Duplicate review: You cannot add another review for this product.")
        
        sales_order_list = frappe.db.sql(
            """
                SELECT so.name
                FROM `tabSales Order` AS so
                LEFT JOIN `tabSales Order Item` AS soi ON soi.parent = so.name
                WHERE so.customer = %(customer)s
                AND so.order_status = "Order Delivered"
                AND soi.item_code = %(item_name)s;
            """, {"customer": customer, "item_name": item_name}, as_dict=True)

        if sales_order_list:
            if comment:
                data = check_inappropriate_content(comment)
                if data["contains_inappropriate"] == False:
                    customer_review_send_email(customer, user,message = f"Your review for the product has been successfully submitted.",verified = 0)
                    return success_response(data=len(sales_order_list)) 
                elif data["contains_inappropriate"] == True:
                    customer_review_send_email(customer, user, message = f"Your Review has been rejected.")
                    return success_response(data=len(sales_order_list))
            return success_response(data=len(sales_order_list))
        else:
            customer_review_send_email(customer, user, message = f"Your are not allowed to review this product.")
            return success_response(data=len(sales_order_list))
    
    except Exception as e:
        frappe.logger("cr").exception(e)
        return error_response(str(e))


def customer_review_send_email(customer, user, message, verified=0):
    try:
        print("Sending email...")
        frappe.sendmail(
            recipients=[user],
            subject="New Customer Review Submission",
            message=message
        )
        print("Email sent successfully")
        request_data = json.loads(frappe.request.data)
        print("Request Data:", request_data)
        # Create a new Customer Reviews document
        cr_doc = frappe.new_doc('Customer Reviews')
        cr_doc.name1 = customer
        cr_doc.email = user
        cr_doc.comment = request_data.get('comment')
        cr_doc.item_code = request_data.get('item_code')
        cr_doc.item_name = request_data.get('item_name')
        cr_doc.rating = request_data.get('rating')
        cr_doc.verified = verified
        cr_doc.date = datetime.now()

        images = request_data.get("images", [])
        print("Review images:", images)
        for i in images:
            image = i.get('image')
            cr_doc.append("review_image", {
                "doctype": "Return Replacement Image",
                "image": image
            })
        cr_doc.save(ignore_permissions=True)

    except Exception as e:
        frappe.logger("cr").exception(f"Error in sending email: {str(e)}")
        # frappe.throw("Failed to send email")
        return error_response(str(e))

def check_inappropriate_content(text):
    profanity.load_censor_words()
    has_profanity = profanity.contains_profanity(text)
    censored_text = profanity.censor(text)
    result = {
        'original_text': text,
        'contains_inappropriate': has_profanity,
        'censored_text': censored_text
    }
    return result
    # print(f"Original text: {result['original_text']}")
    # print(f"Contains inappropriate content: {result['contains_inappropriate']}")
    # print(f"Censored text: {result['censored_text']}")

