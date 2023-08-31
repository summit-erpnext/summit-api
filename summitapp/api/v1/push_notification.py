import frappe
import json
import requests

@frappe.whitelist(allow_guest=True)
def get_notification(**kwargs):
    token = kwargs.get("token")
    existing_tokens = get_existing_tokens(token)
    if token in existing_tokens:
       return {"Token already exist"}
    if token not in existing_tokens:
        create_push_notification_token_doc(token)
        return {"New Token Registered"} 


def create_push_notification_token_doc(token):
    doc = frappe.new_doc("Push Notification Token")
    doc.token = token
    doc.insert()

def get_existing_tokens(token):
    existing_tokens = frappe.get_all("Push Notification Token", filters={"token": token}, fields=['token'])
    return [token_data['token'] for token_data in existing_tokens]

def get_notification_token():
    push_notification_tokens = frappe.get_all(
        "Push Notification Token",
        fields=["token"]
    )
    return [token["token"] for token in push_notification_tokens]

def get_enabled_push_notification_messages():
    push_notification_messages = frappe.get_all(
        "Push Notification Message",
        filters={"enable": 1},
        fields=["name", "body", "title", "image", "icon", "click_action"]
    )
    return push_notification_messages

def get_image_url(image_path):
    return frappe.get_site_path(f"{image_path}")

def send_notification():
    fcm_api = "AAAAYYSGg3s:APA91bFT_gf4aesD3oDQNQz6vS04NegasXlJcuPUdxupW104uTwtEOV3bwUXGGecC4asfyL4Y3NHdZayBzAVfsrOQvDsgpwN4-PI5ypdS1ugp8XFQbu5AK71nPkhDZV_61D3EKRRdLup"
    url = "https://fcm.googleapis.com/fcm/send"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key=" + fcm_api
    }

    registration_ids = get_notification_token()
    enabled_messages = get_enabled_push_notification_messages()

    results = []
    for message in enabled_messages:
        image_url = get_image_url(message["image"])
        icon_url = get_image_url(message["icon"])
        payload = {
            "registration_ids": registration_ids,
            "priority": "high",
            "notification": {
                "body": message["body"],
                "title": message["title"],
                "image": image_url,
                "icon": icon_url,
                "click_action": message["click_action"]
            }
        }
        result = requests.post(url, data=json.dumps(payload), headers=headers)
        results.append(result.json())

    return results

