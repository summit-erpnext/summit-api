import frappe
from summitapp.utils import error_response, success_response, get_access_level, get_allowed_categories, get_allowed_brands, get_child_categories
import json
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe.utils.global_search import search
from frappe.utils import flt, cint, today, add_days
from summitapp.api.v2.translation import translate_result
from summitapp.api.v2.e_tag import handle_etag, handle_response
from summitapp.api.v2.utils import (check_brand_exist, get_filter_list, get_filter_listing,
                                       get_item_images, get_stock_info, 
									   get_processed_list, get_item_field_values, 
									   get_field_names, create_user_tracking,
									   get_default_variant, variant_thumbnail_reqd,
                                    	get_list_product_limit,get_customer_id,get_customer_wise_loyalty_points)
from werkzeug.wrappers import Response
import datetime

@frappe.whitelist(allow_guest=True)
def get_list(kwargs):
    try:
        create_user_tracking(kwargs, "Product Listing") # new doc + commit
        internal_call = kwargs.get("internal", 0) 
        category_slug = kwargs.get('category')
        page_no = cint(kwargs.get('page_no', 1)) - 1
        web_settings = frappe.get_cached_doc("Web Settings")
        user_role = frappe.session.user
        customer_id, customer_group = get_customer_id(kwargs) # db call customer + get_logged user api call
        kwargs["customer_id"] = customer_id
        kwargs["customer_group"] = customer_group
        limit = kwargs.get('limit', 20)
        if not kwargs.get('limit'):
            product_limit = get_list_product_limit(user_role, customer_group, web_settings) # web settings doc + customer and customer group db call
            limit = product_limit 
        filter_list = kwargs.get('filter')
        field_filters = kwargs.get("field_filters")
        or_filters = kwargs.get("or_filters")
        price_range = kwargs.get('price_range')
        search_text = kwargs.get('search_text')
        currency = kwargs.get('currency')
        sort_by = kwargs.get('sort_by')
        access_level = get_access_level(customer_group) #db call csutomer + customer group
        vehicle_filters = kwargs.get('vehicle_filters')
        if not search_text:
            order_by = None
            filter_args = {"access_level": access_level}
            if category_slug:
                child_categories = get_child_categories(category_slug) # 4 db calls on category
                filter_args["category"] = ['in', child_categories]
            if kwargs.get('brand'):
                filter_args["brand"] = frappe.get_value('Brand', {'slug': kwargs.get('brand')})
            if kwargs.get('item'):
                item_value = frappe.get_value('Item', {'name': kwargs.get('item')}) #recheck use case
                if item_value:
                    filter_args["name"] = item_value
            if "review" in category_slug:
                review_list = frappe.get_list("RND Review", { "ss_selection": "", "if_selection": "Accepted" }, pluck="name")
                filter_args["name"] = ["in", review_list]
                filter_args["show_on_website"] = 1

            filters = get_filter_listing(user_role,filter_args, web_settings) # web settings
            type = 'brand-product' if check_brand_exist(filters) else 'product'
            if field_filters:
                field_filters = json.loads(field_filters)
                for value in field_filters.values():
                    if len(value) == 2 and value[0] == 'like':
                        value[1] = f"%{value[1]}%"
                filters.update(field_filters)
            if or_filters:
                or_filters = json.loads(or_filters)
                for value in or_filters.values():
                    if len(value) == 2 and value[0] == 'like':
                        value[1] = f"%{value[1]}%"
            if filter_list:
                filter_list = json.loads(filter_list)
                filters, sort_order = append_applied_filters(filters, filter_list)
                if sort_order:
                    order_by = 'sequence {}'.format(sort_order)
                    del filters['sequence']
            if vehicle_filters:
                vehicle_filters = json.loads(vehicle_filters)
                vehicle_filter_conditions = parse_vehicle_filter(vehicle_filters)
                filters.update(vehicle_filter_conditions)
            debug = kwargs.get("debug_query", 0)
            count, data = get_list_data(kwargs,order_by, sort_by, filters, price_range, None, page_no, vehicle_filters,limit,or_filters=or_filters, debug=debug)
        else:
            type = 'product'
            global_items = search(search_text, doctype='Item')
            count, data = get_list_data(kwargs,None, None, {}, price_range, global_items, page_no, None, limit)
            
        result = get_processed_list(currency, data, customer_id, type) # summit settings doc per row dyanamic fields values and variants
        total_count = count
        translated_item_fields = translate_result(result) #nested loop for transalation
        response_data = json.dumps(translated_item_fields, default=json_handler)

        if internal_call:
            return response_data

        if sort_by == "low_to_high" or sort_by == "high_to_low":
            translated_item_fields = sort_item_by_price(translated_item_fields, sort_by) 
        else:
            translated_item_fields = sort_item_by_price(translated_item_fields, price_range)

        response_body = {
            'msg': 'success',
            'data': translated_item_fields,
            'total_count': total_count
        }
        return response_body

    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))



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

