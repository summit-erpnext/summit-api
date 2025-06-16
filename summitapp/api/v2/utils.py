import frappe
from summitapp.utils import success_response, error_response
from webshop.webshop.utils.product import adjust_qty_for_expired_items
from frappe.utils import flt
from frappe.model.db_query import DatabaseQuery
from frappe.utils import nowdate
import requests
from frappe.utils.data import get_url
import json
from summitapp.api.v2.item_wise_sales_history import get_monthly_target_qty, get_yearly_target_qty

def validate_pincode(kwargs):
	pincode = True if frappe.db.exists(
		'Pin Code', kwargs.get('pincode')) else False
	return success_response(data=pincode)


def get_cities(kwargs):
	city_list = frappe.db.get_list('City', filters = {'state': kwargs.get('state')}, fields =['name', 'state', 'country'], ignore_permissions=True)
	return success_response(data=city_list)

def get_states(kwargs):
	state_list = frappe.db.get_list('State', filters = {}, fields =['name', 'country'], ignore_permissions=True)
	return success_response(state_list)


def get_countries(kwargs):
	country_list = frappe.db.get_list('Country', filters = {}, fields =['name as country_name'], ignore_permissions=True)
	return success_response(data = country_list)


def check_brand_exist(filters):
	return any('brand' in i for i in filters)

# def get_filter_listing(kwargs):
#     filters = {
#         "disabled": 0
#     }
#     display_both_item_and_variant = int(frappe.db.get_value("Web Settings", "Web Settings", "display_both_item_and_variant"))
    
#     if display_both_item_and_variant == 1:
#         filters['has_variants'] = 0
#         filters['show_on_website'] = 1
#     else:
#        filters['variant_of'] = ['is', "not set"]
       
#     for key, val in kwargs.items():
#         if val:
#             filters.update({key: val})

#     return filters

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


def get_field_names(product_type):
    return frappe.db.get_all(
        'Product Fields',
        filters={'parent': frappe.get_value('Product Page Field', {'product_type': product_type})},
        pluck='field'
    )

def get_processed_list(currency,items, customer_id, url_type = "product"):
    field_names = get_field_names('List')
    processed_items = []
    for item in items:
        variant_info = []
        item_description = add_item_description(item) 
        loyalty_points_map = get_loyalty_points(customer_id,currency)
        if item.get("variant_of") is not None:
            filters = {'item_code':item.get('variant_of')}
            variant_list = get_variant_details(filters)
            variant_info = get_variant_info(variant_list)
        item_fields = get_item_field_values(currency,item, customer_id, url_type,field_names,loyalty_points_map, item_description, variant_info)
        processed_items.append(item_fields)
    return processed_items

