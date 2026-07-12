import json
import re
import frappe
from typing import Dict, Any

def validate_credit_limits(data: Dict[str, Any]):
    credit_limits = data.get("credit_limits")
    if credit_limits is not None:
        if not isinstance(credit_limits, list):
            raise frappe.ValidationError("credit_limits must be a list of objects.")
        for cl in credit_limits:
            if not cl.get("company"):
                raise frappe.ValidationError("Company is required for each credit limit entry.")
            if cl.get("credit_limit") is None:
                raise frappe.ValidationError("Credit limit value is required for each entry.")

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
        
    validate_credit_limits(data)
    
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

    tpin = data.get("tpin")
    customer_id = data.get("id") 
    
    if tpin and customer_id:
        existing_customer = frappe.db.get_value("Customer", {"tax_id": tpin}, "name")
        if existing_customer and existing_customer != customer_id:
            raise frappe.exceptions.DuplicateEntryError(f"Customer with TPIN {tpin} already exists.")

    validate_credit_limits(data)