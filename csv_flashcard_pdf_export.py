#!/usr/bin/env python3
"""Export a CSV flashcard file to a clean PDF using pandoc.

The script searches for a user-supplied CSV name or relative path inside the
hard-coded CSV root. Matching is case-insensitive and ignores whether the user
typed the .csv extension.

How to call it:

    python3 csv_flashcard_pdf_export.py
    python3 csv_flashcard_pdf_export.py --hide-numbers
    python3 csv_flashcard_pdf_export.py --sort-col english
    python3 csv_flashcard_pdf_export.py --sort-col spanish
    python3 csv_flashcard_pdf_export.py --sort-col number
    python3 csv_flashcard_pdf_export.py --list-csvs
    python3 csv_flashcard_pdf_export.py --all_files

Example:

    python3 csv_flashcard_pdf_export.py --all_files --hide-numbers --sort-col english

When prompted, the user can enter any of these forms:

    vocab_numbers_01
    vocab_numbers_01.csv
    Vocabulary/vocab_numbers_01
    Vocabulary/vocab_numbers_01.csv

Behavior summary:

    - No --sort-col flag: keep the CSV's original row order.
    - --hide-numbers: omit the first Number/id column from PDF output.
    - --sort-col english: sort by the English column.
    - --sort-col spanish: sort by the Spanish column.
    - --sort-col number: sort by the first numeric/id column.
    - --list-csvs: create a PDF index of all CSV filenames by folder.
    - --all_files: export every CSV to its own PDF under a mirrored Desktop folder.
    - If no CSV matches, report that and quit.
    - If multiple CSV files match, list each matching parent folder and quit.
    - Output PDF is written to the Desktop with the same base filename.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROGRAM_DIR = Path("/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards")
CSV_ROOT = Path("/Volumes/Squallywag/Python/Current Python Projects/streamlit_eng_sp_flashcards/csv/")
DESKTOP_DIR = Path.home() / "Desktop"
ALL_FILES_OUTPUT_DIR = DESKTOP_DIR / "Spanish Flashcards CSVs"

KNOWN_HEADER_ALIASES = {
    "id": "Number",
    "number": "Number",
    "no": "Number",
    "num": "Number",
    "word": "English",
    "english": "English",
    "front": "English",
    "question": "English",
    "answer": "Spanish",
    "spanish": "Spanish",
    "back": "Spanish",
    "translation": "Spanish",
}

ENGLISH_SORT_ARTICLES = ("a", "an", "the")
SPANISH_SORT_ARTICLES = ("el", "la", "los", "las", "lo", "un", "una", "unos", "unas", "al", "del")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find a CSV under the flashcards csv folder and export it to a PDF on the Desktop."
    )
    parser.add_argument(
        "--hide-numbers",
        action="store_true",
        help="Omit the first Number/id column from exported PDFs when present.",
    )
    parser.add_argument(
        "--list-csvs",
        action="store_true",
        help="Create a PDF index of all CSV filenames grouped by folder.",
    )
    parser.add_argument(
        "--all_files",
        action="store_true",
        help="Export every CSV file to a matching PDF under a mirrored Desktop folder.",
    )
    parser.add_argument(
        "--sort-col",
        choices=("english", "spanish", "number"),
        dest="sort_col",
        help="Sort rows by english, spanish, or number. Default keeps the CSV row order.",
    )
    return parser


def strip_csv_suffix(value: str) -> str:
    text = value.strip().strip('"').strip("'")
    if text.lower().endswith(".csv"):
        return text[:-4]
    return text


def normalize_path_value(value: str) -> str:
    cleaned = strip_csv_suffix(value).replace("\\", "/").strip("/")
    return cleaned.casefold()


def normalize_name_value(value: str) -> str:
    return Path(strip_csv_suffix(value)).name.casefold()


def find_matches(user_input: str) -> tuple[list[Path], str]:
    normalized_path = normalize_path_value(user_input)
    normalized_name = normalize_name_value(user_input)

    direct_matches: list[Path] = []
    name_matches: list[Path] = []

    for candidate in CSV_ROOT.rglob("*"):
        if not candidate.is_file() or candidate.suffix.casefold() != ".csv":
            continue

        relative_no_suffix = normalize_path_value(str(candidate.relative_to(CSV_ROOT)))
        candidate_name = candidate.stem.casefold()

        if relative_no_suffix == normalized_path:
            direct_matches.append(candidate)
        elif candidate_name == normalized_name:
            name_matches.append(candidate)

    if direct_matches:
        return sorted(direct_matches), "path"

    return sorted(name_matches), "name"


def detect_delimiter(file_path: Path) -> str:
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)

    if not sample.strip():
        return ","

    try:
        return csv.Sniffer().sniff(sample, delimiters=",;	|").delimiter
    except csv.Error:
        return ","


def read_csv_rows(file_path: Path) -> list[list[str]]:
    delimiter = detect_delimiter(file_path)
    rows: list[list[str]] = []

    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for row in reader:
            trimmed = [cell.strip() for cell in row]
            if any(cell for cell in trimmed):
                rows.append(trimmed)

    return rows


def count_csv_items(file_path: Path) -> int:
    rows = read_csv_rows(file_path)
    return max(0, len(rows) - 1)


def looks_like_header(row: list[str]) -> bool:
    normalized = [cell.strip().casefold() for cell in row]
    recognized = sum(1 for cell in normalized if cell in KNOWN_HEADER_ALIASES)
    return recognized >= max(2, min(len(normalized), 2))


def prettify_headers(first_row: list[str], column_count: int) -> list[str]:
    mapped = [KNOWN_HEADER_ALIASES.get(cell.strip().casefold(), cell.strip()) for cell in first_row[:column_count]]
    if column_count == 3 and mapped == ["Number", "English", "Spanish"]:
        return mapped
    if column_count == 2 and mapped == ["English", "Spanish"]:
        return mapped
    if all(mapped):
        return mapped
    return default_headers(column_count)


def default_headers(column_count: int) -> list[str]:
    if column_count == 3:
        return ["Number", "English", "Spanish"]
    if column_count == 2:
        return ["English", "Spanish"]
    return [f"Column {index}" for index in range(1, column_count + 1)]


def split_header_and_rows(rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    if not rows:
        raise ValueError("The CSV file is empty.")

    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
    first_row = normalized_rows[0]

    if looks_like_header(first_row):
        return prettify_headers(first_row, column_count), normalized_rows[1:]

    return default_headers(column_count), normalized_rows


def sort_rows(rows: list[list[str]], sort_col: str | None) -> list[list[str]]:
    if not sort_col or not rows:
        return rows

    if sort_col == "number":
        column_index = 0
    elif sort_col == "english":
        column_index = 1 if len(rows[0]) >= 3 else 0
    else:
        column_index = 2 if len(rows[0]) >= 3 else 1

    if column_index >= len(rows[0]):
        raise ValueError(f'The file does not support sorting by "{sort_col}".')

    def drop_leading_article(value: str, articles: tuple[str, ...]) -> str:
        for article in articles:
            prefix = f"{article} "
            if value.startswith(prefix):
                return value[len(prefix) :].lstrip()
        return value

    def normalize_text_sort_value(value: str) -> str:
        normalized = value.strip().casefold()
        if sort_col == "spanish":
            normalized = normalized.lstrip("¿¡")
            normalized = drop_leading_article(normalized, SPANISH_SORT_ARTICLES)
        elif sort_col == "english":
            normalized = drop_leading_article(normalized, ENGLISH_SORT_ARTICLES)
        return normalized

    def sort_key(row: list[str]) -> tuple[int, float | str, str]:
        value = row[column_index].strip()
        if sort_col == "number":
            try:
                return (0, float(value), value.casefold())
            except ValueError:
                normalized_value = normalize_text_sort_value(value)
                return (1, normalized_value, value.casefold())
        normalized_value = normalize_text_sort_value(value)
        return (0, normalized_value, value.casefold())

    return sorted(rows, key=sort_key)


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "/": r"/\allowbreak{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    escaped = []
    for char in value.replace("\n", " "):
        escaped.append(replacements.get(char, char))
    return "".join(escaped)


def build_latex_front_matter(
    title: str,
    footer_name: str,
    *,
    font_size: str = "12pt",
    geometry_options: str = "margin=1in",
    extra_header_includes: list[str] | None = None,
) -> list[str]:
    title_text = latex_escape(title)
    footer_text = latex_escape(footer_name)
    header_includes = [
        f'  - \\usepackage[{geometry_options}]{{geometry}}',
        '  - \\usepackage{fontspec}',
        '  - \\setmainfont{TeX Gyre Heros}',
        '  - \\setsansfont{TeX Gyre Heros}',
        '  - \\usepackage{longtable}',
        '  - \\usepackage{array}',
        '  - \\usepackage{fancyhdr}',
        '  - \\pagestyle{fancy}',
        '  - \\fancyhf{}',
        f'  - \\fancyfoot[R]{{\\fontsize{{8}}{{9.6}}\\selectfont {footer_text}\\hspace{{0.7em}}\\thepage}}',
        '  - \\renewcommand{\\headrulewidth}{0pt}',
        '  - \\renewcommand{\\footrulewidth}{0pt}',
        '  - \\setlength{\\parindent}{0pt}',
        '  - \\pagenumbering{arabic}',
    ]
    if extra_header_includes:
        header_includes.extend(f'  - {line}' for line in extra_header_includes)
    return [
        "---",
        'documentclass: article',
        'classoption:',
        f'  - {font_size}',
        'header-includes:',
        *header_includes,
        "---",
        "",
        rf"\begin{{center}}{{\fontsize{{18}}{{21.6}}\selectfont\textbf{{{title_text}}}}}\end{{center}}",
        r"\vspace{0.65em}",
    ]


def column_widths(column_count: int) -> list[str]:
    if column_count == 2:
        return [r">{\raggedright\arraybackslash}p{0.46\textwidth}"] * 2
    if column_count == 3:
        return [
            r">{\raggedright\arraybackslash}p{0.12\textwidth}",
            r">{\raggedright\arraybackslash}p{0.39\textwidth}",
            r">{\raggedright\arraybackslash}p{0.39\textwidth}",
        ]

    usable_width = 0.96 / max(column_count, 1)
    return [rf">{{\raggedright\arraybackslash}}p{{{usable_width:.4f}\textwidth}}"] * column_count


def render_markdown(title: str, footer_name: str, headers: list[str], rows: list[list[str]]) -> str:
    column_spec = "".join(column_widths(len(headers)))
    table_lines = [rf"\begin{{longtable}}{{@{{}}{column_spec}@{{}}}}"]
    header_line = " & ".join(rf"\textbf{{{latex_escape(cell)}}}" for cell in headers)
    table_lines.append(header_line + r" \\[6pt]")
    table_lines.append(r"\endfirsthead")
    table_lines.append(header_line + r" \\[6pt]")
    table_lines.append(r"\endhead")

    for row in rows:
        padded_row = row + [""] * (len(headers) - len(row))
        line = " & ".join(latex_escape(cell) for cell in padded_row[: len(headers)])
        table_lines.append(line + r" \\[5pt]")

    table_lines.append(r"\end{longtable}")

    return "\n".join(
        [
            *build_latex_front_matter(title, footer_name),
            r"\fontsize{13}{16}\selectfont",
            r"\renewcommand{\arraystretch}{1.3}",
            r"\setlength{\LTpre}{0pt}",
            r"\setlength{\LTpost}{0pt}",
            *table_lines,
            "",
        ]
    )


def maybe_hide_number_column(headers: list[str], rows: list[list[str]], hide_numbers: bool) -> tuple[list[str], list[list[str]]]:
    if not hide_numbers or len(headers) < 3:
        return headers, rows

    first_header = headers[0].strip().casefold()
    if first_header != "number":
        return headers, rows

    trimmed_headers = headers[1:]
    trimmed_rows = [row[1:] if len(row) > 1 else [] for row in rows]
    return trimmed_headers, trimmed_rows


def build_csv_tree_lines(current_dir: Path, depth: int = 0) -> list[str]:
    lines: list[str] = []
    directories = sorted(
        (path for path in current_dir.iterdir() if path.is_dir() and not path.name.startswith(".")),
        key=lambda path: path.name.casefold(),
    )
    files = sorted(
        (path for path in current_dir.iterdir() if path.is_file() and path.suffix.casefold() == ".csv"),
        key=lambda path: path.name.casefold(),
    )

    for directory in directories:
        indent_em = depth * 1.6
        child_item_count = len(
            [path for path in directory.iterdir() if (path.is_dir() and not path.name.startswith(".")) or (path.is_file() and path.suffix.casefold() == ".csv")]
        )
        directory_name = latex_escape(f"{directory.name} [{child_item_count}]")
        lines.append(r"\vspace{0.45em}")
        lines.append(
            rf"\noindent\hspace*{{{indent_em:.1f}em}}\textbf{{{directory_name}}}\par"
        )
        lines.extend(build_csv_tree_lines(directory, depth + 1))

    for file_path in files:
        indent_em = depth * 1.6
        file_item_count = count_csv_items(file_path)
        file_name = latex_escape(f"{file_path.name} [{file_item_count}]")
        lines.append(
            rf"\noindent\hspace*{{{indent_em:.1f}em}}{file_name}\par"
        )

    return lines


def render_csv_index_markdown() -> str:
    body_lines = build_csv_tree_lines(CSV_ROOT)
    if not body_lines:
        body_lines = ["No CSV files were found."]

    return "\n".join(
        [
            *build_latex_front_matter(
                "Spanish Flashcard Program: csv file index",
                "csv_file_index.pdf",
                font_size="10pt",
                geometry_options="top=0.5in,left=0.5in,right=0.5in,bottom=1in",
                extra_header_includes=[
                    r"\usepackage{multicol}",
                    r"\setlength{\parskip}{0pt}",
                    r"\setlength{\columnsep}{1.1em}",
                ],
            ),
            r"\raggedcolumns",
            r"\fontsize{10}{11.6}\selectfont",
            r"\begin{multicols}{2}",
            *body_lines,
            r"\end{multicols}",
            "",
        ]
    )


def iter_csv_files(root_dir: Path) -> list[Path]:
    csv_files: list[Path] = []

    for candidate in root_dir.rglob("*"):
        if not candidate.is_file() or candidate.suffix.casefold() != ".csv":
            continue
        if any(part.startswith(".") for part in candidate.relative_to(root_dir).parts):
            continue
        csv_files.append(candidate)

    return sorted(csv_files, key=lambda path: str(path.relative_to(root_dir)).casefold())


def build_output_pdf_path(csv_path: Path) -> Path:
    relative_csv_path = csv_path.relative_to(CSV_ROOT)
    relative_pdf_path = relative_csv_path.with_suffix(".pdf")
    output_path = ALL_FILES_OUTPUT_DIR / relative_pdf_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def export_single_csv(
    csv_path: Path,
    sort_col: str | None,
    hide_numbers: bool,
    output_path: Path | None = None,
) -> Path:
    rows = read_csv_rows(csv_path)
    headers, data_rows = split_header_and_rows(rows)
    sorted_rows = sort_rows(data_rows, sort_col)
    headers, sorted_rows = maybe_hide_number_column(headers, sorted_rows, hide_numbers)
    markdown_text = render_markdown(csv_path.stem, csv_path.name, headers, sorted_rows)

    if output_path is None:
        output_stem = csv_path.stem
    else:
        output_stem = str(output_path.with_suffix(""))

    return export_pdf(output_stem, markdown_text)


def print_progress(current: int, total: int) -> None:
    bar_width = 30
    filled = 0 if total <= 0 else int(bar_width * current / total)
    bar = "#" * filled + "-" * (bar_width - filled)
    print(f"\rWriting PDFs: [{bar}] {current}/{total}", end="", flush=True)
    if current >= total:
        print()


def export_all_csv_files(sort_col: str | None, hide_numbers: bool) -> tuple[int, Path]:
    csv_files = iter_csv_files(CSV_ROOT)
    if not csv_files:
        raise RuntimeError("No CSV files were found under the csv folder.")

    ALL_FILES_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_files = len(csv_files)
    export_count = 0
    print_progress(0, total_files)

    for csv_path in csv_files:
        output_path = build_output_pdf_path(csv_path)
        export_single_csv(csv_path, sort_col, hide_numbers, output_path=output_path)
        export_count += 1
        print_progress(export_count, total_files)

    return export_count, ALL_FILES_OUTPUT_DIR


def find_pdf_engine() -> str:
    for engine in ("xelatex", "lualatex"):
        if shutil.which(engine):
            return engine
    raise RuntimeError("Pandoc PDF export requires xelatex or lualatex to be installed.")


def export_pdf(output_stem: str, markdown_text: str) -> Path:
    if not shutil.which("pandoc"):
        raise RuntimeError("Pandoc is not installed or not on PATH.")

    engine = find_pdf_engine()
    output_path = Path(output_stem)
    if output_path.suffix.casefold() != ".pdf":
        output_path = DESKTOP_DIR / f"{output_stem}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="flashcard_pdf_") as temp_dir:
        temp_markdown = Path(temp_dir) / "export.md"
        temp_markdown.write_text(markdown_text, encoding="utf-8")

        command = [
            "pandoc",
            str(temp_markdown),
            "--from",
            "markdown+raw_tex",
            "--pdf-engine",
            engine,
            "--output",
            str(output_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Unknown pandoc error."
        raise RuntimeError(message)

    return output_path


def report_matches(matches: list[Path]) -> None:
    print(f"Found {len(matches)} matching CSV files. Please be more specific:")
    for match in matches:
        relative_path = match.relative_to(CSV_ROOT)
        parent_folder = relative_path.parent if relative_path.parent != Path('.') else Path('(csv root)')
        print(f"- {match.name} | parent folder: {parent_folder}")
        print(f"  full path: {relative_path}")


def main() -> int:
    os.chdir(PROGRAM_DIR)
    parser = build_parser()
    args = parser.parse_args()

    if not CSV_ROOT.exists():
        print(f"CSV folder not found: {CSV_ROOT}")
        return 1

    if args.list_csvs and args.all_files:
        print("Error: --list-csvs and --all_files cannot be used together.")
        return 1

    if args.list_csvs:
        try:
            markdown_text = render_csv_index_markdown()
            output_path = export_pdf("csv_file_index", markdown_text)
        except Exception as exc:
            print(f"Error: {exc}")
            return 1

        print(f"CSV index PDF created: {output_path}")
        return 0

    if args.all_files:
        try:
            export_count, output_dir = export_all_csv_files(args.sort_col, args.hide_numbers)
        except Exception as exc:
            print(f"Error: {exc}")
            return 1

        print(f"Created {export_count} PDF files in: {output_dir}")
        return 0

    user_input = input("Enter the CSV file name or relative path: ").strip()
    if not user_input:
        print("No file name entered. Quitting.")
        return 1

    matches, match_mode = find_matches(user_input)
    if not matches:
        print("No matching CSV file was found under the csv folder.")
        return 1

    if len(matches) > 1:
        report_matches(matches)
        return 1

    csv_path = matches[0]
    print(f"Matched by {match_mode}: {csv_path.relative_to(CSV_ROOT)}")

    try:
        output_path = export_single_csv(csv_path, args.sort_col, args.hide_numbers)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"PDF created: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())