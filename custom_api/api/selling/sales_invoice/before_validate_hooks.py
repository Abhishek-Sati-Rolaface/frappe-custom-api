import frappe
import json
from frappe.utils import flt

def apply_tax_floor_price(doc, method=None):
    if not doc.get("taxes") or not doc.get("items"):
        return

    for item in doc.items:
        standard_rate = flt(
            frappe.db.get_value("Item", item.item_code, "custom_standard_rate")
        )
        if not standard_rate or flt(item.rate) >= standard_rate:
            continue  # price is at/above standard — nothing to correct

        shortfall = (standard_rate - flt(item.rate)) * flt(item.qty)
        if shortfall <= 0:
            continue

        item_tax_rate = item.get("item_tax_rate")
        if not item_tax_rate:
            continue

        try:
            item_tax_rate = (
                json.loads(item_tax_rate) if isinstance(item_tax_rate, str) else item_tax_rate
            )
        except (TypeError, ValueError):
            continue

        for account_head, rate in item_tax_rate.items():
            additional_tax = flt(
                shortfall * flt(rate) / 100, doc.precision("tax_amount", "taxes")
            )
            for tax_row in doc.taxes:
                if tax_row.account_head == account_head:
                    tax_row.tax_amount = flt(tax_row.tax_amount) + additional_tax
                    tax_row.total = flt(tax_row.total) + additional_tax
                    break

    # Roll the adjusted tax rows back up into document totals
    doc.total_taxes_and_charges = flt(
        sum(flt(t.tax_amount) for t in doc.taxes),
        doc.precision("total_taxes_and_charges"),
    )
    doc.grand_total = flt(doc.net_total) + doc.total_taxes_and_charges
    doc.rounded_total = (
        doc.grand_total if doc.get("disable_rounded_total") else round(doc.grand_total)
    )

    if doc.doctype in ("Sales Invoice", "POS Invoice") and not doc.get("is_return"):
        doc.outstanding_amount = doc.rounded_total or doc.grand_total

def before_validate(doc,method):
    apply_tax_floor_price(doc, method)
    data = frappe.local.form_dict
    if data.get("reason"):
        if not doc.custom_details:
            doc.append("custom_details", {"reason": data.get("reason")})
        else:
            doc.custom_details[0].reason = data.get("reason")


