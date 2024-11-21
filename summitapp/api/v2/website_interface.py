import frappe
from summitapp.utils import error_response, success_response, get_access_level, get_allowed_categories, get_allowed_brands, get_child_categories
import json
from frappe import _

def publish_website_interface(kwargs):
    try:
        len_of_publish_data = frappe.get_list("Website Interface", filters={"publish": 1},fields=["name"], pluck="name")
        if len(len_of_publish_data) > 1:
            return error_response(str("Your cannot have multiple publish at home page at once"))
        data = frappe.db.sql('''
            SELECT wi.name,ac.component,c.page_name,c.section_name,c.image
            FROM `tabWebsite Interface` AS wi 
            LEFT JOIN `tabAssociated Components` AS ac 
            ON wi.name = ac.parent 
            LEFT JOIN `tabComponent` AS c 
            ON c.name = ac.component
            WHERE wi.publish = 1
            ''', as_dict=1)
        return success_response(data = data)
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))
