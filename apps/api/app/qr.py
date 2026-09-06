from __future__ import annotations

import os
from io import BytesIO

import segno


def table_menu_url(public_token: str) -> str:
    base = os.getenv("PUBLIC_WEB_BASE_URL", "http://localhost:3000").rstrip("/")
    return f"{base}/t/{public_token}"


def qr_png_bytes(public_token: str) -> bytes:
    qr = segno.make(table_menu_url(public_token), error="m")
    buffer = BytesIO()
    qr.save(buffer, kind="png", scale=8, border=2)
    return buffer.getvalue()
