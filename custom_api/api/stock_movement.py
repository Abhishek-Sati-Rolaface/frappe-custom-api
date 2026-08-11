import frappe
from frappe import _


@frappe.whitelist()
def create_stock_movement(posting_date, items, posting_time=None):
    """
    items = [
        {
            "item_code": "ITEM-001",
            "qty": 50,
            "source_warehouse": "Stores - ABC",
            "target_warehouse": "Finished Goods - ABC",
            "batch_no": "BATCH-001"
        },
        {
            "item_code": "ITEM-002",
            "qty": 20,
            "source_warehouse": "Stores - ABC",
            "target_warehouse": "Finished Goods - ABC",
            "serial_no": "SN-001\nSN-002"
        }
    ]
    """

    if isinstance(items, str):
        items = frappe.parse_json(items)

    if not items:
        frappe.throw(_("Items list is required"))

    if not frappe.db.get_single_value(
        "Stock Settings", "use_serial_batch_fields"
    ):
        frappe.db.set_single_value(
            "Stock Settings", "use_serial_batch_fields", 1
        )
        frappe.db.commit()

    company = frappe.defaults.get_global_default("company")

    if not company:
        frappe.throw(_("No default company set in Global Defaults"))

    doc = frappe.new_doc("Stock Entry")
    doc.company = company
    doc.stock_entry_type = "Material Transfer"
    doc.purpose = "Material Transfer"
    doc.posting_date = posting_date

    if posting_time:
        doc.set_posting_time = 1
        doc.posting_time = posting_time

    for row in items:
        item_code = row.get("item_code")
        source_warehouse = row.get("source_warehouse")
        target_warehouse = row.get("target_warehouse")
        qty = row.get("qty")

        if not item_code:
            frappe.throw(_("Item Code is required"))

        if not source_warehouse:
            frappe.throw(
                _("Source Warehouse is required for item {0}").format(item_code)
            )

        if not target_warehouse:
            frappe.throw(
                _("Target Warehouse is required for item {0}").format(item_code)
            )

        if source_warehouse == target_warehouse:
            frappe.throw(
                _("Source and target warehouse cannot be the same for item {0}")
                .format(item_code)
            )

        if not qty or qty <= 0:
            frappe.throw(
                _("Quantity must be greater than zero for item {0}")
                .format(item_code)
            )

        has_batch = frappe.db.get_value(
            "Item",
            item_code,
            "has_batch_no"
        )

        if has_batch and not row.get("batch_no"):
            frappe.throw(
                _("Batch No is mandatory for item {0}").format(item_code)
            )

        doc.append("items", {
            "item_code": item_code,
            "s_warehouse": source_warehouse,
            "t_warehouse": target_warehouse,
            "qty": qty,
            "serial_no": row.get("serial_no"),
            "batch_no": row.get("batch_no"),
            "use_serial_batch_fields": 1,
        })

    doc.insert()
    doc.submit()

    return {
        "name": doc.name,
        "status": "success",
        "message": f"Stock Entry {doc.name} submitted successfully"
    }