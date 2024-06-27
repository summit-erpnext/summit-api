import frappe
from summitapp.utils import error_response, success_response
from datetime import datetime, timedelta
from frappe.utils import now_datetime

def put(kwargs):
    try:
        if frappe.session.user == "Guest":
            return error_response('Please login As A Customer')
        id = kwargs.get('id')
        coupon_code = kwargs.get('coupon_code')
        if not coupon_code:
            return error_response("Invalid coupon code")
        
        if coupon_name:=frappe.db.exists('Coupon Code', coupon_code):
            # Validate Maximum Use of Coupon Code
            coupon = frappe.db.get_value("Coupon Code", coupon_name, "*")

            if coupon.valid_from:
                valid_from = datetime.min + (coupon.get("from_time") or timedelta(seconds=0))
                valid_from = datetime.combine(coupon.valid_from, valid_from.time())
                if valid_from > now_datetime():
                    return error_response("Coupon code Invalid/Expired")

            if coupon.valid_upto:
                valid_upto = datetime.min + (coupon.get("upto_time") or timedelta(seconds=86399))
                valid_upto = datetime.combine(coupon.valid_upto, valid_upto.time())
                if valid_upto < now_datetime():
                    return error_response("Coupon code Invalid/Expired")

            if coupon.used >= coupon.maximum_use:
                return error_response("Coupon code Invalid/Expired")

        quot_doc = frappe.get_doc('Quotation', id)
        data = put_coupon_code(quot_doc, coupon_code)
        return success_response(data=data)
    except Exception as e:
        frappe.logger('order').exception(e)
        return error_response(e)


def delete(kwargs):
    try:
        id = kwargs.get('id')
        if frappe.session.user == "Guest":
            return error_response('Please login As A Customer')

        quot_doc = frappe.get_doc('Quotation', id)
        # on_item = frappe.db.get_value("Coupon Code", quot_doc.coupon_code, )
        quot_doc.coupon_code = None
        if quot_doc.get("pricing_rules"):
            for item in quot_doc.items:
                item.pricing_rules = None
                item.discount_amount = 0
                item.discount_percentage = 0
                item.rate = item.price_list_rate
        quot_doc.save(ignore_permissions=True)
        return success_response(data='Coupon Code Deleted!')
    except Exception as e:
        frappe.logger('order').exception(e)
        return error_response(e)


def put_coupon_code(quot_doc, coupon_code):
    quot_doc.coupon_code = coupon_code
    quot_doc.save(ignore_permissions=True)
    return 'Coupon Code Applied!'
