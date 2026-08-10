"""
custom_api/api/payment.py

Payment Entry APIs for Sales Order advance payments.
Dotted path: custom_api.api.payment
"""

import frappe
from frappe import _
from frappe.utils import flt, nowdate, get_datetime, cint
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from erpnext.setup.utils import get_exchange_rate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sales_order(sales_order):
    so = frappe.db.get_value(
        "Sales Order",
        sales_order,
        [
            "name", "docstatus", "company", "customer", "currency",
            "conversion_rate", "per_billed", "advance_paid",
            "rounded_total", "grand_total", "status", "skip_delivery_note",
        ],
        as_dict=True,
    )
    if not so:
        frappe.throw(_("Sales Order {0} not found").format(sales_order), frappe.DoesNotExistError)
    return so


def _validate_permissions(sales_order_doc):
    # Read permission on the SO itself
    if not frappe.has_permission("Sales Order", "read", sales_order_doc.name):
        frappe.throw(_("Not permitted to read Sales Order {0}").format(sales_order_doc.name),
                     frappe.PermissionError)

    # Create permission on Payment Entry
    if not frappe.has_permission("Payment Entry", "create"):
        frappe.throw(_("Not permitted to create Payment Entry"), frappe.PermissionError)


def _validate_mode_of_payment(mode_of_payment, company):
    if not mode_of_payment:
        return
    exists = frappe.db.exists("Mode of Payment", mode_of_payment)
    if not exists:
        frappe.throw(_("Mode of Payment {0} does not exist").format(mode_of_payment))

    # Mode of Payment must have a default account for this company, else
    # Payment Entry will throw on submit with a confusing error.
    has_account = frappe.db.exists(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": company},
    )
    if not has_account:
        frappe.throw(
            _("Mode of Payment {0} has no default account set for company {1}. "
              "Set it in Mode of Payment > Accounts table.").format(mode_of_payment, company)
        )


def _validate_advance_account_setup(company, party_type="Customer"):
    """
    If 'book_advance_payments_in_separate_party_account' is enabled at company
    level, a default advance account must exist (on the party or company),
    otherwise Payment Entry.insert() will throw a raw, unhelpful error.
    """
    book_separately = frappe.db.get_value(
        "Company", company, "book_advance_payments_in_separate_party_account"
    )
    if not book_separately:
        return

    default_advance_account = frappe.db.get_value(
        "Company", company, "default_advance_received_account"
    )
    if not default_advance_account:
        frappe.throw(
            _("Company {0} has 'Book Advance Payments in Separate Party Account' enabled "
              "but no Default Advance Received Account is set.").format(company)
        )


def _check_duplicate_reference(reference_no, party, sales_order):
    """Avoid accidentally double-booking the same transaction reference."""
    if not reference_no:
        return
    existing = frappe.db.exists(
        "Payment Entry",
        {
            "reference_no": reference_no,
            "party": party,
            "docstatus": ["!=", 2],
        },
    )
    if existing:
        frappe.throw(
            _("A Payment Entry {0} already exists with reference number {1} for this party. "
              "Use a unique reference number, or check for a duplicate submission.")
            .format(existing, reference_no)
        )


def _get_outstanding_amount(so):
    outstanding = flt(so.rounded_total or so.grand_total) - flt(so.advance_paid)
    return flt(outstanding, 2)


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_advance_summary(sales_order):
    """
    Fetch advance/outstanding summary for a Sales Order before creating
    a Payment Entry — lets the frontend show correct amounts and validate
    input client-side.
    """
    so = _get_sales_order(sales_order)
    _validate_permissions(so)

    if so.docstatus != 1:
        frappe.throw(_("Sales Order {0} must be submitted").format(sales_order))

    outstanding = _get_outstanding_amount(so)

    return {
        "sales_order": so.name,
        "customer": so.customer,
        "company": so.company,
        "currency": so.currency,
        "grand_total": flt(so.rounded_total or so.grand_total),
        "advance_paid": flt(so.advance_paid),
        "outstanding_amount": outstanding,
        "per_billed": flt(so.per_billed),
        "fully_billed": flt(so.per_billed) >= 100,
        "status": so.status,
    }


