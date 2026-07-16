import frappe
def before_validate(doc,method):
    data = frappe.local.form_dict
    if data.get("reason"):
        if not doc.custom_details:
            doc.append("custom_details", {"reason": data.get("reason")})
        else:
            doc.custom_details[0].reason = data.get("reason")