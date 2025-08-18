import frappe
from summitapp.summitapp.customizations.notification.utils import get_notifications

# Get Push Notifications
@frappe.whitelist(allow_guest=True)
def get_notification(**kwargs):
    return get_notifications(**kwargs)