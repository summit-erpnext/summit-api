import frappe
import io
import os
from PIL import Image
from frappe.utils.image import optimize_image as optimize_image_original

def custom_optimize_image(content, content_type, max_width=1024, max_height=768, optimize=True, quality=85):
	if content_type == "image/svg+xml":
		return content

	try:
		image = Image.open(io.BytesIO(content))
		width, height = image.size
		max_height = max(min(max_height, height * 0.8), 200)
		max_width = max(min(max_width, width * 0.8), 200)
		image_format = "WebP"
		# image_format = content_type.split("/")[1]
		size = max_width, max_height
		image.thumbnail(size, Image.Resampling.LANCZOS)

		output = io.BytesIO()
		image.save(
			output,
			format=image_format,
			optimize=optimize,
			quality=quality,
			save_all=True if image_format == "gif" else None,
		)
		optimized_content = output.getvalue()
		return optimized_content if len(optimized_content) < len(content) else content
	except Exception as e:
		frappe.msgprint(frappe._("Failed to optimize image: {0}").format(str(e)))
		return content

def optimize_image_rouder(**args):
	if args.get("docntype") == "Item":
		custom_optimize_image(args)
	else:
		optimize_image_original(args)
