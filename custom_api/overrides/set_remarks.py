import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

_original_set_remarks = PaymentEntry.set_remarks

PARTY_NAME_FIELD = {
    "Customer": "customer_name",
    "Supplier": "supplier_name",
}

def patched_set_remarks(self):
    # ── Run Frappe's original logic first ──────────────────────────────
    _original_set_remarks(self)

    # ── Only handle Customer and Supplier — everything else falls back ──
    field = PARTY_NAME_FIELD.get(self.party_type)
    if not field:
        return

    if not self.party or not self.remarks:
        return

    party_name = frappe.db.get_value(self.party_type, self.party, field)

    if party_name and party_name != self.party:
        self.remarks = self.remarks.replace(self.party, party_name)

PaymentEntry.set_remarks = patched_set_remarks