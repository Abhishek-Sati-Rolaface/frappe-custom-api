import frappe


def validate_sales_tax_payload(data):
    if not data:
        frappe.throw("Payload is required")

    if not data.get("taxes"):
        frappe.throw("At least one tax row is required")


def get_account_description(account):
    if not account:
        return ""

    acc = frappe.db.get_value(
        "Account",
        account,
        ["account_name", "account_number"],
        as_dict=True,
    )

    if not acc:
        return ""

    if acc.account_number:
        return f"{acc.account_number} - {acc.account_name}"

    return acc.account_name


def map_sales_tax_template(doc, data):
    company_name = frappe.defaults.get_user_default("Company")

    if data.get("title"):
        doc.title = data.get("title")

    doc.company = company_name

    if "disabled" in data:
        doc.disabled = data.get("disabled")

    if "tax_category" in data:
        doc.tax_category = data.get("tax_category") or None

    taxes = data.get("taxes", [])

    for row in taxes:
        charge_type = row.get("charge_type", "On Net Total")
        account = row.get("account_head")

        tax_row = {
            "charge_type": charge_type,
            "account_head": account,
        }

        if row.get("description"):
            tax_row["description"] = row.get("description")
        else:
            tax_row["description"] = get_account_description(account)

        if charge_type == "Actual":
            tax_row["tax_amount"] = row.get("tax_amount", 0.0)
        else:
            tax_row["rate"] = row.get("rate", 0.0)

        doc.append("taxes", tax_row)


def patch_sales_tax_template(doc, data):
    if "title" in data:
        doc.title = data.get("title")

    if "disabled" in data:
        doc.disabled = data.get("disabled")

    if "tax_category" in data:
        doc.tax_category = data.get("tax_category") or None

    if "is_default" in data:
        doc.is_default = data.get("is_default")

    if "taxes" in data:
        for row_data in data.get("taxes"):
            row_id = row_data.get("name")

            if row_id:
                existing_row = next(
                    (r for r in doc.taxes if r.name == row_id), None
                )

                if not existing_row:
                    frappe.throw(
                        f"Child row with name '{row_id}' not found in this template."
                    )

                account = row_data.get("account_head")

                if account and account != existing_row.account_head:
                    existing_row.account_head = account

                    if not row_data.get("description"):
                        existing_row.description = get_account_description(account)

                if row_data.get("description"):
                    existing_row.description = row_data["description"]

                if "charge_type" in row_data:
                    existing_row.charge_type = row_data["charge_type"]

                charge_type = row_data.get(
                    "charge_type", existing_row.charge_type
                )

                if charge_type == "Actual":
                    if "tax_amount" in row_data:
                        existing_row.tax_amount = row_data["tax_amount"]
                    existing_row.rate = 0.0
                else:
                    if "rate" in row_data:
                        existing_row.rate = row_data["rate"]
                    existing_row.tax_amount = 0.0

            else:
                charge_type = row_data.get("charge_type", "On Net Total")
                account = row_data.get("account_head")

                tax_row = {
                    "charge_type": charge_type,
                    "account_head": account,
                }

                if row_data.get("description"):
                    tax_row["description"] = row_data["description"]
                else:
                    tax_row["description"] = get_account_description(account)

                if charge_type == "Actual":
                    tax_row["tax_amount"] = row_data.get("tax_amount", 0.0)
                    tax_row["rate"] = 0.0
                else:
                    tax_row["rate"] = row_data.get("rate", 0.0)
                    tax_row["tax_amount"] = 0.0

                doc.append("taxes", tax_row)


def build_filters(args):
    filters = {}

    if args.get("company"):
        filters["company"] = args.get("company")

    if args.get("name"):
        filters["name"] = args.get("name")

    if args.get("disabled") is not None:
        filters["disabled"] = int(args.get("disabled"))

    if args.get("search"):
        filters["title"] = ["like", f"%{args.get('search')}%"]

    return filters