import frappe
from frappe import _

@frappe.whitelist()
def create_stock_correction(warehouse, posting_date, items, posting_time=None):
    """
    items = [
        {"item_code": "ITEM-001", "qty": 50, "valuation_rate": 120.5, "batch_no": "BATCH-001"},
        {"item_code": "ITEM-002", "qty": 20}
    ]
    """
    if isinstance(items, str):
        items = frappe.parse_json(items)

    if not items:
        frappe.throw(_("Items list is required"))

    # Ensure Stock Settings mein "Use Serial No / Batch Fields" hamesha ON rahe
    if not frappe.db.get_single_value("Stock Settings", "use_serial_batch_fields"):
        frappe.db.set_single_value("Stock Settings", "use_serial_batch_fields", 1)
        frappe.db.commit()

    company = frappe.defaults.get_global_default("company")
    if not company:
        frappe.throw(_("No default company set in Global Defaults"))

    doc = frappe.new_doc("Stock Reconciliation")
    doc.company = company
    doc.purpose = "Stock Reconciliation"
    doc.posting_date = posting_date
    if posting_time:
        doc.set_posting_time = 1
        doc.posting_time = posting_time

    for row in items:
        item_code = row.get("item_code")
        has_batch = frappe.db.get_value("Item", item_code, "has_batch_no")

        if has_batch and not row.get("batch_no"):
            frappe.throw(_("Batch No is mandatory for item {0}").format(item_code))

        doc.append("items", {
            "item_code": item_code,
            "warehouse": row.get("warehouse") or warehouse,
            "qty": row.get("qty"),
            "valuation_rate": row.get("valuation_rate"),
            "serial_no": row.get("serial_no"),
            "batch_no": row.get("batch_no"),
            "use_serial_batch_fields": 1,
        })

    doc.insert()
    doc.submit()

    return {
        "name": doc.name,
        "status": "success",
        "message": f"Stock Reconciliation {doc.name} submitted successfully"
    }