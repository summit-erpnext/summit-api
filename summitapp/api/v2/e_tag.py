# import frappe
# import hashlib
# import json

# @frappe.whitelist(allow_guest=True)
# def get_product_list(kwargs=None):
#     """
#     E-Commerce API endpoint to fetch a list of products with E-Tag support.
#     """
#     # Fetch product data from the database
#     products = frappe.db.get_all('Item', fields=['name', 'slug', 'category', 'modified'])
    
#     # Serialize the response data to JSON
#     response_data = json.dumps(products, default=str)
    
#     # Generate E-Tag using a hash of the response data
#     etag = hashlib.md5(response_data.encode('utf-8')).hexdigest()
    
#     # Check the If-None-Match header from the request
#     client_etag = frappe.get_request_header('If-None-Match')
    
#     if client_etag == etag:
#         # If E-Tag matches, return 304 Not Modified
#         frappe.local.response['http_status_code'] = 304
#         return
    
#     # Return the product list in the response body
#     frappe.local.response["http_status_code"] = 200
#     frappe.local.response["type"] = "json"
#     return {
#         "status": "success",
#         "message": "Product list fetched successfully",
#         "data": custom_response(response,headers=None, etag)
#     }


# def custom_response(data, headers=None, etag):
#     response = Response()
#     response.mimetype = "application/json"
#     response.data = json.dumps(data, default=json_handler, separators=(",", ":"))
#     response.headers["Etag"] = etag
#     return response