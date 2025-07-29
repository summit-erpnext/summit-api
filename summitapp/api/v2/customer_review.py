import frappe
from summitapp.summitapp.doctype.customer_reviews.utils import create_cust_review, get_cust_review, create_cust_review_and_send_mail


# Create customer review
@frappe.whitelist()
def create_customer_review(kwargs):
    return create_cust_review(kwargs)


# Get Customer Review
@frappe.whitelist()
def get_customer_review(kwargs):
    return get_cust_review(kwargs)


# Create Customer review and send email
@frappe.whitelist()
def create_customer_review_and_send_mail(kwargs):
    return create_cust_review_and_send_mail(kwargs)