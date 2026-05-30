# import frappe
# import base64
# from io import BytesIO


# def generate_barcode(value):
#     """PNG barcode generate karta hai — SVG se zyada reliable hai PDF me"""
#     if not value:
#         return ""
#     try:
#         import barcode
#         from barcode.writer import ImageWriter

#         CODE128 = barcode.get_barcode_class("code128")
#         buffer = BytesIO()

#         CODE128(str(value), writer=ImageWriter()).write(buffer, options={
#             "module_height": 15.0,
#             "module_width": 0.8,
#             "quiet_zone": 6.5,
#             "write_text": False,
#             "dpi": 300
#         })

#         buffer.seek(0)
#         img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

#         return f'<img src="data:image/png;base64,{img_base64}" style="width:100%; max-width:350px; height:80px; image-rendering:pixelated;">'

#     except Exception as e:
#         frappe.log_error(str(e), "Barcode Generation Error")
#         return f"<p style='color:red;'>Error: {e}</p>"



# import frappe
# import base64
# from io import BytesIO


# def generate_barcode(value):
#     """PNG barcode generate karta hai"""
#     if not value:
#         return ""
#     try:
#         import barcode
#         from barcode.writer import ImageWriter

#         CODE128 = barcode.get_barcode_class("code128")
#         buffer = BytesIO()

#         CODE128(str(value), writer=ImageWriter()).write(buffer, options={
#             "module_height": 15.0,
#             "module_width": 0.8,
#             "quiet_zone": 6.5,
#             "write_text": False,
#             "dpi": 300
#         })

#         buffer.seek(0)
#         img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

#         return f'<img src="data:image/png;base64,{img_base64}" style="width:100%; max-width:350px; height:80px; image-rendering:pixelated;">'

#     except Exception as e:
#         frappe.log_error(str(e), "Barcode Generation Error")
#         return f"<p style='color:red;'>Error: {e}</p>"




import frappe
import base64
import tempfile
import os
from io import BytesIO


def generate_barcode(value):
    """PNG barcode generate karta hai — PDF ke liye temp file use karta hai"""
    if not value:
        return ""
    try:
        import barcode
        from barcode.writer import ImageWriter

        CODE128 = barcode.get_barcode_class("code128")
        buffer = BytesIO()

        CODE128(str(value), writer=ImageWriter()).write(buffer, options={
            "module_height": 15.0,
            "module_width": 0.8,
            "quiet_zone": 6.5,
            "write_text": False,
            "dpi": 300
        })

        buffer.seek(0)

        # Temp file me save karo
        tmp_file = tempfile.NamedTemporaryFile(
            suffix='.png',
            delete=False,
            dir="/tmp"
        )
        tmp_file.write(buffer.getvalue())
        tmp_file.flush()
        tmp_file.close()

        # file:// path use karo — wkhtmltopdf yeh read kar sakta hai
        return f'<img src="file://{tmp_file.name}" style="width:100%; max-width:350px; height:80px;">'

    except Exception as e:
        frappe.log_error(str(e), "Barcode Generation Error")
        return f"<p style='color:red;'>Error: {e}</p>"