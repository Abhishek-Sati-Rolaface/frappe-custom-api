import frappe
import pandas as pd
from frappe.utils.file_manager import save_file
from io import BytesIO

@frappe.whitelist()
def import_customers():
    """
    REST endpoint - multipart file upload
    POST /api/method/custom_api.api.customer_import.import_customers
    """
    if "file" not in frappe.request.files:
        frappe.throw("No file uploaded")

    file = frappe.request.files["file"]
    filename = file.filename

    if filename.endswith(".csv"):
        df = pd.read_csv(file)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file)
    else:
        frappe.throw("Only CSV or XLSX files allowed")

    df = df.where(pd.notnull(df), None)

    return process_customers(df)


def process_customers(df):
    success, failed = [], []

    required_cols = {"customer_name"}
    missing = required_cols - set(df.columns.str.strip())
    if missing:
        frappe.throw(f"Missing required columns: {', '.join(missing)}")

    for idx, row in df.iterrows():
        row_num = idx + 2  # header offset
        try:
            customer_name = str(row.get("customer_name") or "").strip()
            if not customer_name:
                failed.append({"row": row_num, "error": "customer_name missing"})
                continue

            existing = frappe.db.exists("Customer", {"customer_name": customer_name})
            if existing:
                doc = frappe.get_doc("Customer", existing)
                action = "updated"
            else:
                doc = frappe.new_doc("Customer")
                doc.customer_name = customer_name
                action = "created"

            # map remaining fields
            field_map = {
                "customer_group": row.get("customer_group"),
                "customer_type": row.get("customer_type"),
                "territory": row.get("territory"),
                "tax_id": row.get("tax_id"),
                "mobile_no": row.get("mobile_no"),
                "email_id": row.get("email_id"),
            }
            for field, value in field_map.items():
                if value:
                    doc.set(field, value)

            # defaults if new
            if action == "created":
                doc.customer_group = doc.customer_group or frappe.db.get_single_value(
                    "Selling Settings", "customer_group"
                ) or "All Customer Groups"
                doc.territory = doc.territory or frappe.db.get_single_value(
                    "Selling Settings", "territory"
                ) or "All Territories"

            doc.flags.ignore_mandatory = True
            doc.save(ignore_permissions=True)

            success.append({"row": row_num, "customer": doc.name, "action": action})

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Customer Import Error")
            failed.append({"row": row_num, "error": str(e)})

    frappe.db.commit()

    return {
        "total": len(df),
        "success_count": len(success),
        "failed_count": len(failed),
        "success": success,
        "failed": failed,
    }