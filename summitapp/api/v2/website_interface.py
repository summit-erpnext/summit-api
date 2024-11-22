import frappe
from summitapp.utils import error_response, success_response, get_access_level, get_allowed_categories, get_allowed_brands, get_child_categories
import json
from frappe import _
from frappe import qb

def publish_website_interface(kwargs):
    try:
        len_of_publish_data = frappe.get_list("Website Interface", filters={"publish": 1},fields=["name"], pluck="name")
        if len(len_of_publish_data) > 1:
            return error_response(str("You cannot have multiple home pages publish at once."))
        
        WebsiteInterface = qb.DocType("Website Interface")
        AssociatedComponents = qb.DocType("Associated Components")
        Component = qb.DocType("Component")
        data = (
            qb.from_(WebsiteInterface)
            .left_join(AssociatedComponents)
            .on(WebsiteInterface.name == AssociatedComponents.parent)
            .left_join(Component)
            .on(Component.name == AssociatedComponents.component)
            .select(
                WebsiteInterface.name,
                AssociatedComponents.component,
                Component.page_name,
                Component.section_name,
                Component.image
            )
            .where(WebsiteInterface.publish == 1)
            .orderby(AssociatedComponents.idx) 
            .run(as_dict=True)
        )
        return success_response(data = data)
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))
