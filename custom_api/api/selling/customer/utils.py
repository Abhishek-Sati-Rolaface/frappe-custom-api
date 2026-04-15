import json
import re
import frappe
from typing import Dict, Any

def validate_customer_payload(data: Dict[str, Any]):
    email = data.get("email")
    if email:
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.fullmatch(pattern, email):
            raise frappe.ValidationError(f"Invalid email format: {email}")

    customer_type = data.get("type")
    if customer_type:
        valid_types = {"Individual", "Company", "Partnership"}
        if customer_type not in valid_types:
            raise frappe.ValidationError(f"Invalid customer type. Allowed: {', '.join(valid_types)}")

    tpin = data.get("tpin")
    if tpin and not data.get("id") and frappe.db.exists("Customer", {"tax_id": tpin}):
        raise frappe.exceptions.DuplicateEntryError(f"Customer with TPIN {tpin} already exists.")
    
def validate_customer_update_payload(data: Dict[str, Any]):
    email = data.get("email")
    if email:
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.fullmatch(pattern, email):
            raise frappe.ValidationError(f"Invalid email format: {email}")

    customer_type = data.get("type")
    if customer_type:
        valid_types = {"Individual", "Company", "Partnership"}
        if customer_type not in valid_types:
            raise frappe.ValidationError(f"Invalid customer type. Allowed: {', '.join(valid_types)}")
