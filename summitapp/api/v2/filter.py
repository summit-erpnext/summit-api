import frappe
from summitapp.utils import error_response, success_response
import json
from frappe import _

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
    

# @frappe.whitelist(allow_guest=True)
# def get_vehicle_filters(kwargs):
#     try:
#         # Default response structure (raw)
#         raw_response = {
#             "Vehicle Company": frappe.get_list("Vehicle Company", fields=["name"]),
#             "Vehicle": [],
#             "CC": [],
#             "Model": [],
#             "Year": [],
#             "Model Comments": []
#         }

#         if kwargs.get("vehicle_company"):
#             vehicle_company = kwargs.get("vehicle_company")

#             # Get Vehicle Details Data doc name
#             parent_doc = frappe.get_doc("Vehicle Details Data", vehicle_company)
#             parent_name = parent_doc.name

#             # Define Vehicle Detail as DocType
#             VehicleDetail = DocType("Vehicle Detail")

#             # Query unique values using QB
#             def get_distinct_field(field_name):
#                 results = (
#                     frappe.qb.from_(VehicleDetail)
#                     .select(VehicleDetail[field_name].as_('name'))
#                     .where(VehicleDetail.parent == parent_name)
#                     .run(as_dict=True)
#                 )
#                 return [row.get("name") for row in results if row.get("name")]

#             # Populate filters from Vehicle Detail child table
#             raw_response["Vehicle"] = get_distinct_field("vehicle")
#             raw_response["CC"] = get_distinct_field("cc")
#             raw_response["Model"] = get_distinct_field("model")
#             raw_response["Year"] = get_distinct_field("year")
#             raw_response["Model Comments"] = get_distinct_field("model_comments")

#         else:
#             # Populate all values if no company filter
#             raw_response["Vehicle"] = [row["name"] for row in frappe.get_list("Vehicle Variant Name", fields=["name"])]
#             raw_response["CC"] = [row["name"] for row in frappe.get_list("Engine CC", fields=["name"])]
#             raw_response["Model"] = [row["name"] for row in frappe.get_list("Model", fields=["name"])]
#             raw_response["Year"] = [row["name"] for row in frappe.get_list("Model Year", fields=["name"])]
#             raw_response["Model Comments"] = [row["name"] for row in frappe.get_list("Model Comments", fields=["name"])]

#         # Format final response
#         filters = []
#         for key, values in raw_response.items():
#             filters.append({
#                 "section": "Vehicle Company" if key == "Vehicle Company" else key,
#                 "values": [v["name"] if isinstance(v, dict) else v for v in values]
#             })

#         return {
#             "filters": filters,
#         }

#     except Exception as e:
#         frappe.logger('filter').exception(e)
#         return frappe._dict({"status": "error", "message": str(e)})



def get_filters_without_category(kwargs):
    # Define the fields you want to filter on
    filter_fields = ["brand", "colour", "item_classification", "item_group"]

    filters = []

    for field in filter_fields:
        values = frappe.get_all(
            "Item",
            filters={},  # You can apply custom filters here using kwargs
            distinct=True,
            pluck=field
        )
        # Remove None or empty strings
        values = list(filter(None, values))

        # Set section name, replacing label only for item_group
        if field == "item_group":
            section_name = "Manufacturer"
        else:
            section_name = field.replace("_", " ").title()

        filters.append({
            "section": section_name,
            "values": sorted(values)
        })

    result = {
        "filters": filters
    }
    return success_response(result)


@frappe.whitelist(allow_guest=True)
def get_vehicle_filters(kwargs=None):
    vehicle_company_filter = frappe.form_dict.get("vehicle_company")
    vehicle_name_filter = frappe.form_dict.get("vehicle_name")

    try:
        vehicle_company_list = json.loads(vehicle_company_filter) if vehicle_company_filter else []
    except Exception:
        vehicle_company_list = []

    try:
        vehicle_name_list = json.loads(vehicle_name_filter) if vehicle_name_filter else []
    except Exception:
        vehicle_name_list = []

    # All Vehicle Companies (unfiltered)
    all_vehicle_companies = frappe.get_all(
        "Vehicle Variant Name", pluck="vehicle_company", distinct=True
    )

    # Filtered vehicle list for display (with both fields)
    vehicle_filter_for_list = {}
    if vehicle_company_list:
        vehicle_filter_for_list["vehicle_company"] = ["in", vehicle_company_list]

    filtered_vehicle_records = frappe.get_all(
        "Vehicle Variant Name",
        filters=vehicle_filter_for_list,
        fields=["vehicle_company", "vehicle_name"],
        distinct=True
    )

    # Filter dependent values
    dependent_filters = {}
    if vehicle_company_list:
        dependent_filters["vehicle_company"] = ["in", vehicle_company_list]
    if vehicle_name_list:
        dependent_filters["vehicle_name"] = ["in", vehicle_name_list]

    vehicles = frappe.get_all(
        "Vehicle Variant Name",
        filters=dependent_filters,
        fields=["name", "vehicle_company", "vehicle_name"]
    )

    cc_values = set()
    model_values = set()
    year_values = set()
    model_comment_values = set()

    for v in vehicles:
        details = frappe.get_all(
            "Vehicle Detail",
            filters={"parent": v.name},
            fields=["*"]
        )
        for d in details:
            if d.cc:
                cc_values.add(d.cc)
            if d.model:
                model_values.add(d.model)
            if d.year:
                year_values.add(d.year)
            if d.model_comments:
                model_comment_values.add(d.model_comments)

    filters_response = [
        {"section": "Vehicle Company", "values": sorted(set(all_vehicle_companies))},
        {"section": "Vehicle", "values": sorted(filtered_vehicle_records, key=lambda x: x["vehicle_name"])},
        {"section": "CC", "values": sorted(cc_values)},
        {"section": "Model", "values": sorted(model_values)},
        {"section": "Year", "values": sorted(year_values)},
        {"section": "Model Comments", "values": sorted(model_comment_values)},
    ]
    result = {
        "filters": filters_response
        }
    return success_response(result)
