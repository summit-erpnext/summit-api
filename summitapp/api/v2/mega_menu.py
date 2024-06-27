import frappe
from summitapp.utils import error_response, success_response, get_allowed_categories, get_parent_categories

# Whitelisted Function
@frappe.whitelist(allow_guest=True)
def get(kwargs):
	try:
		filters = {'parent_category':['is','not set']}
		categories = get_allowed_categories()
		if categories:
			filters.update({"name": ["in", categories]})
		category_list = get_item_list('Category', filters)
		category_list = [{'values': get_sub_cat(cat, allowed_categories=categories), **cat} for cat in category_list]
		return category_list
	except Exception as e:
		frappe.logger('registration').exception(e)
		return error_response(e)


def breadcrums(kwargs):
	try:
		listing_map = {
			"listing": "product-category",
			"brand": "brand",
			"catalog": "catalog"
		}
		product_type = kwargs.get('product_type')
		if product_type not in listing_map.keys():
			return error_response('Please Specify Correct Product Type')
		category = kwargs.get('category')
		if category:
			parent_categories = get_parent_categories(category)
		else:
			parent_categories = []
		product = kwargs.get('product')
		brand = kwargs.get('brand')
		res = []
		url=None
		last_cat = None
		if not brand:
			for cat in parent_categories:
				url = prepare_url(listing_map.get(product_type), cat.slug)
				res.append({
					'name': cat.label or cat.name,
					'link': url
				})
				last_cat = cat.slug
			if product:
				res.append({
					'name': frappe.get_value('Item', {'slug': product}, 'item_name'),
					'link': prepare_url("product", product, prepare_url("product", last_cat))
				})

		else:
			res.append({
				'name': brand.capitalize(),
				'link': get_item_url(listing_map.get(product_type), brand)
			})
			if product:
				res.append({
					'name': frappe.get_value('Item', {'slug': product}, 'item_name'),
					'link': prepare_url("product", product, prepare_url('brand-product', brand))
				})

		return success_response(data=res)
	except Exception as e:
		frappe.logger('product').exception(e)
		return error_response('error fetching breadcrums url')
	

def get_sub_cat(cat, allowed_categories = None):
	filters = {'parent_category': cat['name']}
	if allowed_categories:
		filters.update({"name": ["in", allowed_categories]})
	sub_cat_list = get_item_list('Category', filters=filters)
	sub_cat_list = [{
						'url': prepare_url("product-category", sub_cat['slug'], parent = None), 
						'values': get_sub_cat(sub_cat, allowed_categories=allowed_categories), 
						**sub_cat
					} for sub_cat in sub_cat_list]
	return sub_cat_list


def get_item_list(doctype, filters):
	ignore_permissions = frappe.session.user == "Guest"
	return frappe.get_list(doctype,
						   filters=filters,
						   fields=['name', 'label', 'sequence as seq', 'slug', 'image'],
						   order_by='sequence', ignore_permissions=ignore_permissions)


def get_item_url(product_type, category=None, product=None):
	url_str = f'/{product_type}'
	if category:
		url_str += f'/{category}'
	if product:
		url_str += f'/{product}'
	return url_str

def prepare_url(prefix, category, parent=None):
	if parent:
		return f"{parent}/{category}"
	else:
		return f"/{prefix}/{category}"
	

def get_menu(kwargs):
	try:
		filters = {'parent_category':['is','not set']}
		categories = get_allowed_categories()
		if categories:
			filters.update({"name": ["in", categories]})
		category_list = get_item_menu('Website Navigation Menu', filters)
		category_list = [{
			'url': create_url(cat['slug'],cat['is_product_category'],parent= None), 
			'values': get_sub_menu(cat,allowed_categories=categories), 
					**cat} for cat in category_list]
		return category_list
	except Exception as e:
		frappe.logger('registration').exception(e)
		return error_response(e)
	
def get_sub_menu(cat, allowed_categories = None):
	filters = {'parent_category': cat['name']}
	if allowed_categories:
		filters.update({"name": ["in", allowed_categories]})
	sub_cat_list = get_item_menu('Website Navigation Menu', filters=filters)
	sub_cat_list = [{
						'url': create_url(sub_cat['slug'],sub_cat['is_product_category'],cat['slug']), 
						'values': get_sub_menu(sub_cat, allowed_categories=allowed_categories), 
						**sub_cat
					} for sub_cat in sub_cat_list]
	
	return sub_cat_list

def get_item_menu(doctype, filters):
	ignore_permissions = frappe.session.user == "Guest"
	return frappe.get_list(doctype,
						   filters=filters,
						   fields=['name', 'label', 'sequence as seq', 'slug', 'image','is_product_category'],
						   order_by='sequence', ignore_permissions=ignore_permissions)

def create_url(prefix, pc, parent=None):
    if parent and pc == 0:
        return f"/{parent}/{prefix}"
    elif pc == 1:
        return f"/product-category/{prefix}"
    elif prefix:
        return f"/{prefix}"
    else:
        return ""
	
@frappe.whitelist(allow_guest=True)
def get_mega_menu(kwargs):
	try:
		web_settings = frappe.get_doc("Web Settings")
		if web_settings.use_pc_as_menu == 1:
			menu = get(kwargs)
		else:
			menu = get_menu(kwargs)
		return success_response(data=menu)	
	except Exception as e:
		frappe.logger('mega menu').exception(e)
		return error_response(e)	