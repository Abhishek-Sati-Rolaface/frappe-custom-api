import frappe
from typing import Tuple, Dict, Any
from .utils import build_import_log_filters, validate_import_log_payload
from .constant import ALLOWED_IMPORT_LOG_FIELDS, RETURN_FIELDS_GET_ALL, RETURN_FIELDS_GET_BY_ID, ALLOWED_SORT_FIELDS

def create_import_log(data: Dict[str, Any]) -> Dict[str, Any]:
    validate_import_log_payload(data, is_update=False)

    doc = frappe.new_doc("Custom Imported Item Logs")
    
    for field in ALLOWED_IMPORT_LOG_FIELDS:
        if field in data and data.get(field) is not None:
            doc.set(field, data.get(field))
            
    doc.insert(ignore_permissions=True)
    return get_import_log_by_id(doc.name)


def update_import_log(log_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not frappe.db.exists("Custom Imported Item Logs", log_id):
        raise frappe.DoesNotExistError(f"Import Log '{log_id}' does not exist.")

    doc = frappe.get_doc("Custom Imported Item Logs", log_id)
    
    if doc.docstatus == 1:
        raise frappe.ValidationError(f"Cannot update submitted Import Log '{log_id}'.")

    # Inject name for validation checks
    data["name"] = log_id
    validate_import_log_payload(data, is_update=True)
    
    has_changes = False

    for field in ALLOWED_IMPORT_LOG_FIELDS:
        if field in data and data.get(field) is not None:
            if doc.get(field) != data.get(field):
                doc.set(field, data.get(field))
                has_changes = True

    if has_changes:
        doc.save(ignore_permissions=True)

    return get_import_log_by_id(doc.name)


def get_import_log_by_id(log_id: str) -> Dict[str, Any]:
    if not frappe.db.exists("Custom Imported Item Logs", log_id):
        raise frappe.DoesNotExistError(f"Import Log '{log_id}' does not exist.")
        
    doc = frappe.get_doc("Custom Imported Item Logs", log_id)
    result = {field: doc.get(field) for field in RETURN_FIELDS_GET_BY_ID}
    
    return result


def get_import_logs(args: Dict[str, Any], page: int, page_size: int, sort_by="creation", sort_order="desc") -> Tuple[list, int, int]:
    start = (page - 1) * page_size
    or_filters = []
    
    search = args.get("search")
    if search:
        search_term = f"%{str(search).strip()}%"
        or_filters = [
            ["name", "like", search_term],
            ["task_code", "like", search_term],
            ["declaration_no", "like", search_term],
            ["item_name", "like", search_term],
            ["mapped_erp_item", "like", search_term]
        ]

    safe_filters = build_import_log_filters(args)

    if sort_by not in ALLOWED_SORT_FIELDS:
        raise frappe.ValidationError(f"Invalid sort_by field: {sort_by}")

    sort_order_clean = str(sort_order).lower()
    if sort_order_clean not in ["asc", "desc"]:
        raise frappe.ValidationError("Invalid sort_order value. Use 'asc' or 'desc'.")

    order_by_string = f"`tabCustom Imported Item Logs`.`{sort_by}` {sort_order_clean}"

    logs = frappe.get_all(
        "Custom Imported Item Logs",
        filters=safe_filters,
        or_filters=or_filters if search else None,
        fields=RETURN_FIELDS_GET_ALL,
        limit_start=start,
        limit_page_length=page_size,
        order_by=order_by_string,
    )

    total_logs = len(
        frappe.get_all(
            "Custom Imported Item Logs",
            filters=safe_filters,
            or_filters=or_filters if search else None,
            pluck="name",
        )
    )

    total_pages = (total_logs + page_size - 1) // page_size

    return logs, total_logs, total_pages


def delete_import_log(log_id: str):
    if not frappe.db.exists("Custom Imported Item Logs", log_id):
        raise frappe.DoesNotExistError(f"Import Log '{log_id}' does not exist.")
        
    docstatus = frappe.db.get_value("Custom Imported Item Logs", log_id, "docstatus")
    if docstatus == 1:
        raise frappe.ValidationError(f"Cannot delete a submitted Import Log '{log_id}'. Cancel it first.")

    frappe.delete_doc("Custom Imported Item Logs", log_id, ignore_permissions=True)