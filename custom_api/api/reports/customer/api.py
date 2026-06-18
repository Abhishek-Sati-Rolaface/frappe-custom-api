import frappe
import json
from frappe import _
from frappe.utils.pdf import get_pdf
from custom_api.templates.customer_statement_pdf import customer_statement_pdf_html_template

from custom_api.permission import require_permission
from custom_api.utils.response import send_response

from .service import get_customer_statement_data

@frappe.whitelist(allow_guest=False, methods=["GET"])
@require_permission("Customer", "report")
def get_customer_statement():
    customer_id = frappe.form_dict.get("id")
    from_date = frappe.form_dict.get("from_date")
    to_date = frappe.form_dict.get("to_date")
    page = int(frappe.form_dict.get("page", 1))
    page_size = int(frappe.form_dict.get("page_size", 10))
    search_term = frappe.form_dict.get("search_term")
    
    voucher_type = frappe.form_dict.get("voucher_type")
    if voucher_type and isinstance(voucher_type, str) and voucher_type.startswith("["):
        try:
            voucher_type = json.loads(voucher_type)
        except json.JSONDecodeError:
            pass

    if not customer_id:
        return send_response(
            status="fail",
            message="Customer id must not be null",
            data={},
            status_code=400,
            http_status=400
        )

    if not frappe.db.exists("Customer", customer_id):
        return send_response(
            status="fail",
            message=f"Customer with id {customer_id} not found.",
            data={},
            status_code=404,
            http_status=404
        )

    statement = get_customer_statement_data(
        customer_id=customer_id, 
        from_date=from_date, 
        to_date=to_date, 
        page=page, 
        page_size=page_size,
        voucher_type=voucher_type,
        search_term=search_term
    )

    return send_response(
        status="success",
        message="Customer statement retrieved successfully",
        data=statement,
        status_code=200,
        http_status=200
    )


@frappe.whitelist(allow_guest=False, methods=["GET"])
@require_permission("Customer", "report")
def generate_customer_statement_pdf():
    customer_id = frappe.form_dict.get("id")
    from_date = frappe.form_dict.get("from_date")
    to_date = frappe.form_dict.get("to_date")
    search_term = frappe.form_dict.get("search_term")
    
    voucher_type = frappe.form_dict.get("voucher_type")
    if voucher_type and isinstance(voucher_type, str) and voucher_type.startswith("["):
        try:
            voucher_type = json.loads(voucher_type)
        except json.JSONDecodeError:
            pass

    if not customer_id:
        frappe.throw(_("Customer id must not be null"))

    customer = frappe.db.get_value(
        "Customer",
        customer_id,
        ["name", "customer_name", "creation", "tax_id", "primary_address", "email_id", "mobile_no", "creation"],
        as_dict=True
    )

    if not customer:
        frappe.throw(_(f"Customer {customer_id} not found"))

    statement_data = get_customer_statement_data(
        customer_id=customer_id, 
        from_date=from_date, 
        to_date=to_date,
        voucher_type=voucher_type,
        search_term=search_term
    )

    html_template = customer_statement_pdf_html_template()
    html = frappe.render_template(html_template, {
        "customer": customer,
        "from_date": from_date,
        "to_date": to_date,
        "summary": statement_data.get("summary"),
        "ledger": statement_data.get("ledger"),
        "frappe": frappe
    })

    pdf_options = {
        "page-size": "A4",
        "margin-top": "15mm",
        "margin-right": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "15mm",
        "encoding": "UTF-8",
        "no-outline": None
    }

    pdf = get_pdf(html, options=pdf_options)

    frappe.local.response.filename = f"Customer_Statement_{customer.customer_name}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"