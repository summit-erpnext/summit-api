import frappe, json
from frappe.utils.global_search import search
from frappe.utils import cint
from summitapp.api.v2.translation import translate_result
from summitapp.api.v2.utils import (check_brand_exist, get_processed_list, create_user_tracking,
                                    get_list_product_limit,get_customer_id)
from summitapp.utils import error_response, get_access_level
from summitapp.summitapp.customizations.item.utils import get_list_data, json_handler
from summitapp.summitapp.doctype.category.utils import get_child_categories


def get_product_list(kwargs):
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



def get_filter_listing(user_role, kwargs, web_settings):
    filters = {
        "disabled": 0
    }
    if user_role == "Guest":
        display_both_item_and_variant= web_settings.display_both_item_and_variant 
        if display_both_item_and_variant == 1:
            filters['has_variants'] = 0
            filters['show_on_website'] = 1
    elif kwargs.get("category"):
        filters['show_on_website'] = 1
        filters['has_variants'] = 0
    else:
       filters['variant_of'] = ['is', "not set"]
       filters['has_variants'] = 0  
        
    for key, val in kwargs.items():
        if val:
            filters.update({key: val})
    return filters

def get_filter_list(kwargs):
	filters = {
		"disabled": 0,
	}
	for key, val in kwargs.items():
		if val:
			filters.update({key: val})
	return filters
