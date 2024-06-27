import frappe
from summitapp.utils import success_response, error_response
from summitapp.api.v2.utils import get_field_names,get_logged_user

# def get(kwargs):
#     try:
#         if frappe.request.headers:
#             if customer := kwargs.get('customer_id'):
#                 customer_grp = frappe.db.get_value('Customer', customer, 'customer_group')
#             else:
#                 email = get_logged_user()
#                 customer, customer_grp = frappe.db.get_value("Customer", {'email': email}, ['name', "customer_group"])
#             banner_list = frappe.db.sql(f"""
#                 SELECT 
#                     hb.name,
#                     hb.for_customer,
#                     if(hb.for_customer, (
#                         SELECT chb.sequence
#                         FROM `tabHome Banner Sequence` chb
#                         WHERE (
#                             (chb.customer = '{customer}' OR NULLIF(chb.customer,'') IS NULL)
#                             AND (chb.customer_group = '{customer_grp}' OR NULLIF(chb.customer_group,'') IS NULL)
#                         )
#                         AND chb.parent = hb.name
#                         LIMIT 1
#                     ), hb.sequence) as sequence,
#                     hb.img,
#                     hb.button_1_title,
#                     hb.button_1_url,
#                     hb.button_2_title,
#                     hb.button_2_url,
#                     hb.heading,
#                     hb.description
#                 FROM
#                     `tabHome Banner` hb
#                 ORDER BY
#                     sequence,
#                     for_customer DESC
#             """, as_dict=True)

#         else:
#             banner_list = frappe.get_list('Home Banner', filters={'for_customer': 0}, fields=['*'], order_by='sequence', ignore_permissions=True)
#         data = []

#         for banner in banner_list:
#             if not banner.get('sequence'):
#                 continue

#             banner_data = {}
#             field_names = get_field_names('Banner')
#             for field_name in field_names:
#                 if field_name in banner:
#                     banner_data[field_name] = banner[field_name]

#             banner_data['btn_info'] = button_info(banner)
#             data.append(banner_data)

#         return success_response(data)
#     except Exception as e:
#         frappe.logger("registration").exception(e)
#         return error_response(e)


def button_info(banner):
    btn_list = []
    if banner.get('button_1_title') or banner.get('button_1_url'):
        btn_list.append({
            "btn_title": banner.get('button_1_title'),
            "btn_url": banner.get('button_1_url')
        })

    if banner.get('button_2_title') or banner.get('button_2_url'):
        btn_list.append({
            "btn_title": banner.get('button_2_title'),
            "btn_url": banner.get('button_2_url')
        })

    return btn_list


def get(kwargs):
    try:
        fields = get_field_names("Banner")

        banners = frappe.get_list("Home Banner", filters={"show_on_home_page": 1}, fields=["*"],order_by ="sequence")

        if kwargs.get("category"):
            banners = frappe.get_list("Home Banner", filters={"category": kwargs.get("category")}, fields=["*"])

        for banner in banners:
            banner['btn_info'] = button_info(banner)

        # Extracting desired fields after adding button_info
        for banner in banners:
            filtered_banner = {key: value for key, value in banner.items() if key in fields}
            banner.clear()
            banner.update(filtered_banner)

        return success_response(banners)
        
    except Exception as e:
        frappe.logger("banner").exception(e)
        return error_response(e)


