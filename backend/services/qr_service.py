"""
QR code generation — returns a base-64-encoded PNG string.
"""

import base64
from io import BytesIO

import qrcode
from PIL import Image


def generate_qr_base64(url: str, box_size: int = 10, border: int = 4) -> str:
    """
    Generate a QR code for *url* and return it as a base-64 PNG string
    (suitable for embedding in a data URI: ``data:image/png;base64,<return value>``).
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()
