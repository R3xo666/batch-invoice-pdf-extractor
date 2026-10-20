"""Transformation and heuristics engine for invoice fields normalization."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dateutil import parser as date_parser

from src.extractor import PDFExtractionResult
from src.models import (
    FLAGGED_FOR_REVIEW,
    FLAGGED_SCANNED,
    FLAGGED_UNREADABLE,
    InvoiceRecord,
    ProcessingStatus,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config/patterns.json")

FALLBACK_PATTERNS: Dict[str, Any] = {
    "invoice_number_patterns": [
        r"(?i)(?:invoice\s*(?:no\.?|number|num|#|id)|fakturanummer(?:\s*\/\s*invoice\s*#?)?|inv\s*#|bill\s*(?:no\.?|number|#))[:\s#]+([A-Z0-9][A-Z0-9\-\/_]{2,30})",
        r"(?i)(?:invoice|bill)\s*[:#]\s*([A-Z0-9][A-Z0-9\-\/_]{2,30})",
        r"(?i)\b(?:INV|BILL)-[A-Z0-9\-\/_]{3,20}\b",
    ],
    "date_patterns": [
        r"(?i)(?:invoice\s*date|bill(?:ing)?\s*date|issue\s*date|date\s*of\s*issue|fakturadatum(?:\s*\/\s*date)?|date)[:\s]*([A-Za-z0-9\s,\-\/\.]+)",
        r"\b(\d{4}[\-\/]\d{1,2}[\-\/]\d{1,2})\b",
        r"\b(\d{1,2}[\-\/]\d{1,2}[\-\/]\d{2,4})\b",
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
    ],
    "subtotal_patterns": [
        r"(?i)(?:sub[\s\-]?total|net\s*amount|amount\s*before\s*tax)[:\s]*(?:EUR|USD|GBP|[$€£₹])?\s*([\d\.,]+)",
        r"(?i)(?:sub[\s\-]?total)[^\d\n]*(?:EUR|USD|GBP|[$€£₹])?\s*([\d\.,]+)",
    ],
    "tax_patterns": [
        r"(?i)(?:tax|vat|gst|sales\s*tax)(?:\s*(?:rate|amount))?(?:\s*\(?[0-9\.]+%?\)?)?[:\s]+(?:EUR|USD|GBP|[$€£₹])?\s*([0-9\.,]+)",
        r"(?i)(?:vat\s*\d+%?)[^\d\n]*(?:EUR|USD|GBP|[$€£₹])?\s*([0-9\.,]+)",
    ],
    "total_due_patterns": [
        r"(?i)(?:total\s*amount\s*due|total\s*due|balance\s*due|grand\s*total|invoice\s*total|total\s*payable)\b[:\s]*(?:EUR|USD|GBP|[$€£₹])?\s*([0-9\.,]+)",
        r"(?i)\b(?<!sub)(?<!sub-)total[:\s]*(?:EUR|USD|GBP|[$€£₹])?\s*([0-9\.,]+)",
    ],
    "vendor_anchor_keywords": [
        "vendor:",
        "supplier:",
        "from:",
        "bill from:",
        "issued by:",
    ],
    "vendor_ignore_terms": [
        "invoice",
        "tax invoice",
        "commercial invoice",
        "bill to",
        "invoice to",
        "ship to",
        "billed to",
        "client",
        "customer",
        "due date",
        "payment terms",
        "total due",
        "subtotal",
        "fakturanummer",
        "fakturadatum",
        "official receipt",
    ],
    "currency_symbols": ["$", "€", "£", "₹", "¥", "USD", "EUR", "GBP", "INR", "CAD", "AUD"],
}


def load_pattern_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from JSON file or return default fallback patterns."""
    target_path = config_path or DEFAULT_CONFIG_PATH
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
                logger.info("Loaded custom patterns configuration from %s", target_path)
                return {**FALLBACK_PATTERNS, **data}
        except Exception as exc:
            logger.warning("Failed to load config %s: %s; using defaults", target_path, exc)
    return FALLBACK_PATTERNS


