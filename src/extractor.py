"""PDF text and table extraction engine using pdfplumber with fault-tolerant error boundaries."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class PDFPageData:
    """Extracted content from an individual PDF page."""

    page_number: int
    text: str
    tables: List[List[List[Optional[str]]]] = field(default_factory=list)


@dataclass
class PDFExtractionResult:
    """Complete harvest of text, tables, and status for a processed PDF file."""

    file_path: Path
    total_pages: int = 0
    full_text: str = ""
    pages: List[PDFPageData] = field(default_factory=list)
    tables: List[List[List[Optional[str]]]] = field(default_factory=list)
    is_scanned: bool = False
    is_encrypted: bool = False
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Return True if extraction completed without fatal errors."""
        return self.error is None and not self.is_encrypted


class PDFExtractor:
    """Layout-aware PDF reader designed for heterogeneous invoice layouts."""

    def __init__(self, min_text_chars: int = 20) -> None:
        """Initialize extractor.

        Args:
            min_text_chars: Minimum character threshold below which a PDF is treated as scanned/empty.
        """
        self.min_text_chars = min_text_chars

    @staticmethod
    def discover_pdfs(input_dir: Path, recursive: bool = False) -> List[Path]:
        """Find all PDF files in the target directory.

        Args:
            input_dir: Root directory path to scan.
            recursive: If True, recursively traverse subdirectories.

        Returns:
            Sorted list of resolved PDF file paths.
        """
        if not input_dir.is_dir():
            logger.warning("Target directory does not exist: %s", input_dir)
            return []

        pattern = "**/*.pdf" if recursive else "*.pdf"
        found = [p.resolve() for p in input_dir.glob(pattern) if p.is_file()]
        # Case-insensitive check for .PDF uppercase extensions
        if not found:
            upper_pattern = "**/*.PDF" if recursive else "*.PDF"
            found = [p.resolve() for p in input_dir.glob(upper_pattern) if p.is_file()]
        return sorted(found)

    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB threshold
    MAX_PAGES_LIMIT: int = 100

    def extract(self, file_path: Path) -> PDFExtractionResult:
        """Extract text and tables from a single PDF document.

        Args:
            file_path: Absolute or relative path to PDF file.

        Returns:
            PDFExtractionResult with text streams, tables, and fault status.
        """
        result = PDFExtractionResult(file_path=file_path)

        if not file_path.exists():
            result.error = f"File not found: {file_path.name}"
            return result

        file_size = file_path.stat().st_size
        if file_size == 0:
            result.error = "File is zero bytes (empty file)"
            return result

        if file_size > self.MAX_FILE_SIZE_BYTES:
            result.error = f"File exceeds maximum allowed size ({file_size} bytes > {self.MAX_FILE_SIZE_BYTES})"
            return result

        try:
            with pdfplumber.open(file_path) as pdf:
                result.total_pages = len(pdf.pages)

                # Check encryption
                if getattr(pdf, "is_encrypted", False):
                    result.is_encrypted = True
                    result.error = "PDF is password-protected or encrypted"
                    return result

                if result.total_pages == 0:
                    result.error = "PDF contains zero pages"
                    return result

                if result.total_pages > self.MAX_PAGES_LIMIT:
                    result.error = f"PDF exceeds maximum page limit ({result.total_pages} > {self.MAX_PAGES_LIMIT})"
                    return result

                text_fragments: List[str] = []

                for idx, page in enumerate(pdf.pages, start=1):
                    # Extract layout-aware page text
                    page_text = page.extract_text(layout=False) or ""
                    # Also fallback to layout=True if normal extract is sparse
                    if len(page_text.strip()) < self.min_text_chars:
                        alt_text = page.extract_text(layout=True) or ""
                        if len(alt_text.strip()) > len(page_text.strip()):
                            page_text = alt_text

                    text_fragments.append(page_text)

                    # Extract tabular structures
                    page_tables = page.extract_tables() or []
                    result.tables.extend(page_tables)

                    result.pages.append(
                        PDFPageData(
                            page_number=idx,
                            text=page_text,
                            tables=page_tables,
                        )
                    )

                result.full_text = "\n".join(text_fragments)

                # Detect scanned/image-only PDFs
                clean_char_count = len(result.full_text.strip())
                if clean_char_count < self.min_text_chars:
                    result.is_scanned = True
                    logger.warning(
                        "File %s has only %d text characters; marking as scanned",
                        file_path.name,
                        clean_char_count,
                    )

        except Exception as exc:
            error_msg = f"Failed to parse PDF ({type(exc).__name__}): {exc}"
            logger.error("Error extracting %s: %s", file_path.name, error_msg)
            result.error = error_msg

        return result
