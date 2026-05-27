import frappe
def get_warehouses(company, disabled):
    filters = {
                "company": company,
                "is_group": 0,
            }

    if disabled is not None:
        filters["disabled"] = disabled

    warehouses = frappe.db.get_all("Warehouse", filters=filters, pluck="name")   
    return warehouses

STATUS_MAP = {
    "Approved": {
        "action": "submit",
        "erp_status": "To Receive and Bill"
    },
    "Cancelled": {
        "action": "cancel",
        "erp_status": "Cancelled"
    },
    "Completed": {
        "action": None,
        "erp_status": "Completed"
    }
}

def get_leaf_accounts(rows):
    parent_accounts = {row.get("parent_account") for row in rows if row.get("parent_account")}
    return [row for row in rows if row.get("account") not in parent_accounts]

def get_frontend_url():
    return frappe.conf.get("frontend_url", None)