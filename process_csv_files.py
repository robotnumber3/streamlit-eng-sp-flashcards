#!/usr/bin/env python3
"""
Process Spanish vocabulary CSV files.
- Add 'id' column to 2-column CSVs
- If a file is missing a header row, create a standard header automatically
- For files with existing ids, add sequential ids to new rows
- Sort by column 2 (Spanish translation) or column 1 (id)
- Auto-detects comma or semicolon delimiters
- Rename original to _ORIG version
"""

import csv
import os
from pathlib import Path
from shutil import move

# Set this to your CSV folder
CSV_FOLDER = "/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv/"


def preserve_original_order(filename):
    """Return True for sequential-content files whose row order matters.

    Dialogs and stories are not study decks where alphabetical sorting helps;
    their line order is part of the content itself and must be preserved.
    """
    lower_name = filename.lower()
    return 'dialog' in lower_name or 'story' in lower_name

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
    # header already exists. Dialog files were processed without headers, so the
    # first row must be treated as data unless it clearly matches a known header.
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sample = f.read(2048)
            f.seek(0)
            delimiter = detect_delimiter(filepath)
            reader = csv.reader(f, delimiter=delimiter, quotechar='"')
            rows = [row for row in reader if row and any(cell.strip() for cell in row)]
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
        # Separate rows with ids from rows without ids
        rows_with_id = []
        rows_without_id = []

        for row in data:
            if len(row) > 0 and row[0].strip():
                # Try to parse as integer id
                try:
                    id_val = int(row[0].strip())
                    # Store id separately and the rest of the row (without the id)
                    rows_with_id.append((id_val, row[1:]))
                except ValueError:
                    rows_without_id.append(row)
            else:
                # Row without id - could be 2 or 3 columns
                # If it's 3 columns with empty first, keep only columns 2-3
                if len(row) >= 3:
                    rows_without_id.append(row[1:])  # Skip the empty id column
                else:
                    rows_without_id.append(row)

        # Get max id from existing rows
        max_id = 0
        if rows_with_id:
            max_id = max(id_val for id_val, _ in rows_with_id)
            # Sort rows with ids by their id
            rows_with_id.sort(key=lambda x: x[0])

        # Preserve authored order for dialogs/stories. Regular vocab decks still
        # benefit from sorting by the answer column.
        if not preserve_original_order(filename):
            rows_without_id.sort(key=lambda x: x[1].lower() if len(x) > 1 else '')

        # Assign new ids to rows without ids
        final_data = []
        for id_val, row_data in rows_with_id:
            final_data.append([str(id_val)] + row_data)

        for row in rows_without_id:
            max_id += 1
            final_data.append([str(max_id)] + row)

        # Write back to file
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            writer.writerows(final_data)

        print(f"  ✓ {filename} ({len(final_data)} rows, {len(rows_without_id)} new ids) — updated")
        return True

    except Exception as e:
        print(f"  ✗ {filename} — error: {e}")
        return False


def process_new_file(filepath, filename, delimiter, header, data):
    """Process a new 2-column file (add id column)."""
    try:
        # Preserve authored order for dialogs/stories. Regular vocab decks still
        # benefit from sorting by the answer column.
        if preserve_original_order(filename):
            data_sorted = list(data)
        else:
            data_sorted = sorted(data, key=lambda x: x[1].lower() if len(x) > 1 else '')

        # Create _ORIG backup ONLY if it doesn't already exist
        name_without_ext = filepath.rsplit('.csv', 1)[0]
        orig_filepath = f"{name_without_ext}_ORIG.csv"

        if not os.path.exists(orig_filepath):
            # Rename original to _ORIG only on first run
            move(filepath, orig_filepath)

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