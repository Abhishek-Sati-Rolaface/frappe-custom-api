__version__ = "0.0.1"
import frappe
from custom_api.utils.email.email import sendmail
import erpnext.accounts.doctype.payment_entry.payment_entry as pe_module
from custom_api.overrides.set_remarks import patched_set_remarks

frappe._original_sendmail = frappe.sendmail

frappe.sendmail = sendmail

pe_module.PaymentEntry.set_remarks = patched_set_remarks   # Patch the set_remarks method of PaymentEntry to replace party ID with party name in remarks
