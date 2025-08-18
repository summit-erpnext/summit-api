import frappe
from summitapp.summitapp.customizations.blog_post.utils import get_list, get_detail


# Get Blog Post List
@frappe.whitelist(allow_guest=True)
def get_blog_post_list(kwargs):
    return get_list(kwargs)


# Get Blog Post Detail
@frappe.whitelist(allow_guest=True)
def get_blog_post_detail(kwargs):
    return get_detail(kwargs)
