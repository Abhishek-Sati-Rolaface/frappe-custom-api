import frappe
from functools import wraps

def require_permission(doctype, action):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            login_user_roles = frappe.get_roles(frappe.session.user)
            _doctype = "Naming Series" if doctype == "Document Naming Settings" else doctype

            if ("Administrator" not in login_user_roles) and (not frappe.has_permission(doctype=doctype, ptype=action)):
                
                frappe.local.response = frappe._dict({
                    "status_code": 403,
                    "status": "fail",
                    "message": f"You do not have permission to {action} {_doctype}. Please contact your Administrator.",
                })
                frappe.local.response.http_status_code = 403
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator