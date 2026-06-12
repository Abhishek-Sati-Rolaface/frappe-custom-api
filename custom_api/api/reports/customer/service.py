import frappe
from frappe.query_builder import DocType
import frappe.query_builder.functions as fn
from frappe.utils import nowdate, date_diff, getdate

def get_customer_statement_data(customer_id, from_date=None, to_date=None, page=None, page_size=None, voucher_type=None, search_term=None):
    customer_summary = _get_customer_summary(customer_id, from_date, to_date)
    customer_summary["netOutstanding"] = customer_summary["totalInvoiced"] - customer_summary["totalCollected"]

    ledger_details = _get_ledger_entries(
        customer_id=customer_id, 
        from_date=from_date, 
        to_date=to_date, 
        page=page, 
        page_size=page_size,
        voucher_type=voucher_type,
        search_term=search_term
    )

    return {
        "summary": customer_summary,
        "aging": _get_aging_details(customer_id, to_date),
        "ledger": ledger_details.get("ledger"),
        "pagination": ledger_details.get("pagination")
    }

def _get_customer_summary(customer_id, from_date, to_date):
    sales_invoice_table = DocType("Sales Invoice")
    payment_entry_table = DocType("Payment Entry")
    payment_reference_table = DocType("Payment Entry Reference")
    general_ledger_table = DocType("GL Entry")

    sales_invoice_query = frappe.qb.from_(sales_invoice_table).select(
        fn.Count(sales_invoice_table.name).as_("total_invoiced_count"),
        fn.Coalesce(fn.Sum(sales_invoice_table.grand_total), 0).as_("total_invoiced_amount")
    ).where(
        (sales_invoice_table.customer == customer_id) & 
        (sales_invoice_table.docstatus == 1)
    )

    if from_date:
        sales_invoice_query = sales_invoice_query.where(sales_invoice_table.posting_date >= from_date)
    if to_date:
        sales_invoice_query = sales_invoice_query.where(sales_invoice_table.posting_date <= to_date)
    
    sales_invoice_summary = sales_invoice_query.run(as_dict=True)[0]

    payment_entry_query = frappe.qb.from_(payment_reference_table).inner_join(payment_entry_table).on(
        payment_entry_table.name == payment_reference_table.parent
    ).select(
        fn.Coalesce(fn.Sum(payment_reference_table.allocated_amount), 0)
    ).where(
        (payment_entry_table.docstatus == 1) & 
        (payment_reference_table.reference_doctype == 'Sales Invoice') &
        (payment_reference_table.reference_name.isin(
            frappe.qb.from_(sales_invoice_table).select(sales_invoice_table.name).where(
                (sales_invoice_table.customer == customer_id) & 
                (sales_invoice_table.docstatus == 1)
            )
        ))
    )

    if from_date:
        payment_entry_query = payment_entry_query.where(payment_entry_table.posting_date >= from_date)
    if to_date:
        payment_entry_query = payment_entry_query.where(payment_entry_table.posting_date <= to_date)
    
    payment_entry_summary = payment_entry_query.run()
    total_collected_amount = payment_entry_summary[0][0] if payment_entry_summary and payment_entry_summary[0] else 0

    general_ledger_query = frappe.qb.from_(general_ledger_table).select(
        fn.Coalesce(fn.Sum(general_ledger_table.debit_in_account_currency), 0).as_("total_debit"),
        fn.Coalesce(fn.Sum(general_ledger_table.credit_in_account_currency), 0).as_("total_credit")
    ).where(
        (general_ledger_table.party_type == 'Customer') & 
        (general_ledger_table.party == customer_id) & 
        (general_ledger_table.is_cancelled == 0)
    )

    if from_date:
        general_ledger_query = general_ledger_query.where(general_ledger_table.posting_date >= from_date)
    if to_date:
        general_ledger_query = general_ledger_query.where(general_ledger_table.posting_date <= to_date)

    general_ledger_summary = general_ledger_query.run(as_dict=True)[0]

    return {
        "totalInvoices": sales_invoice_summary.get("total_invoiced_count", 0),
        "totalInvoiced": sales_invoice_summary.get("total_invoiced_amount", 0),
        "totalCollected": total_collected_amount,
        "totalDebit": general_ledger_summary.get("total_debit", 0),
        "totalCredit": general_ledger_summary.get("total_credit", 0)
    }

def _get_aging_details(customer_id, to_date):
    aging_reference_date = to_date or nowdate()
    aging_buckets = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "90_plus": 0}

    outstanding_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "customer": customer_id,
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "posting_date": ["<=", aging_reference_date]
        },
        fields=["due_date", "outstanding_amount"]
    )

    current_date_object = getdate(aging_reference_date)

    for invoice_record in outstanding_invoices:
        invoice_due_date = invoice_record.get("due_date") or current_date_object
        invoice_outstanding_amount = invoice_record.get("outstanding_amount", 0)
        days_overdue = date_diff(current_date_object, invoice_due_date)

        if days_overdue <= 0:
            aging_buckets["current"] += invoice_outstanding_amount
        elif days_overdue <= 30:
            aging_buckets["1_30"] += invoice_outstanding_amount
        elif days_overdue <= 60:
            aging_buckets["31_60"] += invoice_outstanding_amount
        elif days_overdue <= 90:
            aging_buckets["61_90"] += invoice_outstanding_amount
        else:
            aging_buckets["90_plus"] += invoice_outstanding_amount

    return aging_buckets

