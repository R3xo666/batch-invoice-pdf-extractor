"""Main entry point for Batch Invoice PDF Extractor CLI tool."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from src.exporter import ExcelExporter
from src.extractor import PDFExtractor
from src.models import AuditRecord, BatchSummary, InvoiceRecord, ProcessingStatus
from src.parser import InvoiceParser, load_pattern_config

console = Console()


def configure_logging(output_dir: Path) -> Path:
    """Set up dual logging to both console and a batch processing log file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = output_dir / "batch_processing.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # File Handler
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Rich Console Handler
    console_handler = RichHandler(
        console=console,
        show_time=False,
        show_path=False,
        rich_tracebacks=True,
    )
    console_handler.setLevel(logging.WARNING)
    root_logger.addHandler(console_handler)

    return log_file_path


def render_summary_table(
    summary: BatchSummary, excel_path: Path, log_path: Path
) -> None:
    """Display an elegant completion summary table in the terminal."""
    table = Table(
        title="[bold navy]Invoice Batch Processing Summary[/bold navy]",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric", style="bold")
    table.add_column("Result", justify="right")

    table.add_row("Total Files Processed", str(summary.total_files))
    table.add_row(
        "Successfully Extracted",
        f"[green]{summary.total_successful}[/green]",
    )
    table.add_row(
        "Flagged for Review",
        f"[yellow]{summary.total_flagged}[/yellow]",
    )
    table.add_row(
        "Extraction Failures",
        f"[red]{summary.total_failed}[/red]"
        if summary.total_failed > 0
        else "0",
    )
    table.add_row(
        "Total Revenue Due (Extracted)",
        f"[bold green]${summary.total_revenue_due:,.2f}[/bold green]",
    )
    table.add_section()
    table.add_row("Generated Excel Report", f"[blue]{excel_path.resolve()}[/blue]")
    table.add_row("Audit Log", f"[blue]{log_path.resolve()}[/blue]")

    console.print()
    console.print(table)
    console.print()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch Invoice PDF Extractor: Extract structured invoice data to Excel with audit tracking."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=Path("./invoices"),
        help="Directory containing PDF invoice files (default: ./invoices).",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=Path,
        default=Path("./output/monthly_summary.xlsx"),
        help="Destination Excel spreadsheet path (default: ./output/monthly_summary.xlsx).",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="Optional custom JSON regex patterns configuration file.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively scan subdirectories for PDF invoices.",
    )
    return parser.parse_args()


def main() -> int:
    """Orchestrate the end-to-end extraction and export pipeline."""
    args = parse_arguments()
    output_dir = args.output_file.parent
    log_path = configure_logging(output_dir)

    console.print(
        Panel.fit(
            "[bold white]Batch Invoice PDF Extractor[/bold white]\n"
            "[cyan]Production Document Extraction & Excel Reconciliation Engine[/cyan]",
            border_style="bright_blue",
        )
    )

    # Load custom or default configuration
    patterns_config = load_pattern_config(args.config)
    extractor = PDFExtractor()
    parser = InvoiceParser(config=patterns_config)
    exporter = ExcelExporter()

    pdf_files = extractor.discover_pdfs(args.input_dir, recursive=args.recursive)

    if not pdf_files:
        console.print(
            f"[yellow]No PDF files located in directory: {args.input_dir.resolve()}[/yellow]"
        )
        logging.warning("No PDF files discovered in %s", args.input_dir)
        return 0

    console.print(f"Found [bold green]{len(pdf_files)}[/bold green] invoice PDF(s) to process.\n")

    invoice_records: List[InvoiceRecord] = []
    audit_records: List[AuditRecord] = []
    summary = BatchSummary()

    # Progress bar loop
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Processing invoices...", total=len(pdf_files))

        for pdf_path in pdf_files:
            progress.update(task_id, description=f"Extracting: [bold]{pdf_path.name}[/bold]")
            try:
                extraction = extractor.extract(pdf_path)
                record = parser.parse(extraction)
                invoice_records.append(record)
                summary.add_record(record)

                notes_str = "; ".join(record.notes) if record.notes else "Clean extraction"
                audit_records.append(
                    AuditRecord(
                        filename=pdf_path.name,
                        pages=extraction.total_pages,
                        status=record.status,
                        notes=notes_str,
                    )
                )
                logging.info(
                    "Processed %s -> Status: %s | Notes: %s",
                    pdf_path.name,
                    record.status.value,
                    notes_str,
                )
            except Exception as unhandled_err:
                # Top-level non-crashing safety boundary
                logging.exception("Unexpected error processing %s: %s", pdf_path.name, unhandled_err)
                failed_record = InvoiceRecord(
                    filename=pdf_path.name,
                    status=ProcessingStatus.FAILED,
                    notes=[f"Unhandled error: {unhandled_err}"],
                )
                invoice_records.append(failed_record)
                summary.add_record(failed_record)
                audit_records.append(
                    AuditRecord(
                        filename=pdf_path.name,
                        pages=0,
                        status=ProcessingStatus.FAILED,
                        notes=f"Unhandled pipeline error: {unhandled_err}",
                    )
                )

            progress.advance(task_id)

    # Export to Excel
    exporter.export(
        output_path=args.output_file,
        records=invoice_records,
        audit_records=audit_records,
        summary=summary,
    )

    render_summary_table(summary, args.output_file, log_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
