import json
import re
import frappe
from typing import Dict, Any

def validate_supplier_payload(data: Dict[str, Any]):
    contacts = data.get("contacts", [])
    if contacts and isinstance(contacts, list):
        for contact in contacts:
            email = contact.get("email")
            if email:
                pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
                if not re.fullmatch(pattern, email):
                    raise frappe.ValidationError(f"Invalid email format in contacts: {email}")

    tpin = data.get("tpin")
    if tpin and not data.get("id") and frappe.db.exists("Supplier", {"tax_id": tpin}):
        raise frappe.exceptions.DuplicateEntryError(f"Supplier with TPIN {tpin} already exists.")
    
def validate_supplier_update_payload(data: Dict[str, Any]):
    contacts = data.get("contacts", [])
    if contacts and isinstance(contacts, list):
        for contact in contacts:
            email = contact.get("email")
            if email:
                pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
                if not re.fullmatch(pattern, email):
                    raise frappe.ValidationError(f"Invalid email format in contacts: {email}")
