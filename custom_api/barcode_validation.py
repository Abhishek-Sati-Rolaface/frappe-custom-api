"""
Server Script for Barcode Validation
Runs on Sales Order Item save
- Auto-fill item details from barcode
- Validate barcode uniqueness
- Add MFG, Expiry, Batch details
"""

def validate_barcode_on_sale(doc, method):
    """
    Hook: Sales Order Item - Before Save
    If barcode is provided, auto-populate item details
    """
    
    if not doc.barcode or not doc.barcode.strip():
        return
    
    barcode = doc.barcode.strip()
    
    # Find barcode in system
    barcode_record = frappe.db.get_value(
        "Item Barcode",
        {"barcode": barcode},
        ["item", "batch"],
        as_dict=True
    )
    
    if not barcode_record:
        frappe.throw(f"❌ Barcode '{barcode}' not found in system")
    
    item_code = barcode_record["item"]
    batch = barcode_record["batch"]
    
    # Auto-fill item details
    if not doc.item_code:
        doc.item_code = item_code
    
    # Get batch details
    if batch:
        batch_details = frappe.db.get_value(
            "Batch",
            batch,
            ["manufacturing_date", "expiry_date"],
            as_dict=True
        )
        
        if batch_details:
            doc.batch = batch
            doc.manufacturing_date = batch_details.get("manufacturing_date")
            doc.expiry_date = batch_details.get("expiry_date")
    
    # Validate: Check if barcode already used
    existing = frappe.db.get_value(
        "Sales Order Item",
        {
            "barcode": barcode,
            "docstatus": ["!=", 2],
            "name": ["!=", doc.name]
        }
    )
    
    if existing:
        frappe.throw(f"⚠️ Barcode '{barcode}' already used in another Sales Order")
    
    frappe.msgprint(f"✅ Barcode validated: {item_code}")


# Register hook
if __name__ == "frappe.client":
    frappe.db.set_value("Event", "Sales Order Item - Validate", "is_enabled", 1)
