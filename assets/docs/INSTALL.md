# Installation & Reproducibility Guide

This document describes how to install, configure, and run the **D.A.R.E. Agentic Bank Statement Extraction System** locally in order to reproduce both **TEXT** and **VISION (OCR)** workflows.

The instructions below assume no prior knowledge of the codebase.

---

## 1. Tech Stack

- **Language / Runtime:** Python 3.10+
- **UI:** Streamlit
- **PDF Text Extraction:** pdfplumber
- **PDF → Image Rendering (OCR path):** PyMuPDF (`fitz`)
- **LLM / Vision OCR:** OpenAI Responses API (text + vision-capable model)
- **Data Handling:** JSON contracts, pandas (UI display)

---

## 2. System Architecture (High-Level)

The system preserves a strict separation of concerns:

- **Router → Orchestrator → Utility → UI**
- Validation and repair loops are core to both pipelines
- Bank name is UI-configured and protected from auto-modification

Each run produces:
- A final structured table (dictionary)
- A full per-field validation report
- Run metadata (rounds used, best round, pass rate, OCR details if applicable)

Refer to the architecture diagram in `assets/images/architecture.png` for a visual overview.

---

## 3. Prerequisites

Ensure the following are available on your system:

- Python **3.10 or newer** available on PATH
- Git (optional, if cloning the repository)
- An **OpenAI API key** with access to the configured models  
  - You must have an active OpenAI account
  - A minimum of **$5.00 USD credit** is recommended for OCR testing

---

## 4. Get the Code

#### Option A — Clone the Repository

```bash
git clone https://github.com/angomezu/agentic-bank-statement-extractor.git
cd agentic-bank-statement-extractor
```

#### Option B — Download ZIP

- Download the repository as a ZIP
- Unzip it locally

```bash
cd into the extracted project directory
```

## 5. Create and Activate a Virtual Environment

- Create a Python virtual environment at the project root:

```bash
python -m venv .venv
```
- Activate it:

macOS / Linux

```bash
source .venv/bin/activate
```

Windows (PowerShell)

```bash
.venv\Scripts\Activate.ps1
```

- Verify activation:

```bash
python --version
```
---
## 6. Install Dependencies

Upgrade pip and install required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Notes

- The TEXT pipeline requires pdfplumber
- The VISION pipeline requires PyMuPDF (fitz) for PDF-to-image rendering
- All required dependencies are declared in requirements.txt

---
## 7. Configure Environment Variables

This variables will determine the speed, prediction accuracy, and **cost**.

- Create a .env file at the project root (same level as requirements.txt).

```bash
OPENAI_API_KEY=YOUR_KEY_HERE
```

- Text pipeline model (extraction / validation / repair)

```bash
LLM_MODEL=gpt-4.1-mini
```

- Vision model for OCR (defaults to LLM_MODEL if omitted)

```bash
VISION_MODEL=gpt-4.1-mini
```

- OCR rendering controls

```bash
OCR_DPI=200
OCR_MAX_PAGES=10
```

#### Configuration Behavior

- LLM_MODEL: Drives schema extraction, validation, and repair logic.

- VISION_MODEL
  - Drives OCR for scanned PDFs.
  - If omitted, the system falls back to LLM_MODEL.

- OCR_DPI and OCR_MAX_PAGES: Control OCR quality vs. speed and cost.

---
## 8. Run the Streamlit UI (Local)

- Start the application:

```bash
streamlit run app/ui_streamlit.py
```

- Open the local URL printed in the terminal (typically):

```bash
http://localhost:8501
```
---

## 9. Reproduce TEXT vs VISION Workflows

#### 9.1 TEXT Run (Machine-Readable PDF)

#### IMPORTANT: 

- This workflow version has a deterministc approach; in the essence that the fields being extracted are determined by the two samples included in this repository.
- The reproduction of this system assumes you will use the same files avaiable here: [Bank Statements](assets/bank_statements)
- The LLM does not take into account any other formats and may or may not produce a bad prediction and result if a different set of PDFs is being provided.

#### To begin:

- Upload a machine-readable bank statement PDF
- Select the Configured bank name from the dropdown
- Confirm the router decision shows:

```bash
route = TEXT
```

- Click Extract and Validate
  - Verify outputs:
    - Final structured table is populated
    - Validation summary and per-field report are visible
    - Pass rate and run metadata are shown

##### 9.2 VISION Run (Scanned / Image PDF)

- Upload a scanned or image-based statement (e.g. statement_ocr.pdf)
- Select the Configured bank name
- Confirm the router decision shows:

```bash
route = VISION
```

- Click Extract and Validate
  - Verify outputs:
    - OCR-specific schema fields are populated
    - Validation report includes evidence quotes

- Metadata includes:
  - ocr_pages_used
  - ocr_dpi
  - vision_model

---

## 10. Expected Artifacts and Outputs

- Uploaded PDFs are saved under:

```bash
artifacts/
```

- VISION runs additionally write rendered page images to:

```bash
artifacts/rendered_pages/
```

- Each run returns three primary objects internally:
  - final_table — structured extraction result (dict)
  - final_report — per-field validation report
  - meta — run metadata (rounds, pass rate, OCR details)

---

## 11. Troubleshooting (Common Issues)

- Missing API key
  - Ensure OPENAI_API_KEY is set correctly in .env.

- VISION runs are slow or expensive
  - Reduce OCR_MAX_PAGES and/or OCR_DPI.

- Import or module errors
  - Confirm:
    - Virtual environment is activated
    - pip install -r requirements.txt completed successfully
    - Unexpected bank name behavior
    - Bank name must be selected in the UI.
    - It is intentionally never inferred from PDF content.
---

## 12. Reproducibility Notes

- Validation and repair loops are bounded (no infinite retries)
- Best round is selected by highest validation pass rate
- Bank name invariants are enforced deterministically

The system is designed to be extended to batch processing and API deployment without architectural changes
