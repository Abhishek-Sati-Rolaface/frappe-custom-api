from custom_api.permission import require_permission
import frappe
from custom_api.utils.response import send_response, send_response_list
from .utils import validate_sales_order_payload
from ....utils.party_utils import parse_api_payload
from . import service


@frappe.whitelist(allow_guest=False, methods=["POST"])
@require_permission("Sales Order", "create")
def create_sales_order():
    try:
        data = parse_api_payload()
        validate_sales_order_payload(data)

        sales_order = service.create_sales_order(data)
        frappe.db.commit()
        return send_response(
            status="success",
            message="Sales Order created successfully.",
            data={"id": sales_order.name},
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
        frappe.log_error(
            frappe.get_traceback(), "Create Sales Order API Error"
        )
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["PUT", "PATCH"])
@require_permission("Sales Order", "write")
def update_sales_order(id=None, **kwargs):
    try:
        data = parse_api_payload()
        sales_order_id = id or frappe.request.args.get("id")

        if not sales_order_id:
            return send_response(
                status="fail",
                message="id is required as query parameter (?id=...)",
                status_code=400,
                http_status=400,
            )

        if not frappe.db.exists("Sales Order", sales_order_id):
            return send_response(
                status="fail",
                message="Sales Order not found",
                status_code=404,
                http_status=404,
            )

        validate_sales_order_payload(data, is_update=True)
        service.update_sales_order(sales_order_id, data)

        frappe.db.commit()

        return send_response(
            status="success",
            message="Sales Order updated successfully",
            status_code=200,
            http_status=200,
        )

    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()
        return send_response(
            status="fail", message=str(e), status_code=400, http_status=400
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(), "Update Sales Order API Error"
        )
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["GET"])
@require_permission("Sales Order", "read")
def get_sales_order_by_id(id):
    try:
        if not frappe.db.exists("Sales Order", id):
            return send_response(
                status="fail",
                message="Sales Order not found",
                status_code=404,
                http_status=404,
            )

        data = service.get_sales_order_by_id(id)

        return send_response(
            status="success",
            message="Sales Order retrieved successfully",
            status_code=200,
            data=data,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(), "Get Sales Order By ID Error"
        )
        return send_response(
            status="error",
            message=f"Failed to retrieve Sales Order: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["GET"])
@require_permission("Sales Order", "read")
def get_sales_orders(page=1, page_size=20):
    data = frappe.local.form_dict
    search = data.get("search")

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

        sales_orders, total_sales_orders, total_pages = service.get_sales_orders(
            data,
            page,
            page_size,
            search,
        )

        response_data = {
            "success": True,
            "message": "Sales Order retrieved successfully",
            "data": sales_orders,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_sales_orders,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

        return send_response_list(
            status="success",
            message="Sales Order retrieved successfully",
            status_code=200,
            data=response_data,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(), "Get All Sales Order Error"
        )
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["DELETE"])
@require_permission("Sales Order", "delete")
def delete_sales_order(id=None):
    try:
        sales_order_id = id or frappe.local.form_dict.get("id")

        if not sales_order_id:
            return send_response(
                status="fail",
                message="id is required as query parameter (?id=...)",
                status_code=400,
                http_status=400,
            )

        if not frappe.db.exists("Sales Order", sales_order_id):
            return send_response(
                status="fail",
                message="Sales Order not found",
                status_code=404,
                http_status=404,
            )

        service.delete_sales_order(sales_order_id)

        frappe.db.commit()

        return send_response(
            status="success",
            message="Sales Order deleted successfully",
            status_code=200,
            http_status=200,
        )

    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()
        return send_response(
            status="fail",
            message=str(e),
            status_code=400,
            http_status=400,
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Delete Sales Order Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["PUT", "PATCH"])
def update_sales_order_status(id=None, action=None):
    try:
        data = parse_api_payload() or {}

        sales_order_id = id or frappe.request.args.get("id") or data.get("id")
        raw_action = action or frappe.request.args.get("action") or data.get("action")

        if not sales_order_id:
            return send_response(
                status="fail",
                message="id is required as query parameter (?id=...)",
                status_code=400,
                http_status=400,
            )

        if not raw_action:
            return send_response(
                status="fail",
                message="Action is required (approved, cancelled, amend, closed, reopened)",
                status_code=400,
                http_status=400,
            )

        action = str(raw_action).strip().lower()

        if action not in {"approved", "cancelled", "amend", "closed", "reopened"}:
            return send_response(
                status="fail",
                message=f"Invalid action '{raw_action}'. Allowed values: approved, cancelled, amend, closed, reopened",
                status_code=400,
                http_status=400,
            )

        if not frappe.db.exists("Sales Order", sales_order_id):
            return send_response(
                status="fail",
                message=f"Sales Order '{sales_order_id}' not found",
                status_code=404,
                http_status=404,
            )

        result = service.update_sales_order_status(
            sales_order_id,
            action,
            data,
        )

        frappe.db.commit()

        action_map = {
            "approved": "approved",
            "cancelled": "cancelled",
            "amend": "amended",
            "closed": "closed",
            "reopened": "reopened",
        }

        return send_response(
            status="success",
            message=f"Sales Order {action_map[action]} successfully.",
            data=result,
            status_code=200,
            http_status=200,
        )

    except frappe.exceptions.ValidationError as e:
        frappe.db.rollback()
        return send_response(
            status="fail",
            message=str(e),
            status_code=400,
            http_status=400,
        )

    except frappe.exceptions.PermissionError:
        frappe.db.rollback()
        return send_response(
            status="fail",
            message="You do not have permission to update the status of this Sales Order. Please contact your Administrator.",
            status_code=403,
            http_status=403,
        )

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(),
            "Update Sales Order Status API Error",
        )
        return send_response(
            status="error",
            message="Internal Server Error",
            status_code=500,
            http_status=500,
        )