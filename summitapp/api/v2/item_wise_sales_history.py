import frappe
from summitapp.summitapp.customizations.general_ledger.utils import item_wise_sales_history


@frappe.whitelist()
def get_item_wise_sales_history(kwargs):
    return item_wise_sales_history(kwargs)