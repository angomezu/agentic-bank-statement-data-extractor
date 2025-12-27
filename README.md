# Agentic Bank Statement PDF Extractor

This is a self-validating, agentic AI workflow system for extracting structured data from bank statement PDFs.  
It autonomously routes PDFs by modality (TEXT vs VISION), extracts schema-based fields, validates every value with evidence, and self-repairs until a quality threshold is met.

---

## What This Project Does

- Extracts structured data from **bank statement PDFs**
- Supports both:
  - **TEXT PDFs** (machine-readable)
  - **VISION PDFs** (scanned / image-based)
- Validates every extracted field with:
  - Evidence quotes from the source
  - PASS / FAIL / UNCERTAIN status
- Automatically repairs failed fields in bounded loops
- Produces auditable outputs suitable for finance, compliance, and analytics

---

## Key Features

- **Agentic workflow** with explicit roles and contracts
- **Autonomous routing**: TEXT vs VISION detection
- **Evidence-grounded validation**
- **Self-repair and convergence**
- **Deterministic bank name control** (never inferred from PDF)
- **Human-readable UI** + machine-consumable outputs

---

## High-Level Architecture

**Flow:**

1. User uploads a PDF via UI  
2. Router Agent determines TEXT vs VISION  
3. Specialized Extraction Agent runs  
4. Validator Agent checks each field against source text  
5. Repair Agent fixes failures (bounded loop)  
6. Final structured outputs + metadata returned  

> See `assets/images/` for full architecture and UI screenshots.

---

## Installation & Setup

This project can be run locally to reproduce both **TEXT** and **VISION (OCR)** workflows.

A full, step-by-step installation and reproducibility guide is provided separately to keep this README concise.

👉 **See:** [`assets/docs/INSTALLATION.md`](assets/docs/INSTALLATION.md)

The installation guide covers:
- Environment setup (Python, virtualenv, dependencies)
- OpenAI API configuration
- Running the Streamlit UI
- Reproducing TEXT vs VISION routing
- Expected artifacts and outputs
- Troubleshooting common issues

---

## Agents Overview

### Router Agent (`app/pdf_router.py`)
- Inspects PDF content
- Routes to:
  - `TEXT` pipeline (machine-readable)
  - `VISION` pipeline (scanned PDFs)

### TEXT Extraction Agent (`app/orchestrator_text.py`)
- Uses `pdfplumber`
- Extracts full schema from text
- Validates and repairs until pass threshold

### VISION Extraction Agent (`app/orchestrator_vision.py`)
- Renders pages to images via PyMuPDF
- Performs OCR using a vision-capable LLM
- Extracts OCR-specific schema
- Shares the same validation/repair loop

### Validator Agent (`app/utility_pdf.py`)
- Verifies each field against source text
- Produces evidence quotes and confidence
- Outputs PASS / FAIL / UNCERTAIN per field

### Repair Agent (loop logic in orchestrators)
- Applies deterministic fixes
- Re-extracts only failed fields
- Tracks best round by pass rate

---

## Extracted Schemas

### TEXT PDFs
- bank_name (UI-configured)
- customer_name
- customer_address
- account_number
- statement_date
- initial_balance
- deposits_other_credits
- ATM_Withdrawals_Debits
- VISA_Check_Card_Purchases_Debits
- Withdrawals_Other_Debits
- total_checks_paid
- ending_balance

### VISION / OCR PDFs
- bank_name (UI-configured)
- account_number
- statement_date
- beginning_balance
- total_deposits_and_other_credits
- total_withdrawals_and_other_debits
- total_service_charges_fees
- ending_balance

---

## Outputs

Each run returns:

- **Final Table**  
  Structured dictionary (exportable to CSV / Excel)

- **Validation Report**  
  Per-field:
  - status
  - extracted value
  - evidence quote
  - suggested value
  - confidence
  - reason

- **Run Metadata**
  - rounds_used
  - best_round
  - final_pass_rate
  - OCR parameters (if applicable)


---
Security & Data Privacy

PDFs are processed locally for routing and rendering

Only extracted text (TEXT pipeline) or rendered images (VISION pipeline) are sent to OpenAI APIs

PDFs are not uploaded as files to OpenAI storage

No training or persistence of user data by default

Designed to support:

On-prem deployment

API isolation

Database-backed auditing (future work)

Planned Extensions

Batch / multi-file processing

Persistent storage (PostgreSQL / BigQuery)

FastAPI service layer

CRM / ERP integrations

Additional OCR format adapters

Role-based access and audit logging

Research Positioning

This project demonstrates:

Agentic AI systems with bounded autonomy

Evidence-based self-validation

Reliable document understanding pipelines

Practical AI safety via explicit invariants

License

MIT

Author

Angel A. Barrera
Agentic Systems • Data Engineering • Applied AI
