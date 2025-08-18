
__version__ = '0.0.1'


from frappe import handler
from summitapp.summitapp.customizations.image_handler.utils import upload_file
handler.upload_file = upload_file

