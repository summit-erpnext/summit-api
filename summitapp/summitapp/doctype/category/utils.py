import frappe
from summitapp.utils import error_response, success_response


def get(kwargs):
	try:
		summit_settings = frappe.get_cached_doc("Summit Settings")
		enable_user_based_menu = summit_settings.enable_user_based_menu 
		filters = {'parent_category': ['is', 'not set']}
		
		categories = get_allowed_categories(enable_user_based_menu=enable_user_based_menu)
		if categories:
			filters.update({"name": ["in", categories]})
		
		category_list = get_item_list('Category', filters)
		category_list = [{
			'url': prepare_url("product-category", cat['slug'], parent=None),
			'values': get_sub_cat(cat, allowed_categories=categories),
			**cat
		} for cat in category_list]
		
		return category_list

	except Exception as e:
		frappe.logger('registration').exception(e)
		return error_response(e)


def get_breadcrums(kwargs):
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
		filters = {'enable_category':"Yes"}
		category_list = get_item_menu('Website Navigation Menu', filters)
		return category_list
	except Exception as e:
		frappe.logger('registration').exception(e)
		return error_response(e)

def get_item_menu(doctype, filters):
	ignore_permissions = frappe.session.user == "Guest"
	return frappe.get_list(doctype,
						   filters=filters,
						   fields=['name', 'label', 'sequence as seq', 'slug', 'image','url'],
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
	

def mega_menu(kwargs):
	try:
		summit_settings = frappe.get_doc("Summit Settings")
		if summit_settings.enable_website_navigation_menu == 1:
			menu = get_menu(kwargs)
			return success_response(data=menu)
		else:
			menu = get(kwargs)
			return success_response(data=menu)	
	except Exception as e:
		frappe.logger('mega menu').exception(e)
		return error_response(e)	
	


def get_allowed_categories(category_list = [],enable_user_based_menu = None):
	categories = []
	user = frappe.session.user
	# Changes email to email_id
	if enable_user_based_menu == 1:
		if user != "Guest":
			cust = frappe.db.get_value("Customer", {"email_id": user}, [
									"name", "customer_group"], as_dict=1)
			if cust:
				categories = frappe.db.get_values(
					"Category Multiselect", {"parent": cust["customer_group"]}, "name1", pluck=1)
				if not categories and cust.get("customer_group"):
					categories = frappe.db.get_values(
						"Category Multiselect", {"parent": cust["customer_group"]}, "name1", pluck=1)
		else:
			categories = frappe.db.get_values(
				"Category Multiselect", {"parent": "Web Settings"}, "name1", pluck=1)		
	
	else:
		categories = frappe.get_list("Category",filters={"old_parent":"","is_group": 1})
	allowed_categories = []
	for category in categories:
		allowed_categories += get_child_categories(category,True,True)
	filtered_category = []
	if allowed_categories:
		if category_list:
			filtered_category = [category for category in allowed_categories if category in category_list]
	return filtered_category or (allowed_categories if categories else category_list)



def get_parent_categories(category, is_name = False, excluded = [], name_only = False):
	filters = category if is_name else {"slug":category} 
	cat = frappe.db.get_value("Category", filters, ['lft','rgt'], as_dict=1)
	if not (cat and category):
		return []
	excluded_cat = "', '".join(excluded)
	parent_categories = frappe.db.sql(
		f"""select name, slug, parent_category from `tabCategory`
		where lft <= %s and rgt >= %s
		and enable_category='Yes' and name not in ('{excluded_cat}')
		order by lft asc""",
		(cat.lft, cat.rgt),
		as_dict=True,
	)
	if name_only:
		return [row.name for row in parent_categories] if parent_categories else []
	return parent_categories

def get_child_categories(category, is_name = False, with_parent = False):
	filters = category if is_name else {"slug":category} 
	cat = frappe.db.get_value("Category", filters, ['lft','rgt'], as_dict=1)
	category_list = []
	if not (cat and filters):
		return []
	child_categories = frappe.db.sql(
		"""select name, slug, parent_category from `tabCategory`
		where lft >= %s and rgt <= %s
		and enable_category='Yes'
		order by lft asc""",
		(cat.lft, cat.rgt),
		as_dict=True,
	)
	category_list = [child.name for child in child_categories]
	if category_list and with_parent:
		for category in category_list:
			category_list += get_parent_categories(category, True, category_list, True)
	return category_list




def categories(kwargs):
	filters = {
		"enable_category": "Yes"
	}
	ignore_perm = frappe.session.user == "Guest"
	return frappe.get_list('Category',
							   filters=filters,
							   fields=['name as category', 'image', 'slug', 'url as category_url', 'description'],
							   ignore_permissions=ignore_perm)
