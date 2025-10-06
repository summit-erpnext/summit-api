import frappe

def set_label_name_value(doc):
    if doc.label:
        doc.label_value = doc.label


def set_update_fields(doc):   
    if not doc.label:
        return
    meta = frappe.get_meta("Item")
    for field_details in meta.fields:
        if field_details.label == doc.label:
            doc.fieldname = field_details.fieldname
            break
        
def get_item_field_details():
    meta = frappe.get_meta("Item")
    exclude_fieldtypes = ["Section Break","Column Break","Tab Break","HTML","Table of Contents","Button"]
    fields_list =  [   
        field.label
        for field in meta.fields
        if field.fieldtype not in exclude_fieldtypes
    ]    
    return fields_list