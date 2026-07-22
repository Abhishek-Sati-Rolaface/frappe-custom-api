from custom_api.permission import require_permission
import frappe
from custom_api.utils.response import send_response, send_response_list
from .utils import validate_quotation_payload
from ....utils.party_utils import parse_api_payload
from . import service
from erpnext.selling.doctype.quotation.quotation import make_sales_invoice
from erpnext.selling.doctype.quotation.quotation import make_sales_invoice, make_sales_order
from custom_api.api.selling.sales_invoice.utils import validate_receivable_account_for_currency
from .utils import validate_quotation_payload, get_naming_series_for_quotation

@frappe.whitelist(allow_guest=False, methods=["POST"])
@require_permission("Quotation", "create")
def create_quotation():
    try:
        data = parse_api_payload()
        validate_quotation_payload(data)
        documentType = data.get("documentType")

        quotation = service.create_quotation(data)
        frappe.db.commit()
        return send_response(
            status="success",
            message=f"{documentType or 'Quotation'} created successfully.",
            data={"id": quotation.name},
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
            frappe.get_traceback(), f"Create {documentType or 'Quotation'} API Error"
        )
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["PUT", "PATCH"])
@require_permission("Quotation", "write")
def update_quotation(id=None, **kwargs):
    try:
        data = parse_api_payload()
        quotation_id = id or frappe.request.args.get("id")
        documentType = data.get("documentType")

        if not quotation_id:
            return send_response(
                status="fail",
                message="id is required as query parameter (?id=...)",
                status_code=400,
                http_status=400,
            )

        if not frappe.db.exists("Quotation", quotation_id):
            return send_response(
                status="fail",
                message="Quotation not found",
                status_code=404,
                http_status=404,
            )

        validate_quotation_payload(data, is_update=True)
        service.update_quotation(quotation_id, data)

        frappe.db.commit()

        return send_response(
            status="success",
            message=f"{documentType or 'Quotation'} updated successfully",
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
            frappe.get_traceback(), f"Update {documentType or 'Quotation'} API Error"
        )
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["GET"])
@require_permission("Quotation", "read")
def get_quotation_by_id(id):
    try:
        if not frappe.db.exists("Quotation", id):
            return send_response(
                status="fail",
                message="Quotation not found",
                status_code=404,
                http_status=404,
            )

        data = service.get_quotation_by_id(id)
        documentType = data.get("documentType")

        return send_response(
            status="success",
            message=f"{documentType or 'Quotation'} retrieved successfully",
            status_code=200,
            data=data,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(), f"Get {documentType or 'Quotation'} By ID Error"
        )
        return send_response(
            status="error",
            message=f"Failed to retrieve {documentType or 'Quotation'}: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["GET"])
@require_permission("Quotation", "read")
def get_quotations(page=1, page_size=20):
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

        quotations, total_quotations, total_pages = service.get_quotations(
            data,
            page,
            page_size,
            search,
        )

        documentType = data.get("documentType")

        response_data = {
            "success": True,
            "message": f"{documentType or 'Quotation'} retrieved successfully",
            "data": quotations,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_quotations,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

        return send_response_list(
            status="success",
            message=f"{documentType or 'Quotation'} retrieved successfully",
            status_code=200,
            data=response_data,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(), f"Get All {documentType or 'Quotation'} Error"
        )
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["DELETE"])
@require_permission("Quotation", "delete")
def delete_quotation(id=None):
    try:
        quotation_id = id or frappe.local.form_dict.get("id")

        if not quotation_id:
            return send_response(
                status="fail",
                message="id is required as query parameter (?id=...)",
                status_code=400,
                http_status=400,
            )

        if not frappe.db.exists("Quotation", quotation_id):
            return send_response(
                status="fail",
                message="Quotation not found",
                status_code=404,
                http_status=404,
            )

        service.delete_quotation(quotation_id)

        frappe.db.commit()

        return send_response(
            status="success",
            message="Quotation deleted successfully",
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
        frappe.log_error(frappe.get_traceback(), "Delete Quotation Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )


@frappe.whitelist(allow_guest=False, methods=["PUT", "PATCH"])
def update_quotation_status(id=None, action=None):
    try:
        data = parse_api_payload() or {}

        quotation_id = id or frappe.request.args.get("id") or data.get("id")
        raw_action = action or frappe.request.args.get("action") or data.get("action")
        documentType = data.get("documentType")

        if not quotation_id:
            return send_response(
                status="fail",
                message="id is required as query parameter (?id=...)",
                status_code=400,
                http_status=400,
            )

        if not raw_action:
            return send_response(
                status="fail",
                message="Action is required (approved, cancelled, amend, lost)",
                status_code=400,
                http_status=400,
            )

        action = str(raw_action).strip().lower()

        if action not in {"approved", "cancelled", "amend", "lost"}:
            return send_response(
                status="fail",
                message=f"Invalid action '{raw_action}'. Allowed values: approved, cancelled, amend, lost",
                status_code=400,
                http_status=400,
            )

        if not frappe.db.exists("Quotation", quotation_id):
            return send_response(
                status="fail",
                message=f"Quotation '{quotation_id}' not found",
                status_code=404,
                http_status=404,
            )

        result = service.update_quotation_status(
            quotation_id,
            action,
            data,
        )

        frappe.db.commit()

        action_map = {
            "approved": "approved",
            "cancelled": "cancelled",
            "amend": "amended",
            "lost": "marked as lost",
        }

        return send_response(
            status="success",
            message=f"{documentType or 'Quotation'} {action_map[action]} successfully.",
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
            message=f"You do not have permission to update the status of this {documentType or 'Quotation'}. Please contact your Administrator.",
            status_code=403,
            http_status=403,
        )

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(),
            f"Update {documentType or 'Quotation'} Status API Error",
        )
        return send_response(
            status="error",
            message="Internal Server Error",
            status_code=500,
            http_status=500,
        )

@frappe.whitelist(allow_guest=False, methods=["POST"])
@require_permission("Sales Invoice", "create")
def create_si_from_quotation():
    quotation_id = frappe.request.args.get("quotation_id") or frappe.request.args.get("id")

    if not quotation_id:
        return send_response(
            status="fail",
            message="quotation_id is required as query parameter (?quotation_id=...)",
            status_code=400,
            http_status=400,
        )

    if not frappe.db.exists("Quotation", quotation_id):
        return send_response(
            status="fail",
            message="Quotation not found",
            status_code=404,
            http_status=404,
        )

    try:
        default_payment_mode = None
        company_name = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company_name)
        if company_doc.custom_extended_details:
            extended_details = company_doc.custom_extended_details[0]
            if extended_details.default_payment_mode:
                default_payment_mode = extended_details.default_payment_mode

        si_doc = make_sales_invoice(quotation_id)
        si_doc.debit_to = validate_receivable_account_for_currency(si_doc.currency)
        si_doc.docstatus = 0
        if default_payment_mode:
            si_doc.append("custom_details", {"payment_mode": default_payment_mode})
        si_doc.insert(ignore_permissions=True)

        frappe.db.commit()

        return send_response(
            status="success",
            message="Sales Invoice created successfully from Quotation",
            data={"id": si_doc.name},
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
        frappe.log_error(frappe.get_traceback(), "Create SI from Quotation API Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )

@frappe.whitelist(allow_guest=False, methods=["POST"])
@require_permission("Sales Order", "create")
def create_so_from_quotation():
    quotation_id = frappe.request.args.get("quotation_id") or frappe.request.args.get("id")

    if not quotation_id:
        return send_response(
            status="fail",
            message="quotation_id is required as query parameter (?quotation_id=...)",
            status_code=400,
            http_status=400,
        )

    if not frappe.db.exists("Quotation", quotation_id):
        return send_response(
            status="fail",
            message="Quotation not found",
            status_code=404,
            http_status=404,
        )

    try:
        # so_doc = make_sales_order(quotation_id)
        # so_doc.docstatus = 0
        # so_doc.insert(ignore_permissions=True)
        so_doc = make_sales_order(quotation_id)

        quotation_valid_till = frappe.db.get_value("Quotation", quotation_id, "valid_till")
        fallback_delivery_date = quotation_valid_till or frappe.utils.nowdate()

        for item in so_doc.items:
            if not item.delivery_date:
                item.delivery_date = fallback_delivery_date

        so_doc.docstatus = 0
        so_doc.insert(ignore_permissions=True)

        frappe.db.commit()

        return send_response(
            status="success",
            message="Sales Order created successfully from Quotation",
            data={"id": so_doc.name},
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
        frappe.log_error(frappe.get_traceback(), "Create SO from Quotation API Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )
    
@frappe.whitelist(allow_guest=False, methods=["POST"])
@require_permission("Quotation", "create")
def create_proforma_from_quotation():
    quotation_id = frappe.request.args.get("quotation_id") or frappe.request.args.get("id")

    if not quotation_id:
        return send_response(
            status="fail",
            message="quotation_id is required as query parameter (?quotation_id=...)",
            status_code=400,
            http_status=400,
        )

    if not frappe.db.exists("Quotation", quotation_id):
        return send_response(
            status="fail",
            message="Quotation not found",
            status_code=404,
            http_status=404,
        )

    try:
        source = frappe.get_doc("Quotation", quotation_id)

        proforma_doc = frappe.copy_doc(source)
        proforma_doc.docstatus = 0
        proforma_doc.amended_from = None
        proforma_doc.naming_series = get_naming_series_for_quotation("Proforma Invoice")
        proforma_doc.set("custom_extended_details", [])
        proforma_doc.append("custom_extended_details", {
            "document_type": "Proforma Invoice",
        })
        proforma_doc.insert(ignore_permissions=True)

        frappe.db.commit()

        return send_response(
            status="success",
            message="Proforma Invoice created successfully from Quotation",
            data={"id": proforma_doc.name},
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
        frappe.log_error(frappe.get_traceback(), "Create Proforma from Quotation API Error")
        return send_response(
            status="error",
            message=f"Internal Server Error: {str(e)}",
            status_code=500,
            http_status=500,
        )