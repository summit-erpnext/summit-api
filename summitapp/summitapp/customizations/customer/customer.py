from summitapp.summitapp.customizations.customer.utils import set_email_id_and_mobile_no, set_full_name_add_category, on_update_create_shipping_address_and_user

def on_save(self, method):
	set_email_id_and_mobile_no(self)
	

def validate(self, method=None):
	set_full_name_add_category(self)


def on_update(self, method=None):
	on_update_create_shipping_address_and_user(self)


