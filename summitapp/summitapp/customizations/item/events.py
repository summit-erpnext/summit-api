from summitapp.summitapp.customizations.item.utils import (set_product_type_filter, set_parent_category, set_sub_category, set_custom_attributes,
															add_model_no, update_image, validate_category_lvl_4, validate_attribute_value)

def on_save(self, method):
	set_product_type_filter(self, method)

def validate(self, method=None):
	set_parent_category(self)
	set_sub_category(self)
	set_custom_attributes(self)
	add_model_no(self)
	update_image(self)
	validate_category_lvl_4(self)
	validate_attribute_value(self)


