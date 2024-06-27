import frappe
from summitapp.utils import success_response, error_response
import json
from summitapp.api.v2.utils import get_field_names
import datetime
from datetime import datetime


@frappe.whitelist()
def create_warranty_claim(kwargs):
    try:
        if frappe.request.data:
            request_data = json.loads(frappe.request.data)
            if not request_data.get('serial_no'): 
                return error_response('Please Specify Serial No')
            if not request_data.get('customer'): 
                return error_response('Please Specify Customer')
            if not request_data.get('issue'): 
                return error_response('Please Specify Issue')

            wc_doc = frappe.new_doc('Warranty Claim')
            wc_doc.service_address = request_data.get('service_address')
            wc_doc.complaint = request_data.get('issue')
            wc_doc.customer = request_data.get('customer')
            wc_doc.serial_no = request_data.get('serial_no')
            wc_doc.status = "Open"
            wc_doc.warranty_amc_status = request_data.get('warranty_amc_status')
            wc_doc.warranty_expiry_date = request_data.get('warranty_expiry_date')
            wc_doc.amc_expiry_date = request_data.get('amc_expiry_date')
            wc_doc.complaint_date = datetime.now()
            sr_doc = frappe.get_doc("Serial No",request_data.get('serial_no'))
            item_code = sr_doc.item_code
            item = frappe.get_doc("Item",item_code)
            wc_doc.item_code = item.item_code
            wc_doc.item_name = item.item_name
            wc_doc.description = item.description

            wc_doc.save(ignore_permissions=True)

            exs_cust_wc = frappe.get_list("Customer Warranty Claim", filters={"customer": wc_doc.customer}, fields=["*"])

            if not exs_cust_wc:
                cus_wc = frappe.new_doc('Customer Warranty Claim')
                cus_wc.customer = wc_doc.customer
            else:
                cus_wc = frappe.get_doc("Customer Warranty Claim", exs_cust_wc[0].name)

            cus_wc.append('details', {
                'doctype': "Customer Warranty Claim Details",
                'warranty_claim': wc_doc.name,
                'serial_no': wc_doc.serial_no,
                'status': wc_doc.status,
                'warranty_amc_status': wc_doc.warranty_amc_status
            })

            cus_wc.save(ignore_permissions=True)

            return success_response(data={'docname': wc_doc.name, 'doctype': wc_doc.doctype})
    except Exception as e:
        frappe.logger("warranty").exception(e)
        return error_response(str(e))



@frappe.whitelist()
def get_warranty_claim(kwargs):
    try:
        filed_names = get_field_names("Warranty Claim")
        if not kwargs.get('serial_no'): 
            return error_response('Please Specify Serial No')
        serial_no = kwargs.get("serial_no")
        warranty_claim = frappe.get_list("Warranty Claim", filters={"serial_no": serial_no}, fields=filed_names)
        return success_response(data=warranty_claim)
    except Exception as e:
        frappe.logger("warranty").exception(e)
        return error_response(str(e))

@frappe.whitelist()
def get_sr_no_list(kwargs):
    try:
        filed_names = get_field_names("Serial NO")
        if not kwargs.get('item_code'): 
            return error_response('Please Specify Item Code')
        item_code = kwargs.get("item_code")
        sr_no = frappe.get_list("Serial No", filters={"item_code": item_code}, fields=filed_names)
        return success_response(data=sr_no)
    except Exception as e:
        frappe.logger("warranty").exception(e)
        return error_response(str(e))

@frappe.whitelist()
def get_sr_no_details(kwargs):
    try:
        filed_names = get_field_names("Serial NO")
        if not kwargs.get('serial_no'): 
            return error_response('Please Specify Serial No')
        serial_no = kwargs.get("serial_no")
        sr_no = frappe.get_list("Serial No", filters={"serial_no": serial_no}, fields=filed_names)
        return success_response(data=sr_no)
    except Exception as e:
        frappe.logger("warranty").exception(e)
        return error_response(str(e))
    
@frappe.whitelist()
def get_cust_wc_details(kwargs):
    try:
        if not kwargs.get('customer'): 
            return error_response('Please Specify Customer Name')
        customer = kwargs.get("customer")
        cust_wc_details = frappe.get_list("Customer Warranty Claim", filters={"name": customer})
        result = {
            "warranty_details":get_details(cust_wc_details[0].name)
        }
        return success_response(data=result)
    except Exception as e:
        frappe.logger("warranty").exception(e)
        return error_response(str(e))    

def get_details(doc):
    try:
        details = frappe.get_all("Customer Warranty Claim Details",
            filters={"parent": doc},fields=["warranty_claim","serial_no","status","warranty_amc_status"])
        return details
    except Exception as e:
        frappe.logger("warranty").exception(e)
        return error_response(e)        