import frappe
from frappe import _
from summitapp.utils import error_response, success_response
from summitapp.api.v2.mega_menu import get_item_url
from summitapp.utils import get_parent_categories
def get_meta_tags(kwargs):
    if not kwargs.get("page_name"):
        return error_response("Missing argument 'page_name'")
    meta = frappe.db.get_value("Meta Tags",{"page_name":kwargs.get("page_name")},
                               ["page_name", "meta_title", "robots", "description"], as_dict=1)
    return success_response(data = meta)

"""
product category- product-category/categorySlug/subCategorySlug/subSubCategorySlug
product - product/categorySlug/subCategorySlug/subSubCategorySlug/productDetailSlug
catalog - catalog/catalog-slug
catalog product - catalog-product/catalog-slug/catalog-product-slug
brand - brand/brandSlug
brand prod - brand-product/brandSlug/brandProductDetailSlug 
"""

def get_site_map(kwargs):
    if kwargs.get("type") == "brand":
        return brand_urls()
    if kwargs.get("type") == "brand-product":
        return brand_product_urls()
    if kwargs.get("type") == "catalog":
        return catalog_urls()
    if kwargs.get("type") == "catalog-product":
        return catalog_product_urls()
    if kwargs.get("type") == "product-category":
        return product_urls()
    if kwargs.get("type") == "product":
        return product_page_urls()

def brand_product_urls():
    brands = frappe.get_all("Brand", {"slug":["is","set"]},["slug","name"])
    BRANDS = {row.name: row.slug for row in brands}
    items = frappe.get_all("Item", {"slug":["is","set"],"published_in_website":1, "brand":["is","set"]},["slug", "brand"])
    result = [generate_urls(["brand-product",BRANDS.get(item.brand), item.slug]) for item in items]
    return result

def brand_urls(with_product=False):
    brands = frappe.get_all("Brand", {"slug":["is","set"]},["slug","name"])
    BRANDS = {row.name: row.slug for row in brands}
    result = [generate_urls(["brand",brand]) for brand in BRANDS.values()]
    return result
    
def catalog_product_urls():
    catalogs = frappe.get_all("Catalog", {"slug":["is","set"]},["slug","name"])
    CATALOGS = {row.name: row.slug for row in catalogs}
    items = frappe.get_all("Item Child",fields=["parent", "item_slug"])
    result = [generate_urls(["catalog-product",CATALOGS.get(item.parent), item.item_slug]) for item in items]
    return result

def catalog_urls(with_product=False):
    catalogs = frappe.get_all("Catalog", {"slug":["is","set"]},["slug","name"])
    CATALOGS = {row.name: row.slug for row in catalogs}
    result = [generate_urls(["catalog",catalog]) for catalog in CATALOGS.values()]
    return result

# def product_urls():
#     categories = frappe.get_all("Category", {"slug":["is","set"]},["slug","name"])
#     CATEGORIES = {row.name: row.slug for row in categories}
#     sub_cat = frappe.get_all("Sub Category", {"slug":["is","set"]},["slug","name", "category"])
#     SUB_CATEGORIES = {row.name: {"slug":row.slug,"parent": row.category} for row in sub_cat}
#     sub_subcat = frappe.get_all("Sub Category", {"slug":["is","set"]},["slug","name", "sub_category_name"])
#     result = []
#     for cat in sub_subcat:
#         lvl3 = cat.slug
#         lvl2 = SUB_CATEGORIES.get(cat.sub_category_name).get('slug')
#         lvl1 = SUB_CATEGORIES.get(cat.sub_category_name).get('parent')
#         lvl1 = CATEGORIES.get(lvl1)
#         result.append(generate_urls(["product-category",lvl1,lvl2,lvl3]))
#     return result

# def product_page_urls():
#     categories = frappe.get_all("Category", {"slug":["is","set"]},["slug","name"])
#     CATEGORIES = {row.name: row.slug for row in categories}
#     sub_cat = frappe.get_all("Sub Category", {"slug":["is","set"]},["slug","name", "category"])
#     SUB_CATEGORIES = {row.name: {"slug":row.slug,"parent": row.category} for row in sub_cat}
#     sub_subcat = frappe.get_all("Sub Category", {"slug":["is","set"]},["slug","name"])
#     SUB_SUBCATEGORIES = {row.name: row.slug for row in sub_subcat}
#     items = frappe.get_all("Item", {"slug":["is","set"],"published_in_website":1,
#                                     "category":["is","set"],"sub_category":["is","set"],
#                                     "level_three_category_name":["is","set"]},["slug","category","sub_category", "level_three_category_name as sub_subcat"])
#     result = []
#     for item in items:
#         lvl4 = item.slug
#         lvl3 = SUB_SUBCATEGORIES.get(item.sub_subcat)
#         lvl2 = SUB_CATEGORIES.get(item.sub_category).get('slug')
#         lvl1 = CATEGORIES.get(item.category)
#         result.append(generate_urls(["product",lvl1,lvl2,lvl3, lvl4]))
#     return result


def generate_urls(path_elements):
    #elements: list of elements of path
    filtered_path_elements = [element for element in path_elements if element is not None]
    return '/' + '/'.join(filtered_path_elements)

def product_urls():
    try:
        categories = frappe.get_list("Category", {"is_group":0,"enable_category":"yes"},pluck="slug")
        item_url_list = []
        
        for rec in categories:
            data = get_parent_categories(rec)
            url = "/".join([data_dict.get("slug") for data_dict in data])
            url = "product-category/" + url
            item_url_list.append(url)
        return success_response(data = item_url_list)
    except Exception as e:
        frappe.logger('utils').exception(e)
        return error_response(e)

def product_page_urls():
    try:
        item_doc = frappe.get_list("Item",["slug", "category"])
        category_url_list = []
        
        for rec in item_doc:
            category_slug = frappe.get_value("Category",rec.get("category"),"slug")
            category_data = get_parent_categories(category_slug)
            category_url = "/".join([data_dict.get("slug") for data_dict in category_data])
            full_url = "product/" + category_url + "/" + rec.get("slug")
            category_url_list.append(full_url)
        count_of_url = len(category_url_list)
        return success_response(data = category_url_list)
    except Exception as e:
        frappe.logger('utils').exception(e)
        return error_response(e)