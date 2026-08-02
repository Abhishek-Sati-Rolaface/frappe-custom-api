import frappe
from datetime import timedelta
from frappe.utils import flt, cint, getdate, nowdate, date_diff

def get_customer_dashboard_data(year=None, dormant_days=None):
    company = frappe.defaults.get_user_default("Company") or frappe.get_default("Company")
    year = cint(year) or getdate(nowdate()).year

    if not dormant_days:
        frappe.throw("Dormant days is required")
    dormant_days = cint(dormant_days)
    if dormant_days <= 0:
        frappe.throw("Dormant days must be a positive number")
    currency = frappe.db.get_value("Company", company, "default_currency")

    return {
        "currency": currency,
        "period": {"year": year},
        "summary": get_summary(company, year, dormant_days),
        "customer_growth": get_customer_growth(company, year),
        "top_performing_customers": get_top_performing_customers(company, year),
        "new_vs_repeat": get_new_vs_repeat_customers(company, year),
        "credit_limit_utilization": get_credit_limit_utilization(company),
        "top_performers_trend": get_top_performers_trend(company, year),
        "recovery_time": get_recovery_time(company),
        "needs_attention": get_needs_attention_section(company, dormant_days),
    }



def get_total_customers():
    total = frappe.db.count("Customer", filters={"disabled": 0})
    individual = frappe.db.count("Customer", filters={"disabled": 0, "customer_type": "Individual"})
    company_type = frappe.db.count("Customer", filters={"disabled": 0, "customer_type": "Company"})

    return {
        "total": total,
        "individual": individual,
        "company": company_type,
    }

def get_overdue_payments_count(company):
    return frappe.db.count(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "company": company,
            "outstanding_amount": [">", 0],
            "due_date": ["<", nowdate()],
        },
    )

def get_dormant_customers_count(company, dormant_days):
    today = getdate(nowdate())
    cutoff_date = today - timedelta(days=dormant_days)

    rows = frappe.db.sql(
        """
        SELECT c.name AS customer_id
        FROM `tabCustomer` c
        LEFT JOIN `tabSales Invoice` si
            ON si.customer = c.name
            AND si.docstatus = 1
            AND si.company = %(company)s
        WHERE c.disabled = 0
        GROUP BY c.name
        HAVING MAX(si.posting_date) IS NULL
            OR MAX(si.posting_date) <= %(cutoff_date)s
        """,
        {"company": company, "cutoff_date": cutoff_date},
        as_dict=True,
    )

    return len(rows)

def get_revenue_summary(company, year):
    row = frappe.db.sql(
        """
        SELECT
            COUNT(*) AS invoice_count,
            COALESCE(SUM(base_grand_total), 0) AS total_revenue
        FROM `tabSales Invoice`
        WHERE docstatus = 1
            AND company = %(company)s
            AND posting_date BETWEEN %(start)s AND %(end)s
        """,
        {"company": company, "start": f"{year}-01-01", "end": f"{year}-12-31"},
        as_dict=True,
    )[0]

    invoice_count = cint(row.invoice_count)
    total_revenue = flt(row.total_revenue)
    avg_order_value = flt(total_revenue / invoice_count) if invoice_count else 0.0

    return {
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
    }

def get_avg_payment_delay_days(company):
    today = getdate(nowdate())

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "company": company,
            "outstanding_amount": [">", 0],
            "due_date": ["<", today],
        },
        fields=["due_date"],
    )

    if not invoices:
        return 0

    total_delay = sum(date_diff(today, inv.due_date) for inv in invoices)
    return round(total_delay / len(invoices))


def get_summary(company, year, dormant_days):
    revenue_data = get_revenue_summary(company, year)
    customer_counts = get_total_customers()

    return {
        "total_customers": customer_counts["total"],
        "individual_customers": customer_counts["individual"],
        "company_customers": customer_counts["company"],
        "overdue_payments": get_overdue_payments_count(company),
        "dormant_customers": get_dormant_customers_count(company, dormant_days),
        "total_revenue": revenue_data["total_revenue"],
        "avg_order_value": revenue_data["avg_order_value"],
        "avg_payment_delay_days": get_avg_payment_delay_days(company),
    }

