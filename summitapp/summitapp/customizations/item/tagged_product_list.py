import frappe, json
from summitapp.utils import success_response, error_response
from summitapp.summitapp.customizations.item.utils import json_handler, get_access_level, get_tagged_product_limit
from summitapp.api.v2.translation import translate_result
from summitapp.api.v2.utils import get_processed_list

def tagged_products(kwargs):
    try:
        currency = kwargs.get("currency")
        if not kwargs.get('tag'):
            return error_response("key missing 'tag'")

        tag = kwargs.get('tag')
        tag_doc = frappe.get_doc("Featured Collection", tag)
        product_limit = tag_doc.set_product_limit
        side_banner_image = tag_doc.tag_image
        items = frappe.get_list(
            "Tags MultiSelect", 
            {"tag": tag}, 
            pluck='parent', 
            ignore_permissions=True
        )
        customer_id = kwargs.get("customer_id")
        res = get_detailed_item_list(currency, items, customer_id, None, product_limit)
        response = {"message": {
            "msg": "success",
            "side_banner": side_banner_image,
            "data": res
        }}
        response_data = json.dumps(response, default=json_handler)
        return success_response(data=response_data)
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))
    

def get_detailed_item_list(currency, items, customer_id=None, filters=None, product_limit=None):
    from itertools import islice

    filters = filters or {}
    customer_id = customer_id or frappe.db.get_value("Customer", {"email": frappe.session.user}, 'name')
    access_level = get_access_level(customer_id)
    
    item_filters = {
        "name": ["in", items],
        "access_level": access_level,
        "disabled": 0
    }
    item_filters.update(filters)

    user_role = frappe.session.user
    apply_product_limit = get_tagged_product_limit(user_role, customer_id)

    data = frappe.get_list('Item', filters=item_filters, fields="*", ignore_permissions=True)

    if product_limit and apply_product_limit == 1:
        data = list(islice(data, product_limit))  

    result = get_processed_list(currency, data, customer_id, "product")
    return translate_result(result)    