import frappe, json, re
from frappe import _
from typing import Any, Dict, List, Optional, Tuple

# ----------------------------
# Utilities
# ----------------------------

def normalize_fieldname(name: str) -> str:
    """Convert human-readable names into valid fieldnames: 'Weight Range' -> 'weight_range'"""
    return re.sub(r'\s+', '_', name.strip().lower())


def build_filters(base_filters: Dict[str, Any], filter_list: Optional[str]) -> Dict[str, Any]:
    """
    Merge base filters with dynamic filters from request.
    Supports dict-style and list-style filter payloads.
    """
    filters = dict(base_filters)
    if not filter_list:
        return filters

    try:
        parsed_filters = json.loads(filter_list)

        # Case 1: Dict style ({"Category": "X", "sections": [...]})
        if isinstance(parsed_filters, dict):
            for key, val in parsed_filters.items():
                if key == "sections":
                    continue
                filters[normalize_fieldname(key)] = val

            for section in parsed_filters.get("sections", []):
                fieldname = normalize_fieldname(section.get("name", ""))
                values = section.get("value", [])
                if fieldname and values:
                    filters[fieldname] = ["in", values] if len(values) > 1 else values[0]

        # Case 2: List style ([{"name":"..","value":[..]}, ...])
        elif isinstance(parsed_filters, list):
            for section in parsed_filters:
                fieldname = normalize_fieldname(section.get("name", ""))
                values = section.get("value", [])
                if fieldname and values:
                    filters[fieldname] = ["in", values] if len(values) > 1 else values[0]

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Filter Parsing Error")

    return filters


