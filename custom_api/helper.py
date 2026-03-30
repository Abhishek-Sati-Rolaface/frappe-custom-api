import frappe
def get_warehouses(company):
    warehouses = frappe.db.get_all("Warehouse", filters={"company": company, "is_group": 0}, pluck="name")
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

def get_tax_account(company_name, root_type):
    """
    Fetch the default VAT/tax payable account for the company.
    Adjust the account name to match your Chart of Accounts.
    """
    tax_account = frappe.db.get_value(
        "Account",
        {
            "company": company_name,
            "account_type": "Tax",
            "root_type": root_type,
            "is_group": 0
        },
        "name"
    )
    return tax_account