def get_item_field_values(currency, item, customer_id, url_type, field_names,loyalty_points_map, item_description,variant_info):
    try:
        attributes= get_item_varient_attribute(item.name)
        loyalty_points_map = loyalty_points_map or {}
       
        computed_fields = {
            'status': lambda: {'status': 'template' if item.get('has_variants') else 'published'},
            'in_stock_status': lambda: {'in_stock_status': get_stock_info(item.get('name'), 'stock_qty') != 0},
            'brand_img': lambda: {'brand_img': frappe.get_value('Brand', item.get('brand'), ['image']) or None},
            'mrp_price': lambda: {'mrp_price': get_item_price(currency, item.get("name"), customer_id, get_price_list(customer_id))[1]},
            'price': lambda: {'price': get_item_price(currency, item.get("name"), customer_id, get_price_list(customer_id))[0]},
            'loyalty_points': lambda: {'loyalty_points': loyalty_points_map.get(item.get("name"), 0)},
            'currency': lambda: {'currency': get_currency(currency)},
            'currency_symbol': lambda: {'currency_symbol': get_currency_symbol(currency)},
            'display_tag': lambda: {
                'display_tag': item.get('display_tag') or frappe.get_list("Tags MultiSelect", {"parent": item.name}, pluck='tag', ignore_permissions=True)
            },
            'url': lambda: {'url': get_product_url(item, url_type)},
            'category_slug': lambda: {'category_slug': get_category_slug(item)},
            'variant': lambda: {'variant': variant_info},
            'variant_of': lambda: {'variant_of': item.get('variant_of')},
            'attributes': lambda: {'attributes':attributes},
            'equivalent': lambda: {'equivalent': bool(item.get('equivalent') == '1')},
            'alternate': lambda: {'alternate': bool(item.get('alternate') == '1')},
            'mandatory': lambda: {'mandatory': bool(item.get('mandatory') == '1')},
            'suggested': lambda: {'suggested': bool(item.get('suggested') == '1')},
            'e_commerce_platforms': lambda: {'e_commerce_platforms': get_ecommerce_platforms(item)},
            'brand_video_url': lambda: {'brand_video_url': frappe.get_value('Brand', item.get('brand'), ['brand_video_link']) or None},
            'size_chart': lambda: {'size_chart': frappe.get_value('Size Chart', item.get('size_chart'), 'chart')},
            'slide_img': lambda: {'slide_img': get_item_images(item.get("name"))},
            'features': lambda: {'features': get_features(item.key_features) if item.key_features else []},
            'why_to_buy': lambda: {'why_to_buy': frappe.db.get_value('Why To Buy', item.get("select_why_to_buy"), "name1")},
            'prod_specifications': lambda: {'prod_specifications': get_specifications(item)},
            'item_pdf_url': lambda: {'item_pdf_url': get_pdf_attachments("Item", item.get("name"))},
            'store_pick_up_available': lambda: {'store_pick_up_available': item.get('store_pick_up_available') == 'Yes'},
            'home_delivery_available': lambda: {'home_delivery_available': item.get('home_delivery_available') == 'Yes'},
            'category_size': lambda: {'category_size':get_category_size(item.get('category'))},
            'vehicle_details':lambda:{'vehicle_details':get_vehicle_detail(item.get("name"))},
            'item_characteristics': lambda: {'item_characteristics': get_item_characteristics(item.get('category'))},
            'monthly_target_qty': lambda: {'monthly_target_qty':get_monthly_target_qty(customer_id,item.get("item_code"))},
            'target_qty': lambda: {'taget_qty':get_yearly_target_qty(customer_id,item.get("item_code"))},
            'item_description': lambda:{'item_description':item_description},
            'category_specification': lambda: {'category_specification':category_specification(item.get('category'))},
        }

        item_fields = {}

        for field_name in field_names:
            if field_name in computed_fields:
                item_fields.update(computed_fields[field_name]())
            else:
                item_fields.update({field_name: item.get(field_name)})

        return item_fields

    except Exception as e:
        frappe.logger('product').exception("Error in get_item_field_values")
        return error_response(f"An error occurred: {str(e)}")


def get_category_slug(item_detail):
	if not item_detail:
		return []
	item_cat = item_detail.get('category')
	item_cat_slug = frappe.db.get_value('Category',item_cat,'slug')
	return item_cat_slug

def get_currency(currency):
    if currency is None:
        currency = 'INR'
    currency_doc = frappe.get_doc("Currency", currency)
    return currency_doc.get("currency_name", currency)

def get_currency_symbol(currency):
    if currency is None:
        currency = 'INR'
    currency_doc = frappe.get_doc("Currency", currency)
    return currency_doc.get("symbol", currency)

def get_product_url(item_detail, url_type = "product"):
	if not item_detail:
		return "/"
	item_cat = item_detail.get('category')
	item_cat_slug = frappe.db.get_value('Category',item_cat,'slug')
	product_slug = item_detail.get("slug")
	from summitapp.api.v2.mega_menu import get_item_url
	return get_item_url(url_type, item_cat_slug, product_slug)


