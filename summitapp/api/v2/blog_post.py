import frappe
from summitapp.api.v2.utils import get_field_names
from summitapp.utils import success_response, error_response

def get_blog_post_list(kwargs):
    fields = get_field_names("Blog Post")
    blog_post_list = frappe.get_list("Blog Post",fields=fields)
    return success_response(data=blog_post_list)


def get_blog_post_detail(kwargs):
    slug = kwargs.get("slug")
    if not slug:
        return error_response("Slug is required to fetch detail page")
    fields = get_field_names("Blog Post")
    blog_post_detail = frappe.get_list("Blog Post", filters={"custom_slug": slug}, fields=fields)
    if not blog_post_detail:
        return error_response("Blog Post not found")
    blog_images = frappe.get_all(
        "Item Images",
        filters={"parent": blog_post_detail[0].name},
        fields=["upload_image"]
    )
    blog_post_detail[0]["blog_images"] = blog_images
    
    return success_response(blog_post_detail[0])
