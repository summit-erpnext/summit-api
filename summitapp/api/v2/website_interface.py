import frappe
from summitapp.utils import error_response, success_response
from frappe import qb

def publish_website_interface(kwargs):
    try:
        page_type = kwargs.get("page_type")
        
        # Ensure only one home page is published
        published_pages = frappe.get_list(
            "Website Interface", filters={"publish": 1, "page_type": page_type}, fields=["name"], pluck="name"
        )
        if len(published_pages) > 1:
            return error_response("You cannot have multiple home pages published at once.")
        
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
        
        # Fetch data based on the page_type
        page_type_to_component_mapping = {
            "Home Page": ("Website Interface", "Associated Components", "component"),
            "Product Category Page": ("Website Interface", "Top Section Components", "component"),
            "Product Page": ("Website Interface", "Top Section Components", "component"),
            "Cart Page": ("Website Interface", "Associated Components", "component"),
            "Catalog Page": ("Website Interface", "Associated Components", "component"),
        }
        
        if page_type not in page_type_to_component_mapping:
            return error_response("Invalid page_type specified.")
        
        # Extract the relevant doctypes and fetch components
        parent_doctype, child_doctype, component_field = page_type_to_component_mapping[page_type]
        components = fetch_component_data(parent_doctype, child_doctype, component_field)
        
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
        
        # Filter the fetched components
        filtered_components = filter_invalid_components(components)
        
        # Format the output
        formatted_output = {
            "page_name": page_type,
            "component_list": filtered_components,
        }
        
        # Include layout if page_type is product_category_page
        if page_type == "product_category_page" and filtered_components:
            formatted_output["layout"] = filtered_components[0].get("layout")
        
        return success_response(data=formatted_output)
    
    except Exception as e:
        frappe.logger('product').exception(e)
        return error_response(str(e))
