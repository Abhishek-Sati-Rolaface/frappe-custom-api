from custom_api.schedulars.customer_payment_reminder.invoices import get_overdue_invoices_grouped_by_customer
from custom_api.schedulars.customer_payment_reminder.utils import send_payment_reminder_email, should_send_reminder, upsert_scheduler_log
import frappe

def send_overdue_payment_reminders():
    try:
        notification_scheduler_doc = frappe.get_doc("Custom Notification Scheduler","Payment Reminder")
        template = frappe.get_doc("Email Template", "Payment Reminder")
        customers = get_overdue_invoices_grouped_by_customer()
        if customers:
            now = frappe.utils.now_datetime()
            company_name = frappe.defaults.get_user_default("Company")
                        
            for customer_data in customers.values():
                notification_scheduler_log = frappe.get_value(
                                                    "Custom Notification Scheduler Log",

                                                    filters={
                                                        "custom_notification_scheduler_name": notification_scheduler_doc.name,
                                                        "reference_doctype": "Customer",
                                                        "reference_doctype_name": customer_data["customer"]
                                                    }, 
                                                    fieldname=["*"], as_dict=True)

                customer_data["company_name"] = company_name
                if not should_send_reminder(notification_scheduler_log, notification_scheduler_doc.frequency, now):
                    return

                send_payment_reminder_email(customer_data, template)

                # ── Update or create the log ────────────────────────────────────────
                upsert_scheduler_log(notification_scheduler_log, notification_scheduler_doc.name, customer_data["customer"], now, customer_data["contact_email"], "Customer")
                        
            print("Finished sending payment reminders.")

    except Exception as e:
        print("Error --->>> ", e)