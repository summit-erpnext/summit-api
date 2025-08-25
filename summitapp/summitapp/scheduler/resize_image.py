import frappe
from frappe.utils import get_url, now
import requests
from PIL import Image
import io
import os
import time


def resize_image():
    BATCH_SIZE = 50
    TIMEOUT_SECONDS = 295

    try:
        start_time = time.time()
        while True:
            item_images_list = frappe.db.get_all(
                "Item Images",
                filters={
                    "small_size_image": "",
                    "large_size_image": "",
                    "image_unavailable": 0,
                },
                fields=["name", "upload_image"],
                limit=BATCH_SIZE,
            )

            if not item_images_list:
                break

            for image in item_images_list:
                if time.time() - start_time > TIMEOUT_SECONDS:
                    return
                try:
                    process_single_image(image)
                except Exception as e:
                    continue

    except Exception as e:
        frappe.log_error("Error resizing images", f"Error: {str(e)}")


def process_single_image(image):
    url = get_url()  # Uncomment this in production
    # url = "http://127.0.0.1:8000"  # Development URL
    url = url + image.upload_image
    response = requests.get(url, timeout=5, stream=True)

    if response.status_code != 200:
        frappe.db.set_value("Item Images", image.name, "image_unavailable", 1)
        return

    response.raw.decode_content = True

    with Image.open(response.raw) as img:
        if img.mode in ("RGBA", "LA"):
            rgb_img = img
        elif img.mode != "RGB":
            rgb_img = img.convert("RGB")
        else:
            rgb_img = img

        def save_resized_webp_image(size, prefix, resize=True):
            if resize:
                resized_img = rgb_img.resize((size, size))
            else:
                resized_img = rgb_img  # keep original resolution
            with io.BytesIO() as temp:
                resized_img.save(temp, format="WEBP", quality=90)
                file_name = f"{prefix}-{os.path.splitext(os.path.basename(image.upload_image))[0]}.webp"
                file_doc = frappe.get_doc(
                    {
                        "doctype": "File",
                        "file_name": file_name,
                        "content": temp.getvalue(),
                    }
                )
                file_doc.save()
                return file_doc.file_url

        small_image_url = save_resized_webp_image(600, "small", resize=True)
        large_image_url = save_resized_webp_image(None, "large", resize=False)

        frappe.db.set_value(
            "Item Images",
            image.name,
            {
                "small_size_image": small_image_url,
                "large_size_image": large_image_url,
                "created_on": now(),
            },
        )
