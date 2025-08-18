from summitapp.summitapp.doctype.web_settings.utils import add_category_from_sub

def validate(self, method=None):
	add_category_from_sub(self, "select_sub_category", "select_category")