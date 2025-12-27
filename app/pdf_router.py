import re
from typing import Dict, Any
import pdfplumber

def extract_text_pdfplumber(pdf_path: str) -> str:
    """
    Extracts text from every page using pdfplumber.

    Why this function:
    - We need a consistent local method to detect whether the PDF contains real text.
    - If the PDF is scanned (image-only), extract_text() returns empty or near-empty output.

    Returns:
        str: concatenated text from all pages (may be empty).
    """
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            parts.append(page_text)
    return "\n".join(parts).strip()


def route_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    RouterAgent: decides whether to use TEXT extraction or VISION extraction.

    Decision idea:
    - If we can extract enough readable words, it's a text PDF -> TEXT route.
    - If text is empty or tiny, it's likely scanned -> VISION route.

    Returns:
        dict with route decision and diagnostics.
    """
    text = extract_text_pdfplumber(pdf_path)

    text_len = len(text)
    words = re.findall(r"[A-Za-z]{2,}", text)
    word_count = len(words)

    digits = re.findall(r"\d", text)
    digit_count = len(digits)
    digit_ratio = digit_count / max(text_len, 1)

    # Heuristics you can tune later.
    # We require a minimum amount of text and words to consider it "readable text PDF".
    is_text_readable = (text_len >= 300) and (word_count >= 30)

    route = "TEXT" if is_text_readable else "VISION"

    return {
        "route": route,
        "text_len": text_len,
        "word_count": word_count,
        "digit_ratio": round(digit_ratio, 4),
        "preview": text[:400],
    }
