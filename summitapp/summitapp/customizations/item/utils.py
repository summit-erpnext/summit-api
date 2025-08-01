import frappe, json
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe.utils import now
from summitapp.summitapp.customizations.brand.utils import get_allowed_brands
from summitapp.summitapp.doctype.category.utils import get_allowed_categories
import datetime
from werkzeug.wrappers import Response
from summitapp.utils import success_response, error_response, get_access_level
from summitapp.api.v2.utils import  get_processed_list, get_customer_id
from summitapp.api.v2.translation import translate_result
from summitapp.api.v2.product import get_list

def set_product_type_filter(self, method):
	if self.get("product_type"):
		pt_doc = frappe.get_doc('Product Type', self.product_type)
		field_names = [field.field_name for field in pt_doc.product_type_field]
		item_filters_field = [field.field_name for field in self.item_filters]
		for field_name in field_names:
			if field_name not in item_filters_field:
				self.append("item_filters", {
					"doctype": "Item Filters",
					"field_name": field_name
				})


def add_model_no(self):
	if self.get("model_multiselect"):
		self.model_no = ", ".join([row.name1 for row in self.get("model_multiselect")])
	else:
		self.model_no = None


def toggle_variant_as_default(item_code, attribute, docname, value):
	value = 1 - int(value)
	if value:
		existing = frappe.db.get_value("Item Variant Attribute", {"variant_of": item_code, "attribute": attribute, "is_default":1, "name": ["!=",docname]},"parent")
		if existing:
			frappe.throw(_(f"Please toggle default of Item: {existing} first"))
	frappe.db.set_value("Item Variant Attribute", docname, "is_default", value)


def set_custom_attributes(doc):
    colour = None
    size = None
    stone = None

    for variant in doc.get("attributes") or []:
        attribute_doc = frappe.get_doc("Item Attribute", variant.attribute)
        for value_row in attribute_doc.get("item_attribute_values") or []:
            if value_row.attribute_value == variant.attribute_value:
                if variant.attribute == "Colour":
                    colour = value_row.attribute_colour
                elif variant.attribute == "Size":
                    size = value_row.abbr
                elif variant.attribute == "Stone":
                    stone = value_row.abbr

    doc.custom_colour = colour
    doc.custom_size = size
    doc.custom_stone = stone



def set_parent_category(doc):
	if doc.category:
		parent = frappe.db.get_value("Category", doc.category, "parent_category")
		if parent:
			doc.custom_parent_category = parent

def set_sub_category(doc):
	if doc.category:
		doc.sub_category = doc.category
  

def update_image(self):
    if self.image:
        self.custom_item_image = self.image

        existing_images = [row.upload_image for row in self.get("custom_item_images")]

        if self.image not in existing_images:
            self.append("custom_item_images", {"upload_image": self.image, "created_on": now()})
    else:
        self.custom_item_image = None
        

def validate_category_lvl_4(self):
    if frappe.db.get_value("Category", self.category, "is_group") != 0:
        frappe.throw(_(f"Category {self.category} is not a level 4 category"))

      
def validate_attribute_value(self):
	for attribute in self.attributes:
		if (
			self.has_variants == 0
			and attribute.attribute
			and attribute.attribute_value
			and frappe.db.get_value(
				"Item Attribute", attribute.attribute, "numeric_values"
			)
			== 1
		):
			try:
				float(attribute.attribute_value)
			except (TypeError, ValueError):
				frappe.throw(
					_(
						f"Attribute Value must be a number for attribute {attribute.attribute}"
					)
				)



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



def get_items_via_search(global_items, filters):
	item_list = []
	items = [item.name for item in global_items]
	filters['name'] = ["in", items]
	ignore_permission = bool(frappe.session.user == "Guest")
	item_list = frappe.get_list(
		'Item', filters, '*', ignore_permissions=ignore_permission)
	return len(item_list), item_list

def get_count(doctype, **args):
	distinct = "distinct " if args.get("distinct") else ""
	args["fields"] = [f"count({distinct}`tab{doctype}`.name) as total_count"]
	res = DatabaseQuery(doctype).execute(**args)
	data = res[0].get("total_count")
	return data


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



def get_item_varient_attribute(item_code):
    item_varient_details = frappe.get_all('Item Variant Attribute',
							{'parent': item_code}, ['attribute', 'attribute_value'])
    for item in item_varient_details:
        item["abbr"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'abbr')
        item["attr_colour"] = frappe.db.get_value('Item Attribute Value', {"attribute_value": item["attribute_value"]}, 'attribute_colour')
    return item_varient_details



def cyu_categories(kwargs):
    ignore_permissions = frappe.session.user == "Guest"
    data = frappe.get_list('CYU Categories',
                           filters={},
                           fields=['name as product_category', 'heading', 'label', 'image as product_img', 'slug', 'url as category_url', 'description', 'offer', 'range_start_from'],
                           order_by='sequence',
                           ignore_permissions=ignore_permissions) 
    data_list = success_response(data=data)
    return custom_response(data_list)  


def get_products_recommendation(kwargs):
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


def top_categories(kwargs):
	categories = cyu_categories(kwargs)
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


def default_currency(kwargs):
    ecom_settings = frappe.get_single('Webshop Settings')
    company_name = ecom_settings.company
    default_currency = frappe.get_value('Company', company_name, 'default_currency')
    if not default_currency:
        frappe.throw(f"Default currency not set for company '{company_name}'.")
    return {
          'default_currency': default_currency,
          'company':company_name
          }     



def get_quick_order(kwargs):
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
    


def customer_wise_loyalty_points(email_id, currency):
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
    
