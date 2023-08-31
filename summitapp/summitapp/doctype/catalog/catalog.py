# Copyright (c) 2022, 8848Digital LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Catalog(Document):
	pass

@frappe.whitelist()
def update_filter():
    all_catalog = frappe.get_all("Catalog")
    for catalog in all_catalog:
        update_catalog_filter(catalog.name)
        
def update_catalog_filter(catalog):
    try:
        filter  = frappe.get_doc('Catalog Filter',catalog)
        clear_child_table(filter)
        template = """
                    SELECT fl.filter_type, fl.filter_name
                    FROM
                        `tabItem Child` as ic
                    LEFT JOIN
                        `tabItem` as i ON i.name = ic.item
                    LEFT JOIN
                        `tabProduct Type` as pt ON pt.name = i.product_type
                    LEFT JOIN 
                        `tabFilters List` as fl ON fl.parent = pt.name
                    WHERE
                        ic.parent = '%s'
                    """ % catalog
        data = frappe.db.sql(template,as_dict=1)
        for i in data:
            if i.filter_type!=None and i.filter_name!=None:
                filter.add_filter(i.filter_name,i.filter_type)
        filter.save(ignore_permissions=True)
    except Exception as e:
        frappe.logger('filter').exception(e)


def clear_child_table(filter):
    for row in filter.filters:
        filter.remove(row)
    filter.save(ignore_permissions=True)



