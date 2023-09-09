import frappe

def validate(self, method=None):
    name = [self.first_name, self.middle_name, self.last_name]
    self.full_name = " ".join([part.strip() for part in name if part])