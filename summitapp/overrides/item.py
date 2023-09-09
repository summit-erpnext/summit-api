import frappe
import json
from frappe import _
from erpnext.e_commerce.doctype.website_item.website_item import insert_item_to_index

def on_save(self, method):
	if self.get("product_type"):
		pt_doc = frappe.get_doc('Product Type', self.product_type)
		field_names = [field.field_name for field in pt_doc.product_type_field]
		item_filters_field = [field.field_name for field in self.item_filters]
		for field_name in field_names:
			if field_name not in item_filters_field:
				self.append("item_filters", {
					"doctype": "Item Filters",
					"field_name": field_name
				})

def on_update(self, method=None):
	if self.published_in_website and frappe.flags.in_import:
		make_website_item(self)

def validate(self, method=None):
	specs_desc = ''
	for row in (self.get("item_filters") or []):
		specs_desc += f'{row.field_name} : {str(row.get("field_value"))}\n'
	self.specification_description = specs_desc
	add_synonym_desc(self)
	add_model_no(self)

def add_synonym_desc(self):
	synonym_desc = ''
	desc = str(self.item_name) + str(self.description) + str(self.specification_description)
	desc = desc.lower()
	all_synonyms = frappe.get_list("Synonyms","*")
	for synonym in all_synonyms:
		if synonym.get('word').lower() in desc:
			synonym_desc += f"{str(synonym.get('synonym'))} "
		elif synonym.get('synonym').lower() in desc:
			synonym_desc += f"{str(synonym.get('word'))} "
	self.synonyms_description = synonym_desc

def add_model_no(self):
	if self.get("model_multiselect"):
		self.model_no = ", ".join([row.name1 for row in self.get("model_multiselect")])
	else:
		self.model_no = None

@frappe.whitelist()
def toggle_variant_as_default(item_code, attribute, docname, value):
	value = 1 - int(value)
	if value:
		existing = frappe.db.get_value("Item Variant Attribute", {"variant_of": item_code, "attribute": attribute, "is_default":1, "name": ["!=",docname]},"parent")
		if existing:
			frappe.throw(_(f"Please toggle default of Item: {existing} first"))
	frappe.db.set_value("Item Variant Attribute", docname, "is_default", value)

@frappe.whitelist()
def make_website_item(doc, save=True):
	"Make Website Item from Item. Used via Form UI or patch."

	if not doc:
		return

	if isinstance(doc, str):
		doc = json.loads(doc)

	if frappe.db.exists("Website Item", {"item_code": doc.get("item_code")}):
		return
	
	website_item = frappe.new_doc("Website Item")
	website_item.web_item_name = doc.get("item_name")

	fields_to_map = [
		"item_code",
		"item_name",
		"item_group",
		"stock_uom",
		"brand",
		"has_variants",
		"variant_of",
		"description",
	]
	for field in fields_to_map:
		website_item.update({field: doc.get(field)})

	# Needed for publishing/mapping via Form UI only
	if not frappe.flags.in_migrate and (doc.get("image") and not website_item.website_image):
		website_item.website_image = doc.get("image")

	if not save:
		return website_item

	website_item.save()

	# Add to search cache
	insert_item_to_index(website_item)

	return [website_item.name, website_item.web_item_name]
