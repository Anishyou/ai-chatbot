"""
Helpers to fetch a menu file and extract text from PDFs or images.
Requires: requests, pdfplumber, pillow, pytesseract
"""

import io
from typing import Tuple

import pdfplumber
import requests
from PIL import Image
import pytesseract


def fetch_bytes(url: str, timeout: int = 20) -> Tuple[bytes, str]:
    """
    Download a URL and return (bytes, content_type).
    Raises for non-2xx.
    """
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content, (r.headers.get("content-type") or "").lower()


def parse_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF (best-effort)."""
    parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            parts.append(txt)
    return "\n".join(parts).strip()


def parse_image(img_bytes: bytes) -> str:
    """OCR an image using Tesseract (auto language)."""
    img = Image.open(io.BytesIO(img_bytes))
    # You can pass lang="eng+deu" if you installed those packs
    return pytesseract.image_to_string(img)


def parse_menu_url(url: str) -> str:
    """
    Fetch a URL and extract text if it's a PDF or an image.
    If it's HTML, returns a plain-text fallback.
    """
    raw, ctype = fetch_bytes(url)
    lower = url.lower()

    if "pdf" in ctype or lower.endswith(".pdf"):
        return parse_pdf(raw)

    if ("image" in ctype) or any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")):
        return parse_image(raw)

    # Fallback: try HTML parsing
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw, "html.parser")
        return soup.get_text("\n", strip=True)
    except Exception:
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return ""
