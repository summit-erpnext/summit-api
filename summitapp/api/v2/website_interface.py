import frappe
from summitapp.utils import error_response, success_response
from frappe import qb

def publish_website_interface(kwargs):
    try:
        # Extract page_type from kwargs
        page_type = kwargs.get("page_type")
        
        if not page_type:
            return error_response("page_type is required.")

        # Ensure only one home page is published
        published_pages = frappe.get_list(
            "Website Interface",
            filters={"publish": 1, "page_type": page_type},
            fields=["name"],
            pluck="name"
        )
        if len(published_pages) > 1:
            return error_response("You cannot have multiple home pages published at once.")

        # Function to fetch component data for a specific child table
        def fetch_component_data(parent_doctype, child_doctype, component_field, page_type):
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
                    Parent.page_url,
                    Parent.from_date,
                    Parent.to_date,
                    Parent.page_type,
                    Parent.product_category_page_layout,
                    Parent.filters_component,
                    Parent.product_card_components,
                    Child[component_field],
                    Component.component_name,
                    Component.section_name,
                    Component.image,
                )
                .where((Parent.publish == 1) & (Parent.page_type == page_type))  # Ensure page_type filter
                .orderby(Child.idx)
                .run(as_dict=True)
            )

        # Mapping of page types to their associated doctypes and fields
        page_type_to_component_mapping = {
            "Home Page": ("Website Interface", {"associated_component": "Associated Components"}, "component"),
            "Product Category Page": (
                "Website Interface", 
                {
                    "top_section_component": "Top Section Components",
                    "bottom_section_component": "Bottom Section Components"
                },
                "component"
            ),
            "Product Page": (
                "Website Interface", 
                {
                    "top_section_component": "Top Section Components",
                    "bottom_section_component": "Bottom Section Components"
                },
                "component"
            ),
            "Cart Page": ("Website Interface", {"associated_component": "Associated Components"}, "component"),
            "Catalog Page": ("Website Interface", {"associated_component": "Associated Components"}, "component"),
        }
        
        # Validate page_type
        if page_type not in page_type_to_component_mapping:
            return error_response("Invalid page_type specified.")
        
        # Extract the relevant doctypes and fetch components
        parent_doctype, child_table_mapping, component_field = page_type_to_component_mapping[page_type]

        # Fetch and organize components by child table name
        component_list = {}
        for table_name, child_doctype in child_table_mapping.items():
            component_list[table_name] = fetch_component_data(parent_doctype, child_doctype, component_field, page_type)

        # Filter out invalid components for each child table
        def filter_invalid_components(components):
            return [
                component
                for component in components
                if any(
                    value is not None for key, value in component.items()
                    if key not in ["name", "layout"]  # Ignore certain fields when checking for None
                )
            ]
        
        # Apply filtering to all component lists
        for table_name in component_list:
            component_list[table_name] = filter_invalid_components(component_list[table_name])

        # Format the output
        formatted_output = {
            "page_name": page_type,
            "component_list": component_list,
        }
        
        return success_response(data=formatted_output)

    except Exception as e:
        frappe.logger("product").exception(e)
        return error_response(str(e))
