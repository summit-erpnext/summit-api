import frappe

def before_validate(self, method=None):
    if not self.gst_category:
        self.gst_category = "Unregistered"
    if not self.address_type:
        self.address_type = "Billing"