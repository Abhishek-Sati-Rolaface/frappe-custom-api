"""
Barcode Management API
- Save barcode for item (manual entry)
- Scan and validate barcode on sale
- Fetch item details from barcode
"""

import frappe
from frappe import _
from custom_api.utils.response import send_response


@frappe.whitelist(allow_guest=False, methods=["POST"])
def save_barcode():
    """
    Save barcode for item (manual entry)
    Input: {
        "barcode": "12345678",
        "item_code": "ITEM-001",
        "batch": "BATCH-2024-001"
    }
    """
    try:
        data = frappe.request.get_json()
        
        if not data:
            return send_response(
                status="error",
                message="Request body required",
                data=None,
                status_code=400,
                http_status=400
            )
        
        barcode = data.get("barcode", "").strip()
        item_code = data.get("item_code", "").strip()
        batch = data.get("batch", "").strip()
        
        if not barcode:
            return send_response(
                status="error",
                message="'barcode' is required",
                data=None,
                status_code=400,
                http_status=400
            )
        
        if not item_code:
            return send_response(
                status="error",
                message="'item_code' is required",
                data=None,
                status_code=400,
                http_status=400
            )
        
        # Verify item exists
        if not frappe.db.exists("Item", item_code):
            return send_response(
                status="error",
                message=f"Item '{item_code}' not found",
                data=None,
                status_code=404,
                http_status=404
            )
        
        # Check if barcode already exists
        existing = frappe.db.get_value(
            "Item Barcode",
            {"barcode": barcode}
        )
        
        if existing:
            return send_response(
                status="error",
                message=f"Barcode '{barcode}' already exists",
                data=None,
                status_code=400,
                http_status=400
            )
        
        # Save barcode record
        barcode_doc = frappe.new_doc("Item Barcode")
        barcode_doc.item = item_code
        barcode_doc.barcode = barcode
        if batch:
            barcode_doc.batch = batch
        barcode_doc.status = "Active"
        barcode_doc.insert(ignore_permissions=True)
        
        frappe.db.commit()
        
        return send_response(
            status="success",
            message=f"Barcode saved successfully",
            data={
                "barcode": barcode,
                "item_code": item_code,
                "batch": batch,
                "status": "Active"
            },
            status_code=201,
            http_status=201
        )
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Save Barcode Error")
        return send_response(
            status="error",
            message=str(e),
            data=None,
            status_code=500,
            http_status=500
        )


@frappe.whitelist(allow_guest=False, methods=["POST"])
def scan_barcode():
    """
    Scan barcode and get complete item details
    Input: {
        "barcode": "ITEM-001-BATCH-001-ABC12345"
    }
    Output: Item Name, MFG Date, Expiry, Batch, Price, etc.
    """
    try:
        data = frappe.request.get_json()
        barcode = data.get("barcode", "").strip()
        
        if not barcode:
            return send_response(
                status="error",
                message="'barcode' is required",
                data=None,
                status_code=400,
                http_status=400
            )
        
        # Find barcode record
        barcode_record = frappe.db.get_value(
            "Item Barcode",
            {"barcode": barcode},
            ["item", "batch", "creation"],
            as_dict=True
        )
        
        if not barcode_record:
            return send_response(
                status="error",
                message=f"Barcode '{barcode}' not found in system",
                data=None,
                status_code=404,
                http_status=404
            )
        
        item_code = barcode_record["item"]
        batch = barcode_record["batch"]
        
        # Get item details
        item_doc = frappe.get_doc("Item", item_code)
        
        # Get batch details (if exists)
        batch_details = {}
        if batch:
            batch_details = frappe.db.get_value(
                "Batch",
                batch,
                ["name", "item", "manufacturing_date", "expiry_date", "qty_to_be_received"],
                as_dict=True
            ) or {}
        
        # Get latest price from Price List
        price_list_item = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "selling": 1},
            ["price_list_rate", "currency"],
            as_dict=True
        ) or {}
        
        item_details = {
            "barcode": barcode,
            "item_code": item_code,
            "item_name": item_doc.item_name,
            "description": item_doc.description,
            "uom": item_doc.stock_uom,
            "batch": batch,
            "manufacturing_date": batch_details.get("manufacturing_date"),
            "expiry_date": batch_details.get("expiry_date"),
            "qty_available": batch_details.get("qty_to_be_received", 0),
            "price": float(price_list_item.get("price_list_rate", 0)) if price_list_item else 0,
            "currency": price_list_item.get("currency", "INR") if price_list_item else "INR",
            "scanned_at": frappe.utils.now(),
            "status": "valid"
        }
        
        return send_response(
            status="success",
            message="Barcode scanned successfully",
            data=item_details,
            status_code=200,
            http_status=200
        )
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Scan Barcode Error")
        return send_response(
            status="error",
            message=str(e),
            data=None,
            status_code=500,
            http_status=500
        )


@frappe.whitelist(allow_guest=False, methods=["POST"])
def validate_barcode():
    """
    Validate if barcode is unique and active
    Input: {
        "barcode": "ITEM-001-BATCH-001-ABC12345"
    }
    """
    try:
        data = frappe.request.get_json()
        barcode = data.get("barcode", "").strip()
        
        if not barcode:
            return send_response(
                status="error",
                message="'barcode' is required",
                data=None,
                status_code=400,
                http_status=400
            )
        
        # Check if barcode exists
        exists = frappe.db.exists("Item Barcode", {"barcode": barcode})
        
        if not exists:
            return send_response(
                status="error",
                message=f"Barcode '{barcode}' is not valid",
                data=None,
                status_code=404,
                http_status=404
            )
        
        # Check if already used in a sale
        sales_order_item = frappe.db.get_value(
            "Sales Order Item",
            {"barcode": barcode, "docstatus": ["!=", 2]},
            ["parent", "item_code", "qty"]
        )
        
        is_used = False
        used_in = None
        
        if sales_order_item:
            is_used = True
            used_in = f"Sales Order {sales_order_item[0]}"
        
        return send_response(
            status="success",
            message="Barcode validation successful",
            data={
                "barcode": barcode,
                "is_valid": True,
                "is_used": is_used,
                "used_in": used_in
            },
            status_code=200,
            http_status=200
        )
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Validate Barcode Error")
        return send_response(
            status="error",
            message=str(e),
            data=None,
            status_code=500,
            http_status=500
        )


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_barcode_history():
    """
    Get history of scanned barcodes
    Query params:
    - limit: number of records (default: 50)
    - filters: JSON filter object
    """
    try:
        args = frappe.request.args
        limit = int(args.get("limit", 50))
        
        # Get recent barcode scans from Sales Order Items
        barcodes = frappe.get_all(
            "Sales Order Item",
            filters={"barcode": ["!=", ""]},
            fields=[
                "barcode",
                "item_code",
                "item_name",
                "qty",
                "rate",
                "amount",
                "parent as sales_order",
                "creation"
            ],
            order_by="creation desc",
            limit_page_length=limit
        )
        
        return send_response(
            status="success",
            message="Barcode history fetched",
            data={
                "total": len(barcodes),
                "barcodes": barcodes
            },
            status_code=200,
            http_status=200
        )
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Barcode History Error")
        return send_response(
            status="error",
            message=str(e),
            data=None,
            status_code=500,
            http_status=500
        )
