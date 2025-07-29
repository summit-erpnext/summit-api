import frappe
from summitapp.summitapp.customizations.coupon_code.utils import update_coupon_code, delete_coupon_code


# Update Coupon Code
@frappe.whitelist()
def put(kwargs):
    return update_coupon_code(kwargs)


# Delete Coupon Code
@frappe.whitelist()
def delete(kwargs):
    return delete_coupon_code(kwargs)
