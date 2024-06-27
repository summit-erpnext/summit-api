# import frappe
# from summitapp.utils import success_response, error_response
# import summitapp.api.v2.banner as banner
# from summitapp.api.V1 import V1

# class V2(V1):
#     def __init__(self):
#         self.methods = {'banner':['get']}

#     def class_map(self,kwargs):
#         entity = kwargs.get('entity')
#         method = kwargs.get('method')
#         if self.methods.get(entity) and method in self.methods.get(entity):
#             function = f"{kwargs.get('entity')}.{kwargs.get('method')}({kwargs})"
#             return eval(function)
#         return V1.class_map(self,kwargs)

import frappe
from summitapp.utils import success_response, error_response
import summitapp.api.v2.banner as banner
import summitapp.api.v2.brand as brand
import summitapp.api.v2.otp as otp
import summitapp.api.v2.cart as cart
import summitapp.api.v2.catalog as catalog
import summitapp.api.v2.coupon_code as coupon_code
import summitapp.api.v2.customer_address as customer_address
import summitapp.api.v2.filter as filter
import summitapp.api.v2.mega_menu as mega_menu
import summitapp.api.v2.order as order
import summitapp.api.v2.product as product
import summitapp.api.v2.registration as registration
import summitapp.api.v2.seller as seller
import summitapp.api.v2.signin as signin
import summitapp.api.v2.profile as profile
import summitapp.api.v2.dealer as dealer
import summitapp.api.v2.store_credit as store_credit
import summitapp.api.v2.gl as gl
import summitapp.api.v2.wishlist as wishlist
import summitapp.api.v2.seo as seo
import summitapp.api.v2.utils as utils
import summitapp.api.v2.push_notification as push_notification
import summitapp.api.v2.access_token as access_token
import summitapp.api.v2.translation as translation
import summitapp.api.v2.customer_review as customer_review
import summitapp.api.v2.warranty_claim as warranty_claim


class V2():
    def __init__(self):
        self.methods = {
            'banner': ['get'],
            'otp': ['send_otp', 'verify_otp','send_twilio_sms','send_email_otp','send_pinnacle_sms','login_with_mobile_otp'],
            "brand": ['get', 'get_product_list', 'get_product_details'],
            "cart": ['get_list', 'put_products', 'delete_products', 'clear_cart','request_for_quotation','get_quotation_history'],
            "catalog": ['get', 'get_items','put','put_items','delete','delete_items'],
            "coupon_code": ['put', 'delete'],
            "customer_address": ['get', 'put'],
            "dealer": ['get_dealer'],
            "profile": ['get_profile','customer_inquiry', 'ageing_report', 'get_transporters'],
            "filter": ['get_filters'],
            "mega_menu": ['get', 'breadcrums','get_mega_menu','get_navbar_data','get_menu'],
            "order": ['get_list', 'get_summary', 'get_order_id', 'place_order', 'return_replace_item', 'get_razorpay_payment_url', 'get_order_details', 'recently_bought'],
            "product": ['get_list', 'get_details', 'get_cyu_categories', 'get_variants', 'get_recommendation', 'get_top_categories', "get_tagged_products", "check_availability", "get_categories",'get_default_currency'],
            "registration": ['add_subscriber','customer_signup', 'change_password', 'reset_password', 'send_reset_link', 'create_registration'],
            "seller": ['get'],
            "signin": ['signin', 'get_user_profile', 'signin_as_guest', 'get_redirecting_urls', 'login_via_token','existing_user_signin'],
            "store_credit": ['put', 'delete'],
            "gl": ['get_dealer_ledger', 'get_ledger_summary', "export_ledger"],
            "wishlist": ["add_to_wishlist", "remove_from_wishlist", "get_wishlist_items"],
            "seo": ["get_meta_tags","get_site_map"],
            "utils": ["validate_pincode", "get_cities", 'get_states', 'get_countries','get_contact_us','get_about_us','get_home_page',
                      'get_marquee','get_testomonial','get_company_motto','get_product_specifications','get_pdf_attachments'],
            "push_notification":["get_notification"],
            "access_token":['auth',"get_access_token","login"],
            "translation":["get_languages",'get_translation_text'],
            "customer_review":["get_customer_review","create_customer_review"],
            "warranty_claim":["get_warranty_claim","create_warranty_claim",
                              "get_sr_no_list","get_sr_no_details","get_cust_wc_details"]
        }

    def class_map(self, kwargs):
        entity = kwargs.get('entity')
        print("entity",entity)
        method = kwargs.get('method')
        print("method",method)
        if self.methods.get(entity):
            if method in self.methods.get(entity):
                function = f"{kwargs.get('entity')}.{kwargs.get('method')}({kwargs})"
                return eval(function)
            else:
                return error_response("Method Not Found!")
        else:
            return error_response("Entity Not Found!")
    
        
    
    
    