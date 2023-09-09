import frappe

def set_cookie(self, key, value, expires=None, secure=False, httponly=False, samesite="None"):
    if not secure and hasattr(frappe.local, "request"):
        secure = frappe.local.request.scheme == "https"

    self.cookies[key] = {
        "value": value,
        "expires": expires,
        "secure": secure,
        "httponly": httponly,
        "samesite": samesite,
    }
