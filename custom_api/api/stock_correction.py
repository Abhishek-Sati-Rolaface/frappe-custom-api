# # import frappe
# # from frappe import _

# # @frappe.whitelist()
# # def create_stock_correction(warehouse, posting_date, items, posting_time=None):
# #     """
# #     items = [
# #         {"item_code": "ITEM-001", "qty": 50, "valuation_rate": 120.5},
# #         {"item_code": "ITEM-002", "qty": 20}
# #     ]
# #     """
# #     if isinstance(items, str):
# #         items = frappe.parse_json(items)

# #     if not items:
# #         frappe.throw(_("Items list is required"))

# #     company = frappe.defaults.get_global_default("company")
# #     if not company:
# #         frappe.throw(_("No default company set in Global Defaults"))

# #     doc = frappe.new_doc("Stock Reconciliation")
# #     doc.company = company
# #     doc.purpose = "Stock Reconciliation"
# #     doc.posting_date = posting_date
# #     if posting_time:
# #         doc.set_posting_time = 1
# #         doc.posting_time = posting_time

# #     for row in items:
# #         item_code = row.get("item_code")

# #         has_batch = frappe.db.get_value("Item", item_code, "has_batch_no")
# #         if has_batch and not row.get("batch_no"):
# #             frappe.throw(_("Batch No is mandatory for item {0}").format(item_code))

# #         doc.append("items", {
# #             "item_code": item_code,
# #             "warehouse": row.get("warehouse") or warehouse,
# #             "qty": row.get("qty"),
# #             "valuation_rate": row.get("valuation_rate"),
# #             "serial_no": row.get("serial_no"),
# #             "batch_no": row.get("batch_no"),
# #         })

# #     doc.insert()
# #     doc.submit()

# #     return {
# #         "name": doc.name,
# #         "status": "success",
# #         "message": f"Stock Reconciliation {doc.name} submitted successfully"
# #     }

# # import frappe
# # from frappe import _

# # @frappe.whitelist()
# # def create_stock_correction(warehouse, posting_date, items, posting_time=None):
# #     """
# #     items = [
# #         {"item_code": "ITEM-001", "qty": 50, "valuation_rate": 120.5, "batch_no": "BATCH-001"},
# #         {"item_code": "ITEM-002", "qty": 20}
# #     ]
# #     """
# #     if isinstance(items, str):
# #         items = frappe.parse_json(items)

# #     if not items:
# #         frappe.throw(_("Items list is required"))

# #     company = frappe.defaults.get_global_default("company")
# #     if not company:
# #         frappe.throw(_("No default company set in Global Defaults"))

# #     doc = frappe.new_doc("Stock Reconciliation")
# #     doc.company = company
# #     doc.purpose = "Stock Reconciliation"
# #     doc.posting_date = posting_date
# #     if posting_time:
# #         doc.set_posting_time = 1
# #         doc.posting_time = posting_time

# #     doc.set_new_name()

# #     for row in items:
# #         item_code = row.get("item_code")
# #         item_warehouse = row.get("warehouse") or warehouse
# #         has_batch = frappe.db.get_value("Item", item_code, "has_batch_no")

# #         item_row = doc.append("items", {
# #             "item_code": item_code,
# #             "warehouse": item_warehouse,
# #             "qty": row.get("qty"),
# #             "valuation_rate": row.get("valuation_rate"),
# #             "serial_no": row.get("serial_no"),
# #         })

# #         # Batch-tracked item -> create Serial and Batch Bundle
# #         if has_batch:
# #             batch_no = row.get("batch_no")
# #             if not batch_no:
# #                 frappe.throw(_("Batch No is mandatory for item {0}").format(item_code))

# #             current_qty = frappe.db.get_value(
# #                 "Bin", {"item_code": item_code, "warehouse": item_warehouse}, "actual_qty"
# #             ) or 0

# #             bundle_doc = frappe.new_doc("Serial and Batch Bundle")
# #             bundle_doc.item_code = item_code
# #             bundle_doc.warehouse = item_warehouse
# #             bundle_doc.voucher_type = "Stock Reconciliation"
# #             bundle_doc.voucher_no = doc.name
# #             bundle_doc.type_of_transaction = "Inward" if row.get("qty") >= current_qty else "Outward"
# #             bundle_doc.append("entries", {
# #                 "batch_no": batch_no,
# #                 "qty": row.get("qty"),
# #             })
# #             bundle_doc.insert(ignore_permissions=True)
# #             bundle_doc.submit()

# #             item_row.serial_and_batch_bundle = bundle_doc.name
# #             item_row.batch_no = batch_no

# #     doc.insert()
# #     doc.submit()

# #     return {
# #         "name": doc.name,
# #         "status": "success",
# #         "message": f"Stock Reconciliation {doc.name} submitted successfully"
# #     }

# import frappe
# from frappe import _

# @frappe.whitelist()
# def create_stock_correction(warehouse, posting_date, items, posting_time=None):
#     """
#     items = [
#         {"item_code": "ITEM-001", "qty": 50, "valuation_rate": 120.5, "batch_no": "BATCH-001"},
#         {"item_code": "ITEM-002", "qty": 20}
#     ]
#     """
#     if isinstance(items, str):
#         items = frappe.parse_json(items)

#     if not items:
#         frappe.throw(_("Items list is required"))

#     company = frappe.defaults.get_global_default("company")
#     if not company:
#         frappe.throw(_("No default company set in Global Defaults"))

