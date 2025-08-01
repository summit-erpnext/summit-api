import frappe, json
from summitapp.utils import success_response, error_response
from summitapp.summitapp.customizations.user.utils import get_logged_user
from frappe.utils import flt
from summitapp.api.v2.utils import (get_stock_info,get_field_names,get_product_url,
				    get_currency,get_currency_symbol,get_logged_user,get_variant_attributes)
from summitapp.summitapp.doctype.category.utils import get_parent_categories

def get_cart_list(kwargs):
    try:
        email = None
        token = None
        headers = frappe.request.headers
        if not headers or 'Authorization' not in headers:
            return error_response('Please Specify Authorization Token')
        auth_header = headers.get('Authorization')
        if "token" in auth_header:
            email = get_logged_user()
        else:
            token = auth_header
        customer = frappe.get_value("Customer", {'email': email})
        result = get_quotation_details(customer, token)
        return {'msg': 'success', 'data': result}
    except Exception as e:
        frappe.logger('cart').exception(e)
        return error_response(e)


def get_quotation_details(customer,token):
	or_filter = {"session_id":token}
	if customer:
		or_filter["party_name"] = customer
	quotations = frappe.get_list("Quotation", filters={'status': 'Draft'}, or_filters=or_filter, fields='*')
	grand_total = 0
	item_fields = []
	grand_total_excluding_tax = 0
	result = {}
	for quot in quotations:
		quot_doc = frappe.get_doc('Quotation', quot['name'])
		grand_total = quot_doc.rounded_total or quot_doc.grand_total
		grand_total_excluding_tax = quot_doc.total
		item_fields = get_processed_cart(quot_doc)
		result = {
			'party_name': quot_doc.party_name,
			'name':  quot_doc.name,
			'total_qty':  quot_doc.total_qty,
			'transaction_date': quot_doc.transaction_date,
			'categories': item_fields,
			'grand_total_including_tax': grand_total,
			'grand_total_excluding_tax': grand_total_excluding_tax, 
		}
	return result


def get_processed_cart(quot_doc):
    item_dict = {}
    category_wise_item = {}
    processed = []
    field_names = get_field_names('Cart')  # Retrieve field names from admin-controlled function
    for row in quot_doc.items:
        item_doc = frappe.db.get_value("Item", row.item_code, "*")
        computed_fields = {
			"variant_attributes": lambda: {"variant_attributes":get_variant_attributes(item_doc)},
            'min_order_qty': lambda: {'min_order_qty': item_doc.get("min_order_qty")},
			'weight_per_unit':lambda:{"weight_per_unit":item_doc.get("weight_per_unit")},
			'total_weight':lambda:{"total_weight":row.get("total_weight")},
            'brand_img': lambda: {'brand_img': frappe.get_value('Brand', {'name': item_doc.get('brand')}, 'image')},
            'level_three_category_name': lambda: {'level_three_category_name': item_doc.get("level_three_category_name")},
            'tax': lambda: {'tax': flt(get_item_wise_tax(quot_doc.taxes).get(item_doc.name, {}).get('tax_amount', 0), 2)},
            'product_url': lambda: {'product_url': get_product_url(item_doc)},
            'in_stock_status': lambda: {"in_stock_status": True if get_stock_info(item_doc.name, 'stock_qty') != 0 else False},
            'image_url': lambda: {"image_url": item_doc.get("image")},
            'details': lambda: {"details": get_item_details(item_doc, row)},
	    	'currency':lambda:{'currency':get_currency(quot_doc.currency)},
			'currency_symbol':lambda:{'currency_symbol':get_currency_symbol(quot_doc.currency)},
            'store_pickup_available': lambda: {"store_pickup_available": item_doc.get("store_pick_up_available", "No")},
            'home_delivery_available': lambda: {"home_delivery_available": item_doc.get("home_delivery_available", "No")},
        }

        if row.item_code not in item_dict:
            item_dict[row.item_code] = {}
        for field_name in field_names:
            if field_name in computed_fields.keys():
                item_dict[row.item_code].update(computed_fields[field_name]())
            else:
                item_dict[row.item_code].update({field_name: row.get(field_name)})

        existing_cat = category_wise_item.get(item_doc.category)
        item_list = [row.item_code]
        if existing_cat:
            item_list = existing_cat.get('item_list', [])
            if row.item_code not in item_list:
                item_list.append(row.item_code)
        category_wise_item[item_doc.category] = {
            'item_list': item_list,
            'category': item_doc.category  # Add the category field to the dictionary
        }
    processed = [
        {
            "category": items.get('category'),  # Get the category from the dictionary
            "parent_categories": get_parent_categories(items.get('category'), True, name_only=True),
            "orders": [item_dict[item] for item in items['item_list'] if item in item_dict]
        }
        for category, items in category_wise_item.items()
    ]
    return processed


def get_item_wise_tax(taxes):
	itemised_tax = {}
	for tax in taxes:
		if getattr(tax, "category", None) and tax.category == "Valuation":
			continue

		item_tax_map = json.loads(tax.item_wise_tax_detail) if tax.item_wise_tax_detail else {}
		if item_tax_map:
			for item_code, tax_data in item_tax_map.items():
				itemised_tax.setdefault(item_code, frappe._dict())
				existing = itemised_tax.get(item_code)
				tax_rate = existing.get('tax_rate',0.0)
				tax_amount =  existing.get('tax_amount',0.0)

				if isinstance(tax_data, list):
					tax_rate += flt(tax_data[0])
					tax_amount += flt(tax_data[1])
				else:
					tax_rate += flt(tax_data)

				itemised_tax[item_code] = frappe._dict(
					dict(tax_rate=tax_rate, tax_amount=tax_amount)
				)

	return itemised_tax


def get_item_details(item_doc, item_row):
	res = []
	res.append({'name': 'Model No', 'value': item_doc.name})
	res.append({'name': 'Price', 'value': item_row.get("price_list_rate")})
	res.extend({"name": attr.attribute, "value": attr.attribute_value} for attr in item_doc.get("attributes",[]))
	return res