def get_price_list(customer=None):
    selling_settings = frappe.get_cached_value(
        "Web Settings", None, "default_price_list")
    if customer:
        cust = frappe.get_cached_value(
            "Customer", customer, ["default_price_list", "customer_group"], as_dict=True)
        cust_grp_pl = frappe.get_cached_value(
            "Customer Group", cust.get("customer_group"), "default_price_list")
        return cust.get("default_price_list") or cust_grp_pl or selling_settings
    return selling_settings


def get_item_price(currency, item_name, customer_id=None, price_list=None, valuation_rate=0):
    item_filter = {
        'item_code': item_name,
        'price_list': price_list
    }

    if customer_id:
        item_filter['customer'] = customer_id
        price, mrp_price = frappe.db.get_value("Item Price", item_filter, ['price_list_rate', 'strikethrough_rate']) or (0, 0)
        if price:
            return convert_currency(price, currency), convert_currency(mrp_price, currency)

    item_filter['customer'] = ["is", "null"]
    price, mrp_price = frappe.get_value('Item Price', item_filter, ['price_list_rate', 'strikethrough_rate']) or (0, 0)
    return convert_currency(price, currency), convert_currency(mrp_price, currency)


def convert_currency(amount, currency):
    if currency and currency != 'INR':
        exchange_rate = get_exchange_rate(currency)
        if exchange_rate is not None:
            amount = round(amount * exchange_rate, 2)
    return amount

def get_exchange_rate(currency):
    filters = {
        "to_currency": currency,
        "from_currency": "INR"
    }
    exchange_rate_doc = frappe.get_list("Currency Exchange", filters=filters, fields=["exchange_rate"])
    if exchange_rate_doc:
        exchange_rate = exchange_rate_doc[0].exchange_rate
        return exchange_rate
    else:
        return None



def get_stock_info(item_code, key, with_future_stock=True):
    try:
        roles = frappe.get_roles(frappe.session.user)
        is_dealer = "Dealer" in roles
        warehouse_field = 'dealer_warehouse' if is_dealer else 'website_warehouse'
        variant_list = frappe.db.get_all('Item', {'variant_of': item_code}, 'name')
        if not variant_list:
            variant_list = frappe.db.get_all('Item', {'name': item_code}, 'name')
        stock = 0
        for variant in variant_list:
            stock_qty = get_web_item_qty_in_stock(
                variant.get('name'), warehouse_field).get(key)
            stock += flt(stock_qty)
            if with_future_stock:
                future_stock = get_web_item_future_stock(
                    variant.get('name'), warehouse_field)
                stock += flt(future_stock)
        if key == 'stock_qty':
            return stock
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(e)

