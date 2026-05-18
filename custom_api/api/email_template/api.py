from custom_api.api.email_template.service import create_email_template_service
import frappe
from frappe.email.doctype.email_template.email_template import get_email_template
from custom_api.utils.response import send_old_response, send_response_list
from frappe.exceptions import DuplicateEntryError

@frappe.whitelist(allow_guest=False, methods=["POST"])
def get_by_id(**payload):
        try:
            template_id = payload.get("id")
            doc_type = payload.get("doc_type")
            doc_type_name = payload.get("doc_type_name")
            get_full_doc = frappe.get_doc(doc_type, doc_type_name)
            response = get_email_template(template_id, get_full_doc.as_dict())
            return send_old_response(
                    status="success",
                    message=response,
                    status_code=200,
                    http_status=200
                )
        except Exception as e:
            frappe.log_error(str(e), "get email template by id API error")

            return send_old_response(
                                        status="fail",
                                        message=str(e),
                                        status_code=500,
                                        http_status=500
                                    )

@frappe.whitelist(allow_guest=False, methods=["POST"])
def create():
    try:
        data = frappe.local.form_dict
        create_email_template_service(data)
        return send_old_response(
                                    status="success",
                                    message="Email Template created successfully",
                                    status_code=200,
                                    http_status=200
                                )
    except DuplicateEntryError as e:
        return send_old_response(
                                    status="fail",
                                    message="You Can only have one template for each Type. Please update the existing template if you want to make changes.",
                                    status_code=409,
                                    http_status=409
                                )
    except Exception as e:
        frappe.log_error(str(e), "get email template API error")

        return send_old_response(
                                    status="fail",
                                    message=str(e),
                                    status_code=500,
                                    http_status=500
                                )

@frappe.whitelist(allow_guest=False, methods=["PUT"])
def update():
    try:
        data = frappe.local.form_dict

        template_name = data.get("id")

        if not template_name:
            return send_old_response(
                status="fail",
                message="template_name is required.",
                status_code=400,
                http_status=400,
            )

        if not frappe.db.exists("Email Template", template_name):
            return send_old_response(
                status="fail",
                message=f"Email Template '{template_name}' not found.",
                status_code=404,
                http_status=404,
            )

        template = frappe.get_doc("Email Template", template_name)

        if data.get("subject"):
            template.subject = data.get("subject")

        if data.get("message"):
            template.response = data.get("message")

        template.save(ignore_permissions=True)

        return send_old_response(
            status="success",
            message="Email Template updated successfully.",
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Email Template API Error")

        return send_old_response(
            status="fail",
            message=str(e),
            status_code=500,
            http_status=500,
        )