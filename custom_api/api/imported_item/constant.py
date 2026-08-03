ALLOWED_IMPORT_LOG_FIELDS = {
    "task_code", "declaration_no", "declaration_date", "item_sequence",
    "hs_code", "item_name", "origin_country", "export_country",
    "quantity", "quantity_unit", "package_count", "package_unit",
    "total_weight", "net_weight", "invoice_amount", "currency",
    "exchange_rate", "base_invoice_amount", "supplier_name",
    "agent_name", "status", "status_code", "mapped_erp_item",
    "remarks", "checker", "checked_at"
}

ALLOWED_SORT_FIELDS = {
    "name", "creation", "modified", "task_code", "declaration_no", 
    "declaration_date", "item_sequence", "quantity", 
    "invoice_amount", "base_invoice_amount", "status"
}

RETURN_FIELDS_GET_ALL = [
    "name", "task_code", "declaration_no", "declaration_date",
    "item_sequence", "item_name", "quantity", "invoice_amount",
    "base_invoice_amount", "status", "mapped_erp_item"
]

RETURN_FIELDS_GET_BY_ID = list(ALLOWED_IMPORT_LOG_FIELDS) + [
    "name", "creation", "modified", "docstatus"
]