def get_customer_growth(company, year):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    data = [{"month": m, "count": 0} for m in months]

    customers = frappe.get_all(
    "Customer",
    filters={
        "creation": ["between", [f"{year}-01-01 00:00:00", f"{year}-12-31 23:59:59"]],
    },
    fields=["creation"],
    )

    for cust in customers:
        month_idx = getdate(cust.creation).month - 1
        data[month_idx]["count"] += 1

    return data

def get_top_performing_customers(company, year, limit=5):
    rows = frappe.db.sql(
        """
        SELECT customer AS customer_id, customer_name, SUM(base_grand_total) AS revenue
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND company = %(company)s
            AND posting_date BETWEEN %(start)s AND %(end)s
        GROUP BY customer
        ORDER BY revenue DESC
        LIMIT %(limit)s
        """,
        {
            "company": company,
            "start": f"{year}-01-01",
            "end": f"{year}-12-31",
            "limit": limit,
        },
        as_dict=True,
    )

    return [
        {
            "customer_id": row.customer_id,
            "customer_name": row.customer_name,
            "revenue": flt(row.revenue),
        }
        for row in rows
    ]

def get_customer_first_order_dates(company):
    rows = frappe.db.sql(
        """
        SELECT customer, MIN(posting_date) AS first_order_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND company = %(company)s
        GROUP BY customer
        """,
        {"company": company},
        as_dict=True,
    )
    return {row.customer: row.first_order_date for row in rows}

def get_customer_revenue_for_year(company, year):
    rows = frappe.db.sql(
        """
        SELECT customer, SUM(base_grand_total) AS revenue
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND company = %(company)s
            AND posting_date BETWEEN %(start)s AND %(end)s
        GROUP BY customer
        """,
        {"company": company, "start": f"{year}-01-01", "end": f"{year}-12-31"},
        as_dict=True,
    )
    return rows

def get_new_vs_repeat_customers(company, year):
    first_order_dates = get_customer_first_order_dates(company)
    year_revenue_rows = get_customer_revenue_for_year(company, year)

    new_revenue = 0.0
    repeat_revenue = 0.0

    for row in year_revenue_rows:
        customer = row.customer
        revenue = flt(row.revenue)

        first_order_date = first_order_dates.get(customer)
        first_order_year = getdate(first_order_date).year if first_order_date else None

        if first_order_year == year:
            new_revenue += revenue
        else:
            repeat_revenue += revenue

    total_revenue = new_revenue + repeat_revenue

    return {
        "new_revenue": new_revenue,
        "repeat_revenue": repeat_revenue,
        "new_percent": round((new_revenue / total_revenue) * 100) if total_revenue else 0,
        "repeat_percent": round((repeat_revenue / total_revenue) * 100) if total_revenue else 0,
    }

def get_credit_limit_utilization(company):
    credit_limits = frappe.db.sql(
        """
        SELECT c.name AS customer_id, c.customer_name, ccl.credit_limit AS credit_limit
        FROM `tabCustomer` c
        INNER JOIN `tabCustomer Credit Limit` ccl
            ON ccl.parent = c.name AND ccl.company = %(company)s
        WHERE ccl.credit_limit > 0
        """,
        {"company": company},
        as_dict=True,
    )

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": 1, "company": company, "outstanding_amount": [">", 0]},
        fields=["customer", "outstanding_amount", "conversion_rate"],
    )

    outstanding_by_customer = {}
    for inv in invoices:
        conv_rate = flt(inv.conversion_rate) or 1.0
        base_outstanding = flt(inv.outstanding_amount) * conv_rate
        outstanding_by_customer[inv.customer] = outstanding_by_customer.get(inv.customer, 0.0) + base_outstanding

    result = []
    for row in credit_limits:
        credit_limit = flt(row.credit_limit)
        outstanding = outstanding_by_customer.get(row.customer_id, 0.0)
        utilization_percent = round((outstanding / credit_limit) * 100) if credit_limit else 0

        result.append({
            "customer_id": row.customer_id,
            "customer_name": row.customer_name,
            "credit_limit": credit_limit,
            "outstanding": outstanding,
            "utilization_percent": utilization_percent,
        })

    result.sort(key=lambda x: x["utilization_percent"], reverse=True)
    return result

