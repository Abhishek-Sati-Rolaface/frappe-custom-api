import json
import frappe
from frappe.utils import flt
from .utils import (
    build_quotation_filters,
    ensure_lost_reason,
    get_extended_item_detail,
    sync_taxes,
    sync_quotation_terms,
    get_naming_series_for_quotation
)
from custom_api.api.item.utils.item_utils import _get_tax
from ....api.buying.purchase_order.utils import _get_item_tax_template


def create_quotation(data):
    company = frappe.defaults.get_user_default("Company")
    company_doc = frappe.get_cached_doc("Company", company)

    currency = data.get("currency") or company_doc.default_currency

    document_type = data.get("documentType") or data.get("document_type")
    if not document_type:
        extended_details = data.get("extendedDetails") or data.get("extended_details", [])
        if extended_details and isinstance(extended_details, list):
            document_type = extended_details[0].get("documentType") or extended_details[0].get("document_type")
    
    document_type = document_type or "Quotation"
    naming_series = get_naming_series_for_quotation(document_type)

    quotation = frappe.new_doc("Quotation")

    quotation.update(
        {
            "naming_series": naming_series,
            "title": data.get("title"),
            "quotation_to": "Customer",
            "party_name": data.get("customerId"),
            "currency": currency,
            "conversion_rate": data.get("exchangeRate", 1),
            "transaction_date": data.get("postingDate"),
            "valid_till": data.get("validTill"),
            "tax_category": data.get("taxCategory"),
            "customer_address": data.get("billingAddress"),
            "shipping_address_name": data.get("shippingAddress"),
            "taxes_and_charges": data.get("salesTaxTemplate"),
            "order_type": data.get("orderType", "Sales"),
        }
    )

    quotation.append("custom_extended_details", {
        "document_type": document_type
    })

    for item in data.get("items", []):
        quotation.append(
            "items",
            {
                "item_code": item.get("itemCode"),
                "qty": item.get("quantity"),
                "uom": item.get("uom"),
                "discount_percentage": item.get("discount", 0),
                "rate": item.get("rate"),
                "is_alternative": (
                    1 if item.get("isAlternative") or item.get("is_alternative") else 0
                ),
                "item_tax_template": _get_item_tax_template(
                    item.get("itemCode"), data.get("taxCategory")
                ),
            },
        )

    sync_taxes(quotation, data)

    quotation.insert(ignore_permissions=True)

    terms_payload = data.get("terms")
    if terms_payload:
        sync_quotation_terms(quotation, terms_payload)

    return quotation


def update_quotation(quotation_id, data):
    quotation = frappe.get_doc("Quotation", quotation_id)

    if quotation.docstatus == 1:
        raise frappe.ValidationError(
            "Cannot edit a submitted Quotation. Cancel it first."
        )

    company = quotation.company
    company_doc = frappe.get_cached_doc("Company", company)
    currency = data.get("currency") or company_doc.default_currency

    field_map = {
        "title": "title",
        "customerId": "party_name",
        "currency": "currency",
        "exchangeRate": "conversion_rate",
        "postingDate": "transaction_date",
        "validTill": "valid_till",
        "taxCategory": "tax_category",
        "billingAddress": "customer_address",
        "shippingAddress": "shipping_address_name",
        "salesTaxTemplate": "taxes_and_charges",
        "orderType": "order_type",
    }

    for k, v in field_map.items():
        if data.get(k) is not None:
            setattr(quotation, v, data.get(k))

    if currency:
        quotation.currency = currency

    document_type = data.get("documentType") or data.get("document_type")
    if not document_type:
        extended_details = data.get("extendedDetails") or data.get("extended_details")
        if extended_details and isinstance(extended_details, list):
            document_type = extended_details[0].get("documentType") or extended_details[0].get("document_type")

    if document_type:
        quotation.set("custom_extended_details", [])
        quotation.append("custom_extended_details", {
            "document_type": document_type
        })

    if "items" in data:
        quotation.set("items", [])
        for item in data.get("items"):
            quotation.append(
                "items",
                {
                    "item_code": item.get("itemCode"),
                    "qty": item.get("quantity"),
                    "uom": item.get("uom"),
                    "rate": item.get("rate"),
                    "discount_percentage": item.get("discount", 0),
                    "is_alternative": (
                        1
                        if item.get("isAlternative") or item.get("is_alternative")
                        else 0
                    ),
                    "item_tax_template": _get_item_tax_template(
                        item.get("itemCode"),
                        data.get("taxCategory") or quotation.tax_category,
                    ),
                },
            )

    sync_taxes(quotation, data)

    quotation.save(ignore_permissions=True)

    terms_payload = data.get("terms")
    if terms_payload:
        sync_quotation_terms(quotation, terms_payload)

    return quotation


