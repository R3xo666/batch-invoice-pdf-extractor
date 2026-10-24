# DocuParse

DocuParse is a Python command-line tool for extracting invoice fields from PDFs and writing them to an Excel workbook. It uses `pdfplumber` to read text and tables, then applies configurable patterns to find the vendor, invoice number, date, subtotal, tax, and total due.

The parser marks missing or unreadable fields for review. Image-only PDFs are identified as scanned; this project does not perform OCR. Check flagged values against the original invoice before using the workbook for bookkeeping.

## Requirements and setup

~~~bash
git clone https://github.com/R3xo666/batch-invoice-pdf-extractor.git
cd batch-invoice-pdf-extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

## Run

Sample files are included in `sample_invoices/`.

~~~bash
python3 main.py --input-dir sample_invoices --output-file output/monthly_summary.xlsx
~~~

The default input directory is `./invoices`; the default workbook path is `./output/monthly_summary.xlsx`.

### Command-line options

| Option | Description |
| --- | --- |
| `-i`, `--input-dir` | Directory containing PDFs; scans only that directory unless `--recursive` is set |
| `-o`, `--output-file` | Destination `.xlsx` file |
| `-c`, `--config` | Optional JSON file with custom extraction patterns |
| `-r`, `--recursive` | Include PDFs in subdirectories |

### Extracted fields and status

The summary records the filename, vendor, invoice number, invoice date, subtotal, tax, total due, and processing status. Status is `SUCCESS`, `FLAGGED`, or `FAILED`. Incomplete records remain in the workbook with a review marker instead of being silently treated as complete.

Patterns are loaded from `config/patterns.json`. They cover labels for invoice numbers, dates, vendor names, subtotal, tax, and total due; you can pass a JSON file to override or extend them. Currency values are normalized from common US and European number formats.

### Input handling and output

The extractor accepts PDFs up to 50 MB and 100 pages. It flags a file as scanned when it yields fewer than 20 characters of text. It does not recognize handwriting or extract text from image-only pages.

The workbook contains an `Invoice Summary` sheet and an `Audit & Errors` sheet. The output directory also receives `batch_processing.log`. Formula-like text is escaped before writing string values to Excel.

## Tests

~~~bash
pytest -q
~~~