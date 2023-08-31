import frappe
from summitapp.utils import success_response, error_response


def get():
    try:
        # banner_list = frappe.get_all('Home Banner','*')
        # data = []
        # for banner in banner_list:
        #     btn_info = button_info(banner)
        #     data.append(
        #         {
        #             "id": banner.name,
        #             "seq": banner.sequence,
        #             "img": banner.image,
        #             "btn_info": btn_info
        #         }
        #     )
        return success_response(data="v2-banner")
    except Exception as e:
        frappe.logger("registration").exception(e)
        return error_response(e)


def button_info(banner):
    btn_list = []
    if banner.button_1_title and banner.button_1_url:
        btn_list.append({"btn_title":banner.button_1_title, "btn_url":banner.button_1_url})

    if banner.button_2_title and banner.button_2_url:
        btn_list.append({"btn_title":banner.button_2_title, "btn_url":banner.button_2_url})
    return btn_list


