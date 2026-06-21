import frappe

def before_validate(doc, method):

    default_cost_center = frappe.db.get_value("Company", doc.company, "cost_center")
    
    if doc.accounts:
        for account in doc.accounts:
            if not account.cost_center:
                account.cost_center = default_cost_center