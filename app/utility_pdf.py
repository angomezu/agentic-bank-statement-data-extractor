import os
import json
import time
import base64
from pathlib import Path
from typing import Dict, Any, List

import pdfplumber
import fitz
from openai import OpenAI


def log_event(event_type: str, payload: Dict[str, Any]):
    os.makedirs("logs", exist_ok=True)
    event = {
        "timestamp": time.time(),
        "type": event_type,
        "payload": payload,
    }
    with open("logs/events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def extract_text_from_pdf(pdf_path: str) -> str:
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def create_openai_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def render_pdf_to_images(
    pdf_path: str,
    out_dir: str,
    dpi: int = 200,
    max_pages: int = 10,
) -> List[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    try:
        page_count = min(len(doc), max_pages)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        image_paths: List[str] = []
        for i in range(page_count):
            pix = doc.load_page(i).get_pixmap(matrix=mat, alpha=False)
            img_path = out / f"page_{i+1:02d}.png"
            pix.save(str(img_path))
            image_paths.append(str(img_path))

        return image_paths
    finally:
        doc.close()


def _image_b64_png(path: str) -> str:
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def llm_ocr_images_to_text(
    client: OpenAI,
    image_paths: List[str],
    model: str,
) -> str:
    pages_text: List[str] = []

    for idx, path in enumerate(image_paths, start=1):
        b64 = _image_b64_png(path)
        prompt = (
            "You are an OCR engine for bank statements.\n"
            "Transcribe ALL visible text.\n"
            "Return plain text only (no JSON, no markdown).\n"
            "Preserve line breaks where possible.\n"
        )

        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"},
                    ],
                }
            ],
            max_output_tokens=7000,
        )

        page_text = (response.output_text or "").strip()
        log_event(
            "llm_ocr_page",
            {
                "model": model,
                "page": idx,
                "image_path": path,
                "text_len": len(page_text),
                "text_preview": page_text[:300],
            },
        )
        pages_text.append(page_text)

    return "\n\n".join(pages_text).strip()


def llm_extract_statement_fields(
    client: OpenAI,
    statement_text: str,
    model: str
) -> str:
    schema_keys = [
        "bank_name",
        "customer_name",
        "customer_address",
        "account_number",
        "statement_date",
        "initial_balance",
        "deposits_other_credits",
        "ATM_Withdrawals_Debits",
        "VISA_Check_Card_Purchases_Debits",
        "Withdrawals_Other_Debits",
        "total_checks_paid",
        "ending_balance",
    ]

    prompt = (
        "You are extracting fields from a bank statement.\n"
        "Return ONLY a valid JSON object with EXACTLY these keys:\n"
        + ", ".join(schema_keys)
        + "\n\n"
        "Rules:\n"
        "1) If a value is missing or cannot be found, set it to null.\n"
        "2) Preserve numbers as strings exactly as shown (including commas and decimals).\n"
        "3) For customer_address, return a single string with the full address.\n"
        "4) Do not include extra keys.\n"
        "5) Do not include markdown fences.\n\n"
        "BANK STATEMENT TEXT:\n"
        + statement_text
    )

    log_event(
        "llm_extract_request",
        {"model": model, "text_len": len(statement_text)}
    )

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=700,
    )

    output = (response.output_text or "").strip()

    log_event(
        "llm_extract_response",
        {"model": model, "output_preview": output[:300]}
    )

    return output


def llm_validate_statement_fields(
    client: OpenAI,
    statement_text: str,
    extracted: Dict[str, Any],
    model: str
) -> str:
    fields = list(extracted.keys())

    prompt = (
        "You are validating an extracted bank statement table against the original statement text.\n"
        "For EACH field, you MUST search the statement text and decide if the extracted value matches.\n\n"
        "Return ONLY valid JSON (no markdown).\n"
        "Return a single JSON object with one key: report.\n"
        "The value of report must be a JSON array of objects.\n"
        "Each object must contain exactly these keys:\n"
        "field, status, extracted_value, evidence_quote, suggested_value, confidence, reason\n\n"
        "Rules:\n"
        "1) status must be one of: PASS, FAIL, UNCERTAIN\n"
        "2) evidence_quote must be an exact substring copied from the statement text if found, otherwise 'NOT FOUND'\n"
        "3) If FAIL and the correct value is clearly present in the statement text, set suggested_value to the correct value.\n"
        "4) If UNCERTAIN, suggested_value must be null.\n"
        "5) confidence must be a number between 0 and 1.\n"
        "6) Do not invent values. Use ONLY the statement text.\n"
        "7) If a clearly labeled total matches the extracted value, status MUST be PASS.\n\n"
        "STATEMENT TEXT:\n"
        + statement_text
        + "\n\nEXTRACTED TABLE JSON:\n"
        + json.dumps(extracted, ensure_ascii=False)
        + "\n\nFIELDS TO VALIDATE:\n"
        + ", ".join(fields)
    )

    log_event(
        "llm_validate_request",
        {"model": model, "text_len": len(statement_text)}
    )

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=1500,
    )

    output = (response.output_text or "").strip()

    log_event(
        "llm_validate_response",
        {"model": model, "output_preview": output[:300]}
    )

    return output


def extract_json_object(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty text; no JSON to extract.")

    text = text.strip()

    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj = json.loads(text[i:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON object found in model output.")


def apply_suggestions(extracted: Dict[str, Any], report: list) -> Dict[str, Any]:
    corrected = dict(extracted)

    for item in report:
        field = item.get("field")
        if field == "bank_name":
            continue

        if item.get("status") in ("FAIL", "UNCERTAIN"):
            suggested = item.get("suggested_value")
            if suggested is not None and field in corrected:
                corrected[field] = suggested

    return corrected


def llm_fix_failed_fields(
    client: OpenAI,
    statement_text: str,
    current: Dict[str, Any],
    report: list,
    model: str
) -> str:
    to_fix = []
    for r in report:
        field = r.get("field")
        if not field or field == "bank_name":
            continue
        if r.get("status") in ("FAIL", "UNCERTAIN") and r.get("suggested_value") is None:
            to_fix.append(field)

    if not to_fix:
        return "{}"

    prompt = (
        "You are fixing specific fields in a bank statement extraction.\n"
        "Return ONLY valid JSON (no markdown). Output must contain ONLY these keys:\n"
        + ", ".join(to_fix)
        + "\n\n"
        "Rules:\n"
        "1) Use ONLY the statement text. Do not guess.\n"
        "2) Preserve amounts exactly as shown (commas/decimals), no currency symbols.\n"
        "3) If a field cannot be found, set it to null.\n\n"
        "STATEMENT TEXT:\n"
        + statement_text
        + "\n\nCURRENT EXTRACTION JSON:\n"
        + json.dumps(current, ensure_ascii=False)
        + "\n\nFIELDS TO FIX:\n"
        + ", ".join(to_fix)
    )

    log_event(
        "llm_fix_request",
        {"model": model, "fields_to_fix": to_fix}
    )

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=500,
    )

    output = (response.output_text or "").strip()

    log_event(
        "llm_fix_response",
        {"model": model, "output_preview": output[:300]}
    )

    return output
