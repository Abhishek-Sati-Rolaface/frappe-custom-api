import math
import frappe
from frappe.utils import today
from erpnext.accounts.report.accounts_receivable.accounts_receivable import execute
from custom_api.utils.response import send_response


def _format_currency(value):
    if value is None:
        return 0.0
    try:
        return round(float(value), 2)
    except Exception:
        return 0.0


def _get_arg(key, default=None):
    return frappe.request.args.get(key, default)


def _calculate_receivable_kpis(rows):

    total_outstanding = 0
    total_invoiced = 0
    total_paid = 0

    total_invoices = 0
    overdue_amount = 0
    overdue_invoices = 0

    ageing_0_30 = ageing_31_60 = ageing_61_90 = 0
    ageing_91_120 = ageing_121_above = 0

    customer_totals = {}

    total_age_days = 0
    counted_age_rows = 0

    today_date = frappe.utils.getdate()

    for r in rows:

        if not isinstance(r, dict):
            continue

        voucher_type = r.get("voucher_type")
        is_return = r.get("is_return")

        outstanding = _format_currency(r.get("outstanding"))
        invoiced = _format_currency(r.get("invoiced"))
        paid = _format_currency(r.get("paid"))

        due_date = r.get("due_date")
        age = r.get("age") or 0

        if voucher_type == "Sales Invoice":
            if is_return:
                total_paid += abs(invoiced)  # credit note
            else:
                total_invoiced += invoiced
                total_invoices += 1

        elif voucher_type == "Payment Entry":
            total_paid += paid

        elif voucher_type == "Journal Entry":
            total_paid += paid

        total_outstanding += outstanding

        if due_date and frappe.utils.getdate(due_date) < today_date and outstanding > 0:
            overdue_amount += outstanding
            overdue_invoices += 1

        ageing_0_30 += _format_currency(r.get("range1"))
        ageing_31_60 += _format_currency(r.get("range2"))
        ageing_61_90 += _format_currency(r.get("range3"))
        ageing_91_120 += _format_currency(r.get("range4"))
        ageing_121_above += _format_currency(r.get("range5"))

        if age:
            total_age_days += age
            counted_age_rows += 1

        customer = r.get("customer_name") or r.get("party") or "Unknown"
        customer_totals.setdefault(customer, 0)
        customer_totals[customer] += outstanding

    avg_collection_days = total_age_days / counted_age_rows if counted_age_rows else 0
    avg_invoice = total_invoiced / total_invoices if total_invoices else 0

    top_customers = sorted(customer_totals.items(), key=lambda x: x[1], reverse=True)[
        :5
    ]

    concentration_ratio = (
        sum(v for _, v in top_customers) / total_outstanding if total_outstanding else 0
    )

    return {
        "total_outstanding": total_outstanding,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_customers": len(customer_totals),
        "total_invoices": total_invoices,
        "overdue_amount": overdue_amount,
        "overdue_invoices": overdue_invoices,
        "average_invoice_amount": _format_currency(avg_invoice),
        "average_collection_days": round(avg_collection_days, 2),
        # "customer_concentration_ratio": round(concentration_ratio, 2),
        # "bad_debt_risk": ageing_91_120 + ageing_121_above,
        "ageing_summary": {
            "0_30": ageing_0_30,
            "31_60": ageing_31_60,
            "61_90": ageing_61_90,
            "91_120": ageing_91_120,
            "121_above": ageing_121_above,
        },
        "top_customers": [
            {"customer": c, "outstanding": _format_currency(v)}
            for c, v in top_customers
        ],
    }


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_accounts_receivable():

    group_by = _get_arg("group_by", "none")
    search_term = _get_arg("search", "").strip().lower()

    filters = frappe._dict(
        {
            "company": frappe.defaults.get_user_default("Company"),
            "report_date": _get_arg("report_date", today()),
            "cost_center": _get_arg("cost_center"),
            "party_account": _get_arg("party_account"),
            "party_type": _get_arg("party_type"),
            "party": _get_arg("party"),
            "customer_group": _get_arg("customer_group"),
            "ageing_based_on": _get_arg("ageing_based_on", "Due Date"),
            "calculate_ageing_with": _get_arg("calculate_ageing_with", "Today Date"),
            "range": _get_arg("range", "30, 60, 90, 120"),
            "group_by_party": 1 if group_by == "customer" else 0,
            "ignore_accounts": 1 if group_by == "voucher" else 0,
        }
    )

    filters = frappe._dict({k: v for k, v in filters.items() if v is not None})

    page = int(_get_arg("page", 1))
    page_size = int(_get_arg("page_size", 10))

    columns, raw_data, message, chart, report_summary, skip_total_row = execute(filters)

    filtered_data = []
    for row in raw_data:
        if not isinstance(row, dict):
            continue

        if search_term:
            customer = str(row.get("party") or "").lower()
            voucher_no = str(row.get("voucher_no", "") or "").lower()

            if search_term not in customer and search_term not in voucher_no:
                continue

        filtered_data.append(row)

    kpis = _calculate_receivable_kpis(filtered_data)

    rows = []

    for row in filtered_data:
        rows.append(
            {
                "posting_date": row.get("posting_date"),
                "customer": row.get("party"),
                "party_type": row.get("party_type"),
                "receivable_account": row.get("party_account"),
                "voucher_type": row.get("voucher_type"),
                "voucher_no": row.get("voucher_no"),
                "due_date": row.get("due_date"),
                "po_no": row.get("po_no"),
                "cost_center": row.get("cost_center"),
                "currency": row.get("currency"),
                "territory": row.get("territory"),
                "customer_group": row.get("customer_group"),
                "customer_contact": row.get("customer_primary_contact"),
                "amounts": {
                    "invoiced": _format_currency(row.get("invoiced")),
                    "paid": _format_currency(row.get("paid")),
                    "credit_note": _format_currency(row.get("credit_note")),
                    "outstanding": _format_currency(row.get("outstanding")),
                },
                "age": row.get("age"),
                "ageing": {
                    "0_30": _format_currency(row.get("range1")),
                    "31_60": _format_currency(row.get("range2")),
                    "61_90": _format_currency(row.get("range3")),
                    "91_120": _format_currency(row.get("range4")),
                    "121_above": _format_currency(row.get("range5")),
                },
            }
        )

    total_items = len(rows)
    total_pages = math.ceil(total_items / page_size) if page_size else 1

    start = (page - 1) * page_size
    end = start + page_size

    paginated_rows = rows[start:end]

    pagination = {
        "page": page,
        "page_size": page_size,
        "items_in_page": len(paginated_rows),
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }

    return send_response(
        status="success",
        message="Accounts Receivable fetched successfully.",
        data={
            "kpis": kpis,
            # "columns": columns,
            "data": paginated_rows,
            "summary": report_summary,
            "pagination": pagination,
        },
        status_code=200,
        http_status=200,
    )
