import frappe
from custom_api.utils.response import send_old_response
from frappe.utils import flt, getdate, get_datetime
from custom_api.api.dashboard.sales.service import get_top_recent_sales_data

@frappe.whitelist(allow_guest=False, methods=["GET"])
def top_recent_sales(order_by=None):
    """
    API Endpoint: /api/method/your_app_name.api.top_recent_sales
    Accepts:
        - order_by (str): Optional custom sorting (e.g., "base_grand_total desc")
    """
    try:
        # Call the service layer to get raw data
        recent_sales = get_top_recent_sales_data(order_by=order_by)

        return send_old_response(
            status="success",
            message="Top 10 recent sales retrieved successfully.",
            data=recent_sales,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Recent Sales API Error")
        return send_old_response(
            status="error",
            message=f"Error retrieving recent sales data: {str(e)}",
            data=None,
            status_code=500,
            http_status=500,
        )

@frappe.whitelist(allow_guest=False, methods=["GET"])
def monthly_sales_breakdown(year=None):
    try:
        company = frappe.defaults.get_user_default("Company") or frappe.get_default("Company")

        filters = {
            "docstatus": 1,
            "company": company
        }

        # Apply year filter if provided
        if year:
            filters["posting_date"] = ["between", [f"{year}-01-01", f"{year}-12-31"]]

        # Fetch relevant invoice data
        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=["posting_date", "base_grand_total", "outstanding_amount", "conversion_rate"]
        )

        # ==========================================
        # 1. Initialize 12 Months Array
        # ==========================================
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # This structure matches the frontend ECharts expectation
        chart_data = [
            {"month": m, "totalSales": 0.0, "totalReceived": 0.0, "totalPending": 0.0} 
            for m in months
        ]

        # ==========================================
        # 2. Populate Array with Data
        # ==========================================
        for inv in invoices:
            if not inv.posting_date:
                continue
                
            # Get the month index (0 to 11)
            month_idx = getdate(inv.posting_date).month - 1 
            
            # Calculate amounts in base currency
            sales_amount = flt(inv.base_grand_total)
            
            # Ensure conversion_rate fallback to 1 to avoid multiplying by 0
            conversion_rate = flt(inv.conversion_rate) or 1.0 
            pending_amount = flt(inv.outstanding_amount) * conversion_rate
            
            received_amount = sales_amount - pending_amount

            # Add to the respective month's totals
            if 0 <= month_idx < 12:
                chart_data[month_idx]["totalSales"] += sales_amount
                chart_data[month_idx]["totalPending"] += pending_amount
                chart_data[month_idx]["totalReceived"] += received_amount

        # ==========================================
        # 3. Return Final Data
        # ==========================================
        return send_old_response(
            status="success",
            message="Monthly sales breakdown retrieved successfully.",
            data=chart_data,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Monthly Sales Breakdown API Error")
        return send_old_response(
            status="error",
            message=f"Error retrieving sales breakdown: {str(e)}",
            data=None,
            status_code=500,
            http_status=500,
        )

@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_document_counts():
    try:
        company = frappe.defaults.get_user_default("Company") or frappe.get_default("Company")

        # Base filter: Only count submitted documents (docstatus = 1) for the current company
        base_filters = {
            "docstatus": 1,
            "company": company
        }

        # Initialize counts
        counts = {
            "proforma_invoices": 0,
            "quotations": 0,
            "sales_invoices": 0,
            "credit_notes": 0,
            "debit_notes": 0
        }

        # 1. Count Quotations
        counts["quotations"] = frappe.db.count("Quotation", filters=base_filters)

        # 2. Count regular Sales Invoices (excluding returns)
        counts["sales_invoices"] = frappe.db.count(
            "Sales Invoice", 
            filters={**base_filters, "is_return": 0}
        )

        # 3. Count Credit Notes (Sales Invoices where is_return = 1)
        counts["credit_notes"] = frappe.db.count(
            "Sales Invoice", 
            filters={**base_filters, "is_return": 1}
        )

        # 4. Count Debit Notes (Purchase Invoices where is_return = 1)
        counts["debit_notes"] = frappe.db.count(
            "Purchase Invoice", 
            filters={**base_filters, "is_return": 1}
        )

        # 5. Count Proforma Invoices (Assuming it's a custom DocType)
        if frappe.db.exists("DocType", "Proforma Invoice"):
            counts["proforma_invoices"] = frappe.db.count("Proforma Invoice", filters=base_filters)

        return send_old_response(
            status="success",
            message="Document counts retrieved successfully.",
            data=counts,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Document Counts API Error")
        return send_old_response(
            status="error",
            message=f"Error retrieving document counts: {str(e)}",
            data=None,
            status_code=500,
            http_status=500,
        )

@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_monthly_sales(year=None):
    try:
        company = frappe.defaults.get_user_default("Company") or frappe.get_default("Company")

        # Default to current year if not provided
        if not year:
            year = get_datetime().year
        
        # Ensure year is an integer
        year = int(year)

        # 1. Initialize the 12-month data structure
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        data = [
            {
                "month": month,
                "year": year,
                "totalSales": 0.0,
                "receivable": 0.0,
                "received": 0.0
            }
            for month in months
        ]

        # 2. Fetch all submitted Sales Invoices for the given year
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={
                "docstatus": 1,
                "company": company,
                "posting_date": ["between", [f"{year}-01-01", f"{year}-12-31"]]
            },
            fields=["posting_date", "base_grand_total", "outstanding_amount", "conversion_rate"]
        )

        # 3. Process and aggregate the data
        for inv in invoices:
            if not inv.posting_date:
                continue
                
            # Get the month index (0 for Jan, 11 for Dec)
            month_idx = getdate(inv.posting_date).month - 1 
            
            # --- UPDATED CALCULATION LOGIC ---
            # Safe conversion rate (defaults to 1 to avoid multiplying by 0)
            conv_rate = flt(inv.conversion_rate) or 1.0
            
            # Calculate Receivable (Pending)
            receivable_pending = flt(inv.outstanding_amount) * conv_rate
            
            # Calculate Received (Total Invoiced - Pending)
            received = flt(inv.base_grand_total) - receivable_pending
            
            # Store total sales for the array
            total_sales = flt(inv.base_grand_total)
            # ---------------------------------

            # Add to the respective month's totals
            if 0 <= month_idx < 12:
                data[month_idx]["totalSales"] += total_sales
                data[month_idx]["receivable"] += receivable_pending
                data[month_idx]["received"] += received

        # 4. Return formatted response
        return send_old_response(
            status="success",
            message="Sales Data retrieved successfully.",
            data=data,
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Monthly Sales API Error")
        return send_old_response(
            status="error",
            message=f"Error retrieving sales data: {str(e)}",
            data=None,
            status_code=500,
            http_status=500,
        )