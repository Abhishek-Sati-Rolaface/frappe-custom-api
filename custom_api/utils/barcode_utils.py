import frappe
@frappe.whitelist()
def get_item_from_batch_barcode(barcode):
    """Batch ke custom_barcode se item aur batch fetch karta hai"""
    
    batch = frappe.db.get_value(
        "Batch",
        {"custom_barcode": str(barcode)},
        ["name", "item", "batch_id", "expiry_date"],
        as_dict=True
    )

    if not batch:
        return None

    # Item ki details fetch karo
    item = frappe.db.get_value(
        "Item",
        batch.item,
        ["item_name", "stock_uom", "description"],
        as_dict=True
    )

    return {
        "item_code": batch.item,
        "item_name": item.item_name,
        "batch_no": batch.batch_id,
        "uom": item.stock_uom,
        "expiry_date": batch.expiry_date,
        "barcode": barcode
    }