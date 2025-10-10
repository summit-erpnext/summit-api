import frappe

def set_item_fields(doc):
    item_meta = frappe.get_meta("Item")

    item_field_map = {
        df.label: df.fieldname
        for df in item_meta.fields
        if df.label
    }

    for item_field in doc.item_details:
        label = item_field.label
        if label in item_field_map:
            item_field.fieldname = item_field_map[label]