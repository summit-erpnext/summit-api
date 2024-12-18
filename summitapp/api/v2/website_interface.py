import frappe
from summitapp.utils import error_response, success_response, get_access_level, get_allowed_categories, get_allowed_brands, get_child_categories
import json
from frappe import _
from frappe import qb

# def publish_website_interface(kwargs):
#     try:
#         len_of_publish_data = frappe.get_list("Website Interface", filters={"publish": 1},fields=["name"], pluck="name")
#         if len(len_of_publish_data) > 1:
#             return error_response(str("You cannot have multiple home pages publish at once."))
        
#         WebsiteInterface = qb.DocType("Website Interface")
#         AssociatedComponents = qb.DocType("Associated Components")
#         Component = qb.DocType("Component")
#         data = (
#             qb.from_(WebsiteInterface)
#             .left_join(AssociatedComponents)
#             .on(WebsiteInterface.name == AssociatedComponents.parent)
#             .left_join(Component)
#             .on(Component.name == AssociatedComponents.component)
#             .select(
#                 WebsiteInterface.name,
#                 AssociatedComponents.component,
#                 Component.component_name,
#                 Component.page_name,
#                 Component.section_name,
#                 Component.image
#             )
#             .where(WebsiteInterface.publish == 1)
#             .orderby(AssociatedComponents.idx) 
#             .run(as_dict=True)
#         )
#         return success_response(data = data)
#     except Exception as e:
#         frappe.logger('product').exception(e)
#         return error_response(str(e))


def publish_website_interface(kwargs):
    try:
        len_of_publish_data = frappe.get_list("Website Interface", filters={"publish": 1}, fields=["name"], pluck="name")
        if len(len_of_publish_data) > 1:
            return error_response("You cannot have multiple home pages published at once.")

        WebsiteInterface = qb.DocType("Website Interface")
        AssociatedComponents = qb.DocType("Associated Components")
        ListingPageComponents = qb.DocType("Listing Page Components")
        LayoutComponents = qb.DocType("Layout Components")
        DetailPageComponents = qb.DocType("Detail Page Components")
        CartPageComponents = qb.DocType("Cart Page Components")
        Component = qb.DocType("Component")

        # Fetching data for Home Page
        home_page_data = (
            qb.from_(WebsiteInterface)
            .left_join(AssociatedComponents)
            .on(WebsiteInterface.name == AssociatedComponents.parent)
            .left_join(Component)
            .on(Component.name == AssociatedComponents.component)
            .select(
                WebsiteInterface.name,
                AssociatedComponents.component,
                Component.component_name,
                Component.section_name,
                Component.image
            )
            .where(WebsiteInterface.publish == 1)
            .orderby(AssociatedComponents.idx)
            .run(as_dict=True)
        )

        # Fetching data for Listing Page
        listing_page_data = (
            qb.from_(WebsiteInterface)
            .left_join(ListingPageComponents)
            .on(WebsiteInterface.name == ListingPageComponents.parent)
            .left_join(Component)
            .on(Component.name == ListingPageComponents.component)
            .select(
                WebsiteInterface.name,
                ListingPageComponents.component,
                Component.component_name,
                Component.section_name,
                Component.image
            )
            .where(WebsiteInterface.publish == 1)
            .orderby(ListingPageComponents.idx)
            .run(as_dict=True)
        )

        # Fetching layout component data
        layout_components_data = (
            qb.from_(WebsiteInterface)
            .left_join(LayoutComponents)
            .on(WebsiteInterface.name == LayoutComponents.parent)
            .left_join(Component)
            .on(Component.name == LayoutComponents.component)
            .select(
                WebsiteInterface.name,
                WebsiteInterface.layout,  # Adding the layout field
                LayoutComponents.component,
                Component.component_name,
                Component.section_name,
                Component.image
            )
            .where(WebsiteInterface.publish == 1)
            .orderby(LayoutComponents.idx)
            .run(as_dict=True)
        )

        # Fetching data for Detail Page
        detail_page_data = (
            qb.from_(WebsiteInterface)
            .left_join(DetailPageComponents)
            .on(WebsiteInterface.name == DetailPageComponents.parent)
            .left_join(Component)
            .on(Component.name == DetailPageComponents.component)
            .select(
                WebsiteInterface.name,
                DetailPageComponents.component,
                Component.component_name,
                Component.section_name,
                Component.image
            )
            .where(WebsiteInterface.publish == 1)
            .orderby(DetailPageComponents.idx)
            .run(as_dict=True)
        )

        # Fetching data for Cart Page
        cart_page_data = (
            qb.from_(WebsiteInterface)
            .left_join(CartPageComponents)
            .on(WebsiteInterface.name == CartPageComponents.parent)
            .left_join(Component)
            .on(Component.name == CartPageComponents.component)
            .select(
                WebsiteInterface.name,
                CartPageComponents.component,
                Component.component_name,
                Component.section_name,
                Component.image
            )
            .where(WebsiteInterface.publish == 1)
            .orderby(CartPageComponents.idx)
            .run(as_dict=True)
        )

        # Formatting output
        formatted_output = [
            {"page_name": "home-page", "component_list": home_page_data},
            {
                "page_name": "listing-page",
                "component_list": listing_page_data,
                "layout": layout_components_data[0]["layout"] if layout_components_data else None,
                "layout_component_list": layout_components_data

            },
            {"page_name": "detail-page", "component_list": detail_page_data},
            {"page_name": "cart-page", "component_list": cart_page_data},
        ]


        return success_response(data=formatted_output)

    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))
