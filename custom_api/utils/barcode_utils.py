# import frappe
# @frappe.whitelist()
# def get_item_from_batch_barcode(barcode):
#     """Batch ke custom_barcode se item aur batch fetch karta hai"""
    
#     batch = frappe.db.get_value(
#         "Batch",
#         {"custom_barcode": str(barcode)},
#         ["name", "item", "batch_id", "expiry_date"],
#         as_dict=True
#     )

#     if not batch:
#         return None

#     # Item ki details fetch karo
#     item = frappe.db.get_value(
#         "Item",
#         batch.item,
#         ["item_name", "stock_uom", "description"],
#         as_dict=True
#     )

#     return {
#         "item_code": batch.item,
#         "item_name": item.item_name,
#         "batch_no": batch.batch_id,
#         "uom": item.stock_uom,
#         "expiry_date": batch.expiry_date,
#         "barcode": barcode
#     }


import frappe

@frappe.whitelist()
def get_item_from_batch_barcode(barcode):
    # Batch name se dhundho (jo aapka "batch-055" hai)
    batch = frappe.db.get_value(
        "Batch",
        {"name": barcode},          # batch name = scanned barcode
        ["name", "item"],
        as_dict=True
    )

    # Agar name se nahi mila toh batch_id se try karo
    if not batch:
        batch = frappe.db.get_value(
            "Batch",
            {"batch_id": barcode},
            ["name", "item"],
            as_dict=True
        )

    if not batch:
        return None

    # Item details lo
    item = frappe.db.get_value(
        "Item",
        batch.item,
        ["item_code", "item_name", "stock_uom"],
        as_dict=True
    )

    if not item:
        return None

    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "batch_no": batch.name,
        "uom": item.stock_uom
    }