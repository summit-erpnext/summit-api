import frappe
from summitapp.utils import error_response, success_response
import json

def get_filters(kwargs):
    try:
        if kwargs.get('doctype') and kwargs.get('docname'):
            doc_name = frappe.db.get_value(kwargs.get('doctype'), {'slug': kwargs.get('docname')})
            if not doc_name:
                return error_response('Docname invalid')
            doc = frappe.get_doc('Page Filter Setting',{'doctype_name':kwargs.get('doctype'),'doctype_link':doc_name})
            return success_response(data = json.loads(doc.response_json))
        return error_response('please Specify docname and doctype')
    except Exception as e:
        frappe.logger('filter').exception(e)
        return error_response(e)