from summitapp.summitapp.customizations.address.utils import set_gst_category_and_address_type

def before_validate(self, method=None):
    set_gst_category_and_address_type(self)