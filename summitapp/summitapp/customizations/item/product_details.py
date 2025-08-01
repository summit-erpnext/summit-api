import frappe
from summitapp.api.v2.utils import (get_field_names, get_filter_list, get_customer_wise_loyalty_points, create_user_tracking,
                                    get_item_field_values,get_item_varient_attribute)
from summitapp.utils import error_response, get_access_level
from summitapp.summitapp.customizations.item.variants import get_product_variants
from frappe import _


def get_product_details(kwargs):
    try:
        create_user_tracking(kwargs, "Product Detail")
        item_slug = kwargs.get('item')
        currency = kwargs.get('currency')
        if not item_slug:
            return error_response(_("Invalid key 'item'"))
        customer_id = kwargs.get('customer_id') or frappe.db.get_value("Customer", {"email": frappe.session.user}, 'name') if frappe.session.user != "Guest" else None
        filters = get_filter_list({'slug': item_slug, 'access_level': get_access_level(customer_id)})
        item_list = frappe.get_list("Item", filters=filters, fields=["*"])
        if not item_list:
            return error_response(_("Item not found"))

        item = item_list[0]  # Now item is a dict, not a list

        field_names = get_field_names('Details')
        translated_item_fields = {}
        if item:
            loyalty_points_map = get_customer_wise_loyalty_points(customer_id, currency)
            item_fields = get_item_field_values(currency, item, customer_id, None, field_names,loyalty_points_map,None,None)
            for fieldname, value in item_fields.items():
                translated_item_fields[fieldname] = _(value)
            translated_item_fields["variants"] = []
            translated_item_fields["attributes"] = []
            translated_item_fields["is_template"] = False
            varient_item = frappe.get_value("Item", {"slug": item_slug}, 'variant_of')
            has_varient = frappe.get_value("Item", {"slug": item_slug}, 'has_variants')
            if varient_item is not None or has_varient == 1:
                if has_varient == 1:
                    template = item_slug
                    translated_item_fields["is_template"] = True
                else:
                    template = varient_item
                processed_items_varient = get_product_variants({"item": template})['data']
                if processed_items_varient["item_code"]:
                    translated_item_fields["item_code"] = processed_items_varient["item_code"]
                translated_item_fields["variants"] = processed_items_varient["variants"]
                translated_item_fields["attributes"] = processed_items_varient["attributes"]
            product_attributes = {}
            if not translated_item_fields["is_template"]:
                for item in get_item_varient_attribute(item.name):
                    product_attributes[item["attribute"]] = item["abbr"]
            translated_item_fields["product_attributes"] = product_attributes
            thumbnail_images = []
            colours = []
            if translated_item_fields.get("slide_img") and 'Colour' in translated_item_fields['product_attributes'].keys() and translated_item_fields['product_attributes']["Colour"] not in colours:
                thumbnail_images.append({ 
                                            "field_name": "Colour",
                                            "Colour": translated_item_fields['product_attributes']["Colour"],
                                            # "image": translated_item_fields.get("slide_img")[0]
                                         })
                colours.append(translated_item_fields['product_attributes']["Colour"])
            
            for varient in translated_item_fields["variants"]:
                if varient.get("image") and 'Colour' in varient.keys() and varient["Colour"] not in colours:
                    thumbnail_images.append({ 
                                            "field_name": "Colour",
                                            "Colour": varient["Colour"],
                                            "image": varient.get("image")[0]
                                         })
                    colours.append(varient["Colour"])
            translated_item_fields["thumbnail_images"] = thumbnail_images
            if translated_item_fields:
                translated_item_fields['previous_item'] = frappe.db.get_value(
                    "Item",
                    {"modified": (">", item.modified), "category": item.category, "show_on_website": 1, "disabled": 0},
                    "slug",
                    order_by="modified asc"
                )
                translated_item_fields['next_item'] = frappe.db.get_value(
                    "Item",
                    {"modified": ("<", item.modified), "category": item.category, "show_on_website": 1, "disabled": 0},
                    "slug",
                    order_by="modified desc"
                )
        
        return {'msg':('Success'), 'data': translated_item_fields}
    
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))