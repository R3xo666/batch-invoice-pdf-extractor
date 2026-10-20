# Technical Specification & Architecture: Batch Invoice PDF Extractor to Excel

**Target Role:** Elite Solutions Architect & Technical Specification Specialist  
**Domain:** Document Processing / PDF Parsing / Data Pipeline & Automation  
**Client Budget:** $30 | **Platform:** Discord Freelance Hub / Upwork  

---

## Phase 1: Architectural Assessment & Reality Check

### 1. Underlying Objective
The client runs a small business receiving 50+ diverse vendor invoices in PDF format weekly. The current workflow relies on slow, error-prone manual data entry into spreadsheets.
The goal is an autonomous, fault-tolerant local Python CLI tool that:
1. Recursively/batch scans an `--input-dir` containing PDF invoices.
2. Extracts core financial and identification fields:
   - `Invoice Number`
   - `Invoice Date`
   - `Vendor Name`
   - `Subtotal`
   - `Tax / VAT`
   - `Total Due`
3. Gracefully flags unlocatable or irregular fields as `"FLAGGED FOR REVIEW"` without crashing.
4. Consolidates valid and flagged records into a styled `monthly_summary.xlsx` spreadsheet (with dedicated summary and audit sheets).
5. Emits a secondary audit log (`batch_processing.log` or audit CSV) tracking file-by-file status (`SUCCESS`, `FLAGGED`, `FAILED`).
6. Delivers a synthetic test data generator script or 3 sample mock PDFs for immediate client verification.

---

### 2. Strategy Matrix

| Approach | Architecture | Pros | Cons | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **1. Heavyweight OCR (Tesseract / EasyOCR / PaddleOCR)** | Rasterize PDF pages into images and run computer-vision OCR models. | Can read scanned photocopies or flat image PDFs. | High latency (~2-5s per page), heavy C++ dependencies (`tesseract-ocr`, leptonica), high CPU/RAM overhead, prone to character misread (`O` vs `0`). | ❌ Overkill for 95% of digital native vendor invoices. |
| **2. Cloud LLM / Multimodal API (OpenAI Vision, Gemini Document, AWS Textract)** | Upload each PDF to a remote cloud API for zero-shot JSON extraction. | High accuracy across messy layouts. | Recurring API cost, latency, exposes client financial invoices to external third-party cloud APIs (privacy risk). | ❌ Violates local execution requirement; recurring API cost unacceptable on a $30 one-off budget. |
| **3. Pure Text Regex with `pypdf` / `pdfminer.six`** | Stream raw text strings and apply naive regex patterns. | Lightweight, zero native binaries. | Completely fails on multi-column layouts; words jumble together across tables. | ❌ Brittle on varied invoice layouts. |
| **4. Hybrid Layout-Aware Extraction: `pdfplumber` + RegEx Heuristics + Fallback Normalizer** | High-precision text extraction with word coordinates, spatial bounding boxes, and multi-pattern regex banks. | Pure Python, fast (<100ms per PDF), layout-aware, handles tables and varied vendor formats, zero external API costs. | Cannot parse scanned paper photographs without OCR fallback. | **✅ RECOMMENDED (Optimal)** |

#### Recommended Primary Approach:
**Strategy 4 (`pdfplumber` + Multi-Pass Heuristics + Fuzzy Regex Engine)**:
- Reads digital PDF text streams and layout tables.
- Leverages a regex pattern bank for dates (ISO, US, EU, alphanumeric), monetary figures (currency symbol stripping, thousand separators), and keyword anchors (`Invoice No`, `Bill To`, `Subtotal`, `VAT / Tax`, `Total Due`).
- Implements an anchor-proximity extractor: if regex misses, locates anchor tokens and inspects adjacent bounding boxes.
- Missing fields default gracefully to `"FLAGGED FOR REVIEW"`.

---

### 3. Obstacle & Failure Surface

1. **Vendor Schema Diversity:** Different vendors place Total Due at top right, bottom right, or inside a summary table. Dates arrive in `DD/MM/YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD`, or `Oct 24, 2026`.
   - *Mitigation:* Multi-pattern regex cascade with strict currency/date normalization via `dateutil.parser`.
2. **Corrupted or Password-Protected PDFs:** Files might be empty, encrypted, or malformed.
   - *Mitigation:* Pre-flight validation (`pdf.is_encrypted`, page count check) wrapped in isolated `try/except`. Corrupted files are flagged as `FAILED` in the audit log without halting the batch loop.
3. **Number Formatting Pitfalls:** Commas vs periods in currency (`$1,250.00` vs `€1.250,00`).
   - *Mitigation:* Clean currency sanitizer that strips currency glyphs (`$`, `€`, `£`, `₹`, `USD`, `EUR`) and standardizes decimal notation into Python `float`.
