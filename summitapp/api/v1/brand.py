from shutil import ExecError
import frappe
from summitapp.utils import error_response, success_response, get_allowed_brands
from summitapp.api.v1.product import get_list, get_details
from summitapp.api.v1.utils import get_field_names

def get(kwargs):
    filters = {"publish":1}
    if brands:=get_allowed_brands():
        filters["name"] = ["in", brands]
    
    ignore_permissions = bool(frappe.session.user == "Guest")  
    field_names = get_field_names('Brand')
    brand_list = frappe.db.get_list('Brand',
                                filters = filters,
                                fields = field_names,
                                ignore_permissions=ignore_permissions)
    transformed_brand_list = []

    for brand in brand_list:
        transformed_brand = get_brand_json(brand)
        transformed_brand['url'] = f"/brand/{brand.get('slug')}"
        transformed_brand_list.append(transformed_brand)
    return success_response(data=transformed_brand_list)


def get_brand_json(brand):
    transformed_brand = {}
    for field_name in brand:
        transformed_brand[field_name] = brand[field_name]
    return transformed_brand

def get_product_list(kwargs):
    try:
        brand_name = kwargs.get('brand_name')
        brand_name = frappe.db.get_value('Brand', {'slug': brand_name}, 'name')
        return get_list({"brand" : brand_name})
    except Exception as e:
        frappe.logger('brand').exception(e)
        return error_response(e)

def get_product_details(kwargs):
    try:
        brand_name , item = kwargs.get('brand_name'), kwargs.get('item')
        brand_name = frappe.db.get_value('Brand', {'slug': brand_name}, 'name')
        return get_details({"brand":brand_name,  "item" : item})
    except Exception as e:
        frappe.logger('brand').exception(e)
        return error_response(e)