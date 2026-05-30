import frappe


@frappe.whitelist()
def get_item_from_batch_barcode(barcode):
    """Batch Barcode from item details """
    try:
        batch = frappe.db.get_value(
            "Batch",
            {"custom_barcode": str(barcode)},
            ["name", "item", "batch_id", "expiry_date", "manufacturing_date"],  # ← mfg_date add kiya
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

        # Batch quantity fetch karo
        batch_qty = frappe.db.get_value(
            "Batch",
            {"batch_id": batch.batch_id},
            "batch_qty"
        ) or 0

        return {
            "item_code": batch.item,
            "item_name": item.item_name,
            "batch_no": batch.batch_id,
            "uom": item.stock_uom,
            "rate": rate,
            "quantity": batch_qty,
            "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
            "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
            "barcode": barcode
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Barcode Scan Error")
        return None


@frappe.whitelist()
def get_item_batches(item_code):
    """Item ke saare batches with details fetch karo"""
    try:
        if not item_code:
            frappe.throw("Item code required hai")

        # Item exist karta hai?
        item = frappe.db.get_value(
            "Item",
            item_code,
            ["item_name", "stock_uom"],
            as_dict=True
        )

        if not item:
            return {"success": False, "message": f"Item '{item_code}' not found"}

        # Saare batches fetch karo
        batches = frappe.db.get_all(
            "Batch",
            filters={"item": item_code},
            fields=[
                "name",
                "batch_id",
                "manufacturing_date",
                "expiry_date",
                "batch_qty",
                "custom_barcode",
                "disabled"
            ],
            order_by="creation desc"
        )

        if not batches:
            return {
                "success": True,
                "item_code": item_code,
                "item_name": item.item_name,
                "batches": [],
                "message": "Koi batch nahi mila"
            }

        # Har batch me barcode print URL add karo
        batch_list = []
        for batch in batches:
            batch_data = {
                "batch_id": batch.batch_id,
                "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
                "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
                "quantity": batch.batch_qty or 0,
                "disabled": batch.disabled,
                "barcode": {
                    "value": batch.custom_barcode or None,
                    "has_barcode": bool(batch.custom_barcode),
                    "print_url": (
                        f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf"
                        f"?doctype=Batch&name={batch.name}"
                        f"&format=Batch Barcode Label&no_letterhead=1"
                    ) if batch.custom_barcode else None
                }
            }
            batch_list.append(batch_data)

        return {
            "success": True,
            "item_code": item_code,
            "item_name": item.item_name,
            "uom": item.stock_uom,
            "total_batches": len(batch_list),
            "batches": batch_list
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Item Batches Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist(allow_guest=True)
def get_barcode_image(value):
    """Barcode PNG image directly return karta hai"""
    try:
        import barcode
        from barcode.writer import ImageWriter
        from io import BytesIO

        CODE128 = barcode.get_barcode_class("code128")
        buffer = BytesIO()

        CODE128(str(value), writer=ImageWriter()).write(buffer, options={
            "module_height": 15.0,
            "module_width": 0.8,
            "quiet_zone": 6.5,
            "write_text": False,
            "dpi": 300
        })

        buffer.seek(0)

        frappe.local.response.filename = f"barcode_{value}.png"
        frappe.local.response.filecontent = buffer.getvalue()
        frappe.local.response.type = "png"

    except Exception as e:
        frappe.log_error(str(e), "Barcode Image Error")