def build_prev_next_items(
    item_slug: str, kwargs: Dict[str, Any], item_category: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Compute previous and next slugs for given item based on filters and sort order.
    """
    # Extract sorting info
    sort_by = kwargs.get("sort_by") or "creation"
    order_by = None  # decided inside get_list_data

    # Base filters
    base_filters = {"category": item_category, "show_on_website": 1, "disabled": 0}
    filters = build_filters(base_filters, kwargs.get("filter"))

    # Fetch all items for navigation
    total_count, all_items = get_list_data(
        kwargs=kwargs,
        order_by=order_by,
        sort_by=sort_by,
        filters=filters,
        price_range=None,
        global_items=None,
        page_no=None,  # fetch all for prev/next
        vehicle_filters=None,
        limit=0,  # 0 means no limit
    )

    # Find current index
    current_index = next((i for i, d in enumerate(all_items) if d["slug"] == item_slug), None)

    prev_slug, next_slug = None, None
    if current_index is not None:
        if current_index > 0:
            prev_slug = all_items[current_index - 1]["slug"]
        if current_index < len(all_items) - 1:
            next_slug = all_items[current_index + 1]["slug"]

    return prev_slug, next_slug


def get_thumbnail_images(translated_item_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build thumbnail images list based on colour attributes from item & variants.
    """
    thumbnail_images, colours = [], []

    # Add base item image if Colour exists
    if (
        translated_item_fields.get("slide_img")
        and "Colour" in translated_item_fields["product_attributes"].keys()
    ):
        colour = translated_item_fields["product_attributes"]["Colour"]
        if colour not in colours:
            thumbnail_images.append({
                "field_name": "Colour",
                "Colour": colour,
                # "image": translated_item_fields.get("slide_img")[0]
            })
            colours.append(colour)

    # Add variant images
    for var in translated_item_fields.get("variants", []):
        if var.get("image") and "Colour" in var and var["Colour"] not in colours:
            thumbnail_images.append({
                "field_name": "Colour",
                "Colour": var["Colour"],
                "image": var.get("image")[0],
            })
            colours.append(var["Colour"])

    return thumbnail_images


def get_item_details_dict(item: Dict[str, Any], kwargs: Dict[str, Any], customer_id: Optional[str], currency: str) -> Dict[str, Any]:
    """
    Build complete item details dictionary with translations, variants, attributes, etc.
    """
    field_names = get_field_names("Details")
    loyalty_points_map = get_customer_wise_loyalty_points(customer_id, currency)

    # Translate item fields
    item_fields = get_item_field_values(currency, item, customer_id, None, field_names, loyalty_points_map, None, None)
    translated_item_fields = {fname: _(val) for fname, val in item_fields.items()}

    # Default placeholders
    translated_item_fields.update({
        "variants": [],
        "attributes": [],
        "is_template": False,
    })

    # Check variants/template
    varient_item, has_varient = frappe.db.get_value(
        "Item", {"slug": item.slug}, ["variant_of", "has_variants"]
    ) or (None, 0)

    if varient_item or has_varient == 1:
        template = item.slug if has_varient == 1 else varient_item
        translated_item_fields["is_template"] = bool(has_varient == 1)

        processed_items_varient = get_variants({"item": template})["data"]
        if processed_items_varient.get("item_code"):
            translated_item_fields["item_code"] = processed_items_varient["item_code"]

        translated_item_fields["variants"] = processed_items_varient.get("variants", [])
        translated_item_fields["attributes"] = processed_items_varient.get("attributes", [])

    # Product attributes
    product_attributes = {}
    if not translated_item_fields["is_template"]:
        for attr in get_item_varient_attribute(item.name):
            product_attributes[attr["attribute"]] = attr["abbr"]
    translated_item_fields["product_attributes"] = product_attributes

    # Thumbnail images
    translated_item_fields["thumbnail_images"] = get_thumbnail_images(translated_item_fields)

    # Prev / Next items
    prev_slug, next_slug = build_prev_next_items(item.slug, kwargs, item.category)
    translated_item_fields["previous_item"] = prev_slug
    translated_item_fields["next_item"] = next_slug
    translated_item_fields["item_field_details"] = get_item_field_details(item.category,item.name)
    return translated_item_fields


def get_item_field_details(category,item):
    if not (category or item):
        return []
    
    item_detail_fields = frappe.db.get_all(
        "Item Details",filters = {"parent":category,"fieldname":["NOT IN",["",None]]},fields = ["label","fieldname"]
    )

    fields = [ field.fieldname for field in item_detail_fields ]
    
    item_field_values = frappe.db.get_value("Item",item,fields,as_dict=True)

    for field in item_detail_fields:
        field["value"] =  item_field_values.get(field.fieldname)
        
    return item_detail_fields

# ----------------------------
# Main API
# ----------------------------

@frappe.whitelist(allow_guest=True)
def get_details(kwargs: Dict[str, Any]):
    try:
        create_user_tracking(kwargs, "Product Detail")

        item_slug = kwargs.get("item")
        currency = kwargs.get("currency")
        if not item_slug:
            return error_response(_("Invalid key 'item'"))

        # Get customer id
        customer_id = None
        if frappe.session.user != "Guest":
            customer_id = kwargs.get("customer_id") or frappe.db.get_value(
                "Customer", {"email": frappe.session.user}, "name"
            )

        # Fetch item
        filters = get_filter_list({"slug": item_slug, "access_level": get_access_level(customer_id)})
        item_list = frappe.get_list("Item", filters=filters, fields=["*"])
        if not item_list:
            return error_response(_("Item not found"))

        item = item_list[0]

        translated_item_fields = get_item_details_dict(item, kwargs, customer_id, currency)

        return {"msg": "Success", "data": translated_item_fields}

    except Exception as e:
        frappe.logger("product").exception(e)
        return error_response(str(e))

# Whitelisted Function
@frappe.whitelist(allow_guest=True)
def get_cyu_categories(kwargs):
    ignore_permissions = frappe.session.user == "Guest"
    data = frappe.get_list('CYU Categories',
                           filters={},
                           fields=['name as product_category', 'heading', 'label', 'image as product_img', 'slug', 'url as category_url', 'description', 'offer', 'range_start_from'],
                           order_by='sequence',
                           ignore_permissions=ignore_permissions) 
    data_list = success_response(data=data)
    return custom_response(data_list)  


@frappe.whitelist(allow_guest=True)
def get_categories(kwargs):
	filters = {
		"enable_category": "Yes"
	}
	ignore_perm = frappe.session.user == "Guest"
	return frappe.get_list('Category',
							   filters=filters,
							   fields=['name as category', 'image', 'slug', 'url as category_url', 'description'],
							   ignore_permissions=ignore_perm)


def get_top_categories(kwargs):
	categories = get_cyu_categories(kwargs)
	limit = int(kwargs.get('limit', 3))
	if limit and len(categories) > limit:
		categories = categories[:limit]
	res = []
	for category in categories:
		data = {
			"container": {
				"container_name": category.get("product_category"),
				"slug": category.get("slug"),
				"banner_img": category.get("product_img"),
				"banner_description": category.get("description"),
			}}
		kwargs['category'] = category.get('slug')
		kwargs['internal'] = 1
		kwargs['limit'] = 8
		p_list = get_list(kwargs)
		data['product_list'] = p_list
		res.append(data)
	return success_response(res)


def get_list_data(kwargs,order_by, sort_by, filters, price_range, global_items, page_no, vehicle_filters, limit, or_filters={}, debug=0):
    offset = 0
    if page_no is not None:
        if limit is None:
            limit = 0
        offset = int(page_no) * int(limit)

    if 'access_level' not in filters:
        filters['access_level'] = 0

    # Inject category and brand filtering logic

    if not kwargs.get("category"):
        if categories := get_allowed_categories(filters.get("category")): # same as brand
            filters["category"] = ["in", categories]

    if not kwargs.get("brand"):
        if brands := get_allowed_brands(kwargs.get("customer_id"),kwargs.get("customer_group")):
            if not (filters.get("brand") and filters.get("brand") in brands):
                filters["brand"] = ["in", brands]

    # Dynamically fetch all fields from Vehicle Detail child table
    if vehicle_filters:
        vehicle_child_filters(filters)

    if global_items is not None:
        return get_items_via_search(global_items, filters)

    ignore_permissions = frappe.session.user == "Guest"

    if not order_by:
        order_by = 'valuation_rate asc' if price_range == 'low_to_high' else 'valuation_rate desc' if price_range == 'high_to_low' else ''
        if sort_by == "oldest":
            order_by = "modified asc"
        elif sort_by == "latest":
            order_by = "modified desc"
        elif sort_by == "creation":
            order_by = "creation desc"
    else:
        order_by = order_by
    data = frappe.get_list('Item',
                           filters=filters,
                           or_filters=or_filters,
                           fields="*",
                           limit_page_length=limit,
                           limit_start=offset,
                           order_by=order_by,
                           ignore_permissions=ignore_permissions,
                           debug=debug)
    
    count = get_count("Item", filters=filters, or_filters=or_filters,
                      ignore_permissions=ignore_permissions)

    if limit == 1:
        data = data[0] if data else []
    return count, data




def get_count(doctype, **args):
	distinct = "distinct " if args.get("distinct") else ""
	args["fields"] = [f"count({distinct}`tab{doctype}`.name) as total_count"]
	res = DatabaseQuery(doctype).execute(**args)
	data = res[0].get("total_count")
	return data


def get_items_via_search(global_items, filters):
	item_list = []
	items = [item.name for item in global_items]
	filters['name'] = ["in", items]
	ignore_permission = bool(frappe.session.user == "Guest")
	item_list = frappe.get_list(
		'Item', filters, '*', ignore_permissions=ignore_permission)
	return len(item_list), item_list


# Get Variants Helper Functions
def get_variant_details(filters):
    ignore_perm = frappe.session.user == "Guest"
    variants = frappe.get_list('Item', {'variant_of': filters.get('item_code')}, ignore_permissions=ignore_perm)
    return variants
	

def get_variant_size(item_code):
	return frappe.get_value('Item Variant Attribute',
							{'parent': item_code, 'attribute': 'Size'}, 'attribute_value')


def get_variant_colour(item_code):
	colour = frappe.get_value('Item Variant Attribute',
							  {'parent': item_code, 'attribute': 'Colour'}, 'attribute_value')
	return frappe.get_value('Item Attribute Value', {'attribute_value': colour}, 'abbr')

def get_variant_slug(item_code):
	return frappe.get_value('Item',{'item_code':item_code},'slug')

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


def append_applied_filters(filters, filter_list):
    section_list = filter_list.get('sections')
    filters_list = list(filters.items())  # Convert filters to a list of key-value tuples
    sort_order = None  # Initialize sort_order variable
    for section in section_list:
        doc_name, field_val = frappe.db.get_value('Filter Section Setting', {'filter_section_name': section['name']}, ["doctype_name","field"] )
        if doc_name == 'Item':
            filters_list.append((field_val, ['in', section['value']]))
            if field_val == 'sequence':
                # Get the sort order value from the section's value list
                sort_order = section['value'][0]
    filters = dict(filters_list)  # Convert filters_list back to a dictionary
    return filters, sort_order


def get_recommendation(kwargs):
	# ptype = ["Equivalent", "Suggested", "Mandatory", "Alternate"]
	currency = kwargs.get("currency")
	if kwargs.get("item_code"):
		item_code = kwargs.get("item_code")
	elif kwargs.get('item'):
		item_code = frappe.get_value('Item', {'slug': kwargs.get('item')})
	else:
		return error_response("invalid argument 'item'")
	fieldnames = ['item_code_1', 'item_code_2', 'item_code_3', 'item_code_4', 'item_code_5',
				  'item_code_6', 'item_code_7', 'item_code_8', 'item_code_9', 'item_code_10',
				  'item_code_11', 'item_code_12', 'item_code_13', 'item_code_14', 'item_code_15',
				  'item_code_16', 'item_code_17', 'item_code_18', 'item_code_19', 'item_code_20']
	if kwargs.get('ptype') == "Suggested":
		condition = f"item_code_1 = '{item_code}'"
	else:
		condition = ' or '.join([f'{field} = "{item_code}"' for field, item_code in zip(
			fieldnames, [item_code]*len(fieldnames))])
	items = frappe.db.sql(
		f"""select {', '.join(fieldnames)} from `tabMatching Items` where type = '{kwargs.get('ptype','')}' and ({condition})""", as_list=True)
	res = []
	if items:
		for item in items:
			for code in item:
				if code and code not in res:
					res.append(code)
		items = res
		if kwargs.get("item_only"):
			return items
		items.remove(item_code)
	else:
		if kwargs.get("item_only"):
			return []
		return error_response("No match found")
	result = get_detailed_item_list(currency,items, kwargs.get("customer_id"))
	return success_response(data=result)


def get_product_url(item_detail):
	if not item_detail:
		return "/"
	item_cat = item_detail.get('category')
	item_cat_slug = frappe.db.get_value('Category',item_cat,'slug')
	if product_template:=item_detail.get("variant_of"):
		product_slug = frappe.db.get_value('Item', product_template, 'slug')
	else:
		product_slug = item_detail.get("slug")
	from summitapp.api.v2.mega_menu import get_item_url
	return get_item_url('product', item_cat_slug, product_slug)


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


def get_tagged_products(kwargs):
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
        etag = handle_etag(response_data)
        if etag is None:
            return
        return handle_response(response, etag=etag)
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



def get_tagged_product_limit(user_role, customer_id):
    if user_role == "Guest":
        web_settings = frappe.get_single("Web Settings")
        if web_settings.apply_product_limit:
            return web_settings.apply_product_limit
    elif customer_id:
        grp = frappe.db.get_value("Customer", customer_id, 'customer_group')
        if grp:
            apply_customer_group_limit = frappe.db.get_value("Customer Group", grp, "apply_the_product_limit")

            if apply_customer_group_limit:
                return apply_customer_group_limit

    return 0



def check_availability(kwargs):
    try:
        item_code = kwargs.get("item_code")
        if not item_code:
            return error_response("item_code missing")

        req_qty = flt(kwargs.get("qty", 1))
        
        stock_qty = flt(get_stock_info(item_code, "stock_qty", with_future_stock=False))

        qty = min(req_qty, stock_qty)

        template_item_code, lead_days = frappe.db.get_value(
            "Item", item_code, ["variant_of", "lead_time_days"])

        warehouse = frappe.db.get_value(
            "Item", {"item_code": item_code}, "website_warehouse")
        
        if not warehouse and template_item_code and template_item_code != item_code:
            warehouse = frappe.db.get_value(
                "Item", {"item_code": template_item_code}, "website_warehouse")

        future_stock = frappe.get_list("Item Future Availability", {
            'item': item_code,
            'date': [">", frappe.utils.today()],
            "quantity": [">", 0]
        }, "warehouse, date, quantity", order_by="date", ignore_permissions=True)
    
        res = []
        data = {
            "warehouse": warehouse,
            "qty": qty,
            "date": today(),
            "incoming_qty": 0,
            "incoming_date": ''
        }
    
        if req_qty <= stock_qty:
            return success_response(data=[data])

        req_qty -= stock_qty

        
        for row in future_stock:
            if req_qty <= 0:
                break

            qty = min(req_qty, row.get("quantity"))
            req_qty -= qty

            if row.get("warehouse") == data["warehouse"] and not data["incoming_qty"]:
                data.update({"incoming_qty": qty, "incoming_date": row.get("date")})
            else:
                res.append({
                    "warehouse": row.get("warehouse"),
                    "incoming_qty": qty,
                    "incoming_date": row.get("date")
                })
            res = [data] + res
    
            if req_qty > 0:
                res[-1].update({
                    "additional_qty": req_qty,
                    "available_on": add_days(row.get("date"), lead_days)  
                })
            return success_response(data=res)
        return success_response(data = "Data Not Found" )
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(e)



def get_web_item_future_stock(item_code, item_warehouse_field, warehouse=None):
	in_stock, stock_qty = 0, ""
	template_item_code, is_stock_item = frappe.db.get_value(
		"Item", item_code, ["variant_of", "is_stock_item"]
	)
	if not warehouse:
		warehouse = frappe.db.get_value(
			"Item", {"item_code": item_code}, item_warehouse_field)

	if not warehouse and template_item_code and template_item_code != item_code:
		warehouse = frappe.db.get_value(
			"Item", {
				"item_code": template_item_code}, item_warehouse_field
		)
	if warehouse:
		stock_qty = frappe.db.sql(
			"""
			select sum(quantity)
			from `tabItem Future Availability`
			where date >= CURDATE() and item=%s and warehouse=%s""",
			(item_code, warehouse),
		)

		if stock_qty:
			return stock_qty[0][0]


def get_default_currency(kwargs):
    ecom_settings = frappe.get_single('Webshop Settings')
    company_name = ecom_settings.company
    default_currency = frappe.get_value('Company', company_name, 'default_currency')
    if not default_currency:
        frappe.throw(f"Default currency not set for company '{company_name}'.")
    return {
          'default_currency': default_currency,
          'company':company_name
          }        

def sort_item_by_price(items, price_range):
    if price_range:
        reverse = None
        if price_range == 'low_to_high':
            reverse = False
        if price_range == 'high_to_low':
            reverse = True
        if reverse is not None:
            sorted_items = sorted(items, key=lambda item: float(item.get('price', 0)), reverse=reverse)
            items = sorted_items
    return items


def get_item_varient_attribute(item_code):
    item_varient_details = frappe.get_all('Item Variant Attribute',
							{'parent': item_code}, ['attribute', 'attribute_value'])
    for item in item_varient_details:
        item["abbr"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'abbr')
        item["attr_colour"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'attribute_colour')
    return item_varient_details


def quick_order(kwargs):
    try:
        currency = kwargs.get('currency')
        customer_id = get_customer_id(kwargs)
        if not kwargs.get('item'):
            return error_response('Item filter not provided')
        filter = json.loads(kwargs.get('item'))
        data = [frappe.db.get_value('Item', filter, ['*'],as_dict=True)]
        if result := get_processed_list(currency, data, customer_id):
            return {'msg': 'success', 'data': result[0]}
        else:
            return {'msg': 'success', 'data': []}
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))

