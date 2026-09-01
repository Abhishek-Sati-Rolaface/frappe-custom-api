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

def transform_item_classes(item_list):
    return [
        {
            "id": item.get("itemClsCd"),
            "class_code": item.get("itemClsCd"),
            "class_name": item.get("itemClsNm"),
            "class_level": item.get("itemClsLvl"),
            # "tax_type_code": item.get("taxTyCd"),
            # "major_target": item.get("mjrTgYn"),
            "is_active": item.get("useYn") == "Y",
        }
        for item in item_list
    ]
def trigger_zra_select_items_class():
    installed_apps = frappe.get_installed_apps()
    if "zra_smart_invoice" in installed_apps:
        try:
            from zra_smart_invoice.client import make_vsdc_request
            from zra_smart_invoice.config import get_zra_config
            config = get_zra_config()
            payload = {}
            payload["tpin"] = config["tpin"]
            payload["bhfId"] = config["bhf_id"]
            payload["lastReqDt"] = "20231215000000"
            result = make_vsdc_request("itemClass/selectItemsClass", payload)
            if result.get('resultCd') == '000':
                data = result.get("data")
                item_list = data.get("itemClsList")
                return transform_item_classes(item_list)
                # return data
        except Exception as e:
            frappe.log_error("trigger_zra_select_items_class Exception", str(e))