import frappe
import hashlib
import json
from werkzeug.wrappers import Response
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def get_product_list(kwargs=None):
    try:
        filters = {"show_on_website": 1}
        products = frappe.db.get_list(
            "Item",
            fields=["name", "slug", "category", "modified",'show_on_website','has_variants'],
            filters=filters,
            order_by="modified desc"
        )
        response_data = json.dumps(products, default=json_handler)
        etag = handle_etag(response_data)
        if etag is None:
            return  
        response_body = {
            "status": "success",
            "message": "Product list fetched successfully",
            "data": products
        }
        return custom_response(response_body, etag=etag)

    except Exception as e:
        frappe.log_error(f"Error in get_product_list: {str(e)}")
        return custom_response({
            "status": "error",
            "message": f"Failed to fetch product list: {str(e)}"
        })


def json_handler(obj):
    if isinstance(obj, (datetime, frappe.utils.datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def custom_response(data, etag=None):
    response = Response(
        response=json.dumps(data, default=json_handler),
        mimetype="application/json"
    )
    if etag:
        response.headers["Etag"] = etag
    return response

def handle_etag(response_data):
    etag = hashlib.md5(response_data.encode('utf-8')).hexdigest()
    client_etag = frappe.get_request_header('If-None-Match')

    if client_etag == etag:
        frappe.local.response['http_status_code'] = 304
        return None

    return etag