def get_quotation_by_id(quotation_id):
    quotation = frappe.get_doc("Quotation", quotation_id)
    customer_name = (
        frappe.db.get_value("Customer", quotation.party_name, "customer_name")
        if quotation.quotation_to == "Customer"
        else None
    )

    data = {
        "id": quotation.name,
        "title": quotation.title,
        "quotationTo": quotation.quotation_to,
        "customerId": quotation.party_name,
        "customerName": customer_name,
        "currency": quotation.currency,
        "exchangeRate": quotation.conversion_rate,
        "postingDate": quotation.transaction_date,
        "validTill": quotation.valid_till,
        "taxCategory": quotation.tax_category,
        "customerAddressId": quotation.customer_address,
        "billingAddress": quotation.address_display,
        "shippingAddressId": quotation.shipping_address_name,
        "shippingAddress": quotation.shipping_address,
        "salesTaxTemplate": quotation.taxes_and_charges,
        "status": quotation.status,
        "docstatus": quotation.docstatus,
        "roundingAdjustment": quotation.rounding_adjustment,
        "roundedTotal": quotation.rounded_total,
        "totalQty": quotation.total_qty,
        "totalTax": quotation.total_taxes_and_charges,
        "netTotal": quotation.net_total,
        "grandTotal": quotation.grand_total,
        "inWords": quotation.in_words,
        "detailedLostReason": quotation.order_lost_reason,
        "documentType": "Quotation", # Default, overridden below
        "lostReason": None,
        "items": [],
        "taxes": [],
        "charges": [],
        "terms": {},
    }

    ext_details = quotation.get("custom_extended_details", [])
    if ext_details:
        data["documentType"] = ext_details[0].document_type

    lost_rsns = quotation.get("lost_reasons", [])
    if lost_rsns:
        data["lostReason"] = lost_rsns[0].lost_reason

    for item in quotation.items:
        tax_info = _get_tax(item.item_code, quotation.tax_category)

        item_data = {
            "itemCode": item.item_code,
            "itemName": item.item_name,
            "uom": item.uom,
            "quantity": item.qty,
            "rate": item.price_list_rate,
            "discount": item.discount_percentage,
            "discountAmount": item.discount_amount,
            "amount": item.amount,
            "isAlternative": bool(item.is_alternative),
            "taxInfo": tax_info,
        }

        metadata = get_extended_item_detail(item.item_code)
        if metadata:
            meta = metadata[0]
            item_data.update(
                {
                    "hsnCode": meta.get("hsn_code"),
                    "packingUnit": meta.get("packing_unit"),
                    "packingSize": meta.get("packing_size"),
                }
            )

        data["items"].append(item_data)

    total_tax = 0
    total_charges = 0

    for tax in quotation.get("taxes", []):
        amount = tax.tax_amount or 0
        account = frappe.get_cached_value(
            "Account", tax.account_head, ["account_type", "account_name"], as_dict=True
        )

        account_type = account.account_type if account else None
        account_name = account.account_name if account else None

        row = {
            "accountHead": tax.account_head,
            "accountName": account_name,
            "chargeType": tax.charge_type,
            "rate": tax.rate,
            "amount": amount,
            "description": tax.description,
        }

        if account_type == "Tax":
            data["taxes"].append(row)
            total_tax += amount
        else:
            data["charges"].append(row)
            total_charges += amount

    data["totalCalculatedTax"] = total_tax
    data["totalCalculatedCharges"] = total_charges

    if quotation.tc_name and frappe.db.exists(
        "Terms and Conditions", quotation.tc_name
    ):
        tc_content = frappe.db.get_value(
            "Terms and Conditions", quotation.tc_name, "terms"
        )
        try:
            data["terms"]["selling"] = json.loads(tc_content)
        except Exception:
            data["terms"]["selling"] = tc_content

    attachments = frappe.db.get_all(
        "File",
        filters={
            "attached_to_doctype": "Quotation",
            "attached_to_name": quotation_id,
        },
        fields=[
            "name",
            "file_name",
            "file_url",
            "file_size",
            "file_type",
            "is_private",
            "creation",
        ],
        order_by="creation desc",
    )
    data["attachments"] = [att for att in attachments]

    return data


