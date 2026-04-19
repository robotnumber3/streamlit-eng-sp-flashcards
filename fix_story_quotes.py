from pathlib import Path
import csv
import re


CSV_DIR = Path(__file__).resolve().parent / "csv"
FILE_PATTERN = re.compile(r"PoS_verbs_reg_PRIMARY_0[1-9][abc]_story\.csv$")


def clean_answer_field(value: str) -> str:
    cleaned = value.strip()
    while len(cleaned) >= 2 and cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def normalize_file(path: Path) -> bool:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=';', quotechar='"'))

    changed = False
    for row in rows[1:]:
        if len(row) != 3:
            continue
        cleaned = clean_answer_field(row[2])
        if cleaned != row[2]:
            row[2] = cleaned
            changed = True

    if changed:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerows(rows)

    return changed


updated_files = []
for path in sorted(CSV_DIR.iterdir()):
    if path.is_file() and FILE_PATTERN.match(path.name):
        if normalize_file(path):
            updated_files.append(path.name)

print(f"Updated {len(updated_files)} files.")
for name in updated_files:
    print(name)
