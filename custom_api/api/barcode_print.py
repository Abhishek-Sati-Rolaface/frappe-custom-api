"""
Barcode Print API
- Generate printable HTML label
- Support for Thermal printer & normal printer
- QR Code & Code128 barcode formats
"""

import frappe
from frappe import _
from custom_api.utils.response import send_response


@frappe.whitelist(allow_guest=False, methods=["POST"])
def get_barcode_label():
    """
    Get printable HTML for barcode label
    Input: {
        "barcode": "12345678",
        "format": "html" or "pdf"
    }
    """
    try:
        data = frappe.request.get_json()
        barcode = data.get("barcode", "").strip()
        label_format = data.get("format", "html")  # html or pdf
        
        if not barcode:
            return send_response(
                status="error",
                message="'barcode' is required",
                data=None,
                status_code=400,
                http_status=400
            )
        
        # Get barcode details
        barcode_record = frappe.db.get_value(
            "Item Barcode",
            {"barcode": barcode},
            ["item", "batch"],
            as_dict=True
        )
        
        if not barcode_record:
            return send_response(
                status="error",
                message=f"Barcode '{barcode}' not found",
                data=None,
                status_code=404,
                http_status=404
            )
        
        item_code = barcode_record["item"]
        
        # Get item details
        item_doc = frappe.db.get_value(
            "Item",
            item_code,
            ["item_name", "item_code"],
            as_dict=True
        )
        
        if label_format == "pdf":
            # Return PDF download link
            html_content = generate_label_html(barcode, item_doc)
            
            # Generate PDF
            from frappe.utils.pdf import get_pdf
            pdf_content = get_pdf(html_content)
            
            frappe.response['filename'] = f"barcode_{barcode}.pdf"
            frappe.response.data = pdf_content
            frappe.response['filetype'] = 'pdf'
            
            return {
                "status": "success",
                "message": "PDF generated",
                "file": f"barcode_{barcode}.pdf"
            }
        else:
            # Return HTML for browser printing
            html_content = generate_label_html(barcode, item_doc)
            
            return send_response(
                status="success",
                message="Label HTML generated",
                data={
                    "html": html_content,
                    "barcode": barcode,
                    "item_code": item_code,
                    "item_name": item_doc.get("item_name")
                },
                status_code=200,
                http_status=200
            )
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Barcode Label Error")
        return send_response(
            status="error",
            message=str(e),
            data=None,
            status_code=500,
            http_status=500
        )


def generate_label_html(barcode, item_doc):
    """Generate HTML for barcode label"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Barcode Label</title>
        <style>
            body {{
                margin: 0;
                padding: 10px;
                font-family: Arial, sans-serif;
                background: white;
            }}
            
            .label {{
                width: 80mm;
                height: 50mm;
                border: 1px solid #ccc;
                padding: 8px;
                text-align: center;
                display: inline-block;
                page-break-after: always;
            }}
            
            .barcode-img {{
                width: 100%;
                height: 25mm;
                margin: 5px 0;
            }}
            
            .item-name {{
                font-size: 10pt;
                font-weight: bold;
                margin: 3px 0;
                word-wrap: break-word;
            }}
            
            .barcode-text {{
                font-size: 9pt;
                font-family: monospace;
                margin: 2px 0;
            }}
            
            .item-code {{
                font-size: 8pt;
                color: #666;
            }}
            
            @media print {{
                body {{
                    margin: 0;
                    padding: 0;
                }}
                .label {{
                    border: none;
                    margin: 0;
                    page-break-inside: avoid;
                }}
            }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
    </head>
    <body>
        <div class="label">
            <svg id="barcode-{barcode}"></svg>
            <script>
                JsBarcode("#barcode-{barcode}", "{barcode}", {{
                    format: "CODE128",
                    width: 2,
                    height: 50,
                    displayValue: false
                }});
            </script>
            <div class="item-name">{item_doc.get('item_name', '')}</div>
            <div class="barcode-text">{barcode}</div>
            <div class="item-code">Code: {item_doc.get('item_code', '')}</div>
        </div>
    </body>
    </html>
    """
    
    return html


@frappe.whitelist(allow_guest=False, methods=["POST"])
def print_multiple_barcodes():
    """
    Print multiple barcodes at once
    Input: {
        "barcodes": ["12345678", "87654321", ...],
        "format": "html" or "pdf"
    }
    """
    try:
        data = frappe.request.get_json()
        barcodes = data.get("barcodes", [])
        label_format = data.get("format", "html")
        
        if not barcodes or not isinstance(barcodes, list):
            return send_response(
                status="error",
                message="'barcodes' array is required",
                data=None,
                status_code=400,
                http_status=400
            )
        
        if len(barcodes) > 100:
            return send_response(
                status="error",
                message="Maximum 100 barcodes at once",
                data=None,
                status_code=400,
                http_status=400
            )
        
        label_html_list = []
        
        for barcode in barcodes:
            barcode_record = frappe.db.get_value(
                "Item Barcode",
                {"barcode": barcode.strip()},
                ["item"],
                as_dict=True
            )
            
            if barcode_record:
                item_code = barcode_record["item"]
                item_doc = frappe.db.get_value(
                    "Item",
                    item_code,
                    ["item_name", "item_code"],
                    as_dict=True
                )
                html = generate_label_html(barcode.strip(), item_doc)
                label_html_list.append(html)
        
        if label_format == "pdf":
            # Combine all labels and generate single PDF
            combined_html = "<html><body>" + "".join(label_html_list) + "</body></html>"
            
            from frappe.utils.pdf import get_pdf
            pdf_content = get_pdf(combined_html)
            
            frappe.response['filename'] = f"barcodes_{len(barcodes)}_labels.pdf"
            frappe.response.data = pdf_content
            frappe.response['filetype'] = 'pdf'
            
            return {
                "status": "success",
                "message": f"PDF generated for {len(label_html_list)} barcodes",
                "count": len(label_html_list)
            }
        else:
            # Return combined HTML
            combined_html = "<html><head><style>body {margin: 0; padding: 10px;}</style></head><body>" + "".join(label_html_list) + "</body></html>"
            
            return send_response(
                status="success",
                message=f"HTML generated for {len(label_html_list)} barcodes",
                data={
                    "html": combined_html,
                    "count": len(label_html_list),
                    "total_requested": len(barcodes)
                },
                status_code=200,
                http_status=200
            )
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Print Multiple Barcodes Error")
        return send_response(
            status="error",
            message=str(e),
            data=None,
            status_code=500,
            http_status=500
        )