def get_quotations(filters=None, page=1, page_size=20, search=None, sort_by="creation", sort_order="desc"):
    filters = filters or {}
    
    frappe_filters = build_quotation_filters(filters)

    or_filters = []
    if search:
        search = str(search).strip()
        or_filters = [
            ["name", "like", f"%{search}%"],
            ["party_name", "like", f"%{search}%"],
            ["customer_name", "like", f"%{search}%"],
            ["status", "like", f"%{search}%"],
            ["currency", "like", f"%{search}%"],
            ["order_lost_reason", "like", f"%{search}%"],
        ]

    start = (page - 1) * page_size
    
    order_string = f"{sort_by} {sort_order}" if sort_by else "creation desc"

    quotations = frappe.get_all(
        "Quotation",
        filters=frappe_filters,
        or_filters=or_filters if search else None,
        fields=[
            "name",
            "quotation_to",
            "party_name",
            "customer_name",
            "transaction_date",
            "valid_till",
            "base_grand_total",
            "grand_total",
            "currency",
            "status",
            "order_lost_reason"
        ],
        limit_start=start,
        limit_page_length=page_size,
        order_by=order_string,
    )

    total_quotations = len(
        frappe.get_all(
            "Quotation",
            filters=frappe_filters,
            or_filters=or_filters if search else None,
            pluck="name",
        )
    )

    total_pages = (total_quotations + page_size - 1) // page_size

    quotation_names = [q.name for q in quotations]
    
    extended_map = {}
    lost_reasons_map = {}

    if quotation_names:
        ext_data = frappe.get_all(
            "Custom Quotation Extended Details",
            filters={"parent": ["in", quotation_names]},
            fields=["parent", "document_type"]
        )
        for d in ext_data:
            extended_map[d.parent] = d.document_type

        lr_data = frappe.get_all(
            "Quotation Lost Reason Detail",
            filters={"parent": ["in", quotation_names]},
            fields=["parent", "lost_reason"]
        )
        for lr in lr_data:
            lost_reasons_map[lr.parent] = lr.lost_reason


    for qt in quotations:
        qt_name = qt.name
        qt["id"] = qt.pop("name")
        qt["customer"] = qt.pop("party_name")
        qt["customerName"] = qt.pop("customer_name")
        qt["quotationTo"] = qt.pop("quotation_to")
        qt["postingDate"] = qt.pop("transaction_date")
        qt["validTill"] = qt.pop("valid_till")
        qt["total"] = qt.pop("grand_total")
        qt["baseGrandTotal"] = qt.pop("base_grand_total")
        qt["detailedLostReason"] = qt.pop("order_lost_reason")
        
        qt["documentType"] = extended_map.get(qt_name, "Quotation")
        qt["lostReason"] = lost_reasons_map.get(qt_name, None)

    return quotations, total_quotations, total_pages


