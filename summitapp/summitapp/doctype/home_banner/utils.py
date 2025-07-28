import frappe
from summitapp.utils import success_response, error_response
from summitapp.api.v2.utils import get_field_names
from werkzeug.wrappers import Response
import json
import datetime


def get_home_banner(kwargs):
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
        # return custom_response(banners_data)
        
    except Exception as e:
        frappe.logger("banner").exception(e)
        return error_response(e)
    
def json_handler(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

def custom_response(data, headers=None):
    response = Response()
    response.mimetype = "application/json"
    response.data = json.dumps(data, default=json_handler, separators=(",", ":"))
    response.headers["Cache-Control"] = "max-age=450000"
    return response



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
