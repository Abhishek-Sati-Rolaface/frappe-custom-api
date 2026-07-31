import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def delete_payment_entry(payment_entry_name=None, payment_entries=None, permanent_delete=0):
    """
    Cancel (and optionally delete) one or more Payment Entries.

    Default behavior: only CANCEL the Payment Entry (docstatus 1 -> 2).
    Record stays in DB for audit trail. GL Entries get reversed/cleared
    by Frappe's standard cancel process.

    Pass permanent_delete=1 explicitly to also hard-delete the doc
    after cancelling (irreversible - use with caution).

    Args:
        payment_entry_name (str): Single Payment Entry name (for single op)
        payment_entries (str/list): JSON list or list of Payment Entry names (bulk op)
        permanent_delete (int/bool): 0 = cancel only (default, safe)
                                      1 = cancel + hard delete (irreversible)

    Returns:
        dict: summary with success/failed lists
    """

    permanent_delete = cint(permanent_delete)

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
        "failed": [],
        "mode": "cancel_and_delete" if permanent_delete else "cancel_only"
    }

    for pe_name in names:
        try:
            action_taken = _cancel_or_delete_payment_entry(pe_name, permanent_delete)
            results["success"].append({
                "name": pe_name,
                "action": action_taken
            })
        except Exception:
            frappe.db.rollback()
            error_msg = frappe.get_traceback()
            frappe.log_error(
                title=f"Payment Entry Cancel/Delete Failed: {pe_name}",
                message=error_msg
            )
            results["failed"].append({
                "name": pe_name,
                "error": error_msg.splitlines()[-1] if error_msg else "Unknown error"
            })

    results["total"] = len(names)
    results["success_count"] = len(results["success"])
    results["failed_count"] = len(results["failed"])

    return results


def _cancel_or_delete_payment_entry(pe_name, permanent_delete=0):
    """
    Cancel a single Payment Entry (default), and hard-delete it too
    only if permanent_delete=1 is explicitly passed.

    Returns a string describing the action taken: "cancelled",
    "already_cancelled", "deleted_draft", or "cancelled_and_deleted"
    """

    if not frappe.db.exists("Payment Entry", pe_name):
        frappe.throw(_("Payment Entry {0} does not exist").format(pe_name))

    doc = frappe.get_doc("Payment Entry", pe_name)

    # permission check
    if not doc.has_permission("cancel"):
        frappe.throw(_("Not permitted to cancel Payment Entry {0}").format(pe_name))

    # docstatus: 0 = Draft, 1 = Submitted, 2 = Cancelled
    action = None

    if doc.docstatus == 1:
        doc.cancel()
        frappe.db.commit()
        action = "cancelled"
    elif doc.docstatus == 2:
        action = "already_cancelled"
    elif doc.docstatus == 0:
        # Draft - nothing submitted yet, no GL impact.
        # Only delete a draft if permanent_delete explicitly requested,
        # otherwise leave it untouched.
        if not permanent_delete:
            frappe.throw(
                _("Payment Entry {0} is a Draft. Nothing to cancel. "
                  "Pass permanent_delete=1 if you want to delete the draft.").format(pe_name)
            )

    # Stop here unless permanent_delete is explicitly set
    if not permanent_delete:
        return action

    # ---- permanent_delete=1: proceed to hard delete ----
    if not doc.has_permission("delete"):
        frappe.throw(_("Not permitted to delete Payment Entry {0}").format(pe_name))

    doc = frappe.get_doc("Payment Entry", pe_name)  # re-fetch fresh docstatus

    if doc.docstatus in (0, 2):
        frappe.delete_doc(
            "Payment Entry",
            pe_name,
            ignore_permissions=False,
            force=False
        )
        frappe.db.commit()
        action = "cancelled_and_deleted" if action == "cancelled" else "deleted_draft"
    else:
        frappe.throw(_("Payment Entry {0} could not be cancelled, so it was not deleted").format(pe_name))

    return action