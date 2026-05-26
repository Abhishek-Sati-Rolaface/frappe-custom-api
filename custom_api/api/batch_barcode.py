"""
Batch Barcode API
File: your_app/api/batch_barcode.py

3 Endpoints:
1. validate_barcode_unique  — hooks.py se call hota hai (before_save)
2. get_batch_by_barcode     — Sale pe scan karne ke liye
3. check_barcode_unique     — React real-time validation ke liye
"""

import frappe


# ─────────────────────────────────────────────────────────────────────────────
# 1. VALIDATION — hooks.py ke through Batch save pe automatic call hota hai
# ─────────────────────────────────────────────────────────────────────────────

def validate_barcode_unique(doc, method=None):
    """
    Batch save hone se pehle check karo:
    Koi aur batch mein same barcode to nahi.
    hooks.py mein register hai — manually call karne ki zaroorat nahi.
    """
    if not doc.custom_barcode:
        return

    existing = frappe.db.get_value(
        "Batch",
        {
            "custom_barcode": doc.custom_barcode,
            "name": ["!=", doc.name or ""],
        },
        ["name", "item"],
        as_dict=True,
    )

    if existing:
        frappe.throw(
            f"Barcode <b>{doc.custom_barcode}</b> already exists "
            f"in Batch <b>{existing.name}</b> (Item: <b>{existing.item}</b>). "
            "Please use a unique barcode.",
            title="Duplicate Barcode",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET BATCH BY BARCODE — Sale pe scan karo → details fetch karo
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_batch_by_barcode(barcode):
    """
    React se call hoga jab sale pe barcode scan hoga.

    Request:  POST /api/method/your_app.your_app.api.batch_barcode.get_batch_by_barcode
    Params:   { barcode: "RAJ-2024-001" }

    Response: {
        batch_no, item_code, item_name, uom,
        expiry_date, manufacturing_date,
        price, currency, available_qty
    }
    """
    if not barcode:
        frappe.throw("Barcode is required", frappe.ValidationError)

    # Batch dhundo
    batch = frappe.db.get_value(
        "Batch",
        {"custom_barcode": barcode},
        [
            "name",
            "item",
            "expiry_date",
            "manufacturing_date",
            "custom_barcode",
        ],
        as_dict=True,
    )

    if not batch:
        frappe.throw(
            f"Barcode <b>{barcode}</b> batch not found.",
            frappe.DoesNotExistError
        )

    # Item details
    item = frappe.db.get_value(
        "Item",
        batch.item,
        ["item_name", "item_code", "stock_uom"],
        as_dict=True,
    )

    # Selling price — pehle batch-wise, phir standard
    price_data = _get_selling_price(batch.item, batch.name)

    # Available stock
    stock = frappe.db.sql("""
        SELECT COALESCE(SUM(actual_qty), 0) as qty
        FROM `tabBin`
        WHERE item_code = %s AND batch_no = %s
    """, (batch.item, batch.name), as_dict=True)

    available_qty = stock[0].qty if stock else 0

    return {
        "batch_no":           batch.name,
        "barcode":            batch.custom_barcode,
        "item_code":          item.item_code,
        "item_name":          item.item_name,
        "uom":                item.stock_uom,
        "expiry_date":        str(batch.expiry_date) if batch.expiry_date else None,
        "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
        "price":              price_data.get("rate", 0),
        "currency":           price_data.get("currency", "INR"),
        "price_list":         price_data.get("price_list", ""),
        "is_batch_price":     price_data.get("is_batch_price", False),
        "available_qty":      float(available_qty),
    }


def _get_selling_price(item_code, batch_name):
    """
    Selling price fetch karo.
    Pehle batch-wise check, phir standard selling price.
    """
    # Batch-wise price
    batch_price = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "batch_no": batch_name,
            "selling": 1,
        },
        ["price_list_rate", "currency", "price_list"],
        as_dict=True,
    )

    if batch_price:
        return {
            "rate": batch_price.price_list_rate,
            "currency": batch_price.currency,
            "price_list": batch_price.price_list,
            "is_batch_price": True,
        }

    # Standard price fallback
    std_price = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "selling": 1,
            "price_list": "Standard Selling",
        },
        ["price_list_rate", "currency", "price_list"],
        as_dict=True,
    )

    if std_price:
        return {
            "rate": std_price.price_list_rate,
            "currency": std_price.currency,
            "price_list": std_price.price_list,
            "is_batch_price": False,
        }

    return {"rate": 0, "currency": "INR", "price_list": "", "is_batch_price": False}


# ─────────────────────────────────────────────────────────────────────────────
# 3. CHECK BARCODE UNIQUE — React real-time validation ke liye
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def check_barcode_unique(barcode, batch_name=""):
    """
    React se call hoga jab user barcode type kare.
    Real-time check — duplicate hai ya nahi.

    Request:  POST /api/method/your_app.your_app.api.batch_barcode.check_barcode_unique
    Params:   { barcode: "RAJ-2024-001", batch_name: "" }

    Response: { is_unique: true }
          OR  { is_unique: false, existing_batch: "BCH-001", existing_item: "RAJMA" }
    """
    if not barcode:
        return {"is_unique": True}

    filters = {"custom_barcode": barcode}
    if batch_name:
        filters["name"] = ["!=", batch_name]

    existing = frappe.db.get_value(
        "Batch",
        filters,
        ["name", "item"],
        as_dict=True,
    )

    if existing:
        return {
            "is_unique": False,
            "existing_batch": existing.name,
            "existing_item": existing.item,
        }

    return {"is_unique": True}