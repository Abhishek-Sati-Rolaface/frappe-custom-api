"""
Patch: Batch DocType mein custom_barcode field create karo
File: your_app/patches/v1_0/create_batch_barcode_field.py

Run Command:
bench --site [your-site] run-patch your_app.your_app.patches.v1_0.create_batch_barcode_field
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    this will run only one time.
    """

    field_exists = frappe.db.exists(
        "Custom Field",
        {"dt": "Batch", "fieldname": "custom_barcode"}
    )

    if field_exists:
        print("✓ custom_barcode field already exists in Batch — skipping.")
        return

    # Field create karo
    create_custom_fields({
        "Batch": [
            {
                "label": "Barcode",
                "fieldname": "custom_barcode",
                "fieldtype": "Data",
                "insert_after": "expiry_date",
                "unique": 1,
                "search_index": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
                "bold": 0,
                "reqd": 0,
            }
        ]
    })

    frappe.db.commit()
    print("✓ custom_barcode field created successfully in Batch DocType.")