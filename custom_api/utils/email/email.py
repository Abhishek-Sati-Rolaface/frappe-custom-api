import frappe


def get_routed_email_account(reference_doctype=None):

    if not reference_doctype:
        return None

    email_accounts = frappe.get_all(
        "Email Account",
        filters={"enable_outgoing": 1},
        pluck="name"
    )

    for email_account in email_accounts:

        account_doc = frappe.get_cached_doc(
            "Email Account",
            email_account
        )

        mappings = account_doc.custom_document_email_mapping or []

        for row in mappings:

            if row.reference_doctype != reference_doctype:
                continue

            return account_doc

    return None

def sendmail(*args, **kwargs):

    reference_doctype = kwargs.get("reference_doctype")

    email_account = get_routed_email_account(reference_doctype)

    # Inject sender
    if email_account:
        kwargs["sender"] = email_account.email_id
        # kwargs["sender_full_name"] = email_account.email_account_name
        frappe.local.outgoing_email_account = email_account

    return frappe._original_sendmail(*args, **kwargs)