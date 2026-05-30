import frappe


@frappe.whitelist()
def get_item_from_batch_barcode(barcode):
    """Batch Barcode from item details """
    try:
        batch = frappe.db.get_value(
            "Batch",
            {"custom_barcode": str(barcode)},
            ["name", "item", "batch_id", "expiry_date", "manufacturing_date"],  # ← mfg_date add 
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

        # Default selling price list
        selling_price_list = frappe.db.get_single_value(
            "Selling Settings", "selling_price_list"
        ) or "Standard Selling"

        # Item rate from price list
        rate = frappe.db.get_value(
            "Item Price",
            {
                "item_code": batch.item,
                "selling": 1,
                "price_list": selling_price_list
            },
            "price_list_rate"
        ) or 0

        # Batch quantity
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


# @frappe.whitelist()
# def get_item_batches(item_code):
#     """Item batches with details"""
#     try:
#         if not item_code:
#             frappe.throw("Item code required hai")

#         # Item exist 
#         item = frappe.db.get_value(
#             "Item",
#             item_code,
#             ["item_name", "stock_uom"],
#             as_dict=True
#         )

#         if not item:
#             return {"success": False, "message": f"Item '{item_code}' not found"}

#         # Fecth all batches for the item
#         batches = frappe.db.get_all(
#             "Batch",
#             filters={"item": item_code},
#             fields=[
#                 "name",
#                 "batch_id",
#                 "manufacturing_date",
#                 "expiry_date",
#                 "batch_qty",
#                 "custom_barcode",
#                 "disabled"
#             ],
#             order_by="creation desc"
#         )

#         if not batches:
#             return {
#                 "success": True,
#                 "item_code": item_code,
#                 "item_name": item.item_name,
#                 "batches": [],
#                 "message": "No batches found for this item"
#             }

#         # Add batch barcode print URL and other details
#         batch_list = []
#         for batch in batches:
#             batch_data = {
#                 "batch_id": batch.batch_id,
#                 "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
#                 "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
#                 "quantity": batch.batch_qty or 0,
#                 "disabled": batch.disabled,
#                 "barcode": {
#                     "value": batch.custom_barcode or None,
#                     "has_barcode": bool(batch.custom_barcode),
#                     "print_url": (
#                         f"{frappe.utils.get_url()}/api/method/frappe.utils.print_format.download_pdf"
#                         f"?doctype=Batch&name={batch.name}"
#                         f"&format=Batch Barcode Label&no_letterhead=1"
#                     ) if batch.custom_barcode else None
#                 }
#             }
#             batch_list.append(batch_data)

#         return {
#             "success": True,
#             "item_code": item_code,
#             "item_name": item.item_name,
#             "uom": item.stock_uom,
#             "total_batches": len(batch_list),
#             "batches": batch_list
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Get Item Batches Error")
#         return {"success": False, "message": str(e)}



@frappe.whitelist()
def get_item_batches(item_code):
    """Item code se saare batches with details fetch karo"""
    try:
        if not item_code:
            frappe.throw("Item code is required")

        item = frappe.db.get_value(
            "Item",
            item_code,
            ["name", "item_name", "stock_uom"],
            as_dict=True
        )

        if not item:
            return {"success": False, "message": f"Item '{item_code}' not found"}

        batches = frappe.db.get_all(
            "Batch",
            filters={"item": item_code},
            fields=[
                "name", "batch_id", "manufacturing_date",
                "expiry_date", "batch_qty", "custom_barcode", "disabled"
            ],
            order_by="creation desc"
        )

        if not batches:
            return {
                "success": True,
                "item_code": item.name,
                "item_name": item.item_name,
                "batches": [],
                "message": "No batches found for this item"
            }

        base_url = frappe.utils.get_url()
        batch_list = []

        for batch in batches:
            batch_list.append({
                "item_code": item.name,
                "item_name": item.item_name,
                "batch_no": batch.batch_id,
                "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
                "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
                "quantity": batch.batch_qty or 0,
                "barcode_value": batch.custom_barcode or None,
                "barcode_image_url": (
                    f"{base_url}/api/method/custom_api.utils.barcode_utils.get_barcode_image?value={batch.custom_barcode}"
                    if batch.custom_barcode else None
                )
            })

        return {
            "success": True,
            "total_batches": len(batch_list),
            "batches": batch_list
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Item Batches Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist(allow_guest=True)
def get_barcode_image(value):
    """Barcode PNG image directly return"""
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
        frappe.local.response.type = "download"
        frappe.local.response["Content-Type"] = "image/png"

    except Exception as e:
        frappe.log_error(str(e), "Barcode Image Error")
        frappe.throw(str(e))


@frappe.whitelist()
def search_item_batches(search_term):
    """Item name search karke saare matching items with batches fetch karo"""
    try:
        if not search_term:
            frappe.throw("Search term required hai")

        # Search karo items me
        items = frappe.db.get_all(
            "Item",
            filters={
                "item_name": ["like", f"%{search_term}%"],
                "disabled": 0
            },
            fields=["name", "item_name", "stock_uom", "item_group", "description"],
            order_by="item_name asc"
        )

        if not items:
            return {
                "success": True,
                "search_term": search_term,
                "total_items": 0,
                "results": [],
                "message": "Koi item nahi mila"
            }

        results = []
        for item in items:
            batches = frappe.db.get_all(
                "Batch",
                filters={"item": item.name, "disabled": 0},
                fields=[
                    "batch_id",
                    "manufacturing_date",
                    "expiry_date",
                    "batch_qty"
                ],
                order_by="creation desc"
            )

            results.append({
                "item_code": item.name,
                "item_name": item.item_name,
                "uom": item.stock_uom,
                "item_group": item.item_group,
                "description": item.description,
                "total_batches": len(batches),
                "batches": [
                    {
                        "batch_no": batch.batch_id,
                        "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
                        "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
                        "quantity": batch.batch_qty or 0
                    }
                    for batch in batches
                ]
            })

        return {
            "success": True,
            "search_term": search_term,
            "total_items": len(results),
            "results": results
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Search Item Batches Error")
        return {"success": False, "message": str(e)}