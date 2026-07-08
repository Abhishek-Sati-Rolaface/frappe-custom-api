import frappe

def before_insert(doc, method):
    if doc.is_return == 1:
        sales_invoice = frappe.get_doc("Sales Invoice", doc.return_against)
        doc.conversion_rate = sales_invoice.conversion_rate
        payment_mode = sales_invoice.custom_details[0].get("payment_mode") if sales_invoice.custom_details else None

        if not doc.custom_details:
            doc.append("custom_details", {"payment_mode": payment_mode})
        else:
            doc.custom_details[0].payment_mode = payment_mode

                
        if not doc.custom_details:
            doc.append("custom_details", {"payment_mode": payment_mode})
        else:
            doc.custom_details[0].payment_mode = payment_mode

        naming_series_options = frappe.get_meta("Sales Invoice").get_field("naming_series").options
        series_list = [s.strip() for s in naming_series_options.split("\n") if s.strip()]

        si_prefix = series_list[1]
        cn_prefix = series_list[2] if len(series_list) > 1 else None
        if not cn_prefix:
            frappe.throw(
                            _("Credit Note prefix is not configured. Please create and configure a Credit Note prefix in the Naming Series before proceeding.")
                        )
        next_name = frappe.model.naming.make_autoname(series_list[0])
        doc.name = next_name.replace(si_prefix, cn_prefix, 1)
        doc.naming_series = series_list[3]
        doc.flags.name_set = True 
        print("Return Invoice — name:", doc.name)