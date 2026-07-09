# convert_all_pdfs_to_half_size.py

#!/usr/bin/env python3
"""
convert_all_pdfs_to_half_size.py

Batch‑process every PDF inside a folder (recursively), convert each one into
a 2‑up duplex‑ready landscape layout (11×8.5") with 2 portrait pages per side,
and write all resulting PDFs into a single output folder.

Source pages are 8.5×11" portrait.  Each output sheet is 11×8.5" landscape:
  • Front side: source page 1 on the RIGHT half, source page 2 on the LEFT half
  • Back side:  source page 3 on the LEFT half,  source page 4 on the RIGHT half
Print duplex (flip on long edge) and pages read in correct sequential order.

USAGE EXAMPLES:

    python convert_all_pdfs_to_half_size.py \
        --input "/Users/David/Desktop/Spanish Flashcards PDFs" \
        --output "/Users/David/Desktop/2up_output"

ARGUMENTS:

    --input    Path to the input folder containing PDFs (searched recursively)
    --output   Path to the folder where all processed PDFs will be written
"""

import os
import argparse
from PIL import Image
from pypdf import PdfReader, PdfWriter

try:
    from pdf2image import convert_from_path as pdf2image_convert_from_path  # pyright: ignore[reportMissingImports]
except ImportError:
    pdf2image_convert_from_path = None

PROGRAM_DIR = "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards"

DPI = 300

# Output sheet dimensions (landscape)
PAGE_W_IN = 11.0
PAGE_H_IN = 8.5
PAGE_W = int(PAGE_W_IN * DPI)
PAGE_H = int(PAGE_H_IN * DPI)

# Margins
MARGIN_TOP_IN        = 0.0
MARGIN_BOTTOM_IN     = 0.0
MARGIN_ODD_LEFT_IN   = 0.75   # pages 1 and 3
MARGIN_ODD_RIGHT_IN  = 0.0    # pages 1 and 3
MARGIN_EVEN_LEFT_IN  = 0.0    # pages 2 and 4
MARGIN_EVEN_RIGHT_IN = 0.75   # pages 2 and 4

HALF_W_IN = PAGE_W_IN / 2    # 5.5" — width of each half-slot

# Content size after margins are applied (same for all pages)
CONTENT_W_IN = HALF_W_IN - MARGIN_ODD_LEFT_IN  - MARGIN_ODD_RIGHT_IN   # 4.0"
CONTENT_H_IN = PAGE_H_IN  - MARGIN_TOP_IN      - MARGIN_BOTTOM_IN      # 7.5"
CONTENT_W = int(CONTENT_W_IN * DPI)
CONTENT_H = int(CONTENT_H_IN * DPI)

RESAMPLING_MODULE = getattr(Image, "Resampling", Image)
LANCZOS_FILTER = RESAMPLING_MODULE.LANCZOS

def inches_to_pixels(x_in, y_in):
    return int(x_in * DPI), int(y_in * DPI)

# Position of each source page on the output sheet.
# Output PDF page 1: P3 on left, P1 on right  (front of physical sheet)
# Output PDF page 2: P2 on left, P4 on right  (back of physical sheet)
POS = {
    "P1": inches_to_pixels(HALF_W_IN + MARGIN_ODD_LEFT_IN,  MARGIN_TOP_IN),  # right half, odd margins
    "P2": inches_to_pixels(MARGIN_EVEN_LEFT_IN,              MARGIN_TOP_IN),  # left half,  even margins
    "P3": inches_to_pixels(MARGIN_ODD_LEFT_IN,               MARGIN_TOP_IN),  # left half,  odd margins
    "P4": inches_to_pixels(HALF_W_IN + MARGIN_EVEN_LEFT_IN,  MARGIN_TOP_IN),  # right half, even margins
}

# -----------------------------
# Progress bar helper
# -----------------------------
def progress_bar(current, total, width=30):
    ratio = current / total
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    percent = int(ratio * 100)
    return f"[{bar}] {percent:3d}%   ({current} of {total})"

# -----------------------------
# PDF processing
# -----------------------------
def make_sheet(mapping, writer):
    sheet = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    for img, (x, y) in mapping.values():
        if img is None:
            continue
        img_resized = img.resize((CONTENT_W, CONTENT_H), LANCZOS_FILTER)
        sheet.paste(img_resized, (x, y))

    temp_path = "temp_page.pdf"
    sheet.save(temp_path, "PDF", resolution=DPI)
    page_reader = PdfReader(temp_path)
    writer.add_page(page_reader.pages[0])
    os.remove(temp_path)

def process_pdf(path, output_folder):
    if pdf2image_convert_from_path is None:
        raise RuntimeError("pdf2image is required to convert PDFs. Install it in the active Python environment.")

    images = pdf2image_convert_from_path(path, dpi=DPI)
    num_pages = len(images)

    writer = PdfWriter()

    for base in range(0, num_pages, 4):
        group = images[base:base + 4]
        while len(group) < 4:
            group.append(None)

        # Output PDF page 1 (front of physical sheet): p3 on left, p1 on right
        page1_map = {
            "P3": (group[2], POS["P3"]),
            "P1": (group[0], POS["P1"]),
        }
        if any(img for img, _ in page1_map.values()):
            make_sheet(page1_map, writer)

        # Output PDF page 2 (back of physical sheet): p2 on left, p4 on right
        page2_map = {
            "P2": (group[1], POS["P2"]),
            "P4": (group[3], POS["P4"]),
        }
        if any(img for img, _ in page2_map.values()):
            make_sheet(page2_map, writer)

    base_name = os.path.splitext(os.path.basename(path))[0]
    out_path = os.path.join(output_folder, f"{base_name}_2up.pdf")

    with open(out_path, "wb") as f:
        writer.write(f)

def walk_folder(input_folder, output_folder):
    # Collect all PDFs first (so we know total count)
    pdfs = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, file))

    total = len(pdfs)
    if total == 0:
        print("No PDFs found.")
        return

    print(f"Found {total} PDFs. Starting batch processing...\n")

    for i, pdf_path in enumerate(pdfs, start=1):
        print(progress_bar(i, total))
        print(f"Processing: {os.path.basename(pdf_path)}")
        process_pdf(pdf_path, output_folder)
        print()  # blank line for readability

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursive 2-up duplex imposition (landscape 11×8.5\")")
    parser.add_argument("--input", required=True, help="Folder containing PDFs")
    parser.add_argument("--output", required=True, help="Folder to write processed PDFs")
    args = parser.parse_args()

    os.chdir(PROGRAM_DIR)
    os.makedirs(args.output, exist_ok=True)
    walk_folder(args.input, args.output)
