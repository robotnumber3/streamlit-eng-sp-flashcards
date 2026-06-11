# convert_all_pdfs_to_quarter_size.py

#!/usr/bin/env python3
"""
convert_all_pdfs_to_quarter_size.py

Batch‑process every PDF inside a folder (recursively), convert each one into
a 4‑up duplex‑ready layout using explicit inch‑based coordinates, and write
all resulting PDFs into a single output folder.

USAGE EXAMPLES:

    python convert_all_pdfs_to_quarter_size.py \
        --input "/Users/David/Desktop/Spanish Flashcards PDFs" \
        --output "/Users/David/Desktop/4up_output"

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

# Card size (quarter page)
CARD_W_IN = 4.25
CARD_H_IN = 5.5
CARD_W = int(CARD_W_IN * DPI)
CARD_H = int(CARD_H_IN * DPI)

PAGE_W_IN = 8.5
PAGE_H_IN = 11.0
PAGE_W = int(PAGE_W_IN * DPI)
PAGE_H = int(PAGE_H_IN * DPI)

RESAMPLING_MODULE = getattr(Image, "Resampling", Image)
LANCZOS_FILTER = RESAMPLING_MODULE.LANCZOS

def inches_to_pixels(x_in, y_in):
    return int(x_in * DPI), int(y_in * DPI)

# FRONT (odd): [1][3] / [5][7]
FRONT_POS = {
    "P1": inches_to_pixels(0.25,   0.0),
    "P3": inches_to_pixels(4.5,  0.0),
    "P5": inches_to_pixels(0.25,   5.5),
    "P7": inches_to_pixels(4.5,  5.5),
}

# BACK (even): [4][2] / [8][6]
BACK_POS = {
    "P4": inches_to_pixels(0.0,   0.125),
    "P2": inches_to_pixels(4.25,  0.125),
    "P8": inches_to_pixels(0.0,   5.6875),
    "P6": inches_to_pixels(4.25,  5.6875),
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
        img_resized = img.resize((CARD_W, CARD_H), LANCZOS_FILTER)
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

    for base in range(0, num_pages, 8):
        group = images[base:base + 8]
        while len(group) < 8:
            group.append(None)

        # FRONT: [1,3;5,7]
        front_map = {
            "P1": (group[0], FRONT_POS["P1"]),
            "P3": (group[2], FRONT_POS["P3"]),
            "P5": (group[4], FRONT_POS["P5"]),
            "P7": (group[6], FRONT_POS["P7"]),
        }
        if any(img for img, _ in front_map.values()):
            make_sheet(front_map, writer)

        # BACK: [4,2;8,6]
        back_map = {
            "P4": (group[3], BACK_POS["P4"]),
            "P2": (group[1], BACK_POS["P2"]),
            "P8": (group[7], BACK_POS["P8"]),
            "P6": (group[5], BACK_POS["P6"]),
        }
        if any(img for img, _ in back_map.values()):
            make_sheet(back_map, writer)

    base_name = os.path.splitext(os.path.basename(path))[0]
    out_path = os.path.join(output_folder, f"{base_name}_4up.pdf")

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
    parser = argparse.ArgumentParser(description="Recursive 4-up duplex imposition")
    parser.add_argument("--input", required=True, help="Folder containing PDFs")
    parser.add_argument("--output", required=True, help="Folder to write processed PDFs")
    args = parser.parse_args()

    os.chdir(PROGRAM_DIR)
    os.makedirs(args.output, exist_ok=True)
    walk_folder(args.input, args.output)
