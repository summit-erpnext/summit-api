from mimetypes import guess_type
import frappe
from frappe.handler import check_write_permission
from typing import TYPE_CHECKING

from frappe.utils.data import cint
from frappe.utils.image import optimize_image
if TYPE_CHECKING:
	from frappe.core.doctype.file.file import File
	from frappe.core.doctype.user.user import User
ALLOWED_MIMETYPES = (
	"image/png",
	"image/jpeg",
	"application/pdf",
	"application/msword",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
	"application/vnd.ms-excel",
	"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
	"application/vnd.oasis.opendocument.text",
	"application/vnd.oasis.opendocument.spreadsheet",
	"text/plain",
	"video/quicktime",
	"video/mp4",
)
from summitapp.overrides.image import custom_optimize_image
@frappe.whitelist(allow_guest=True)
def upload_file():
	user = None
	if frappe.session.user == "Guest":
		if frappe.get_system_settings("allow_guests_to_upload_files"):
			ignore_permissions = True
		else:
			raise frappe.PermissionError
	else:
		user: "User" = frappe.get_doc("User", frappe.session.user)
		ignore_permissions = False
	files = frappe.request.files
	is_private = frappe.form_dict.is_private
	doctype = frappe.form_dict.doctype
	docname = frappe.form_dict.docname
	fieldname = frappe.form_dict.fieldname
	file_url = frappe.form_dict.file_url
	folder = frappe.form_dict.folder or "Home"
	method = frappe.form_dict.method
	filename = frappe.form_dict.file_name
	optimize = frappe.form_dict.optimize
	content = None
	if library_file := frappe.form_dict.get("library_file_name"):
		frappe.has_permission("File", doc=library_file, throw=True)
		doc = frappe.get_value(
			"File",
			frappe.form_dict.library_file_name,
			["is_private", "file_url", "file_name"],
			as_dict=True,
		)
		is_private = doc.is_private
		file_url = doc.file_url
		filename = doc.file_name
	if not ignore_permissions:
		check_write_permission(doctype, docname)
	if "file" in files:
		file = files["file"]
		content = file.stream.read()
		filename = file.filename
		content_type = guess_type(filename)[0]
		if optimize and content_type and content_type.startswith("image/"):
			if doctype == "Item":
				args = {"content": content, "content_type": content_type,"quality": 85}
			else:
				args = {"content": content, "content_type": content_type}
			if frappe.form_dict.max_width:
				args["max_width"] = int(frappe.form_dict.max_width)
			if frappe.form_dict.max_height:
				args["max_height"] = int(frappe.form_dict.max_height)
			if doctype == "Item":
				content = custom_optimize_image(**args)
				filename = filename.split(".")[0] + ".webp"
			else:
				content = optimize_image(**args)

	frappe.local.uploaded_file = content
	frappe.local.uploaded_filename = filename
	if content is not None and (frappe.session.user == "Guest" or (user and not user.has_desk_access())):
		filetype = guess_type(filename)[0]
		if filetype not in ALLOWED_MIMETYPES:
			frappe.throw(_("You can only upload JPG, PNG, PDF, TXT or Microsoft documents."))
	if method:
		method = frappe.get_attr(method)
		frappe.is_whitelisted(method)
		return method()
	else:
		if doctype == "Item":
			file_doc = frappe.get_doc(
				{
					"doctype": "File",
					"attached_to_doctype": doctype,
					"attached_to_name": docname,
					"attached_to_field": fieldname,
					"folder": folder,
					"file_name": filename,
					"file_url": file_url,
					"is_private": cint(is_private),
					"content": content,
				}
			).save(ignore_permissions=ignore_permissions)
			
			# Set file_type using db.set_value
			frappe.db.set_value("File", file_doc.name, "file_type", "WPMG")
			
			return file_doc  # Return the saved document
    
		else:
			file_doc = frappe.get_doc(
				{
					"doctype": "File",
					"attached_to_doctype": doctype,
					"attached_to_name": docname,
					"attached_to_field": fieldname,
					"folder": folder,
					"file_name": filename,
					"file_url": file_url,
					"is_private": cint(is_private),
					"content": content,
				}
			).save(ignore_permissions=ignore_permissions)
			
			return file_doc  # Return the saved document
