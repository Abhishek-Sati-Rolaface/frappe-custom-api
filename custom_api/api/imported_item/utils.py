import frappe
from frappe.utils import flt, cint, getdate
from typing import Dict, Any

def validate_import_log_payload(data: Dict[str, Any], is_update=False):
    if not is_update:
        required_fields = ["task_code", "item_sequence", "declaration_no"]
        for field in required_fields:
            if not data.get(field):
                raise frappe.ValidationError(f"'{field}' is required.")

        # Ensure we don't insert duplicate items for the same task
        if frappe.db.exists("Custom Imported Item Logs", {
            "task_code": data.get("task_code"),
            "item_sequence": data.get("item_sequence")
        }):
            raise frappe.ValidationError(
                f"Import Log for Task Code '{data.get('task_code')}' and Item Sequence '{data.get('item_sequence')}' already exists."
            )

    if is_update and data.get("task_code") and data.get("item_sequence"):
        existing = frappe.db.exists("Custom Imported Item Logs", {
            "task_code": data.get("task_code"),
            "item_sequence": data.get("item_sequence")
        })
        if existing and existing != data.get("name"):
            raise frappe.ValidationError(
                f"Import Log for Task Code '{data.get('task_code')}' and Item Sequence '{data.get('item_sequence')}' already exists."
            )

    numeric_fields = [
        "quantity", "package_count", "total_weight", 
        "net_weight", "invoice_amount", "exchange_rate", 
        "base_invoice_amount"
    ]
    for field in numeric_fields:
        if field in data and data.get(field) is not None and flt(data.get(field)) < 0:
            raise frappe.ValidationError(f"'{field}' cannot be negative.")

    if data.get("mapped_erp_item") and not frappe.db.exists("Item", data.get("mapped_erp_item")):
        raise frappe.ValidationError(f"Mapped ERP Item '{data.get('mapped_erp_item')}' does not exist.")


def build_import_log_filters(args: Dict[str, Any]) -> Dict[str, Any]:
    frappe_filters = {}
    if not args:
        return frappe_filters

    # Exact match strings
    exact_match_fields = [
        "declaration_no", "task_code", "status", "status_code", 
        "checker", "mapped_erp_item", "hs_code", "origin_country", 
        "export_country", "currency"
    ]
    for field in exact_match_fields:
        if args.get(field):
            frappe_filters[field] = args[field]

    # Date ranges
    from_date = args.get("fromDate")
    to_date = args.get("toDate")
    if from_date and to_date:
        frappe_filters["declaration_date"] = ["between", [getdate(from_date), getdate(to_date)]]
    elif from_date:
        frappe_filters["declaration_date"] = [">=", getdate(from_date)]
    elif to_date:
        frappe_filters["declaration_date"] = ["<=", getdate(to_date)]

    # Invoice Amount ranges
    min_inv = args.get("minInvoiceAmount")
    max_inv = args.get("maxInvoiceAmount")
    if min_inv and max_inv:
        frappe_filters["invoice_amount"] = ["between", [flt(min_inv), flt(max_inv)]]
    elif min_inv:
        frappe_filters["invoice_amount"] = [">=", flt(min_inv)]
    elif max_inv:
        frappe_filters["invoice_amount"] = ["<=", flt(max_inv)]

    # Base Invoice Amount ranges
    min_base = args.get("minBaseInvoiceAmount")
    max_base = args.get("maxBaseInvoiceAmount")
    if min_base and max_base:
        frappe_filters["base_invoice_amount"] = ["between", [flt(min_base), flt(max_base)]]
    elif min_base:
        frappe_filters["base_invoice_amount"] = [">=", flt(min_base)]
    elif max_base:
        frappe_filters["base_invoice_amount"] = ["<=", flt(max_base)]

    return frappe_filters