import frappe
from datetime import timedelta
from custom_api.config.constant import FREQUENCY_DAYS
import html

def should_send_reminder(notification_scheduler_log, frequency, now):
    """
    Decide whether a reminder should be sent based on the last-sent
    timestamp and the configured frequency.
    """
    # No log yet — always send the first reminder
    if not notification_scheduler_log or not notification_scheduler_log.sent_on:
        return True
 
    time_diff = now - notification_scheduler_log.sent_on

    if frequency == "Hourly":
        return time_diff >= timedelta(hours=1)
 
    if frequency in FREQUENCY_DAYS:
        return time_diff >= timedelta(days=FREQUENCY_DAYS[frequency])
 
    # Unknown frequency — fail safe, don't spam
    return False

def send_payment_reminder_email(customer, template):
    
    message_template = template.response

    if "{{ invoice_table }}" in message_template:
        PAYMENT_REMINDER_TEMPLATE = "custom_api/templates/customer_payment_reminder.html"
        invoice_table_html = frappe.render_template(PAYMENT_REMINDER_TEMPLATE, customer )
        message_template = message_template.replace("{{ invoice_table }}", invoice_table_html)

    subject = frappe.render_template(template.subject, customer)
    message = frappe.render_template(message_template, customer)
    
    message = html.unescape(message)
    frappe.sendmail(
        recipients=[customer["contact_email"]],
        subject=subject,
        content=message,
        raw_html=True
        # now=True
    )

def upsert_scheduler_log(notification_scheduler_log, scheduler_name, reference_doctype_name, now, recipient, reference_doctype="Sales Invoice"):
    """Update the existing log's sent_on, or create a new log entry."""
 
    if notification_scheduler_log:
        frappe.db.set_value(
            "Custom Notification Scheduler Log",
            notification_scheduler_log.name,
            "sent_on",
            now,
        )
    else:
        frappe.get_doc({
            "doctype": "Custom Notification Scheduler Log",
            "custom_notification_scheduler_name": scheduler_name,
            "reference_doctype": reference_doctype,
            "reference_doctype_name": reference_doctype_name,
            "recipient": recipient,
            "sent_on": now,
        }).insert(ignore_permissions=True)
 