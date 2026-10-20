"""Data models and constants for invoice processing and audit reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProcessingStatus(str, Enum):
    """Lifecycle status of an invoice extraction record."""

    SUCCESS = "SUCCESS"
    FLAGGED = "FLAGGED"
    FAILED = "FAILED"


FLAGGED_FOR_REVIEW = "FLAGGED FOR REVIEW"
FLAGGED_UNREADABLE = "FLAGGED FOR REVIEW (UNREADABLE)"
FLAGGED_SCANNED = "FLAGGED FOR REVIEW (SCANNED)"

VALID_STATUSES = {
    ProcessingStatus.SUCCESS.value,
    ProcessingStatus.FLAGGED.value,
    ProcessingStatus.FAILED.value,
}


@dataclass
class InvoiceRecord:
    """Represents an extracted invoice with its core fields and review status."""

    filename: str
    vendor_name: str = FLAGGED_FOR_REVIEW
    invoice_number: str = FLAGGED_FOR_REVIEW
    invoice_date: str = FLAGGED_FOR_REVIEW
    subtotal: float | str = FLAGGED_FOR_REVIEW
    tax: float | str = 0.0
    total_due: float | str = FLAGGED_FOR_REVIEW
    status: ProcessingStatus = ProcessingStatus.SUCCESS
    notes: List[str] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def is_flagged(self) -> bool:
        """Return True if any key field is marked for review."""
        flagged_markers = (FLAGGED_FOR_REVIEW, FLAGGED_UNREADABLE, FLAGGED_SCANNED)
        fields_to_check = [
            self.vendor_name,
            self.invoice_number,
            self.invoice_date,
            self.subtotal,
            self.total_due,
        ]
        return any(
            isinstance(val, str) and any(marker in val for marker in flagged_markers)
            for val in fields_to_check
        )

    def evaluate_status(self) -> ProcessingStatus:
        """Recalculate status based on current field values unless already FAILED."""
        if self.status == ProcessingStatus.FAILED:
            return ProcessingStatus.FAILED
        if self.is_flagged():
            self.status = ProcessingStatus.FLAGGED
        else:
            self.status = ProcessingStatus.SUCCESS
        return self.status

    def to_summary_row(self) -> List[Any]:
        """Format as a row for the Invoice Summary Excel sheet."""
        return [
            self.filename,
            self.vendor_name,
            self.invoice_number,
            self.invoice_date,
            self.subtotal,
            self.tax,
            self.total_due,
            self.status.value,
        ]


@dataclass
class AuditRecord:
    """Audit entry documenting per-file extraction details and diagnostic notes."""

    filename: str
    pages: int
    status: ProcessingStatus
    notes: str
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def to_audit_row(self) -> List[Any]:
        """Format as a row for the Audit & Errors Excel sheet."""
        return [
            self.timestamp,
            self.filename,
            self.pages,
            self.status.value,
            self.notes,
        ]


@dataclass
class BatchSummary:
    """Aggregate KPI statistics for a completed batch run."""

    total_files: int = 0
    total_successful: int = 0
    total_flagged: int = 0
    total_failed: int = 0
    total_revenue_due: float = 0.0

    def add_record(self, record: InvoiceRecord) -> None:
        """Increment counters based on a processed InvoiceRecord."""
        self.total_files += 1
        if record.status == ProcessingStatus.SUCCESS:
            self.total_successful += 1
        elif record.status == ProcessingStatus.FLAGGED:
            self.total_flagged += 1
        elif record.status == ProcessingStatus.FAILED:
            self.total_failed += 1

        if isinstance(record.total_due, (int, float)):
            self.total_revenue_due += float(record.total_due)
