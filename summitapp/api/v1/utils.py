import frappe
from summitapp.utils import success_response, error_response
from webshop.webshop.utils.product import adjust_qty_for_expired_items
from frappe.utils import flt
from frappe.model.db_query import DatabaseQuery
from frappe.utils import nowdate
import requests
from frappe.utils.data import get_url

def validate_pincode(kwargs):
	pincode = True if frappe.db.exists(
		'Delivery Pincode', kwargs.get('pincode')) else False
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

def get_filter_listing(kwargs):
    filters = {
        "disabled": 0
    }
    display_both_item_and_variant = int(frappe.db.get_value("Web Settings", "Web Settings", "display_both_item_and_variant"))
    
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
        item_fields = get_item_field_values(currency,item, customer_id, url_type,field_names)
        processed_items.append(item_fields)
    return processed_items

def get_item_field_values(currency,item, customer_id, url_type,field_names):
    computed_fields = {
        'image_url': lambda: {'image_url': get_default_slide_images(item, True,"size")},
        'status': lambda: {'status': 'template' if item.get('has_variants') else 'published'},
        'in_stock_status': lambda: {'in_stock_status': True if get_stock_info(item.get('name'), 'stock_qty') != 0 else False},
        'brand_img': lambda: {'brand_img': frappe.get_value('Brand', item.get('brand'), ['image']) or None},
        'mrp_price': lambda: {'mrp_price': get_item_price(currency,item.get("name"), customer_id, get_price_list(customer_id))[1]},
        'price': lambda: {'price': get_item_price(currency,item.get("name"), customer_id, get_price_list(customer_id))[0]},
        'currency':lambda:{'currency':get_currency(currency)},
		'currency_symbol':lambda:{'currency_symbol':get_currency_symbol(currency)},
		'display_tag': lambda: {'display_tag': item.get('display_tag') or frappe.get_list("Tags MultiSelect", {"parent": item.name}, pluck='tag', ignore_permissions=True)},
        'url': lambda: {'url': get_product_url(item, url_type)},
		'category_slug': lambda: {'category_slug': get_category_slug(item)},
		'variant': lambda: {'variant':get_variant_details(item.get('variant_of'))},
		'variant_of': lambda: {'variant_of':item.get('variant_of')},
		'equivalent': lambda: {'equivalent': bool(item.get('equivalent') == '1')},
    	'alternate': lambda: {'alternate': bool(item.get('alternate') == '1')},
    	'mandatory': lambda: {'mandatory': bool(item.get('mandatory') == '1')},
    	'suggested': lambda: {'suggested': bool(item.get('suggested') == '1')},
        'brand_video_url': lambda: {'brand_video_url': frappe.get_value('Brand', item.get('brand'), ['brand_video_link']) or None},
		'size_chart': lambda: {'size_chart': frappe.get_value('Size Chart', item.get('size_chart'), 'chart')},
		'slide_img': lambda: {'slide_img': get_default_slide_images(item, False,"size")},
		'features': lambda: {'features': get_features(item.key_features) if item.key_features else []},
		'why_to_buy': lambda: {'why_to_buy': frappe.db.get_value('Why To Buy', item.get("select_why_to_buy"), "name1")},
		'prod_specifications': lambda: {'prod_specifications': get_specifications(item)},
		'store_pick_up_available': lambda: {'store_pick_up_available': item.get('store_pick_up_available') == 'Yes'},
		'home_delivery_available': lambda: {'home_delivery_available': item.get('home_delivery_available') == 'Yes'}
    }
    item_fields = {}
    for field_name in field_names:
        if field_name in computed_fields.keys():
            item_fields.update(computed_fields.get(field_name)())
        else:
            item_fields.update({field_name: item.get(field_name)})
    return item_fields

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
	from summitapp.api.v1.mega_menu import get_item_url
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
				"Website Item", {"item_code": item_code}, item_warehouse_field)
		if not warehouse and template_item_code and template_item_code != item_code:
			warehouse = frappe.db.get_value(
				"Website Item", {
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
			warehouse = frappe.db.get_value("Website Item", {"item_code": item_code}, item_warehouse_field)

		if not warehouse and template_item_code and template_item_code != item_code:
			warehouse = frappe.db.get_value(
				"Website Item", {"item_code": template_item_code}, item_warehouse_field
			)
		if warehouse:
			warehouses.append(warehouse)
			stock_list = frappe.db.sql(
				f"""
				select GREATEST(S.actual_qty - S.reserved_qty - S.reserved_qty_for_production - S.reserved_qty_for_sub_contract, 0) / IFNULL(C.conversion_factor, 1),
				S.warehouse
				from tabBin S
				inner join `tabItem` I on S.item_code = I.Item_code
				left join `tabUOM Conversion Detail` C on I.sales_uom = C.uom and C.parent = I.Item_code
				where S.item_code='{item_code}' and S.warehouse in ('{"', '".join(warehouses)}')"""
			)
			if stock_list:
				for stock_qty in stock_list:
					stock_qty = adjust_qty_for_expired_items(item_code, [stock_qty], stock_qty[1])
					total_qty += stock_qty[0][0]
					if not in_stock:
						in_stock = stock_qty[0][0] > 0 and 1 or 0
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
	feat_val = frappe.get_all("Key Feature",{"key_feature": ["in",key_features]}, ["key_feature as heading", "description"], order_by = "idx")
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

def get_variant_details(item_code):
	if not item_code:
		return []
	item = frappe.db.get_all('Item', filters={'variant_of': item_code}, fields=['name as item_code'])
	for i in item:
		item_doc = frappe.get_doc('Item', i)
		i['attr'] = {}
		for attr in item_doc.attributes:
			if attr.attribute == "Category":
				attr_abbr = frappe.db.get_value('Item Attribute Value', {'parent': attr.attribute, 'attribute_value': attr.attribute_value}, "abbr")
			else:
				attr_abbr = attr.attribute_value
			i['attr'][attr.attribute] = attr_abbr
		for key, val in i['attr'].items():
			i[key] = val
	return item	

def get_list_product_limit(user_role, customer_id):
    if user_role == "Guest":
        web_settings = frappe.get_single("Web Settings")
        if web_settings.product_limit is not None and web_settings.apply_product_limit == 1:
            return web_settings.product_limit
    elif customer_id:
        grp = frappe.db.get_value("Customer", customer_id, 'customer_group')
        if grp:
            customer_group_limit = frappe.db.get_value("Customer Group", grp, "product_limit")
            apply_customer_group_limit = frappe.db.get_value("Customer Group", grp, "apply_product_limit")
            
            if customer_group_limit is not None and apply_customer_group_limit == 1:
                return customer_group_limit
    return 0

def get_logged_user():
    header = {"Authorization": frappe.request.headers.get('Authorization')}
    response = requests.post(get_url() + "/api/method/frappe.auth.get_logged_user", headers=header)
    user = response.json().get("message")
    return user

def get_customer_id(kwargs):
    if kwargs.get('customer_id'):
        customer_id = kwargs.get('customer_id')
    elif frappe.request.headers:
        email = get_logged_user()
        customer_id = frappe.db.get_value("Customer", {"email": email}, 'name')
    else:
        customer_id = None
    return customer_id

def get_guest_user(auth_header):
	guest_user = frappe.db.get_value("Access Token", {"token": auth_header}, 'email')
	if guest_user:
		return guest_user
