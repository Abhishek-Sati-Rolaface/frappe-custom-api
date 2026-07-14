import frappe

class ZRAConnectionError(Exception):
    def __init__(self, msg, doc=None):
        super().__init__(msg)
        if doc:
            self.doc = doc
            self.invoice_id = doc.name if doc else None

            if self.invoice_id:
                self._mark_connection_failed()

    def _mark_connection_failed(self):
        frappe.db.rollback()
        new_status = "Pending"

        frappe.db.sql("""
            UPDATE `tabSales Invoice`
            SET status = %s,
                modified = NOW(),
                modified_by = %s
            WHERE name = %s
        """, (new_status, frappe.session.user, self.invoice_id))
        frappe.db.commit()

# class ZRAResponseError(Exception):
#     def __init__(self, msg, doc=None):
#         super().__init__(msg)
#         self.doc = doc
#         self.invoice_id = doc.name if doc else None

#         if self.invoice_id:
#             self._mark_connection_failed()

#     def _mark_connection_failed(self):
#         frappe.db.rollback()
#         new_status = "Failed"

#         frappe.db.sql("""
#             UPDATE `tabSales Invoice`
#             SET status = %s,
#                 modified = NOW(),
#                 modified_by = %s
#             WHERE name = %s
#         """, (new_status, frappe.session.user, self.invoice_id))
#         frappe.db.commit() 