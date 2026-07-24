from custom_api.utils.response import send_old_response
import frappe
from custom_api.api.dashboard.customer.service import get_customer_dashboard_data


@frappe.whitelist(allow_guest=False, methods=["GET"])
def customer_dashboard(year=None, dormant_days=None):
    try:
        data = get_customer_dashboard_data(year=year, dormant_days=dormant_days)

        return send_old_response(
            status="success",
            message="Customer dashboard data retrieved successfully.",
            data=data,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Customer Dashboard API Error")
        return send_old_response(
            status="error",
            message=f"Error retrieving customer dashboard data: {str(e)}",
            data=None,
            status_code=500,
            http_status=500,
        )