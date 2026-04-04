#!/usr/bin/env python3
"""
Process Spanish vocabulary CSV files.
- Add 'id' column to 2-column CSVs
- Sort by column 2 (Spanish translation)
- Auto-detects comma or semicolon delimiters
- Rename original to _ORIG version
- Leave 3+ column files untouched
"""

import csv
import os
from pathlib import Path
from shutil import move

# Set this to your CSV folder
CSV_FOLDER = "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv/"

def detect_delimiter(filepath):
    """Auto-detect delimiter (comma or semicolon) in CSV file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sample = f.read(2048)  # Read first 2KB

        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample, delimiters=',;').delimiter
        return delimiter
    except Exception:
        # Default to comma if detection fails
        return ','

def count_columns(filepath):
    """Count columns in a CSV file. Returns (count, delimiter)."""
    try:
        delimiter = detect_delimiter(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter, quotechar='"')
            header = next(reader, None)
            col_count = len(header) if header else 0
            return col_count, delimiter
    except Exception as e:
        print(f"  ✗ Error reading {filepath}: {e}")
        return None, None

def process_csv(filepath):
    """Process a single CSV file."""
    filename = os.path.basename(filepath)

    # Skip files that are already backups
    if filename.endswith('_ORIG.csv'):
        return True  # Silently skip backups

    # Count columns and detect delimiter
    num_cols, delimiter = count_columns(filepath)
    if num_cols is None:
        return False

    if num_cols >= 3:
        print(f"  ⊘ {filename} ({num_cols} columns) — skipping")
        return True

    if num_cols != 2:
        print(f"  ✗ {filename} ({num_cols} columns) — unexpected format, skipping")
        return True

    try:
        # Read the CSV
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter, quotechar='"')
            header = next(reader)
            data = list(reader)

        # Remove empty rows
        data = [row for row in data if row and any(row)]

        # Sort by column 2 (index 1, the answer column) alphabetically
        data_sorted = sorted(data, key=lambda x: x[1].lower() if len(x) > 1 else '')

        # Create _ORIG backup ONLY if it doesn't already exist
        name_without_ext = filepath.rsplit('.csv', 1)[0]
        orig_filepath = f"{name_without_ext}_ORIG.csv"

        if not os.path.exists(orig_filepath):
            # Rename original to _ORIG only on first run
            move(filepath, orig_filepath)
        else:
            # Already has backup, just read from current file
            pass

        # Write modified file with original name (preserve delimiter and quoting)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_ALL)
            # Write header with new 'id' column
            writer.writerow(['id'] + header)
            # Write data rows with sequential IDs
            for i, row in enumerate(data_sorted, start=1):
                writer.writerow([i] + row)

        print(f"  ✓ {filename} ({len(data_sorted)} rows) — processed")
        return True

    except Exception as e:
        print(f"  ✗ {filename} — error: {e}")
        return False

def main():
    """Process all CSV files in the folder."""
    csv_path = Path(CSV_FOLDER)

    if not csv_path.exists():
        print(f"Error: Folder not found: {CSV_FOLDER}")
        return

    # Find all CSV files
    csv_files = sorted(csv_path.glob('*.csv'))

    if not csv_files:
        print(f"No CSV files found in {CSV_FOLDER}")
        return

    print(f"\nProcessing {len(csv_files)} CSV files...\n")

    processed = 0
    skipped = 0

    for filepath in csv_files:
        if process_csv(str(filepath)):
            processed += 1
        else:
            skipped += 1

    print(f"\n✓ Complete: {processed} files processed, {skipped} errors/skipped")

if __name__ == '__main__':
    main()