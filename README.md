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

## Security & Data Privacy

- PDFs are processed locally for routing and rendering
- Only extracted text (TEXT pipeline) or rendered images (VISION pipeline) are sent to OpenAI APIs
- PDFs are not uploaded as files to OpenAI storage
- No training or persistence of user data by default

---

## Designed to support:

- On-prem deployment
- API isolation
- Database-backed auditing (future work)

---

## Planned Extensions

+ Batch / multi-file processing
- Persistent storage (PostgreSQL / BigQuery)
- FastAPI service layer
- CRM / ERP integrations

---

## Additional OCR format adapters

Role-based access and audit logging

---

## Research Positioning

This project demonstrates:

- Agentic AI systems with bounded autonomy
- Evidence-based self-validation
- Reliable document understanding pipelines
* Practical AI safety via explicit invariants

---

## Author

Angel A. Barrera
Agentic Systems • Data Engineering • Applied AI
