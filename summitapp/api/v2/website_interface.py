import frappe
from summitapp.utils import error_response, success_response
from frappe import qb

def publish_website_interface(kwargs):
    try:
        # Ensure only one home page is published
        published_pages = frappe.get_list(
            "Website Interface", filters={"publish": 1}, fields=["name"], pluck="name"
        )
        if len(published_pages) > 1:
            return error_response("You cannot have multiple home pages published at once.")

        # Define the doctypes
        doctypes = {
            "home_page": ("Associated Components", "component"),
            "listing_page": ("Listing Page Components", "component"),
            "layout_components": ("Layout Components", "component"),
            "detail_page": ("Detail Page Components", "component"),
            "cart_page": ("Cart Page Components", "component"),
        }

        # Function to fetch component data
        def fetch_component_data(parent_doctype, child_doctype, component_field):
            Component = qb.DocType("Component")
            Parent = qb.DocType(parent_doctype)
            Child = qb.DocType(child_doctype)

            return (
                qb.from_(Parent)
                .left_join(Child)
                .on(Parent.name == Child.parent)
                .left_join(Component)
                .on(Component.name == getattr(Child, component_field))
                .select(
                    Parent.name,
                    Child[component_field],
                    Component.component_name,
                    Component.section_name,
                    Component.image,
                    getattr(Parent, "layout", None).as_("layout")
                )
                .where(Parent.publish == 1)
                .orderby(Child.idx)
                .run(as_dict=True)
            )

        # Fetch data for all page types
        page_data = {
            "home_page": fetch_component_data("Website Interface", "Associated Components", "component"),
            "listing_page": fetch_component_data("Website Interface", "Listing Page Components", "component"),
            "layout_components": fetch_component_data("Website Interface", "Layout Components", "component"),
            "detail_page": fetch_component_data("Website Interface", "Detail Page Components", "component"),
            "cart_page": fetch_component_data("Website Interface", "Cart Page Components", "component"),
        }

        # Filter out invalid components
        def filter_invalid_components(components):
            return [
                component
                for component in components
                if any(
                    value is not None for key, value in component.items()
                    if key not in ["name", "layout"]  # Ignore certain fields when checking for `None`
                )
            ]

        # Format the output
        formatted_output = [
            {
                "page_name": "home-page",
                "component_list": filter_invalid_components(page_data["home_page"]),
            },
            {
                "page_name": "listing-page",
                "component_list": filter_invalid_components(page_data["listing_page"]),
                "layout": page_data["layout_components"][0]["layout"] if page_data["layout_components"] else None,
                "layout_component_list": filter_invalid_components(page_data["layout_components"]),
            },
            {
                "page_name": "detail-page",
                "component_list": filter_invalid_components(page_data["detail_page"]),
            },
            {
                "page_name": "cart-page",
                "component_list": filter_invalid_components(page_data["cart_page"]),
            },
        ]

        return success_response(data=formatted_output)

    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))
