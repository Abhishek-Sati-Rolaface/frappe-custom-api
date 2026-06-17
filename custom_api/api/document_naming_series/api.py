import frappe
import json
from custom_hrms.utils.response import send_response, send_response_list
from . import service
from custom_api.permission import require_permission

def parse_api_payload():
    if frappe.request and frappe.request.data:
        try:
            return json.loads(frappe.request.data)
        except json.JSONDecodeError:
            return frappe.local.form_dict
    return frappe.local.form_dict

@frappe.whitelist(allow_guest=False, methods=["POST"])
@require_permission("Document Naming Settings", "create")
def create_naming_series():
    try:
        data = parse_api_payload()
        doctype = data.get("document_type")
        prefix = data.get("prefix")
        starting_number = data.get("starting_number", 0)

        if not doctype or not prefix:
            return send_response(
                status="fail",
                message="document_type and prefix are required.",
                status_code=400,
                http_status=400,
            )

        result = service.add_series_to_doctype(doctype, prefix, starting_number)
        frappe.db.commit()

        return send_response(
            status="success",
            message="Naming series configured successfully.",
            data=result,
            status_code=201,
            http_status=201,
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Create Native Naming Series API Error")
        return send_response(status="error", message=str(e), status_code=500, http_status=500)

@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_naming_series():
    try:
        doctype = frappe.request.args.get("document_type")
        
        if doctype:
            data = service.get_series_for_doctype(doctype)
            msg = f"Naming series retrieved for {doctype}."
        else:
            data = service.get_all_active_series()
            msg = "All naming series retrieved successfully."

        return send_response_list(
            status="success",
            message=msg,
            data=data,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Native Naming Series Error")
        return send_response(status="error", message=str(e), status_code=500, http_status=500)

@frappe.whitelist(allow_guest=False, methods=["PUT", "PATCH"])
@require_permission("Document Naming Settings", "write")
def update_naming_series():
    try:
        data = parse_api_payload()
        prefix = data.get("prefix") or frappe.request.args.get("prefix")
        new_current = data.get("current_value")

        if not prefix or new_current is None:
            return send_response(
                status="fail",
                message="prefix and current_value are required.",
                status_code=400,
                http_status=400,
            )

        result = service.update_series_counter(prefix, new_current)
        frappe.db.commit()

        return send_response(
            status="success",
            message="Naming series counter updated successfully.",
            data=result,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Native Naming Series Error")
        return send_response(status="error", message=str(e), status_code=500, http_status=500)

@frappe.whitelist(allow_guest=False, methods=["DELETE"])
@require_permission("Document Naming Settings", "delete")
def delete_naming_series():
    try:
        doctype = frappe.local.form_dict.get("document_type")
        prefix = frappe.local.form_dict.get("prefix")
        
        if not doctype or not prefix:
            return send_response(
                status="fail",
                message="Both document_type and prefix are required for deletion.",
                status_code=400,
                http_status=400,
            )

        service.remove_series_from_doctype(doctype, prefix)
        frappe.db.commit()

        return send_response(
            status="success",
            message=f"Prefix '{prefix}' removed from {doctype} options.",
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Delete Native Naming Series Error")
        return send_response(status="error", message=str(e), status_code=500, http_status=500)
    
@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_company_naming_settings():
    try:
        data = service.get_bulk_naming_settings()

        return send_response(
            status="success",
            message="Company naming series settings retrieved successfully.",
            data=data,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Bulk Naming Settings Error")
        return send_response(status="error", message=str(e), status_code=500, http_status=500)


@frappe.whitelist(allow_guest=False, methods=["POST", "PUT", "PATCH"])
@require_permission("Document Naming Settings", "create")
def update_company_naming_settings():
    try:
        data = parse_api_payload()
        
        if not data:
            return send_response(
                status="fail",
                message="No configuration payload provided.",
                status_code=400,
                http_status=400,
            )

        updated_settings, skipped = service.update_bulk_naming_settings(data)
        frappe.db.commit()

        if skipped:
            msg = "Update partially successful. Some fields were skipped because they are in use."
            status_val = "partial_success"
        else:
            msg = "Company naming series configured successfully."
            status_val = "success"

        return send_response(
            status=status_val,
            message=msg,
            data={
                "settings": updated_settings,
                "warnings": skipped
            },
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Bulk Naming Settings Error")
        return send_response(status="error", message=str(e), status_code=500, http_status=500)