
import frappe
from erpnext.accounts.report.cash_flow.cash_flow import execute
from custom_api.utils.response import send_response

def get_summary_with_colors(report_summary):
    colored_summary = []
    for item in report_summary:
        value = item.get("value", 0)

        if value > 0:
            color = "green"
        elif value < 0:
            color = "red"
        else:
            color = "gray"

        colored_summary.append({
            "label": item.get("label"),
            "value": value,
            "datatype": item.get("datatype"),
            "currency": item.get("currency"),
            "color": color
        })

    return colored_summary


def get_period_fieldnames(columns):
    """Dynamically extract period fieldnames from columns"""
    skip_fields = {"section", "currency", "total", "account"}
    return [
        col.get("fieldname")
        for col in columns
        if col.get("fieldname") and col.get("fieldname") not in skip_fields
    ]


def restructure_data(data, period_fieldnames):
    """
    Simply restructure flat data into parent/child tree.
    Group period fields under 'periods' key.
    No transformation of values.
    """
    result = []
    current_parent = None

    for row in data:
        # Skip empty rows
        if not row:
            continue

        # Separate period fields into 'periods' object
        periods = {f: row.get(f) for f in period_fieldnames if f in row}
        periods["total"] = row.get("total")

        # Build clean node — keep all original fields except period fields
        node = {
            k: v for k, v in row.items()
            if k not in period_fieldnames and k != "total"
        }
        node["periods"] = periods
        node["children"] = []

        indent = row.get("indent", 0)

        if indent == 0:
            # Top-level parent node
            current_parent = node
            result.append(current_parent)
        else:
            # Child node — append to current parent
            if current_parent is not None:
                current_parent["children"].append(node)

    return result


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_cash_flow():
    try:
        company = frappe.defaults.get_user_default("Company")
        current_year = frappe.utils.now_datetime().year

        period_start_date = frappe.request.args.get("from_date", None)
        period_end_date = frappe.request.args.get("to_date", None)
        periodicity = frappe.request.args.get("periodicity", "Yearly")
        from_fiscal_year = frappe.request.args.get("from_fiscal_year", current_year)
        to_fiscal_year = frappe.request.args.get("to_fiscal_year", current_year)
        filter_based_on = frappe.request.args.get("filter_based_on", "Fiscal Year")

        filters = frappe._dict({
            "company": company,
            "from_fiscal_year": from_fiscal_year,
            "to_fiscal_year": to_fiscal_year,
            "period_start_date": period_start_date,
            "period_end_date": period_end_date,
            "filter_based_on": filter_based_on,
            "periodicity": periodicity,
            "include_default_book_entries": 0,
        })

        columns, data, _, chart, report_summary = execute(filters)

        period_fieldnames = get_period_fieldnames(columns)

        return send_response(
            status="success",
            message="Cash Flow fetched successfully.",
            data={
                "columns": columns,
                "summary": get_summary_with_colors(report_summary),
                "data": restructure_data(data, period_fieldnames)
            },
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Cash Flow API Error")
        return send_response(
            status="fail",
            message=str(e),
            data=None,
            status_code=500,
            http_status=500
        )