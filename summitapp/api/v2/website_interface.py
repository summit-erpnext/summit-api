import frappe
from summitapp.utils import error_response, success_response
from frappe import qb

def publish_website_interface(kwargs):
    try:
        # Extract and validate `page_type` from kwargs
        page_type = kwargs.get("page_type")
        if not page_type:
            return error_response("page_type is required.")

        # Ensure only one home page is published
        if is_multiple_pages_published(page_type):
            return error_response("You cannot have multiple home pages published at once.")

        # Fetch page components and format output
        formatted_output = get_page_components(page_type)

        return success_response(data=formatted_output)

    except Exception as e:
        frappe.logger("product").exception(e)
        return error_response(str(e))

def is_multiple_pages_published(page_type):
    """Check if multiple pages of a given type are published."""
    published_pages = frappe.get_list(
        "Website Interface",
        filters={"publish": 1, "page_type": page_type},
        fields=["name"],
        pluck="name"
    )
    return len(published_pages) > 1

def fetch_component_data(parent_doctype, child_doctype, component_field, page_type):
    """Fetch component data for a specific child table."""
    Component = qb.DocType("Component")
    Parent = qb.DocType(parent_doctype)
    Child = qb.DocType(child_doctype)

    return (
        qb.from_(Parent)
        .left_join(Child).on(Parent.name == Child.parent)
        .left_join(Component).on(Component.name == getattr(Child, component_field))
        .select(
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
            Component.page_name,
            Component.image,
        )
        .where((Parent.publish == 1) & (Parent.page_type == page_type))
        .orderby(Child.idx)
        .run(as_dict=True)
    )

def get_page_components(page_type):
    """Fetch and structure components data based on page type."""
    # Mapping of page types to associated doctypes and fields
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
        raise ValueError("Invalid page_type specified.")

    # Extract relevant doctypes and child table mappings
    parent_doctype, child_table_mapping, component_field = page_type_to_component_mapping[page_type]

    # Fetch components and extract common fields
    components = {}
    common_fields = {}
    for table_name, child_doctype in child_table_mapping.items():
        raw_data = fetch_component_data(parent_doctype, child_doctype, component_field, page_type)
        if raw_data:
            # Extract common fields from the first row
            if not common_fields:
                common_fields = extract_common_fields(raw_data[0])
            # Filter out rows where all component-specific fields are null
            components[table_name] = [
                {key: value for key, value in row.items() if key not in common_fields and value is not None}
                for row in raw_data
                if any(value is not None for key, value in row.items() if key not in common_fields)
            ]
        else:
            # Assign an empty array if no data is found
            components[table_name] = []

    return {
        "page_name": page_type,
        **common_fields,
        **components,
    }

def extract_common_fields(row):
    """Extract common fields from a row."""
    return {
        "page_url": row["page_url"],
        "from_date": row["from_date"],
        "to_date": row["to_date"],
        "page_type": row["page_type"],
        "product_category_page_layout": row["product_category_page_layout"],
        "filters_component": row["filters_component"],
        "product_card_components": row["product_card_components"],
    }
