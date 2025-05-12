import json
import frappe
from frappe import _
from erpnext.selling.report.item_wise_sales_history.item_wise_sales_history import get_data
from summitapp.utils import error_response, success_response


@frappe.whitelist()
def get_item_wise_sales_history(kwargs):
    try:
        if isinstance(kwargs, str):
            kwargs = json.loads(kwargs)

        filters = kwargs.get("filters", {})
        if isinstance(filters, str):
            filters = json.loads(filters)

        filters = frappe._dict(filters)
        
        # Set default dates
        from frappe.utils import nowdate, getdate, add_years
        
        # Default to_date = today
        if not filters.get('to_date'):
            filters.to_date = nowdate()
        
        # Default from_date = 1 year before today
        if not filters.get('from_date'):
            today = getdate(nowdate())
            one_year_ago = add_years(today, -1)
            filters.from_date = one_year_ago.strftime('%Y-%m-%d')

        if filters.from_date > filters.to_date:
            frappe.throw(_("From Date cannot be greater than To Date"))
        # Get original report data
        report_data = get_data(filters)
        
        # Calculate targets and enhance data
        enhanced_data = add_target_quantities(report_data, filters)
        
        return success_response(enhanced_data)
    except Exception as e:
        frappe.logger('REPORT').exception(e)
        return error_response(str(e))


def add_target_quantities(data, filters):
    # Group data for target calculations
    target_map = {}
    for row in data:
        key = (row['item_code'], row['customer'])
        if key not in target_map:
            target_map[key] = {'monthly': {}, 'yearly': {}}
        
        date = frappe.utils.getdate(row['transaction_date'])
        year = date.year
        month = date.month
        
        # Monthly aggregation
        month_key = (year, month)
        target_map[key]['monthly'][month_key] = target_map[key]['monthly'].get(month_key, 0) + row['quantity']
        
        # Yearly max tracking
        if year not in target_map[key]['yearly'] or target_map[key]['monthly'][month_key] > target_map[key]['yearly'][year]:
            target_map[key]['yearly'][year] = target_map[key]['monthly'][month_key]

    # Enhance original data with targets
    for row in data:
        date = frappe.utils.getdate(row['transaction_date'])
        year = date.year
        month = date.month
        key = (row['item_code'], row['customer'])
        
        # Add monthly target (total sales for that month)
        row['monthly_target_qty'] = target_map[key]['monthly'].get((year, month), 0)
        
        # Add yearly target (max monthly sales in the year)
        row['target_qty'] = target_map[key]['yearly'].get(year, 0)

    return data


def get_monthly_target_qty(customer, item):
    get_company = frappe.get_doc("Webshop Settings")
    company = get_company.company

    filters = {"company": company, "customer": customer, "item_code": item}
    sales_orders = get_item_wise_sales_history({"filters": filters})  

    if sales_orders and sales_orders.get("data"):
        return sales_orders["data"][0].get('monthly_target_qty')
    return None


def get_yearly_target_qty(customer, item):
    get_company = frappe.get_doc("Webshop Settings")
    company = get_company.company

    filters = {"company": company, "customer": customer, "item_code": item}
    sales_orders = get_item_wise_sales_history({"filters": filters})  

    if sales_orders and sales_orders.get("data"):
        return sales_orders["data"][0].get('target_qty')
    return None
