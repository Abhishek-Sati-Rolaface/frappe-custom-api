"""
Patch: Add Barcode Field to Sales Order Item
- Adds barcode custom field
- Adds manufacturing_date field
- Adds expiry_date field

Run command:
bench --site [site] run-patch custom_api.patches.v1_0.add_barcode_fields
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Create custom fields for barcode on Sales Order Item"""
    
    custom_fields = {
        "Sales Order Item": [
            {
                "fieldname": "barcode_section",
                "label": "Barcode & Batch Details",
                "fieldtype": "Section Break",
                "insert_after": "item_name",
                "collapsible": 0
            },
            {
                "fieldname": "barcode",
                "label": "Barcode",
                "fieldtype": "Data",
                "insert_after": "barcode_section",
                "read_only": 0,
                "unique": 0,
                "help": "Scan or enter product barcode"
            },
            {
                "fieldname": "batch",
                "label": "Batch",
                "fieldtype": "Link",
                "options": "Batch",
                "insert_after": "barcode",
                "read_only": 1
            },
            {
                "fieldname": "manufacturing_date",
                "label": "Manufacturing Date",
                "fieldtype": "Date",
                "insert_after": "batch",
                "read_only": 1
            },
            {
                "fieldname": "expiry_date",
                "label": "Expiry Date",
                "fieldtype": "Date",
                "insert_after": "manufacturing_date",
                "read_only": 1
            },
            {
                "fieldname": "barcode_col_break",
                "fieldtype": "Column Break",
                "insert_after": "expiry_date"
            }
        ]
    }
    
    create_custom_fields(custom_fields, ignore_validate=True)
    
    # Create Item Barcode DocType if not exists
    if not frappe.db.exists("DocType", "Item Barcode"):
        create_item_barcode_doctype()
    
    frappe.db.commit()
    print("✅ Barcode fields added successfully")


def create_item_barcode_doctype():
    """Create Item Barcode DocType"""
    
    doctype_dict = {
        "doctype": "Item Barcode",
        "document_type": "Document",
        "engine": "InnoDB",
        "fields": [
            {
                "fieldname": "item",
                "label": "Item",
                "fieldtype": "Link",
                "options": "Item",
                "reqd": 1
            },
            {
                "fieldname": "barcode",
                "label": "Barcode",
                "fieldtype": "Data",
                "unique": 1,
                "reqd": 1
            },
            {
                "fieldname": "batch",
                "label": "Batch",
                "fieldtype": "Link",
                "options": "Batch"
            },
            {
                "fieldname": "status",
                "label": "Status",
                "fieldtype": "Select",
                "options": "Active\nUsed\nCancelled",
                "default": "Active"
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1
            }
        ]
    }
    
    doc = frappe.new_doc("DocType")
    doc.update(doctype_dict)
    doc.insert(ignore_if_duplicate=True)
