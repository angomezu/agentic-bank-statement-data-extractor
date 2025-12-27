# Agentic Workflow for Data Extraction From Bank Statements Using OpenAI API

<!-- Technology Stack Logos -->
<div align="center" style="display: flex; justify-content: center; gap: 24px; margin-top: 20px; margin-bottom: 20px;">
  <img src="assets/images/python_logo.png" height="80" />
  <img src="assets/images/pymupdf_logo.png" height="80" />
  <img src="assets/images/OpenAI-Logo-2022.png" height="80" />
  <img src="assets/images/534702.png" height="80" />
</div

<p align="center">
  <img src="assets/images/Second_Module_3.png" width=1250" />
</p>
<p align="center">
  <em>Figure 1: Result of using agents to extract data from a bank statement PDF that is image-based.</em>
</p>

Reliable data extraction from documentation (PDFs) remains a hard problem in production systems. Documents like bank statements vary widely across institutions and are frequently delivered as a mix of machine-readable PDFs and scanned, image-based documents. Layout changes, noisy tables, and inconsistent formatting routinely break rule-based parsers and template-driven solutions, forcing manual review and introducing downstream risk.

This project was built to levarage the power of LLMs to treat data extraction as an **iterative, fast, and self-correcting process**. The result is a reproducible, auditable, and extensible foundation for bank statement ingestion that prioritizes correctness, explainability, and robustness over brittle heuristics.

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

## Installation & Setup

This project can be run locally to reproduce both **TEXT** and **VISION (OCR)** workflows.

A full, step-by-step installation and reproducibility guide is provided separately to keep this README concise.

👉 **See:** [Installation Guide](assets/docs/INSTALLATION.md)

The installation guide covers:
- Environment setup (Python, virtualenv, dependencies)
- OpenAI API configuration
- Running the Streamlit UI
- Reproducing TEXT vs VISION routing
- Expected artifacts and outputs
- Troubleshooting common issues

---

## High-Level Architecture

**Flow:**

1. User uploads a PDF via UI  
2. Router Agent determines TEXT vs VISION  
3. Specialized Extraction Agent runs  
4. Validator Agent checks each field against source text  
5. Repair Agent fixes failures (bounded loop)  
6. Final structured outputs + metadata returned  

<p align="center">
  <img src="assets/images/architecture.png" width=1250" />
</p>
<p align="center">
  <em>Figure 2: Agentic AI Workflow Architecture.</em>
</p>

---

## Security & Data Privacy

This system is designed with a **local-first processing model**, but it is important to clearly state its current security boundaries.

- PDF files are **processed locally** for routing (TEXT vs VISION) and for PDF-to-image rendering.
- **PDF files are never uploaded as files** to OpenAI or stored in external object storage.
- For LLM operations:
  - The **TEXT pipeline** sends extracted text segments to the OpenAI API.
  - The **VISION pipeline** sends rendered page images to the OpenAI API for OCR.
- As a result, **OpenAI has transient access to the extracted content or images** during API inference.
  - This access is **momentary** and used strictly to generate the requested response.
  - No user data is stored, trained on, or persisted by the system by default.

#### Current Limitations

- The system does **not yet apply automated redaction or masking** to sensitive values (e.g., account numbers, balances) before sending content to the LLM.
- All validation and repair steps operate on the same extracted content passed to the model.

#### Planned Security Enhancements

Future iterations can further harden privacy and compliance by adding:

- **Field-level masking or partial obfuscation** (e.g., last-4 digits only) before LLM calls.
- **Selective tokenization** of sensitive fields for validation-only workflows.
- **On-prem or self-hosted LLM deployments** for fully isolated environments.
- **Role-based access controls and audit logs** for multi-user deployments.

This design makes the current system suitable for **research, prototyping, and controlled environments**, while providing a clear path toward stricter security and compliance requirements in production settings.


---

## Designed to Support

- **On-prem deployment**  
  The system is designed to run entirely in a local or self-hosted environment, enabling use in regulated or security-sensitive contexts where data cannot leave controlled infrastructure.

- **API isolation**  
  Core extraction, validation, and repair logic is decoupled from the UI, allowing the workflow to be exposed as a service or integrated into existing systems without coupling to Streamlit or frontend concerns.

- **Database-backed auditing (future work)**  
  The architecture anticipates persistent storage of extractions, validation reports, evidence snippets, and run metadata to enable traceability, compliance reviews, and historical quality analysis.

---

## Planned Extensions

- **Batch / multi-file processing**  
  Support for high-volume ingestion pipelines where large sets of statements must be processed deterministically and monitored at scale.

- **Persistent storage (PostgreSQL / BigQuery)**  
  Centralized storage of structured outputs, validation results, and metadata to support analytics, monitoring, and downstream consumption.

- **FastAPI service layer**  
  A stateless API layer to expose the extraction workflow programmatically, enabling integration with internal services and external applications.

- **CRM / ERP integrations**  
  Direct handoff of validated financial data into operational systems to reduce manual data entry and reconciliation effort.

---

## Additional Capabilities (Planned)

- **Additional OCR format adapters**  
  Pluggable adapters for alternative OCR engines or document renderers to improve robustness across document types and vendors.

- **Role-based access and audit logging**  
  Fine-grained access control and immutable audit trails to support enterprise governance, compliance, and multi-user environments.

---

## Author

Angel A. Barrera
Agentic Systems • Data Engineering • Applied AI
