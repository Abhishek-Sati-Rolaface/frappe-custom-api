import frappe
from typing import Dict, Any


def validate_classification_payload(data: Dict[str, Any], is_update=False):
    if not is_update:
        if not data.get("class_code"):
            raise frappe.ValidationError("class_code is required.")
        if not data.get("class_name"):
            raise frappe.ValidationError("class_name is required.")

        if frappe.db.exists("Custom Item Classification", {"class_code": data.get("class_code")}):
            raise frappe.ValidationError(f"Custom Item Classification with class_code '{data.get('class_code')}' already exists.")

    if is_update and data.get("class_code"):
        existing = frappe.db.exists("Custom Item Classification", {"class_code": data.get("class_code")})
        if existing and existing != data.get("id"):
            raise frappe.ValidationError(f"Custom Item Classification with class_code '{data.get('class_code')}' already exists.")


def build_classification_filters(args: Dict[str, Any]) -> dict:
    frappe_filters = {}

    if not args:
        return frappe_filters

    if args.get("class_code"):
        frappe_filters["class_code"] = args["class_code"]

    if args.get("class_level") is not None:
        try:
            frappe_filters["class_level"] = int(args["class_level"])
        except ValueError:
            pass

    if args.get("is_active") is not None:
        val = str(args.get("is_active")).lower()
        frappe_filters["is_active"] = 1 if val in ["true", "1", "yes"] else 0

    return frappe_filters