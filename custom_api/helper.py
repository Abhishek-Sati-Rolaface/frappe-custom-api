import frappe
def get_warehouses(company):
    warehouses = frappe.db.get_all("Warehouse", filters={"company": company, "is_group": 0}, pluck="name")
    return warehouses