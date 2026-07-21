import frappe
from custom_api.utils.response import send_old_response
from custom_api.api.dashboard.sales.service import get_sales_dashboard_data


@frappe.whitelist(allow_guest=False, methods=["GET"])
def sales_dashboard(year=None, order_by=None):
    """
<<<<<<< HEAD
    API Endpoint: /api/method/custom_api.api.dashboard.sales.api.sales_dashboard
=======
    API Endpoint: /api/method/your_app_name.api.sales_dashboard
>>>>>>> 88c5e12 (refactor sales dashboard API to consolidate data retrieval and improve error handling)
    Accepts:
        - year (int): Optional, defaults to current year
        - order_by (str): Optional sorting for top_recent_sales (e.g., "base_grand_total desc")
    """
    try:
        data = get_sales_dashboard_data(year=year, order_by=order_by)

        return send_old_response(
            status="success",
            message="Sales dashboard data retrieved successfully.",
            data=data,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sales Dashboard API Error")
        return send_old_response(
            status="error",
            message=f"Error retrieving sales dashboard data: {str(e)}",
            data=None,
            status_code=500,
            http_status=500,
        )