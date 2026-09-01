import frappe
from frappe.utils import cint
from .utils import build_classification_filters, trigger_zra_select_items_class


def create_classification(data: dict):
    doc = frappe.new_doc("Custom Item Classification")
    doc.update({
        "class_code": data.get("class_code"),
        "class_name": data.get("class_name"),
        "class_level": cint(data.get("class_level") or 0),
        "is_active": 1 if data.get("is_active") in [1, True, "1", "true"] else 0,
    })

    doc.insert(ignore_permissions=True)
    return doc


def update_classification(classification_id: str, data: dict):
    doc = frappe.get_doc("Custom Item Classification", classification_id)

    field_map = {
        "class_code": "class_code",
        "class_name": "class_name",
        "class_level": "class_level",
    }

    for k, v in field_map.items():
        if data.get(k) is not None:
            if k == "class_level":
                setattr(doc, v, cint(data.get(k)))
            else:
                setattr(doc, v, data.get(k))

    if data.get("is_active") is not None:
        doc.is_active = 1 if data.get("is_active") in [1, True, "1", "true"] else 0

    doc.save(ignore_permissions=True)
    return doc


def get_classification_by_id(classification_id: str) -> dict:
    doc = frappe.get_doc("Custom Item Classification", classification_id)
    
    return {
        "id": doc.name,
        "class_code": doc.class_code,
        "class_name": doc.class_name,
        "class_level": doc.class_level,
        "is_active": bool(doc.is_active),
        "creation": doc.creation,
        "modified": doc.modified,
    }

def get_classification_by_code(class_code: str) -> dict | None:
    doc_name = frappe.db.get_value(
        "Custom Item Classification",
        {"class_code": class_code},
        "name"
    )
    
    if not doc_name:
        return None
        
    return get_classification_by_id(doc_name)

def get_classifications(filters=None, page=1, page_size=20, search=None):
    filters = filters or {}
    data = trigger_zra_select_items_class()
    if data:
        return data, len(data), 1
    allowed_filters = {
        key: filters.get(key)
        for key in ["class_code", "class_level", "is_active"]
        if filters.get(key) is not None
    }

    frappe_filters = build_classification_filters(allowed_filters)
    
    order_by = "class_level asc"
    if filters.get("sort_by"):
        order_by = f"{filters.get('sort_by')} {filters.get('sort_order') or 'asc'}"

    or_filters = []
    if search:
        search = str(search).strip()
        or_filters = [
            ["name", "like", f"%{search}%"],
            ["class_code", "like", f"%{search}%"],
            ["class_name", "like", f"%{search}%"],
        ]

    start = (page - 1) * page_size

    classifications = frappe.get_all(
        "Custom Item Classification",
        filters=frappe_filters,
        or_filters=or_filters if search else None,
        fields=[
            "name as id",
            "class_code",
            "class_name",
            "class_level",
            "is_active",
            # "creation",
            # "modified"
        ],
        limit_start=start,
        limit_page_length=page_size,
        order_by=order_by,
    )

    total_records = len(
        frappe.get_all(
            "Custom Item Classification",
            filters=frappe_filters,
            or_filters=or_filters if search else None,
            pluck="name",
        )
    )

    total_pages = (total_records + page_size - 1) // page_size

    for item in classifications:
        item["is_active"] = bool(item.get("is_active"))
        item["class_level"] = cint(item.get("class_level"))

    return classifications, total_records, total_pages


def delete_classification(classification_id: str):
    frappe.delete_doc("Custom Item Classification", classification_id, ignore_permissions=True)