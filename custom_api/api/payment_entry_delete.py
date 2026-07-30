import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def delete_payment_entry(payment_entry_name=None, payment_entries=None):
    """
    Delete (cancel + delete) one or more Payment Entries.

    Args:
        payment_entry_name (str): Single Payment Entry name (for single delete)
        payment_entries (str/list): JSON list or list of Payment Entry names (for bulk delete)

    Returns:
        dict: summary with success/failed lists
    """

    # normalize input into a list
    names = []
    if payment_entries:
        if isinstance(payment_entries, str):
            names = frappe.parse_json(payment_entries)
        else:
            names = payment_entries
    elif payment_entry_name:
        names = [payment_entry_name]
    else:
        frappe.throw(_("Please provide payment_entry_name or payment_entries"))

    if not isinstance(names, list) or len(names) == 0:
        frappe.throw(_("No Payment Entry names provided"))

    results = {
        "success": [],
        "failed": []
    }

    for pe_name in names:
        try:
            _delete_single_payment_entry(pe_name)
            results["success"].append(pe_name)
        except Exception:
            frappe.db.rollback()
            error_msg = frappe.get_traceback()
            frappe.log_error(
                title=f"Payment Entry Delete Failed: {pe_name}",
                message=error_msg
            )
            results["failed"].append({
                "name": pe_name,
                "error": str(frappe.get_traceback().splitlines()[-1]) if error_msg else "Unknown error"
            })

    results["total"] = len(names)
    results["success_count"] = len(results["success"])
    results["failed_count"] = len(results["failed"])

    return results


def _delete_single_payment_entry(pe_name):
    """Cancel (if submitted) and delete a single Payment Entry."""

    if not frappe.db.exists("Payment Entry", pe_name):
        frappe.throw(_("Payment Entry {0} does not exist").format(pe_name))

    doc = frappe.get_doc("Payment Entry", pe_name)

    # permission check
    if not doc.has_permission("cancel") or not doc.has_permission("delete"):
        frappe.throw(_("Not permitted to delete Payment Entry {0}").format(pe_name))

    # docstatus: 0 = Draft, 1 = Submitted, 2 = Cancelled
    if doc.docstatus == 1:
        doc.cancel()
        frappe.db.commit()

    # re-fetch after cancel to get updated docstatus
    doc = frappe.get_doc("Payment Entry", pe_name)

    if doc.docstatus in (0, 2):
        frappe.delete_doc(
            "Payment Entry",
            pe_name,
            ignore_permissions=False,
            force=False
        )
        frappe.db.commit()
    else:
        frappe.throw(_("Payment Entry {0} could not be cancelled").format(pe_name))