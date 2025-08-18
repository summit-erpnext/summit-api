import frappe
from summitapp.utils import success_response,error_response



def get_catalog_list(kwargs):
	try:
		catalog_list = frappe.get_list('Catalog', {}, '*', ignore_permissions=1, order_by='sequence')
		result = [{"id": catalog.name, "access_level": catalog.access_level, "name": catalog.name,"slug":catalog.slug,"image":catalog.image,"sequence":catalog.sequence, "product_counts": len(get_item_list(catalog.name)), "url": f"catalog/{catalog.slug}"} for catalog in catalog_list]
		return success_response(data=result)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'Catalog Error')
		return error_response(e)

def get_item(kwargs):
    from summitapp.api.v2.product import get_list as get_item_details
    try:
        catalog_slug = kwargs.get('catalog_slug')
        catalog = frappe.db.get_value('Catalog', {'slug': catalog_slug})
        if not catalog:
            return error_response('Catalog Does Not Exist')
        item_list = get_item_list(catalog)
        results = []
        for item in item_list:
            result = get_item_details({'item': item}).get("data")
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


def create_new_catalog(kwargs):
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
    

def update_catalog_items(kwargs):
    try:
        if frappe.request.headers:
            roles = frappe.get_roles(frappe.session.user)
            if "Customer" not in roles:
                return error_response('please login as a Customer')

            catalog_name = kwargs.get('catalog_name')
            items = kwargs.get('item')  # Expecting a list of items as stringified JSON

            if not frappe.db.exists('Catalog', catalog_name):
                return error_response(f'Catalog {catalog_name} does not exist')

            # Ensure items is parsed into a proper list
            try:
                if isinstance(items, str):
                    items = frappe.parse_json(items)
                if not isinstance(items, list):
                    items = [items]
            except Exception:
                return error_response('Invalid items format. Expected a JSON array.')

            result = add_items(catalog_name, items)
            return success_response(data=result)
    except Exception as e:
        frappe.logger('catalog').exception(e)
        return error_response('Error posting catalog')


def add_items(catalog_name, items):
    cat_doc = frappe.get_doc('Catalog', catalog_name)
    existing_items = get_item(cat_doc.name)  # Get existing items in catalog

    response_message = ''
    for item in items:
        if not frappe.db.exists('Item', item):
            response_message += f'Item {item} does not exist. '
            continue

        if item in existing_items:
            response_message += f'Item {item} already present in catalog. '
            continue

        # Append item to catalog
        cat_doc.append('items', {'item': item})
        response_message += f'Item {item} added to catalog. '

    # Save the catalog only if there are changes
    if response_message and 'added to catalog' in response_message:
        cat_doc.save(ignore_permissions=True)

    return response_message.strip()


def delete_catalog_items(kwargs):
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



def delete_item(catalog_name, item):
    cat_doc = frappe.get_doc('Catalog', catalog_name)
    item_doc = frappe.get_doc('Item', item)
    if item_doc.name not in get_item(cat_doc.name):
        return 'Item Not Present In Catalog'
    
    frappe.db.delete('Item Child', 
                    {'parent': cat_doc.name, 'item': item_doc.name})
    return 'Item Deleted From Catalog'


def delete_entire_catalog(kwargs):
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
    

def delete_catalog(catalog):
    frappe.db.delete('Catalog', catalog)
    return 'Catalog Deleted'    

def get_item(catalog):
    cat_doc = frappe.get_doc('Catalog', catalog)
    return [items.item for items in cat_doc.items]
