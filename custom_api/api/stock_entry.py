import frappe
import json
from frappe import _


@frappe.whitelist()
def create_stock_entry(entry_type, items, company=None):
    """
    Create and submit a Stock Entry via API.

    entry_type: 'Material Transfer' / 'Material Issue' / 'Material Receipt' / etc.
    items: JSON string or list of dicts:
        [
            {
                "item_code": "ITEM-001",
                "qty": 10,
                "s_warehouse": "Stores - RC",   # not needed for Material Receipt
                "t_warehouse": "Finished Goods - RC",  # not needed for Material Issue
                "batch_no": "BATCH-2026-001",   # optional, only if batch tracked
                "basic_rate": 150               # optional, mainly for Receipt
            }
        ]
    company: optional, only needed if multi-company site
    """
    try:
        if isinstance(items, str):
            items = json.loads(items)

        if not items or not isinstance(items, list):
            frappe.throw(_("Items list is required"))

        se_doc = {
            "doctype": "Stock Entry",
            "stock_entry_type": entry_type,
            "items": items
        }

        if company:
            se_doc["company"] = company

        doc = frappe.get_doc(se_doc)
        doc.insert()
        doc.submit()
        frappe.db.commit()

        return {
            "success": True,
            "stock_entry": doc.name,
            "docstatus": doc.docstatus
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Stock Entry API Error")
        return {
            "success": False,
            "error": str(e)
        }