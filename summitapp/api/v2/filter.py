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
    
from frappe.query_builder import DocType
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_vehicle_filters(kwargs):
    try:
        # Default response structure
        response = {
            "Company": frappe.get_list("Motor Company", fields=["name"]),
            "Vehicle": [],
            "CC": [],
            "Model": [],
            "Year": [],
            "Model Comments": []
        }

        if kwargs.get("motor_company"):
            motor_company = kwargs.get("motor_company")

            # Get Vehicle Details Data doc name
            parent_doc = frappe.get_doc("Vehicle Details Data", motor_company)
            parent_name = parent_doc.name

            # Define Vehicle Detail as DocType
            VehicleDetail = DocType("Vehicle Detail")

            # Query unique values using QB
            def get_distinct_field(field_name):
                results = (
                    frappe.qb.from_(VehicleDetail)
                    .select(VehicleDetail[field_name].as_('name'))
                    .where(VehicleDetail.parent == parent_name)
                    .run(as_dict=True)
                )
                return [row for row in results if row.get("name")]

            # Populate filters from Vehicle Detail child table
            response["Vehicle"] = get_distinct_field("vehicle")
            response["CC"] = get_distinct_field("cc")
            response["Model"] = get_distinct_field("model")
            response["Year"] = get_distinct_field("year")
            response["Model Comments"] = get_distinct_field("model_comments")

        else:
            # Populate all values if no company filter
            response["Vehicle"] = frappe.get_list("Vehicle Variant Name", fields=["name"])
            response["CC"] = frappe.get_list("Engine CC", fields=["name"])
            response["Model"] = frappe.get_list("Model", fields=["name"])
            response["Year"] = frappe.get_list("Model Year", fields=["name"])
            response["Model Comments"] = frappe.get_list("Model Comments", fields=["name"])

        return response

    except Exception as e:
        frappe.logger('filter').exception(e)
        return frappe._dict({"status": "error", "message": str(e)})
