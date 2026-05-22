import frappe
from frappe.core.doctype.communication.email import make as original_make

@frappe.whitelist()
def make(**kwargs):
    """
    Wrapper around frappe.core.doctype.communication.email.make
    Auto-injects default print format if use_default_print_format is True.
    """
    use_default = frappe.utils.cint(kwargs.pop("use_default_print_format", 0))


    if use_default:
        doctype   = kwargs.get("doctype")
        doc_name  = kwargs.get("name")

        if doctype:
            # ── Option 1: Fetch default print format set on the DocType ───
            default_pf = frappe.db.get_value(
                "Property Setter",
                {
                    "doc_type":      doctype,
                    "property":      "default_print_format",
                    "doctype_or_field": "DocType",
                },
                "value"
            )

            # ── Option 2: Fallback to first print format for this DocType ─
            if not default_pf:
                default_pf = frappe.db.get_value(
                    "Print Format",
                    {
                        "doc_type": doctype,
                        "disabled": 0,
                    },
                    "name",
                    order_by="standard desc, creation asc"  # prefer standard ones
                )

            if default_pf:
                kwargs["print_format"] = default_pf
                frappe.logger().info(
                    f"[make email] Auto-injected print_format={default_pf} "
                    f"for {doctype}/{doc_name}"
                )

    # ── Delegate to original Frappe function with updated kwargs ──────────
    return original_make(**kwargs)