import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe import _

@frappe.whitelist()
def get_current_fiscal_year():
    today = frappe.utils.nowdate()
    company = frappe.defaults.get_user_default("Company")
    fy, fy_start, fy_end = get_fiscal_year(today, company=company)
    return {
        "fiscal_year": fy,
        "start_date": fy_start,
        "end_date": fy_end
    }