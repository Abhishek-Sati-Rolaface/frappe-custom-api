import frappe

def get_top_recent_sales_data(order_by=None):
    
    company = frappe.defaults.get_user_default("Company") or frappe.get_default("Company")

    if not order_by:
        order_by = "base_grand_total desc"

    recent_sales = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "company": company
        },
        fields=[
            "name", 
            "customer_name", 
            "posting_date", 
            "base_grand_total", 
            "outstanding_amount", 
            "status",
            "currency"
        ],
        order_by=order_by,
        limit_page_length=10
    )

    return recent_sales