
from distutils.log import error
import frappe
from summitapp.utils import error_response, success_response 

def get(kwargs):
    try:
        data = frappe.db.sql(details_query(), as_dict=1)
        return success_response(data=data)
    except Exception as e:
        frappe.logger('seller').exception(e)
        return error_response('error in fetching seller details')

def details_query():
    return  """
            SELECT 
            se.name as username,
            se.gst_number,
            se.user_email_id as email_id,
            se.billing_address as address,
            se.state as state_name,
            se.city as city_name,
            se.country as country_name
            FROM
            `tabSeller Registration` se   
        """