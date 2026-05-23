__version__ = "0.0.1"
import frappe
from custom_api.utils.email.email import sendmail

frappe._original_sendmail = frappe.sendmail

frappe.sendmail = sendmail