def get_web_item_future_stock(item_code, item_warehouse_field, warehouse=None):
	try:
		stock_qty = 0
		template_item_code = frappe.db.get_value(
			"Item", item_code, ["variant_of"]
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
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response(e)		


def get_web_item_qty_in_stock(item_code, item_warehouse_field, warehouse=None):
    try:
        in_stock, stock_qty = 0, ""
        total_qty = 0
        template_item_code, is_stock_item = frappe.db.get_value(
            "Item", item_code, ["variant_of", "is_stock_item"]
        )
        default_warehouse = frappe.get_cached_value("Web Settings", None, "default_warehouse")
        warehouses = [default_warehouse] if default_warehouse else []
        if not warehouse:
            warehouse = frappe.db.get_value("Item", {"item_code": item_code}, item_warehouse_field)

        if not warehouse and template_item_code and template_item_code != item_code:
            warehouse = frappe.db.get_value(
                "Item", {"item_code": template_item_code}, item_warehouse_field
            )
        if warehouse:
            warehouses.append(warehouse)
            stock_list = frappe.db.sql(
                f"""
                select GREATEST(S.actual_qty - S.reserved_qty - S.reserved_qty_for_production - S.reserved_qty_for_sub_contract, 0) / IFNULL(C.conversion_factor, 1),
                S.warehouse
                from `tabBin` as S
                inner join `tabItem` I on S.item_code = I.Item_code
                left join `tabUOM Conversion Detail` C on I.sales_uom = C.uom and C.parent = I.Item_code
                where S.item_code='{item_code}' and S.warehouse in ('{"', '".join(warehouses)}')"""
            )
            if stock_list:
                for stock_qty in stock_list:
                    stock_qty = adjust_qty_for_expired_items(item_code, [stock_qty], stock_qty[1])
                    total_qty += stock_qty
                    if not in_stock:
                        in_stock = stock_qty > 0 and 1 or 0
        return frappe._dict(
            {"in_stock": in_stock, "stock_qty": total_qty, "is_stock_item": is_stock_item}
        )
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(e)
	

def get_slide_images(item, tile_image):
    img = None if tile_image else []
    imgs = get_slideshow_value(item)
    if imgs:
        if slideshow := imgs.get("slideshow"):
            ss_doc = frappe.get_all('Website Slideshow Item', {
                                        "parent": slideshow}, "*", order_by='idx asc')
            ss_images = [image.image for image in ss_doc]
            if ss_images:
                img = ss_images[0] if tile_image else ss_images
                return img
        if imgs.get('website_image'):
            img = imgs.get('website_image') if tile_image else [
                imgs.get('website_image')]
        elif not imgs.get("slideshow") and not imgs.get("website_image"):
            img = frappe.db.get_value("Item", item, "image")
            if img:
                return img if tile_image else [img]
            else:
                return "" if tile_image else []     
    return img

def get_default_slide_images(item_doc, tile_image, attribute):
    if images := get_slide_images(item_doc.name, tile_image):
        return images

    if item_doc.get("has_variant") and (variant := frappe.get_value("Item Variant Attribute", {"variant_of": item_doc.name, "is_default": 1, "attribute": attribute}, "parent")):
        return get_slide_images(variant, tile_image)

    return None if tile_image else []

def get_default_variant(item_code, attribute):
	attr = frappe.get_value("Item Variant Attribute", {"variant_of": item_code, "is_default":1, "attribute": attribute},"attribute_value")
	return frappe.get_value('Item Attribute Value', {'attribute_value': attr}, 'abbr')

def variant_thumbnail_reqd(item_code, attribute):
	res = frappe.get_value("Item Variant Attribute", {"parent": item_code, "display_thumbnail":1, "attribute": attribute},"name")
	return bool(res)

def get_slideshow_value(item_name):
	return frappe.get_value('Website Item', {'item_code': item_name}, ['slideshow', "website_image"], as_dict=True)

def get_features(key_feature):
	key_features = frappe.get_all(
		"Key Feature Detail", {"parent": key_feature}, pluck = "key_feature", order_by ="idx")
	feat_val = frappe.get_all("Key Feature",{"key_feature": ["in",key_features]}, ["key_feature as heading", "description","image"], order_by = "idx")
	return {'name': 'Key Features', 'values': feat_val}


def get_technologies_details(item):
    techs = frappe.get_list("Final Technology", {'parent': item.technologies}, pluck='technology', ignore_permissions=True, order_by="idx")
    lst = []
    for row in techs:
        name = frappe.db.get_value("Technology", row, "name")
        image = frappe.db.get_value("Technology", row, "image")
        description = frappe.db.get_value("Technology", row, "description")
        tech_details = {}
        tech_details['name'] = name
        tech_details['image'] = image
        tech_details['description'] = description
        technology_details = []
        
        tech_details_rows = frappe.get_all(
            "Technology Details",
            filters={'parent': name},
            fields=["title", "video_frame", "description", "image", "sequence"],
            order_by="idx ASC"
        )
        
        for tech_details_row in tech_details_rows:
            details = {}
            details['title'] = tech_details_row.title
            details['video_frame'] = tech_details_row.video_frame
            details['description'] = tech_details_row.description
            details['image'] = tech_details_row.image
            details['sequence'] = tech_details_row.sequence
            technology_details.append(details)
        
        tech_details['technology_details'] = technology_details
        lst.append(tech_details)
    return lst

def get_specifications(item):
	res = []
	item_filters = frappe.get_all("Item Filters", {"parent":item.name}, ["field_name","field_value"], order_by="idx")
	if item_filters:
		res.append({
			'name': 'Specifications',
			'values': get_specification_details(item_filters) if item_filters else []
		})
	if item.get("geometry_file"):
		res.append({
			'name': 'Geometry',
			'values': item.get("geometry_file")
		})
	if item.get("technologies"):
		res.append({
			'name': 'Technologies',
			'values': item.get("technologies"),
			'details': get_technologies_details(item)
		})
	return res

def get_specification_details(filters):
	return [
		{
			'name': tech.field_name,
			'values': tech.field_value
		}
		for tech in filters
	]
 
def create_user_tracking(kwargs, page):
	if frappe.session.user == "Guest":
		return
	doc = frappe.new_doc("User Tracking")
	doc.user = frappe.session.user
	doc.page = page
	doc.ip_address = frappe.local.request_ip
	for key, value in kwargs.items():
		if key in ["version", "method", "entity", "cmd"]:
			continue
		doc.append("parameters",{
			"key": key,
			"value": value
		})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


def get_list_product_limit(user_role, customer_group, web_settings):
    # If the user is a Guest and global product limit is applied
    if user_role == "Guest":
        if web_settings.product_limit is not None and web_settings.apply_product_limit == 1:
            return web_settings.product_limit

    # If the user belongs to a customer group and group-specific limit is applied
    elif customer_group:
        customer_group_details = frappe.get_value(
            "Customer Group",
            customer_group,
            ["set_product_limit", "apply_the_product_limit"],
            as_dict=True
        ) or {}

        if customer_group_details.get("apply_the_product_limit") is not None and customer_group_details.get("apply_the_product_limit") == 1:
            return customer_group_details.get("set_product_limit", 0)

    # Default: no limit applied
    return 0


def get_logged_user():
    header = {"Authorization": frappe.request.headers.get('Authorization')}
    response = requests.post(get_url() + "/api/method/frappe.auth.get_logged_user", headers=header)
    user = response.json().get("message")
    return user

def get_customer_id(kwargs):
    customer_id = kwargs.get('customer_id')
    email_id = kwargs.get('email')

    # First preference: Use email_id from kwargs if available
    if email_id:
        customer = frappe.db.get_value("Customer", {"email": email_id}, ['name', 'customer_group'], as_dict=True)
        if customer:
            return customer.name, customer.customer_group

    # Second preference: Use customer_id from kwargs if available
    if customer_id:
        customer = frappe.db.get_value("Customer", customer_id, ['name', 'customer_group'], as_dict=True)
        if customer:
            return customer.name, customer.customer_group

    # Third preference: Use the logged-in user's email if not Guest
    if frappe.session.user and frappe.session.user != "Guest":
        customer = frappe.db.get_value("Customer", {"email": frappe.session.user}, ['name', 'customer_group'], as_dict=True)
        if customer:
            return customer.name, customer.customer_group

    # Default: Nothing found
    return None, None



def get_guest_user(auth_header):
	guest_user = frappe.db.get_value("Access Token", {"token": auth_header}, 'email')
	if guest_user:
		return guest_user

def get_ecommerce_platforms(item):
    try:
        platforms = frappe.get_all("E Commerce Platforms",
                                   filters={"parent": item.name},
                                   fields=["platform", "link", "sequence"],
                                   order_by="sequence")
        return platforms  # Adjusted indentation here
    except Exception as e:
        frappe.logger("product").exception(e)
        return error_response(e)


def get_marquee(kwargs):
    try:
        marquee = frappe.get_doc("Marquee")
        result = [
            {"heading_1": marquee.heading_1},
            {"heading_2": marquee.heading_2},
            {"heading_3": marquee.heading_3},
            {"heading_4": marquee.heading_4},
            {"heading_5": marquee.heading_5},
            {"heading_6": marquee.heading_6},
            {"heading_7": marquee.heading_7},
            {"heading_8": marquee.heading_8},
            {"heading_9": marquee.heading_9},
            {"heading_10": marquee.heading_10},
        ]
        return success_response(result)
    except Exception as e:
        frappe.logger("product").exception(e)
        return error_response(e)

	

def get_testomonial(kwargs):
    try:
        if not kwargs.get('category'): 
            return error_response('Please Specify Category')
        
        test_doc = frappe.get_list("Testomonial",
                                 filters={"category": kwargs.get("category")},
                                 fields=["category", "heading", "description","name"])
        
        test_with_details = []
        for t in test_doc:
            details = get_testomonial_details(t['name'])  # Fetch images for each review
            t['details'] = details  # Append images to the review
            test_with_details.append(t)
        response_data = test_with_details
        return success_response(response_data)
    
    except Exception as e:
        frappe.logger("utils").exception(e)
        return error_response(str(e))


def get_testomonial_details(doc):
    try:
        details = frappe.get_all("Testomonial Details",
                                   filters={"parent": doc},
                                   fields=["image","name1","comment","url","label","sequence"],ignore_permissions=True,order_by="sequence")
        return details
    except Exception as e:
        frappe.logger("profile").exception(e)
        return error_response(str(e))
	

def get_company_motto(kwargs):
    try:
        # Assuming frappe.get_doc() returns a document with the specified fields
        company_motto = frappe.get_doc("Company Motto")
        result = {
            "heading_1": company_motto.heading_1,
            "heading_2": company_motto.heading_2,
            "heading_3": company_motto.heading_3,
            "description_1": company_motto.description_1,
            "description_2": company_motto.description_2,
            "details": get_company_motto_details(company_motto)
        }
        return success_response(result)
    
    except Exception as e:
        frappe.logger("utils").exception(e)
        return error_response(str(e))


def get_company_motto_details(doc):
    try:
        details = frappe.get_all("Company Motto Details",
                                   filters={"parent": doc},
                                   fields=["image","heading","sequence"],order_by="sequence")
        return details
    except Exception as e:
        frappe.logger("utils").exception(e)
        return error_response(str(e))


def get_product_specifications(kwargs):
    try:
        prod_specifications = frappe.get_all("Specifications Name",
                                             filters={"parent": kwargs.get("name")},
                                             fields=["name1"],
                                             order_by="idx")
        result = []

        for spec in prod_specifications:
            item_specs = frappe.get_all("Item Specifications",
                                        filters={"name": spec.get("name1")},
                                        fields=["name", "name1"])
            
            spec_values = []
            for item_spec in item_specs:
                spec_details = frappe.get_all("Item Specifications Details",
                                              filters={'parent': item_spec.get("name")},
                                              fields=["item_specifications_value"],
                                              order_by="idx")
                
                item_values = []
                for spec_detail in spec_details:
                    spec_value = frappe.get_all("Item Specifications Value",
                                                filters={"name": spec_detail.get("item_specifications_value")},
                                                fields=["name_value"])
                    value_details = frappe.get_all("Item Specifications Value Details",
                                                   filters={"parent": spec_detail.get("item_specifications_value")},
                                                   fields=["value"],
                                                   order_by="idx")

                    value_list = []
                    for value_detail in value_details:
                        for value in spec_value:
                            value_list.append({"value": value_detail.get("value")})

                    item_values.append({"name": value.get("name_value"), "values": value_list})

                spec_values.append({
                    "name": item_spec.get("name1"),
                    "values": item_values
                })

            result.extend(spec_values)

        return success_response(data=result)
    except Exception as e:
        frappe.logger("utils").exception(e)
        # Assuming error_response is a function that creates an error response
        return error_response(str(e))


def get_contact_us(kwargs):
    try:
        contact_us = frappe.get_doc("Contact Us")
        result = {
            "sales_email_id":contact_us.sales_email_id,
            "sales_contact_number":contact_us.sales_contact_number,
            "supports_email_id":contact_us.supports_email_id,
            "supports_contact_number":contact_us.supports_contact_number
        }
        return success_response(result)
    except Exception as e:
        frappe.logger("utils").exception(e)
        return error_response(str(e))    



def get_pdf_attachments(doctype, doc_name):
    try:
        files = frappe.get_list("File", filters={"attached_to_doctype": doctype, "attached_to_name": doc_name},
                                fields=['file_url'])
        pdf_files = [file for file in files if file.get('file_url').endswith('.pdf')]
        pdf_urls = [file.get('file_url') for file in pdf_files]
        return pdf_urls
    except Exception as e:
        frappe.logger("utils").exception(e)
        return error_response(str(e))

def get_about_us(kwargs):
    try:
        about_us = frappe.get_doc("About Us")
        result = {
            "description":about_us.description
        }
        return success_response(result)
    except Exception as e:
        frappe.logger("utils").exception(e)
        return error_response(str(e))   
    
def get_home_page(kwargs):
    try:
        home_page = frappe.get_doc("Home Page")
        result = {
            "about_us_summary":home_page.about_us_summary,
            "image":home_page.image,
            "about_us_link":home_page.about_us_link,
            "heading":home_page.heading
        }
        return success_response(result)
    except Exception as e:
        frappe.logger("utils").exception(e)
        return error_response(str(e))   


def get_item_images(item_code):
    # Get all Item Images records for the parent item
    child_image_docs = frappe.get_all(
        "Item Images", 
        {"parent": item_code}, 
        ["large_size_image", "upload_image"], 
        order_by="idx asc"
    )
    
    # Process each record to get the appropriate image
    child_images = []
    for img in child_image_docs:
        # Use large_size_image if present, otherwise fall back to upload_image
        image = img.large_size_image if img.large_size_image else img.upload_image
        if image:
            child_images.append(image)
    
    return child_images


def get_variant_attributes(item):
    variant_attribute = frappe.get_all("Item Variant Attribute", filters={"parent":item.get("name")},fields=["attribute","attribute_value"])
    return variant_attribute

def get_variant_details(filters):
	ignore_perm = frappe.session.user == "Guest"
	return frappe.get_list('Item', {"has_variants":0,'variant_of': filters.get('item_code'),"show_on_website":1,"disabled":0}, ignore_permissions=ignore_perm)
	

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

def get_variant_slug(item_code):
	return frappe.get_value('Item',{'item_code':item_code},'slug')


def get_item_varient_attribute(item_code):
    item_varient_details = frappe.get_all('Item Variant Attribute',
							{'parent': item_code}, ['attribute', 'attribute_value'])
    for item in item_varient_details:
        item["abbr"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'abbr')
        item["attr_colour"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'attribute_colour')
    return item_varient_details

# Whitelisted Function
@frappe.whitelist(allow_guest=True)
def get_variants_for_listing(**kwargs):
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


import ast


def get_item_characteristics(category):
    characteristics = frappe.db.sql("""
        SELECT
            ic.label_name, ic.data_type,
            CASE
                WHEN ic.has_value = 0 THEN ic.data_type
                ELSE ic.value
            END
            AS value
        FROM
            `tabItem Characteristics Detail` AS icd
        JOIN
            `tabItem Characteristics` AS ic ON ic.characteristic_name = icd.label_name
        WHERE
            icd.parent = %s;
    """, (category,), as_dict=True)
    if not characteristics:
        return[]

    item_characteristics = {}
    for row in characteristics:
        label_name = row["label_name"]
        if label_name == "Size":
            try:
                item_characteristics["Size"] = json.loads(row["value"])
            except (TypeError, json.JSONDecodeError):
                item_characteristics["Size"] = row["value"]
        else:
            item_characteristics[label_name] = row["value"]
    return item_characteristics


def get_category_size(parent_category):
    item_characteristics_detail = frappe.get_all(
        "Item Characteristics Detail",
        filters={"parent": parent_category},
        fields=["label_name"]
    )
    if not item_characteristics_detail:
        return []

    label_names = [item["label_name"] for item in item_characteristics_detail]
    
    item_characteristics = frappe.get_list(
        "Item Characteristics",
        filters={"name": ["in", label_names]},
        fields=["value"]
    )
    
    category_size = []
    for item in item_characteristics:
        value = item.get("value")
        if not value:
            continue
        
        try:
            parsed_value = ast.literal_eval(value)
            if isinstance(parsed_value, list):
                # Filter out non-numeric values
                category_size.extend([num for num in parsed_value if isinstance(num, (int, float))])
            elif isinstance(parsed_value, (int, float)):
                category_size.append(parsed_value)
            else:
                # Handle non-numeric types gracefully
                return(f"Non-numeric value ignored: {parsed_value}")
        except (ValueError, SyntaxError):
            return(f"Error parsing value: {value}")
            continue

    return category_size


def get_vehicle_detail(item):
    vehicle_detail = frappe.get_all("Vehicle Detail", filters={"parent":item},fields=['vehicle','cc','model','year','model_comments'])
    return vehicle_detail



def get_customer_wise_loyalty_points(email_id, currency):
    try:
        from decimal import Decimal, ROUND_HALF_UP
        from summitapp.api.v2.utils import get_item_price, get_price_list

        
        customer = frappe.get_list(
            "Customer",
            filters={"name": email_id},
            fields=["name", "loyalty_program"]
        )

        if not customer:
            return {}

        loyalty_program_collections = frappe.get_all(
            "Loyalty Program Collection",
            filters={"parent": customer[0].loyalty_program},
            fields=["item", "collection_factor"]
        )

        loyalty_points = {}

        for collection in loyalty_program_collections:
            item_price = get_item_price(
                currency,
                collection.item,
                customer[0].name,
                get_price_list(customer[0].name)
            )

            if item_price[0] and collection.collection_factor:
                item_loyalty_point = item_price[0] / collection.collection_factor
                rounded_points = int(Decimal(item_loyalty_point).to_integral_value(rounding=ROUND_HALF_UP))
                loyalty_points[collection.item] = rounded_points
            else:
                loyalty_points[collection.item] = 0

        return loyalty_points

    except Exception as e:
        frappe.logger('Loyalty').exception(e)
        return error_response(str(e))
    

def add_item_description(item):
    item_description = frappe.db.get_all(
        "Item Description Detail",
        {"parent": item.get("category"), "for_web": 1},
        ["field_name", "label_name"],
        order_by="idx asc",
    )

    for row in item_description:
        row["value"] = item.get(row["field_name"])

    return item_description


def get_loyalty_points(customer_id,currency):
    summit_settings = frappe.get_cached_doc("Summit Settings")
    enable_loyalty_points = summit_settings.enable_loyalty_points 
    if enable_loyalty_points == 1:
        loyalty_points_map = get_customer_wise_loyalty_points(customer_id, currency)
    else:
        loyalty_points_map = {}
    return loyalty_points_map



import json

def category_specification(parent_category):
    item_specification_detail = frappe.get_all(
        "Item Specification Detail",
        filters={"parent": parent_category},
        fields=["specification"]
    )
    if not item_specification_detail:
        return []

    label_names = [item["specification"] for item in item_specification_detail]

    item_specification = frappe.get_list(
        "Item Specification",
        filters={"name": ["in", label_names]},
        fields=["name", "data_type", "value", "value_2"]
    )

    category_specification = []

    for item in item_specification:
        raw_value = item.get("value")
        processed_value = raw_value

        # Try to parse JSON if it's a list-like string
        if isinstance(raw_value, str) and raw_value.strip().startswith("[") and raw_value.strip().endswith("]"):
            try:
                parsed = json.loads(raw_value)
                if isinstance(parsed, list):
                    processed_value = parsed
            except json.JSONDecodeError:
                pass

        spec_data = {
            "specification": item["name"],
            "data_type": item["data_type"],
            "value": processed_value
        }

        # Include value_2 only for formula type
        if item["data_type"] == "formula":
            spec_data["value_2"] = item.get("value_2")

        category_specification.append(spec_data)

    return category_specification

