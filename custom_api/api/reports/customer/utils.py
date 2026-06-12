def get_pdf_html_template():
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">

    <style>
    *{
        margin:0;
        padding:0;
        box-sizing:border-box;
    }

    body{
        font-family:Arial,Helvetica,sans-serif;
        font-size:11px;
        color:#334155;
        padding:20px;
        line-height:1.5;
        background:#ffffff;
    }

    .text-right{
        text-align:right;
    }

    .header{
        width:100%;
        margin-bottom:24px;
        border-bottom:2px solid #e2e8f0;
        padding-bottom:18px;
    }

    .header-table{
        width:100%;
        border-collapse:collapse;
    }

    .company-name{
        font-size:24px;
        font-weight:700;
        color:#0f172a;
        margin-bottom:4px;
    }

    .company-meta{
        color:#64748b;
        font-size:11px;
    }

    .statement-title{
        font-size:26px;
        font-weight:700;
        color:#0f172a;
        text-transform:uppercase;
        letter-spacing:1px;
    }

    .statement-date{
        color:#64748b;
        margin-top:6px;
    }

    .customer-card{
        width:100%;
        border:1px solid #e2e8f0;
        background:#f8fafc;
        border-radius:8px;
        padding:16px;
        margin-bottom:24px;
    }

    .customer-table{
        width:100%;
        border-collapse:collapse;
    }

    .label{
        font-size:10px;
        color:#94a3b8;
        font-weight:700;
        text-transform:uppercase;
    }

    .value{
        font-size:14px;
        color:#0f172a;
        font-weight:700;
        margin-top:4px;
    }

    .muted{
        color:#64748b;
        font-size:11px;
    }

    .metrics{
        width:100%;
        border-collapse:separate;
        border-spacing:8px;
        margin-bottom:24px;
    }

    .metric{
        border:1px solid #e2e8f0;
        border-radius:8px;
        padding:16px;
        background:#ffffff;
    }

    .metric.invoiced{ background:#f8fafc; }
    .metric.collected{ background:#f0fdf4; }
    .metric.outstanding{ background:#eff6ff; }
    .metric.overdue{ background:#fef2f2; }

    .metric-label{
        font-size:10px;
        text-transform:uppercase;
        color:#64748b;
        font-weight:700;
    }

    .metric-value{
        margin-top:8px;
        font-size:20px;
        font-weight:700;
        color:#0f172a;
    }

    .section-title{
        font-size:16px;
        font-weight:700;
        color:#0f172a;
        margin-bottom:12px;
    }

    .ledger{
        width:100%;
        border-collapse:collapse;
    }

    .ledger thead{ display:table-header-group; }

    .ledger th{
        background:#f8fafc;
        color:#475569;
        text-transform:uppercase;
        font-size:10px;
        padding:12px 10px;
        border-bottom:2px solid #cbd5e1;
        text-align:left;
    }

    .ledger td{
        padding:12px 10px;
        border-bottom:1px solid #e2e8f0;
        vertical-align:middle;
    }

    .ledger tbody tr:nth-child(even){ background:#fafafa; }

    .badge{
        padding:4px 8px;
        border-radius:12px;
        font-size:10px;
        font-weight:700;
        white-space:nowrap;
    }

    .invoice{ background:#dbeafe; color:#1d4ed8; }
    .payment{ background:#dcfce7; color:#15803d; }
    .credit-note{ background:#fef3c7; color:#b45309; }
    .journal{ background:#ede9fe; color:#6d28d9; }

    .debit{ color:#dc2626; font-weight:700; }
    .credit{ color:#16a34a; font-weight:700; }
    .balance{ color:#0f172a; font-weight:700; }

    .footer{
        margin-top:24px;
        padding-top:12px;
        border-top:1px solid #e2e8f0;
        text-align:center;
        color:#94a3b8;
        font-size:10px;
    }
    </style>
    </head>

    <body>

    <div class="header">
        <table class="header-table">
            <tr>
                {% set company = frappe.get_doc(
                    "Company",
                    frappe.defaults.get_user_default("Company")
                ) %}

                <td style="width:50%;">
                    <div class="company-name">
                        {{ company.company_name }}
                    </div>

                    <div class="company-meta">

                        {% if company.tax_id %}
                            Tax ID: {{ company.tax_id }}<br>
                        {% endif %}

                        {% if company.email %}
                            {{ company.email }}<br>
                        {% endif %}

                        {% if company.phone_no %}
                            {{ company.phone_no }}<br>
                        {% endif %}

                        {% if company.company_address %}
                            {{ company.company_address }}
                        {% endif %}

                    </div>
                </td>
                <td style="width:50%;" align="right">
                    <div class="statement-title">
                        Customer Statement
                    </div>
                    <div class="statement-date">
                        Generated on {{ frappe.utils.formatdate(frappe.utils.nowdate()) }}
                    </div>
                </td>
            </tr>
        </table>
    </div>

    <div class="customer-card">
        <table class="customer-table">
            <tr>
                <td width="50%">
                <div class="label">Customer</div>
                <div class="value">{{ customer.customer_name or customer.name }}</div>
                <div class="muted">
                    Tax ID: {{ customer.tax_id or "-" }}
                </div>
            </td>
                <td width="50%" align="right">
                    <div class="label">Statement Period</div>
                    <div class="value">
                        {% if from_date and to_date %}
                            {{ frappe.utils.formatdate(from_date) }} to {{ frappe.utils.formatdate(to_date) }}
                        {% elif from_date %}
                            From {{ frappe.utils.formatdate(from_date) }}
                        {% elif to_date %}
                            Up to {{ frappe.utils.formatdate(to_date) }}
                        {% else %}
                            All Time
                        {% endif %}
                    </div>
                </td>
            </tr>
        </table>
    </div>

    <table class="metrics">
        <tr>
            <td class="metric invoiced">
                <div class="metric-label">Total Invoiced</div>
                <div class="metric-value">{{ frappe.format_value(summary.totalInvoiced, {"fieldtype":"Currency"}) }}</div>
            </td>
            <td class="metric collected">
                <div class="metric-label">Total Collected</div>
                <div class="metric-value">{{ frappe.format_value(summary.totalCollected, {"fieldtype":"Currency"}) }}</div>
            </td>
            <td class="metric outstanding">
                <div class="metric-label">Outstanding</div>
                <div class="metric-value">{{ frappe.format_value(summary.netOutstanding, {"fieldtype":"Currency"}) }}</div>
            </td>
            <td class="metric overdue">
                <div class="metric-label">Overdue</div>
                <div class="metric-value">
                    {% set overdue_amount = (summary.netOutstanding if not aging else (aging.get('1_30', 0) + aging.get('31_60', 0) + aging.get('61_90', 0) + aging.get('90_plus', 0))) %}
                    {{ frappe.format_value(overdue_amount, {"fieldtype":"Currency"}) }}
                </div>
            </td>
        </tr>
    </table>

    <div class="section-title">
        Transaction History
    </div>

    <table class="ledger">
        <thead>
            <tr>
                <th style="width:10%">Date</th>
                <th style="width:12%">Type</th>
                <th style="width:14%">Reference</th>
                <th style="width:28%">Remarks</th>
                <th style="width:12%" class="text-right">Debit</th>
                <th style="width:12%" class="text-right">Credit</th>
                <th style="width:12%" class="text-right">Balance</th>
            </tr>
        </thead>
        <tbody>
        {% for row in ledger %}
            <tr>
                <td>{{ frappe.utils.formatdate(row.date) }}</td>
                <td>
                    {% if row.type == 'Sales Invoice' %}
                        <span class="badge invoice">Invoice</span>
                    {% elif row.type == 'Payment Entry' %}
                        <span class="badge payment">Payment</span>
                    {% elif row.type == 'Journal Entry' %}
                        <span class="badge journal">Journal</span>
                    {% else %}
                        <span class="badge credit-note">{{ row.type }}</span>
                    {% endif %}
                </td>
                <td>{{ row.ref }}</td>
                <td>{{ row.note or '-' }}</td>
                
                <td class="text-right {% if row.debit %}debit{% endif %}">
                    {{ frappe.format_value(row.debit, {"fieldtype":"Currency"}) if row.debit else '-' }}
                </td>
                
                <td class="text-right {% if row.credit %}credit{% endif %}">
                    {{ frappe.format_value(row.credit, {"fieldtype":"Currency"}) if row.credit else '-' }}
                </td>
                
                <td class="text-right balance">
                    {{ frappe.format_value(row.balance, {"fieldtype":"Currency"}) }}
                </td>
            </tr>
        {% else %}
            <tr>
                <td colspan="7" style="text-align: center; padding: 30px; color: #94a3b8;">
                    No transactions found for this period.
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

    <div class="footer">
        This is a system generated customer statement and does not require a signature.
    </div>

    </body>
    </html>
    """
