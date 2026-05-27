import frappe


@frappe.whitelist()
def get_item_from_batch_barcode(barcode):
    """Batch Barcode from item details """
    try:
        batch = frappe.db.get_value(
            "Batch",
            {"custom_barcode": str(barcode)},
            ["name", "item", "batch_id", "expiry_date"],
            as_dict=True
        )

        if not batch:
            return None

        item = frappe.db.get_value(
            "Item",
            batch.item,
            ["item_name", "stock_uom"],
            as_dict=True
        )

        if not item:
            frappe.log_error(f"Item {batch.item} not found", "Barcode Scan")
            return None

        # Default selling price list fetch karo
        selling_price_list = frappe.db.get_single_value(
            "Selling Settings", "selling_price_list"
        ) or "Standard Selling"

        # Rate fetch karo Item Price se
        rate = frappe.db.get_value(
            "Item Price",
            {
                "item_code": batch.item,
                "selling": 1,
                "price_list": selling_price_list
            },
            "price_list_rate"
        ) or 0

        return {
            "item_code": batch.item,
            "item_name": item.item_name,
            "batch_no": batch.batch_id,
            "uom": item.stock_uom,
            "rate": rate,
            "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
            "barcode": barcode
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Barcode Scan Error")
        return None