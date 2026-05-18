import frappe


def create_email_template_service(data):

    template = frappe.get_doc({
        "doctype": "Email Template",
        "name": data.get("template_name"),
        "subject": data.get("subject"),
        "response": data.get("message"),
    })

    template.insert(ignore_permissions=True)

    return template