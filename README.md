# Batch Invoice PDF Extractor to Excel

A production-grade, fault-tolerant local Python CLI tool designed to batch-extract financial and vendor metadata from heterogeneous PDF invoices into a professionally styled Excel workbook (`monthly_summary.xlsx`) with comprehensive audit tracking.

---

## Features

- **Layout-Aware PDF Extraction**: Leverages `pdfplumber` to handle multi-column layouts, tables, and diverse text streams.
- **Robust Pattern Cascades**: Extracts `Invoice Number`, `Invoice Date`, `Vendor Name`, `Subtotal`, `Tax/VAT`, and `Total Due` using multi-pattern regex cascades and date/currency normalizers.
- **International Number & Date Formatting**: Seamlessly parses both US (`$1,250.00`, `YYYY-MM-DD`, `Oct 24, 2026`) and European (`1.250,00 EUR`, `DD/MM/YYYY`) conventions.
- **Fault-Tolerant Resilience**: Non-crashing exception boundaries. Corrupted or encrypted files are safely recorded as `FAILED`, scanned/unsearchable image PDFs are marked as `FLAGGED FOR REVIEW (SCANNED)`, and missing fields default to `FLAGGED FOR REVIEW`.
- **Professional Multi-Sheet Excel Output (`openpyxl`)**:
  - **`Invoice Summary` Sheet**: Dark navy headers (`#1B365D`), zebra striping, currency cell formatting (`$#,##0.00`), centered dates, and soft yellow highlights (`#FFF3CD`) on flagged review items.
  - **`Audit & Errors` Sheet**: Executive KPI metric cards (Total Files, Successful, Flagged, Failed) and detailed per-file audit diagnostics.
- **Interactive Terminal UI & Dual Logging**: Real-time progress bar powered by `rich`, terminal KPI summary table, and persistent disk logging in `output/batch_processing.log`.
- **Synthetic Test Data Generator**: Standalone script (`generate_dummies.py`) providing immediate test verification with realistic invoices.

---

## Project Structure

```
├── config/
│   └── patterns.json           # Configurable regexes & vendor keywords
├── sample_invoices/            # Sample test invoices
│   ├── invoice_vendor_a.pdf    # Standard US corporate invoice
│   ├── invoice_vendor_b.pdf    # European multi-line table with 20% VAT
│   ├── invoice_vendor_c.pdf    # Compact design receipt with discount
│   └── invoice_scanned_blank.pdf # Empty/scanned image test case
├── output/
│   ├── monthly_summary.xlsx    # Styled Excel workbook (Summary + Audit tabs)
│   └── batch_processing.log   # Detailed execution and error log
├── src/
│   ├── __init__.py
│   ├── models.py               # InvoiceRecord & AuditRecord dataclasses
│   ├── extractor.py            # pdfplumber layout harvester with safety guards
│   ├── parser.py               # Pattern cascade, regex matcher, sanitizers
│   └── exporter.py             # openpyxl workbook generator with custom styling
├── tests/
│   ├── __init__.py
│   └── test_extractor.py       # Comprehensive pytest unit test suite
├── generate_dummies.py         # Mock invoice PDF generator (fpdf2)
├── main.py                     # CLI entrypoint with argparse & rich UI
├── requirements.txt            # Pinned project dependencies
├── pytest.ini                  # Pytest configuration
└── README.md                   # Documentation and user guide
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.12 / 3.14)
- `uv` (recommended) or standard `python3-venv`

### Step 1: Create Virtual Environment
Using `uv`:
```bash
uv venv venv --python python3
source venv/bin/activate
uv pip install -r requirements.txt
```

Or using standard `venv` and `pip`:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### 1. Generate Sample Invoices (Optional)
To create 4 realistic mock PDF invoices for immediate verification:
```bash
python3 generate_dummies.py --output-dir sample_invoices
```

### 2. Run Batch Extraction
Run the CLI orchestrator targeting your invoice directory:
```bash
python3 main.py --input-dir sample_invoices --output-file output/monthly_summary.xlsx
```

### CLI Options:
| Flag | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--input-dir` | `-i` | `./invoices` | Path to directory containing PDF invoices. |
| `--output-file` | `-o` | `./output/monthly_summary.xlsx` | Output Excel workbook destination. |
| `--config` | `-c` | `config/patterns.json` | Optional path to custom JSON regex patterns. |
| `--recursive` | `-r` | `False` | Recursively scan subfolders for `.pdf` files. |

### Example CLI Output:
```text
╭──────────────────────────────────────────────────────────────╮
│ Batch Invoice PDF Extractor                                  │
│ Production Document Extraction & Excel Reconciliation Engine │
╰──────────────────────────────────────────────────────────────╯
Found 4 invoice PDF(s) to process.

  Extracting: invoice_vendor_c.pdf ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4/4 0:00:00

                        Invoice Batch Processing Summary                        
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                        ┃                                       Result ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total Files Processed         │                                            4 │
│ Successfully Extracted        │                                            3 │
│ Flagged for Review            │                                            1 │
│ Extraction Failures           │                                            0 │
│ Total Revenue Due (Extracted) │                                    $9,205.75 │
├───────────────────────────────┼──────────────────────────────────────────────┤
│ Generated Excel Report        │ output/monthly_summary.xlsx                  │
│ Audit Log                     │ output/batch_processing.log                  │
└───────────────────────────────┴──────────────────────────────────────────────┘
```

---

## Running Unit Tests

Run the test suite with `pytest`:
```bash
pytest tests/ -v
```

All 14 unit tests cover:
- US and European currency format normalization (`$1,250.00` and `1.250,00 EUR`).
- Date parsing and ISO formatting (`YYYY-MM-DD`).
- Cascading regex matchers for invoice numbers and vendors.
- Fault resilience on corrupted, encrypted, or zero-byte PDFs.
- Excel workbook formatting, header styles, and cell highlighting.

---

## Troubleshooting & FAQ

1. **Scanned / Image PDFs**:
   - If a PDF does not contain digital text (e.g. phone camera scans), the system identifies this via character density threshold (`< 20 chars`) and flags the record as `FLAGGED FOR REVIEW (SCANNED)` rather than crashing.
2. **Missing Fields**:
   - If an unusual invoice layout omits standard anchors, the unlocatable fields are flagged with `FLAGGED FOR REVIEW` and highlighted in soft yellow (`#FFF3CD`) in the Excel sheet for rapid manual reconciliation.
3. **Custom Vendor Patterns**:
   - You can add custom regex patterns or keyword anchors directly into `config/patterns.json` without modifying code.