#     doc = frappe.new_doc("Stock Reconciliation")
#     doc.company = company
#     doc.purpose = "Stock Reconciliation"
#     doc.posting_date = posting_date
#     if posting_time:
#         doc.set_posting_time = 1
#         doc.posting_time = posting_time

#     # Pehle items append karo bina bundle ke
#     row_meta = []  # batch info baad mein process karne ke liye store kar lo
#     for row in items:
#         item_code = row.get("item_code")
#         item_warehouse = row.get("warehouse") or warehouse
#         has_batch = frappe.db.get_value("Item", item_code, "has_batch_no")

#         item_row = doc.append("items", {
#             "item_code": item_code,
#             "warehouse": item_warehouse,
#             "qty": row.get("qty"),
#             "valuation_rate": row.get("valuation_rate"),
#             "serial_no": row.get("serial_no"),
#         })

#         if has_batch:
#             batch_no = row.get("batch_no")
#             if not batch_no:
#                 frappe.throw(_("Batch No is mandatory for item {0}").format(item_code))
#             row_meta.append({
#                 "item_row": item_row,
#                 "item_code": item_code,
#                 "warehouse": item_warehouse,
#                 "qty": row.get("qty"),
#                 "batch_no": batch_no,
#             })

#     # Step 1: Draft insert -> ab real name mil jayega DB mein
#     doc.insert()

#     # Step 2: Ab real voucher_no ke saath bundles banao
#     for meta in row_meta:
#         current_qty = frappe.db.get_value(
#             "Bin", {"item_code": meta["item_code"], "warehouse": meta["warehouse"]}, "actual_qty"
#         ) or 0

#         bundle_doc = frappe.new_doc("Serial and Batch Bundle")
#         bundle_doc.item_code = meta["item_code"]
#         bundle_doc.warehouse = meta["warehouse"]
#         bundle_doc.voucher_type = "Stock Reconciliation"
#         bundle_doc.voucher_no = doc.name          # ab ye real hai, DB mein exist karta hai
#         bundle_doc.voucher_detail_no = meta["item_row"].name
#         bundle_doc.type_of_transaction = "Inward" if meta["qty"] >= current_qty else "Outward"
#         bundle_doc.append("entries", {
#             "batch_no": meta["batch_no"],
#             "qty": meta["qty"],
#         })
#         bundle_doc.insert(ignore_permissions=True)
#         bundle_doc.submit()

#         # Item row ko bundle reference se update karo
#         frappe.db.set_value(
#             "Stock Reconciliation Item",
#             meta["item_row"].name,
#             {
#                 "serial_and_batch_bundle": bundle_doc.name,
#                 "batch_no": meta["batch_no"],
#             }
#         )

#     # Step 3: Reload aur submit
#     doc.reload()
#     doc.submit()

#     return {
#         "name": doc.name,
#         "status": "success",
#         "message": f"Stock Reconciliation {doc.name} submitted successfully"
#     }

import frappe
from frappe import _

@frappe.whitelist()
def create_stock_correction(warehouse, posting_date, items, posting_time=None):
    """
    items = [
        {"item_code": "ITEM-001", "qty": 50, "valuation_rate": 120.5, "batch_no": "BATCH-001"},
        {"item_code": "ITEM-002", "qty": 20}
    ]
    """
    if isinstance(items, str):
        items = frappe.parse_json(items)

    if not items:
        frappe.throw(_("Items list is required"))

    company = frappe.defaults.get_global_default("company")
    if not company:
        frappe.throw(_("No default company set in Global Defaults"))

    doc = frappe.new_doc("Stock Reconciliation")
    doc.company = company
    doc.purpose = "Stock Reconciliation"
    doc.posting_date = posting_date
    if posting_time:
        doc.set_posting_time = 1
        doc.posting_time = posting_time

    # Naam pehle hi reserve kar lo (DB mein insert kiye bina)
    doc.set_new_name()

    for row in items:
        item_code = row.get("item_code")
        item_warehouse = row.get("warehouse") or warehouse
        has_batch = frappe.db.get_value("Item", item_code, "has_batch_no")

        item_row = doc.append("items", {
            "item_code": item_code,
            "warehouse": item_warehouse,
            "qty": row.get("qty"),
            "valuation_rate": row.get("valuation_rate"),
            "serial_no": row.get("serial_no"),
        })

        if has_batch:
            batch_no = row.get("batch_no")
            if not batch_no:
                frappe.throw(_("Batch No is mandatory for item {0}").format(item_code))

            current_qty = frappe.db.get_value(
                "Bin", {"item_code": item_code, "warehouse": item_warehouse}, "actual_qty"
            ) or 0

            bundle_doc = frappe.new_doc("Serial and Batch Bundle")
            bundle_doc.item_code = item_code
            bundle_doc.warehouse = item_warehouse
            bundle_doc.voucher_type = "Stock Reconciliation"
            bundle_doc.voucher_no = doc.name
            bundle_doc.type_of_transaction = "Inward" if row.get("qty") >= current_qty else "Outward"
            bundle_doc.append("entries", {
                "batch_no": batch_no,
                "qty": row.get("qty"),
            })

            # 👇 Link validation skip karo — parent abhi DB mein exist nahi karta
            bundle_doc.flags.ignore_links = True
            bundle_doc.insert(ignore_permissions=True)
            bundle_doc.submit()

            item_row.serial_and_batch_bundle = bundle_doc.name
            item_row.batch_no = batch_no

    doc.insert()   # ab same reserved name se insert hoga, bundles already link ho chuke
    doc.submit()

    return {
        "name": doc.name,
        "status": "success",
        "message": f"Stock Reconciliation {doc.name} submitted successfully"
    }