4. **Scanned Images vs Native Text:** If an invoice is an unsearchable image scan.
   - *Mitigation:* Script detects 0 extractable text characters on page 1, immediately logs `"SCANNED_PDF_NO_TEXT"`, marks fields as `"FLAGGED FOR REVIEW (SCANNED)"`, and continues execution.

---

### 4. Viability & Scope
- **Environment:** 100% self-contained on Linux/macOS/Windows with Python 3.10+.
- **Dependencies:** `pdfplumber`, `openpyxl`, `pandas`, `rich`, `python-dateutil`, `fpdf2` (for test generator).
- **Feasibility:** 100% viable within scope.

---

## Phase 2: System Design & Zero-Hardcode Architecture

### 1. Architectural Layers & Separation of Concerns

```
[ Input PDF Directory ]
           │
           ▼
┌────────────────────────────────────────────────────────┐
│  Ingestion & Extraction Layer (src/extractor.py)       │
│  - File discovery & validation                         │
│  - pdfplumber text stream & table extraction           │
│  - Spatial anchor & bounding-box analysis              │
└──────────────────────────┬─────────────────────────────┘
                           │ Raw Text & Layout Tokens
                           ▼
┌────────────────────────────────────────────────────────┐
│  Transformation & Heuristics (src/parser.py)           │
│  - Regex pattern cascade (dates, totals, invoice IDs)  │
│  - Vendor name normalization & heuristic anchors       │
│  - Currency sanitizer & number parser                  │
│  - Fallback assignment: "FLAGGED FOR REVIEW"          │
└──────────────────────────┬─────────────────────────────┘
                           │ Clean InvoiceRecord Data Transfer Objects
                           ▼
┌────────────────────────────────────────────────────────┐
│  Persistence & Reporting Layer (src/exporter.py)       │
│  - openpyxl workbook generator with professional styles│
│  - Sheet 1: 'Monthly Summary' (Structured Data)        │
│  - Sheet 2: 'Audit Log' (Success/Flag/Fail status)     │
│  - File-based diagnostic logging (batch_process.log)   │
└────────────────────────────────────────────────────────┘
```

### 2. Zero-Hardcode Configuration Standard
- All CLI parameters supplied via `argparse`:
  - `--input-dir` (`-i`): Path to folder containing invoice PDFs (default: `./invoices`).
  - `--output-file` (`-o`): Destination Excel file (default: `./output/monthly_summary.xlsx`).
  - `--config` (`-c`): Optional JSON file to override regex patterns, field keywords, or default currencies.
  - `--recursive` (`-r`): Flag to recursively search subdirectories.
- Configurable rules defined in `config/patterns.json`.

---

## Phase 3: Client Handoff & Value Delivery

### 1. Client Pitch / Acknowledgment Message
> *"Hi! I have reviewed your requirement for the batch invoice PDF extractor. I can deliver a clean, lightweight Python CLI tool that parses your 50+ vendor invoices, normalizes invoice numbers, dates, vendor names, and monetary totals, and compiles them into a professionally formatted Excel workbook (`monthly_summary.xlsx`). Any irregular or missing fields will be automatically marked as 'FLAGGED FOR REVIEW' with a dedicated audit log so the process never crashes. I will also provide 3 sample test invoice PDFs and a dummy generator script so you can test it immediately on your machine. Delivery within 24 hours."*

### 2. Deliverable Manifest
```
invoice-extractor/
├── venv/                       # Python virtual environment
├── config/
│   └── patterns.json           # Regex patterns & vendor keyword dictionary
├── sample_invoices/            # Sample test invoices
│   ├── invoice_vendor_a.pdf    # Clean digital invoice
│   ├── invoice_vendor_b.pdf    # Multi-line table layout
│   └── invoice_vendor_c.pdf    # Complex layout with VAT & discounts
├── output/
│   ├── monthly_summary.xlsx    # Generated Excel workbook (Summary + Audit)
│   └── batch_processing.log   # Detailed execution and error log
├── src/
│   ├── __init__.py
│   ├── models.py               # InvoiceRecord dataclass & validation
│   ├── extractor.py            # pdfplumber PDF reader & text harvester
│   ├── parser.py               # Pattern cascade, regex matcher, sanitizers
│   └── exporter.py             # openpyxl multi-sheet Excel generator
├── generate_dummies.py         # Standalone generator to create realistic mock PDFs
├── main.py                     # CLI orchestrator with Rich progress bar
├── requirements.txt            # Pinned dependencies
└── README.md                   # Step-by-step setup, CLI flags, troubleshooting
```

---

## Phase 4: Downstream Coding AI Prompt (The Anti-Gravity Directive)