@frappe.whitelist()
def create_advance_payment_from_so(
    sales_order,
    paid_amount=None,
    mode_of_payment=None,
    reference_no=None,
    reference_date=None,
    paid_to=None,
    remarks=None,
    submit=0,
):
    """
    Create an advance Payment Entry against a Sales Order, with the full
    set of checks Frappe/ERPNext expects before this can safely submit.

    Args:
        sales_order (str): Sales Order name
        paid_amount (float, optional): Advance amount. Defaults to full outstanding.
        mode_of_payment (str, optional): e.g. "Cash", "Bank Transfer"
        reference_no (str, optional): Cheque/UTR/transaction reference
        reference_date (str, optional): Reference date, defaults to today
        paid_to (str, optional): Override receiving account (defaults from Mode of Payment)
        remarks (str, optional): Custom remarks
        submit (int/bool, optional): If truthy, submits the Payment Entry

    Returns:
        dict: created Payment Entry summary
    """
    submit = cint(submit)

    if not sales_order:
        frappe.throw(_("Sales Order is required"))

    so = _get_sales_order(sales_order)
    _validate_permissions(so)

    if so.docstatus != 1:
        frappe.throw(_("Sales Order {0} must be submitted before creating a Payment Entry")
                     .format(sales_order))

    if flt(so.per_billed) >= 100:
        frappe.throw(_("Sales Order {0} is fully billed. Advance payment against it is not applicable")
                     .format(sales_order))

    outstanding = _get_outstanding_amount(so)
    if outstanding <= 0:
        frappe.throw(_("Sales Order {0} has no outstanding amount to collect advance against")
                     .format(sales_order))

    paid_amount = flt(paid_amount) if paid_amount else outstanding

    if paid_amount <= 0:
        frappe.throw(_("Paid amount must be greater than zero"))

    # Allow small rounding tolerance (2 currency units) but block gross over-collection
    if paid_amount > outstanding + 2:
        frappe.throw(
            _("Paid amount {0} cannot exceed outstanding amount {1} for Sales Order {2}")
            .format(paid_amount, outstanding, sales_order)
        )

    _validate_mode_of_payment(mode_of_payment, so.company)
    _validate_advance_account_setup(so.company)
    _check_duplicate_reference(reference_no, so.customer, sales_order)

    try:
        pe = get_payment_entry("Sales Order", sales_order)

        pe.payment_type = "Receive"
        pe.posting_date = nowdate()
        pe.reference_no = reference_no or f"ADV-{sales_order}-{frappe.generate_hash(length=6)}"
        pe.reference_date = reference_date or nowdate()

        if mode_of_payment:
            pe.mode_of_payment = mode_of_payment

        if paid_to:
            if not frappe.db.exists("Account", paid_to):
                frappe.throw(_("Account {0} does not exist").format(paid_to))
            pe.paid_to = paid_to

        if remarks:
            pe.remarks = remarks

        # Multi-currency: re-fetch exchange rate if party currency differs
        # from company currency, so paid_amount/received_amount don't drift.
        company_currency = frappe.db.get_value("Company", so.company, "default_currency")
        if so.currency != company_currency:
            rate = get_exchange_rate(so.currency, company_currency, nowdate())
            pe.source_exchange_rate = rate
            pe.target_exchange_rate = rate

        pe.paid_amount = paid_amount
        pe.received_amount = paid_amount

        # Re-sync allocation on the SO reference row so it matches paid_amount
        for ref in pe.references:
            if ref.reference_doctype == "Sales Order" and ref.reference_name == sales_order:
                ref.allocated_amount = paid_amount

        pe.setup_party_account_field()
        pe.set_missing_values()
        pe.validate()

        pe.insert(ignore_permissions=False)

        if submit:
            pe.submit()

        frappe.db.commit()

    except frappe.ValidationError:
        frappe.db.rollback()
        raise
    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            title="create_advance_payment_from_so failed",
            message=frappe.get_traceback(),
        )
        frappe.throw(_("Failed to create Payment Entry. Error has been logged."))

    return {
        "name": pe.name,
        "docstatus": pe.docstatus,
        "status": "Submitted" if pe.docstatus == 1 else "Draft",
        "party": pe.party,
        "paid_amount": pe.paid_amount,
        "reference_no": pe.reference_no,
        "sales_order": sales_order,
        "outstanding_after": flt(outstanding - paid_amount, 2),
    }


@frappe.whitelist()
def cancel_advance_payment(payment_entry):
    """
    Cancel an advance Payment Entry linked to a Sales Order.
    Wraps standard cancel with permission + link-status checks.
    """
    if not frappe.has_permission("Payment Entry", "cancel", payment_entry):
        frappe.throw(_("Not permitted to cancel Payment Entry {0}").format(payment_entry),
                     frappe.PermissionError)

    pe = frappe.get_doc("Payment Entry", payment_entry)

    if pe.docstatus != 1:
        frappe.throw(_("Only submitted Payment Entries can be cancelled"))

    try:
        pe.cancel()
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(title="cancel_advance_payment failed", message=frappe.get_traceback())
        frappe.throw(_("Failed to cancel Payment Entry. It may be linked to a submitted "
                        "Sales Invoice or Journal Entry. Error has been logged."))

    return {"name": pe.name, "docstatus": pe.docstatus, "status": "Cancelled"}