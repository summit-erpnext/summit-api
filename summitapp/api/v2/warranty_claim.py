import frappe
from summitapp.summitapp.customizations.warranty_claim.utils import (warranty_claim, new_warranty_claim, serial_number_list,
                                                                     serial_number_details, customer_warranty_claim_details)


# Get warranty claim
@frappe.whitelist()
def get_warranty_claim(kwargs):
    return warranty_claim(kwargs)

# Create Warranty Claim
@frappe.whitelist()
def create_warranty_claim(kwargs):
    return new_warranty_claim(kwargs)
   
# Get serial number list
@frappe.whitelist()
def get_sr_no_list(kwargs):
    return serial_number_list(kwargs)

# get serial number details
@frappe.whitelist()
def get_sr_no_details(kwargs):
    return serial_number_details(kwargs)
    
# get custome warranty claim details    
@frappe.whitelist()
def get_cust_wc_details(kwargs):
    return customer_warranty_claim_details(kwargs)