```markdown
# AGENT DIRECTIVE: Batch Invoice PDF Extractor to Excel

You are an expert Python automation and document processing engineer. Build a production-ready, fault-tolerant CLI tool that extracts structured invoice data from batches of heterogeneous PDF invoices into an Excel workbook (`monthly_summary.xlsx`) with an audit log.

---

### 1. Environment & Setup
- Target Environment: Linux / macOS / Windows (Python 3.10+).
- Setup commands:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```
- Required Dependencies in `requirements.txt`:
  ```text
  pdfplumber==0.11.4
  openpyxl==3.1.5
  pandas==2.2.3
  python-dateutil==2.9.0.post0
  rich==13.9.4
  fpdf2==2.8.2
  ```

---

### 2. Functional Requirements

#### A. Data Fields to Extract:
1. `Invoice Number` (e.g., `INV-2024-001`, `#98432`, `2024/OCT/092`)
2. `Invoice Date` (Normalized to standard `YYYY-MM-DD`)
3. `Vendor Name` (Extracted from invoice header / company block)
4. `Subtotal` (Numeric float, stripped of currency symbols)
5. `Tax/VAT` (Numeric float, stripped of currency symbols; defaults to 0.0 if not applicable)
6. `Total Due` (Numeric float, stripped of currency symbols)

#### B. Fallback & Resilience Protocol (Non-Negotiable):
- **NEVER CRASH ON A BAD PDF**: If a field cannot be reliably found or parsed, populate that field with the exact string: `"FLAGGED FOR REVIEW"`.
- If a PDF is corrupted, unreadable, or contains no extractable text layer, catch the exception, mark all fields as `"FLAGGED FOR REVIEW (UNREADABLE)"`, log the error to `batch_processing.log`, and continue processing the rest of the batch.
- Overall process must exit with return code `0` on completed batch.

#### C. Output Excel Architecture (`monthly_summary.xlsx` via `openpyxl`):
- **Sheet 1: `Invoice Summary`**:
  - Columns: `Filename`, `Vendor Name`, `Invoice Number`, `Invoice Date`, `Subtotal`, `Tax/VAT`, `Total Due`, `Status`.
  - Formatting: Header in dark navy (`#1B365D`) with bold white text, zebra striping on alternating rows, currency columns formatted as financial numbers (`$#,##0.00`), dates centered.
  - Rows with any `"FLAGGED FOR REVIEW"` cell must have that specific cell highlighted in soft yellow (`#FFF3CD`) or light orange.
- **Sheet 2: `Audit & Errors`**:
  - Columns: `Timestamp`, `Filename`, `Pages`, `Processing Status` (`SUCCESS`, `FLAGGED`, `FAILED`), `Notes / Missing Fields`.
  - Summary cards or KPI row at top: Total Files Processed, Total Successful, Total Flagged, Total Failed.

#### D. Interactive CLI & Progress:
- Implement rich terminal feedback using `rich.progress.Progress`:
  - Display progress bar, percentage, current file name, and elapsed time.
  - On batch completion, render a `rich.table.Table` summarizing extracted counts and totals.
- Command-line arguments via `argparse`:
  - `--input-dir` / `-i`: Input directory containing PDFs (default: `./invoices`).
  - `--output-file` / `-o`: Output Excel path (default: `./output/monthly_summary.xlsx`).
  - `--recursive` / `-r`: Scan subdirectories recursively.
  - `--config` / `-c`: Optional path to custom JSON pattern config.

#### E. Test Data Generator (`generate_dummies.py`):
- Must include a standalone generator script using `fpdf2` that creates at least 3 distinct, realistic PDF invoices:
  - `sample_invoice_1.pdf`: Standard modern layout with clear key-value pairs.
  - `sample_invoice_2.pdf`: Multi-line table with Subtotal, 20% VAT, and Total Due formatted in Euro notation.
  - `sample_invoice_3.pdf`: Compact service receipt with discount and unusual date format.

---

### 3. Modular Code Structure to Implement

```
├── config/
│   └── patterns.json           # Regex patterns for Invoice No, Date, Totals, Vendor heuristics
├── src/
│   ├── __init__.py
│   ├── models.py               # InvoiceRecord dataclass with to_dict() and validation
│   ├── extractor.py            # pdfplumber reader extracting text lines & table cells
│   ├── parser.py               # Pattern matching, dateutil parser, currency cleaner
│   └── exporter.py             # openpyxl styled Excel builder with audit tab
├── generate_dummies.py         # Dummy generator creating 3 test PDFs
├── main.py                     # CLI entrypoint with argparse & rich UI
├── requirements.txt            # Pinned requirements
└── README.md                   # Full documentation & quickstart guide
```

---

### 4. Implementation Guidelines for Code
- Zero hardcoding: regex patterns and anchor keywords should be loaded from `config/patterns.json` or module constants with fallback defaults.
- Clean logging: Initialize logging to both console (`rich.logging.RichHandler`) and `output/batch_processing.log`.
- Deliver completely functional code with all files written and verified.
```
