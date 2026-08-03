import frappe
from custom_api.permission import require_permission
from custom_api.utils.response import send_response, send_response_list
from custom_api.utils.party_utils import parse_api_payload
from . import service

@frappe.whitelist(allow_guest=False, methods=["POST"])
def create_import_log():
    try:
        data = parse_api_payload()
        log_data = service.create_import_log(data)
        frappe.db.commit()

        return send_response(
            status="success",
            message="Import Log created successfully.",
            data={"id": log_data.get("name")},
            status_code=201,
            http_status=201,
        )

    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()
        return send_response(
            status="fail", message=str(e), status_code=400, http_status=400
        )
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Create Import Log API Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["PUT", "PATCH"])
def update_import_log(id=None, **kwargs):
    try:
        data = parse_api_payload()
        log_id = id or frappe.request.args.get("id")

        if not log_id:
            return send_response(
                status="fail",
                message="Log ID required as query parameter (?id=...)",
                status_code=400,
                http_status=400,
            )

        log_data = service.update_import_log(log_id, data)
        frappe.db.commit()

        return send_response(
            status="success",
            message="Import Log updated successfully",
            data=log_data,
            status_code=200,
            http_status=200,
        )

    except frappe.DoesNotExistError as e:
        frappe.db.rollback()
        return send_response(
            status="fail", message=str(e), status_code=404, http_status=404
        )
    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()
        return send_response(
            status="fail", message=str(e), status_code=400, http_status=400
        )
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Update Import Log API Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_import_log_by_id(id=None):
    try:
        log_id = id or frappe.request.args.get("id")
        if not log_id:
            return send_response(
                status="fail",
                message="Log ID required",
                status_code=400,
                http_status=400,
            )

        data = service.get_import_log_by_id(log_id)
        return send_response(
            status="success",
            message="Import Log retrieved successfully",
            status_code=200,
            data=data,
            http_status=200,
        )

    except frappe.DoesNotExistError as e:
        return send_response(
            status="fail", message=str(e), status_code=404, http_status=404
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Import Log By ID Error")
        return send_response(
            status="error",
            message=f"Failed to retrieve Import Log: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_import_logs(page=1, page_size=10):
    data = frappe.local.form_dict
    
    try:
        try:
            page, page_size = int(page), int(page_size)
            if page < 1 or page_size < 1:
                raise ValueError
        except ValueError:
            return send_response(
                status="fail",
                message="Page constraints must be positive integers.",
                status_code=400,
                http_status=400,
            )

        sort_by = data.get("sort_by", "creation")
        sort_order = data.get("sort_order", "desc")

        logs, total_records, total_pages = service.get_import_logs(
            data, page, page_size, sort_by, sort_order
        )

        response_data = {
            "success": True,
            "message": "Import Logs retrieved successfully",
            "data": logs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

        return send_response_list(
            status="success",
            message="Import Logs retrieved successfully",
            status_code=200,
            data=response_data,
            http_status=200,
        )

    except frappe.exceptions.ValidationError as e:
        return send_response(
            status="fail", message=str(e), status_code=400, http_status=400
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get All Import Logs Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["DELETE"])
def delete_import_log(id=None):
    try:
        log_id = id or frappe.local.form_dict.get("id")
        if not log_id:
            return send_response(
                status="fail",
                message="Log ID required",
                status_code=400,
                http_status=400,
            )

        service.delete_import_log(log_id)
        frappe.db.commit()

        return send_response(
            status="success",
            message="Import Log deleted successfully",
            status_code=200,
            http_status=200,
        )

    except frappe.DoesNotExistError as e:
        frappe.db.rollback()
        return send_response(
            status="fail", message=str(e), status_code=404, http_status=404
        )
    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()
        return send_response(
            status="fail", message=str(e), status_code=400, http_status=400
        )
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Delete Import Log Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )