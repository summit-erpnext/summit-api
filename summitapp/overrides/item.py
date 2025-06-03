import frappe
import json
from frappe import _
from frappe.utils import now


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

def validate(self, method=None):
	set_parent_category(self)
	set_sub_category(self)
	set_custom_attributes(self)
	add_model_no(self)
	update_image(self)
	validate_category_lvl_4(self)
	validate_attribute_value(self)


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


def set_custom_attributes(doc):
    colour = None
    size = None
    stone = None

    for variant in doc.get("attributes") or []:
        attribute_doc = frappe.get_doc("Item Attribute", variant.attribute)
        for value_row in attribute_doc.get("item_attribute_values") or []:
            if value_row.attribute_value == variant.attribute_value:
                if variant.attribute == "Colour":
                    colour = value_row.attribute_colour
                elif variant.attribute == "Size":
                    size = value_row.abbr
                elif variant.attribute == "Stone":
                    stone = value_row.abbr

    doc.colour = colour
    doc.custom_size = size
    doc.custom_stone = stone



def set_parent_category(doc):
	if doc.category:
		parent = frappe.db.get_value("Category", doc.category, "parent_category")
		if parent:
			doc.custom_parent_category = parent

def set_sub_category(doc):
	if doc.category:
		doc.sub_category = doc.category
  

def update_image(self):
    if self.image:
        self.custom_item_image = self.image

        existing_images = [row.upload_image for row in self.get("custom_item_images")]

        if self.image not in existing_images:
            self.append("custom_item_images", {"upload_image": self.image, "created_on": now()})
    else:
        self.custom_item_image = None
        

def validate_category_lvl_4(self):
    if frappe.db.get_value("Category", self.category, "is_group") != 0:
        frappe.throw(_(f"Category {self.category} is not a level 4 category"))

      
def validate_attribute_value(self):
	for attribute in self.attributes:
		if (
			self.has_variants == 0
			and attribute.attribute
			and attribute.attribute_value
			and frappe.db.get_value(
				"Item Attribute", attribute.attribute, "numeric_values"
			)
			== 1
		):
			try:
				float(attribute.attribute_value)
			except (TypeError, ValueError):
				frappe.throw(
					_(
						f"Attribute Value must be a number for attribute {attribute.attribute}"
					)
				)