class InvoiceParser:
    """Extracts, normalizes, and validates invoice attributes from raw PDF text."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize parser with pattern configuration."""
        self.config = config or load_pattern_config()

    def clean_currency(self, raw_value: Any) -> float | str:
        """Sanitize raw currency string and convert to float.

        Handles US ($1,250.00) and European (€1.250,00 or 1250,00) number notations.
        """
        if isinstance(raw_value, (int, float)):
            return round(float(raw_value), 2)

        if not raw_value or not isinstance(raw_value, str):
            return FLAGGED_FOR_REVIEW

        text = raw_value.strip()
        # Strip currency symbols and letters
        for symbol in self.config.get("currency_symbols", []):
            text = text.replace(symbol, "")
        text = re.sub(r"[^\d\.,\-]", "", text).strip()

        if not text:
            return FLAGGED_FOR_REVIEW

        try:
            # European format: 1.250,50 -> 1250.50 or 1250,50 -> 1250.50
            if re.match(r"^\-?\d{1,3}(?:\.\d{3})+,\d{2}$", text):
                text = text.replace(".", "").replace(",", ".")
            elif re.match(r"^\-?\d+,\d{2}$", text):
                text = text.replace(",", ".")
            elif re.match(r"^\-?\d{1,3}(?:,\d{3})+\.\d{2}$", text):
                text = text.replace(",", "")
            elif "," in text and "." not in text:
                text = text.replace(",", ".")
            elif "," in text and "." in text:
                # Determine which separator is last
                if text.rfind(",") > text.rfind("."):
                    text = text.replace(".", "").replace(",", ".")
                else:
                    text = text.replace(",", "")

            return round(float(text), 2)
        except (ValueError, TypeError):
            return FLAGGED_FOR_REVIEW

    def parse_date(self, raw_value: Any) -> str:
        """Parse varied date formats and normalize to ISO YYYY-MM-DD."""
        if not raw_value or not isinstance(raw_value, str):
            return FLAGGED_FOR_REVIEW

        cleaned = raw_value.strip().rstrip(".,;:")
        try:
            parsed = date_parser.parse(cleaned, fuzzy=True, dayfirst=False)
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            # Try dayfirst=True fallback
            try:
                parsed = date_parser.parse(cleaned, fuzzy=True, dayfirst=True)
                return parsed.strftime("%Y-%m-%d")
            except Exception:
                return FLAGGED_FOR_REVIEW

    def extract_invoice_number(self, text: str) -> str:
        """Extract invoice identifier via regex pattern cascade."""
        for pattern in self.config.get("invoice_number_patterns", []):
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1).strip()
                # Exclude purely generic non-IDs
                if candidate.lower() not in {"date", "due", "total", "subtotal"}:
                    return candidate
        return FLAGGED_FOR_REVIEW

    def extract_date(self, text: str) -> str:
        """Extract invoice date via regex cascade and normalize to YYYY-MM-DD."""
        for pattern in self.config.get("date_patterns", []):
            match = re.search(pattern, text)
            if match:
                normalized = self.parse_date(match.group(1))
                if normalized != FLAGGED_FOR_REVIEW:
                    return normalized
        return FLAGGED_FOR_REVIEW

    def extract_vendor_name(self, text: str, lines: List[str]) -> str:
        """Extract vendor name using anchor keywords and header heuristics."""
        # 1. Search for explicit anchor keywords (e.g. "From: Acme Corp")
        for anchor in self.config.get("vendor_anchor_keywords", []):
            pattern = rf"(?i){re.escape(anchor)}\s*([^\n\r]+)"
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1).strip()
                if candidate and len(candidate) > 2:
                    return candidate

        # 2. Inspect top non-empty lines for company name
        ignore_terms = self.config.get("vendor_ignore_terms", [])
        for line in lines[:10]:
            clean_line = line.strip()
            if not clean_line or len(clean_line) < 3:
                continue

            lower_line = clean_line.lower()
            if any(term in lower_line for term in ignore_terms):
                continue

            # Skip lines that are purely numbers, dates, or emails
            if re.match(r"^[\d\s\-\/\:\.,]+$", clean_line):
                continue
            if "@" in clean_line and "." in clean_line:
                continue

            # Return first reasonable header line
            return clean_line

        return FLAGGED_FOR_REVIEW

    def extract_financials(
        self, text: str, tables: List[List[List[Optional[str]]]]
    ) -> Tuple[float | str, float | str, float | str]:
        """Extract subtotal, tax/VAT, and total due using text patterns and table inspection."""
        subtotal: float | str = FLAGGED_FOR_REVIEW
        tax: float | str = 0.0
        total_due: float | str = FLAGGED_FOR_REVIEW

        # 1. Check tables first (tables often store final totals cleanly)
        for table in tables:
            for row in table:
                if not row or len(row) < 2:
                    continue
                row_text = " ".join(str(cell) for cell in row if cell).lower()
                last_cell = str(row[-1]) if row[-1] else ""

                if "total due" in row_text or "grand total" in row_text or "total amount" in row_text:
                    parsed_val = self.clean_currency(last_cell)
                    if parsed_val != FLAGGED_FOR_REVIEW:
                        total_due = parsed_val
                elif "subtotal" in row_text or "sub-total" in row_text:
                    parsed_val = self.clean_currency(last_cell)
                    if parsed_val != FLAGGED_FOR_REVIEW:
                        subtotal = parsed_val
                elif "tax" in row_text or "vat" in row_text or "gst" in row_text:
                    parsed_val = self.clean_currency(last_cell)
                    if parsed_val != FLAGGED_FOR_REVIEW:
                        tax = parsed_val

        # 2. Text patterns for subtotal
        if subtotal == FLAGGED_FOR_REVIEW:
            for pattern in self.config.get("subtotal_patterns", []):
                match = re.search(pattern, text)
                if match:
                    val = self.clean_currency(match.group(1))
                    if val != FLAGGED_FOR_REVIEW:
                        subtotal = val
                        break

        # 3. Text patterns for tax/VAT
        for pattern in self.config.get("tax_patterns", []):
            match = re.search(pattern, text)
            if match:
                val = self.clean_currency(match.group(1))
                if val != FLAGGED_FOR_REVIEW:
                    tax = val
                    break

        # 4. Text patterns for total due
        if total_due == FLAGGED_FOR_REVIEW:
            for pattern in self.config.get("total_due_patterns", []):
                match = re.search(pattern, text)
                if match:
                    val = self.clean_currency(match.group(1))
                    if val != FLAGGED_FOR_REVIEW:
                        total_due = val
                        break

        # Consistency heuristic: if subtotal missing but total found and tax is 0.0, subtotal = total
        if subtotal == FLAGGED_FOR_REVIEW and total_due != FLAGGED_FOR_REVIEW and tax == 0.0:
            subtotal = total_due

        return subtotal, tax, total_due

    def parse(self, result: PDFExtractionResult) -> InvoiceRecord:
        """Parse an extraction result into a structured InvoiceRecord."""
        filename = result.file_path.name
        record = InvoiceRecord(filename=filename)

        # Handle extraction failures (corrupted, encrypted, zero bytes)
        if not result.is_valid:
            record.status = ProcessingStatus.FAILED
            record.vendor_name = FLAGGED_UNREADABLE
            record.invoice_number = FLAGGED_UNREADABLE
            record.invoice_date = FLAGGED_UNREADABLE
            record.subtotal = FLAGGED_UNREADABLE
            record.tax = FLAGGED_UNREADABLE
            record.total_due = FLAGGED_UNREADABLE
            record.notes.append(result.error or "Corrupted or encrypted PDF")
            return record

        # Handle scanned image-only PDFs
        if result.is_scanned:
            record.status = ProcessingStatus.FLAGGED
            record.vendor_name = FLAGGED_SCANNED
            record.invoice_number = FLAGGED_SCANNED
            record.invoice_date = FLAGGED_SCANNED
            record.subtotal = FLAGGED_SCANNED
            record.tax = FLAGGED_SCANNED
            record.total_due = FLAGGED_SCANNED
            record.notes.append("Scanned PDF with no digital text layer")
            return record

        text = result.full_text
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Extract individual fields
        record.invoice_number = self.extract_invoice_number(text)
        record.invoice_date = self.extract_date(text)
        record.vendor_name = self.extract_vendor_name(text, lines)
        record.subtotal, record.tax, record.total_due = self.extract_financials(
            text, result.tables
        )

        # Record diagnostic notes on flagged fields
        missing_fields: List[str] = []
        if record.vendor_name == FLAGGED_FOR_REVIEW:
            missing_fields.append("Vendor Name")
        if record.invoice_number == FLAGGED_FOR_REVIEW:
            missing_fields.append("Invoice Number")
        if record.invoice_date == FLAGGED_FOR_REVIEW:
            missing_fields.append("Invoice Date")
        if record.subtotal == FLAGGED_FOR_REVIEW:
            missing_fields.append("Subtotal")
        if record.total_due == FLAGGED_FOR_REVIEW:
            missing_fields.append("Total Due")

        if missing_fields:
            record.notes.append(f"Missing or unlocatable: {', '.join(missing_fields)}")

        record.evaluate_status()
        return record
