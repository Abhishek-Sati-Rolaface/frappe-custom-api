
def generate_barcode(value):
    """Code128 barcode SVG generate karta hai"""
    if not value:
        return ""
    
    try:
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        CODE128 = barcode.get_barcode_class("code128")
        buffer = BytesIO()
        CODE128(str(value), writer=SVGWriter()).write(buffer)

        svg_content = buffer.getvalue().decode("utf-8")

        # Sirf <svg> tag extract karo (DOCTYPE remove karo)
        start = svg_content.find("<svg")
        return svg_content[start:] if start != -1 else ""

    except Exception as e:
        return f"<p style='color:red;'>Barcode Error: {e}</p>"