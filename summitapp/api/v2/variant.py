import frappe
from summitapp.utils import error_response, success_response, get_access_level, get_allowed_categories, get_allowed_brands, get_child_categories
import json
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe.utils.global_search import search
from frappe.utils import flt, cint, today, add_days
from summitapp.api.v2.translation import translate_result
from summitapp.api.v2.utils import (check_brand_exist, get_filter_list, get_filter_listing,
                                       get_slide_images, get_stock_info, 
									   get_processed_list, get_item_field_values, 
									   get_field_names, create_user_tracking,
									   get_default_variant, variant_thumbnail_reqd,
                                    	get_list_product_limit,get_customer_id)



# Whitelisted Function
@frappe.whitelist(allow_guest=True)
def get_variants(kwargs):
    try:
        slug = kwargs.get('item')
        item_code = frappe.get_value('Item', {'slug': slug})
        filters = {'item_code': item_code}
        variant_list = get_variant_details(filters)
        variant_info = get_variant_info(variant_list)
        attributes = []
        for varient in variant_info:
            varient_attribute = get_item_varient_attribute(varient['variant_code'])
            for att in varient_attribute:
                if att.get('attribute') not in attributes:
                    attributes.append(att.get('attribute'))
        attributes_list = []

        for attribute in attributes:
            # Collect unique values for the attribute
            unique_values = {var.get(attribute) for var in variant_info if var.get(attribute)}
            attr = list(unique_values)
            # Sort the attribute values based on 'abbr' and 'idx'
            sorted_attr = frappe.get_all(
                "Item Attribute Value",
                filters={"abbr": ["IN", attr], "parent": attribute},
                pluck='abbr',
                order_by="idx asc",
            )
            # Append the attribute details to the list
            attributes_list.append({
                "field_name": attribute,
                "label": f"Select {attribute}",
                "values": attr,
                "default_value": get_default_variant(item_code, attribute),
                "display_thumbnail": variant_thumbnail_reqd(item_code, attribute)
            })

        stock_len = len([var.get('stock') for var in variant_info if var.get('stock')])
        attr_dict = {'item_code': item_code,
                        'variants': get_variant_info(variant_list),
                        'attributes': attributes_list}
        return success_response(data=attr_dict)
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(e)


def get_variant_info(variant_list):
    variant_info_list = []
    for item in variant_list:
        variant_info = {
            'variant_code': item.name,
            'slug': get_variant_slug(item.name),
        }
        item_variant_attribute = get_item_varient_attribute(item.name)
        for attribute in item_variant_attribute:
            if frappe.db.get_value("Item Attribute", attribute["attribute"], "numeric_values") == 1:
                variant_info[attribute['attribute']] = attribute["attribute_value"]
            else:
                variant_info[attribute['attribute']] = attribute['abbr']
        variant_info['stock'] = get_stock_info(item.name, 'stock_qty') != 0
        variant_info['image'] = get_slide_images(item.name, False)
        variant_info_list.append(variant_info)
    return variant_info_list


def get_item_varient_attribute(item_code):
    item_varient_details = frappe.get_all('Item Variant Attribute',
							{'parent': item_code}, ['attribute', 'attribute_value'])
    
    for item in item_varient_details:
        if frappe.db.get_value("Item Attribute", item["attribute"], "numeric_values") == 1:
            item["abbr"] = item["attribute_value"]
        else:
            item["abbr"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'abbr')
    return item_varient_details


# Get Variants Helper Functions
def get_variant_details(filters):
	ignore_perm = frappe.session.user == "Guest"
	return frappe.get_list('Item', {'variant_of': filters.get('item_code')}, ignore_permissions=ignore_perm)


def get_variant_slug(item_code):
	return frappe.get_value('Item',{'item_code':item_code},'slug')


def get_default_variant(item_code, attribute):
    attr = frappe.get_value("Item Variant Attribute", {"variant_of": item_code, "is_default":1, "attribute": attribute},"attribute_value")
    if attr: 
        if frappe.db.get_value("Item Attribute", attribute, "numeric_values") == 1:
            attr = frappe.db.get_value('Item Variant Attribute',filters={'variant_of': item_code,'is_default': 1,"attribute_value":attr},fieldname='attribute_value')
            return attr
        else:
            attr = frappe.get_value("Item Variant Attribute", {"variant_of": item_code, "is_default":1, "attribute": attribute},"attribute_value")
            return frappe.get_value('Item Attribute Value', {'attribute_value': attr}, 'abbr')


def variant_thumbnail_reqd(item_code, attribute):
	res = frappe.get_value("Item Variant Attribute", {"parent": item_code, "display_thumbnail":1, "attribute": attribute},"name")
	return bool(res)
    