def delete_quotation(quotation_id):
    quotation = frappe.get_doc("Quotation", quotation_id)
    if quotation.docstatus == 1:
        raise frappe.ValidationError(
            "Cannot delete a submitted Quotation. Cancel it first."
        )

    frappe.db.set_value(
        "Quotation",
        quotation_id,
        {"tc_name": None, "payment_terms_template": None},
        update_modified=False,
    )

    frappe.delete_doc("Quotation", quotation_id, ignore_permissions=True)

    tc_name = f"{quotation_id} Terms"
    if frappe.db.exists("Terms and Conditions", tc_name):
        frappe.delete_doc(
            "Terms and Conditions", tc_name, ignore_permissions=True, force=True
        )

    pt_name = f"{quotation_id} PT"
    if frappe.db.exists("Payment Terms Template", pt_name):
        template_doc = frappe.get_doc("Payment Terms Template", pt_name)
        terms_to_delete = [t.payment_term for t in template_doc.terms]

        frappe.delete_doc(
            "Payment Terms Template", pt_name, ignore_permissions=True, force=True
        )

        for term in terms_to_delete:
            is_used_elsewhere = frappe.db.exists(
                "Payment Terms Template Detail", {"payment_term": term}
            )
            if not is_used_elsewhere:
                try:
                    frappe.delete_doc("Payment Term", term, ignore_permissions=True)
                except frappe.exceptions.LinkExistsError:
                    pass


def update_quotation_status(quotation_id, action, payload=None):
    payload = payload or {}

    quotation = frappe.get_doc("Quotation", quotation_id)

    if not frappe.has_permission("Quotation", "write", quotation):
        raise frappe.PermissionError("No permission to modify this quotation")

    if action == "approved":
        if quotation.docstatus == 1:
            raise frappe.ValidationError("Quotation is already approved.")
        if quotation.docstatus == 2:
            raise frappe.ValidationError(
                "Cannot approve a cancelled quotation. Please amend it first."
            )

        quotation.submit()

        return {
            "id": quotation.name,
            "status": quotation.status,
            "docstatus": quotation.docstatus,
        }

    elif action == "cancelled":
        if quotation.docstatus == 2:
            raise frappe.ValidationError("Quotation is already cancelled.")
        if quotation.docstatus == 0:
            raise frappe.ValidationError(
                "Cannot cancel a Draft quotation. Submit it first."
            )

        quotation.cancel()

        return {
            "id": quotation.name,
            "status": quotation.status,
            "docstatus": quotation.docstatus,
        }

    elif action == "amend":
        if quotation.docstatus == 0:
            raise frappe.ValidationError("Quotation is already in Draft state.")
        if quotation.docstatus == 1:
            raise frappe.ValidationError(
                "Cannot amend a approved quotation. Cancel it first."
            )

        amended_doc = frappe.copy_doc(quotation)
        amended_doc.amended_from = quotation.name
        amended_doc.docstatus = 0
        amended_doc.insert()

        return {
            "id": amended_doc.name,
            "status": amended_doc.status,
            "docstatus": amended_doc.docstatus,
        }

    elif action == "lost":
        if quotation.docstatus == 0:
            raise frappe.ValidationError(
                "Cannot mark a Draft quotation as lost. Submit it first."
            )
        if quotation.docstatus == 2:
            raise frappe.ValidationError("Cannot mark a cancelled quotation as lost.")

        lost_reason = payload.get("lostReason") or payload.get("lost_reason")
        detailed_reason = payload.get("detailedReason") or payload.get(
            "detailed_reason"
        )

        if not lost_reason:
            raise frappe.ValidationError(
                "Lost Reason is mandatory when marking a quotation as lost."
            )

        ensure_lost_reason(lost_reason)

        quotation.set("lost_reasons", [])
        quotation.append("lost_reasons", {"lost_reason": lost_reason})

        quotation.order_lost_reason = detailed_reason
        quotation.status = "Lost"

        quotation.flags.ignore_validate_update_after_submit = True
        quotation.save(ignore_permissions=True)

        return {
            "id": quotation.name,
            "status": quotation.status,
            "docstatus": quotation.docstatus,
        }

    else:
        raise frappe.ValidationError(
            "Invalid action. Allowed: approved, cancelled, amend, lost"
        )