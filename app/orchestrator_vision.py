import os
from typing import Dict, Any, Tuple, Optional

from app.config import load_config
from app.orchestrator_text import (
    force_single_bank_field,
    pass_rate,
    merge_updates,
    normalize_report,
)
from app.utility_pdf import (
    create_openai_client,
    extract_json_object,
    llm_validate_statement_fields,
    apply_suggestions,
    llm_fix_failed_fields,
    log_event,
)



def llm_extract_ocr_statement_fields(
    client,
    statement_text: str,
    model: str,
) -> str:
    """
    OCR-specific extraction for the SAMPLE 'Statement of Account' scanned format.
    This schema is intentionally different from the TEXT pipeline schema.
    """
    schema_keys = [
        "bank_name",
        "account_number",
        "statement_date",
        "beginning_balance",
        "total_deposits_and_other_credits",
        "total_withdrawals_and_other_debits",
        "total_service_charges_fees",
        "ending_balance",
    ]

    prompt = (
        "You are extracting fields from a SCANNED (OCR) bank statement in the "
        "'Statement of Account' format.\n\n"
        "Return ONLY a valid JSON object with EXACTLY these keys:\n"
        + ", ".join(schema_keys)
        + "\n\n"
        "Rules:\n"
        "1) If a value is missing or cannot be found, set it to null.\n"
        "2) Preserve numbers as strings exactly as shown (commas/decimals). "
        "Do not add currency symbols.\n"
        "3) account_number: extract the full account number as shown (digits only if possible).\n"
        "4) statement_date: extract the statement date shown on the statement (e.g., '01/31/2024').\n"
        "5) beginning_balance / ending_balance: use the 'Summary of Your Account' box when present.\n"
        "6) totals: use the totals in the 'Summary of Your Account' box when present.\n"
        "7) Do not include extra keys. Do not include markdown fences.\n\n"
        "OCR STATEMENT TEXT:\n"
        + statement_text
    )

    log_event("llm_ocr_extract_request", {"model": model, "text_len": len(statement_text)})

    resp = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=500,
    )

    out = (resp.output_text or "").strip()

    log_event("llm_ocr_extract_response", {"model": model, "output_preview": out[:300]})

    return out


def run_vision_pipeline(
    pdf_path: str,
    max_rounds: int = 2,
    min_pass_rate: float = 0.90,
    configured_bank_name: Optional[str] = None,
) -> Tuple[Dict[str, Any], list, Dict[str, Any]]:
    """
    OCR/image-based pipeline for the scanned 'Statement of Account' format.
    Output contract matches TEXT pipeline: (final_table, final_report, meta).
    """
    config = load_config()
    model = config["LLM_MODEL"]
    vision_model = config.get("VISION_MODEL", model)

    client = create_openai_client(config["OPENAI_API_KEY"])
    from app.utility_pdf import render_pdf_to_images, llm_ocr_images_to_text

    img_dir = os.path.join("artifacts", "rendered_pages")
    image_paths = render_pdf_to_images(
        pdf_path=pdf_path,
        out_dir=img_dir,
        dpi=int(config.get("OCR_DPI", 200)),
        max_pages=int(config.get("OCR_MAX_PAGES", 10)),
    )

    statement_text = llm_ocr_images_to_text(
        client=client,
        image_paths=image_paths,
        model=vision_model,
    )

    # ---- Round 1 extraction (OCR-specific schema) ----
    raw = llm_extract_ocr_statement_fields(client, statement_text, model)
    extracted = extract_json_object(raw)

    if configured_bank_name:
        extracted["bank_name"] = configured_bank_name

    # ---- Initial validation ----
    raw_val = llm_validate_statement_fields(client, statement_text, extracted, model)
    parsed_val = extract_json_object(raw_val)
    report = normalize_report(parsed_val.get("report", []))

    if configured_bank_name:
        report = force_single_bank_field(report, configured_bank_name)

    current_rate = pass_rate(report)

    best_extracted = extracted
    best_report = report
    best_rate = current_rate
    best_round = 1

    round_num = 1
    while current_rate < min_pass_rate and round_num < max_rounds:
        corrected = apply_suggestions(extracted, report)

        if configured_bank_name:
            corrected["bank_name"] = configured_bank_name

        raw_fix = llm_fix_failed_fields(client, statement_text, corrected, report, model)
        try:
            fix_updates = extract_json_object(raw_fix) if raw_fix and raw_fix.strip() else {}
        except Exception:
            fix_updates = {}

        corrected = merge_updates(corrected, fix_updates)

        if configured_bank_name:
            corrected["bank_name"] = configured_bank_name

        raw_val2 = llm_validate_statement_fields(client, statement_text, corrected, model)
        parsed_val2 = extract_json_object(raw_val2)
        report2 = normalize_report(parsed_val2.get("report", []))

        if configured_bank_name:
            report2 = force_single_bank_field(report2, configured_bank_name)

        extracted = corrected
        report = report2
        current_rate = pass_rate(report)

        if current_rate >= best_rate:
            best_rate = current_rate
            best_extracted = extracted
            best_report = report
            best_round = round_num + 1

        round_num += 1

    return best_extracted, best_report, {
        "rounds_used": round_num,
        "best_round": best_round,
        "final_pass_rate": best_rate,
        "ocr_pages_used": len(image_paths),
        "ocr_dpi": int(config.get("OCR_DPI", 200)),
        "vision_model": vision_model,
    }
