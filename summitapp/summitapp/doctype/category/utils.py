import frappe

def set_item_fields(doc):
    for item_field in doc.item_details:
        item_field.fieldname = frappe.db.get_value(
            "Item Field Details",item_field.label,"fieldname"
        )
    