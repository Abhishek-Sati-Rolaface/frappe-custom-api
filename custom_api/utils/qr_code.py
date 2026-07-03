import frappe
import base64
from io import BytesIO


def get_qr_code_image(value):
    """Returns base64 PNG string of a QR code for use in Jinja templates"""
    try:
        import qrcode

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=4,
        )
        qr.add_data(str(value))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    except Exception as e:
        frappe.log_error(str(e), "QR Code Generation Error")
        return None