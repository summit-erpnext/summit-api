
def set_gst_category_and_address_type(self, method=None):
    if not self.gst_category:
        self.gst_category = "Unregistered"
    if not self.address_type:
        self.address_type = "Billing"