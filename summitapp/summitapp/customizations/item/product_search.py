import frappe
from summitapp.utils import success_response, error_response
from summitapp.api.v2.utils import create_user_tracking, get_processed_list

def get_product_search(kwargs):
    create_user_tracking(kwargs, "Product Search")
    
    search_value = kwargs.get('search_value')
    if not search_value:
        return error_response("Missing 'search_value' parameter")
    items = frappe.get_list(
        "Item",
        filters = { "disabled": 0},
        or_filters=[
            {"name": search_value}, 
            {"bom_factory_code": search_value}  
        ],
        fields=["name", "category", "slug"]
    )

    if not items:
        return error_response("No products found for the given search value")

    formatted_items = []

    for item in items:
        category = frappe.get_list(
            "Category",
            filters={"name": item['category']},
            fields=["name", "slug"]
        )
        
        if category:
            category_slug = category[0]['slug']
            formatted_items.append(
                {"product": f"product/{category_slug}/{item['slug']}"}
            )
    return {
        "status": "success",
        "data": formatted_items
    }




def get_item_search(kwargs):
    create_user_tracking(kwargs, "Product Search")
    search_value = kwargs.get('search_value')
    if not search_value:
        return error_response("Missing 'search_value' parameter")
    items = frappe.get_list(
                "Item",
                filters={
                    "category": ["like", f"%{search_value}%"]
                },
                fields=['*']
            )
    item_fields = get_processed_list(None,items,None,None)
    return success_response(item_fields)