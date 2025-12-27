import json
from typing import Dict, Any, Tuple, Optional

from app.config import load_config
from app.utility_pdf import (
    extract_text_from_pdf,
    create_openai_client,
    extract_json_object,
    llm_extract_statement_fields,
    llm_validate_statement_fields,
    apply_suggestions,
    llm_fix_failed_fields,
)

def force_single_bank_field(report: list, bank_name: str) -> list:
    # Remove any existing bank_name entries
    report = [r for r in report if r.get("field") != "bank_name"]

    # Add exactly one deterministic bank_name entry
    report.append({
        "field": "bank_name",
        "status": "PASS",
        "extracted_value": bank_name,
        "evidence_quote": f"CONFIG: {bank_name}",
        "suggested_value": bank_name,
        "confidence": 1.0,
        "reason": "Bank name is configured from UI selection."
    })

    return report


def pass_rate(report: list) -> float:
    total = len(report)
    passed = sum(1 for r in report if r.get("status") == "PASS")
    return passed / total if total else 0.0


def merge_updates(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for k, v in updates.items():
        if k in merged and v is not None:
            merged[k] = v
    return merged


def normalize_report(report: list) -> list:
    for r in report:
        if r.get("status") != "FAIL":
            continue

        extracted_value = str(r.get("extracted_value") or "").strip()
        suggested_value = str(r.get("suggested_value") or "").strip()
        evidence = str(r.get("evidence_quote") or "")

        if extracted_value and (
            (suggested_value and suggested_value == extracted_value) or
            (evidence and extracted_value in evidence)
        ):
            r["status"] = "PASS"
            r["reason"] = "Auto-correct: evidence/suggested matches extracted."
            try:
                r["confidence"] = max(float(r.get("confidence") or 0), 0.95)
            except Exception:
                r["confidence"] = 0.95

    return report


def run_text_pipeline(
    pdf_path: str,
    max_rounds: int = 2,
    min_pass_rate: float = 0.90,
    configured_bank_name: Optional[str] = None,
) -> Tuple[Dict[str, Any], list, Dict[str, Any]]:
    config = load_config()
    model = config["LLM_MODEL"]

    client = create_openai_client(config["OPENAI_API_KEY"])
    statement_text = extract_text_from_pdf(pdf_path)

    # ---- Round 1 extraction ----
    raw = llm_extract_statement_fields(client, statement_text, model)
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
    }


def summarize_report(report: list) -> dict:
    total = len(report)
    passed = sum(1 for r in report if r.get("status") == "PASS")
    failed = sum(1 for r in report if r.get("status") == "FAIL")
    uncertain = sum(1 for r in report if r.get("status") == "UNCERTAIN")
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "uncertain": uncertain,
        "pass_rate": (passed / total) if total else 0.0,
    }


if __name__ == "__main__":
    final_table, final_report, meta = run_text_pipeline(
        "statement_sample1.pdf",
        configured_bank_name="Commerce Bank",
    )
    print(json.dumps(final_table, indent=2))
    print(meta)