def _get_ledger_entries(customer_id, from_date, to_date, page, page_size, voucher_type=None, search_term=None):
    general_ledger_table = DocType("GL Entry")
    
    query_conditions = [
        general_ledger_table.party_type == 'Customer',
        general_ledger_table.party == customer_id,
        general_ledger_table.is_cancelled == 0
    ]
    
    if from_date: 
        query_conditions.append(general_ledger_table.posting_date >= from_date)
    if to_date: 
        query_conditions.append(general_ledger_table.posting_date <= to_date)
        
    if voucher_type:
        if isinstance(voucher_type, list):
            query_conditions.append(general_ledger_table.voucher_type.isin(voucher_type))
        else:
            query_conditions.append(general_ledger_table.voucher_type == voucher_type)
            
    if search_term:
        search_wildcard = f"%{search_term}%"
        matched_voucher_names = []
        
        # Smart Search: Pre-fetch vouchers where the user's search matches the remarks field
        matched_voucher_names.extend(frappe.get_all("Sales Invoice", filters={"remarks": ["like", search_wildcard]}, pluck="name") or [])
        matched_voucher_names.extend(frappe.get_all("Payment Entry", filters={"remarks": ["like", search_wildcard]}, pluck="name") or [])
        matched_voucher_names.extend(frappe.get_all("Journal Entry", filters={"user_remark": ["like", search_wildcard]}, pluck="name") or [])
        
        if matched_voucher_names:
            query_conditions.append(
                (general_ledger_table.voucher_no.like(search_wildcard)) | 
                (general_ledger_table.voucher_no.isin(matched_voucher_names))
            )
        else:
            query_conditions.append(general_ledger_table.voucher_no.like(search_wildcard))

    count_query = frappe.qb.from_(general_ledger_table).select(fn.Count(general_ledger_table.name))
    for condition in query_conditions:
        count_query = count_query.where(condition)
    
    total_ledger_entries_count = count_query.run()[0][0] or 0
    
    limit_page_length = page_size if page and page_size else 0
    limit_start_offset = ((page - 1) * page_size) if page and page_size else 0

    main_ledger_query = frappe.qb.from_(general_ledger_table).select(
        general_ledger_table.posting_date,
        general_ledger_table.voucher_type,
        general_ledger_table.voucher_no,
        general_ledger_table.debit_in_account_currency.as_("debit_amount"),
        general_ledger_table.credit_in_account_currency.as_("credit_amount")
    ).orderby(general_ledger_table.posting_date).orderby(general_ledger_table.creation)
    
    for condition in query_conditions:
        main_ledger_query = main_ledger_query.where(condition)
        
    if limit_page_length:
        main_ledger_query = main_ledger_query.limit(limit_page_length).offset(limit_start_offset)
        
    general_ledger_rows = main_ledger_query.run(as_dict=True)

    running_account_balance = 0

    if limit_start_offset > 0:
        inner_balance_query = frappe.qb.from_(general_ledger_table).select(
            general_ledger_table.debit_in_account_currency.as_("debit_amount"),
            general_ledger_table.credit_in_account_currency.as_("credit_amount")
        ).orderby(general_ledger_table.posting_date).orderby(general_ledger_table.creation).limit(limit_start_offset)
        
        for condition in query_conditions:
            inner_balance_query = inner_balance_query.where(condition)
            
        compiled_inner_sql = inner_balance_query.get_sql()
        
        balance_result = frappe.db.sql(f"""
            SELECT COALESCE(SUM(debit_amount - credit_amount), 0) 
            FROM ({compiled_inner_sql}) as previous_entries_subquery
        """)
        running_account_balance = balance_result[0][0] if balance_result else 0

    voucher_remarks_mapping = _get_voucher_remarks(general_ledger_rows)
    formatted_ledger_list = []

    for ledger_row in general_ledger_rows:
        row_debit_amount = ledger_row.get("debit_amount") or 0
        row_credit_amount = ledger_row.get("credit_amount") or 0
        running_account_balance += row_debit_amount - row_credit_amount

        formatted_ledger_list.append({
            "date": ledger_row.get("posting_date"),
            "type": ledger_row.get("voucher_type"),
            "ref": ledger_row.get("voucher_no"),
            "debit": row_debit_amount,
            "credit": row_credit_amount,
            "balance": running_account_balance,
            "note": voucher_remarks_mapping.get(ledger_row.get("voucher_no"), "")
        })

    pagination_metadata = None
    if page and page_size:
        calculated_total_pages = (total_ledger_entries_count + page_size - 1) // page_size
        pagination_metadata = {
            "page": page,
            "page_size": page_size,
            "total": total_ledger_entries_count,
            "total_pages": calculated_total_pages,
            "has_next": page < calculated_total_pages,
            "has_prev": page > 1
        }

    return {"ledger": formatted_ledger_list, "pagination": pagination_metadata}

def _get_voucher_remarks(general_ledger_rows):
    categorized_vouchers = {
        "Sales Invoice": [], 
        "Payment Entry": [], 
        "Journal Entry": []
    }
    
    for ledger_row in general_ledger_rows:
        row_voucher_type = ledger_row.get("voucher_type")
        if row_voucher_type in categorized_vouchers:
            categorized_vouchers[row_voucher_type].append(ledger_row.get("voucher_no"))

    consolidated_remarks = {}
    doctype_to_remark_field_mapping = {
        "Sales Invoice": "remarks",
        "Payment Entry": "remarks",
        "Journal Entry": "user_remark"
    }

    for specific_doctype, specific_remark_field in doctype_to_remark_field_mapping.items():
        if categorized_vouchers[specific_doctype]:
            fetched_records = frappe.get_all(
                specific_doctype, 
                filters={"name": ["in", categorized_vouchers[specific_doctype]]}, 
                fields=["name", specific_remark_field]
            )
            consolidated_remarks.update({
                record.name: record.get(specific_remark_field) 
                for record in fetched_records
            })

    return consolidated_remarks