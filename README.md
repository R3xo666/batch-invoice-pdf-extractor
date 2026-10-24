# DocuParse

DocuParse is a Python command-line tool that reads invoice PDFs and writes extracted fields to an Excel workbook. It uses `pdfplumber` for text and table extraction, then applies configurable patterns to find values such as vendor, invoice number, date, subtotal, tax, and total.

The parser marks missing or unreadable fields for review. Image-only PDFs are reported as scanned; the project does not run OCR. The workbook contains an invoice summary and an audit sheet, and the run also writes a processing log.

## Setup

~~~bash
git clone https://github.com/R3xo666/batch-invoice-pdf-extractor.git
cd batch-invoice-pdf-extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
~~~

## Run

Sample PDFs are in `sample_invoices/`.

~~~bash
python3 main.py --input-dir sample_invoices --output-file output/monthly_summary.xlsx
~~~

Useful options:

- `--input-dir` sets the folder to scan. The default is `./invoices`.
- `--output-file` sets the workbook path. The default is `./output/monthly_summary.xlsx`.
- `--recursive` includes PDFs in subfolders.
- `--config` loads a JSON file with custom extraction patterns. The default patterns are in `config/patterns.json`.

The output folder also receives `batch_processing.log`. String values that could be interpreted as spreadsheet formulas are escaped before they are written to the workbook.

## Tests

~~~bash
pytest -q
~~~