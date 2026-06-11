# convert_single_pdf_to_quarter_size.py

from pdf2image import convert_from_path
from PIL import Image
from pypdf import PdfReader, PdfWriter
import os

INPUT = "/Users/David/Desktop/Spanish Flashcards PDFs (from CSVs)/Vocabulary/vocab_food.pdf"
OUTPUT = "/Users/David/Desktop/vocab_food_4up_duplex_explicit_coords_v2.pdf"

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

def inches_to_pixels(x_in, y_in):
    return int(x_in * DPI), int(y_in * DPI)

# FRONT (odd): [1][3] / [5][7]
front_positions = {
    "P1": inches_to_pixels(0.25, 0.0),   # TL
    "P3": inches_to_pixels(4.5, 0.0),  # TR
    "P5": inches_to_pixels(0.25, 5.5),   # BL
    "P7": inches_to_pixels(4.5, 5.5),  # BR
}

# BACK (even): [4][2] / [8][6]
back_positions = {
    "P4": inches_to_pixels(0.25, 0.125),      # TL
    "P2": inches_to_pixels(4.5, 0.125),     # TR
    "P8": inches_to_pixels(0.25, 5.6875),     # BL
    "P6": inches_to_pixels(4.5, 5.6875),    # BR
}

images = convert_from_path(INPUT, dpi=DPI)
num_pages = len(images)

writer = PdfWriter()

def make_sheet(mapping):
    sheet = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    for img, (x, y) in mapping.values():
        if img is None:
            continue
        img_resized = img.resize((CARD_W, CARD_H), Image.LANCZOS)
        sheet.paste(img_resized, (x, y))

    temp_path = "temp_page.pdf"
    sheet.save(temp_path, "PDF", resolution=DPI)
    page_reader = PdfReader(temp_path)
    writer.add_page(page_reader.pages[0])
    os.remove(temp_path)

for base in range(0, num_pages, 8):
    group = images[base:base + 8]
    while len(group) < 8:
        group.append(None)

    # FRONT: [1,3;5,7] → indices [0,2;4,6]
    front_map = {
        "P1": (group[0], front_positions["P1"]),
        "P3": (group[2], front_positions["P3"]),
        "P5": (group[4], front_positions["P5"]),
        "P7": (group[6], front_positions["P7"]),
    }
    if any(img for img, _ in front_map.values()):
        make_sheet(front_map)

    # BACK: [4,2;8,6] → indices [3,1;7,5]
    back_map = {
        "P4": (group[3], back_positions["P4"]),
        "P2": (group[1], back_positions["P2"]),
        "P8": (group[7], back_positions["P8"]),
        "P6": (group[5], back_positions["P6"]),
    }
    if any(img for img, _ in back_map.values()):
        make_sheet(back_map)

with open(OUTPUT, "wb") as f:
    writer.write(f)

print("Done:", OUTPUT)
