import frappe
from summitapp.utils import success_response,error_response
from summitapp.api.v1.product import get_list as get_item_details


def get(kwargs):
	try:
		catalog_list = frappe.get_list('Catalog', {}, '*', ignore_permissions=1, order_by='sequence')
		result = [{"id": catalog.name, "access_level": catalog.access_level, "name": catalog.name,"slug":catalog.slug,"image":catalog.image,"sequence":catalog.sequence, "product_counts": len(get_item_list(catalog.name)), "url": f"catalog/{catalog.slug}"} for catalog in catalog_list]
		return success_response(data=result)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'Catalog Error')
		return error_response(e)

def get_items(kwargs):
    try:
        catalog_slug = kwargs.get('catalog_slug')
        catalog = frappe.db.get_value('Catalog', {'slug': catalog_slug})
        if not catalog:
            return error_response('Catalog Does Not Exist')
        item_list = get_item_list(catalog)
        results = []
        for item in item_list:
            result = get_item_details({'item': item}).get('data')
            results.extend(result)  # Use extend() instead of append() to add the dictionaries directly
            for item_dict in result:
                item_dict['url'] = f"/catalog-product/{catalog_slug}/{item_dict.get('slug')}"
        return success_response(results)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Catalog Error')
        return error_response(e)

def get_item_list(catalog):
	items = frappe.get_list("Item Child",{"parent":catalog,"parenttype":'Catalog'},pluck='item', ignore_permissions=1)
	return items or []

@frappe.whitelist()
def put(kwargs):
    try:
        if frappe.request.headers:
            roles = frappe.get_roles(frappe.session.user)
            if "Customer" not in roles:
                return error_response('please login as a Customer')

            catalog_name = kwargs.get('catalog_name')
            catalog_access_level = kwargs.get('catalog_access_level')

            if frappe.db.exists('Catalog', catalog_name):
                return error_response(f'catalog {catalog_name} already exists')

            result = create_catalog(catalog_name, catalog_access_level)
            return success_response(data = result)      
    except Exception as e:
        frappe.logger('catalog').exception(e)
        return error_response('error posting catalog')    
    
@frappe.whitelist()
def put_items(kwargs):
    try:
        if frappe.request.headers:
            roles = frappe.get_roles(frappe.session.user)
            if "Customer" not in roles:
                return error_response('please login as a Customer')

            catalog_name = kwargs.get('catalog_name')
            item = kwargs.get('item')
            if not frappe.db.exists('Catalog', catalog_name):
                return error_response(f'catalog {catalog_name} does not exists')

            if not frappe.db.exists('Item', item):
                return error_response(f'Item {item} does not exists')

            result = add_item(catalog_name, item)
            return success_response(data = result)      
    except Exception as e:
        frappe.logger('catalog').exception(e)
        return error_response('error posting catalog')

@frappe.whitelist()
def delete_items(kwargs):
    try:
        if frappe.request.headers:
            roles = frappe.get_roles(frappe.session.user)
            if "Customer" not in roles:
                return error_response('please login as a Customer')

            catalog_name = kwargs.get('catalog_name')
            item = kwargs.get('item')
            if not frappe.db.exists('Catalog', catalog_name):
                return error_response(f'catalog {catalog_name} does not exists')

            if not frappe.db.exists('Item', item):
                return error_response(f'Item {item} does not exists')

            result = delete_item(catalog_name, item)
            return success_response(data = result)      
    except Exception as e:
        frappe.logger('catalog').exception(e)
        return error_response('error posting catalog')       

@frappe.whitelist()
def delete(kwargs):
    try:
        if frappe.request.headers:
            roles = frappe.get_roles(frappe.session.user)
            if "Customer" not in roles:
                return error_response('please login as a Customer')

            catalog_name = kwargs.get('catalog_name')
            if not frappe.db.exists('Catalog', catalog_name):
                return error_response(f'catalog {catalog_name} does not exists')
            result = delete_catalog(catalog_name)
            return success_response(data = result)      
    except Exception as e:
        frappe.logger('catalog').exception(e)
        return error_response('error posting catalog')         
    

def create_catalog(catalog_name, catalog_access_level):
    try:
        last_catalog = frappe.get_last_doc('Catalog')
        last_sequence = last_catalog.sequence
    except frappe.exceptions.DoesNotExistError:
        # Handle the case where there are no documents of type 'Catalog'
        last_sequence = 0
    
    catalog_doc = frappe.new_doc('Catalog')
    catalog_doc.name1 = catalog_name
    catalog_doc.access_level = catalog_access_level
    catalog_doc.sequence = last_sequence + 1
    catalog_doc.save(ignore_permissions=True)
    
    return f'Catalog {catalog_name} Created'


def add_item(catalog_name, item):
    cat_doc = frappe.get_doc('Catalog', catalog_name)
    item_doc = frappe.get_doc('Item', item)
    if item_doc.name in get_item(cat_doc.name):
        return 'Item already Present In Catalog'
    cat_doc.append('items', {
        'item': item_doc.name,
    })
    cat_doc.save(ignore_permissions=True)
    return 'Item Added To Catalog'

def delete_item(catalog_name, item):
    cat_doc = frappe.get_doc('Catalog', catalog_name)
    item_doc = frappe.get_doc('Item', item)
    if item_doc.name not in get_item(cat_doc.name):
        return 'Item Not Present In Catalog'
    
    frappe.db.delete('Item Child', 
                    {'parent': cat_doc.name, 'item': item_doc.name})
    return 'Item Deleted From Catalog'


def get_item(catalog):
    cat_doc = frappe.get_doc('Catalog', catalog)
    return [items.item for items in cat_doc.items]

def delete_catalog(catalog):
    frappe.db.delete('Catalog', catalog)
    return 'Catalog Deleted'