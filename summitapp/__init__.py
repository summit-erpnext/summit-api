
__version__ = '0.0.1'


from frappe import handler
from summitapp.overrides.handler import upload_file
handler.upload_file = upload_file


# import frappe.handler
# import summitapp.overrides.handler
# frappe.handler.upload_file = summitapp.overrides.handler.upload_file