def json_handler(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

def custom_response(data, headers=None):
    response = Response()
    response.mimetype = "application/json"
    response.data = json.dumps(data, default=json_handler, separators=(",", ":"))
    # response.headers["Cache-Control"] = "max-age=450000"
    return response



@frappe.whitelist(allow_guest=True)
def product_search(kwargs):
    create_user_tracking(kwargs, "Product Search")
    
    search_value = kwargs.get('search_value')
    if not search_value:
        return error_response("Missing 'search_value' parameter")
    items = frappe.get_list(
        "Item",
        filters = { "disabled": 0},
        or_filters=[
            {"name": search_value}, 
            {"bom_factory_code": search_value},
            {"market_design_name": search_value} 
        ],
        fields=["name", "category", "slug"]
    )

    if not items:
        return error_response("No products found for the given search value")

    formatted_items = []

    for item in items:
        category = frappe.get_list(
            "Category",
            filters={"name": item['category']},
            fields=["name", "slug"]
        )
        
        if category:
            category_slug = category[0]['slug']
            formatted_items.append(
                {"product": f"product/{category_slug}/{item['slug']}"}
            )
    return {
        "status": "success",
        "data": formatted_items
    }


def parse_vehicle_filter(vehicle_filter_data):
    # Dynamically get all fields from Vehicle Detail doctype
    vehicle_fields = [
        df.fieldname for df in frappe.get_meta("Vehicle Detail").fields
        if df.fieldtype not in ["Section Break", "Column Break"]
    ]

    vehicle_conditions = {}

    # Add top-level fields (like "vehicle": "Car")
    for key, val in vehicle_filter_data.items():
        if key != "sections" and key in vehicle_fields:
            vehicle_conditions[key] = val

    # Parse section-based values
    sections = vehicle_filter_data.get("sections", [])
    for section in sections:
        name = section.get("name")
        value = section.get("value")
        if not name:
            continue

        # Convert label-style name to fieldname format
        field_key = name.lower().replace(" ", "_")
        if field_key in vehicle_fields:
            vehicle_conditions[field_key] = value if len(value) > 1 else value[0]

    return vehicle_conditions

def vehicle_child_filters(filters):
    vehicle_meta = frappe.get_meta("Vehicle Detail")
    vehicle_fields = [df.fieldname for df in vehicle_meta.fields if df.fieldtype not in ["Section Break", "Column Break"]]

    # Extract only vehicle-related filters
    vehicle_filter_conditions = {k: filters.pop(k) for k in vehicle_fields if k in filters}

    if vehicle_filter_conditions:
        vehicle_detail = frappe.qb.DocType("Vehicle Detail")
        query = frappe.qb.from_(vehicle_detail).select(vehicle_detail.parent)

        for field, value in vehicle_filter_conditions.items():
            if isinstance(value, list):
                query = query.where(getattr(vehicle_detail, field).isin(value))
            else:
                query = query.where(getattr(vehicle_detail, field) == value)

        item_names = [r[0] for r in query.distinct().run()]
        if not item_names:
            return 0, []

        filters["name"] = ["in", item_names]



import frappe
import traceback

@frappe.whitelist(allow_guest=True)
def item_search(kwargs):
    create_user_tracking(kwargs, "Product Search")
    search_value = kwargs.get('search_value')
    if not search_value:
        return error_response("Missing 'search_value' parameter")
    items = frappe.get_list(
                "Item",
                filters={
                    "category": ["like", f"%{search_value}%"]
                },
                fields=['*']
            )
    item_fields = get_processed_list(None,items,None,None)
    return success_response(item_fields)
