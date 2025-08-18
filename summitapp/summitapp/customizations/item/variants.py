import frappe
from summitapp.utils import success_response, error_response
from summitapp.api.v2.utils import (get_item_images, get_stock_info, get_default_variant, variant_thumbnail_reqd)

def get_product_variants(kwargs):
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
            attr = list({var.get(attribute) for var in variant_info if var.get(attribute)})
            sorted_attr = frappe.get_all("Item Attribute Value",{"abbr":["IN", attr], "parent": attribute},pluck='abbr', order_by="idx asc")
            sorted_attribute = frappe.get_all("Item Attribute Value",{"abbr":["IN", attr], "parent": attribute},pluck='attribute_colour', order_by="idx asc")
            attributes_list.append({
                "field_name": attribute, 
                "label": f"Select {attribute}", 
                "values": sorted_attr, 
                "hex_value": sorted_attribute,
                "default_value": get_default_variant(item_code, attribute), 
                "display_thumbnail": variant_thumbnail_reqd(item_code, attribute)
            })
        attr_dict = {'item_code': item_code,
                        'variants': get_variant_info(variant_list),
                        'attributes': attributes_list}
        return success_response(data=attr_dict)
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(e)



# Get Variants Helper Functions
def get_variant_details(filters):
    ignore_perm = frappe.session.user == "Guest"
    variants = frappe.get_list('Item', {'variant_of': filters.get('item_code')}, ignore_permissions=ignore_perm)
    return variants


def get_variant_info(variant_list):
    varient_info_list = []
    for item in variant_list:
        varient_info = {
            'variant_code': item.name,
            'slug': get_variant_slug(item.name),
            }
        item_varient_attribute = get_item_varient_attribute(item.name)
        for attribute in item_varient_attribute:
            varient_info[attribute['attribute']] = attribute['abbr']
            attr_colour_key = f"{attribute['attribute'].lower()}_attr_colour"
            varient_info[attr_colour_key] = attribute['attr_colour']
        varient_info['stock'] = True if get_stock_info(item.name, 'stock_qty') != 0 else False
        varient_info['image'] = get_item_images(item.name)
        varient_info_list.append(varient_info)
        
    return varient_info_list


def get_item_varient_attribute(item_code):
    item_varient_details = frappe.get_all('Item Variant Attribute',
							{'parent': item_code}, ['attribute', 'attribute_value'])
    for item in item_varient_details:
        item["abbr"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'abbr')
        item["attr_colour"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'attribute_colour')
    return item_varient_details


def get_variant_slug(item_code):
	return frappe.get_value('Item',{'item_code':item_code},'slug')



def get_variants_listing(**kwargs):
    try:
        slug = kwargs.get("item")
        show_variant_on_product_card = kwargs.get("show_variant_on_product_card")
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
        summit_setting =  frappe.get_value("Summit Settings","show_variant_on_product_card", as_dict=1)
        if show_variant_on_product_card == True:
            if summit_setting.show_variant_on_product_card == 1:
                attribute = summit_setting.variant_attribute_on_product_card
                add_attribute_to_list(attribute, variant_info, item_code, attributes_list)
            else:
                for attribute in attributes:
                    add_attribute_to_list(attribute, variant_info, item_code, attributes_list)
        else:
            for attribute in attributes:
                add_attribute_to_list(attribute, variant_info, item_code, attributes_list)

        stock_len = len([var.get('stock') for var in variant_info if var.get('stock')])
        if show_variant_on_product_card == True:
            if summit_setting.show_variant_on_product_card == 1:
                variant_attribute_on_product_card = summit_setting.variant_attribute_on_product_card
                attr_dict = {'item_code': item_code,
                                'variants': get_variant_info_limited(variant_list,variant_attribute_on_product_card),
                                'attributes': attributes_list}
                return success_response(data=attr_dict)
        attr_dict = {'item_code': item_code,
                        'variants': get_variant_info(variant_list),
                        'attributes': attributes_list}
        return success_response(attr_dict)
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(e)
    

def add_attribute_to_list(attribute, variant_info, item_code, attributes_list):
    attr = list({var.get(attribute) for var in variant_info if var.get(attribute)})
    sorted_attr = frappe.get_all("Item Attribute Value",{"abbr":["IN", attr], "parent": attribute},pluck='abbr', order_by="idx asc")
    sorted_attribute = frappe.get_all("Item Attribute Value",{"abbr":["IN", attr], "parent": attribute},pluck='attribute_colour', order_by="idx asc")
    attributes_list.append({
        "field_name": attribute, 
        "label": f"Select {attribute}", 
        "values": sorted_attr, 
        "default_value": get_default_variant(item_code, attribute), 
        "hex_value": sorted_attribute,
        "display_thumbnail": variant_thumbnail_reqd(item_code, attribute)
    })



def get_variant_info_limited(variant_list,variant_attribute_on_product_card):
    varient_info_list = []
    for item in variant_list:
        variant_info = {
            'variant_code': item.name,
            'slug': get_variant_slug(item.name),
            }
        item_variant_attribute = get_item_varient_attribute(item.name)
        for attribute in item_variant_attribute:
            if attribute['attribute'] == variant_attribute_on_product_card:
                variant_info[attribute['attribute']] = attribute['abbr']
                attr_colour_key = f"{attribute['attribute'].lower()}_attr_colour"
                variant_info[attr_colour_key] = attribute['attr_colour']
        variant_info['stock'] = True if get_stock_info(item.name, 'stock_qty') != 0 else False
        variant_info['image'] = get_item_images(item.name)
        varient_info_list.append(variant_info)
    return varient_info_list



def get_item(item_code, size, colour):  # for cart
	variant_list = get_variant_details({'item_code': item_code})
	variants = get_variant_info(variant_list)
	if size and colour:
		item_code = [i.get('variant_code') for i in variants if i.get('size') == size and i.get('colour') == colour]
	elif size:
		item_code = [i.get('variant_code') for i in variants if i.get('size') == size]
	elif colour:
		item_code = [i.get('variant_code') for i in variants if i.get('colour') == colour]
	else:
		item_code = [item_code]
	return item_code[0] if item_code else []