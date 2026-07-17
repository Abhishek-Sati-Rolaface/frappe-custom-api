import frappe

class ZRAConnectionError(Exception):
    def __init__(self, msg, doc=None, result=None):
        super().__init__(msg)
        self.doc = doc
        self.result = result
        self.invoice_id = doc.name if doc else None
        self.doctype = doc.doctype if doc else None

        if self.invoice_id:
            self._mark_connection_failed()

    def _mark_connection_failed(self):
        frappe.db.rollback()
        new_status = "Pending"

        fresh_doc = frappe.get_doc(self.doctype, self.invoice_id)
        fresh_doc.db_set("status", new_status, update_modified=True)

        if self.doctype == "Purchase Invoice" and fresh_doc.get("custom_invoice_metadata"):
            child_row = fresh_doc.custom_invoice_metadata[0]
            if child_row.get("name"):
                child_row.db_set("zra_response", self.result, update_modified=True)

        elif self.doctype == "Sales Invoice" and fresh_doc.get("custom_details"):
            child_row = fresh_doc.custom_details[0]
            if child_row.get("name"):
                child_row.db_set("zra_response", self.result, update_modified=True)

        frappe.db.commit()

class ZRAResponseError(Exception):
    def __init__(self, msg, doc=None, result=None):
        super().__init__(msg)
        self.doc = doc
        self.result = result
        self.invoice_id = doc.name if doc else None
        self.doctype = doc.doctype if doc else None

        if self.invoice_id:
            self._mark_connection_failed()

    def _mark_connection_failed(self):
        frappe.db.rollback()
        new_status = "Failed"

        fresh_doc = frappe.get_doc(self.doctype, self.invoice_id)
        fresh_doc.db_set("status", new_status, update_modified=True)

        result_value = self.result
        if result_value is not None and not isinstance(result_value, str):
            result_value = frappe.as_json(result_value)

        if self.doctype == "Purchase Invoice" and fresh_doc.get("custom_invoice_metadata"):
            child_row = fresh_doc.custom_invoice_metadata[0]
            if child_row.get("name"):
                child_row.db_set("zra_response", result_value, update_modified=True)

        elif self.doctype == "Sales Invoice" and fresh_doc.get("custom_details"):
            child_row = fresh_doc.custom_details[0]
            if child_row.get("name"):
                child_row.db_set("zra_response", result_value, update_modified=True)

        frappe.db.commit()