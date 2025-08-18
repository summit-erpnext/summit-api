import frappe
from summitapp.summitapp.customizations.general_ledger.utils import dealer_ledger, ledger_summary, export_ledger_data


# Get Dealer Ledger
@frappe.whitelist()
def get_dealer_ledger(kwargs):  
	return dealer_ledger(kwargs)


# Get Ledger Summary
@frappe.whitelist()
def get_ledger_summary(kwargs):
	return ledger_summary(kwargs)


# Export Ledger
@frappe.whitelist()
def export_ledger(kwargs):
	return export_ledger_data(kwargs)