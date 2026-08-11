import frappe
from frappe import _

STOCK_ENTRY_RULES = {
    "Material Receipt": {"source": False, "target": True},
    "Material Issue": {"source": True, "target": False},
    "Material Transfer": {"source": True, "target": True},
    "Material Transfer for Manufacture": {"source": True, "target": True},
    "Material Consumption for Manufacture": {"source": True, "target": False},
    "Send to Subcontractor": {"source": True, "target": True},
    "Manufacture": {"mixed": True},
    "Repack": {"mixed": True},
    "Disassemble": {"mixed": True},
}

@frappe.whitelist()
def create_stock_entry(
    stock_entry_type,
    posting_date,
    items,
    posting_time=None,
    source_warehouse=None,
    target_warehouse=None,
    work_order=None,
    bom_no=None,
    remarks=None,
    submit=1,
):
    """
    Generic Stock Entry creator — handles every ERPNext stock entry type.

    Normal types (Receipt / Issue / Transfer / Transfer for Manufacture /
    Consumption for Manufacture / Send to Subcontractor):
        items = [
            {"item_code": "ITEM-001", "qty": 50, "batch_no": "BATCH-001"},
            {"item_code": "ITEM-002", "qty": 20,
             "source_warehouse": "Stores - ABC", "target_warehouse": "FG - ABC"}
        ]

    Manufacture / Repack / Disassemble (each row needs a "role"):
        items = [
            {"item_code": "RAW-001", "qty": 10, "role": "consume", "source_warehouse": "Stores - ABC"},
            {"item_code": "FG-001", "qty": 5, "role": "produce", "target_warehouse": "FG - ABC", "is_finished_item": 1},
        ]
    """
    items = frappe.parse_json(items) if isinstance(items, str) else items
    if not items:
        frappe.throw(_("Items list is required"))

    if stock_entry_type not in STOCK_ENTRY_RULES:
        frappe.throw(
            _("Invalid Stock Entry Type: {0}. Must be one of: {1}").format(
                stock_entry_type, ", ".join(STOCK_ENTRY_RULES.keys())
            )
        )
    rules = STOCK_ENTRY_RULES[stock_entry_type]

    if not frappe.db.get_single_value("Stock Settings", "use_serial_batch_fields"):
        frappe.db.set_single_value("Stock Settings", "use_serial_batch_fields", 1)
        frappe.db.commit()

    company = frappe.defaults.get_global_default("company")
    if not company:
        frappe.throw(_("No default company set in Global Defaults"))

    doc = frappe.new_doc("Stock Entry")
    doc.company = company
    doc.stock_entry_type = stock_entry_type
    doc.purpose = stock_entry_type
    doc.posting_date = posting_date

    if posting_time:
        doc.set_posting_time = 1
        doc.posting_time = posting_time
    if work_order:
        doc.work_order = work_order
    if bom_no:
        doc.bom_no = bom_no
    if remarks:
        doc.remarks = remarks

    for row in items:
        doc.append("items", build_item_row(row, rules, source_warehouse, target_warehouse))

    doc.insert()
    if int(submit):
        doc.submit()

    return {
        "name": doc.name,
        "docstatus": doc.docstatus,
        "status": "success",
        "message": f"Stock Entry {doc.name} {'submitted' if int(submit) else 'saved as draft'} successfully",
    }


def build_item_row(row, rules, default_source, default_target):
    """Validate one item row and build the child-table dict for it."""
    item_code = row.get("item_code")
    qty = row.get("qty")

    if not item_code:
        frappe.throw(_("Item Code is required for every row"))
    if not qty or qty <= 0:
        frappe.throw(_("Quantity must be greater than zero for item {0}").format(item_code))

    if frappe.db.get_value("Item", item_code, "has_batch_no") and not row.get("batch_no"):
        frappe.throw(_("Batch No is mandatory for item {0}").format(item_code))
    if frappe.db.get_value("Item", item_code, "has_serial_no") and not row.get("serial_no"):
        frappe.throw(_("Serial No is mandatory for item {0}").format(item_code))

    source = row.get("source_warehouse") or default_source
    target = row.get("target_warehouse") or default_target

    item_row = {
        "item_code": item_code,
        "qty": qty,
        "batch_no": row.get("batch_no"),
        "serial_no": row.get("serial_no"),
        "use_serial_batch_fields": 1,
    }
    if row.get("valuation_rate") is not None:
        item_row["valuation_rate"] = row.get("valuation_rate")
    if row.get("uom"):
        item_row["uom"] = row.get("uom")

    if rules.get("mixed"):
        role = row.get("role")
        if role not in ("consume", "produce"):
            frappe.throw(_("Item {0}: 'role' must be 'consume' or 'produce'").format(item_code))
        if role == "consume":
            if not source:
                frappe.throw(_("Source Warehouse is required for consumed item {0}").format(item_code))
            item_row["s_warehouse"] = source
        else:
            if not target:
                frappe.throw(_("Target Warehouse is required for produced item {0}").format(item_code))
            item_row["t_warehouse"] = target
            if row.get("is_finished_item"):
                item_row["is_finished_item"] = 1
            if row.get("is_scrap_item"):
                item_row["is_scrap_item"] = 1
    else:
        if rules["source"]:
            if not source:
                frappe.throw(_("Source Warehouse is required for item {0}").format(item_code))
            item_row["s_warehouse"] = source
        if rules["target"]:
            if not target:
                frappe.throw(_("Target Warehouse is required for item {0}").format(item_code))
            item_row["t_warehouse"] = target
        if rules["source"] and rules["target"] and source == target:
            frappe.throw(_("Source and target warehouse cannot be the same for item {0}").format(item_code))

    return item_row