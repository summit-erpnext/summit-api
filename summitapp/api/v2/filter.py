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
        # Default response structure (raw)
        raw_response = {
            "Company": frappe.get_list("Vehicle Company", fields=["name"]),
            "Vehicle": [],
            "CC": [],
            "Model": [],
            "Year": [],
            "Model Comments": []
        }

        if kwargs.get("vehicle_company"):
            vehicle_company = kwargs.get("vehicle_company")

            # Get Vehicle Details Data doc name
            parent_doc = frappe.get_doc("Vehicle Details Data", vehicle_company)
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
                return [row.get("name") for row in results if row.get("name")]

            # Populate filters from Vehicle Detail child table
            raw_response["Vehicle"] = get_distinct_field("vehicle")
            raw_response["CC"] = get_distinct_field("cc")
            raw_response["Model"] = get_distinct_field("model")
            raw_response["Year"] = get_distinct_field("year")
            raw_response["Model Comments"] = get_distinct_field("model_comments")

        else:
            # Populate all values if no company filter
            raw_response["Vehicle"] = [row["name"] for row in frappe.get_list("Vehicle Variant Name", fields=["name"])]
            raw_response["CC"] = [row["name"] for row in frappe.get_list("Engine CC", fields=["name"])]
            raw_response["Model"] = [row["name"] for row in frappe.get_list("Model", fields=["name"])]
            raw_response["Year"] = [row["name"] for row in frappe.get_list("Model Year", fields=["name"])]
            raw_response["Model Comments"] = [row["name"] for row in frappe.get_list("Model Comments", fields=["name"])]

        # Format final response
        filters = []
        for key, values in raw_response.items():
            filters.append({
                "section": "Company" if key == "Company" else key,
                "values": [v["name"] if isinstance(v, dict) else v for v in values]
            })

        return {
            "filters": filters,
        }

    except Exception as e:
        frappe.logger('filter').exception(e)
        return frappe._dict({"status": "error", "message": str(e)})
