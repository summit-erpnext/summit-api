# Copyright (c) 2022, 8848Digital LLP and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
# import json

# class PageFilterSetting(Document):
# 	def validate(self):
# 		self.update_filters()

# 	def update_filters(self):
# 		try:
# 			results = []
# 			for section in self.filter_sections:
# 				fs = frappe.get_doc('Filter Section Setting', section.filter_section)
# 				values = []
# 				template = f"SELECT DISTINCT({fs.field}) AS value FROM `tab{fs.doctype_name}`"
# 				if fs.static_condition:
# 					template += f" WHERE {fs.static_condition}"
# 				if fs.apply_dynamic_filter and self.dynamic_field_name:
# 					if not fs.static_condition:
# 						template += " WHERE "
# 					else:
# 						template += " AND "
# 					template += f"{self.dynamic_field_name} = '{self.doctype_link}'"
# 				data = frappe.db.sql(template, as_dict=True)
# 				for row in data:
# 					values.append(row.value)
# 				values = [i for i in values if i]
# 				results.append({
# 					'section': section.filter_section,
# 					'values': values
# 				})
# 			self.response_json = json.dumps({
# 				'doctype': self.doctype_name,
# 				'docname': self.doctype_link,
# 				'filters': results
# 			})
# 		except Exception as e:
# 			frappe.log_error("Error updating filters for page", e)
# 			return None

import frappe
from frappe.model.document import Document
import json

class PageFilterSetting(Document):
    def validate(self):
        self.update_filters()

    def update_filters(self):
        try:
            results = []
            for section in self.filter_sections:
                fs = frappe.get_doc('Filter Section Setting', section.filter_section)
                values = []
                template = f"SELECT DISTINCT({fs.field}) AS value FROM `tab{fs.doctype_name}`"
                if fs.static_condition:
                    template += f" WHERE {fs.static_condition}"
                if fs.apply_dynamic_filter and self.dynamic_field_name:
                    if not fs.static_condition:
                        template += " WHERE "
                    else:
                        template += " AND "
                    template += f"{self.dynamic_field_name} = '{self.doctype_link}'"
                data = frappe.db.sql(template, as_dict=True)
                for row in data:
                    values.append(row.value)
                values = [i for i in values if i]
                if fs.field == "sequence":
                    values = ["asc", "desc"]
                results.append({
                    'section': section.filter_section,
                    'values': values
                })
            self.response_json = json.dumps({
                'doctype': self.doctype_name,
                'docname': self.doctype_link,
                'filters': results
            })
        except Exception as e:
            frappe.log_error("Error updating filters for page", e)
            return None
