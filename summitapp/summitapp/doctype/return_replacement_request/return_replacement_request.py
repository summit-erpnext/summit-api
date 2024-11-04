# Copyright (c) 2024, 8848 Digital LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from datetime import datetime, timedelta

class ReturnReplacementRequest(Document):
    def on_submit(self):
        def update_field(source, target,source_parent):
            target.is_replacement=1
            target.returrn_replacement_request = self.name
            # if replacement_sales_order == 0:
            #     target.name = f"{sales_order.name}-Replacement"
            #     # print("iffffffffffffffffffff111",sales_order_naming)
            # else:
            #     target.name = f"{sales_order.name}-Replacement-{replacement_sales_order}"
            #     # print("elseeeeeeee222",sales_order_naming)
        def update_qty(source, target, source_parent):
            target.qty=self.get("quantity")
            target.discount_percentage = 100
       
        sales_order = frappe.get_doc("Sales Order", self.order_id)
        # replacement_sales_order = len(frappe.db.get_all("Sales Order", filters={"parent_sales_order": sales_order.name}, pluck="parent_sales_order"))
             
        new_sales_order = get_mapped_doc(
            "Sales Order",
            self.order_id,
            {
                "Sales Order": {
                    "doctype": "Sales Order",
                    "is_replacement": 1,
                    "transaction_date": datetime.now(),
                    "delivery_date": datetime.now() + timedelta(days=15),
                    "selling_price_list": "Replacement",
                    "returrn_replacement_request":self.name,
                    "postprocess":update_field, 
                    "parent_sales_order":sales_order.name,
                },
                "Sales Order Item": {
				"doctype": "Sales Order Item",
                "field_no_map": ["rate"],
                "field_map": {
                    "item_code": self.product_id,
                    "delivery_date":datetime.now() + timedelta(days=15),
				    },
                "postprocess":update_qty,
				"condition": lambda doc: doc.item_code == self.product_id
			    },   
            },
            target_doc=None
        )

        new_sales_order.insert(ignore_permissions=True)
        frappe.db.set_value("Sales Order",new_sales_order.name,"workflow_state","Approved")
        print(f"New Sales Order Created: {new_sales_order.name}")

@frappe.whitelist()
def get_items_from_sales(doctype, txt, searchfield, start, page_len, filters):
	where_clause = f""" where parent  = '{filters.get("sales_order")}' """ if filters.get("sales_order") else ""
	query = f"""SELECT item_code from `tabSales Order Item` {where_clause}  """
	print(query)
	return frappe.db.sql(query)