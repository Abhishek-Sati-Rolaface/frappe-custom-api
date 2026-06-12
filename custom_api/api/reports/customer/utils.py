def get_pdf_html_template():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            /* Reset & Base Typography */
            body { 
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
                font-size: 12px; 
                color: #334155; 
                line-height: 1.5;
                margin: 0;
                padding: 0;
            }
            h1, h2, h3, p { margin: 0; padding: 0; }
            
            /* Helper Classes */
            .text-right { text-align: right !important; }
            .text-left { text-align: left !important; }
            .font-bold { font-weight: 700 !important; }
            .text-muted { color: #64748b !important; }

            /* Header Section */
            .header {
                width: 100%;
                margin-bottom: 30px;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 20px;
            }
            .header-table {
                width: 100%;
                border-collapse: collapse;
            }
            .header-table td {
                vertical-align: top;
            }
            .title {
                font-size: 24px;
                font-weight: bold;
                color: #0f172a;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }

            /* Info Blocks */
            .info-block { margin-bottom: 5px; }
            .info-label { font-size: 10px; text-transform: uppercase; color: #94a3b8; font-weight: bold; }
            .info-value { font-size: 13px; color: #0f172a; font-weight: 600; }

            /* Summary Cards (Table Layout for PDF Engine Safety) */
            .summary-container {
                width: 100%;
                margin-bottom: 30px;
                border-collapse: collapse;
            }
            .summary-box {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                padding: 15px;
                text-align: center;
                width: 33.33%;
            }
            .summary-title {
                font-size: 10px;
                text-transform: uppercase;
                color: #64748b;
                font-weight: 700;
                margin-bottom: 5px;
            }
            .summary-amount {
                font-size: 16px;
                font-weight: bold;
                color: #0f172a;
            }

            /* Ledger Table */
            table.ledger {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            table.ledger th {
                background-color: #f1f5f9;
                color: #475569;
                font-size: 10px;
                text-transform: uppercase;
                padding: 12px 8px;
                border-bottom: 2px solid #cbd5e1;
                text-align: left;
            }
            table.ledger td {
                padding: 10px 8px;
                border-bottom: 1px solid #f1f5f9;
                font-size: 11px;
                vertical-align: middle;
            }
            /* Zebra striping for readability */
            table.ledger tbody tr:nth-child(even) { background-color: #fafafa; }
            table.ledger tbody tr:last-child td { border-bottom: 2px solid #cbd5e1; }
        </style>
    </head>
    <body>

        <div class="header">
            <table class="header-table">
                <tr>
                    <td style="width: 50%;">
                        <div class="title">Statement of Account</div>
                        
                        <div class="info-block" style="margin-top: 15px;">
                            <div class="info-label">Customer</div>
                            <div class="info-value">{{ customer.customer_name or customer.name }}</div>
                            <div style="font-size: 11px; color: #64748b;">ID: {{ customer.name }}</div>
                        </div>
                    </td>
                    <td style="width: 50%; text-align: right;">
                        <div class="info-block" style="margin-top: 40px;">
                            <div class="info-label">Statement Period</div>
                            <div class="info-value">
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
                        </div>
                        <div class="info-block" style="margin-top: 10px;">
                            <div class="info-label">Date Generated</div>
                            <div class="info-value">{{ frappe.utils.formatdate(frappe.utils.nowdate()) }}</div>
                        </div>
                    </td>
                </tr>
            </table>
        </div>

        <table class="summary-container">
            <tr>
                <td class="summary-box" style="border-right: none;">
                    <div class="summary-title">Total Invoiced</div>
                    <div class="summary-amount">{{ frappe.format_value(summary.totalInvoiced, {"fieldtype":"Currency"}) }}</div>
                </td>
                <td class="summary-box" style="border-right: none;">
                    <div class="summary-title">Total Collected</div>
                    <div class="summary-amount">{{ frappe.format_value(summary.totalCollected, {"fieldtype":"Currency"}) }}</div>
                </td>
                <td class="summary-box">
                    <div class="summary-title">Net Outstanding</div>
                    <div class="summary-amount">{{ frappe.format_value(summary.netOutstanding, {"fieldtype":"Currency"}) }}</div>
                </td>
            </tr>
        </table>

        <table class="ledger">
            <thead>
                <tr>
                    <th style="width: 12%;">Date</th>
                    <th style="width: 20%;">Type</th>
                    <th style="width: 20%;">Reference</th>
                    <th class="text-right" style="width: 16%;">Debit</th>
                    <th class="text-right" style="width: 16%;">Credit</th>
                    <th class="text-right" style="width: 16%;">Balance</th>
                </tr>
            </thead>
            <tbody>
            {% for row in ledger %}
                <tr>
                    <td>{{ frappe.utils.formatdate(row.date) }}</td>
                    <td><span class="text-muted">{{ row.type }}</span></td>
                    <td class="font-bold">{{ row.ref }}</td>
                    <td class="text-right">{{ frappe.format_value(row.debit, {"fieldtype":"Currency"}) if row.debit else '-' }}</td>
                    <td class="text-right">{{ frappe.format_value(row.credit, {"fieldtype":"Currency"}) if row.credit else '-' }}</td>
                    <td class="text-right font-bold">{{ frappe.format_value(row.balance, {"fieldtype":"Currency"}) }}</td>
                </tr>
            {% else %}
                <tr>
                    <td colspan="6" style="text-align: center; padding: 30px; color: #94a3b8;">
                        No transactions found for this period.
                    </td>
                </tr>
            {% endfor %}
            </tbody>
        </table>

    </body>
    </html>
    """