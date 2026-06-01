import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def _get_db_key(prefix):
    hash_index = str(prefix).find('#')
    if hash_index != -1:
        db_key = prefix[:hash_index]
        if db_key.endswith('.'):
            db_key = db_key[:-1]
        return db_key
    return prefix

def get_series_for_doctype(doctype):
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(f"DocType '{doctype}' does not exist.")

    meta = frappe.get_meta(doctype)
    naming_field = meta.get_field("naming_series")
    
    if not naming_field:
        frappe.throw(f"DocType '{doctype}' does not support naming_series.")

    options = naming_field.options or ""
    series_prefixes = [opt.strip() for opt in options.split("\n") if opt.strip()]

    result = []
    for prefix in series_prefixes:
        db_key = _get_db_key(prefix)
        
        db_val = frappe.db.sql("SELECT current FROM `tabSeries` WHERE name = %s", (db_key,))
        current_val = db_val[0][0] if db_val else 0
        
        result.append({
            "prefix": prefix,
            "current_value": current_val
        })

    return result

def add_series_to_doctype(doctype, prefix, starting_number=0):
    meta = frappe.get_meta(doctype)
    naming_field = meta.get_field("naming_series")
    
    if not naming_field:
        frappe.throw(f"DocType '{doctype}' does not support naming_series.")

    options = naming_field.options or ""
    series_prefixes = [opt.strip() for opt in options.split("\n") if opt.strip()]

    if prefix not in series_prefixes:
        series_prefixes.append(prefix)
        new_options = "\n".join(series_prefixes)
        make_property_setter(doctype, "naming_series", "options", new_options, "Text")

    db_key = _get_db_key(prefix)
    frappe.db.sql("""
        INSERT INTO `tabSeries` (name, current) 
        VALUES (%s, %s) 
        ON DUPLICATE KEY UPDATE current = %s
    """, (db_key, starting_number, starting_number))

    return {"doctype": doctype, "prefix": prefix, "current_value": starting_number}

def update_series_counter(prefix, new_current_value):
    db_key = _get_db_key(prefix)
    
    exists = frappe.db.sql("SELECT name FROM `tabSeries` WHERE name = %s", (db_key,))
    if not exists:
        frappe.throw(f"Naming Series counter for '{db_key}' not found in the database. Please create it first.")

    frappe.db.sql("""
        UPDATE `tabSeries` 
        SET current = %s 
        WHERE name = %s
    """, (new_current_value, db_key))

    return {"prefix": prefix, "current_value": new_current_value}

def remove_series_from_doctype(doctype, prefix):
    meta = frappe.get_meta(doctype)
    naming_field = meta.get_field("naming_series")
    
    if not naming_field:
        frappe.throw(f"DocType '{doctype}' does not support naming_series.")

    options = naming_field.options or ""
    series_prefixes = [opt.strip() for opt in options.split("\n") if opt.strip()]

    if prefix in series_prefixes:
        series_prefixes.remove(prefix)
        
        new_options = "\n".join(series_prefixes) if series_prefixes else ""
        make_property_setter(doctype, "naming_series", "options", new_options, "Text")
        
    return True

def get_all_active_series():
    docfield_series = frappe.db.sql("""
        SELECT parent as doctype, options 
        FROM `tabDocField` 
        WHERE fieldname = 'naming_series' AND options IS NOT NULL AND options != ''
    """, as_dict=True)
    
    property_setter_series = frappe.db.sql("""
        SELECT doc_type as doctype, value as options 
        FROM `tabProperty Setter` 
        WHERE field_name = 'naming_series' AND property = 'options' AND value IS NOT NULL AND value != ''
    """, as_dict=True)
    
    series_map = {}
    for df in docfield_series:
        series_map[df.doctype] = df.options
        
    for ps in property_setter_series:
        series_map[ps.doctype] = ps.options
        
    all_counters = frappe.db.sql("SELECT name, current FROM `tabSeries`", as_dict=True)
    counter_map = {row.name: row.current for row in all_counters}
    
    result = []
    for doctype, options in series_map.items():
        prefixes = [opt.strip() for opt in options.split("\n") if opt.strip()]
        for prefix in prefixes:
            db_key = _get_db_key(prefix)
            result.append({
                "document_type": doctype,
                "prefix": prefix,
                "current_value": counter_map.get(db_key, 0)
            })
            
    return result


FRONTEND_DOCTYPE_MAP = {
    "sales_order": "Sales Order",
    "sales_invoice": "Sales Invoice",
    "quotation": "Quotation",
    "proforma_invoice": "Quotation",
    "purchase_order": "Purchase Order",
    "purchase_invoice": "Purchase Invoice",
    "customer": "Customer",
    "supplier": "Supplier",
    "item_code": "Item",
    "employee": "Employee",
    "payment_entry": "Payment Entry",
    "journal_entry": "Journal Entry",
    "supplier_quotation": "Supplier Quotation",
    "rfq": "Request for Quotation",
    "purchase_receipt": "Purchase Receipt"
}

def get_bulk_naming_settings():
    settings = {}
    
    for frontend_key, doctype in FRONTEND_DOCTYPE_MAP.items():
        options = frappe.db.get_value("Property Setter", {"doc_type": doctype, "property": "options", "field_name": "naming_series"}, "value")
        
        if not options:
            options = frappe.db.get_value("DocField", {"parent": doctype, "fieldname": "naming_series"}, "options") or ""
        
        prefixes = [opt.strip() for opt in options.split("\n") if opt.strip()]
        
        if doctype == "Quotation":
            if frontend_key == "quotation":
                settings[frontend_key] = prefixes[0] if len(prefixes) > 0 else ""
            elif frontend_key == "proforma_invoice":
                settings[frontend_key] = prefixes[1] if len(prefixes) > 1 else ""
        else:
            settings[frontend_key] = prefixes[0] if prefixes else ""
            
    return settings

def update_bulk_naming_settings(payload_data):
    doctype_prefixes = {}
    
    for key, prefix in payload_data.items():
        if not prefix:
            continue
            
        doctype = FRONTEND_DOCTYPE_MAP.get(key)
        if doctype:
            if doctype not in doctype_prefixes:
                doctype_prefixes[doctype] = []
            doctype_prefixes[doctype].append(prefix)
            
    for doctype, prefixes in doctype_prefixes.items():
        new_options = "\n".join(prefixes)
        make_property_setter(doctype, "naming_series", "options", new_options, "Text")
        
        for pref in prefixes:
            db_key = _get_db_key(pref)
            frappe.db.sql("""
                INSERT INTO `tabSeries` (name, current) 
                VALUES (%s, 0) 
                ON DUPLICATE KEY UPDATE name=name
            """, (db_key,))
            
    return get_bulk_naming_settings()