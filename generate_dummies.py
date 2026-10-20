"""Standalone synthetic test invoice generator creating realistic mock PDFs using modern fpdf2 API."""

from __future__ import annotations

import argparse
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos


def create_invoice_vendor_a(output_path: Path) -> None:
    """Generate sample_invoice_1: Modern US corporate layout with key-value pairs."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header / Vendor
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(27, 54, 93)  # Navy
    pdf.cell(0, 10, "Apex Cloud Solutions Inc.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "100 Innovation Way, Suite 400, San Francisco, CA 94105", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "support@apexcloud.io | +1 (415) 555-0199", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Divider line
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Invoice Details Block
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(100, 8, "INVOICE", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(90, 8, "Invoice Date: 2026-10-15", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.set_font("Helvetica", size=10)
    pdf.cell(100, 6, "Invoice Number: INV-2026-8941", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(90, 6, "Payment Terms: Net 30", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    pdf.ln(8)

    # Bill To
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Bill To:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, "Global Enterprises LLC", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "500 Market Street, New York, NY 10001", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Items Table Header
    pdf.set_fill_color(240, 243, 246)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(90, 8, " Description", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L", fill=True)
    pdf.cell(30, 8, "Hours/Qty", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="C", fill=True)
    pdf.cell(35, 8, "Rate", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R", fill=True)
    pdf.cell(35, 8, "Amount", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R", fill=True)

    # Items Rows
    items = [
        ("Cloud Infrastructure Migration Consulting", "20 hrs", "$150.00", "$3,000.00"),
        ("Kubernetes Cluster Setup & Optimization", "12 hrs", "$175.00", "$2,100.00"),
        ("Automated CI/CD Pipeline Deployment", "1", "$850.00", "$850.00"),
    ]

    pdf.set_font("Helvetica", size=9)
    for desc, qty, rate, amt in items:
        pdf.cell(90, 7, f" {desc}", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
        pdf.cell(30, 7, qty, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="C")
        pdf.cell(35, 7, rate, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
        pdf.cell(35, 7, amt, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.ln(5)

    # Totals Section
    pdf.set_font("Helvetica", size=10)
    pdf.cell(130, 6, "", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(30, 6, "Subtotal:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
    pdf.cell(30, 6, "$5,950.00", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.cell(130, 6, "", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(30, 6, "Tax (8.5%):", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
    pdf.cell(30, 6, "$505.75", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(27, 54, 93)
    pdf.cell(130, 8, "", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(30, 8, "Total Due:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
    pdf.cell(30, 8, "$6,455.75", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.output(str(output_path))


def create_invoice_vendor_b(output_path: Path) -> None:
    """Generate sample_invoice_2: European format with 20% VAT and Euro number notation."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # European Vendor Header
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(40, 80, 120)
    pdf.cell(0, 10, "Nordic Data Systems AB", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "Kungsgatan 42, 111 35 Stockholm, Sweden", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "Org.nr: 556012-3456 | VAT: SE556012345601", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Metadata Grid
    pdf.set_draw_color(180, 180, 180)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(50, 6, "Fakturanummer / Invoice #:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(50, 6, "SE-2026-9042", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(40, 6, "Fakturadatum / Date:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(40, 6, "18/10/2026", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, 6, "Vendor:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(50, 6, "Nordic Data Systems AB", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Multi-line item table
    pdf.set_fill_color(230, 235, 240)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 8, "Artiklar / Description", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L", fill=True)
    pdf.cell(30, 8, "Antal / Qty", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="C", fill=True)
    pdf.cell(35, 8, "Pris / Price", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R", fill=True)
    pdf.cell(45, 8, "Summa / Total", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R", fill=True)

    items = [
        ("Server Hosting - Enterprise Node A", "1", "450,00 EUR", "450,00 EUR"),
        ("Database Backup Storage 10TB", "1", "350,00 EUR", "350,00 EUR"),
        ("24/7 SLA Technical Support", "1", "241,67 EUR", "241,67 EUR"),
    ]

    pdf.set_font("Helvetica", size=9)
    for desc, qty, price, total in items:
        pdf.cell(80, 7, desc, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
        pdf.cell(30, 7, qty, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="C")
        pdf.cell(35, 7, price, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
        pdf.cell(45, 7, total, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.ln(6)

    # European totals table
    pdf.set_font("Helvetica", size=10)
    pdf.cell(110, 6, "", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(40, 6, "Subtotal:", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.cell(40, 6, "1.041,67 EUR", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.cell(110, 6, "", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(40, 6, "VAT 20%:", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.cell(40, 6, "208,33 EUR", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(110, 7, "", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.cell(40, 7, "Total Due:", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.cell(40, 7, "1.250,00 EUR", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.output(str(output_path))


def create_invoice_vendor_c(output_path: Path) -> None:
    """Generate sample_invoice_3: Compact service receipt with discount and unusual date format."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 8, "Vanguard Design Lab", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 4, "Studio 12, Arts District, Austin, TX 78701", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.cell(0, 4, "billing@vanguarddesign.co", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(6)

    pdf.set_draw_color(220, 220, 220)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 6, "OFFICIAL RECEIPT / INVOICE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 5, "Bill No: VDL-2026/OCT/092", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "Issue Date: 24-Oct-2026", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Table
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(120, 6, "Service", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L", fill=True)
    pdf.cell(60, 6, "Price", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R", fill=True)

    pdf.set_font("Helvetica", size=8)
    pdf.cell(120, 6, "Brand Identity & Logo Redesign", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.cell(60, 6, "$1,200.00", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")
    pdf.cell(120, 6, "Typography Guidelines Book", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.cell(60, 6, "$450.00", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.ln(4)
    pdf.cell(120, 5, "Subtotal:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
    pdf.cell(60, 5, "$1,650.00", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.cell(120, 5, "Promotional Discount:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
    pdf.cell(60, 5, "-$150.00", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.cell(120, 5, "Sales Tax (0%):", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
    pdf.cell(60, 5, "$0.00", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(120, 6, "Total Amount Due:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align="R")
    pdf.cell(60, 6, "$1,500.00", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    pdf.output(str(output_path))


def create_scanned_mock(output_path: Path) -> None:
    """Generate sample_scanned: Scanned or image-like PDF with no digital text layer."""
    pdf = FPDF()
    pdf.add_page()
    # Add a blank page or minimal graphical line to simulate unextractable image scan
    pdf.set_draw_color(150, 150, 150)
    pdf.rect(10, 10, 190, 277)
    pdf.output(str(output_path))


def generate_all_samples(output_dir: Path) -> None:
    """Generate all test invoices in the target folder."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating realistic mock invoice PDFs in: {output_dir.resolve()}")

    create_invoice_vendor_a(output_dir / "invoice_vendor_a.pdf")
    print("  [+] Created invoice_vendor_a.pdf (Modern US Key-Value layout)")

    create_invoice_vendor_b(output_dir / "invoice_vendor_b.pdf")
    print("  [+] Created invoice_vendor_b.pdf (European layout with 20% VAT)")

    create_invoice_vendor_c(output_dir / "invoice_vendor_c.pdf")
    print("  [+] Created invoice_vendor_c.pdf (Receipt layout with 24-Oct-2026 date)")

    create_scanned_mock(output_dir / "invoice_scanned_blank.pdf")
    print("  [+] Created invoice_scanned_blank.pdf (Simulated image/scanned PDF)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic sample invoices for testing.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("sample_invoices"),
        help="Directory to save generated sample PDF files.",
    )
    args = parser.parse_args()
    generate_all_samples(args.output_dir)
