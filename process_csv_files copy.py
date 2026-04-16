#!/usr/bin/env python3
"""
Process Spanish vocabulary CSV files.
- Add 'id' column to 2-column CSVs
- If a file is missing a header row, create a standard header automatically
- For files with existing ids, add sequential ids to new rows
- Preserve existing row order
- Remove empty rows and empty columns
- Auto-detects comma or semicolon delimiters
- Rename original to _ORIG version
"""

import csv
import os
from pathlib import Path
from shutil import move

# Set this to your CSV folder
CSV_FOLDER = "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv/"
ORIGINAL_BACKUP_FOLDER = "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/CSV_ORIGINALS_BACKUP/"


def original_backup_path(filepath):
    source_path = Path(filepath)
    backup_dir = Path(ORIGINAL_BACKUP_FOLDER)
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir / f"{source_path.stem}_ORIG{source_path.suffix}"

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


def normalize_header_cell(value):
    return value.strip().lower()


def sanitize_rows(rows):
    """Remove blank rows and columns that contain no data anywhere."""
    trimmed_rows = []

    for row in rows:
        row_values = list(row)

        while row_values and not row_values[-1].strip():
            row_values.pop()

        if any(cell.strip() for cell in row_values):
            trimmed_rows.append(row_values)

    if not trimmed_rows:
        return []

    max_columns = max(len(row) for row in trimmed_rows)
    keep_indexes = []

    for column_index in range(max_columns):
        if any(column_index < len(row) and row[column_index].strip() for row in trimmed_rows):
            keep_indexes.append(column_index)

    return [
        [row[column_index] for column_index in keep_indexes if column_index < len(row)]
        for row in trimmed_rows
    ]


def detect_header_type(row):
    """Return the recognized header type for a row, if any."""
    normalized = [normalize_header_cell(cell) for cell in row]

    if len(normalized) >= 3 and normalized[0] == 'id' and normalized[1] == 'word' and normalized[2] == 'answer':
        return 'id_word_answer'

    if len(normalized) >= 2 and normalized[0] == 'word' and normalized[1] == 'answer':
        return 'word_answer'

    return None

def process_csv(filepath):
    """Process a single CSV file."""
    filename = os.path.basename(filepath)

    # Skip files that are already backups
    if filename.endswith('_ORIG.csv'):
        return True  # Silently skip backups

    # Read the CSV file and inspect the first row before deciding whether a
    # header already exists. Treat the first row as data unless it clearly
    # matches a known header.
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            delimiter = detect_delimiter(filepath)
            reader = csv.reader(f, delimiter=delimiter, quotechar='"')
            rows = sanitize_rows(list(reader))
    except Exception as e:
        print(f"  ✗ {filename} — error reading file: {e}")
        return False

    if not rows:
        print(f"  ✗ {filename} — empty file, skipping")
        return True

    first_row = rows[0]
    header_type = detect_header_type(first_row)
    num_cols = len(first_row)

    if header_type == 'id_word_answer':
        header = first_row
        data = rows[1:]
        return process_existing_id_file(filepath, filename, delimiter, header, data)

    if header_type == 'word_answer':
        header = first_row
        data = rows[1:]
        return process_new_file(filepath, filename, delimiter, header, data)

    # Recover malformed files from the earlier bug where the first data row was
    # written as: id;<word>;<answer> instead of adding a real header row.
    if num_cols == 3 and normalize_header_cell(first_row[0]) == 'id':
        return recover_malformed_id_header_file(filepath, filename, delimiter, rows)

    # No recognized header exists. Create the standard header automatically.
    if num_cols == 3:
        return process_existing_id_file(filepath, filename, delimiter, ['id', 'word', 'answer'], rows)

    if num_cols == 2:
        return process_new_file(filepath, filename, delimiter, ['word', 'answer'], rows)

    # Unexpected format
    print(f"  ✗ {filename} ({num_cols} columns) — unexpected format, skipping")
    return True


def recover_malformed_id_header_file(filepath, filename, delimiter, rows):
    """Repair files where the first data row was accidentally used as a header.

    In this broken format the first row looks like: id;<word>;<answer>.
    The safest repair is to rebuild the file as a standard 2-column payload,
    then write a proper id/word/answer header with fresh sequential ids.
    """
    try:
        recovered_rows = []
        for row in rows:
            if len(row) >= 3:
                recovered_rows.append([row[1], row[2]])
            elif len(row) == 2:
                recovered_rows.append(row)

        return process_new_file(filepath, filename, delimiter, ['word', 'answer'], recovered_rows)
    except Exception as e:
        print(f"  ✗ {filename} — error recovering malformed header: {e}")
        return False


def process_existing_id_file(filepath, filename, delimiter, header, data):
    """Process a file that already has an id column (3 columns).
    Keeps existing ids unchanged, assigns new sequential ids to rows without ids."""
    try:
        # Determine the next id without disturbing the original row order.
        existing_ids = []
        for row in data:
            if len(row) > 0 and row[0].strip():
                try:
                    existing_ids.append(int(row[0].strip()))
                except ValueError:
                    continue

        max_id = max(existing_ids, default=0)

        final_data = []
        for row in data:
            if len(row) > 0 and row[0].strip():
                try:
                    id_val = int(row[0].strip())
                    final_data.append([str(id_val)] + row[1:])
                    continue
                except ValueError:
                    pass

            if len(row) >= 3:
                row_payload = row[1:]
            else:
                row_payload = row

            max_id += 1
            final_data.append([str(max_id)] + row_payload)

        # Write back to file
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            writer.writerows(final_data)

        new_id_count = len(final_data) - len(existing_ids)
        print(f"  ✓ {filename} ({len(final_data)} rows, {new_id_count} new ids) — updated")
        return True

    except Exception as e:
        print(f"  ✗ {filename} — error: {e}")
        return False


def process_new_file(filepath, filename, delimiter, header, data):
    """Process a new 2-column file (add id column)."""
    try:
        data_rows = list(data)

        # Create _ORIG backup ONLY if it doesn't already exist.
        orig_filepath = original_backup_path(filepath)

        if not orig_filepath.exists():
            # Rename original to _ORIG only on first run
            move(filepath, orig_filepath)

        # Write modified file with original name (preserve delimiter and quoting)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_ALL)
            # Write header with new 'id' column
            writer.writerow(['id'] + header)
            # Write data rows with sequential IDs
            for i, row in enumerate(data_rows, start=1):
                writer.writerow([i] + row)

        print(f"  ✓ {filename} ({len(data_rows)} rows) — processed")
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