def get_customer_recovery_delay(company):
    rows = frappe.db.sql(
        """
        SELECT
            pe.party AS customer_id,
            pe.party_name AS customer_name,
            AVG(DATEDIFF(pe.posting_date, per.due_date)) AS avg_delay
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per
            ON per.parent = pe.name
        WHERE pe.docstatus = 1
            AND pe.company = %(company)s
            AND pe.payment_type = 'Receive'
            AND per.reference_doctype = 'Sales Invoice'
            AND per.due_date IS NOT NULL
        GROUP BY pe.party, pe.party_name
        """,
        {"company": company},
        as_dict=True,
    )
    return rows

def get_recovery_time(company):
    rows = get_customer_recovery_delay(company)

    customers = [
        {
            "customer_id": row.customer_id,
            "customer_name": row.customer_name,
            "avg_delay_days": round(flt(row.avg_delay)),
        }
        for row in rows
    ]

    on_time = sorted(customers, key=lambda x: x["avg_delay_days"])[:5]
    late = sorted(customers, key=lambda x: x["avg_delay_days"], reverse=True)[:5]

    return {"on_time": on_time, "late": late}


def get_top_outstanding_customers(company):
    invoices = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": 1, "company": company, "outstanding_amount": [">", 0]},
        fields=["customer", "customer_name", "outstanding_amount", "conversion_rate"],
    )

    outstanding_by_customer = {}
    for inv in invoices:
        conv_rate = flt(inv.conversion_rate) or 1.0
        base_outstanding = flt(inv.outstanding_amount) * conv_rate

        if inv.customer not in outstanding_by_customer:
            outstanding_by_customer[inv.customer] = {
                "customer_id": inv.customer,
                "customer_name": inv.customer_name,
                "outstanding": 0.0,
            }
        outstanding_by_customer[inv.customer]["outstanding"] += base_outstanding

    result = list(outstanding_by_customer.values())
    result.sort(key=lambda x: x["outstanding"], reverse=True)
    return result


def get_dormant_customers_list(company, dormant_days):
    today = getdate(nowdate())
    cutoff_date = today - timedelta(days=dormant_days)

    rows = frappe.db.sql(
        """
        SELECT c.name AS customer_id, c.customer_name, MAX(si.posting_date) AS last_order_date
        FROM `tabCustomer` c
        LEFT JOIN `tabSales Invoice` si
            ON si.customer = c.name
            AND si.docstatus = 1
            AND si.company = %(company)s
        WHERE c.disabled = 0
        GROUP BY c.name, c.customer_name
        HAVING MAX(si.posting_date) IS NULL
            OR MAX(si.posting_date) <= %(cutoff_date)s
        """,
        {"company": company, "cutoff_date": cutoff_date},
        as_dict=True,
    )

    result = []
    for row in rows:
        if row.last_order_date:
            days_inactive = date_diff(today, row.last_order_date)
        else:
            days_inactive = None  # never ordered

        result.append({
            "customer_id": row.customer_id,
            "customer_name": row.customer_name,
            "last_order_days_ago": days_inactive,
        })

    result.sort(key=lambda x: (x["last_order_days_ago"] is None, x["last_order_days_ago"]), reverse=True)
    return result

def get_needs_attention_section(company, dormant_days):
    return {
        "dormant_customers": get_dormant_customers_list(company, dormant_days),
        "top_outstanding_customers": get_top_outstanding_customers(company),
    }


def get_top_performers_trend(company, year):
    top_3 = get_top_performing_customers(company, year, limit=3)
    customer_ids = [c["customer_id"] for c in top_3]
    customer_names = [c["customer_name"] for c in top_3]

    if not customer_ids:
        return {"customers": [], "series": []}

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "company": company,
            "customer": ["in", customer_ids],
            "posting_date": ["between", [f"{year}-01-01", f"{year}-12-31"]],
        },
        fields=["customer", "posting_date", "base_grand_total"],
    )

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    series = []
    for month in months:
        row = {"month": month}
        for name in customer_names:
            row[name] = 0.0
        series.append(row)

    customer_id_to_name = dict(zip(customer_ids, customer_names))

    for inv in invoices:
        month_idx = getdate(inv.posting_date).month - 1
        customer_name = customer_id_to_name.get(inv.customer)
        if customer_name:
            series[month_idx][customer_name] += flt(inv.base_grand_total)

    return {
        "customers": customer_names,
        "series": series,
    }